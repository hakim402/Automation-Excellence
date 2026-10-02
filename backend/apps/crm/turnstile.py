"""Fail-closed server verification; only the token and optional IP leave this process."""

import json
from http.client import HTTPException
from urllib.error import URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener

from django.conf import settings
from rest_framework.exceptions import APIException, ValidationError


class VerificationUnavailable(APIException):
    status_code = 503
    default_detail = "Verification is temporarily unavailable. Please try again later."
    default_code = "verification_unavailable"


class NoRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def verify_turnstile(token, ip_address, *, action):
    if not settings.TURNSTILE_SECRET_KEY or not settings.TURNSTILE_ALLOWED_HOSTNAMES:
        raise VerificationUnavailable()
    payload = {"secret": settings.TURNSTILE_SECRET_KEY, "response": token}
    if ip_address:
        payload["remoteip"] = ip_address
    request = Request(
        "https://challenges.cloudflare.com/turnstile/v0/siteverify",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", "User-Agent": "Automex-Capture/1.0"},
        method="POST",
    )
    try:
        with build_opener(NoRedirects()).open(
            request, timeout=settings.TURNSTILE_TIMEOUT
        ) as response:
            raw = response.read(65537)
        if len(raw) > 65536:
            raise VerificationUnavailable()
        result = json.loads(raw)
        if not isinstance(result, dict):
            raise VerificationUnavailable()
    except (URLError, OSError, HTTPException, ValueError):
        # Never expose provider bodies, tokens or settings in errors/logs.
        raise VerificationUnavailable() from None
    if result.get("success") is not True:
        errors = result.get("error-codes") or []
        if not isinstance(errors, list) or not all(isinstance(code, str) for code in errors):
            raise VerificationUnavailable()
        if set(errors) & {
            "missing-input-secret",
            "invalid-input-secret",
            "internal-error",
        }:
            raise VerificationUnavailable()
        raise ValidationError(
            {"turnstile_token": "Verification failed or expired. Please try again."}
        )
    if (
        result.get("hostname") not in settings.TURNSTILE_ALLOWED_HOSTNAMES
        or result.get("action") != action
    ):
        raise ValidationError({"turnstile_token": "Verification failed. Please try again."})
