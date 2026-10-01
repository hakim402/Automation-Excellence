"""Shared form layout for Phase 2 content; model admins declare their own lists."""

from types import MethodType

from django import forms
from django.contrib.postgres.fields import ArrayField
from django.db import models
from unfold.admin import ModelAdmin, StackedInline
from unfold.widgets import UnfoldAdminCheckboxSelectMultipleWidget

from .admin_mixins import (
    LanguageTabsMixin,
    PublishStatusMixin,
    TranslationStatusMixin,
    image_preview,
)


class ContentFieldsMixin(LanguageTabsMixin):
    show_history = True
    translated_field_order = (
        "name",
        "title",
        "tagline",
        "summary",
        "description",
        "objective",
        "results",
        "challenge",
        "solution",
        "outcome",
        "excerpt",
        "body",
        "example_prompt",
        "features",
        "caption",
        "label",
    )

    def __init__(self, model, admin_site):
        super().__init__(model, admin_site)
        model = self.model  # InlineModelAdmin receives its parent in __init__.
        translated = set(self.get_translated_fields())
        shared, media, publishing, history = [], [], [], []
        relationships, links = [], []
        readonly = list(self.readonly_fields)
        excluded = set(self.exclude or ())
        if isinstance(self, StackedInline):
            excluded.update(
                f.name
                for f in model._meta.fields
                if f.many_to_one
                and f.related_model._meta.concrete_model is self.parent_model._meta.concrete_model
            )
        for field in [*model._meta.fields, *model._meta.many_to_many]:
            name = field.name
            if (
                field.primary_key
                or name in excluded
                or name in translated
                or hasattr(field, "translated_field")
            ):
                continue
            if name in ("created_at", "updated_at", "published_at"):
                if self.show_history:
                    history.append(name)
                    readonly.append(name)
            elif name in ("status", "translation_status", "is_active"):
                publishing.append(name)
            elif isinstance(field, models.ImageField):
                preview = f"{name}_preview"
                setattr(self, preview, MethodType(image_preview(name), self))
                readonly.append(preview)
                media.extend([name, preview])
            elif field.many_to_many or (field.many_to_one and field.blank):
                relationships.append(name)
            elif isinstance(field, models.URLField) and field.blank:
                links.append(name)
            else:
                shared.append(name)
        self.readonly_fields = tuple(dict.fromkeys(readonly))
        groups = [(None, {"fields": shared})]
        if relationships:
            groups.append(("Related content", {"fields": relationships, "classes": ("collapse",)}))
        if links:
            groups.append(("Links", {"fields": links, "classes": ("collapse",)}))
        if media:
            groups.append(("Images", {"fields": media, "classes": ("collapse",)}))
        if publishing:
            groups.append(("Publishing and review", {"fields": publishing}))
        if history:
            groups.append(("History", {"fields": history, "classes": ("collapse",)}))
        self.shared_fieldsets = tuple(groups)

    def get_fieldsets(self, request, obj=None):
        if not self.get_translated_fields():
            return self.shared_fieldsets
        return super().get_fieldsets(request, obj)

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if isinstance(db_field, ArrayField) and db_field.base_field.choices:
            return forms.MultipleChoiceField(
                choices=db_field.base_field.choices,
                required=not db_field.blank,
                widget=UnfoldAdminCheckboxSelectMultipleWidget,
                help_text=db_field.help_text,
                label=db_field.verbose_name.capitalize(),
            )
        return super().formfield_for_dbfield(db_field, request, **kwargs)


class ContentAdmin(ContentFieldsMixin, PublishStatusMixin, TranslationStatusMixin, ModelAdmin):
    list_display = ("__str__", "publish_badge", "translation_badge", "order")
    list_filter = ("status", "translation_status")
    search_fields = ("name_en", "slug")
    list_per_page = 30


class ContentInline(ContentFieldsMixin, StackedInline):
    template = "admin/core/translated_stacked.html"
    extra = 0
    show_history = False
    ordering = ("order",)
