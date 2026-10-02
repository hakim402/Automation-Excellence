from rest_framework import serializers

from apps.products.models import Product
from apps.services.models import Service

from .models import Lead, NewsletterSubscriber


class StrictInputMixin:
    def to_internal_value(self, data):
        if isinstance(data, dict):
            unknown = set(data) - set(self.fields)
            if unknown:
                raise serializers.ValidationError({"detail": "Unexpected form fields."})
        return super().to_internal_value(data)


class LeadSerializer(StrictInputMixin, serializers.ModelSerializer):
    turnstile_token = serializers.CharField(max_length=2048, write_only=True)
    website = serializers.CharField(
        required=False, allow_blank=True, max_length=500, write_only=True
    )
    service = serializers.SlugRelatedField(
        slug_field="slug", queryset=Service.objects.published(), required=False, allow_null=True
    )
    product = serializers.SlugRelatedField(
        slug_field="slug",
        queryset=Product.objects.published(),
        required=False,
        allow_null=True,
        write_only=True,
    )
    message = serializers.CharField(max_length=10000)

    class Meta:
        model = Lead
        fields = (
            "full_name",
            "email",
            "phone",
            "company",
            "country",
            "service",
            "product",
            "message",
            "preferred_contact",
            "locale",
            "source_path",
            "utm_source",
            "utm_medium",
            "utm_campaign",
            "turnstile_token",
            "website",
        )

    def validate_source_path(self, value):
        if value and (
            not value.startswith("/")
            or value.startswith("//")
            or "\\" in value
            or "?" in value
            or "#" in value
        ):
            raise serializers.ValidationError("Use a relative page path without query or fragment.")
        return value

    def validate(self, attrs):
        if attrs.get("preferred_contact") in ("phone", "whatsapp") and not attrs.get("phone"):
            raise serializers.ValidationError(
                {"phone": "Enter a phone number for this contact method."}
            )
        return attrs


class NewsletterSerializer(StrictInputMixin, serializers.ModelSerializer):
    # Duplicate subscriptions return the same response; do not reveal registration status.
    email = serializers.EmailField(max_length=254)
    turnstile_token = serializers.CharField(max_length=2048, write_only=True)
    website = serializers.CharField(
        required=False, allow_blank=True, max_length=500, write_only=True
    )

    class Meta:
        model = NewsletterSubscriber
        fields = ("email", "locale", "turnstile_token", "website")
        validators = []
