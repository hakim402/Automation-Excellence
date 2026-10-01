"""Phase 1 regressions: editing, review gates and service navigation."""

from django.conf import settings
from django.contrib import admin
from django.test import TestCase
from django.urls import reverse
from django.utils import translation
from unfold.contrib.forms.widgets import WysiwygWidget
from unfold.utils import display_for_label

from apps.core.admin_mixins import TRANSLATION_STATUS_COLOURS
from apps.core.models import SiteSettings, Stat, TeamMember, Testimonial
from apps.services.models import FAQ, Service, ServiceOffering
from config.admin_navigation import SERVICE_GROUPS
from tests.test_admin import AdminSmokeTestCase


class PublicationGateTests(TestCase):
    def test_machine_content_is_hidden_even_when_marked_published(self):
        item = Testimonial.objects.create(
            client_name="Placeholder",
            quote_en="Example",
            status="published",
            translation_status="machine",
        )
        self.assertFalse(Testimonial.objects.published().filter(pk=item.pk).exists())
        self.assertFalse(item.is_published)
        item.translation_status = "reviewed"
        item.save()
        self.assertTrue(Testimonial.objects.published().filter(pk=item.pk).exists())

    def test_service_requires_publication_review_and_active_state(self):
        service = Service.objects.get(key="cyber-security")
        self.assertFalse(Service.objects.published().exists())
        service.status = "published"
        service.save(update_fields=["status"])
        service.refresh_from_db()
        self.assertIsNotNone(service.published_at)
        self.assertTrue(Service.objects.published().filter(pk=service.pk).exists())
        service.translation_status = "machine"
        service.save()
        self.assertFalse(Service.objects.published().exists())
        service.translation_status = "reviewed"
        service.is_active = False
        service.save()
        self.assertFalse(service.is_published)
        self.assertFalse(Service.objects.published().exists())

    def test_team_and_stats_follow_editor_order(self):
        for position in (30, 10, 20):
            TeamMember.objects.create(name=f"Placeholder {position}", order=position)
            Stat.objects.create(label_en="Placeholder", value="0", order=position)
        for model in (TeamMember, Stat):
            self.assertEqual(list(model.objects.values_list("order", flat=True)), [10, 20, 30])


class EditingWorkflowTests(AdminSmokeTestCase):
    def service_data(self):
        service = Service.objects.get(key="cyber-security")
        data = {
            "key": service.key,
            "slug": service.slug,
            "order": "60",
            "status": "draft",
            "translation_status": "none",
            "is_active": "on",
            "name_en": service.name_en,
        }
        for prefix in ("offerings", "process_steps", "faqs"):
            data.update(
                {
                    f"{prefix}-TOTAL_FORMS": "0",
                    f"{prefix}-INITIAL_FORMS": "0",
                    f"{prefix}-MIN_NUM_FORMS": "0",
                    f"{prefix}-MAX_NUM_FORMS": "1000",
                }
            )
        return service, data

    def test_admin_saves_two_languages_and_sanitises_inline_rich_text(self):
        service, data = self.service_data()
        data.update(
            {
                "name_ar": "الأمن السيبراني",
                "body_en": "<p>Example</p><script>x()</script>",
                "offerings-TOTAL_FORMS": "1",
                "offerings-0-order": "1",
                "offerings-0-title_en": "Example offering",
                "offerings-0-title_ar": "خدمة",
                "offerings-0-description_en": "Example description",
                "offerings-0-translation_status": "reviewed",
                "faqs-TOTAL_FORMS": "1",
                "faqs-0-order": "1",
                "faqs-0-question_en": "Example question?",
                "faqs-0-question_ar": "سؤال؟",
                "faqs-0-answer_en": "<h2>Title</h2><p>Answer</p><script>x()</script>",
                "faqs-0-answer_ar": "<p>إجابة</p>",
                "faqs-0-translation_status": "reviewed",
            }
        )
        response = self.client.post(
            reverse("admin:services_service_change", args=[service.pk]), data
        )
        self.assertEqual(response.status_code, 302)
        service.refresh_from_db()
        self.assertNotIn("script", service.body_en)
        offering = ServiceOffering.objects.get(service=service)
        self.assertEqual(offering.title_ar, "خدمة")
        with translation.override("de"):
            self.assertEqual(offering.title, "Example offering")
        faq = FAQ.objects.get(service=service)
        self.assertEqual(faq.answer_ar, "<p>إجابة</p>")
        self.assertNotIn("<h2>", faq.answer_en)
        self.assertNotIn("script", faq.answer_en)

    def test_blank_english_name_is_rejected_without_requiring_other_locales(self):
        service, data = self.service_data()
        data["name_en"] = ""
        response = self.client.post(
            reverse("admin:services_service_change", args=[service.pk]), data
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("name_en", response.context["adminform"].form.errors)
        self.assertNotIn("name_ar", response.context["adminform"].form.errors)

    def test_editor_widgets_and_inline_tabs_are_scoped_to_rich_text(self):
        service, _ = self.service_data()
        response = self.client.get(reverse("admin:services_service_change", args=[service.pk]))
        form = response.context["adminform"].form
        self.assertIsInstance(form.fields["body_ar"].widget, WysiwygWidget)
        self.assertNotIsInstance(form.fields["intro_ar"].widget, WysiwygWidget)
        for inline in response.context["inline_admin_formsets"]:
            tabs = [
                name for name, options in inline.fieldsets if "tab" in options.get("classes", ())
            ]
            self.assertEqual(tabs, [label for _, label in settings.LANGUAGES])
        self.assertContains(response, 'id="id_body_ar-input"')
        self.assertContains(response, 'input="id_body_ar-input"')

    def test_settings_review_status_is_editable(self):
        request = self.client.get(reverse("admin:core_sitesettings_change", args=[1])).wsgi_request
        form = admin.site._registry[SiteSettings].get_form(request)
        self.assertIn("translation_status", form.base_fields)

    def test_machine_badge_uses_warning_colour(self):
        value = admin.site._registry[Service].translation_badge(
            Service(translation_status="machine")
        )
        rendered = display_for_label(value, "-", TRANSLATION_STATUS_COLOURS)
        self.assertIn("Machine translated", rendered)
        self.assertIn("orange", rendered)

    def test_service_sidebar_links_load_and_filter_results(self):
        for service in Service.objects.all():
            ServiceOffering.objects.create(
                service=service, title_en=service.key, description_en="Example"
            )
        for group in SERVICE_GROUPS:
            for item in group["items"]:
                with self.subTest(link=item["link"]):
                    response = self.client.get(item["link"])
                    self.assertEqual(response.status_code, 200)
                    if item["title"] == "Offerings":
                        self.assertEqual(response.context["cl"].result_count, 1)
