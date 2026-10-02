from unittest.mock import MagicMock, patch
from urllib.error import URLError

from django.db import transaction
from django.test import TestCase, override_settings

from apps.core.models import Industry, SiteSettings, Tool
from apps.core.revalidation import notify_frontend
from apps.crm.models import Lead
from apps.cyber_security.models import Certification
from apps.products.models import Product
from apps.services.models import Service, ServiceOffering


@override_settings(REVALIDATE_WEBHOOK_URL="")
class HomeAPITests(TestCase):
    def test_home_hides_drafts_and_unreviewed_nested_content(self):
        service = Service.objects.get(key="cyber-security")
        industry = Industry.objects.create(name_en="Fixture industry", slug="fixture")
        tool = Tool.objects.create(name="Fixture tool", slug="fixture-tool")
        service.industries.add(industry)
        service.tools.add(tool)
        Certification.objects.create(
            name="Fixture certificate", slug="fixture-cert", status="published"
        )
        Product.objects.create(
            name_en="Fixture product",
            slug="fixture-product",
            category="template",
            delivery="customisable",
            is_featured=True,
        )
        data = self.client.get("/api/v1/home/?lang=ar").json()
        for key in ["products", "industries", "tools", "certifications"]:
            self.assertEqual(data[key], [])
        service.status = "published"
        service.save()
        data = self.client.get("/api/v1/home/?lang=ar").json()
        self.assertEqual(data["industries"][0]["name"], "Fixture industry")
        self.assertEqual(len(data["tools"]), 1)
        self.assertEqual(len(data["certifications"]), 1)
        industry.translation_status = "machine"
        industry.save()
        self.assertEqual(self.client.get("/api/v1/home/").json()["industries"], [])
        service.status = "draft"
        service.save()
        self.assertEqual(self.client.get("/api/v1/home/").json()["certifications"], [])

    def test_response_time_is_optional_and_localized(self):
        site = SiteSettings.load()
        site.response_time_en = "Fixture response time"
        site.response_time_ar = "وقت الرد للاختبار"
        site.save()
        self.assertEqual(
            self.client.get("/api/v1/site/settings/?lang=ar").json()["response_time"],
            "وقت الرد للاختبار",
        )
        self.assertEqual(
            self.client.get("/api/v1/site/settings/?lang=fr").json()["response_time"],
            "Fixture response time",
        )


@override_settings(
    REVALIDATE_WEBHOOK_URL="https://frontend.example.test/api/revalidate",
    REVALIDATE_WEBHOOK_SECRET="test-only-webhook-secret",
)
class RevalidationTests(TestCase):
    def test_save_unpublish_delete_and_m2m_are_after_commit(self):
        with patch("apps.core.revalidation.notify_frontend") as notify:
            with self.captureOnCommitCallbacks(execute=True):
                service = Service.objects.get(key="ai-automation")
                service.status = "published"
                service.save()
                self.assertFalse(notify.called)
            notify.assert_called_once()
            with self.captureOnCommitCallbacks(execute=True):
                service.status = "draft"
                service.save()
            self.assertEqual(notify.call_count, 2)
            with self.captureOnCommitCallbacks(execute=True):
                offering = ServiceOffering.objects.create(service=service, title_en="Fixture")
                offering.delete()
            self.assertEqual(notify.call_count, 4)
            tool = Tool.objects.create(name="Fixture", slug="fixture")
            notify.reset_mock()
            with self.captureOnCommitCallbacks(execute=True):
                service.tools.add(tool)
                service.tools.clear()
            self.assertEqual(notify.call_count, 2)

    def test_rollback_and_private_crm_do_not_invalidate(self):
        with patch("apps.core.revalidation.notify_frontend") as notify:
            with self.captureOnCommitCallbacks(execute=True):
                try:
                    with transaction.atomic():
                        Tool.objects.create(name="Rolled back", slug="rollback")
                        raise ValueError
                except ValueError:
                    pass
                Lead.objects.create(
                    full_name="Fixture", email="fixture@example.test", message="Fixture"
                )
            notify.assert_not_called()

    def test_sender_uses_header_and_fixed_scope_and_refuses_redirects(self):
        with patch("apps.core.revalidation.build_opener") as build:
            response = MagicMock()
            response.read.return_value = b'{"revalidated":true}'
            build.return_value.open.return_value.__enter__.return_value = response
            self.assertTrue(notify_frontend())
            req = build.return_value.open.call_args.args[0]
            self.assertEqual(req.data, b'{"scope": "content"}')
            self.assertEqual(req.get_header("Authorization"), "Bearer test-only-webhook-secret")
            self.assertIsNone(
                build.call_args.args[0].redirect_request(
                    None, None, 302, None, None, "https://other.test"
                )
            )

    def test_failure_is_safe_and_does_not_break_content_saves(self):
        with patch("apps.core.revalidation.build_opener") as build:
            build.return_value.open.side_effect = URLError("sensitive provider details")
            with self.assertLogs("apps.core.revalidation", level="WARNING") as logs:
                self.assertFalse(notify_frontend())
            self.assertNotIn("sensitive provider details", " ".join(logs.output))
        with (
            override_settings(REVALIDATE_WEBHOOK_SECRET=""),
            patch("apps.core.revalidation.build_opener") as build,
        ):
            self.assertFalse(notify_frontend())
            build.assert_not_called()
