from django.contrib import admin

from apps.core.content_admin import ContentAdmin
from apps.portfolio.admin import ServiceCaseStudyAdmin

from .models import Campaign, CreativeWork, DigitalMarketingCaseStudy, SocialChannel


@admin.register(Campaign)
class CampaignAdmin(ContentAdmin):
    list_display = ("title", "client_name", "start_date", "publish_badge", "translation_badge")
    list_filter = ("status", "translation_status", "is_featured")
    search_fields = ("title_en",)
    prepopulated_fields = {"slug": ("title_en",)}


@admin.register(SocialChannel)
class SocialChannelAdmin(ContentAdmin):
    list_display = ("platform", "handle", "follower_count", "is_managed_for_clients", "order")
    list_filter = ("platform", "is_managed_for_clients")
    search_fields = ("handle",)
    prepopulated_fields = {"slug": ("handle",)}


@admin.register(CreativeWork)
class CreativeWorkAdmin(ContentAdmin):
    list_display = ("title", "kind", "client_name", "publish_badge", "translation_badge")
    list_filter = ("kind", "status", "translation_status")
    search_fields = ("title_en",)
    prepopulated_fields = {"slug": ("title_en",)}


@admin.register(DigitalMarketingCaseStudy)
class DigitalMarketingCaseStudyAdmin(ServiceCaseStudyAdmin):
    pass
