from modeltranslation.translator import TranslationOptions, register

from .models import Category, Post, Tag


@register(Category)
class CategoryTranslationOptions(TranslationOptions):
    required_languages = ("en",)
    fields = ("name", "description")


@register(Tag)
class TagTranslationOptions(TranslationOptions):
    required_languages = ("en",)
    fields = ("name",)


@register(Post)
class PostTranslationOptions(TranslationOptions):
    required_languages = ("en",)
    fields = ("title", "excerpt", "body", "meta_title", "meta_description")
