from django.contrib.postgres.fields import ArrayField
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.core.models import (
    Ordered,
    Publishable,
    TimeStamped,
    TranslationTracked,
    validate_slug_is_english,
)
from apps.core.uploads import (
    UploadTo,
    validate_image_file,
    validate_upload_size,
)
from apps.portfolio.models import CaseStudy


class MobileApp(Publishable, Ordered):
    name = models.CharField(max_length=160)
    slug = models.SlugField(max_length=180, unique=True, validators=[validate_slug_is_english])
    client_name = models.CharField(max_length=160, blank=True)
    platforms = ArrayField(
        models.CharField(max_length=10, choices=[("ios", "iOS"), ("android", "Android")]),
        default=list,
    )
    description = models.TextField()
    features = models.TextField(blank=True, help_text="Plain text: one feature per line.")
    app_store_url = models.URLField(blank=True)
    play_store_url = models.URLField(blank=True)
    icon_image = models.ImageField(
        upload_to=UploadTo("mobile/icons"),
        validators=[validate_upload_size, validate_image_file],
        blank=True,
    )
    downloads = models.PositiveBigIntegerField(null=True, blank=True)
    rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(5)],
    )

    class Meta(Ordered.Meta):
        pass

    def __str__(self):
        return self.name


class MobileAppScreenshot(TimeStamped, TranslationTracked, Ordered):
    app = models.ForeignKey(MobileApp, on_delete=models.CASCADE, related_name="screenshots")
    image = models.ImageField(
        upload_to=UploadTo("mobile/screenshots"),
        validators=[validate_upload_size, validate_image_file],
        blank=False,
    )
    caption = models.CharField(max_length=240, blank=True)

    class Meta(Ordered.Meta):
        pass

    def __str__(self):
        return self.caption or f"{self.app} — screenshot {self.order}"


class MobileDevelopmentCaseStudy(CaseStudy):
    service_key = "mobile-development"

    class Meta:
        proxy = True
        verbose_name = "Case study"
        verbose_name_plural = "Case studies"
