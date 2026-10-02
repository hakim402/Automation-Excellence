from django.db import transaction
from rest_framework import status
from rest_framework.parsers import FormParser, JSONParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Lead, NewsletterSubscriber
from .serializers import LeadSerializer, NewsletterSerializer
from .throttling import LeadThrottle, NewsletterThrottle, client_ip
from .turnstile import verify_turnstile


class CaptureView(APIView):
    authentication_classes = []
    parser_classes = [JSONParser, FormParser]
    http_method_names = ["post", "options"]

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        response["Cache-Control"] = "no-store"
        return response

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        values = dict(serializer.validated_data)
        trap = values.pop("website", "")
        token = values.pop("turnstile_token")
        if not trap:
            ip = client_ip(request)
            verify_turnstile(token, ip, action=self.turnstile_action)
            with transaction.atomic():
                self.capture(values, request, ip)
        # Honeypots look accepted but never persist or trigger mail/provider calls.
        return Response(
            {"detail": "Thank you. Your request has been received."}, status=self.success_status
        )


class LeadCaptureView(CaptureView):
    serializer_class = LeadSerializer
    throttle_classes = [LeadThrottle]
    turnstile_action = "lead"
    success_status = status.HTTP_201_CREATED

    def capture(self, values, request, ip):
        product = values.pop("product", None)
        if product:
            # The canonical slug is safe, stable context; never trust a browser-supplied name.
            values["message"] = f"[Product: {product.slug}]\n\n" + values["message"]
        Lead.objects.create(
            **values, ip_address=ip, user_agent=request.META.get("HTTP_USER_AGENT", "")[:500]
        )


class NewsletterCaptureView(CaptureView):
    serializer_class = NewsletterSerializer
    throttle_classes = [NewsletterThrottle]
    turnstile_action = "newsletter"
    success_status = status.HTTP_202_ACCEPTED

    def capture(self, values, request, ip):
        NewsletterSubscriber.objects.get_or_create(
            email__iexact=values["email"].strip().lower(),
            defaults={
                "email": values["email"].strip().lower(),
                "locale": values.get("locale", "en"),
                "is_confirmed": False,
            },
        )
