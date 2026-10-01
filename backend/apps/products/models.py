from django.db import models

from apps.core.models import (
    Ordered,
    Publishable,
    RichTextSanitised,
    SEOFields,
    TimeStamped,
    TranslationTracked,
    validate_icon_name,
    validate_slug_is_english,
)
from apps.core.uploads import (
    UploadTo,
    validate_image_file,
    validate_upload_size,
)


class Product(RichTextSanitised, Publishable, SEOFields, Ordered):
    rich_text_fields = ("body",)
    name = models.CharField(max_length=160)
    slug = models.SlugField(max_length=180, unique=True, validators=[validate_slug_is_english])
    tagline = models.CharField(max_length=200, blank=True)
    category = models.CharField(
        max_length=20,
        choices=[
            ("database", "Database"),
            ("web-app", "Web app"),
            ("mobile-app", "Mobile app"),
            ("dashboard", "Dashboard"),
            ("automation", "Automation"),
            ("template", "Template"),
            ("integration", "Integration"),
        ],
        db_index=True,
    )
    summary = models.TextField()
    body = models.TextField(blank=True)
    cover_image = models.ImageField(
        upload_to=UploadTo("products"),
        validators=[validate_upload_size, validate_image_file],
        blank=True,
    )
    icon = models.CharField(max_length=40, blank=True, validators=[validate_icon_name])
    delivery = models.CharField(
        max_length=20,
        choices=[
            ("ready-to-deploy", "Ready to deploy"),
            ("customisable", "Customisable"),
            ("white-label", "White label"),
        ],
    )
    demo_url = models.URLField(blank=True)
    docs_url = models.URLField(blank=True)
    tech_stack = models.ManyToManyField("core.Tool", blank=True, related_name="products")
    services = models.ManyToManyField("services.Service", blank=True, related_name="products")
    industries = models.ManyToManyField("core.Industry", blank=True, related_name="products")
    is_featured = models.BooleanField(default=False, db_index=True)

    class Meta(Ordered.Meta):
        pass

    def __str__(self):
        return self.name


class ProductFeature(TimeStamped, TranslationTracked, Ordered):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="features")
    title = models.CharField(max_length=160)
    description = models.TextField()
    icon = models.CharField(max_length=40, blank=True, validators=[validate_icon_name])

    class Meta(Ordered.Meta):
        pass

    def __str__(self):
        return self.title


class ProductImage(TimeStamped, TranslationTracked, Ordered):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="gallery")
    image = models.ImageField(
        upload_to=UploadTo("products/gallery"),
        validators=[validate_upload_size, validate_image_file],
        blank=False,
    )
    caption = models.CharField(max_length=240, blank=True)

    class Meta(Ordered.Meta):
        pass

    def __str__(self):
        return self.caption or f"{self.product} — image {self.order}"
