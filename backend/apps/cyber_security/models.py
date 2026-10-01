from django.db import models

from apps.core.models import (
    Ordered,
    Publishable,
    validate_icon_name,
    validate_slug_is_english,
)
from apps.core.uploads import (
    UploadTo,
    validate_image_file,
    validate_upload_size,
)
from apps.portfolio.models import CaseStudy


class SecurityService(Publishable, Ordered):
    name = models.CharField(max_length=160)
    slug = models.SlugField(max_length=180, unique=True, validators=[validate_slug_is_english])
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=40, blank=True, validators=[validate_icon_name])

    class Meta(Ordered.Meta):
        pass

    def __str__(self):
        return self.name


class ComplianceStandard(Publishable, Ordered):
    name = models.CharField(max_length=160)
    slug = models.SlugField(max_length=180, unique=True, validators=[validate_slug_is_english])
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=40, blank=True, validators=[validate_icon_name])
    logo = models.ImageField(
        upload_to=UploadTo("compliance"),
        validators=[validate_upload_size, validate_image_file],
        blank=True,
    )

    class Meta(Ordered.Meta):
        pass

    def __str__(self):
        return self.name


class Certification(Publishable, Ordered):
    name = models.CharField(max_length=160)
    slug = models.SlugField(max_length=180, unique=True, validators=[validate_slug_is_english])

    icon = models.CharField(max_length=40, blank=True, validators=[validate_icon_name])
    issuer = models.CharField(max_length=160)
    logo = models.ImageField(
        upload_to=UploadTo("certifications"),
        validators=[validate_upload_size, validate_image_file],
        blank=True,
    )
    credential_url = models.URLField(blank=True)

    class Meta(Ordered.Meta):
        pass

    def __str__(self):
        return self.name


class CyberSecurityCaseStudy(CaseStudy):
    service_key = "cyber-security"

    class Meta:
        proxy = True
        verbose_name = "Case study"
        verbose_name_plural = "Case studies"
