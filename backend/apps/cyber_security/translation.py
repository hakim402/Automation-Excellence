from modeltranslation.translator import TranslationOptions, register

from .models import ComplianceStandard, CyberSecurityCaseStudy, SecurityService


@register(SecurityService)
class SecurityServiceTranslationOptions(TranslationOptions):
    required_languages = ("en",)
    fields = ("name", "description")


@register(ComplianceStandard)
class ComplianceStandardTranslationOptions(TranslationOptions):
    required_languages = ("en",)
    fields = ("description",)


@register(CyberSecurityCaseStudy)
class CyberSecurityCaseStudyTranslationOptions(TranslationOptions):
    pass
