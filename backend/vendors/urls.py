from django.urls import path
from . import views

urlpatterns = [
    # Business registration endpoints
    path('business/register/', views.register_business, name='register_business'),
    path('business/upload-documents/', views.upload_business_documents, name='upload_business_documents'),
    path('business/verification-status/', views.get_verification_status, name='business_verification_status'),
    
    # Admin endpoints for managing business verification
    path('admin/pending-businesses/', views.list_pending_businesses, name='list_pending_businesses'),
    path('admin/business/<int:business_id>/verify/', views.update_verification_status, name='update_verification_status'),
]
