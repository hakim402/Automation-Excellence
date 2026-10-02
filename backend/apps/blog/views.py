from apps.core.api import ContentPagination, PublicReadOnlyViewSet, public_queryset
from apps.core.public_queries import filter_category, filter_slug, posts

from .models import Category, Tag
from .serializers import CategorySerializer, PostDetailSerializer, PostSummarySerializer


class PostViewSet(PublicReadOnlyViewSet):
    pagination_class = ContentPagination

    def get_queryset(self):
        queryset = posts()
        if self.action == "list":
            params = self.request.query_params
            queryset = filter_category(queryset, params)
            queryset = filter_slug(queryset, params, "service", "service__slug")
            if params.get("tag"):
                queryset = queryset.filter(tags__in=public_queryset(Tag).filter(slug=params["tag"]))
        return queryset.distinct()

    def get_serializer_class(self):
        return PostDetailSerializer if self.action == "retrieve" else PostSummarySerializer


class CategoryViewSet(PublicReadOnlyViewSet):
    serializer_class = CategorySerializer

    def get_queryset(self):
        return public_queryset(Category)
