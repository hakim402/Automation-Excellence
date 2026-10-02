"""
Admin for the site-wide models.

Every class extends unfold.admin.ModelAdmin (never Django's) so the theme
holds, and combines LanguageTabsMixin so the six locales appear as tabs on
one form.
"""

from django.contrib import admin
from django.http import HttpRequest, HttpResponseRedirect
from django.urls import reverse
from unfold.admin import ModelAdmin
from unfold.decorators import display

from .admin_mixins import (
    LanguageTabsMixin,
    PublishStatusMixin,
    TranslationStatusMixin,
    image_preview,
    render_image,
)
from .content_admin import ContentAdmin
from .models import Industry, SiteSettings, Stat, TeamMember, Testimonial, Tool, Video


@admin.register(SiteSettings)
class SiteSettingsAdmin(LanguageTabsMixin, TranslationStatusMixin, ModelAdmin):
    """
    The singleton. Add and delete are disabled, and the changelist redirects
    straight to the one row so an admin never sees a list of length one.
    """

    logo_preview = image_preview("logo")
    logo_dark_preview = image_preview("logo_dark")
    favicon_preview = image_preview("favicon", height=48)
    default_og_image_preview = image_preview("default_og_image")

    translated_field_order = (
        "tagline",
        "about_short",
        "response_time",
        "default_meta_title",
        "default_meta_description",
    )

    readonly_fields = (
        "logo_preview",
        "logo_dark_preview",
        "favicon_preview",
        "default_og_image_preview",
    )

    shared_fieldsets = (
        (
            "Identity",
            {
                "fields": ("company_name",),
                "description": (
                    "The tagline and the short description are per-language — see the tabs below."
                ),
            },
        ),
        (
            "Brand assets",
            {
                "fields": (
                    "logo",
                    "logo_preview",
                    "logo_dark",
                    "logo_dark_preview",
                    "favicon",
                    "favicon_preview",
                ),
            },
        ),
        (
            "Address",
            {
                "fields": (
                    "address_line_1",
                    "address_line_2",
                    "city",
                    "state",
                    "postal_code",
                    "country",
                    "service_area",
                ),
            },
        ),
        (
            "Contact",
            {
                "fields": (
                    "email",
                    "phone_us",
                    "phone_af",
                    "show_phone_af_publicly",
                    "domain",
                ),
            },
        ),
        (
            "Company facts",
            {
                "fields": ("founded_year", "team_size"),
                "description": (
                    "Not yet supplied by the client. Leave empty rather than estimating — "
                    "these appear in structured data that search engines read."
                ),
            },
        ),
        (
            "Social profiles",
            {
                "fields": (
                    "linkedin_url",
                    "x_url",
                    "github_url",
                    "instagram_url",
                    "youtube_url",
                    "facebook_url",
                ),
                "description": "Not yet supplied. Only filled-in profiles are shown on the site.",
                "classes": ("collapse",),
            },
        ),
        (
            "Analytics",
            {"fields": ("ga4_measurement_id",), "classes": ("collapse",)},
        ),
        (
            "Search defaults",
            {
                "fields": ("default_og_image", "default_og_image_preview", "translation_status"),
                "description": (
                    "Used on any page that does not set its own. "
                    "The title and description are per-language, below."
                ),
            },
        ),
    )

    def has_add_permission(self, request: HttpRequest) -> bool:
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request: HttpRequest, obj=None) -> bool:
        return False

    def changelist_view(self, request: HttpRequest, extra_context=None):
        settings_row = SiteSettings.load()
        return HttpResponseRedirect(
            reverse("admin:core_sitesettings_change", args=[settings_row.pk])
        )


@admin.register(Tool)
class ToolAdmin(ModelAdmin):
    """Not translatable — a tool's name is a product name."""

    logo_preview = image_preview("logo", height=64)

    list_display = ("logo_thumb", "name", "category", "order")
    list_display_links = ("logo_thumb", "name")
    list_filter = ("category",)
    list_editable = ("order",)
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("logo_preview",)
    fieldsets = (
        (None, {"fields": ("name", "slug", "category", "url", "order")}),
        ("Logo", {"fields": ("logo", "logo_preview")}),
    )

    @display(description="")
    def logo_thumb(self, obj) -> str:
        return render_image(obj.logo, height=24)


@admin.register(Industry)
class IndustryAdmin(LanguageTabsMixin, TranslationStatusMixin, ModelAdmin):
    list_display = ("name", "slug", "translation_badge", "order")
    list_editable = ("order",)
    list_filter = ("translation_status",)
    search_fields = ("name_en", "slug")
    prepopulated_fields = {"slug": ("name_en",)}
    shared_fieldsets = ((None, {"fields": ("slug", "icon", "order", "translation_status")}),)


@admin.register(Testimonial)
class TestimonialAdmin(LanguageTabsMixin, PublishStatusMixin, TranslationStatusMixin, ModelAdmin):
    company_logo_preview = image_preview("company_logo", height=64)

    list_display = (
        "client_name",
        "client_company",
        "service",
        "rating",
        "is_featured",
        "publish_badge",
        "translation_badge",
    )
    list_filter = ("status", "translation_status", "is_featured", "service")
    list_editable = ("is_featured",)
    search_fields = ("client_name", "client_company")
    autocomplete_fields = ("service",)
    readonly_fields = ("company_logo_preview", "published_at", "created_at")
    shared_fieldsets = (
        (
            "Client",
            {
                "fields": (
                    "client_name",
                    "client_company",
                    "company_logo",
                    "company_logo_preview",
                )
            },
        ),
        (
            "Placement",
            {"fields": ("service", "rating", "is_featured", "order")},
        ),
        (
            "Publishing",
            {"fields": ("status", "translation_status", "published_at", "created_at")},
        ),
    )


@admin.register(TeamMember)
class TeamMemberAdmin(LanguageTabsMixin, TranslationStatusMixin, ModelAdmin):
    photo_preview = image_preview("photo")

    list_display = ("photo_thumb", "name", "is_active", "translation_badge", "order")
    list_display_links = ("photo_thumb", "name")
    list_filter = ("is_active", "translation_status")
    list_editable = ("order",)
    search_fields = ("name",)
    readonly_fields = ("photo_preview",)
    shared_fieldsets = (
        (None, {"fields": ("name", "is_active", "order", "translation_status")}),
        ("Photo", {"fields": ("photo", "photo_preview")}),
        ("Links", {"fields": ("linkedin", "github")}),
    )

    @display(description="")
    def photo_thumb(self, obj) -> str:
        return render_image(obj.photo, height=28)


@admin.register(Stat)
class StatAdmin(LanguageTabsMixin, TranslationStatusMixin, ModelAdmin):
    list_display = ("__str__", "service", "translation_badge", "order")
    list_filter = ("service", "translation_status")
    list_editable = ("order",)
    search_fields = ("label_en",)
    autocomplete_fields = ("service",)
    shared_fieldsets = (
        (
            None,
            {
                "fields": ("value", "unit", "service", "order", "translation_status"),
                "description": (
                    'The value is free text so "3x", "99.9" and "24/7" all work. '
                    "Leave the service empty for a company-wide number."
                ),
            },
        ),
    )


@admin.register(Video)
class VideoAdmin(ContentAdmin):
    list_display = (
        "title",
        "orientation",
        "source",
        "publish_badge",
        "translation_badge",
        "is_featured",
        "order",
    )
    list_filter = ("orientation", "source", "status", "translation_status", "is_featured")
    search_fields = ("title_en", "slug")
    prepopulated_fields = {"slug": ("title_en",)}
    autocomplete_fields = ("service", "product", "case_study")
