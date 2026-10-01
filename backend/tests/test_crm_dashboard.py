"""Private CRM delivery and permission-aware dashboard regression tests."""

from datetime import UTC, datetime, timedelta
from unittest.mock import patch

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core import mail
from django.db import IntegrityError, transaction
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from apps.crm.models import Lead, NewsletterSubscriber
from apps.crm.notifications import send_lead_alert
from apps.portfolio.models import CaseStudy
from apps.products.models import Product
from apps.services.models import Service
from config.dashboard import dashboard_callback
from tests.test_admin import AdminSmokeTestCase


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    LEAD_ALERT_RECIPIENTS=["staff@example.com"],
    ADMIN_BASE_URL="https://admin.example.com",
)
class LeadAlertTests(TestCase):
    def create_lead(self):
        return Lead.objects.create(
            full_name="Private Example",
            email="private@example.com",
            message="Private request",
            internal_notes="Private notes",
        )

    def test_alert_waits_for_commit_and_is_not_repeated_on_update(self):
        with self.captureOnCommitCallbacks(execute=True) as callbacks:
            lead = self.create_lead()
            self.assertEqual(len(mail.outbox), 0)
        self.assertEqual(len(callbacks), 1)
        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertEqual(message.to, ["staff@example.com"])
        self.assertIn(f"https://admin.example.com/admin/crm/lead/{lead.pk}/change/", message.body)
        for private in [lead.full_name, lead.email, lead.message, lead.internal_notes]:
            self.assertNotIn(private, message.body + message.subject)
        lead.refresh_from_db()
        self.assertIsNotNone(lead.alert_sent_at)
        with self.captureOnCommitCallbacks(execute=True) as callbacks:
            lead.status = "contacted"
            lead.save()
        self.assertEqual(callbacks, [])
        self.assertFalse(send_lead_alert(lead.pk))
        self.assertEqual(len(mail.outbox), 1)

    def test_rollback_never_sends(self):
        with self.captureOnCommitCallbacks(execute=True) as callbacks:
            try:
                with transaction.atomic():
                    self.create_lead()
                    raise ValueError("Abort test transaction")
            except ValueError:
                pass
        self.assertEqual(callbacks, [])
        self.assertEqual(len(mail.outbox), 0)
        self.assertFalse(Lead.objects.exists())

    def test_smtp_failure_keeps_lead_and_allows_retry_without_logging_payload(self):
        with (
            patch("apps.crm.notifications.send_mail", side_effect=OSError("private@example.com")),
            self.assertLogs("apps.crm.notifications", level="ERROR") as logs,
            self.captureOnCommitCallbacks(execute=True),
        ):
            lead = self.create_lead()
        lead.refresh_from_db()
        self.assertIsNone(lead.alert_sent_at)
        self.assertNotIn("private@example.com", " ".join(logs.output))
        self.assertTrue(send_lead_alert(lead.pk))
        self.assertFalse(send_lead_alert(lead.pk))
        self.assertEqual(len(mail.outbox), 1)

    @override_settings(LEAD_ALERT_RECIPIENTS=[])
    def test_no_recipients_leaves_alert_unsent(self):
        with self.captureOnCommitCallbacks(execute=True):
            lead = self.create_lead()
        lead.refresh_from_db()
        self.assertIsNone(lead.alert_sent_at)
        self.assertEqual(len(mail.outbox), 0)

    def test_newsletter_normalizes_and_database_rejects_case_duplicate(self):
        subscriber = NewsletterSubscriber.objects.create(email=" Example@Example.com ")
        self.assertEqual(subscriber.email, "example@example.com")
        self.assertFalse(subscriber.is_confirmed)
        with transaction.atomic(), self.assertRaises(IntegrityError):
            NewsletterSubscriber.objects.bulk_create(
                [NewsletterSubscriber(email="EXAMPLE@example.com")]
            )


class DashboardTests(AdminSmokeTestCase):
    def request_for(self, user):
        request = RequestFactory().get("/admin/")
        request.user = user
        return request

    def test_proxy_rows_are_not_double_counted(self):
        initial = dashboard_callback(self.request_for(self.user), {})
        CaseStudy.objects.create(
            title_en="Example",
            slug="example",
            service=Service.objects.first(),
            translation_status="machine",
        )
        Product.objects.create(name_en="Example", slug="example", translation_status="machine")
        context = dashboard_callback(self.request_for(self.user), {})
        self.assertEqual(context["draft_total"], initial["draft_total"] + 2)
        self.assertEqual(context["review_total"], initial["review_total"] + 2)

    def test_week_counts_respect_local_monday_and_status(self):
        # Sunday UTC is already Monday in Kabul.
        now = datetime(2026, 10, 4, 21, 0, tzinfo=UTC)
        start = datetime(2026, 10, 4, 19, 30, tzinfo=UTC)
        service = Service.objects.get(key="cyber-security")
        for when, status in [
            (start - timedelta(seconds=1), "new"),
            (start, "new"),
            (start + timedelta(hours=1), "contacted"),
            (start + timedelta(days=7), "new"),
        ]:
            lead = Lead.objects.create(
                full_name="Example",
                email="example@example.com",
                message="Example",
                service=service,
                status=status,
            )
            Lead.objects.filter(pk=lead.pk).update(created_at=when)
        with timezone.override("Asia/Kabul"), patch("django.utils.timezone.now", return_value=now):
            context = dashboard_callback(self.request_for(self.user), {})
        self.assertEqual(context["new_leads_this_week"], 1)
        self.assertEqual(
            context["leads_by_service"], [{"service__name_en": service.name_en, "count": 2}]
        )

    def test_staff_without_crm_permission_cannot_see_counts_or_records(self):
        staff = get_user_model().objects.create_user(username="editor", is_staff=True)
        staff.user_permissions.add(Permission.objects.get(codename="view_product"))
        Product.objects.create(name_en="Example", slug="example", translation_status="machine")
        Lead.objects.create(
            full_name="Private Example", email="example@example.com", message="Private"
        )
        self.client.force_login(staff)
        response = self.client.get(reverse("admin:index"))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["can_view_leads"])
        self.assertNotIn("new_leads_this_week", response.context)
        self.assertNotContains(response, "Private Example")
        self.assertEqual(response.context["draft_total"], 1)
        self.assertEqual(response.context["review_total"], 1)
        self.assertEqual(self.client.get(reverse("admin:crm_lead_changelist")).status_code, 403)

    def test_view_only_staff_cannot_retry_alerts(self):
        staff = get_user_model().objects.create_user(username="viewer", is_staff=True)
        staff.user_permissions.add(Permission.objects.get(codename="view_lead"))
        actions = admin.site._registry[Lead].get_actions(self.request_for(staff))
        self.assertNotIn("retry_alerts", actions)

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        LEAD_ALERT_RECIPIENTS=["staff@example.com"],
    )
    def test_retry_action_delivers_only_unsent_selected_rows(self):
        leads = [
            Lead.objects.create(full_name="Example", email="example@example.com", message="Example")
            for _ in range(2)
        ]
        send_lead_alert(leads[0].pk)
        response = self.client.post(
            reverse("admin:crm_lead_changelist"),
            {"action": "retry_alerts", "_selected_action": [str(item.pk) for item in leads]},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 2)
        self.assertFalse(Lead.objects.filter(alert_sent_at__isnull=True).exists())

    def test_anonymous_requests_cannot_read_dashboard_or_leads(self):
        self.client.logout()
        for url in (reverse("admin:index"), reverse("admin:crm_lead_changelist")):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)
            self.assertIn("/login/", response.url)
