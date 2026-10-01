from django.db import models

from apps.core.models import (
    Ordered,
    Publishable,
    validate_icon_name,
    validate_slug_is_english,
)
from apps.portfolio.models import CaseStudy


class SystemType(Publishable, Ordered):
    name = models.CharField(max_length=160)
    slug = models.SlugField(max_length=180, unique=True, validators=[validate_slug_is_english])
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=40, blank=True, validators=[validate_icon_name])

    class Meta(Ordered.Meta):
        pass

    def __str__(self):
        return self.name


class DatabaseCapability(Publishable, Ordered):
    name = models.CharField(max_length=160)
    slug = models.SlugField(max_length=180, unique=True, validators=[validate_slug_is_english])
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=40, blank=True, validators=[validate_icon_name])

    class Meta(Ordered.Meta):
        verbose_name_plural = "Database capabilities"

    def __str__(self):
        return self.name


class CustomSoftwareCaseStudy(CaseStudy):
    service_key = "custom-software"

    class Meta:
        proxy = True
        verbose_name = "Case study"
        verbose_name_plural = "Case studies"
