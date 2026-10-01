"""
Admin building blocks shared by every app.

The pieces here are what make the admin operable by a non-developer: one
form per record with a tab per language, a translation-status badge in every
list, and a visible thumbnail wherever an image is stored.
"""

from django.conf import settings
from django.utils.html import format_html
from modeltranslation.translator import NotRegistered, translator
from modeltranslation.utils import build_localized_fieldname
from unfold.decorators import display

from .models import PublishStatus, TranslationStatus

# Unfold's own semantic label colours. These are admin chrome, not the public
# design system, so they are deliberately not drawn from the brand tokens.
TRANSLATION_STATUS_COLOURS = {
    TranslationStatus.NONE: "",
    TranslationStatus.MACHINE: "warning",
    TranslationStatus.REVIEWED: "success",
}

PUBLISH_STATUS_COLOURS = {
    PublishStatus.DRAFT: "warning",
    PublishStatus.PUBLISHED: "success",
}


def translated_fields_for(model) -> tuple[str, ...]:
    """
    The model's translatable field names, in the order they are declared on
    the model rather than the arbitrary order modeltranslation stores them in.
    """
    try:
        options = translator.get_options_for_model(model)
    except NotRegistered:
        return ()

    # `options.fields` is a tuple of field names in arbitrary order, which is
    # exactly why the model's declaration order is reapplied below.
    registered = set(options.fields)
    declared = [f.name for f in model._meta.get_fields() if getattr(f, "name", None) in registered]
    return tuple(dict.fromkeys(declared))


def image_preview(field_name: str, *, height: int = 120, description: str | None = None):
    """
    Builds a read-only admin field that renders the stored image.

    Used on change forms so an admin can see what is already uploaded rather
    than inferring it from a filename:

        logo_preview = image_preview("logo")
        readonly_fields = ("logo_preview",)
    """

    def preview(_model_admin, obj=None) -> str:
        return render_image(getattr(obj, field_name, None) if obj else None, height=height)

    preview.short_description = description or f"Current {field_name.replace('_', ' ')}"
    return preview


def render_image(image, *, height: int) -> str:
    if not image:
        return format_html('<span class="text-base-400">Nothing uploaded</span>')
    return format_html(
        '<img src="{}" alt="" loading="lazy" '
        'style="height:{}px;width:auto;border-radius:4px;background:#0e4553;padding:2px" />',
        image.url,
        height,
    )


class LanguageTabsMixin:
    """
    Renders one Unfold tab per locale, English first.

    Each tab holds every translatable field for that language, so a
    translator works down one column instead of hunting for the Spanish
    version of a field between the German and Arabic ones. Untranslated
    fields -- slugs, images, ordering, relations -- sit above the tabs
    because all six languages share them.

    Unfold puts a validation-error count on each tab, so a required field
    left empty in Arabic is visible without opening the Arabic tab.

    Subclasses declare `shared_fieldsets` rather than `fieldsets`.
    """

    #: Fieldsets for the untranslated fields. Same shape as `fieldsets`.
    shared_fieldsets: tuple = ()

    #: Optional field order inside each language tab. Fields inherited from an
    #: abstract base (meta_title and friends) otherwise sort ahead of the
    #: model's own, which puts search metadata above the headline. Any
    #: translatable field left out of this list is appended rather than
    #: dropped, so adding one later cannot quietly hide it from translators.
    translated_field_order: tuple[str, ...] = ()

    def get_translated_fields(self) -> tuple[str, ...]:
        declared = translated_fields_for(self.model)

        if not self.translated_field_order:
            return declared

        preferred = [field for field in self.translated_field_order if field in declared]
        remainder = [field for field in declared if field not in preferred]
        return tuple(preferred + remainder)

    def get_fieldsets(self, request, obj=None):
        translated = self.get_translated_fields()

        if not translated:
            return super().get_fieldsets(request, obj)

        fieldsets = [
            (name, {**options, "fields": list(options.get("fields", ()))})
            for name, options in self.shared_fieldsets
        ]

        for code, label in settings.LANGUAGES:
            fields = [
                build_localized_fieldname(field, code)
                for field in translated
                if hasattr(self.model, build_localized_fieldname(field, code))
            ]
            if fields:
                fieldsets.append((label, {"fields": fields, "classes": ["tab"]}))

        return fieldsets

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        """
        Give right-to-left locales right-to-left inputs.

        Without this a translator types Arabic into a left-aligned box and
        cannot see the start of their own sentence. `lang` also lets the
        browser pick the right font and spellchecker.
        """
        formfield = super().formfield_for_dbfield(db_field, request, **kwargs)

        if formfield is None:
            return None

        for code, _label in settings.LANGUAGES:
            if db_field.name.endswith(f"_{code}"):
                formfield.widget.attrs["lang"] = code
                if code in settings.RTL_LANGUAGES:
                    formfield.widget.attrs["dir"] = "rtl"
                break

        return formfield


class TranslationStatusMixin:
    """Adds a coloured translation-status badge for `list_display`."""

    @display(
        description="Translation",
        label=TRANSLATION_STATUS_COLOURS,
        ordering="translation_status",
    )
    def translation_badge(self, obj) -> str:
        return obj.get_translation_status_display()


class PublishStatusMixin:
    """Adds a coloured publish-status badge for `list_display`."""

    @display(description="Status", label=PUBLISH_STATUS_COLOURS, ordering="status")
    def publish_badge(self, obj) -> str:
        return obj.get_status_display()
