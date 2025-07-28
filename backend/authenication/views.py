from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from .models import CustomUser, OTPVerification
from .serializers import (
    UserRegistrationSerializer, 
    UserLoginSerializer, 
    OTPVerificationSerializer,
    ResendOTPSerializer,
    UserSerializer
)
import logging

logger = logging.getLogger(__name__)

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def register_user(request):
    """Register a new user and send OTP for verification"""
    serializer = UserRegistrationSerializer(data=request.data)
    
    if serializer.is_valid():
        user = serializer.save()
        
        # Create OTP for email verification
        email_otp = OTPVerification.objects.create(
            user=user,
            otp_type='email',
            contact=user.email
        )
        
        # Create OTP for phone verification
        phone_otp = OTPVerification.objects.create(
            user=user,
            otp_type='phone',
            contact=user.phone
        )
        
        # Send email OTP (in development, this will print to console)
        try:
            send_mail(
                'ODA - Email Verification',
                f'Your email verification code is: {email_otp.otp_code}',
                settings.DEFAULT_FROM_EMAIL,  # Use the setting we just added
                [user.email],
                fail_silently=False,
            )
        except Exception as e:
            logger.error(f"Failed to send email OTP: {e}")
        
        # Here you would integrate with SMS service to send phone OTP
        # For now, we'll just log it
        logger.info(f"Phone OTP for {user.phone}: {phone_otp.otp_code}")
        
        return Response({
            'message': 'User registered successfully. Please verify your email and phone.',
            'user_id': user.id,
            'email': user.email,
            'phone': user.phone
        }, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def login_user(request):
    """Login user with email/phone and password"""
    serializer = UserLoginSerializer(data=request.data)
    
    if serializer.is_valid():
        user = serializer.validated_data['user']
        
        # Check if user has verified email or phone
        if not (user.is_email_verified or user.is_phone_verified):
            return Response({
                'error': 'Please verify your email or phone number before logging in.'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        token, created = Token.objects.get_or_create(user=user)
        
        return Response({
            'token': token.key,
            'user': UserSerializer(user).data,
            'message': 'Login successful'
        }, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def verify_otp(request):
    """Verify OTP for email or phone"""
    serializer = OTPVerificationSerializer(data=request.data)
    
    if serializer.is_valid():
        otp = serializer.validated_data['otp']
        otp.is_verified = True
        otp.save()
        
        # Update user verification status
        user = otp.user
        if otp.otp_type == 'email':
            user.is_email_verified = True
        elif otp.otp_type == 'phone':
            user.is_phone_verified = True
        user.save()
        
        return Response({
            'message': f'{otp.otp_type.title()} verified successfully'
        }, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def resend_otp(request):
    """Resend OTP for email or phone"""
    serializer = ResendOTPSerializer(data=request.data)
    
    if serializer.is_valid():
        contact = serializer.validated_data['contact']
        otp_type = serializer.validated_data['otp_type']
        
        # Find user by contact
        user = None
        if otp_type == 'email':
            try:
                user = CustomUser.objects.get(email=contact)
            except CustomUser.DoesNotExist:
                return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        elif otp_type == 'phone':
            try:
                user = CustomUser.objects.get(phone=contact)
            except CustomUser.DoesNotExist:
                return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Create new OTP
        otp = OTPVerification.objects.create(
            user=user,
            otp_type=otp_type,
            contact=contact
        )
        
        # Send OTP
        if otp_type == 'email':
            try:
                send_mail(
                    'ODA - Email Verification',
                    f'Your email verification code is: {otp.otp_code}',
                    settings.DEFAULT_FROM_EMAIL,  # Use the setting we just added
                    [contact],
                    fail_silently=False,
                )
            except Exception as e:
                logger.error(f"Failed to send email OTP: {e}")
        else:
            # Log phone OTP (integrate with SMS service)
            logger.info(f"Phone OTP for {contact}: {otp.otp_code}")
        
        return Response({
            'message': f'OTP sent to {contact}'
        }, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def refresh_token(request):
    """Refresh user token"""
    user = request.user
    token = Token.objects.get(user=user)
    token.delete()
    new_token = Token.objects.create(user=user)
    
    return Response({
        'token': new_token.key,
        'message': 'Token refreshed successfully'
    }, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def logout_user(request):
    """Logout user by deleting token"""
    try:
        token = Token.objects.get(user=request.user)
        token.delete()
        return Response({
            'message': 'Logout successful'
        }, status=status.HTTP_200_OK)
    except Token.DoesNotExist:
        return Response({
            'message': 'User is already logged out'
        }, status=status.HTTP_200_OK)
