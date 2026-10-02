"""Capture endpoints must never expose CRM data or accept unverified submissions."""

import json
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from io import BytesIO, StringIO
from unittest.mock import patch
from urllib.error import URLError

from django.core import mail
from django.core.management import call_command
from django.db import close_old_connections, connections
from django.test import SimpleTestCase, TestCase, TransactionTestCase, override_settings
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIClient, APIRequestFactory

from apps.crm.models import CaptureThrottleBucket, Lead, NewsletterSubscriber
from apps.crm.throttling import LeadThrottle, client_ip
from apps.crm.turnstile import NoRedirects, VerificationUnavailable, verify_turnstile
from apps.products.models import Product
from apps.services.models import Service


@override_settings(
    TURNSTILE_SECRET_KEY="fixture-secret", TURNSTILE_ALLOWED_HOSTNAMES=["example.test"]
)
class TurnstileTests(SimpleTestCase):
    def result(self, value):
        return BytesIO(json.dumps(value).encode())

    @patch("apps.crm.turnstile.build_opener")
    def test_verifies_token_hostname_action_with_timeout_and_no_personal_payload(self, factory):
        factory.return_value.open.return_value = self.result(
            {"success": True, "hostname": "example.test", "action": "lead"}
        )
        verify_turnstile("fixture-token", "192.0.2.1", action="lead")
        request = factory.return_value.open.call_args.args[0]
        self.assertEqual(
            request.full_url, "https://challenges.cloudflare.com/turnstile/v0/siteverify"
        )
        self.assertEqual(set(json.loads(request.data)), {"secret", "response", "remoteip"})
        self.assertEqual(factory.return_value.open.call_args.kwargs["timeout"], 10)
        self.assertIsNone(
            NoRedirects().redirect_request(None, None, 302, "", {}, "https://untrusted.test")
        )

    @patch("apps.crm.turnstile.build_opener")
    def test_invalid_replayed_wrong_host_or_wrong_action_fails_closed(self, factory):
        for value in (
            {"success": False, "error-codes": ["timeout-or-duplicate"]},
            {"success": True, "hostname": "other.test", "action": "lead"},
            {"success": True, "hostname": "example.test", "action": "newsletter"},
            {"success": "true", "hostname": "example.test", "action": "lead"},
            {"success": True},
        ):
            factory.return_value.open.return_value = self.result(value)
            with self.assertRaises(ValidationError):
                verify_turnstile("fixture-token", None, action="lead")

    @patch("apps.crm.turnstile.build_opener")
    def test_provider_failures_and_bad_configuration_never_expose_secrets(self, factory):
        for content in (
            b"not-json",
            b"[]",
            b"x" * 65537,
            json.dumps({"success": False, "error-codes": ["invalid-input-secret"]}).encode(),
        ):
            factory.return_value.open.return_value = BytesIO(content)
            with self.assertRaises(VerificationUnavailable) as error:
                verify_turnstile("fixture-token", None, action="lead")
            self.assertNotIn("fixture-secret", str(error.exception))
        factory.return_value.open.side_effect = URLError("fixture-secret")
        with self.assertRaises(VerificationUnavailable):
            verify_turnstile("fixture-token", None, action="lead")
        factory.reset_mock()
        with override_settings(TURNSTILE_SECRET_KEY=""), self.assertRaises(VerificationUnavailable):
            verify_turnstile("fixture-token", None, action="lead")
        factory.assert_not_called()

    def test_forwarded_ip_headers_require_a_trusted_direct_proxy(self):
        request = APIRequestFactory().post(
            "/",
            REMOTE_ADDR="192.0.2.1",
            HTTP_X_FORWARDED_FOR="198.51.100.2",
            HTTP_X_REAL_IP="198.51.100.3",
        )
        self.assertEqual(client_ip(request), "192.0.2.1")
        with override_settings(CAPTURE_TRUSTED_PROXIES=["192.0.2.0/24"]):
            self.assertEqual(client_ip(request), "198.51.100.3")
            request.META["HTTP_X_REAL_IP"] = "198.51.100.3, 198.51.100.4"
            self.assertEqual(client_ip(request), "192.0.2.1")


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    LEAD_ALERT_RECIPIENTS=["staff@example.test"],
)
class CaptureAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.service = Service.objects.get(key="web-development")
        self.service.status = "published"
        self.service.save()
        self.payload = {
            "full_name": "Fixture visitor",
            "email": "visitor@example.test",
            "message": "A fixture request",
            "service": "web-development",
            "locale": "ar",
            "source_path": "/ar/web-development",
            "turnstile_token": "fixture-token",
            "website": "",
            "utm_source": "fixture",
        }

    def submit(self, data=None, **extra):
        return self.client.post("/api/v1/crm/leads/", data or self.payload, format="json", **extra)

    @patch("apps.crm.views.verify_turnstile")
    def test_valid_lead_captures_attribution_and_sends_only_staff_link_after_commit(self, verify):
        with self.captureOnCommitCallbacks(execute=True):
            response = self.submit(
                REMOTE_ADDR="192.0.2.1",
                HTTP_USER_AGENT="Fixture agent",
                HTTP_X_FORWARDED_FOR="1.2.3.4",
            )
        self.assertEqual(response.status_code, 201, response.content)
        self.assertEqual(set(response.json()), {"detail"})
        self.assertEqual(response["Cache-Control"], "no-store")
        lead = Lead.objects.get()
        self.assertEqual(
            (lead.locale, lead.source_path, lead.utm_source),
            ("ar", "/ar/web-development", "fixture"),
        )
        self.assertEqual(lead.ip_address, "192.0.2.1")
        self.assertEqual(lead.status, "new")
        verify.assert_called_once_with("fixture-token", "192.0.2.1", action="lead")
        self.assertEqual(len(mail.outbox), 1)
        self.assertNotIn("visitor@example.test", mail.outbox[0].body)
        self.assertNotIn("A fixture request", mail.outbox[0].body)
        self.assertIn("/admin/crm/lead/", mail.outbox[0].body)

    @patch("apps.crm.views.verify_turnstile")
    def test_product_context_is_canonical_and_no_staff_fields_can_be_injected(self, verify):
        Product.objects.create(
            name_en="Product",
            slug="product",
            summary_en="Fixture",
            category="template",
            delivery="customisable",
            status="published",
        )
        self.assertEqual(self.submit({**self.payload, "product": "product"}).status_code, 201)
        self.assertTrue(Lead.objects.get().message.startswith("[Product: product]"))
        for name in ("status", "internal_notes", "ip_address", "alert_sent_at"):
            response = self.submit({**self.payload, name: "injected"}, REMOTE_ADDR="192.0.2.3")
            self.assertEqual(response.status_code, 400)
        self.assertEqual(Lead.objects.count(), 1)

    @patch("apps.crm.views.verify_turnstile")
    def test_honeypot_accepts_without_persistence_provider_or_email(self, verify):
        with self.captureOnCommitCallbacks(execute=True):
            response = self.submit({**self.payload, "website": "spam"})
        self.assertEqual(response.status_code, 201)
        self.assertFalse(Lead.objects.exists())
        verify.assert_not_called()
        self.assertEqual(len(mail.outbox), 0)

    @patch("apps.crm.views.verify_turnstile")
    def test_invalid_input_rejected_before_provider(self, verify):
        for i, change in enumerate(
            (
                {"email": "bad"},
                {"full_name": ""},
                {"message": "x" * 10001},
                {"turnstile_token": "x" * 2049},
                {"locale": "xx"},
                {"source_path": "https://evil.test"},
                {"source_path": "//evil.test"},
                {"service": "cyber-security"},
                {"preferred_contact": "phone"},
            )
        ):
            response = self.submit({**self.payload, **change}, REMOTE_ADDR=f"192.0.2.{i + 1}")
            self.assertEqual(response.status_code, 400, response.content)
        verify.assert_not_called()
        self.assertFalse(Lead.objects.exists())

    @patch(
        "apps.crm.views.verify_turnstile",
        side_effect=ValidationError({"turnstile_token": "Invalid"}),
    )
    def test_verification_failure_never_creates_a_lead(self, verify):
        self.assertEqual(self.submit().status_code, 400)
        self.assertFalse(Lead.objects.exists())

    @override_settings(TURNSTILE_SECRET_KEY="")
    def test_missing_provider_configuration_returns_503_without_creating_content(self):
        self.assertEqual(self.submit().status_code, 503)
        self.assertFalse(Lead.objects.exists())

    @patch("apps.crm.views.verify_turnstile")
    def test_throttling_is_per_ip_shared_across_clients_and_ignores_spoofed_headers(self, verify):
        for i in range(5):
            self.assertEqual(self.submit(HTTP_X_FORWARDED_FOR=f"192.0.2.{i}").status_code, 201)
        response = APIClient().post(
            "/api/v1/crm/leads/", self.payload, format="json", HTTP_X_FORWARDED_FOR="203.0.113.1"
        )
        self.assertEqual(response.status_code, 429)
        self.assertIn("Retry-After", response)
        self.assertEqual(verify.call_count, 5)
        self.assertEqual(self.submit(REMOTE_ADDR="192.0.2.99").status_code, 201)
        for key in CaptureThrottleBucket.objects.values_list("key", flat=True):
            self.assertNotIn("127.0.0.1", key)
        CaptureThrottleBucket.objects.update(expires_at=timezone.now() - timedelta(seconds=1))
        self.assertEqual(self.submit().status_code, 201)
        call_command("prune_capture_throttles", stdout=StringIO())
        self.assertEqual(CaptureThrottleBucket.objects.count(), 1)

    @patch("apps.crm.views.verify_turnstile")
    def test_newsletter_is_case_insensitive_private_unconfirmed_and_idempotent(self, verify):
        payload = {"email": "New@Example.test", "locale": "ar", "turnstile_token": "fixture-token"}
        a = self.client.post("/api/v1/crm/newsletter/", payload, format="json")
        b = self.client.post(
            "/api/v1/crm/newsletter/",
            {**payload, "email": "new@example.test", "locale": "en"},
            format="json",
        )
        self.assertEqual(a.status_code, 202, a.content)
        self.assertEqual(a.json(), b.json())
        subscriber = NewsletterSubscriber.objects.get()
        self.assertEqual(subscriber.email, "new@example.test")
        self.assertEqual(subscriber.locale, "ar")
        self.assertFalse(subscriber.is_confirmed)
        self.assertEqual(self.client.get("/api/v1/crm/newsletter/").status_code, 405)
        self.assertEqual(
            self.client.post(
                "/api/v1/crm/newsletter/", {**payload, "is_confirmed": True}, format="json"
            ).status_code,
            400,
        )
        verify.assert_called_with("fixture-token", "127.0.0.1", action="newsletter")


class ConcurrentThrottleTests(TransactionTestCase):
    def test_concurrent_requests_cannot_exceed_the_shared_limit(self):
        def attempt(_):
            close_old_connections()
            try:
                request = APIRequestFactory().post("/", REMOTE_ADDR="192.0.2.10")
                return LeadThrottle().allow_request(request, None)
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=8) as executor:
            results = list(executor.map(attempt, range(12)))
        self.assertEqual(sum(results), 5)
        self.assertEqual(CaptureThrottleBucket.objects.get().count, 5)
