"""Public query plans shared by lists and nested page payloads."""

from django.db.models import Prefetch, Q

from apps.blog.models import Category, Post, Tag
from apps.portfolio.models import CaseStudy, CaseStudyImage, CaseStudyMetric
from apps.products.models import Product, ProductFeature, ProductImage
from apps.services.models import Service

from .api import public_queryset, public_service_owner
from .models import Industry, Video


def case_studies():
    return (
        CaseStudy.objects.published()
        .filter(service__in=Service.objects.published())
        .select_related("service", "industry")
    )


def videos():
    return (
        Video.objects.published()
        .filter(public_service_owner())
        .filter(
            Q(product__isnull=True) | Q(product__in=Product.objects.published()),
            Q(case_study__isnull=True) | Q(case_study__in=case_studies()),
        )
    )


def products(*, detail=False):
    queryset = Product.objects.published().prefetch_related(
        "tech_stack", Prefetch("services", queryset=Service.objects.published())
    )
    if detail:
        queryset = queryset.prefetch_related(
            Prefetch("industries", queryset=public_queryset(Industry)),
            Prefetch("features", queryset=public_queryset(ProductFeature)),
            Prefetch("gallery", queryset=public_queryset(ProductImage)),
            Prefetch("videos", queryset=videos(), to_attr="public_videos"),
        )
    return queryset


def case_study_details():
    return case_studies().prefetch_related(
        "tech_stack",
        Prefetch("metrics", queryset=public_queryset(CaseStudyMetric)),
        Prefetch("gallery", queryset=public_queryset(CaseStudyImage)),
        Prefetch("videos", queryset=videos(), to_attr="public_videos"),
    )


def posts():
    return (
        Post.objects.published()
        .filter(public_service_owner())
        .select_related("author", "category", "service")
        .prefetch_related(Prefetch("tags", queryset=public_queryset(Tag)))
    )


def filter_slug(queryset, params, parameter, lookup):
    value = params.get(parameter)
    return queryset.filter(**{lookup: value}) if value else queryset


def filter_category(queryset, params):
    value = params.get("category")
    if value:
        queryset = queryset.filter(category__in=public_queryset(Category).filter(slug=value))
    return queryset
