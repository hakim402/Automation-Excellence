from rest_framework import serializers

from apps.core.api import PublicSerializer

from .models import Industry, SiteSettings, Stat, TeamMember, Testimonial, Tool, Video


class ToolSerializer(PublicSerializer):
    class Meta:
        model = Tool
        fields = ("name", "slug", "logo", "category", "url")


class IndustrySerializer(PublicSerializer):
    class Meta:
        model = Industry
        fields = ("name", "slug", "icon", "description")


class TeamMemberSerializer(PublicSerializer):
    class Meta:
        model = TeamMember
        fields = ("name", "role", "bio", "photo", "linkedin", "github")


class StatSerializer(PublicSerializer):
    class Meta:
        model = Stat
        fields = ("label", "value", "unit")


class TestimonialSerializer(PublicSerializer):
    class Meta:
        model = Testimonial
        fields = (
            "client_name",
            "client_role",
            "client_company",
            "company_logo",
            "quote",
            "rating",
            "is_featured",
        )


class VideoSerializer(PublicSerializer):
    class Meta:
        model = Video
        fields = (
            "slug",
            "title",
            "description",
            "orientation",
            "source",
            "external_url",
            "video_file",
            "poster_image",
            "duration_seconds",
            "captions_url",
            "is_featured",
            "published_at",
        )


class SiteSettingsSerializer(PublicSerializer):
    phone_af = serializers.CharField(source="public_phone_af", read_only=True)

    class Meta:
        model = SiteSettings
        fields = (
            "company_name",
            "tagline",
            "about_short",
            "response_time",
            "logo",
            "logo_dark",
            "favicon",
            "address_line_1",
            "address_line_2",
            "city",
            "state",
            "postal_code",
            "country",
            "service_area",
            "phone_us",
            "phone_af",
            "email",
            "domain",
            "founded_year",
            "team_size",
            "linkedin_url",
            "x_url",
            "github_url",
            "instagram_url",
            "youtube_url",
            "facebook_url",
            "ga4_measurement_id",
            "default_meta_title",
            "default_meta_description",
            "default_og_image",
        )
