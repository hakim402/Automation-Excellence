from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.crm.models import CaptureThrottleBucket


class Command(BaseCommand):
    help = "Delete expired capture rate-limit counters. Safe to run periodically."

    def handle(self, *args, **options):
        count, _ = CaptureThrottleBucket.objects.filter(expires_at__lte=timezone.now()).delete()
        self.stdout.write(f"Removed {count} expired rate-limit counters.")
