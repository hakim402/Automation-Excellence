from apps.core.api import PublicSerializer

from .models import Campaign, CreativeWork, SocialChannel


class CampaignSerializer(PublicSerializer):
    class Meta:
        model = Campaign
        fields = (
            "title",
            "slug",
            "client_name",
            "objective",
            "summary",
            "results",
            "platforms",
            "start_date",
            "end_date",
            "cover_image",
            "reach",
            "engagement_rate",
            "conversions",
            "is_featured",
        )


class SocialChannelSerializer(PublicSerializer):
    class Meta:
        model = SocialChannel
        fields = ("platform", "handle", "url", "follower_count", "is_managed_for_clients")


class CreativeWorkSerializer(PublicSerializer):
    class Meta:
        model = CreativeWork
        fields = (
            "kind",
            "title",
            "slug",
            "description",
            "thumbnail",
            "file",
            "external_url",
            "client_name",
        )
