from django.conf import settings
from django.db.models import Max
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from apps.products.models import Product
from apps.services.models import Service

from .api import PublicReadOnlyViewSet, public_queryset, public_service_owner
from .models import SiteSettings, TeamMember, Testimonial
from .public_queries import case_studies, filter_slug, posts, videos
from .serializers import (
    SiteSettingsSerializer,
    TeamMemberSerializer,
    TestimonialSerializer,
    VideoSerializer,
)


class SiteSettingsViewSet(PublicReadOnlyViewSet):
    serializer_class = SiteSettingsSerializer

    def list(self, request):
        obj = get_object_or_404(public_queryset(SiteSettings), pk=SiteSettings.SINGLETON_PK)
        return Response(self.get_serializer(obj).data)


class TeamViewSet(PublicReadOnlyViewSet):
    serializer_class = TeamMemberSerializer

    def get_queryset(self):
        return public_queryset(TeamMember)


class TestimonialViewSet(PublicReadOnlyViewSet):
    serializer_class = TestimonialSerializer

    def get_queryset(self):
        return Testimonial.objects.published().filter(public_service_owner())


class VideoViewSet(PublicReadOnlyViewSet):
    serializer_class = VideoSerializer

    def get_queryset(self):
        queryset = videos()
        for param, lookup in (
            ("orientation", "orientation"),
            ("service", "service__slug"),
            ("product", "product__slug"),
        ):
            queryset = filter_slug(queryset, self.request.query_params, param, lookup)
        featured = self.request.query_params.get("featured")
        if featured is not None:
            if featured not in ("true", "false", "1", "0"):
                raise ValidationError({"featured": "Use true, false, 1 or 0."})
            queryset = queryset.filter(is_featured=featured in ("true", "1"))
        return queryset


class SitemapViewSet(PublicReadOnlyViewSet):
    def list(self, request):
        origin = settings.SITE_DOMAIN.rstrip("/")
        # Static pages exist even before editorial content is added. No artificial lastmod.
        lastmod = public_queryset(SiteSettings).aggregate(value=Max("updated_at"))["value"]
        pages = [(path, lastmod) for path in ("", "about", "contact", "products", "work", "blog")]
        for prefix, queryset in (
            ("", Service.objects.published()),
            ("products/", Product.objects.published()),
            ("work/", case_studies()),
            ("blog/", posts()),
        ):
            pages.extend(
                (prefix + row.slug, row.updated_at) for row in queryset.filter(noindex=False)
            )
        entries = []
        for path, modified in pages:
            alternates = {
                code: f"{origin}/{code}" + (f"/{path}" if path else "")
                for code, _ in settings.LANGUAGES
            }
            for locale, url in alternates.items():
                entries.append(
                    {
                        "url": url,
                        "locale": locale,
                        "lastmod": modified,
                        "alternates": {**alternates, "x-default": alternates["en"]},
                    }
                )
        return Response(entries)
