from apps.core.api import PublicRelated, PublicSerializer
from apps.core.serializers import IndustrySerializer, ToolSerializer, VideoSerializer
from apps.services.serializers import ServiceSummarySerializer

from .models import Product, ProductFeature, ProductImage


class ProductFeatureSerializer(PublicSerializer):
    class Meta:
        model = ProductFeature
        fields = ("title", "description", "icon", "order")


class ProductImageSerializer(PublicSerializer):
    class Meta:
        model = ProductImage
        fields = ("image", "caption", "order")


class ProductSummarySerializer(PublicSerializer):
    tech_stack = PublicRelated(ToolSerializer, many=True)
    services = PublicRelated(ServiceSummarySerializer, many=True)

    class Meta:
        model = Product
        fields = (
            "name",
            "slug",
            "tagline",
            "category",
            "summary",
            "cover_image",
            "icon",
            "delivery",
            "is_featured",
            "tech_stack",
            "services",
        )


class ProductDetailSerializer(ProductSummarySerializer):
    features = PublicRelated(ProductFeatureSerializer, many=True)
    gallery = PublicRelated(ProductImageSerializer, many=True)
    videos = PublicRelated(VideoSerializer, many=True, source="public_videos")
    industries = PublicRelated(IndustrySerializer, many=True)

    class Meta(ProductSummarySerializer.Meta):
        fields = ProductSummarySerializer.Meta.fields + (
            "body",
            "demo_url",
            "docs_url",
            "features",
            "gallery",
            "videos",
            "industries",
            "meta_title",
            "meta_description",
            "og_image",
            "noindex",
            "updated_at",
        )
