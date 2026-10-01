from django.contrib import admin

from apps.core.content_admin import ContentAdmin
from apps.portfolio.admin import ServiceCaseStudyAdmin

from .models import CustomSoftwareCaseStudy, DatabaseCapability, SystemType


@admin.register(SystemType)
class SystemTypeAdmin(ContentAdmin):
    list_display = ("name", "publish_badge", "translation_badge", "order")
    list_filter = ("status", "translation_status")
    search_fields = ("name_en",)
    prepopulated_fields = {"slug": ("name_en",)}


@admin.register(DatabaseCapability)
class DatabaseCapabilityAdmin(ContentAdmin):
    list_display = ("name", "publish_badge", "translation_badge", "order")
    list_filter = ("status", "translation_status")
    search_fields = ("name_en",)
    prepopulated_fields = {"slug": ("name_en",)}


@admin.register(CustomSoftwareCaseStudy)
class CustomSoftwareCaseStudyAdmin(ServiceCaseStudyAdmin):
    pass
