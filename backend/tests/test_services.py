"""Tests for the six service lines and the content that fills a service page."""

from django.test import TestCase

from apps.services.models import FAQ, ProcessStep, Service, ServiceKey, ServiceOffering

EXPECTED_SLUGS = [
    "digital-marketing",
    "ai-automation",
    "custom-software",
    "web-development",
    "mobile-development",
    "cyber-security",
]


class ServiceSetTests(TestCase):
    def test_all_six_services_exist_in_order(self):
        self.assertEqual(list(Service.objects.values_list("slug", flat=True)), EXPECTED_SLUGS)

    def test_keys_match_the_public_slugs(self):
        """A serializer goes from key to route with no lookup table."""
        for service in Service.objects.all():
            self.assertEqual(service.key, service.slug)

    def test_choice_set_matches_the_seeded_rows(self):
        self.assertEqual(sorted(ServiceKey.values), sorted(EXPECTED_SLUGS))

    def test_marketing_copy_is_not_invented(self):
        for service in Service.objects.all():
            with self.subTest(service=service.slug):
                self.assertEqual(service.hero_headline, "")
                self.assertEqual(service.intro, "")
                self.assertEqual(service.body, "")

    def test_slug_defaults_to_the_key(self):
        service = Service.objects.create(key="custom-key-test", name_en="Test")
        self.assertEqual(service.slug, "custom-key-test")

    def test_an_explicit_slug_is_respected(self):
        service = Service.objects.create(key="another-key", slug="different", name_en="Test")
        self.assertEqual(service.slug, "different")


class ServiceContentTests(TestCase):
    def setUp(self):
        self.service = Service.objects.get(key="cyber-security")

    def test_offerings_process_and_faqs_relate_to_a_service(self):
        ServiceOffering.objects.create(
            service=self.service, title_en="Pen testing", description_en="We break it."
        )
        ProcessStep.objects.create(
            service=self.service, order=1, title_en="Scope", description_en="Agree the targets."
        )
        FAQ.objects.create(service=self.service, question_en="How long?", answer_en="<p>Weeks.</p>")

        self.assertEqual(self.service.offerings.count(), 1)
        self.assertEqual(self.service.process_steps.count(), 1)
        self.assertEqual(self.service.faqs.count(), 1)

    def test_a_general_faq_needs_no_service(self):
        faq = FAQ.objects.create(question_en="Where are you?", answer_en="<p>Kent, WA.</p>")
        self.assertIsNone(faq.service)

    def test_deleting_a_service_takes_its_content_with_it(self):
        ServiceOffering.objects.create(service=self.service, title_en="x", description_en="y")
        self.service.delete()
        self.assertEqual(ServiceOffering.objects.count(), 0)

    def test_ordering_is_by_order_then_pk(self):
        for position in (30, 10, 20):
            ServiceOffering.objects.create(
                service=self.service, order=position, title_en=f"o{position}", description_en="d"
            )
        self.assertEqual(
            [o.order for o in self.service.offerings.all()],
            [10, 20, 30],
        )


class RichTextSanitisationTests(TestCase):
    """Rich text is cleaned on write, so the database never holds bad markup."""

    def test_service_body_is_sanitised_on_save(self):
        service = Service.objects.get(key="web-development")
        service.body_en = '<p>Safe</p><script>alert(1)</script><p onclick="x()">Also safe</p>'
        service.save()
        service.refresh_from_db()

        self.assertNotIn("script", service.body_en)
        self.assertNotIn("onclick", service.body_en)
        self.assertIn("<p>Safe</p>", service.body_en)

    def test_every_locale_column_is_sanitised_not_just_the_active_one(self):
        service = Service.objects.get(key="ai-automation")
        service.body_en = "<p>en</p><script>a</script>"
        service.body_ar = "<p>ar</p><script>b</script>"
        service.body_zh = "<p>zh</p><script>c</script>"
        service.save()
        service.refresh_from_db()

        for value in (service.body_en, service.body_ar, service.body_zh):
            self.assertNotIn("script", value)

    def test_faq_answers_use_the_restricted_profile(self):
        faq = FAQ.objects.create(
            service=None,
            question_en="Q",
            answer_en="<h2>Heading</h2><p>Body</p><img src='/x.png'>",
        )
        faq.refresh_from_db()

        self.assertNotIn("<h2>", faq.answer_en)
        self.assertNotIn("<img", faq.answer_en)
        self.assertIn("<p>Body</p>", faq.answer_en)

    def test_plain_text_fields_are_left_alone(self):
        """intro is plain text, so angle brackets are content, not markup."""
        service = Service.objects.get(key="mobile-development")
        service.intro_en = "Scaling 1 < 2 and 3 > 2"
        service.save()
        service.refresh_from_db()
        self.assertEqual(service.intro_en, "Scaling 1 < 2 and 3 > 2")
