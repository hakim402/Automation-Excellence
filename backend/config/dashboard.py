"""Permission-aware admin counts. Proxies never double-count shared records."""

from datetime import timedelta

from django.contrib import admin
from django.db.models import Count
from django.urls import reverse
from django.utils import timezone

from apps.core.models import Publishable, TranslationTracked
from apps.crm.models import Lead


def dashboard_callback(request, context):
    draft_rows, review_rows = [], []
    for model, model_admin in admin.site._registry.items():
        if model._meta.proxy or not model_admin.has_view_or_change_permission(request):
            continue
        meta = model._meta
        url = reverse(f"admin:{meta.app_label}_{meta.model_name}_changelist")
        queryset = model_admin.get_queryset(request)
        if issubclass(model, Publishable):
            count = queryset.filter(status="draft").count()
            if count:
                draft_rows.append(
                    {
                        "label": str(meta.verbose_name_plural),
                        "count": count,
                        "url": f"{url}?status__exact=draft",
                    }
                )
        if issubclass(model, TranslationTracked):
            count = queryset.filter(translation_status="machine").count()
            if count:
                review_rows.append(
                    {
                        "label": str(meta.verbose_name_plural),
                        "count": count,
                        "url": f"{url}?translation_status__exact=machine",
                    }
                )
    context.update(
        draft_rows=draft_rows,
        review_rows=review_rows,
        draft_total=sum(row["count"] for row in draft_rows),
        review_total=sum(row["count"] for row in review_rows),
        can_view_leads=admin.site._registry[Lead].has_view_or_change_permission(request),
    )
    if context["can_view_leads"]:
        today = timezone.localdate()
        week_start_date = today - timedelta(days=today.weekday())
        week_start = timezone.make_aware(
            timezone.datetime.combine(week_start_date, timezone.datetime.min.time())
        )
        week_end = timezone.make_aware(
            timezone.datetime.combine(
                week_start_date + timedelta(days=7), timezone.datetime.min.time()
            )
        )
        leads = admin.site._registry[Lead].get_queryset(request)
        weekly = leads.filter(created_at__gte=week_start, created_at__lt=week_end)
        context.update(
            new_leads_this_week=weekly.filter(status="new").count(),
            leads_by_service=list(
                weekly.order_by()
                .values("service__name_en")
                .annotate(count=Count("pk"))
                .order_by("service__name_en")
            ),
            lead_week_start=week_start_date,
            leads_url=reverse("admin:crm_lead_changelist"),
        )
    return context
