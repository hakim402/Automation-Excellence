from django.contrib import admin

from apps.core.content_admin import ContentAdmin, ContentInline
from apps.services.models import Service

from .models import CaseStudy, CaseStudyImage, CaseStudyMetric


class CaseStudyMetricInline(ContentInline):
    model = CaseStudyMetric


class CaseStudyImageInline(ContentInline):
    model = CaseStudyImage


@admin.register(CaseStudyMetric)
class CaseStudyMetricAdmin(ContentAdmin):
    list_display = ("label", "value", "unit", "case_study", "translation_badge", "order")
    list_filter = ("case_study", "translation_status")
    search_fields = ("label_en",)
    autocomplete_fields = ("case_study",)


@admin.register(CaseStudyImage)
class CaseStudyImageAdmin(ContentAdmin):
    list_display = ("__str__", "case_study", "translation_badge", "order")
    list_filter = ("case_study", "translation_status")
    search_fields = ("caption_en",)
    autocomplete_fields = ("case_study",)


@admin.register(CaseStudy)
class CaseStudyAdmin(ContentAdmin):
    list_display = ("title", "service", "client_name", "publish_badge", "translation_badge")
    list_filter = ("service", "industry", "status", "translation_status")
    search_fields = ("title_en",)
    prepopulated_fields = {"slug": ("title_en",)}
    autocomplete_fields = ("service", "industry")
    filter_horizontal = ("tech_stack",)
    inlines = (
        CaseStudyMetricInline,
        CaseStudyImageInline,
    )


class ServiceCaseStudyAdmin(CaseStudyAdmin):
    """A service-specific view of the shared table, including object lookups."""

    exclude = ("service",)
    autocomplete_fields = ("industry",)
    list_filter = ("industry", "status", "translation_status")

    def get_queryset(self, request):
        return super().get_queryset(request).filter(service__key=self.model.service_key)

    def has_add_permission(self, request):
        return (
            super().has_add_permission(request)
            and Service.objects.filter(key=self.model.service_key).exists()
        )

    def save_model(self, request, obj, form, change):
        obj.service = Service.objects.get(key=self.model.service_key)
        super().save_model(request, obj, form, change)
