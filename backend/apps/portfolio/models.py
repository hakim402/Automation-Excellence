from django.db import models

from apps.core.models import (
    Ordered,
    Publishable,
    RichTextSanitised,
    SEOFields,
    TimeStamped,
    TranslationTracked,
    validate_slug_is_english,
)
from apps.core.uploads import (
    UploadTo,
    validate_image_file,
    validate_upload_size,
)


class CaseStudy(RichTextSanitised, Publishable, SEOFields, Ordered):
    rich_text_fields = ("challenge", "solution", "outcome")
    service = models.ForeignKey(
        "services.Service", on_delete=models.PROTECT, related_name="case_studies"
    )
    title = models.CharField(max_length=180)
    slug = models.SlugField(max_length=180, unique=True, validators=[validate_slug_is_english])
    client_name = models.CharField(max_length=160)
    client_logo = models.ImageField(
        upload_to=UploadTo("portfolio/logos"),
        validators=[validate_upload_size, validate_image_file],
        blank=True,
    )
    industry = models.ForeignKey(
        "core.Industry",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="case_studies",
    )
    country = models.CharField(max_length=100, blank=True)
    challenge = models.TextField()
    solution = models.TextField()
    outcome = models.TextField()
    cover_image = models.ImageField(
        upload_to=UploadTo("portfolio"),
        validators=[validate_upload_size, validate_image_file],
        blank=True,
    )
    project_url = models.URLField(blank=True)
    duration_months = models.PositiveSmallIntegerField(null=True, blank=True)
    tech_stack = models.ManyToManyField("core.Tool", blank=True, related_name="case_studies")
    is_featured = models.BooleanField(default=False, db_index=True)

    class Meta(Ordered.Meta):
        verbose_name_plural = "Case studies"

    def __str__(self):
        return self.title


class CaseStudyMetric(TimeStamped, TranslationTracked, Ordered):
    case_study = models.ForeignKey(CaseStudy, on_delete=models.CASCADE, related_name="metrics")
    label = models.CharField(max_length=120)
    value = models.CharField(max_length=40)
    unit = models.CharField(max_length=30, blank=True)

    class Meta(Ordered.Meta):
        pass

    def __str__(self):
        return f"{self.label}: {self.value}{self.unit}"


class CaseStudyImage(TimeStamped, TranslationTracked, Ordered):
    case_study = models.ForeignKey(CaseStudy, on_delete=models.CASCADE, related_name="gallery")
    image = models.ImageField(
        upload_to=UploadTo("portfolio/gallery"),
        validators=[validate_upload_size, validate_image_file],
        blank=False,
    )
    caption = models.CharField(max_length=240, blank=True)

    class Meta(Ordered.Meta):
        pass

    def __str__(self):
        return self.caption or f"{self.case_study} — image {self.order}"
