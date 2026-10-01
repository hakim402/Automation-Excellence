"""
Base settings shared by every environment.

Environment-specific modules (dev.py, prod.py) import * from here and override.
Nothing secret lives in this file — see .env.example for the full key list.
"""

from pathlib import Path

import environ
from django.conf.locale import LANG_INFO

from config.admin_navigation import NAVIGATION

# backend/config/settings/base.py -> backend/
BASE_DIR = Path(__file__).resolve().parents[2]

env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, []),
    CORS_ALLOWED_ORIGINS=(list, []),
)
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("SECRET_KEY")
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env("ALLOWED_HOSTS")

# The public site's origin. Used for CORS and for building absolute URLs.
FRONTEND_ORIGIN = env("FRONTEND_ORIGIN", default="http://localhost:3000")
SITE_DOMAIN = env("SITE_DOMAIN", default="https://automex.tech")


# --------------------------------------------------------------------------
# Applications
#
# Unfold and its contrib apps MUST precede django.contrib.admin — they
# override the admin templates. See CLAUDE.md section 5.
# --------------------------------------------------------------------------

UNFOLD_APPS = [
    "unfold",
    "unfold.contrib.filters",
    "unfold.contrib.forms",
    "unfold.contrib.inlines",
]

# django-modeltranslation must precede django.contrib.admin so its model
# registry is populated before the admin autodiscovers.
TRANSLATION_APPS = ["modeltranslation"]

DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "corsheaders",
]

# Local apps. Registered as "apps.<name>" per CLAUDE.md section 5.
LOCAL_APPS = [
    "apps.core",
    "apps.services",
]

INSTALLED_APPS = UNFOLD_APPS + TRANSLATION_APPS + DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS


MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
# Note: django.middleware.locale.LocaleMiddleware is deliberately absent.
# The admin is English only (CLAUDE.md section 5); public locales are the
# frontend's concern and reach the API via ?lang=.

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"


# --------------------------------------------------------------------------
# Database
# --------------------------------------------------------------------------

DATABASES = {"default": env.db("DATABASE_URL")}
DATABASES["default"]["ATOMIC_REQUESTS"] = False
DATABASES["default"]["CONN_MAX_AGE"] = env.int("DB_CONN_MAX_AGE", default=60)

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# --------------------------------------------------------------------------
# Authentication
# --------------------------------------------------------------------------

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# --------------------------------------------------------------------------
# Internationalisation
#
# These six locales define the public site. For django-modeltranslation each
# entry below becomes one database column per translatable field, so the list
# is not free to grow. The admin itself stays English.
# --------------------------------------------------------------------------

LANGUAGE_CODE = "en"

# Django ships language metadata for "zh-hans" and "zh-hant" but not for a
# bare "zh", and any admin template that renders language info raises
# KeyError on an unknown code. The public locale is "zh" everywhere -- the
# URL /zh/, the API's ?lang=zh, and modeltranslation's _zh columns -- so we
# register the code rather than fragment it into zh_hans across three layers.
LANG_INFO.setdefault(
    "zh",
    {"bidi": False, "code": "zh", "name": "Simplified Chinese", "name_local": "简体中文"},
)

LANGUAGES = [
    ("en", "English"),
    ("es", "Spanish"),
    ("fr", "French"),
    ("de", "German"),
    ("zh", "Chinese (Simplified)"),
    ("ar", "Arabic"),
]

# Locales that render right-to-left. Mirrored in the frontend's i18n config.
RTL_LANGUAGES = ["ar"]

# English is the source of truth; every other locale falls back to it.
MODELTRANSLATION_DEFAULT_LANGUAGE = "en"
MODELTRANSLATION_FALLBACK_LANGUAGES = ("en",)

TIME_ZONE = env("TIME_ZONE", default="America/Los_Angeles")
USE_I18N = True
USE_TZ = True

LOCALE_PATHS = [BASE_DIR / "locale"]


# --------------------------------------------------------------------------
# Static and media
#
# Media is local disk for now. Swapping to S3 is a STORAGES change and
# nothing else — never reference MEDIA_ROOT outside this file.
# --------------------------------------------------------------------------

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}

# Upload limits. Enforced again per-field by validators in Phase 2.
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024
MAX_UPLOAD_SIZE_BYTES = env.int("MAX_UPLOAD_SIZE_BYTES", default=10 * 1024 * 1024)


# --------------------------------------------------------------------------
# Django REST Framework
#
# Public read endpoints are unauthenticated and cacheable. Write endpoints
# exist only in crm and add their own throttles on top of these defaults.
# --------------------------------------------------------------------------

REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.AllowAny"],
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 12,
    "DEFAULT_THROTTLE_RATES": {
        "leads": env("THROTTLE_LEADS", default="5/hour"),
        "newsletter": env("THROTTLE_NEWSLETTER", default="5/hour"),
    },
    "UNAUTHENTICATED_USER": None,
}

if DEBUG:
    REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] = [
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ]


# --------------------------------------------------------------------------
# CORS
#
# Explicit origin list only. CORS_ALLOW_ALL_ORIGINS is never set.
# --------------------------------------------------------------------------

CORS_ALLOWED_ORIGINS = env("CORS_ALLOWED_ORIGINS") or [FRONTEND_ORIGIN]
CORS_ALLOW_CREDENTIALS = False
# Only the API needs to be cross-origin readable.
CORS_URLS_REGEX = r"^/api/.*$"

CSRF_TRUSTED_ORIGINS = [FRONTEND_ORIGIN]


# --------------------------------------------------------------------------
# Email — SMTP via env. Used for lead alerts from Phase 2.
# --------------------------------------------------------------------------

EMAIL_HOST = env("EMAIL_HOST", default="")
EMAIL_PORT = env.int("EMAIL_PORT", default=587)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="Automex <info@automex.tech>")
LEAD_ALERT_RECIPIENTS = env.list("LEAD_ALERT_RECIPIENTS", default=[])


# --------------------------------------------------------------------------
# Third-party integrations. Consumed in later phases; declared here so the
# env surface is visible in one place.
# --------------------------------------------------------------------------

GROQ_API_KEY = env("GROQ_API_KEY", default="")
GROQ_MODEL = env("GROQ_MODEL", default="llama-3.3-70b-versatile")

TURNSTILE_SECRET_KEY = env("TURNSTILE_SECRET_KEY", default="")
TURNSTILE_VERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"

# Shared secret for the publish -> Next.js revalidation webhook.
REVALIDATE_WEBHOOK_SECRET = env("REVALIDATE_WEBHOOK_SECRET", default="")
REVALIDATE_WEBHOOK_URL = env("REVALIDATE_WEBHOOK_URL", default="")


# --------------------------------------------------------------------------
# Logging
#
# Lead payloads contain personal data and are never logged in full
# (CLAUDE.md section 10).
# --------------------------------------------------------------------------

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {"format": "{levelname} {asctime} {name} {message}", "style": "{"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "standard"},
    },
    "root": {"handlers": ["console"], "level": env("LOG_LEVEL", default="INFO")},
    "loggers": {
        "django.db.backends": {"level": "WARNING", "propagate": True},
    },
}


# --------------------------------------------------------------------------
# Unfold admin
#
# Palette is the Deep Harbor brand (CLAUDE.md section 8): the primary ramp is
# anchored on cyan #3FC9CE (400), harbor #0E4553 (900) and petrol #0A2830
# (950); the base ramp runs mist #F2F6F6 -> slate #8FA9AE -> petrol so the
# dark admin sits on the brand background. Amber is not in either ramp: it is
# reserved for status badges, so it stays rare.
#
# SIDEBAR navigation is grouped by service, which is what makes six services
# read as six sections over a deliberately shared model layer. Groups are
# added as their models land, phase by phase.
# --------------------------------------------------------------------------

UNFOLD = {
    "SITE_TITLE": "Automex Admin",
    "SITE_HEADER": "Automex",
    "SITE_SUBHEADER": "Content and leads",
    "SITE_URL": FRONTEND_ORIGIN,
    "SHOW_HISTORY": True,
    "SHOW_VIEW_ON_SITE": True,
    "SHOW_LANGUAGES": False,  # admin is English only
    "COLORS": {
        "primary": {
            "50": "236 251 251",
            "100": "211 245 245",
            "200": "171 235 236",
            "300": "116 220 222",
            "400": "63 201 206",
            "500": "36 170 177",
            "600": "27 136 143",
            "700": "26 108 116",
            "800": "26 88 95",
            "900": "14 69 83",
            "950": "10 40 48",
        },
        "base": {
            "50": "242 246 246",
            "100": "228 235 236",
            "200": "203 216 218",
            "300": "168 188 192",
            "400": "143 169 174",
            "500": "107 133 139",
            "600": "85 108 114",
            "700": "68 88 94",
            "800": "42 64 72",
            "900": "22 50 59",
            "950": "10 40 48",
        },
        "font": {
            "subtle-light": "107 133 139",
            "subtle-dark": "143 169 174",
            "default-light": "22 50 59",
            "default-dark": "234 242 242",
            "important-light": "10 40 48",
            "important-dark": "255 255 255",
        },
    },
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": False,
        "navigation": NAVIGATION,
    },
}
