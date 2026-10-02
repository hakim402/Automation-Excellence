from apps.core.api import ContentPagination, PublicReadOnlyViewSet, public_queryset
from apps.core.models import Industry
from apps.core.public_queries import case_studies, case_study_details, filter_slug

from .serializers import CaseStudyDetailSerializer, CaseStudySummarySerializer


class CaseStudyViewSet(PublicReadOnlyViewSet):
    pagination_class = ContentPagination

    def get_queryset(self):
        if self.action == "retrieve":
            return case_study_details()
        params = self.request.query_params
        queryset = filter_slug(case_studies(), params, "service", "service__slug")
        if params.get("industry"):
            queryset = queryset.filter(
                industry__in=public_queryset(Industry).filter(slug=params["industry"])
            )
        return queryset

    def get_serializer_class(self):
        return (
            CaseStudyDetailSerializer if self.action == "retrieve" else CaseStudySummarySerializer
        )
