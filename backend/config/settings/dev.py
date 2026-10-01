"""Development settings. Never used in production."""

from .base import *  # noqa: F403
from .base import BASE_DIR, env  # noqa: F401

DEBUG = True

ALLOWED_HOSTS = ["localhost", "127.0.0.1", "[::1]", "0.0.0.0"]

# Convenience for local work against a dev frontend on any port.
CORS_ALLOWED_ORIGIN_REGEXES = [r"^http://localhost:\d+$", r"^http://127\.0\.0\.1:\d+$"]

# Print emails instead of sending them unless an SMTP host is configured.
if not env("EMAIL_HOST", default=""):
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
