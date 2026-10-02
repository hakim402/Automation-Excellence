from django.contrib import admin
from django.urls import NoReverseMatch, reverse
from django.utils.html import format_html
from unfold.admin import ModelAdmin
from unfold.decorators import display

from .client import CONFIGURATION_HELP
from .models import TranslationLog


@admin.register(TranslationLog)
class TranslationLogAdmin(ModelAdmin):
    list_display = (
        "created_at",
        "content_type",
        "object_id",
        "locale",
        "result_badge",
        "error_code",
        "attempts",
    )
    list_filter = ("status", "locale", "content_type", "created_at")
    search_fields = ("object_id", "model_name", "error_code")
    readonly_fields = (*tuple(field.name for field in TranslationLog._meta.fields), "resolution")
    list_select_related = ("content_type", "actor")
    actions = None

    @display(
        description="Result", label={"success": "success", "failed": "danger", "skipped": "warning"}
    )
    def result_badge(self, obj):
        return obj.status, obj.get_status_display()

    @admin.display(description="What to do next")
    def resolution(self, obj):
        if obj.status == "success":
            return (
                "Review the translated fields on the record before marking it "
                "Reviewed and publishing."
            )
        messages = {
            "nothing_missing": "All fields with English source text already have translations.",
            "record_changed": (
                "An editor changed this record during translation. Their changes were preserved."
            ),
            "record_deleted": "The source record was deleted. No generated text was saved.",
            "configuration": CONFIGURATION_HELP,
            "http_401": "Check the Groq API key in the server environment.",
            "http_403": "Check Groq account and model access. No content was saved for this batch.",
            "http_404": "Check that the configured Groq model is still available.",
            "http_429": (
                "Groq rate limit reached. Wait, then retry missing translations from the record."
            ),
            "source_too_long": (
                "This field exceeds GROQ_BATCH_CHARS. Increase the limit and "
                "output token budget together, or translate this field manually."
            ),
        }
        return messages.get(
            obj.error_code,
            (
                "This batch failed validation or delivery. Existing text was "
                "preserved. Retry missing translations from the record, or fill them manually."
            ),
        )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def change_view(self, request, object_id, form_url="", extra_context=None):
        extra_context = dict(extra_context or {})
        log = self.get_object(request, object_id)
        if log:
            model = log.content_type.model_class()
            model_admin = admin.site._registry.get(model)
            if model_admin and model_admin.has_view_or_change_permission(request):
                obj = model_admin.get_object(request, log.object_id)
                if obj and model_admin.has_view_or_change_permission(request, obj):
                    try:
                        url = reverse(
                            f"admin:{model._meta.app_label}_{model._meta.model_name}_change",
                            args=[log.object_id],
                        )
                        extra_context["subtitle"] = format_html(
                            '<a href="{}">Open record to review or retry missing translations</a>',
                            url,
                        )
                    except NoReverseMatch:
                        pass
        return super().change_view(request, object_id, form_url, extra_context)
