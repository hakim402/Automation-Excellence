"""Private lead capture records. No public read endpoints belong to this app."""

from django.conf import settings
from django.db import models
from django.db.models.functions import Lower


class Lead(models.Model):
    full_name = models.CharField(max_length=160)
    email = models.EmailField()
    phone = models.CharField(max_length=40, blank=True)
    company = models.CharField(max_length=160, blank=True)
    country = models.CharField(max_length=100, blank=True)
    service = models.ForeignKey(
        "services.Service", on_delete=models.SET_NULL, null=True, blank=True, related_name="leads"
    )
    message = models.TextField(max_length=10000)
    preferred_contact = models.CharField(
        max_length=12,
        choices=[("email", "Email"), ("phone", "Phone"), ("whatsapp", "WhatsApp")],
        default="email",
    )
    locale = models.CharField(max_length=2, choices=settings.LANGUAGES, default="en")
    source_path = models.CharField(max_length=500, blank=True)
    utm_source = models.CharField(max_length=200, blank=True)
    utm_medium = models.CharField(max_length=200, blank=True)
    utm_campaign = models.CharField(max_length=200, blank=True)
    status = models.CharField(
        max_length=12,
        choices=[
            ("new", "New"),
            ("contacted", "Contacted"),
            ("qualified", "Qualified"),
            ("won", "Won"),
            ("lost", "Lost"),
        ],
        default="new",
        db_index=True,
    )
    internal_notes = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    alert_sent_at = models.DateTimeField(null=True, blank=True, editable=False)

    class Meta:
        ordering = ["-created_at", "-pk"]

    def __str__(self):
        return f"{self.full_name} — {self.get_status_display()}"


class NewsletterSubscriber(models.Model):
    email = models.EmailField(unique=True)
    locale = models.CharField(max_length=2, choices=settings.LANGUAGES, default="en")
    is_confirmed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(Lower("email"), name="newsletter_email_case_insensitive")
        ]

    def __str__(self):
        return self.email

    def save(self, *args, **kwargs):
        self.email = self.email.strip().lower()
        super().save(*args, **kwargs)


class CaptureThrottleBucket(models.Model):
    """Ephemeral counters shared across workers; keys are HMACs, never raw IP addresses."""

    key = models.CharField(max_length=40, unique=True)
    count = models.PositiveIntegerField(default=0)
    expires_at = models.DateTimeField(db_index=True)

    def __str__(self):
        return f"Capture counter expiring {self.expires_at.isoformat()}"
