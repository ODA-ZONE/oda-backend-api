from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
import random
import string

# Create your models here.
class UserRole(models.TextChoices):
    CONSUMER = 'consumer', 'Consumer'
    RETAILER = 'retailer', 'Retailer'
    VENDOR = 'vendor', 'Vendor'
    ADMIN = 'admin', 'Admin'

class CustomUser(AbstractUser):
    full_name = models.CharField(max_length=255, blank=True, null=True)  # Added full_name field
    phone = models.CharField(max_length=15, unique=True)
    role = models.CharField(max_length=10, choices=UserRole.choices)
    is_phone_verified = models.BooleanField(default=False)
    is_email_verified = models.BooleanField(default=False)
    location_lat = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
    location_lng = models.DecimalField(max_digits=11, decimal_places=8, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Auto-populate first_name and last_name from full_name if provided
        if self.full_name and not self.first_name and not self.last_name:
            name_parts = self.full_name.strip().split()
            if len(name_parts) >= 1:
                self.first_name = name_parts[0]
            if len(name_parts) >= 2:
                self.last_name = ' '.join(name_parts[1:])
        # Auto-populate full_name from first_name and last_name if not provided
        elif not self.full_name and (self.first_name or self.last_name):
            self.full_name = f"{self.first_name or ''} {self.last_name or ''}".strip()
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.username} - {self.email}"

class OTPVerification(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    otp_code = models.CharField(max_length=6)
    otp_type = models.CharField(max_length=10, choices=[('email', 'Email'), ('phone', 'Phone')])
    contact = models.CharField(max_length=255)  # email or phone number
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        ordering = ['-created_at']

    def is_expired(self):
        return timezone.now() > self.expires_at

    def save(self, *args, **kwargs):
        if not self.otp_code:
            self.otp_code = ''.join(random.choices(string.digits, k=6))
        if not self.expires_at:
            self.expires_at = timezone.now() + timezone.timedelta(minutes=5)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"OTP for {self.user.username} - {self.otp_type}"