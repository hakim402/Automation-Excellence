"""Phase 2 acceptance: publishing, actual admin writes, proxies, and media."""

from datetime import date
from io import BytesIO
from tempfile import TemporaryDirectory

from django import forms
from django.apps import apps
from django.conf import settings
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError, transaction
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import translation
from PIL import Image
from unfold.contrib.forms.widgets import WysiwygWidget

from apps.blog.models import Category, Post, Tag
from apps.core.admin_mixins import translated_fields_for
from apps.core.content_admin import ContentAdmin
from apps.core.models import Publishable, TeamMember, Video
from apps.core.uploads import validate_image_file, validate_media_file, validate_video_file
from apps.digital_marketing.models import Campaign, CreativeWork
from apps.mobile_development.models import MobileApp
from apps.portfolio.models import CaseStudy
from apps.products.models import Product
from apps.services.models import Service
from tests.test_admin import AdminSmokeTestCase


def image_upload(name="example.png"):
    output = BytesIO()
    Image.new("RGB", (8, 8), color="white").save(output, format="PNG")
    return SimpleUploadedFile(name, output.getvalue(), content_type="image/png")


def inline_data(prefix, total=0):
    return {
        f"{prefix}-TOTAL_FORMS": str(total),
        f"{prefix}-INITIAL_FORMS": "0",
        f"{prefix}-MIN_NUM_FORMS": "0",
        f"{prefix}-MAX_NUM_FORMS": "1000",
    }


def editorial_data(slug):
    return {"slug": slug, "order": "1", "status": "draft", "translation_status": "none"}


