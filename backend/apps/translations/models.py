"""Audit metadata only: no source text, model response, keys or customer payloads."""

import uuid

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db import models


class TranslationLog(models.Model):
    run_id = models.UUIDField(default=uuid.uuid4, db_index=True)
    content_type = models.ForeignKey(ContentType, on_delete=models.PROTECT)
    object_id = models.CharField(max_length=64)
    locale = models.CharField(max_length=2, choices=settings.LANGUAGES)
    fields = models.JSONField(default=list)
    status = models.CharField(
        max_length=12,
        choices=[("success", "Translated"), ("failed", "Failed"), ("skipped", "Skipped")],
        db_index=True,
    )
    error_code = models.CharField(max_length=40, blank=True)
    attempts = models.PositiveSmallIntegerField(default=0)
    model_name = models.CharField(max_length=120)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at", "-pk"]
        verbose_name = "Translation log"
        verbose_name_plural = "Translation log"

    def __str__(self):
        return (
            f"{self.content_type} #{self.object_id} · {self.locale} · {self.get_status_display()}"
        )
