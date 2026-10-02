"""Invalidate public content only, after the database transaction commits."""

import json
import logging
from http.client import HTTPException
from urllib.error import URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener

from django.conf import settings
from django.db import transaction
from django.db.models.signals import m2m_changed, post_delete, post_save
from django.dispatch import receiver

logger = logging.getLogger(__name__)
CONTENT_APPS = {
    "core",
    "services",
    "products",
    "portfolio",
    "blog",
    "digital_marketing",
    "ai_automation",
    "custom_software",
    "web_development",
    "mobile_development",
    "cyber_security",
}


class NoRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def notify_frontend():
    if not settings.REVALIDATE_WEBHOOK_URL or not settings.REVALIDATE_WEBHOOK_SECRET:
        return False
    request = Request(
        settings.REVALIDATE_WEBHOOK_URL,
        data=json.dumps({"scope": "content"}).encode(),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.REVALIDATE_WEBHOOK_SECRET}",
        },
        method="POST",
    )
    try:
        with build_opener(NoRedirects()).open(request, timeout=3) as response:
            result = json.loads(response.read(4096))
        if result.get("revalidated") is not True:
            raise ValueError("Invalid acknowledgement")
        return True
    except (URLError, OSError, HTTPException, ValueError, AttributeError):
        # Provider errors can contain secrets. Log neither URL, payload nor exception.
        logger.warning(
            "Frontend revalidation failed; retry with revalidate_frontend. "
            "Timed ISR remains active."
        )
        return False


@receiver(post_save, dispatch_uid="core.content_saved")
@receiver(post_delete, dispatch_uid="core.content_deleted")
def content_changed(sender, instance, using="default", raw=False, **kwargs):
    if not raw and sender._meta.app_label in CONTENT_APPS:
        transaction.on_commit(notify_frontend, using=using)


@receiver(m2m_changed, dispatch_uid="core.content_relations")
def relations_changed(sender, instance, action, using="default", **kwargs):
    if (
        action in {"post_add", "post_remove", "post_clear"}
        and instance._meta.app_label in CONTENT_APPS
    ):
        transaction.on_commit(notify_frontend, using=using)
