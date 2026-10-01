from modeltranslation.translator import TranslationOptions, register

from .models import CustomSoftwareCaseStudy, DatabaseCapability, SystemType


@register(SystemType)
class SystemTypeTranslationOptions(TranslationOptions):
    required_languages = ("en",)
    fields = ("name", "description")


@register(DatabaseCapability)
class DatabaseCapabilityTranslationOptions(TranslationOptions):
    required_languages = ("en",)
    fields = ("name", "description")


@register(CustomSoftwareCaseStudy)
class CustomSoftwareCaseStudyTranslationOptions(TranslationOptions):
    pass
