from django.contrib import admin

from apps.core.content_admin import ContentAdmin
from apps.portfolio.admin import ServiceCaseStudyAdmin

from .models import AgentType, AIAutomationCaseStudy, AutomationUseCase, Integration


@admin.register(AutomationUseCase)
class AutomationUseCaseAdmin(ContentAdmin):
    list_display = ("title", "industry", "publish_badge", "translation_badge", "order")
    list_filter = ("industry", "status", "translation_status")
    search_fields = ("title_en",)
    prepopulated_fields = {"slug": ("title_en",)}
    autocomplete_fields = ("industry",)


@admin.register(AgentType)
class AgentTypeAdmin(ContentAdmin):
    list_display = ("name", "publish_badge", "translation_badge", "order")
    list_filter = ("status", "translation_status")
    search_fields = ("name_en",)
    prepopulated_fields = {"slug": ("name_en",)}


@admin.register(Integration)
class IntegrationAdmin(ContentAdmin):
    list_display = ("name", "category", "publish_badge", "order")
    list_filter = ("category", "status")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(AIAutomationCaseStudy)
class AIAutomationCaseStudyAdmin(ServiceCaseStudyAdmin):
    pass
