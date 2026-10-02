from django.urls import path

from .views import LeadCaptureView, NewsletterCaptureView

urlpatterns = [
    path("leads/", LeadCaptureView.as_view(), name="lead-capture"),
    path("newsletter/", NewsletterCaptureView.as_view(), name="newsletter-capture"),
]
