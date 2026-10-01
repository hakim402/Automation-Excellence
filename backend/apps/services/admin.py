"""
Admin for the six service lines.

A service page is edited from one screen: the service's own fields in
language tabs, with its offerings, process steps and FAQs as inlines
underneath. That mirrors how the page is read, so an admin filling in
"Cyber Security" does not have to visit four changelists to finish the job.

The same models also get flat changelists under the Services sidebar group,
for the times someone wants to scan every FAQ at once.
"""

from django.contrib import admin
from unfold.admin import ModelAdmin, StackedInline
from unfold.decorators import display

from apps.core.admin_mixins import (
    LanguageTabsMixin,
    TranslationStatusMixin,
    image_preview,
)

from .models import FAQ, ProcessStep, Service, ServiceOffering


class ServiceOfferingInline(StackedInline):
    """The "what we do" cards."""

    model = ServiceOffering
    extra = 0
    fields = ("order", "icon", "title", "description")
    ordering = ("order",)
    verbose_name = "Offering"
    verbose_name_plural = "Offerings — the 'what we do' cards"
    classes = ("collapse",)


class ProcessStepInline(StackedInline):
    """How we work. A real sequence, so `order` is the step number."""

    model = ProcessStep
    extra = 0
    fields = ("order", "title", "description")
    ordering = ("order",)
    verbose_name = "Process step"
    verbose_name_plural = "Process — shown as a numbered sequence"
    classes = ("collapse",)


class FAQInline(StackedInline):
    model = FAQ
    extra = 0
    fields = ("order", "question", "answer")
    ordering = ("order",)
    verbose_name = "FAQ"
    verbose_name_plural = "FAQs for this service"
    classes = ("collapse",)


@admin.register(Service)
class ServiceAdmin(LanguageTabsMixin, TranslationStatusMixin, ModelAdmin):
    hero_image_preview = image_preview("hero_image", height=160)
    og_image_preview = image_preview("og_image")

    # Prose first, search metadata last — the order a translator reads in.
    translated_field_order = (
        "name",
        "hero_headline",
        "hero_subline",
        "intro",
        "body",
        "meta_title",
        "meta_description",
    )

    list_display = ("name", "slug", "is_active", "content_summary", "translation_badge", "order")
    list_filter = ("is_active", "translation_status")
    list_editable = ("order",)
    search_fields = ("name", "slug", "key")
    filter_horizontal = ("tools", "industries")
    readonly_fields = ("hero_image_preview", "og_image_preview", "created_at", "updated_at")
    inlines = (ServiceOfferingInline, ProcessStepInline, FAQInline)

    shared_fieldsets = (
        (
            "Identity",
            {
                "fields": ("key", "slug", "icon", "order", "is_active"),
                "description": (
                    "The slug is the URL segment and stays English in every language "
                    "(/ar/cyber-security). Changing it after launch breaks links."
                ),
            },
        ),
        # Unfold always renders tab fieldsets after the untabbed ones, so
        # everything left open here pushes the language tabs -- the part an
        # editor actually works in -- further down the page. Only Identity
        # stays open; the set-once fieldsets collapse to a single bar each.
        (
            "Hero image",
            {"fields": ("hero_image", "hero_image_preview"), "classes": ("collapse",)},
        ),
        (
            "Tools and industries",
            {"fields": ("tools", "industries"), "classes": ("collapse",)},
        ),
        (
            "Search",
            {
                "fields": ("og_image", "og_image_preview", "noindex", "translation_status"),
                "description": "Title and description are per-language, in the tabs below.",
                "classes": ("collapse",),
            },
        ),
        (
            "History",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("offerings", "process_steps", "faqs")

    @display(description="Content")
    def content_summary(self, obj) -> str:
        """
        How filled-in this service is, at a glance.

        The whole point of the redesign is that a visitor can find things, so
        an admin needs to see which service pages are still thin.
        """
        return (
            f"{obj.offerings.count()} offerings · "
            f"{obj.process_steps.count()} steps · "
            f"{obj.faqs.count()} FAQs"
        )


@admin.register(ServiceOffering)
class ServiceOfferingAdmin(LanguageTabsMixin, TranslationStatusMixin, ModelAdmin):
    list_display = ("title", "service", "translation_badge", "order")
    list_filter = ("service", "translation_status")
    list_editable = ("order",)
    search_fields = ("title",)
    autocomplete_fields = ("service",)
    shared_fieldsets = ((None, {"fields": ("service", "icon", "order", "translation_status")}),)


@admin.register(ProcessStep)
class ProcessStepAdmin(LanguageTabsMixin, TranslationStatusMixin, ModelAdmin):
    list_display = ("title", "service", "order", "translation_badge")
    list_filter = ("service", "translation_status")
    list_editable = ("order",)
    search_fields = ("title",)
    autocomplete_fields = ("service",)
    shared_fieldsets = (
        (
            None,
            {
                "fields": ("service", "order", "translation_status"),
                "description": "Order is the step number shown on the page.",
            },
        ),
    )


@admin.register(FAQ)
class FAQAdmin(LanguageTabsMixin, TranslationStatusMixin, ModelAdmin):
    list_display = ("question", "service_label", "translation_badge", "order")
    list_filter = ("service", "translation_status")
    list_editable = ("order",)
    search_fields = ("question", "answer")
    autocomplete_fields = ("service",)
    shared_fieldsets = (
        (
            None,
            {
                "fields": ("service", "order", "translation_status"),
                "description": (
                    "Leave the service empty for a general FAQ. "
                    "Answers take links and lists only — no headings or images."
                ),
            },
        ),
    )

    @display(description="Service", ordering="service__name")
    def service_label(self, obj) -> str:
        return obj.service.name if obj.service else "General"
