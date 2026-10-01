"""Translation writes must never overwrite human content or publish machine text."""

import json
from io import BytesIO, StringIO
from unittest.mock import Mock, patch
from urllib.error import HTTPError, URLError

from django.conf import settings
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import Client, RequestFactory, SimpleTestCase, TestCase, override_settings
from django.urls import reverse
from django.utils import translation

from apps.core.models import SiteSettings, Tool
from apps.crm.models import Lead
from apps.portfolio.models import CaseStudy
from apps.services.models import FAQ, Service
from apps.translations.client import GroqClient, NoRedirects, TranslationError
from apps.translations.models import TranslationLog
from apps.translations.services import GroqTranslator
from apps.translations.validation import validate_translation
from apps.web_development.models import WebDevelopmentCaseStudy
from tests.test_admin import AdminSmokeTestCase


class FakeClient:
    def __init__(self, callback=None):
        self.calls = []
        self.callback = callback

    def translate(self, fields, locale, terms):
        self.calls.append((fields, locale, terms))
        if self.callback:
            return self.callback(fields, locale, terms), 1
        return {key: value["text"] + f" [{locale}]" for key, value in fields.items()}, 1


class TranslationWriteTests(TestCase):
    def setUp(self):
        self.service = Service.objects.get(key="cyber-security")
        self.service.name_en = "Cyber Security"
        self.service.name_fr = "Traduction humaine"
        self.service.status = "published"
        self.service.translation_status = "reviewed"
        self.service.save()

    def test_only_missing_columns_are_filled_and_record_becomes_machine_draft(self):
        client = FakeClient()
        # The descriptor must not mistake English fallback for a stored translation.
        with translation.override("ar"):
            logs = GroqTranslator(client=client).translate(self.service)
        self.service.refresh_from_db()
        self.assertEqual(self.service.name_en, "Cyber Security")
        self.assertEqual(self.service.name_fr, "Traduction humaine")
        for lang in ("es", "de", "zh", "ar"):
            self.assertEqual(getattr(self.service, f"name_{lang}"), f"Cyber Security [{lang}]")
        self.assertEqual(self.service.status, "draft")
        self.assertEqual(self.service.translation_status, "machine")
        self.assertFalse(Service.objects.published().filter(pk=self.service.pk).exists())
        self.assertEqual(sum(log.status == "success" for log in logs), 4)
        self.assertEqual(len({log.run_id for log in logs}), 1)
        self.assertNotIn("Cyber Security", str(list(TranslationLog.objects.values())))
        second = GroqTranslator(client=client).translate(self.service)
        self.assertTrue(all(log.status == "skipped" for log in second))
        self.assertEqual(len(client.calls), 4)

    def test_existing_machine_or_reviewed_text_and_english_are_never_overwritten(self):
        for code, _ in settings.LANGUAGES:
            if code != "en":
                setattr(self.service, f"name_{code}", "Existing")
        self.service.save()
        client = FakeClient()
        GroqTranslator(client=client).translate(self.service)
        self.service.refresh_from_db()
        self.assertEqual(client.calls, [])
        self.assertEqual(self.service.status, "published")
        self.assertEqual(self.service.translation_status, "reviewed")

    def test_partial_provider_failure_keeps_successes_and_can_be_retried(self):
        def provider(fields, locale, terms):
            if locale == "ar":
                raise TranslationError("http_429", 3)
            return {key: value["text"] + " translated" for key, value in fields.items()}

        client = FakeClient(provider)
        with self.assertLogs("apps.translations.services", level="WARNING"):
            logs = GroqTranslator(client=client).translate(self.service, locales=["zh", "ar"])
        self.service.refresh_from_db()
        self.assertEqual([log.status for log in logs], ["success", "failed"])
        self.assertIsNone(self.service.__dict__["name_ar"])
        self.assertEqual(self.service.name_zh, "Cyber Security translated")
        GroqTranslator(client=FakeClient()).translate(self.service, locales=["zh", "ar"])
        self.service.refresh_from_db()
        self.assertEqual(self.service.name_zh, "Cyber Security translated")
        self.assertEqual(self.service.name_ar, "Cyber Security [ar]")

    def test_concurrent_human_translation_wins(self):
        def provider(fields, locale, terms):
            Service.objects.filter(pk=self.service.pk).update(name_ar="Human edit")
            return dict.fromkeys(fields, "Machine text")

        logs = GroqTranslator(client=FakeClient(provider)).translate(self.service, locales=["ar"])
        self.service.refresh_from_db()
        self.assertEqual(self.service.name_ar, "Human edit")
        self.assertEqual(self.service.status, "published")
        self.assertEqual(logs[0].error_code, "record_changed")

    def test_concurrent_english_change_discards_stale_output(self):
        def provider(fields, locale, terms):
            Service.objects.filter(pk=self.service.pk).update(name_en="Changed source")
            return dict.fromkeys(fields, "Stale output")

        logs = GroqTranslator(client=FakeClient(provider)).translate(self.service, locales=["ar"])
        self.service.refresh_from_db()
        self.assertFalse(self.service.__dict__["name_ar"])
        self.assertEqual(logs[0].status, "skipped")

    def test_invalid_batch_does_not_partially_write_or_change_status(self):
        self.service.intro_en = "Intro"
        self.service.save()
        client = FakeClient(
            lambda fields, locale, terms: {"name": "Good", "intro": "<script>x</script>"}
        )
        with self.assertLogs("apps.translations.services", level="WARNING"):
            logs = GroqTranslator(client=client).translate(self.service, locales=["ar"])
        self.service.refresh_from_db()
        self.assertFalse(self.service.__dict__["name_ar"])
        self.assertFalse(self.service.__dict__["intro_ar"])
        self.assertEqual(self.service.status, "published")
        self.assertEqual(logs[0].error_code, "unexpected_html")

    def test_schema_mismatch_and_length_overflow_are_logged(self):
        for output, code in [
            ({"wrong": "text"}, "field_mismatch"),
            ({"name": "x" * 81}, "length_exceeded"),
        ]:
            with (
                self.subTest(code=code),
                self.assertLogs("apps.translations.services", level="WARNING"),
            ):
                logs = GroqTranslator(
                    client=FakeClient(lambda *args, output=output: output)
                ).translate(self.service, locales=["ar"])
                self.assertEqual(logs[0].error_code, code)

    @override_settings(GROQ_BATCH_CHARS=15)
    def test_field_batches_are_bounded_and_oversized_source_is_not_truncated(self):
        self.service.intro_en = "Short intro"
        self.service.body_en = "<p>" + "Very long body" * 10 + "</p>"
        self.service.save()
        client = FakeClient()
        with self.assertLogs("apps.translations.services", level="WARNING"):
            logs = GroqTranslator(client=client).translate(self.service, locales=["ar"])
        self.assertEqual(len(client.calls), 2)
        self.assertIn("source_too_long", [log.error_code for log in logs])
        self.service.refresh_from_db()
        self.assertFalse(self.service.__dict__["body_ar"])

    def test_proxy_translates_shared_row_and_child_without_publish_field_works(self):
        case = WebDevelopmentCaseStudy.objects.create(
            service=Service.objects.get(key="web-development"),
            title_en="Example",
            slug="example",
            client_name="Example client",
        )
        GroqTranslator(client=FakeClient()).translate(case, locales=["ar"])
        self.assertEqual(CaseStudy.objects.get(pk=case.pk).title_ar, "Example [ar]")
        faq = FAQ.objects.create(question_en="Question?", answer_en="Answer")
        GroqTranslator(client=FakeClient()).translate(faq, locales=["zh"])
        faq.refresh_from_db()
        self.assertEqual(faq.translation_status, "machine")
        self.assertEqual(faq.answer_zh, "Answer [zh]")

    def test_private_models_and_english_target_are_refused(self):
        for obj in (Lead(pk=1), Tool(pk=1)):
            with self.assertRaises(TranslationError):
                GroqTranslator(client=FakeClient()).translate(obj)
        with self.assertRaises(TranslationError):
            GroqTranslator(client=FakeClient()).translate(self.service, locales=["en"])

    @override_settings(GROQ_API_KEY="")
    def test_missing_configuration_is_safe_and_logged(self):
        with self.assertLogs("apps.translations.services", level="WARNING"):
            logs = GroqTranslator().translate(self.service, locales=["ar"])
        self.assertEqual(logs[0].error_code, "configuration")
        self.service.refresh_from_db()
        self.assertEqual(self.service.translation_status, "reviewed")


