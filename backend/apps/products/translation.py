from modeltranslation.translator import TranslationOptions, register

from .models import Product, ProductFeature, ProductImage


@register(Product)
class ProductTranslationOptions(TranslationOptions):
    required_languages = ("en",)
    fields = ("name", "tagline", "summary", "body", "meta_title", "meta_description")


@register(ProductFeature)
class ProductFeatureTranslationOptions(TranslationOptions):
    required_languages = ("en",)
    fields = ("title", "description")


@register(ProductImage)
class ProductImageTranslationOptions(TranslationOptions):
    required_languages = ("en",)
    fields = ("caption",)