class PhaseTwoAdminTests(AdminSmokeTestCase):
    def setUp(self):
        super().setUp()
        self.media = TemporaryDirectory()
        self.addCleanup(self.media.cleanup)
        override = override_settings(MEDIA_ROOT=self.media.name)
        override.enable()
        self.addCleanup(override.disable)

    def assert_saved(self, response):
        errors = None
        if response.status_code == 200 and response.context:
            errors = [response.context["adminform"].form.errors]
            errors.extend(
                inline.formset.errors for inline in response.context["inline_admin_formsets"]
            )
        self.assertEqual(response.status_code, 302, errors)

    def test_all_new_lists_and_add_forms_render(self):
        for model, model_admin in admin.site._registry.items():
            if not isinstance(model_admin, ContentAdmin) and model._meta.app_label != "crm":
                continue
            for action in ("changelist", "add"):
                with self.subTest(model=model._meta.label, action=action):
                    self.assertEqual(
                        self.client.get(
                            reverse(
                                f"admin:{model._meta.app_label}_{model._meta.model_name}_{action}"
                            )
                        ).status_code,
                        200,
                    )

    def test_translated_forms_and_inlines_have_six_tabs_and_rtl_widgets(self):
        for model, model_admin in admin.site._registry.items():
            if not isinstance(model_admin, ContentAdmin):
                continue
            instances = [
                model_admin,
                *(inline(model, admin.site) for inline in model_admin.inlines),
            ]
            for instance in instances:
                translated = translated_fields_for(instance.model)
                if not translated:
                    continue
                with self.subTest(model=instance.model._meta.label):
                    tabs = [
                        label
                        for label, opts in instance.get_fieldsets(None)
                        if "tab" in opts.get("classes", ())
                    ]
                    self.assertEqual(tabs, [label for _, label in settings.LANGUAGES])
                    for name in translated:
                        field = instance.formfield_for_dbfield(
                            instance.model._meta.get_field(f"{name}_ar"), None
                        )
                        self.assertEqual(field.widget.attrs.get("dir"), "rtl")
                        self.assertEqual(
                            isinstance(field.widget, WysiwygWidget),
                            name in getattr(instance.model, "rich_text_fields", ()),
                        )

    def test_product_saves_translated_features_gallery_and_rich_body(self):
        data = {
            **editorial_data("example-product"),
            **inline_data("features", 1),
            **inline_data("gallery", 1),
            "name_en": "Example product",
            "name_ar": "منتج",
            "summary_en": "Summary",
            "category": "database",
            "delivery": "customisable",
            "body_ar": '<p onclick="bad()">نص</p><script>bad()</script>',
            "features-0-title_en": "Example feature",
            "features-0-title_ar": "ميزة",
            "features-0-description_en": "Description",
            "features-0-order": "2",
            "features-0-translation_status": "reviewed",
            "gallery-0-image": image_upload(),
            "gallery-0-caption_ar": "صورة",
            "gallery-0-order": "1",
            "gallery-0-translation_status": "none",
        }
        self.assert_saved(self.client.post(reverse("admin:products_product_add"), data))
        product = Product.objects.get(slug="example-product")
        self.assertEqual(product.name_ar, "منتج")
        self.assertEqual(product.features.get().title_ar, "ميزة")
        self.assertEqual(product.gallery.get().caption_ar, "صورة")
        self.assertNotIn("script", product.body_ar)
        self.assertNotIn("onclick", product.body_ar)
        self.assertNotIn("example.png", product.gallery.get().image.name)
        response = self.client.get(reverse("admin:products_product_change", args=[product.pk]))
        self.assertContains(response, product.gallery.get().image.url)
        with translation.override("de"):
            self.assertEqual(product.name, "Example product")

    def test_each_proxy_locks_service_and_hides_other_service_records(self):
        proxies = [
            model
            for model in apps.get_models()
            if model._meta.proxy and issubclass(model, CaseStudy)
        ]
        self.assertEqual(len(proxies), 6)
        for proxy in proxies:
            with self.subTest(proxy=proxy.__name__):
                service = Service.objects.get(key=proxy.service_key)
                other = Service.objects.exclude(pk=service.pk).first()
                foreign = CaseStudy.objects.create(
                    service=other,
                    title_en="Foreign",
                    slug=f"foreign-{proxy.service_key}",
                    client_name="Example",
                )
                base = f"admin:{proxy._meta.app_label}_{proxy._meta.model_name}"
                self.assertNotEqual(
                    self.client.get(reverse(f"{base}_change", args=[foreign.pk])).status_code, 200
                )
                data = {
                    **editorial_data(f"own-{proxy.service_key}"),
                    **inline_data("metrics", 1),
                    **inline_data("gallery"),
                    "service": str(other.pk),
                    "title_en": "Example",
                    "title_ar": "مثال",
                    "client_name": "Example",
                    "challenge_en": "<p>Challenge</p>",
                    "solution_en": "<p>Solution</p>",
                    "outcome_en": "<p>Outcome</p>",
                    "metrics-0-label_en": "Example metric",
                    "metrics-0-label_ar": "مقياس",
                    "metrics-0-value": "0",
                    "metrics-0-order": "1",
                    "metrics-0-translation_status": "none",
                }
                self.assert_saved(self.client.post(reverse(f"{base}_add"), data))
                own = CaseStudy.objects.get(slug=data["slug"])
                self.assertEqual(own.service_id, service.pk)
                self.assertEqual(own.metrics.get().label_ar, "مقياس")
                self.assertEqual(
                    self.client.get(reverse(f"{base}_change", args=[own.pk])).status_code, 200
                )
                listing = self.client.get(reverse(f"{base}_changelist"))
                self.assertNotIn(
                    foreign.pk, list(listing.context["cl"].queryset.values_list("pk", flat=True))
                )

    def test_mobile_multichoice_and_screenshots_save(self):
        data = {
            **editorial_data("example-app"),
            **inline_data("screenshots", 1),
            "name": "Example app",
            "platforms": ["ios", "android"],
            "description_en": "Example",
            "features_ar": "ميزة أولى\nميزة ثانية",
            "rating": "4.25",
            "screenshots-0-image": image_upload(),
            "screenshots-0-caption_en": "Example screen",
            "screenshots-0-order": "1",
            "screenshots-0-translation_status": "none",
        }
        self.assert_saved(self.client.post(reverse("admin:mobile_development_mobileapp_add"), data))
        app = MobileApp.objects.get()
        self.assertEqual(app.platforms, ["ios", "android"])
        self.assertEqual(app.screenshots.count(), 1)
        form = admin.site._registry[MobileApp].formfield_for_dbfield(
            MobileApp._meta.get_field("platforms"), None
        )
        self.assertIsInstance(form, forms.MultipleChoiceField)
        with self.assertRaises(ValidationError):
            form.clean(["invalid"])

    def test_blog_post_saves_rich_text_tags_and_arabic(self):
        author = TeamMember.objects.create(name="Example author")
        category = Category.objects.create(name_en="Example category", slug="example-category")
        tag = Tag.objects.create(name_en="Example tag", slug="example-tag")
        data = {
            **editorial_data("example-post"),
            "title_en": "Example post",
            "title_ar": "مقال",
            "excerpt_en": "Excerpt",
            "body_en": '<p>Body</p><img src="x" onerror="bad()">',
            "body_ar": "<p>نص</p>",
            "author": str(author.pk),
            "category": str(category.pk),
            "tags": [str(tag.pk)],
            "reading_minutes": "3",
        }
        self.assert_saved(self.client.post(reverse("admin:blog_post_add"), data))
        post = Post.objects.get()
        self.assertEqual(post.title_ar, "مقال")
        self.assertNotIn("onerror", post.body_en)
        self.assertEqual(list(post.tags.all()), [tag])

    def test_video_host_errors_are_form_errors_not_server_errors(self):
        data = {
            **editorial_data("example-video"),
            "title_en": "Example",
            "orientation": "portrait",
            "source": "youtube",
            "external_url": "https://example.com/video",
        }
        response = self.client.post(reverse("admin:core_video_add"), data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("external_url", response.context["adminform"].form.errors)
        data["external_url"] = "https://www.youtube.com/watch?v=example"
        self.assert_saved(self.client.post(reverse("admin:core_video_add"), data))
        self.assertEqual(Video.objects.get().orientation, "portrait")

    def test_invalid_extension_is_rejected_on_image_form(self):
        data = {
            **editorial_data("bad-image"),
            **inline_data("features"),
            **inline_data("gallery"),
            "name_en": "Example",
            "summary_en": "Summary",
            "category": "database",
            "delivery": "customisable",
            "cover_image": image_upload("example.bmp"),
        }
        response = self.client.post(reverse("admin:products_product_add"), data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("cover_image", response.context["adminform"].form.errors)


class PhaseTwoModelTests(TestCase):
    def test_all_publishable_managers_apply_the_review_gate(self):
        for model in apps.get_models():
            if not issubclass(model, Publishable) or model._meta.proxy:
                continue
            # Inspect evaluated query results: seeded services are drafts; no model exposes them.
            with self.subTest(model=model._meta.label):
                self.assertFalse(model.objects.published().exists())
        item = Product.objects.create(
            name_en="Example",
            slug="example",
            category="database",
            summary_en="Summary",
            delivery="customisable",
            status="published",
            translation_status="machine",
        )
        self.assertFalse(Product.objects.published().exists())
        item.translation_status = "reviewed"
        item.save()
        self.assertEqual(list(Product.objects.published()), [item])
        self.assertIsNotNone(item.published_at)

    def test_all_new_long_form_fields_sanitise_every_locale(self):
        author = TeamMember.objects.create(name="Example")
        category = Category.objects.create(name_en="Example", slug="example")
        records = [
            Product(name_en="Example", slug="example"),
            CaseStudy(service=Service.objects.first(), title_en="Example", slug="example"),
            Post(title_en="Example", slug="example", author=author, category=category),
        ]
        for item in records:
            for name in item.rich_text_fields:
                for locale, _ in settings.LANGUAGES:
                    setattr(
                        item,
                        f"{name}_{locale}",
                        '<p onclick="bad()">Text</p><script>bad()</script>',
                    )
            item.save()
            item.refresh_from_db()
            for name in item.rich_text_fields:
                for locale, _ in settings.LANGUAGES:
                    text = getattr(item, f"{name}_{locale}")
                    self.assertNotIn("script", text)
                    self.assertNotIn("onclick", text)
                    self.assertIn("<p>", text)

    def test_video_validates_source_owner_and_host(self):
        video = Video(
            title_en="Example",
            slug="example",
            orientation="portrait",
            source="youtube",
            external_url="https://youtu.be/example",
        )
        video.full_clean()
        for url in (
            "http://youtu.be/example",
            "https://youtube.com.example.com/test",
            "https://vimeo.com/1",
        ):
            video.external_url = url
            with self.subTest(url=url), self.assertRaises(ValidationError):
                video.full_clean()
        video.external_url = "https://youtu.be/example"
        video.service = Service.objects.first()
        video.product = Product.objects.create(name_en="Example", slug="example")
        with self.assertRaises(ValidationError):
            video.clean()
        with transaction.atomic(), self.assertRaises(IntegrityError):
            video.save()
        video.service = None
        video.source = "file"
        with self.assertRaises(ValidationError):
            video.clean()

    def test_dates_ratings_and_creative_publication_validate(self):
        with self.assertRaises(ValidationError):
            Campaign(start_date=date(2026, 10, 2), end_date=date(2026, 10, 1)).clean()
        for field, value in [
            (MobileApp._meta.get_field("rating"), 6),
            (Campaign._meta.get_field("engagement_rate"), 101),
        ]:
            with self.assertRaises(ValidationError):
                field.clean(value, None)
        with self.assertRaises(ValidationError):
            CreativeWork(status="published").clean()
        CreativeWork(status="draft").clean()

    def test_upload_bytes_and_extension_must_agree(self):
        validate_image_file(image_upload())
        for name, payload in [
            ("fake.png", b"not an image"),
            ("fake.mp4", b"<script>bad()</script>"),
            ("fake.webm", b"not a video"),
            ("fake.svg", b"<svg></svg>"),
        ]:
            with self.subTest(name=name), self.assertRaises(ValidationError):
                validate_media_file(SimpleUploadedFile(name, payload))
        with self.assertRaises(ValidationError):
            validate_image_file(image_upload("wrong.jpg"))
        with self.assertRaises(ValidationError):
            validate_video_file(image_upload())
