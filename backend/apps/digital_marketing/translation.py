from modeltranslation.translator import TranslationOptions, register

from .models import Campaign, CreativeWork, DigitalMarketingCaseStudy


@register(Campaign)
class CampaignTranslationOptions(TranslationOptions):
    required_languages = ("en",)
    fields = ("title", "objective", "summary", "results")


@register(CreativeWork)
class CreativeWorkTranslationOptions(TranslationOptions):
    required_languages = ("en",)
    fields = ("title", "description")


@register(DigitalMarketingCaseStudy)
class DigitalMarketingCaseStudyTranslationOptions(TranslationOptions):
    pass
