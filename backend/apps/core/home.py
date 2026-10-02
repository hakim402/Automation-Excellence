"""Homepage collections share the same owner/review gates as detail pages."""

from rest_framework.response import Response

from apps.blog.serializers import PostSummarySerializer
from apps.cyber_security.models import Certification, ComplianceStandard
from apps.cyber_security.serializers import CertificationSerializer, ComplianceStandardSerializer
from apps.portfolio.serializers import CaseStudySummarySerializer
from apps.products.serializers import ProductSummarySerializer
from apps.services.models import Service

from .api import PublicReadOnlyViewSet, public_queryset
from .models import Industry, Tool
from .public_queries import case_studies, posts, products
from .serializers import IndustrySerializer, ToolSerializer


class HomeViewSet(PublicReadOnlyViewSet):
    def list(self, request):
        services = Service.objects.published()
        context = self.get_serializer_context()

        def data(serializer, rows):
            return serializer(rows, many=True, context=context).data

        security_visible = services.filter(key="cyber-security").exists()
        return Response(
            {
                "case_studies": data(
                    CaseStudySummarySerializer, case_studies().filter(is_featured=True)[:3]
                ),
                "products": data(ProductSummarySerializer, products().filter(is_featured=True)[:6]),
                "posts": data(PostSummarySerializer, posts().order_by("-published_at", "-pk")[:3]),
                "industries": data(
                    IndustrySerializer,
                    public_queryset(Industry).filter(services__in=services).distinct(),
                ),
                "tools": data(
                    ToolSerializer, Tool.objects.filter(services__in=services).distinct()
                ),
                "certifications": data(
                    CertificationSerializer,
                    public_queryset(Certification) if security_visible else [],
                ),
                "compliance_standards": data(
                    ComplianceStandardSerializer,
                    public_queryset(ComplianceStandard) if security_visible else [],
                ),
            }
        )
