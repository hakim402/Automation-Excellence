from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.core.models import (
    Ordered,
    Publishable,
    TimeStamped,
    validate_slug_is_english,
)
from apps.core.uploads import (
    ALLOWED_IMAGE_EXTENSIONS,
    ALLOWED_VIDEO_EXTENSIONS,
    UploadTo,
    validate_image_file,
    validate_media_file,
    validate_upload_size,
)
from apps.portfolio.models import CaseStudy

SOCIAL_PLATFORMS = [
    ("facebook", "Facebook"),
    ("instagram", "Instagram"),
    ("youtube", "YouTube"),
    ("tiktok", "TikTok"),
    ("linkedin", "LinkedIn"),
    ("x", "X"),
    ("google", "Google"),
    ("other", "Other"),
]


class Campaign(Publishable, Ordered):
    title = models.CharField(max_length=180)
    slug = models.SlugField(max_length=180, unique=True, validators=[validate_slug_is_english])
    client_name = models.CharField(max_length=160)
    objective = models.TextField()
    summary = models.TextField()
    results = models.TextField(blank=True)
    platforms = ArrayField(
        models.CharField(max_length=20, choices=SOCIAL_PLATFORMS), default=list, blank=True
    )
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    cover_image = models.ImageField(
        upload_to=UploadTo("campaigns"),
        validators=[validate_upload_size, validate_image_file],
        blank=True,
    )
    reach = models.PositiveBigIntegerField(null=True, blank=True)
    engagement_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Percentage, 0 to 100. Leave empty when unknown.",
    )
    conversions = models.PositiveIntegerField(null=True, blank=True)
    is_featured = models.BooleanField(default=False, db_index=True)

    class Meta(Ordered.Meta):
        pass

    def clean(self):
        super().clean()
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValidationError({"end_date": "End date must be on or after the start date."})

    def __str__(self):
        return self.title


class SocialChannel(TimeStamped, Ordered):
    platform = models.CharField(max_length=20, choices=SOCIAL_PLATFORMS)
    slug = models.SlugField(max_length=180, unique=True, validators=[validate_slug_is_english])
    handle = models.CharField(max_length=160)
    url = models.URLField()
    follower_count = models.PositiveBigIntegerField(null=True, blank=True)
    is_managed_for_clients = models.BooleanField(default=False)

    class Meta(Ordered.Meta):
        pass

    def __str__(self):
        return f"{self.get_platform_display()} — {self.handle}"


class CreativeWork(Publishable, Ordered):
    kind = models.CharField(
        max_length=20,
        choices=[
            ("video", "Video"),
            ("poster", "Poster"),
            ("graphic", "Graphic"),
            ("reel", "Reel"),
            ("banner", "Banner"),
            ("motion", "Motion"),
        ],
    )
    title = models.CharField(max_length=180)
    slug = models.SlugField(max_length=180, unique=True, validators=[validate_slug_is_english])
    description = models.TextField(blank=True)
    thumbnail = models.ImageField(
        upload_to=UploadTo("creative/thumbnails"),
        validators=[validate_upload_size, validate_image_file],
        blank=True,
    )
    file = models.FileField(
        upload_to=UploadTo("creative", ALLOWED_IMAGE_EXTENSIONS | ALLOWED_VIDEO_EXTENSIONS),
        validators=[validate_upload_size, validate_media_file],
        blank=True,
    )
    external_url = models.URLField(blank=True)
    client_name = models.CharField(max_length=160, blank=True)

    class Meta(Ordered.Meta):
        pass

    def clean(self):
        super().clean()
        if self.file and self.external_url:
            raise ValidationError("Choose an uploaded file or an external URL, not both.")
        if self.status == "published" and not (self.file or self.external_url):
            raise ValidationError("Add a file or external URL before publishing.")

    def __str__(self):
        return self.title


class DigitalMarketingCaseStudy(CaseStudy):
    service_key = "digital-marketing"

    class Meta:
        proxy = True
        verbose_name = "Case study"
        verbose_name_plural = "Case studies"
