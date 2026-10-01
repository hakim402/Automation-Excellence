from django.contrib import admin, messages
from unfold.admin import ModelAdmin

from .models import Lead, NewsletterSubscriber
from .notifications import send_lead_alert


@admin.register(Lead)
class LeadAdmin(ModelAdmin):
    list_display = (
        "full_name",
        "company",
        "service",
        "status",
        "locale",
        "created_at",
        "alert_sent_at",
    )
    list_filter = ("status", "service", "locale", "created_at")
    search_fields = ("full_name", "email", "company")
    autocomplete_fields = ("service",)
    readonly_fields = ("created_at", "alert_sent_at", "ip_address", "user_agent")
    actions = ("retry_alerts",)
    fieldsets = (
        (
            "Contact",
            {"fields": ("full_name", "email", "phone", "company", "country", "preferred_contact")},
        ),
        ("Request", {"fields": ("service", "message", "locale", "status", "internal_notes")}),
        (
            "Attribution",
            {
                "fields": ("source_path", "utm_source", "utm_medium", "utm_campaign"),
                "classes": ("collapse",),
            },
        ),
        (
            "System",
            {
                "fields": ("created_at", "alert_sent_at", "ip_address", "user_agent"),
                "classes": ("collapse",),
            },
        ),
    )

    @admin.action(description="Retry unsent lead alerts", permissions=["change"])
    def retry_alerts(self, request, queryset):
        sent = sum(
            send_lead_alert(pk)
            for pk in queryset.filter(alert_sent_at__isnull=True).values_list("pk", flat=True)
        )
        self.message_user(
            request,
            f"Sent {sent} alert(s). Unsent records can be retried after checking SMTP settings.",
            messages.INFO,
        )


@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(ModelAdmin):
    list_display = ("email", "locale", "is_confirmed", "created_at")
    list_filter = ("locale", "is_confirmed")
    search_fields = ("email",)
    readonly_fields = ("created_at",)