class TranslationValidationTests(SimpleTestCase):
    def test_preserves_attributes_and_structure_in_all_target_languages(self):
        source = '<p>Automex <a href="https://example.com" rel="noopener noreferrer">Link</a></p>'
        for text in ("Enlace", "Lien", "Verweis", "链接", "رابط"):
            output = source.replace("Link", text)
            self.assertEqual(
                validate_translation(source, output, rich=True, terms=["Automex"]), output
            )

    def test_changed_markup_urls_attributes_numbers_names_are_rejected(self):
        source = (
            '<p>Automex 10 <a href="https://example.com" rel="noopener noreferrer">Link</a></p>'
        )
        for output in [
            source.replace("example.com", "evil.example"),
            source.replace("<p>", "<p onclick='x()'>"),
            source.replace("10", "100"),
            source.replace("Automex", "Changed"),
            '<a href="https://example.com" rel="noopener noreferrer"><p>Automex 10 Link</p></a>',
        ]:
            with self.subTest(output=output), self.assertRaises(TranslationError):
                validate_translation(source, output, rich=True, terms=["Automex"])

    def test_plain_text_rejects_html_empty_fences_controls_and_oversized_output(self):
        for output in ("", " ", "<p>text</p>", "```text```", "text\x00", "x" * 21):
            with self.subTest(output=output), self.assertRaises(TranslationError):
                validate_translation("Text", output, max_length=20)


