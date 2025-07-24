from django.db import models
from authenication.models import CustomUser

class BusinessDocument(models.Model):
    DOCUMENT_TYPES = [
        ('business_license', 'Business License'),
        ('tin_certificate', 'TIN Certificate'),
        ('trade_permit', 'Trade Permit'),
        ('health_certificate', 'Health Certificate'),
        ('fire_safety', 'Fire Safety Certificate'),
        ('other', 'Other'),
    ]

    business_profile = models.ForeignKey('BusinessProfile', on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=50, choices=DOCUMENT_TYPES)
    document_file = models.FileField(upload_to='business_documents/')
    document_name = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.document_type} - {self.business_profile.business_name}"

class BusinessProfile(models.Model):
    BUSINESS_TYPES = [
        ('restaurant', 'Restaurant'),
        ('grocery', 'Grocery Store'),
        ('pharmacy', 'Pharmacy'),
        ('electronics', 'Electronics'),
        ('clothing', 'Clothing'),
        ('bakery', 'Bakery'),
        ('butchery', 'Butchery'),
        ('hardware', 'Hardware Store'),
        ('other', 'Other'),
    ]
    
    VERIFICATION_STATUS = [
        ('pending', 'Pending'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('suspended', 'Suspended'),
    ]

    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    business_name = models.CharField(max_length=255)
    business_type = models.CharField(max_length=50, choices=BUSINESS_TYPES)
    business_description = models.TextField(blank=True)
    tin_number = models.CharField(max_length=50, unique=True)
    business_license_number = models.CharField(max_length=100)
    business_address = models.TextField()
    business_phone = models.CharField(max_length=15)
    business_email = models.EmailField()
    
    # Location fields
    location_lat = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
    location_lng = models.DecimalField(max_digits=11, decimal_places=8, null=True, blank=True)
    
    # Verification fields
    verification_status = models.CharField(max_length=20, choices=VERIFICATION_STATUS, default='pending')
    verification_notes = models.TextField(blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_businesses')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.business_name} - {self.user.username}"

    @property
    def total_documents(self):
        return self.documents.count()

    @property
    def verified_documents(self):
        return self.documents.filter(is_verified=True).count()

    @property
    def verification_progress(self):
        if self.total_documents == 0:
            return 0
        return (self.verified_documents / self.total_documents) * 100
