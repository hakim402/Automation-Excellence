from apps.core.api import PublicSerializer

from .models import Certification, ComplianceStandard, SecurityService


class SecurityServiceSerializer(PublicSerializer):
    class Meta:
        model = SecurityService
        fields = ("name", "slug", "description", "icon")


class ComplianceStandardSerializer(PublicSerializer):
    class Meta:
        model = ComplianceStandard
        fields = ("name", "slug", "description", "logo")


class CertificationSerializer(PublicSerializer):
    class Meta:
        model = Certification
        fields = ("name", "slug", "issuer", "logo", "credential_url")
