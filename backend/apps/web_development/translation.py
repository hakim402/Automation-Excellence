from modeltranslation.translator import TranslationOptions, register

from .models import WebCapability, WebDevelopmentCaseStudy


@register(WebCapability)
class WebCapabilityTranslationOptions(TranslationOptions):
    required_languages = ("en",)
    fields = ("name", "description")


@register(WebDevelopmentCaseStudy)
class WebDevelopmentCaseStudyTranslationOptions(TranslationOptions):
    pass
