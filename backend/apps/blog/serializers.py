from apps.core.api import PublicRelated, PublicSerializer
from apps.core.serializers import TeamMemberSerializer
from apps.services.serializers import ServiceSummarySerializer

from .models import Category, Post, Tag


class CategorySerializer(PublicSerializer):
    class Meta:
        model = Category
        fields = ("name", "slug", "description")


class TagSerializer(PublicSerializer):
    class Meta:
        model = Tag
        fields = ("name", "slug")


class PostSummarySerializer(PublicSerializer):
    author = PublicRelated(TeamMemberSerializer)
    service = PublicRelated(ServiceSummarySerializer)
    category = PublicRelated(CategorySerializer)
    tags = PublicRelated(TagSerializer, many=True)

    class Meta:
        model = Post
        fields = (
            "title",
            "slug",
            "excerpt",
            "cover_image",
            "author",
            "service",
            "category",
            "tags",
            "reading_minutes",
            "is_featured",
            "published_at",
        )


class PostDetailSerializer(PostSummarySerializer):
    class Meta(PostSummarySerializer.Meta):
        fields = PostSummarySerializer.Meta.fields + (
            "body",
            "meta_title",
            "meta_description",
            "og_image",
            "noindex",
            "updated_at",
        )
