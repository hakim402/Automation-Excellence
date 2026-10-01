"""Send minimal staff alerts after commit; personal lead data stays in the admin."""

import logging
from functools import partial

from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from django.utils import timezone

from .models import Lead

logger = logging.getLogger(__name__)


def send_lead_alert(lead_id):
    if not settings.LEAD_ALERT_RECIPIENTS:
        return False
    try:
        # Serialise concurrent retries. Failed delivery leaves alert_sent_at empty.
        with transaction.atomic():
            lead = Lead.objects.select_for_update().get(pk=lead_id)
            if lead.alert_sent_at:
                return False
            path = reverse("admin:crm_lead_change", args=[lead.pk])
            url = f"{settings.ADMIN_BASE_URL.rstrip('/')}{path}"
            sent = send_mail(
                subject=f"Automex: new quote request #{lead.pk}",
                message=(
                    f"A new quote request is ready for review.\n\nOpen the secure admin: {url}\n"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=settings.LEAD_ALERT_RECIPIENTS,
                fail_silently=False,
            )
            if sent:
                Lead.objects.filter(pk=lead.pk).update(alert_sent_at=timezone.now())
                return True
    except Exception:
        # SMTP errors can include addresses. Log only the opaque row identifier.
        logger.error("Lead alert delivery failed for lead_id=%s; retry from admin.", lead_id)
    return False


@receiver(post_save, sender=Lead, dispatch_uid="crm.new_lead_alert")
def queue_lead_alert(sender, instance, created, raw=False, **kwargs):
    if created and not raw:
        transaction.on_commit(partial(send_lead_alert, instance.pk))
