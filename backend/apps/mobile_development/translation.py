from modeltranslation.translator import TranslationOptions, register

from .models import MobileApp, MobileAppScreenshot, MobileDevelopmentCaseStudy


@register(MobileApp)
class MobileAppTranslationOptions(TranslationOptions):
    required_languages = ("en",)
    fields = ("description", "features")


@register(MobileAppScreenshot)
class MobileAppScreenshotTranslationOptions(TranslationOptions):
    required_languages = ("en",)
    fields = ("caption",)


@register(MobileDevelopmentCaseStudy)
class MobileDevelopmentCaseStudyTranslationOptions(TranslationOptions):
    pass
