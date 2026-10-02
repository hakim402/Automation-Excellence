"""Disposable Phase 6 browser fixture. Never writes to the development database."""

import os
import signal
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
os.environ["REVALIDATE_WEBHOOK_URL"] = ""
os.environ["LEAD_ALERT_RECIPIENTS"] = ""


def main():
    import django

    django.setup()
    from socketserver import ThreadingMixIn
    from wsgiref.simple_server import WSGIServer, make_server

    class PreviewServer(ThreadingMixIn, WSGIServer):
        daemon_threads = True
        request_queue_size = 128

        def process_request_thread(self, request, client_address):
            from django.db import connections

            try:
                super().process_request_thread(request, client_address)
            finally:
                connections.close_all()

    from django.conf import settings
    from django.core.wsgi import get_wsgi_application
    from django.db import connection

    media = tempfile.TemporaryDirectory(prefix="automex-preview-media-")
    settings.MEDIA_ROOT = media.name
    settings.CORS_ALLOWED_ORIGINS = ["http://localhost:3001"]
    settings.LEAD_ALERT_RECIPIENTS = []
    settings.DATABASES["default"]["TEST"]["NAME"] = f"test_phase6_preview_{os.getpid()}"
    connection.settings_dict["CONN_MAX_AGE"] = 0
    original = connection.settings_dict["NAME"]
    connection.creation.create_test_db(verbosity=0, autoclobber=False)
    try:
        from io import BytesIO

        from django.core.files.base import ContentFile
        from PIL import Image, ImageDraw

        from apps.ai_automation.models import AgentType
        from apps.blog.models import Category, Post
        from apps.core.models import Industry, SiteSettings, TeamMember, Tool, Video
        from apps.portfolio.models import CaseStudy, CaseStudyMetric
        from apps.products.models import Product, ProductFeature
        from apps.services.models import FAQ, ProcessStep, Service, ServiceOffering

        canvas = Image.new("RGB", (1200, 675), "#0B2545")
        draw = ImageDraw.Draw(canvas)
        for x in range(80, 1120, 180):
            draw.rectangle((x, 220, x + 120, 420), outline="#EAF4FB", width=4)
        draw.text((80, 80), "TEST MEDIA - DISPOSABLE PREVIEW", fill="#EAF4FB")
        output = BytesIO()
        canvas.save(output, "PNG")
        fixture_image = output.getvalue()

        site = SiteSettings.load()
        site.tagline_en = "TEST PREVIEW — Systems for connected work"
        site.tagline_ar = "معاينة اختبار — أنظمة للعمل المترابط"
        site.about_short_en = "TEST ONLY — Page templates with disposable content."
        site.about_short_ar = (
            "محتوى اختبار مؤقت لعرض القوالب. هذه البيانات ليست معلومات حقيقية عن الشركة."
        )
        site.response_time_en = "TEST ONLY — Response-time field preview."
        site.save()
        tool = Tool.objects.create(name="Python", slug="python", category="backend")
        industry = Industry.objects.create(
            name_en="TEST industry",
            name_ar="قطاع تجريبي",
            slug="test-industry",
            description_en="An isolated test fixture.",
        )
        for service in Service.objects.all():
            service.status = "published"
            service.intro_en = "TEST PREVIEW — Service content from the public API."
            service.intro_ar = "معاينة اختبار — مقدمة واضحة للخدمة من واجهة المحتوى العامة."
            service.hero_headline_en = f"TEST PREVIEW — {service.name_en}"
            service.body_en = "<p>Test service overview.</p>"
            service.hero_image.save("test-service.png", ContentFile(fixture_image), save=False)
            service.save()
            service.tools.add(tool)
            service.industries.add(industry)
            for i in range(3):
                ServiceOffering.objects.create(
                    service=service,
                    title_en=["Discover requirements", "Design the workflow", "Connect your tools"][
                        i
                    ],
                    description_en="TEST ONLY — A concise explanation of this capability.",
                    order=i,
                )
                ProcessStep.objects.create(
                    service=service,
                    title_en=["Understand", "Build", "Review"][i],
                    description_en="TEST ONLY — This is a sample step, not a business promise.",
                    order=i,
                )
            FAQ.objects.create(
                service=service,
                question_en="Is this real company content?",
                answer_en="<p>No. This page uses an isolated test database.</p>",
            )
        service = Service.objects.get(key="ai-automation")
        AgentType.objects.create(
            name_en="TEST assistant",
            slug="test-assistant",
            status="published",
            description_en="A sample capability for template verification.",
        )
        product = Product.objects.create(
            name_en="TEST workflow toolkit",
            name_ar="أدوات سير عمل تجريبية",
            slug="test-toolkit",
            summary_en="A disposable product fixture for layout verification.",
            tagline_en="TEST ONLY — A connected workflow example.",
            category="automation",
            delivery="customisable",
            body_en="<p>Test product overview, rendered from sanitized HTML.</p>",
            status="published",
            is_featured=True,
        )
        product.cover_image.save("test-product.png", ContentFile(fixture_image))
        product.services.add(service)
        product.tech_stack.add(tool)
        ProductFeature.objects.create(
            product=product,
            title_en="TEST feature",
            description_en="A product feature supplied by the API.",
        )
        for i in range(13):
            Product.objects.create(
                name_en=f"TEST catalog item {i}",
                slug=f"test-catalog-{i}",
                summary_en="Pagination fixture.",
                category="database",
                delivery="ready-to-deploy",
                status="published",
            )
        case = CaseStudy.objects.create(
            title_en="TEST — Connected operations",
            slug="test-case",
            client_name="TEST ONLY",
            service=service,
            status="published",
            is_featured=True,
            challenge_en="<p>Test challenge.</p>",
            solution_en="<p>Test solution.</p>",
            outcome_en="<p>Test outcome. No business metrics are asserted.</p>",
        )
        CaseStudyMetric.objects.create(
            case_study=case, label_en="TEST metric", value="1", unit=" fixture"
        )
        author = TeamMember.objects.create(
            name="TEST author", role_en="Fixture", bio_en="Not a real team member."
        )
        category = Category.objects.create(name_en="TEST journal", slug="test-journal")
        Post.objects.create(
            title_en="TEST — Designing a connected workflow",
            slug="test-post",
            excerpt_en="An isolated article fixture.",
            body_en="<h2>Test section</h2><p>Server-rendered article body.</p>",
            author=author,
            category=category,
            service=service,
            status="published",
        )
        Video.objects.create(
            title_en="TEST video",
            slug="test-video",
            description_en="Player verification fixture.",
            orientation="landscape",
            source="youtube",
            external_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            service=service,
            status="published",
        )
        Video.objects.create(
            title_en="TEST reel",
            slug="test-reel",
            description_en="Portrait player fixture.",
            orientation="portrait",
            source="youtube",
            external_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            service=service,
            status="published",
        )
        print("Disposable fixture ready at http://127.0.0.1:8002", flush=True)

        def stop(*_args):
            raise KeyboardInterrupt

        signal.signal(signal.SIGTERM, stop)
        with make_server(
            "127.0.0.1", 8002, get_wsgi_application(), server_class=PreviewServer
        ) as server:
            server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        connection.creation.destroy_test_db(old_database_name=original, verbosity=0)
        media.cleanup()
        print("Disposable fixture database removed.", flush=True)


if __name__ == "__main__":
    main()
