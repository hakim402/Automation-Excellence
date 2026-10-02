"""One service request includes the content needed by its complete public page."""

from django.db.models import Prefetch
from rest_framework import serializers

from apps.ai_automation.models import AgentType, AutomationUseCase, Integration
from apps.ai_automation.serializers import (
    AgentTypeSerializer,
    AutomationUseCaseSerializer,
    IntegrationSerializer,
)
from apps.core.api import PublicRelated, public_queryset
from apps.core.models import Industry, Stat, Testimonial
from apps.core.public_queries import case_studies, products, videos
from apps.core.serializers import (
    IndustrySerializer,
    StatSerializer,
    TestimonialSerializer,
    ToolSerializer,
    VideoSerializer,
)
from apps.custom_software.models import DatabaseCapability, SystemType
from apps.custom_software.serializers import DatabaseCapabilitySerializer, SystemTypeSerializer
from apps.cyber_security.models import Certification, ComplianceStandard, SecurityService
from apps.cyber_security.serializers import (
    CertificationSerializer,
    ComplianceStandardSerializer,
    SecurityServiceSerializer,
)
from apps.digital_marketing.models import Campaign, CreativeWork, SocialChannel
from apps.digital_marketing.serializers import (
    CampaignSerializer,
    CreativeWorkSerializer,
    SocialChannelSerializer,
)
from apps.mobile_development.models import MobileApp, MobileAppScreenshot
from apps.mobile_development.serializers import MobileAppSerializer
from apps.portfolio.serializers import CaseStudySummarySerializer
from apps.products.serializers import ProductSummarySerializer
from apps.web_development.models import WebCapability
from apps.web_development.serializers import WebCapabilitySerializer

from .models import FAQ, ProcessStep, ServiceOffering
from .serializers import (
    FAQSerializer,
    ProcessStepSerializer,
    ServiceOfferingSerializer,
    ServiceSummarySerializer,
)

SPECIFIC_CONTENT = {
    "digital-marketing": (
        ("campaigns", Campaign, CampaignSerializer),
        ("creative_work", CreativeWork, CreativeWorkSerializer),
        ("social_channels", SocialChannel, SocialChannelSerializer),
    ),
    "ai-automation": (
        ("use_cases", AutomationUseCase, AutomationUseCaseSerializer),
        ("agent_types", AgentType, AgentTypeSerializer),
        ("integrations", Integration, IntegrationSerializer),
    ),
    "custom-software": (
        ("system_types", SystemType, SystemTypeSerializer),
        ("database_capabilities", DatabaseCapability, DatabaseCapabilitySerializer),
    ),
    "web-development": (("capabilities", WebCapability, WebCapabilitySerializer),),
    "mobile-development": (("apps", MobileApp, MobileAppSerializer),),
    "cyber-security": (
        ("security_services", SecurityService, SecurityServiceSerializer),
        ("compliance_standards", ComplianceStandard, ComplianceStandardSerializer),
        ("certifications", Certification, CertificationSerializer),
    ),
}


def page_queryset(queryset):
    return queryset.prefetch_related(
        "tools",
        Prefetch("industries", queryset=public_queryset(Industry)),
        Prefetch("offerings", queryset=public_queryset(ServiceOffering)),
        Prefetch("process_steps", queryset=public_queryset(ProcessStep)),
        Prefetch("faqs", queryset=public_queryset(FAQ)),
        Prefetch("stats", queryset=public_queryset(Stat)),
        Prefetch("testimonials", queryset=Testimonial.objects.published()),
        Prefetch("case_studies", queryset=case_studies().filter(is_featured=True)),
        Prefetch("products", queryset=products()),
        Prefetch("videos", queryset=videos(), to_attr="public_videos"),
    )


class ServiceDetailSerializer(ServiceSummarySerializer):
    offerings = PublicRelated(ServiceOfferingSerializer, many=True)
    process_steps = PublicRelated(ProcessStepSerializer, many=True)
    faqs = PublicRelated(FAQSerializer, many=True)
    tools = PublicRelated(ToolSerializer, many=True)
    industries = PublicRelated(IndustrySerializer, many=True)
    stats = PublicRelated(StatSerializer, many=True)
    testimonials = PublicRelated(TestimonialSerializer, many=True)
    case_studies = PublicRelated(CaseStudySummarySerializer, many=True)
    products = PublicRelated(ProductSummarySerializer, many=True)
    videos = PublicRelated(VideoSerializer, many=True, source="public_videos")
    specific_content = serializers.SerializerMethodField()

    def get_specific_content(self, obj):
        result = {}
        for key, model, serializer in SPECIFIC_CONTENT.get(obj.key, ()):
            queryset = public_queryset(model)
            if model is AutomationUseCase:
                queryset = queryset.select_related("industry")
            elif model is MobileApp:
                queryset = queryset.prefetch_related(
                    Prefetch("screenshots", queryset=public_queryset(MobileAppScreenshot))
                )
            result[key] = serializer(queryset, many=True, context=self.context).data
        return result

    class Meta(ServiceSummarySerializer.Meta):
        fields = ServiceSummarySerializer.Meta.fields + (
            "hero_headline",
            "hero_subline",
            "body",
            "offerings",
            "process_steps",
            "faqs",
            "tools",
            "industries",
            "stats",
            "testimonials",
            "case_studies",
            "products",
            "videos",
            "specific_content",
            "meta_title",
            "meta_description",
            "og_image",
            "noindex",
            "updated_at",
        )
