"""Tests for the shared abstracts, sanitisation and upload safety."""

from django.core.exceptions import ValidationError
from django.db import models
from django.test import SimpleTestCase, TestCase
from django.utils import translation

from apps.core.models import (
    Industry,
    PublishStatus,
    SiteSettings,
    Testimonial,
    TranslationStatus,
)
from apps.core.sanitize import clean_html, tag_signature
from apps.core.uploads import UploadTo


class SanitiserTests(SimpleTestCase):
    def test_script_tags_are_removed(self):
        self.assertEqual(clean_html("<p>ok</p><script>alert(1)</script>"), "<p>ok</p>")

    def test_style_class_and_event_attributes_are_removed(self):
        cleaned = clean_html('<p class="x" style="color:red" onclick="go()">text</p>')
        self.assertEqual(cleaned, "<p>text</p>")

    def test_allowlisted_tags_survive(self):
        html = "<h2>Head</h2><ul><li><strong>a</strong></li></ul><table><tr><td>c</td></tr></table>"
        cleaned = clean_html(html)
        for fragment in ("<h2>", "<ul>", "<li>", "<strong>", "<table>", "<td>"):
            self.assertIn(fragment, cleaned)

    def test_external_links_get_noopener(self):
        cleaned = clean_html('<a href="https://example.com">x</a>')
        self.assertIn('rel="noopener noreferrer"', cleaned)

    def test_javascript_urls_are_dropped(self):
        cleaned = clean_html('<a href="javascript:alert(1)">x</a>')
        self.assertNotIn("javascript", cleaned)

    def test_faq_profile_rejects_headings_and_images(self):
        cleaned = clean_html("<h2>no</h2><p>yes</p><img src='/x.png'>", profile="faq")
        self.assertNotIn("<h2>", cleaned)
        self.assertNotIn("<img", cleaned)
        self.assertIn("<p>yes</p>", cleaned)

    def test_empty_values_stay_empty(self):
        """A blank translation must not become the string 'None'."""
        self.assertEqual(clean_html(None), "")
        self.assertEqual(clean_html(""), "")

    def test_unknown_profile_is_an_error(self):
        with self.assertRaises(ValueError):
            clean_html("<p>x</p>", profile="nope")

    def test_tag_signature_detects_a_dropped_closing_tag(self):
        """Phase 3 relies on this to catch a translation that mangled HTML."""
        original = tag_signature("<p>a</p><p>b</p>")
        mangled = tag_signature("<p>a</p><p>b")
        self.assertNotEqual(original, mangled)


class UploadSafetyTests(SimpleTestCase):
    def test_client_filename_is_discarded(self):
        path = UploadTo("brand")(None, "evil.png")
        self.assertTrue(path.startswith("brand/"))
        self.assertNotIn("evil", path)
        self.assertTrue(path.endswith(".png"))

    def test_path_traversal_in_the_filename_cannot_escape(self):
        path = UploadTo("brand")(None, "../../etc/passwd.png")
        self.assertTrue(path.startswith("brand/"))
        self.assertNotIn("..", path)

    def test_disallowed_extension_is_rejected(self):
        for name in ("shell.svg", "doc.html", "x.php", "noext"):
            with self.subTest(filename=name), self.assertRaises(ValidationError):
                UploadTo("brand")(None, name)

    def test_names_are_unique_per_upload(self):
        upload = UploadTo("team")
        self.assertNotEqual(upload(None, "a.png"), upload(None, "a.png"))

    def test_double_extension_keeps_only_the_real_one(self):
        path = UploadTo("brand")(None, "payload.php.png")
        self.assertTrue(path.endswith(".png"))
        self.assertNotIn("php", path)


class PublishableTests(TestCase):
    def test_default_manager_returns_drafts_but_published_does_not(self):
        Testimonial.objects.create(client_name="Draft co", quote="q")
        live = Testimonial.objects.create(
            client_name="Live co", quote="q", status=PublishStatus.PUBLISHED
        )

        self.assertEqual(Testimonial.objects.count(), 2)
        self.assertEqual([t.pk for t in Testimonial.objects.published()], [live.pk])

    def test_published_at_is_stamped_on_first_publish(self):
        item = Testimonial.objects.create(client_name="A", quote="q")
        self.assertIsNone(item.published_at)

        item.status = PublishStatus.PUBLISHED
        item.save()
        first = item.published_at
        self.assertIsNotNone(first)

        item.quote = "edited"
        item.save()
        self.assertEqual(item.published_at, first, "re-saving must not move the publish date")

    def test_unpublishing_keeps_the_original_publish_date(self):
        item = Testimonial.objects.create(
            client_name="A", quote="q", status=PublishStatus.PUBLISHED
        )
        stamped = item.published_at

        item.status = PublishStatus.DRAFT
        item.save()
        self.assertEqual(item.published_at, stamped)

    def test_awaiting_translation_review_finds_machine_rows(self):
        Testimonial.objects.create(client_name="A", quote="q")
        machine = Testimonial.objects.create(
            client_name="B", quote="q", translation_status=TranslationStatus.MACHINE
        )
        self.assertEqual(
            [t.pk for t in Testimonial.objects.awaiting_translation_review()], [machine.pk]
        )


class SiteSettingsTests(TestCase):
    def test_company_facts_are_seeded_by_migration(self):
        settings_row = SiteSettings.load()
        self.assertEqual(settings_row.company_name, "Automex")
        self.assertEqual(settings_row.city, "Kent")
        self.assertEqual(settings_row.state, "WA")
        self.assertEqual(settings_row.postal_code, "98032")
        self.assertEqual(settings_row.email, "info@automex.tech")
        self.assertEqual(settings_row.phone_us, "+1 (206) 470-9284")

    def test_unsupplied_facts_are_left_empty_not_invented(self):
        settings_row = SiteSettings.load()
        self.assertIsNone(settings_row.founded_year)
        self.assertEqual(settings_row.team_size, "")
        self.assertEqual(settings_row.linkedin_url, "")

    def test_saving_always_targets_the_single_row(self):
        extra = SiteSettings(company_name="Second")
        extra.save()
        self.assertEqual(SiteSettings.objects.count(), 1)
        self.assertEqual(SiteSettings.load().company_name, "Second")

    def test_settings_cannot_be_deleted(self):
        with self.assertRaises(models.ProtectedError):
            SiteSettings.load().delete()

    def test_afghanistan_number_is_withheld_until_switched_on(self):
        """Pending a decision, so the default must be private."""
        settings_row = SiteSettings.load()
        self.assertFalse(settings_row.show_phone_af_publicly)
        self.assertEqual(settings_row.public_phone_af, "")

        settings_row.show_phone_af_publicly = True
        self.assertEqual(settings_row.public_phone_af, "+93 776 320 765")


class TranslationFallbackTests(TestCase):
    def test_a_missing_translation_falls_back_to_english(self):
        industry = Industry.objects.create(slug="logistics", name_en="Logistics", name_ar="")

        with translation.override("ar"):
            industry.refresh_from_db()
            self.assertEqual(industry.name, "Logistics")

    def test_a_present_translation_is_used(self):
        industry = Industry.objects.create(
            slug="healthcare", name_en="Healthcare", name_ar="الرعاية الصحية"
        )

        with translation.override("ar"):
            industry.refresh_from_db()
            self.assertEqual(industry.name, "الرعاية الصحية")

    def test_every_locale_has_a_column(self):
        columns = {field.name for field in Industry._meta.get_fields()}
        for code in ("en", "es", "fr", "de", "zh", "ar"):
            self.assertIn(f"name_{code}", columns)
