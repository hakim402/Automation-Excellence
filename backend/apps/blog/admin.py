from django.contrib import admin

from apps.core.content_admin import ContentAdmin

from .models import Category, Post, Tag


@admin.register(Category)
class CategoryAdmin(ContentAdmin):
    list_display = ("name", "slug", "translation_badge", "order")
    list_filter = ("translation_status",)
    search_fields = ("name_en",)
    prepopulated_fields = {"slug": ("name_en",)}


@admin.register(Tag)
class TagAdmin(ContentAdmin):
    list_display = ("name", "slug", "translation_badge", "order")
    list_filter = ("translation_status",)
    search_fields = ("name_en",)
    prepopulated_fields = {"slug": ("name_en",)}


@admin.register(Post)
class PostAdmin(ContentAdmin):
    list_display = (
        "title",
        "author",
        "category",
        "publish_badge",
        "translation_badge",
        "published_at",
    )
    list_filter = ("category", "service", "status", "translation_status")
    search_fields = ("title_en",)
    prepopulated_fields = {"slug": ("title_en",)}
    autocomplete_fields = ("author", "category", "service")
    filter_horizontal = ("tags",)
