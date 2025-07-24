from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from .models import CustomUser, OTPVerification
import re

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'phone', 'password', 'password_confirm', 'role']

    def validate_email(self, value):
        if CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate_phone(self, value):
        # Basic phone validation - you can make this more sophisticated
        phone_pattern = re.compile(r'^\+?1?\d{9,15}$')
        if not phone_pattern.match(value):
            raise serializers.ValidationError("Enter a valid phone number.")
        
        if CustomUser.objects.filter(phone=value).exists():
            raise serializers.ValidationError("A user with this phone number already exists.")
        return value

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match.")
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = CustomUser(**validated_data)
        user.set_password(password)
        user.save()
        return user

class UserLoginSerializer(serializers.Serializer):
    email_or_phone = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email_or_phone = attrs.get('email_or_phone')
        password = attrs.get('password')

        # Try to find user by email or phone
        user = None
        if '@' in email_or_phone:
            try:
                user = CustomUser.objects.get(email=email_or_phone)
            except CustomUser.DoesNotExist:
                pass
        else:
            try:
                user = CustomUser.objects.get(phone=email_or_phone)
            except CustomUser.DoesNotExist:
                pass

        if user and user.check_password(password):
            if not user.is_active:
                raise serializers.ValidationError("User account is disabled.")
            attrs['user'] = user
            return attrs
        else:
            raise serializers.ValidationError("Invalid credentials.")

class OTPVerificationSerializer(serializers.Serializer):
    contact = serializers.CharField()
    otp_code = serializers.CharField(max_length=6)
    otp_type = serializers.ChoiceField(choices=['email', 'phone'])

    def validate(self, attrs):
        contact = attrs.get('contact')
        otp_code = attrs.get('otp_code')
        otp_type = attrs.get('otp_type')

        try:
            otp = OTPVerification.objects.filter(
                contact=contact,
                otp_code=otp_code,
                otp_type=otp_type,
                is_verified=False
            ).latest('created_at')

            if otp.is_expired():
                raise serializers.ValidationError("OTP has expired.")
            
            attrs['otp'] = otp
            return attrs
        except OTPVerification.DoesNotExist:
            raise serializers.ValidationError("Invalid OTP.")

class ResendOTPSerializer(serializers.Serializer):
    contact = serializers.CharField()
    otp_type = serializers.ChoiceField(choices=['email', 'phone'])

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'phone', 'role', 'is_email_verified', 'is_phone_verified', 'created_at']
        read_only_fields = ['id', 'created_at']