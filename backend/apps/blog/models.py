from django.core.validators import MinValueValidator
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


class Category(TimeStamped, TranslationTracked, Ordered):
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=180, unique=True, validators=[validate_slug_is_english])
    description = models.TextField(blank=True)

    class Meta(Ordered.Meta):
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name


class Tag(TimeStamped, TranslationTracked, Ordered):
    name = models.CharField(max_length=80)
    slug = models.SlugField(max_length=180, unique=True, validators=[validate_slug_is_english])

    class Meta(Ordered.Meta):
        pass

    def __str__(self):
        return self.name


class Post(RichTextSanitised, Publishable, SEOFields):
    rich_text_fields = ("body",)
    title = models.CharField(max_length=180)
    slug = models.SlugField(max_length=180, unique=True, validators=[validate_slug_is_english])
    excerpt = models.TextField()
    body = models.TextField()
    cover_image = models.ImageField(
        upload_to=UploadTo("blog"),
        validators=[validate_upload_size, validate_image_file],
        blank=True,
    )
    author = models.ForeignKey("core.TeamMember", on_delete=models.PROTECT, related_name="posts")
    service = models.ForeignKey(
        "services.Service", on_delete=models.SET_NULL, null=True, blank=True, related_name="posts"
    )
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="posts")
    tags = models.ManyToManyField(Tag, blank=True, related_name="posts")
    reading_minutes = models.PositiveSmallIntegerField(default=1, validators=[MinValueValidator(1)])
    is_featured = models.BooleanField(default=False, db_index=True)

    class Meta:
        ordering = ["-published_at", "-created_at"]

    def __str__(self):
        return self.title
