from apps.core.api import PublicRelated, PublicSerializer

from .models import MobileApp, MobileAppScreenshot


class MobileAppScreenshotSerializer(PublicSerializer):
    class Meta:
        model = MobileAppScreenshot
        fields = ("image", "caption", "order")


class MobileAppSerializer(PublicSerializer):
    screenshots = PublicRelated(MobileAppScreenshotSerializer, many=True)

    class Meta:
        model = MobileApp
        fields = (
            "name",
            "slug",
            "client_name",
            "platforms",
            "description",
            "features",
            "app_store_url",
            "play_store_url",
            "icon_image",
            "downloads",
            "rating",
            "screenshots",
        )