@override_settings(
    GROQ_API_KEY="dummy-key-for-tests", GROQ_MAX_ATTEMPTS=3, GROQ_RETRY_MAX_SECONDS=15
)
class GroqClientTests(SimpleTestCase):
    def response(self, content=None, finish="stop"):
        return BytesIO(
            json.dumps(
                {
                    "choices": [
                        {
                            "finish_reason": finish,
                            "message": {"content": json.dumps(content or {"name": "Translated"})},
                        }
                    ]
                }
            ).encode()
        )

    def test_request_uses_json_mode_model_timeout_and_no_redirects(self):
        opener = Mock()
        opener.open.return_value = self.response()
        data, attempts = GroqClient(opener=opener).translate(
            {"name": {"text": "Name"}}, "ar", ["Automex"]
        )
        request = opener.open.call_args.args[0]
        payload = json.loads(request.data)
        self.assertEqual(data, {"name": "Translated"})
        self.assertEqual(attempts, 1)
        self.assertEqual(payload["response_format"], {"type": "json_object"})
        self.assertEqual(payload["model"], settings.GROQ_MODEL)
        self.assertEqual(opener.open.call_args.kwargs["timeout"], settings.GROQ_TIMEOUT)
        self.assertIsNone(
            NoRedirects().redirect_request(None, None, 302, "", {}, "https://elsewhere.example")
        )

    def test_protected_names_roundtrip_without_transliteration(self):
        opener = Mock()

        def response(request, **kwargs):
            payload = json.loads(request.data)
            fields = json.loads(payload["messages"][1]["content"])["fields"]
            self.assertNotIn("Automex", fields["name"])
            self.assertLess(payload["max_completion_tokens"], settings.GROQ_MAX_COMPLETION_TOKENS)
            return self.response({"name": fields["name"].replace("Contact", "اتصل")})

        opener.open.side_effect = response
        output, _ = GroqClient(opener=opener).translate(
            {"name": {"text": "Contact Automex"}}, "ar", ["Automex"]
        )
        self.assertEqual(output["name"], "اتصل Automex")

    def test_dropped_protected_name_is_rejected(self):
        opener = Mock()
        opener.open.return_value = self.response({"name": "اتصل"})
        with self.assertRaises(TranslationError) as error:
            GroqClient(opener=opener).translate(
                {"name": {"text": "Contact Automex"}}, "ar", ["Automex"]
            )
        self.assertEqual(error.exception.code, "proper_noun_changed")

    def test_retry_after_and_exponential_backoff(self):
        opener, sleep = Mock(), Mock()
        opener.open.side_effect = [
            HTTPError("url", 429, "private error", {"Retry-After": "3"}, BytesIO()),
            URLError("private error"),
            self.response(),
        ]
        _, attempts = GroqClient(opener=opener, sleep=sleep).translate(
            {"name": {"text": "Name"}}, "es", []
        )
        self.assertEqual(attempts, 3)
        self.assertEqual([call.args[0] for call in sleep.call_args_list], [3, 2])

    def test_nonretryable_and_long_rate_limits_do_not_sleep_or_leak_provider_message(self):
        for code, headers in [(401, {}), (429, {"Retry-After": "60"})]:
            opener, sleep = Mock(), Mock()
            opener.open.side_effect = HTTPError(
                "url", code, "PRIVATE PROVIDER TEXT", headers, BytesIO()
            )
            with self.assertRaises(TranslationError) as error:
                GroqClient(opener=opener, sleep=sleep).translate(
                    {"name": {"text": "Name"}}, "ar", []
                )
            self.assertEqual(error.exception.code, f"http_{code}")
            self.assertNotIn("PRIVATE", str(error.exception))
            sleep.assert_not_called()

    def test_malformed_and_truncated_responses_fail_closed(self):
        for response in (BytesIO(b"not-json"), self.response(finish="length")):
            opener = Mock()
            opener.open.return_value = response
            with self.assertRaises(TranslationError):
                GroqClient(opener=opener).translate({"name": {"text": "Name"}}, "ar", [])

    @override_settings(GROQ_API_URL="https://untrusted.example/translate")
    def test_api_key_cannot_be_sent_to_another_host(self):
        with self.assertRaises(TranslationError):
            GroqClient()


