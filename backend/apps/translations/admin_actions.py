"""Shared bulk action and POST-only execution for saved record translations."""

from django.conf import settings
from django.contrib import admin, messages
from django.contrib.admin import helpers
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import path, reverse

from .client import CONFIGURATION_HELP


class TranslationActionsMixin:
    change_form_template = "admin/translations/change_form.html"

    def get_actions(self, request):
        actions = super().get_actions(request)
        if self.get_translated_fields() and self.has_change_permission(request):
            actions["auto_translate"] = (
                type(self).auto_translate,
                "auto_translate",
                "Auto-translate to all languages",
            )
        return actions

    def get_urls(self):
        urls = super().get_urls()
        if not self.get_translated_fields():
            return urls
        meta = self.model._meta
        return [
            path(
                "<path:object_id>/translate/",
                self.admin_site.admin_view(self.translate_view),
                name=f"{meta.app_label}_{meta.model_name}_translate",
            ),
            *urls,
        ]

    def change_view(self, request, object_id, form_url="", extra_context=None):
        obj = self.get_object(request, object_id)
        extra_context = dict(extra_context or {})
        if obj and self.get_translated_fields() and self.has_change_permission(request, obj):
            meta = self.model._meta
            extra_context["translate_url"] = reverse(
                f"admin:{meta.app_label}_{meta.model_name}_translate", args=[object_id]
            )
        return super().change_view(request, object_id, form_url, extra_context)

    def translate_view(self, request, object_id):
        obj = self.get_object(request, object_id)
        if obj is None:
            raise Http404
        return self.auto_translate(
            request, self.get_queryset(request).filter(pk=obj.pk), detail=True
        )

    @admin.action(description="Auto-translate to all languages", permissions=["change"])
    def auto_translate(self, request, queryset, detail=False):
        from .services import GroqTranslator

        objects = list(queryset[: settings.TRANSLATION_ADMIN_MAX_RECORDS + 1])
        if not self.has_change_permission(request) or any(
            not self.has_change_permission(request, obj) for obj in objects
        ):
            raise PermissionDenied
        if not self.get_translated_fields():
            raise PermissionDenied
        if len(objects) > settings.TRANSLATION_ADMIN_MAX_RECORDS:
            self.message_user(
                request,
                f"Select at most {settings.TRANSLATION_ADMIN_MAX_RECORDS} "
                "records per run. Saved translations are kept when you rerun.",
                messages.WARNING,
            )
            return HttpResponseRedirect(request.path)
        if request.method == "POST" and request.POST.get("confirm_translation") == "yes":
            translator = GroqTranslator(actor=request.user)
            logs = [log for obj in objects for log in translator.translate(obj)]
            success = sum(log.status == "success" for log in logs)
            failed = sum(log.status == "failed" for log in logs)
            skipped = sum(log.status == "skipped" for log in logs)
            self.message_user(
                request,
                f"Translation batches: {success} saved, {failed} failed, {skipped} skipped. "
                "Review machine translations before publishing. See System → Translation log; "
                "rerun this action to retry missing fields.",
                messages.WARNING if failed else messages.SUCCESS,
            )
            if any(log.error_code == "configuration" for log in logs):
                self.message_user(request, CONFIGURATION_HELP, messages.ERROR)
            if detail:
                meta = self.model._meta
                return HttpResponseRedirect(
                    reverse(
                        f"admin:{meta.app_label}_{meta.model_name}_change", args=[objects[0].pk]
                    )
                )
            return HttpResponseRedirect(request.path)
        return TemplateResponse(
            request,
            "admin/translations/confirm.html",
            {
                **self.admin_site.each_context(request),
                "title": "Auto-translate to all languages",
                "opts": self.model._meta,
                "objects": objects,
                "action_checkbox_name": helpers.ACTION_CHECKBOX_NAME,
                "media": self.media,
            },
        )
