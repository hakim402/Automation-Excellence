from apps.core.api import ContentPagination, PublicReadOnlyViewSet
from apps.core.public_queries import filter_slug, products
from apps.services.models import Service

from .serializers import ProductDetailSerializer, ProductSummarySerializer


class ProductViewSet(PublicReadOnlyViewSet):
    pagination_class = ContentPagination

    def get_queryset(self):
        queryset = products(detail=self.action == "retrieve")
        if self.action == "list":
            params = self.request.query_params
            queryset = filter_slug(queryset, params, "category", "category")
            if params.get("service"):
                queryset = queryset.filter(
                    services__in=Service.objects.published().filter(slug=params["service"])
                )
        return queryset.distinct()

    def get_serializer_class(self):
        return ProductDetailSerializer if self.action == "retrieve" else ProductSummarySerializer
