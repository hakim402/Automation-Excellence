from rest_framework.decorators import action

from apps.core.api import ContentPagination, PublicReadOnlyViewSet
from apps.core.public_queries import case_studies
from apps.portfolio.serializers import CaseStudySummarySerializer

from .models import Service
from .page import ServiceDetailSerializer, page_queryset
from .serializers import ServiceSummarySerializer


class ServiceViewSet(PublicReadOnlyViewSet):
    serializer_class = ServiceSummarySerializer

    def get_queryset(self):
        queryset = Service.objects.published()
        return page_queryset(queryset) if self.action == "retrieve" else queryset

    def get_serializer_class(self):
        return ServiceDetailSerializer if self.action == "retrieve" else ServiceSummarySerializer

    @action(detail=True, url_path="case-studies")
    def case_studies(self, request, slug=None):
        service = self.get_object()
        paginator = ContentPagination()
        page = paginator.paginate_queryset(case_studies().filter(service=service), request)
        return paginator.get_paginated_response(
            CaseStudySummarySerializer(page, many=True, context=self.get_serializer_context()).data
        )
