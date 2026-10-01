"""
Phase 0 smoke tests.

These guard the scaffold's contract rather than any feature: the backend
serves an admin and a versioned API and nothing else, CORS is not open, and
the production settings module cannot be loaded in a debug state.
"""

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase
from django.urls import reverse


class HealthTests(SimpleTestCase):
    def test_healthz_reports_ok(self):
        response = self.client.get("/healthz")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")


class ApiSurfaceTests(SimpleTestCase):
    def test_api_is_versioned_and_public(self):
        response = self.client.get("/api/v1/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["version"], "v1")

    def test_backend_serves_no_public_html_root(self):
        """The frontend owns every public page; / must not resolve here."""
        self.assertEqual(self.client.get("/").status_code, 404)


class AdminTests(TestCase):
    def test_admin_login_renders_with_unfold(self):
        response = self.client.get(reverse("admin:login"))
        self.assertEqual(response.status_code, 200)
        body = response.content.decode()
        # Unfold must win over django.contrib.admin's templates.
        self.assertIn("unfold/css/styles.css", body)
        self.assertIn("Automex", body)

    def test_admin_requires_authentication(self):
        response = self.client.get("/admin/", follow=False)
        self.assertIn(response.status_code, (301, 302))

    def test_superuser_can_reach_the_dashboard(self):
        get_user_model().objects.create_superuser(
            username="tester", email="t@example.com", password="pw-for-tests-only"
        )
        self.client.login(username="tester", password="pw-for-tests-only")
        response = self.client.get("/admin/")
        self.assertEqual(response.status_code, 200)


class SecurityConfigTests(SimpleTestCase):
    """CLAUDE.md section 10 — these are the settings a mistake would hide in."""

    def test_cors_is_never_open_to_all_origins(self):
        self.assertFalse(getattr(settings, "CORS_ALLOW_ALL_ORIGINS", False))

    def test_cors_is_scoped_to_the_api(self):
        self.assertEqual(settings.CORS_URLS_REGEX, r"^/api/.*$")

    def test_production_settings_disable_debug(self):
        from config.settings import prod  # noqa: PLC0415

        self.assertFalse(prod.DEBUG)
        self.assertTrue(prod.SECURE_SSL_REDIRECT)
        self.assertTrue(prod.SESSION_COOKIE_SECURE)
        self.assertTrue(prod.CSRF_COOKIE_SECURE)


class LocaleConfigTests(SimpleTestCase):
    """The six locales are a build constraint, not a setting to drift."""

    def test_six_locales_are_configured(self):
        self.assertEqual(
            [code for code, _ in settings.LANGUAGES],
            ["en", "es", "fr", "de", "zh", "ar"],
        )

    def test_english_is_the_source_of_truth(self):
        self.assertEqual(settings.LANGUAGE_CODE, "en")
        self.assertEqual(settings.MODELTRANSLATION_DEFAULT_LANGUAGE, "en")
        self.assertEqual(settings.MODELTRANSLATION_FALLBACK_LANGUAGES, ("en",))

    def test_arabic_is_the_only_rtl_locale(self):
        self.assertEqual(settings.RTL_LANGUAGES, ["ar"])

    def test_every_locale_has_language_info(self):
        """A code Django does not know crashes any admin template that
        renders language info. Regression guard for the bare "zh"."""
        from django.utils.translation import get_language_info  # noqa: PLC0415

        for code, _ in settings.LANGUAGES:
            with self.subTest(locale=code):
                self.assertTrue(get_language_info(code)["code"])

    def test_admin_is_not_localised(self):
        """Admin is English only, so LocaleMiddleware must stay out."""
        self.assertNotIn("django.middleware.locale.LocaleMiddleware", settings.MIDDLEWARE)
