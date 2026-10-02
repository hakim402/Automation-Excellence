"""Atomic, shared PostgreSQL rate limits; do not trust client-supplied forwarded IPs."""

from datetime import timedelta
from ipaddress import ip_address, ip_network

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from django.utils.crypto import salted_hmac
from rest_framework.throttling import SimpleRateThrottle

from .models import CaptureThrottleBucket


def client_ip(request):
    try:
        peer = ip_address(request.META.get("REMOTE_ADDR", ""))
    except ValueError:
        return None
    # Only a trusted direct proxy may supply a single, overwritten X-Real-IP.
    if any(peer in ip_network(network) for network in settings.CAPTURE_TRUSTED_PROXIES):
        try:
            return str(ip_address(request.META.get("HTTP_X_REAL_IP", "")))
        except ValueError:
            pass
    return str(peer)


class CaptureThrottle(SimpleRateThrottle):
    def allow_request(self, request, view):
        if request.method != "POST":
            return True
        key = salted_hmac(
            "crm.capture", f"{self.scope}:{client_ip(request) or 'unknown'}"
        ).hexdigest()
        now = timezone.now()
        with transaction.atomic():
            bucket, _ = CaptureThrottleBucket.objects.get_or_create(
                key=key, defaults={"expires_at": now + timedelta(seconds=self.duration)}
            )
            bucket = CaptureThrottleBucket.objects.select_for_update().get(pk=bucket.pk)
            if bucket.expires_at <= now:
                bucket.count = 0
                bucket.expires_at = now + timedelta(seconds=self.duration)
            self.retry_after = max(1, (bucket.expires_at - now).total_seconds())
            if bucket.count >= self.num_requests:
                return False
            bucket.count += 1
            bucket.save(update_fields=["count", "expires_at"])
        return True

    def wait(self):
        return self.retry_after


class LeadThrottle(CaptureThrottle):
    scope = "leads"


class NewsletterThrottle(CaptureThrottle):
    scope = "newsletter"
