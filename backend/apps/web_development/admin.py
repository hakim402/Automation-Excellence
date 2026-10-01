from django.contrib import admin

from apps.core.content_admin import ContentAdmin
from apps.portfolio.admin import ServiceCaseStudyAdmin

from .models import WebCapability, WebDevelopmentCaseStudy


@admin.register(WebCapability)
class WebCapabilityAdmin(ContentAdmin):
    list_display = ("name", "publish_badge", "translation_badge", "order")
    list_filter = ("status", "translation_status")
    search_fields = ("name_en",)
    prepopulated_fields = {"slug": ("name_en",)}


@admin.register(WebDevelopmentCaseStudy)
class WebDevelopmentCaseStudyAdmin(ServiceCaseStudyAdmin):
    pass
