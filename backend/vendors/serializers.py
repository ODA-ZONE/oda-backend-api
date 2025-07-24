from rest_framework import serializers
from .models import BusinessProfile, BusinessDocument
from authenication.models import CustomUser

class BusinessDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusinessDocument
        fields = ['id', 'document_type', 'document_file', 'document_name', 'uploaded_at', 'is_verified']
        read_only_fields = ['id', 'uploaded_at', 'is_verified']

class BusinessRegistrationSerializer(serializers.ModelSerializer):
    documents = BusinessDocumentSerializer(many=True, read_only=True)
    
    class Meta:
        model = BusinessProfile
        fields = [
            'business_name', 'business_type', 'business_description',
            'tin_number', 'business_license_number', 'business_address',
            'business_phone', 'business_email', 'location_lat', 'location_lng',
            'documents'
        ]

    def validate_tin_number(self, value):
        if BusinessProfile.objects.filter(tin_number=value).exists():
            raise serializers.ValidationError("A business with this TIN number already exists.")
        return value

    def validate_business_license_number(self, value):
        if BusinessProfile.objects.filter(business_license_number=value).exists():
            raise serializers.ValidationError("A business with this license number already exists.")
        return value

    def create(self, validated_data):
        user = self.context['request'].user
        
        # Check if user already has a business profile
        if hasattr(user, 'businessprofile'):
            raise serializers.ValidationError("User already has a business profile.")
        
        # Ensure user has vendor role
        if user.role != 'vendor':
            user.role = 'vendor'
            user.save()
        
        validated_data['user'] = user
        return super().create(validated_data)

class BusinessProfileSerializer(serializers.ModelSerializer):
    documents = BusinessDocumentSerializer(many=True, read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_phone = serializers.CharField(source='user.phone', read_only=True)
    total_documents = serializers.ReadOnlyField()
    verified_documents = serializers.ReadOnlyField()
    verification_progress = serializers.ReadOnlyField()

    class Meta:
        model = BusinessProfile
        fields = [
            'id', 'user_email', 'user_phone', 'business_name', 'business_type',
            'business_description', 'tin_number', 'business_license_number',
            'business_address', 'business_phone', 'business_email',
            'location_lat', 'location_lng', 'verification_status',
            'verification_notes', 'verified_at', 'created_at', 'updated_at',
            'documents', 'total_documents', 'verified_documents', 'verification_progress'
        ]
        read_only_fields = [
            'id', 'verification_status', 'verification_notes', 'verified_at',
            'created_at', 'updated_at'
        ]

class DocumentUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusinessDocument
        fields = ['document_type', 'document_file', 'document_name']

    def create(self, validated_data):
        business_profile = self.context['business_profile']
        validated_data['business_profile'] = business_profile
        return super().create(validated_data)
