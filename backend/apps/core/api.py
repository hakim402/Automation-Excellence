"""Shared public API boundaries: locale resolution, explicit fields and visibility."""

from hashlib import sha256

from django.conf import settings
from django.db.models import Q
from django.utils.cache import patch_cache_control
from modeltranslation.translator import NotRegistered, translator
from rest_framework import serializers, viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.renderers import JSONRenderer

from .models import Publishable, TranslationTracked


def public_queryset(model):
    if issubclass(model, Publishable):
        queryset = model.objects.published()
    elif issubclass(model, TranslationTracked):
        queryset = model.objects.exclude(translation_status="machine")
    else:
        queryset = model.objects.all()
    if any(field.name == "is_active" for field in model._meta.fields):
        queryset = queryset.filter(is_active=True)
    return queryset


def is_public(obj):
    return obj is not None and (
        getattr(obj, "translation_status", "none") != "machine"
        and getattr(obj, "status", "published") == "published"
        and getattr(obj, "is_active", True)
    )


def public_service_owner():
    from apps.services.models import Service

    return Q(service__isnull=True) | Q(service__in=Service.objects.published())


def locale_for(request):
    locale = request.query_params.get("lang", "en")
    return locale if locale in dict(settings.LANGUAGES) else "en"


def localized(obj, field, locale):
    # Use stored columns, not modeltranslation's active-language descriptors.
    value = obj.__dict__.get(f"{field}_{locale}")
    return value if value and value.strip() else (obj.__dict__.get(f"{field}_en") or "")


class LocalizedText(serializers.Field):
    def __init__(self, name):
        self.name = name
        super().__init__(source="*", read_only=True)

    def to_representation(self, value):
        return localized(value, self.name, self.context.get("locale", "en"))


class PublicSerializer(serializers.ModelSerializer):
    def get_fields(self):
        fields = super().get_fields()
        try:
            translated = translator.get_options_for_model(self.Meta.model).fields
        except NotRegistered:
            translated = ()
        for name in translated:
            if name in fields:
                fields[name] = LocalizedText(name)
        return fields


class PublicRelated(serializers.Field):
    """Hide unreviewed related records even when a caller forgot a filtered prefetch."""

    def __init__(self, serializer_class, *, many=False, **kwargs):
        self.serializer_class = serializer_class
        self.many = many
        super().__init__(read_only=True, **kwargs)

    def to_representation(self, value):
        if self.many:
            items = value.all() if hasattr(value, "all") else value
            return self.serializer_class(
                [item for item in items if is_public(item)], many=True, context=self.context
            ).data
        return self.serializer_class(value, context=self.context).data if is_public(value) else None


class ContentPagination(PageNumberPagination):
    page_size = 12
    # A fixed limit keeps list responses predictable and query costs bounded.


class PublicReadOnlyViewSet(viewsets.ReadOnlyModelViewSet):
    authentication_classes = []
    pagination_class = None
    lookup_field = "slug"
    http_method_names = ["get", "head", "options"]

    def get_serializer_context(self):
        return {**super().get_serializer_context(), "locale": locale_for(self.request)}

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        if response.status_code == 200:
            # Revalidate every time so unpublishing takes effect on the next API read.
            # Frontend ISR invalidation is separate and belongs to Phase 6.
            patch_cache_control(response, public=True, max_age=0, must_revalidate=True)
            if response.accepted_renderer.format == "json":
                response["ETag"] = (
                    '"' + sha256(JSONRenderer().render(response.data)).hexdigest() + '"'
                )
                if request.headers.get("If-None-Match") == response["ETag"]:
                    response.status_code = 304
                    response.data = None
        else:
            patch_cache_control(response, no_store=True)
        return response
