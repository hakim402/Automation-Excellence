from modeltranslation.translator import TranslationOptions, register

from .models import CaseStudy, CaseStudyImage, CaseStudyMetric


@register(CaseStudy)
class CaseStudyTranslationOptions(TranslationOptions):
    required_languages = ("en",)
    fields = ("title", "challenge", "solution", "outcome", "meta_title", "meta_description")


@register(CaseStudyMetric)
class CaseStudyMetricTranslationOptions(TranslationOptions):
    required_languages = ("en",)
    fields = ("label",)


@register(CaseStudyImage)
class CaseStudyImageTranslationOptions(TranslationOptions):
    required_languages = ("en",)
    fields = ("caption",)
