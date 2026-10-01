from django.contrib import admin

from apps.core.content_admin import ContentAdmin
from apps.portfolio.admin import ServiceCaseStudyAdmin

from .models import Certification, ComplianceStandard, CyberSecurityCaseStudy, SecurityService


@admin.register(SecurityService)
class SecurityServiceAdmin(ContentAdmin):
    list_display = ("name", "publish_badge", "translation_badge", "order")
    list_filter = ("status", "translation_status")
    search_fields = ("name_en",)
    prepopulated_fields = {"slug": ("name_en",)}


@admin.register(ComplianceStandard)
class ComplianceStandardAdmin(ContentAdmin):
    list_display = ("name", "publish_badge", "translation_badge", "order")
    list_filter = ("status", "translation_status")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Certification)
class CertificationAdmin(ContentAdmin):
    list_display = ("name", "issuer", "publish_badge", "order")
    list_filter = ("status", "issuer")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(CyberSecurityCaseStudy)
class CyberSecurityCaseStudyAdmin(ServiceCaseStudyAdmin):
    pass
