from django.contrib import admin

from apps.core.content_admin import ContentAdmin, ContentInline
from apps.portfolio.admin import ServiceCaseStudyAdmin

from .models import MobileApp, MobileAppScreenshot, MobileDevelopmentCaseStudy


class MobileAppScreenshotInline(ContentInline):
    model = MobileAppScreenshot


@admin.register(MobileAppScreenshot)
class MobileAppScreenshotAdmin(ContentAdmin):
    list_display = ("__str__", "app", "translation_badge", "order")
    list_filter = ("app", "translation_status")
    search_fields = ("caption_en",)
    autocomplete_fields = ("app",)


@admin.register(MobileApp)
class MobileAppAdmin(ContentAdmin):
    list_display = ("name", "client_name", "rating", "publish_badge", "translation_badge")
    list_filter = ("status", "translation_status")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}
    inlines = (MobileAppScreenshotInline,)


@admin.register(MobileDevelopmentCaseStudy)
class MobileDevelopmentCaseStudyAdmin(ServiceCaseStudyAdmin):
    pass
