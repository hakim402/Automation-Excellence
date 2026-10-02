from apps.core.api import PublicSerializer

from .models import WebCapability


class WebCapabilitySerializer(PublicSerializer):
    class Meta:
        model = WebCapability
        fields = ("name", "slug", "description", "icon")