class TranslationAdminTests(AdminSmokeTestCase):
    def test_bulk_requires_confirmation_and_records_actor(self):
        service = Service.objects.first()
        url = reverse("admin:services_service_changelist")
        data = {"action": "auto_translate", "_selected_action": [str(service.pk)]}
        with patch("apps.translations.services.GroqClient", return_value=FakeClient()) as factory:
            response = self.client.post(url, data)
            self.assertContains(response, "Translate saved content")
            factory.assert_not_called()
            response = self.client.post(url, {**data, "confirm_translation": "yes"})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            TranslationLog.objects.filter(actor=self.user, status="success").count(), 5
        )

    def test_singleton_has_saved_record_action_and_get_is_read_only(self):
        url = reverse("admin:core_sitesettings_translate", args=[SiteSettings.SINGLETON_PK])
        with patch("apps.translations.services.GroqClient") as client:
            self.assertContains(self.client.get(url), "Save any edits")
            client.assert_not_called()
        response = self.client.get(reverse("admin:core_sitesettings_change", args=[1]))
        self.assertContains(response, url)

    def test_view_only_staff_cannot_execute_translation(self):
        staff = get_user_model().objects.create_user(username="translator-viewer", is_staff=True)
        staff.user_permissions.add(Permission.objects.get(codename="view_service"))
        request = RequestFactory().get("/")
        request.user = staff
        self.assertNotIn("auto_translate", admin.site._registry[Service].get_actions(request))
        self.client.force_login(staff)
        url = reverse("admin:services_service_translate", args=[Service.objects.first().pk])
        self.assertEqual(self.client.post(url, {"confirm_translation": "yes"}).status_code, 403)

    @override_settings(TRANSLATION_ADMIN_MAX_RECORDS=1)
    def test_oversized_selection_is_rejected_before_provider_calls(self):
        with patch("apps.translations.services.GroqClient") as provider:
            response = self.client.post(
                reverse("admin:services_service_changelist"),
                {
                    "action": "auto_translate",
                    "_selected_action": list(Service.objects.values_list("pk", flat=True)),
                    "confirm_translation": "yes",
                },
            )
            provider.assert_not_called()
        self.assertEqual(response.status_code, 302)

    def test_audit_log_is_read_only_and_accessible(self):
        log = GroqTranslator(client=FakeClient(), actor=self.user).translate(
            Service.objects.first(), locales=["ar"]
        )[0]
        url = reverse("admin:translations_translationlog_change", args=[log.pk])
        self.assertContains(self.client.get(url), "Open record")
        self.assertEqual(self.client.post(url, {"status": "success"}).status_code, 403)
        self.assertEqual(
            self.client.get(reverse("admin:translations_translationlog_changelist")).status_code,
            200,
        )


class TranslationCommandTests(TestCase):
    def test_command_requires_explicit_content_ids_and_rejects_private_models(self):
        with self.assertRaises(CommandError):
            call_command("translate_content", "crm.Lead", "1", stdout=StringIO())
        with self.assertRaises(CommandError):
            call_command("translate_content", "services.Service", "999999", stdout=StringIO())
        service = Service.objects.first()
        with patch("apps.translations.services.GroqClient", return_value=FakeClient()):
            output = StringIO()
            call_command(
                "translate_content",
                "services.Service",
                str(service.pk),
                locales=["ar"],
                stdout=output,
            )
        self.assertIn("ar: success", output.getvalue())


class TranslationRequestSafetyTests(AdminSmokeTestCase):
    def test_custom_translation_post_requires_csrf(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)
        url = reverse("admin:services_service_translate", args=[Service.objects.first().pk])
        with patch("apps.translations.services.GroqClient") as provider:
            self.assertEqual(client.post(url, {"confirm_translation": "yes"}).status_code, 403)
            provider.assert_not_called()

    def test_service_proxy_translation_rejects_other_services(self):
        record = CaseStudy.objects.create(
            title_en="Example", slug="example", service=Service.objects.get(key="cyber-security")
        )
        url = reverse("admin:web_development_webdevelopmentcasestudy_translate", args=[record.pk])
        self.assertEqual(self.client.get(url).status_code, 404)
