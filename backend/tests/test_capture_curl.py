"""Real curl over HTTP into Django and PostgreSQL; only Cloudflare transport is simulated."""

import json
import shutil
import subprocess
from io import BytesIO
from unittest import skipUnless
from unittest.mock import patch
from urllib.parse import urlencode

from django.core import mail
from django.test import LiveServerTestCase, override_settings

from apps.crm.models import Lead, NewsletterSubscriber


@skipUnless(shutil.which("curl"), "curl is required for HTTP integration checks")
@override_settings(
    TURNSTILE_SECRET_KEY="test-only-secret",
    TURNSTILE_ALLOWED_HOSTNAMES=["localhost"],
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    LEAD_ALERT_RECIPIENTS=["test-inbox@example.test"],
)
class CurlCaptureTests(LiveServerTestCase):
    def setUp(self):
        self.payload = {
            "full_name": "CURL TEST - not a customer",
            "email": "curl-check@example.test",
            "message": "CURL TEST - مرحبا — a test request",
            "locale": "ar",
            "source_path": "/ar/contact",
            "utm_source": "curl-test",
            "turnstile_token": "fixture-lead",
            "website": "",
        }
        self.provider = patch("apps.crm.turnstile.build_opener").start()
        self.addCleanup(patch.stopall)
        self.provider.return_value.open.side_effect = self.provider_response

    def provider_response(self, request, **kwargs):
        token = json.loads(request.data)["response"]
        if token == "rejected-token":
            result = {"success": False, "error-codes": ["timeout-or-duplicate"]}
        else:
            result = {
                "success": True,
                "hostname": "localhost",
                "action": "newsletter" if token == "fixture-newsletter" else "lead",
            }
        return BytesIO(json.dumps(result).encode())

    def curl(self, path="leads/", payload=None, *, form=False, raw=None, method=None):
        args = [
            "curl",
            "--silent",
            "--show-error",
            "--max-time",
            "15",
            "--noproxy",
            "*",
            "--include",
            "--header",
            "Accept: application/json",
            "--user-agent",
            "Automex-curl-integration-test",
        ]
        body = None
        if not method:
            data = self.payload if payload is None else payload
            body = raw if raw is not None else (urlencode(data) if form else json.dumps(data))
            args += [
                "--header",
                "Content-Type: "
                + ("application/x-www-form-urlencoded" if form else "application/json"),
                "--data-binary",
                "@-",
            ]
        else:
            args += ["--request", method]
        args.append(self.live_server_url + "/api/v1/crm/" + path)
        result = subprocess.run(
            args, input=body, capture_output=True, text=True, check=True, timeout=20
        )
        headers, content = result.stdout.split("\n\n", 1)
        code = int(headers.splitlines()[0].split()[1])
        print(f"curl {method or 'POST'} {path}: {code}")
        self.assertIn("cache-control: no-store", headers.lower())
        return code, json.loads(content), headers

    def test_json_submission_persists_unicode_attribution_and_committed_alert(self):
        code, data, _ = self.curl()
        self.assertEqual(code, 201, data)
        self.assertEqual(set(data), {"detail"})
        record = Lead.objects.get()
        self.assertEqual(record.message, self.payload["message"])
        self.assertEqual(record.locale, "ar")
        self.assertEqual(record.utm_source, "curl-test")
        self.assertEqual(record.source_path, "/ar/contact")
        self.assertEqual(record.status, "new")
        self.assertIsNotNone(record.alert_sent_at)
        self.assertEqual(len(mail.outbox), 1)
        self.assertNotIn(record.email, mail.outbox[0].body)

    def test_form_encoded_submission_and_newsletter_duplicate(self):
        self.assertEqual(self.curl(form=True)[0], 201)
        payload = {
            "email": "Curl-News@Example.test",
            "locale": "fr",
            "turnstile_token": "fixture-newsletter",
        }
        a = self.curl("newsletter/", payload, form=True)
        b = self.curl("newsletter/", {**payload, "email": "curl-news@example.test"})
        self.assertEqual((a[0], b[0]), (202, 202))
        self.assertEqual(a[1], b[1])
        subscriber = NewsletterSubscriber.objects.get()
        self.assertEqual(subscriber.email, "curl-news@example.test")
        self.assertFalse(subscriber.is_confirmed)
        self.assertEqual(Lead.objects.count(), 1)

    def test_invalid_json_email_and_staff_field_tampering(self):
        self.assertEqual(self.curl(raw="{")[0], 400)
        self.assertEqual(self.curl(payload={**self.payload, "email": "invalid"})[0], 400)
        self.assertEqual(self.curl(payload={**self.payload, "internal_notes": "injected"})[0], 400)
        self.assertEqual(self.curl(payload={**self.payload, "status": "won"}, form=True)[0], 400)
        self.assertFalse(Lead.objects.exists())
        self.provider.return_value.open.assert_not_called()

    def test_honeypot_and_replayed_token_create_no_records(self):
        self.assertEqual(self.curl(payload={**self.payload, "website": "filled-by-bot"})[0], 201)
        self.provider.return_value.open.assert_not_called()
        self.assertEqual(
            self.curl(payload={**self.payload, "turnstile_token": "rejected-token"})[0], 400
        )
        self.assertFalse(Lead.objects.exists())
        self.assertEqual(len(mail.outbox), 0)

    @override_settings(TURNSTILE_SECRET_KEY="")
    def test_unconfigured_provider_returns_503_without_persisting(self):
        self.assertEqual(self.curl()[0], 503)
        self.assertFalse(Lead.objects.exists())
        self.provider.return_value.open.assert_not_called()

    def test_sixth_request_is_throttled_and_crm_reads_are_forbidden(self):
        for _ in range(5):
            self.assertEqual(self.curl()[0], 201)
        code, _, headers = self.curl()
        self.assertEqual(code, 429)
        self.assertIn("retry-after:", headers.lower())
        self.assertEqual(Lead.objects.count(), 5)
        self.assertEqual(self.provider.return_value.open.call_count, 5)
        self.assertEqual(self.curl(method="GET")[0], 405)
        self.assertEqual(self.curl("newsletter/", method="GET")[0], 405)
