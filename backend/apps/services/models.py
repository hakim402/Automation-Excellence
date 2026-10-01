"""
The six service lines and the content that fills a service page.

One Service row per service line, with offerings, process steps and FAQs
hanging off it. These four models are shared by all six services rather than
duplicated per service: the admin reads as six sections because the sidebar
is grouped that way, not because the schema is (BUILD_PROMPT.md design note).
"""

from django.db import models

from apps.core.models import (
    Ordered,
    Publishable,
    PublishableQuerySet,
    RichTextSanitised,
    SEOFields,
    TimeStamped,
    TranslationTracked,
    validate_icon_name,
    validate_slug_is_english,
)
from apps.core.uploads import UploadTo, validate_upload_size


class ServiceKey(models.TextChoices):
    """
    The six service lines. Values match the public URL slugs, so a template
    or a serializer can go from key to route without a lookup table.
    """

    DIGITAL_MARKETING = "digital-marketing", "Digital Marketing"
    AI_AUTOMATION = "ai-automation", "AI & Automation"
    CUSTOM_SOFTWARE = "custom-software", "Custom Software Development"
    WEB_DEVELOPMENT = "web-development", "Web App Development"
    MOBILE_DEVELOPMENT = "mobile-development", "Mobile App Development"
    CYBER_SECURITY = "cyber-security", "Cyber Security"


class ServiceQuerySet(PublishableQuerySet):
    def published(self):
        return super().published().filter(is_active=True)


class Service(RichTextSanitised, Publishable, SEOFields, Ordered):
    """
    One of the six service lines.

    Publishing and translation review use the shared gate. is_active is an
    additional switch for temporarily withdrawing a service.
    """

    rich_text_fields = ("body",)
    objects = models.Manager.from_queryset(ServiceQuerySet)()

    @property
    def is_published(self) -> bool:
        return self.is_active and super().is_published

    key = models.CharField(
        max_length=32,
        choices=ServiceKey.choices,
        unique=True,
        help_text="Fixed identifier for this service line. Do not change it after launch.",
    )
    name = models.CharField(max_length=80)
    slug = models.SlugField(
        max_length=90,
        unique=True,
        validators=[validate_slug_is_english],
        help_text=(
            "URL segment, English in every language: /ar/cyber-security. "
            "Changing it breaks existing links and search rankings."
        ),
    )
    icon = models.CharField(max_length=40, blank=True, validators=[validate_icon_name])

    hero_headline = models.CharField(max_length=120, blank=True)
    hero_subline = models.CharField(max_length=240, blank=True)
    hero_image = models.ImageField(
        upload_to=UploadTo("services"), validators=[validate_upload_size], blank=True
    )

    intro = models.TextField(
        blank=True,
        help_text="One short paragraph under the hero. Plain text.",
    )
    body = models.TextField(
        blank=True,
        help_text="Long-form explanation. Formatting allowed.",
    )

    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Turn off to pull this service from the public site.",
    )

    tools = models.ManyToManyField(
        "core.Tool", blank=True, related_name="services", help_text="The stack shown on the page."
    )
    industries = models.ManyToManyField("core.Industry", blank=True, related_name="services")

    class Meta(Ordered.Meta):
        pass

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        # The slug and the key are the same string in practice. Defaulting it
        # means one less field an admin can get wrong, while leaving it
        # editable for the rare case where a URL must differ from the key.
        if not self.slug and self.key:
            self.slug = self.key
        super().save(*args, **kwargs)


class ServiceOffering(TimeStamped, TranslationTracked, Ordered):
    """A "what we do" card on a service page."""

    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name="offerings")
    title = models.CharField(max_length=120)
    description = models.TextField(help_text="Two or three sentences. Plain text.")
    icon = models.CharField(max_length=40, blank=True, validators=[validate_icon_name])

    class Meta(Ordered.Meta):
        pass

    def __str__(self) -> str:
        return f"{self.service.name}: {self.title}"


class ProcessStep(TimeStamped, TranslationTracked, Ordered):
    """
    One step in "how we work".

    This is a genuine sequence, so the frontend is allowed to number it —
    unlike the decorative 01/02/03 markers CLAUDE.md section 8 rules out.
    """

    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name="process_steps")
    title = models.CharField(max_length=120)
    description = models.TextField(help_text="What happens at this step. Plain text.")

    class Meta(Ordered.Meta):
        verbose_name = "Process step"

    def __str__(self) -> str:
        return f"{self.service.name} step {self.order}: {self.title}"


class FAQ(RichTextSanitised, TimeStamped, TranslationTracked, Ordered):
    """
    A question and answer. A null service means a general, site-wide FAQ.

    The answer takes links and lists only — a heading inside an accordion
    panel breaks the page's document outline, which costs us in search.
    """

    rich_text_fields = ("answer",)
    rich_text_profiles = {"answer": "faq"}

    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="faqs",
        help_text="Leave empty for a general FAQ not tied to one service.",
    )
    question = models.CharField(max_length=200)
    answer = models.TextField(help_text="Links and lists allowed. No headings, no images.")

    class Meta(Ordered.Meta):
        verbose_name = "FAQ"
        verbose_name_plural = "FAQs"

    def __str__(self) -> str:
        return self.question
