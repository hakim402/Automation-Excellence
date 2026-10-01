"""
Shared abstract bases and the site-wide content models.

Everything a visitor can see inherits from the abstracts at the top of this
file, so publishing, timestamps, SEO and translation state behave identically
across every app.
"""

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.db import models
from django.utils import timezone
from modeltranslation.utils import build_localized_fieldname

from .sanitize import clean_html
from .uploads import UploadTo, validate_upload_size

# ---------------------------------------------------------------------------
# Choices
# ---------------------------------------------------------------------------


class PublishStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    PUBLISHED = "published", "Published"


class TranslationStatus(models.TextChoices):
    NONE = "none", "Not translated"
    MACHINE = "machine", "Machine translated"
    REVIEWED = "reviewed", "Reviewed by a human"


class ToolCategory(models.TextChoices):
    MARKETING = "marketing", "Marketing"
    AI = "ai", "AI"
    BACKEND = "backend", "Backend"
    FRONTEND = "frontend", "Frontend"
    MOBILE = "mobile", "Mobile"
    SECURITY = "security", "Security"
    DATA = "data", "Data"
    CLOUD = "cloud", "Cloud"


# ---------------------------------------------------------------------------
# Validators shared across apps
# ---------------------------------------------------------------------------

# Icons are Material Symbols names, which is the set Unfold already ships for
# the admin sidebar. Storing a name rather than uploading an image keeps
# stroke weight and colour consistent and costs no media requests.
validate_icon_name = RegexValidator(
    regex=r"^[a-z0-9_]+$",
    message="Use a Material Symbols name in lower_snake_case, e.g. shield_lock.",
)

validate_slug_is_english = RegexValidator(
    regex=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
    message="Lower-case English words separated by single hyphens.",
)


# ---------------------------------------------------------------------------
# Abstracts
# ---------------------------------------------------------------------------


class TimeStamped(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class TranslationTracked(models.Model):
    """
    Carries the review state of a record's non-English fields.

    Split out of Publishable because Service gates visibility on `is_active`
    rather than on `status`, yet still needs a translation state for the Groq
    pipeline and the admin's status badge. Anything translatable inherits
    this; only things with a draft/published lifecycle inherit Publishable.
    """

    translation_status = models.CharField(
        max_length=16,
        choices=TranslationStatus.choices,
        default=TranslationStatus.NONE,
        db_index=True,
        help_text=(
            "Set to 'Machine translated' by the auto-translate action. "
            "A human sets it to 'Reviewed' after checking the wording."
        ),
    )

    class Meta:
        abstract = True

    @property
    def needs_translation_review(self) -> bool:
        return self.translation_status == TranslationStatus.MACHINE


class PublishableQuerySet(models.QuerySet):
    def published(self):
        """Only rows the public API may serve."""
        return self.filter(status=PublishStatus.PUBLISHED).exclude(
            translation_status=TranslationStatus.MACHINE
        )

    def drafts(self):
        return self.filter(status=PublishStatus.DRAFT)

    def awaiting_translation_review(self):
        return self.filter(translation_status=TranslationStatus.MACHINE)


class Publishable(TimeStamped, TranslationTracked):
    """
    Draft/published lifecycle.

    The default manager returns everything so the admin can see drafts;
    `objects.published()` is the gate every API view uses without exception
    (CLAUDE.md section 5).
    """

    status = models.CharField(
        max_length=16,
        choices=PublishStatus.choices,
        default=PublishStatus.DRAFT,
        db_index=True,
        help_text="Only published rows are served to the public site.",
    )
    published_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Set automatically the first time this is published.",
    )

    objects = models.Manager.from_queryset(PublishableQuerySet)()

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        # Stamp the first publication and then leave it alone, so a later
        # edit or unpublish does not rewrite history or move sitemap lastmod.
        if self.status == PublishStatus.PUBLISHED and self.published_at is None:
            self.published_at = timezone.now()
            if kwargs.get("update_fields") is not None:
                kwargs["update_fields"] = set(kwargs["update_fields"]) | {"published_at"}
        super().save(*args, **kwargs)

    @property
    def is_published(self) -> bool:
        return (
            self.status == PublishStatus.PUBLISHED
            and self.translation_status != TranslationStatus.MACHINE
        )


class SEOFields(models.Model):
    """
    Per-page search metadata. meta_title and meta_description are
    translatable; the image and the noindex switch are not.
    """

    meta_title = models.CharField(
        max_length=70,
        blank=True,
        help_text="Falls back to the page title. Around 60 characters reads best in results.",
    )
    meta_description = models.CharField(
        max_length=170,
        blank=True,
        help_text="Around 155 characters. Falls back to the intro.",
    )
    og_image = models.ImageField(
        upload_to=UploadTo("og"),
        validators=[validate_upload_size],
        blank=True,
        help_text="Social sharing image. 1200x630 works everywhere.",
    )
    noindex = models.BooleanField(
        default=False,
        help_text="Ask search engines not to index this page. Leave off unless you mean it.",
    )

    class Meta:
        abstract = True


