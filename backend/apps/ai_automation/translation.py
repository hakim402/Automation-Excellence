from modeltranslation.translator import TranslationOptions, register

from .models import AgentType, AIAutomationCaseStudy, AutomationUseCase


@register(AutomationUseCase)
class AutomationUseCaseTranslationOptions(TranslationOptions):
    required_languages = ("en",)
    fields = ("title", "description")


@register(AgentType)
class AgentTypeTranslationOptions(TranslationOptions):
    required_languages = ("en",)
    fields = ("name", "description", "example_prompt")


@register(AIAutomationCaseStudy)
class AIAutomationCaseStudyTranslationOptions(TranslationOptions):
    pass
