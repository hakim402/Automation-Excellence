from django.contrib import admin

from apps.core.content_admin import ContentAdmin, ContentInline

from .models import Product, ProductFeature, ProductImage


class ProductFeatureInline(ContentInline):
    model = ProductFeature


class ProductImageInline(ContentInline):
    model = ProductImage


@admin.register(ProductFeature)
class ProductFeatureAdmin(ContentAdmin):
    list_display = ("title", "product", "translation_badge", "order")
    list_filter = ("product", "translation_status")
    search_fields = ("title_en",)
    autocomplete_fields = ("product",)


@admin.register(ProductImage)
class ProductImageAdmin(ContentAdmin):
    list_display = ("__str__", "product", "translation_badge", "order")
    list_filter = ("product", "translation_status")
    search_fields = ("caption_en",)
    autocomplete_fields = ("product",)


@admin.register(Product)
class ProductAdmin(ContentAdmin):
    list_display = (
        "name",
        "category",
        "delivery",
        "publish_badge",
        "translation_badge",
        "is_featured",
    )
    list_filter = ("category", "delivery", "status", "translation_status")
    search_fields = ("name_en",)
    prepopulated_fields = {"slug": ("name_en",)}
    filter_horizontal = ("tech_stack", "services", "industries")
    inlines = (
        ProductFeatureInline,
        ProductImageInline,
    )
