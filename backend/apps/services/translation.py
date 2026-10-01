"""
Translatable fields for the services app.

`key` and `slug` stay English across all six locales by design — routing
stability over localised URLs, with hreflang doing the SEO work
(CLAUDE.md section 6).
"""

from modeltranslation.translator import TranslationOptions, register

from .models import FAQ, ProcessStep, Service, ServiceOffering


@register(Service)
class ServiceTranslationOptions(TranslationOptions):
    fields = (
        "name",
        "hero_headline",
        "hero_subline",
        "intro",
        "body",
        "meta_title",
        "meta_description",
    )


@register(ServiceOffering)
class ServiceOfferingTranslationOptions(TranslationOptions):
    fields = ("title", "description")


@register(ProcessStep)
class ProcessStepTranslationOptions(TranslationOptions):
    fields = ("title", "description")


@register(FAQ)
class FAQTranslationOptions(TranslationOptions):
    fields = ("question", "answer")
