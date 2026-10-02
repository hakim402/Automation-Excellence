from apps.core.api import PublicRelated, PublicSerializer
from apps.core.serializers import IndustrySerializer, ToolSerializer, VideoSerializer
from apps.services.serializers import ServiceSummarySerializer

from .models import CaseStudy, CaseStudyImage, CaseStudyMetric


class CaseStudyMetricSerializer(PublicSerializer):
    class Meta:
        model = CaseStudyMetric
        fields = ("label", "value", "unit", "order")


class CaseStudyImageSerializer(PublicSerializer):
    class Meta:
        model = CaseStudyImage
        fields = ("image", "caption", "order")


class CaseStudySummarySerializer(PublicSerializer):
    service = PublicRelated(ServiceSummarySerializer)
    industry = PublicRelated(IndustrySerializer)

    class Meta:
        model = CaseStudy
        fields = (
            "title",
            "slug",
            "client_name",
            "client_logo",
            "industry",
            "country",
            "cover_image",
            "service",
            "is_featured",
        )


class CaseStudyDetailSerializer(CaseStudySummarySerializer):
    metrics = PublicRelated(CaseStudyMetricSerializer, many=True)
    gallery = PublicRelated(CaseStudyImageSerializer, many=True)
    tech_stack = PublicRelated(ToolSerializer, many=True)
    videos = PublicRelated(VideoSerializer, many=True, source="public_videos")

    class Meta(CaseStudySummarySerializer.Meta):
        fields = CaseStudySummarySerializer.Meta.fields + (
            "challenge",
            "solution",
            "outcome",
            "project_url",
            "duration_months",
            "metrics",
            "gallery",
            "tech_stack",
            "videos",
            "meta_title",
            "meta_description",
            "og_image",
            "noindex",
            "updated_at",
        )
