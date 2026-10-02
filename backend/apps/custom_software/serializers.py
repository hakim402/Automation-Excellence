from apps.core.api import PublicSerializer

from .models import DatabaseCapability, SystemType


class SystemTypeSerializer(PublicSerializer):
    class Meta:
        model = SystemType
        fields = ("name", "slug", "description", "icon")


class DatabaseCapabilitySerializer(PublicSerializer):
    class Meta:
        model = DatabaseCapability
        fields = ("name", "slug", "description", "icon")
