"""Versioned public content and private, write-only capture endpoints."""

from django.urls import include, path
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.routers import SimpleRouter

from apps.blog.views import CategoryViewSet, PostViewSet
from apps.core.home import HomeViewSet
from apps.core.views import (
    SitemapViewSet,
    SiteSettingsViewSet,
    TeamViewSet,
    TestimonialViewSet,
    VideoViewSet,
)
from apps.portfolio.views import CaseStudyViewSet
from apps.products.views import ProductViewSet
from apps.services.views import ServiceViewSet

router = SimpleRouter()
router.register("services", ServiceViewSet, basename="service")
router.register("products", ProductViewSet, basename="product")
router.register("portfolio/case-studies", CaseStudyViewSet, basename="case-study")
router.register("blog/posts", PostViewSet, basename="post")

LIST_ENDPOINTS = {
    "home": HomeViewSet,
    "site/settings": SiteSettingsViewSet,
    "videos": VideoViewSet,
    "blog/categories": CategoryViewSet,
    "team": TeamViewSet,
    "testimonials": TestimonialViewSet,
    "seo/sitemap": SitemapViewSet,
}


@api_view(["GET"])
def api_root(_request):
    return Response(
        {
            "version": "v1",
            "endpoints": [
                *[f"{path}/" for path in LIST_ENDPOINTS],
                "services/",
                "services/{slug}/",
                "services/{slug}/case-studies/",
                "products/",
                "products/{slug}/",
                "portfolio/case-studies/",
                "portfolio/case-studies/{slug}/",
                "blog/posts/",
                "blog/posts/{slug}/",
                "crm/leads/",
                "crm/newsletter/",
            ],
        }
    )


urlpatterns = [
    path("", api_root, name="api-root"),
    *[
        path(f"{route}/", view.as_view({"get": "list"}), name=route.replace("/", "-"))
        for route, view in LIST_ENDPOINTS.items()
    ],
    path("crm/", include("apps.crm.urls")),
    path("", include(router.urls)),
]