class Ordered(models.Model):
    """Explicit display order. Lower numbers come first."""

    order = models.PositiveIntegerField(default=0, db_index=True)

    class Meta:
        abstract = True
        ordering = ["order", "pk"]


# ---------------------------------------------------------------------------
# Site-wide models
# ---------------------------------------------------------------------------


class SiteSettings(TimeStamped, TranslationTracked):
    """
    Singleton holding company facts and site-wide defaults.

    Enforced to a single row: the admin hides "add" once one exists, and
    `load()` is the only way code should read it.
    """

    SINGLETON_PK = 1

    company_name = models.CharField(max_length=120, default="Automex")
    tagline = models.CharField(max_length=180, blank=True)
    about_short = models.TextField(blank=True, help_text="Two or three sentences. Plain text.")

    logo = models.ImageField(
        upload_to=UploadTo("brand"), validators=[validate_upload_size], blank=True
    )
    logo_dark = models.ImageField(
        upload_to=UploadTo("brand"),
        validators=[validate_upload_size],
        blank=True,
        help_text="For light backgrounds. The site is dark-first, so this is the exception.",
    )
    favicon = models.ImageField(
        upload_to=UploadTo("brand"), validators=[validate_upload_size], blank=True
    )

    address_line_1 = models.CharField(max_length=160, blank=True)
    address_line_2 = models.CharField(max_length=160, blank=True)
    city = models.CharField(max_length=80, blank=True)
    state = models.CharField(max_length=80, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=80, blank=True)
    service_area = models.CharField(
        max_length=120, blank=True, help_text="Shown in LocalBusiness structured data."
    )

    phone_us = models.CharField("US phone", max_length=40, blank=True)
    phone_af = models.CharField(
        "Afghanistan phone",
        max_length=40,
        blank=True,
        help_text="Whether this is shown publicly is controlled by the switch below.",
    )
    show_phone_af_publicly = models.BooleanField(
        "Show the Afghanistan phone on the public site",
        default=False,
        help_text="PENDING A DECISION. Off means the number stays internal to this admin.",
    )
    email = models.EmailField(blank=True)
    domain = models.URLField(blank=True)

    # --- Not yet supplied by the client -----------------------------------
    founded_year = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1900), MaxValueValidator(2100)],
        help_text="NOT YET SUPPLIED. Leave empty rather than guessing.",
    )
    team_size = models.CharField(
        max_length=40,
        blank=True,
        help_text='NOT YET SUPPLIED. A range reads honestly, e.g. "10-20".',
    )

    linkedin_url = models.URLField(blank=True, help_text="NOT YET SUPPLIED.")
    x_url = models.URLField("X (Twitter) URL", blank=True, help_text="NOT YET SUPPLIED.")
    github_url = models.URLField(blank=True, help_text="NOT YET SUPPLIED.")
    instagram_url = models.URLField(blank=True, help_text="NOT YET SUPPLIED.")
    youtube_url = models.URLField(blank=True, help_text="NOT YET SUPPLIED.")
    facebook_url = models.URLField(blank=True, help_text="NOT YET SUPPLIED.")

    ga4_measurement_id = models.CharField(
        max_length=20, blank=True, help_text="Looks like G-XXXXXXXXXX."
    )

    default_meta_title = models.CharField(max_length=70, blank=True)
    default_meta_description = models.CharField(max_length=170, blank=True)
    default_og_image = models.ImageField(
        upload_to=UploadTo("og"), validators=[validate_upload_size], blank=True
    )

    class Meta:
        verbose_name = "Site settings"
        verbose_name_plural = "Site settings"

    def __str__(self) -> str:
        return f"{self.company_name} — site settings"

    def save(self, *args, **kwargs):
        self.pk = self.SINGLETON_PK

        # Forcing the pk means Django takes the UPDATE path even for a freshly
        # constructed instance, and auto_now_add does not fire on an update --
        # so created_at would be written as NULL. Carry the existing value
        # across, or start the clock if this really is the first save.
        if self.created_at is None:
            self.created_at = (
                type(self).objects.filter(pk=self.pk).values_list("created_at", flat=True).first()
                or timezone.now()
            )

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Deleting the settings row would break every page. Refuse."""
        raise models.ProtectedError("Site settings cannot be deleted.", {self})

    @classmethod
    def load(cls) -> "SiteSettings":
        return cls.objects.get_or_create(pk=cls.SINGLETON_PK)[0]

    @property
    def public_phone_af(self) -> str:
        """The Afghanistan number, or empty if it is meant to stay internal."""
        return self.phone_af if self.show_phone_af_publicly else ""


class Tool(TimeStamped, Ordered):
    """Something Automex builds with. Shown as a stack row, never translated."""

    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=90, unique=True, validators=[validate_slug_is_english])
    logo = models.ImageField(
        upload_to=UploadTo("tools"), validators=[validate_upload_size], blank=True
    )
    category = models.CharField(max_length=20, choices=ToolCategory.choices, db_index=True)
    url = models.URLField(blank=True)

    class Meta(Ordered.Meta):
        ordering = ["category", "order", "name"]

    def __str__(self) -> str:
        return self.name


class Industry(TimeStamped, TranslationTracked, Ordered):
    """A sector Automex sells into. Reused across services and case studies."""

    name = models.CharField(max_length=80)
    slug = models.SlugField(max_length=90, unique=True, validators=[validate_slug_is_english])
    icon = models.CharField(max_length=40, blank=True, validators=[validate_icon_name])
    description = models.CharField(max_length=200, blank=True)

    class Meta(Ordered.Meta):
        verbose_name_plural = "Industries"

    def __str__(self) -> str:
        return self.name


class Testimonial(Publishable, Ordered):
    client_name = models.CharField(max_length=120)
    client_role = models.CharField(max_length=120, blank=True)
    client_company = models.CharField(max_length=120, blank=True)
    company_logo = models.ImageField(
        upload_to=UploadTo("testimonials"), validators=[validate_upload_size], blank=True
    )
    quote = models.TextField(help_text="The client's words. Plain text.")
    rating = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="1 to 5. Leave empty to show no rating.",
    )
    service = models.ForeignKey(
        "services.Service",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="testimonials",
        help_text="Which service this is about. Leave empty for a general testimonial.",
    )
    is_featured = models.BooleanField(default=False, db_index=True)

    class Meta(Ordered.Meta):
        ordering = ["-is_featured", "order", "-created_at"]

    def __str__(self) -> str:
        if self.client_company:
            return f"{self.client_name}, {self.client_company}"
        return self.client_name


class TeamMember(TimeStamped, TranslationTracked, Ordered):
    name = models.CharField(max_length=120)
    role = models.CharField(max_length=120, blank=True)
    bio = models.TextField(blank=True, help_text="Plain text.")
    photo = models.ImageField(
        upload_to=UploadTo("team"), validators=[validate_upload_size], blank=True
    )
    linkedin = models.URLField(blank=True)
    github = models.URLField(blank=True)
    is_active = models.BooleanField(
        default=True, help_text="Turn off when someone leaves, rather than deleting them."
    )

    class Meta(Ordered.Meta):
        pass

    def __str__(self) -> str:
        return self.name


class Stat(TimeStamped, TranslationTracked, Ordered):
    """
    A single number shown on a service page or the home page.

    `value` is text, not a number, because the real ones read "3x", "99.9"
    and "24/7" as often as they read "40". The unit is kept separate so the
    frontend can style it.
    """

    label = models.CharField(max_length=80)
    value = models.CharField(max_length=32)
    unit = models.CharField(max_length=16, blank=True, help_text='e.g. "%", "x", "hrs".')
    service = models.ForeignKey(
        "services.Service",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="stats",
        help_text="Leave empty for a company-wide number shown on the home page.",
    )

    class Meta(Ordered.Meta):
        pass

    def __str__(self) -> str:
        return f"{self.value}{self.unit} {self.label}".strip()


# ---------------------------------------------------------------------------
# Rich text
# ---------------------------------------------------------------------------


class RichTextSanitised(models.Model):
    """
    Mixin that sanitises the fields named in `rich_text_fields` on every save.

    Sanitising on write rather than on read means the database never holds
    markup we would not serve, so a view that forgets to sanitise cannot
    reopen the hole. `rich_text_profiles` narrows the allowlist per field.
    """

    rich_text_fields: tuple[str, ...] = ()
    rich_text_profiles: dict[str, str] = {}

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        for field in self.rich_text_fields:
            profile = self.rich_text_profiles.get(field, "default")
            # Every locale's column is sanitised, not just the active one.
            for code, _ in settings.LANGUAGES:
                localised = build_localized_fieldname(field, code)
                if hasattr(self, localised):
                    setattr(self, localised, clean_html(getattr(self, localised), profile=profile))
            if hasattr(self, field):
                setattr(self, field, clean_html(getattr(self, field), profile=profile))

        super().save(*args, **kwargs)
