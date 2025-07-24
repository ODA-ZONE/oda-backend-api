from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import BusinessProfile, BusinessDocument
from .serializers import (
    BusinessRegistrationSerializer,
    BusinessProfileSerializer,
    DocumentUploadSerializer
)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def register_business(request):
    """Register a new business for the authenticated vendor"""
    
    # Check if user already has a business profile
    if hasattr(request.user, 'businessprofile'):
        return Response({
            'error': 'User already has a business profile'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    serializer = BusinessRegistrationSerializer(data=request.data, context={'request': request})
    
    if serializer.is_valid():
        business_profile = serializer.save()
        
        return Response({
            'message': 'Business registered successfully',
            'business_id': business_profile.id,
            'verification_status': business_profile.verification_status
        }, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def upload_business_documents(request):
    """Upload documents for business verification"""
    
    try:
        business_profile = request.user.businessprofile
    except BusinessProfile.DoesNotExist:
        return Response({
            'error': 'No business profile found. Please register your business first.'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Check if business is already approved
    if business_profile.verification_status == 'approved':
        return Response({
            'error': 'Business is already verified. No additional documents needed.'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    serializer = DocumentUploadSerializer(
        data=request.data, 
        context={'business_profile': business_profile}
    )
    
    if serializer.is_valid():
        document = serializer.save()
        
        # Update business status to under_review if it was pending
        if business_profile.verification_status == 'pending':
            business_profile.verification_status = 'under_review'
            business_profile.save()
        
        return Response({
            'message': 'Document uploaded successfully',
            'document_id': document.id,
            'document_type': document.document_type,
            'business_status': business_profile.verification_status
        }, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_verification_status(request):
    """Get the verification status of the user's business"""
    
    try:
        business_profile = request.user.businessprofile
    except BusinessProfile.DoesNotExist:
        return Response({
            'error': 'No business profile found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    serializer = BusinessProfileSerializer(business_profile)
    
    return Response({
        'business_profile': serializer.data,
        'verification_status': business_profile.verification_status,
        'verification_progress': business_profile.verification_progress,
        'total_documents': business_profile.total_documents,
        'verified_documents': business_profile.verified_documents
    }, status=status.HTTP_200_OK)

# Additional utility views for admin/staff

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def list_pending_businesses(request):
    """List all businesses pending verification (Admin only)"""
    
    if not request.user.is_staff:
        return Response({
            'error': 'Permission denied'
        }, status=status.HTTP_403_FORBIDDEN)
    
    pending_businesses = BusinessProfile.objects.filter(
        verification_status__in=['pending', 'under_review']
    )
    
    serializer = BusinessProfileSerializer(pending_businesses, many=True)
    
    return Response({
        'pending_businesses': serializer.data,
        'count': pending_businesses.count()
    }, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def update_verification_status(request, business_id):
    """Update verification status of a business (Admin only)"""
    
    if not request.user.is_staff:
        return Response({
            'error': 'Permission denied'
        }, status=status.HTTP_403_FORBIDDEN)
    
    business_profile = get_object_or_404(BusinessProfile, id=business_id)
    
    new_status = request.data.get('verification_status')
    notes = request.data.get('verification_notes', '')
    
    if new_status not in ['approved', 'rejected', 'under_review']:
        return Response({
            'error': 'Invalid verification status'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    business_profile.verification_status = new_status
    business_profile.verification_notes = notes
    
    if new_status == 'approved':
        from django.utils import timezone
        business_profile.verified_at = timezone.now()
        business_profile.verified_by = request.user
    
    business_profile.save()
    
    return Response({
        'message': f'Business verification status updated to {new_status}',
        'business_id': business_profile.id,
        'new_status': new_status
    }, status=status.HTTP_200_OK)
