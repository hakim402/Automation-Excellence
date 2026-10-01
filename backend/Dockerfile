# Automex backend.
#
# Written for a future container deployment. The current workflow runs
# directly on a single VPS and does NOT use this file (BUILD_PROMPT.md:
# "no Docker for now"). Kept current so the switch is not a rewrite.

FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# libpq for psycopg. Build tools are not needed: psycopg[binary] ships wheels.
RUN apt-get update \
    && apt-get install --no-install-recommends -y libpq5 curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Never run as root.
RUN useradd --create-home --uid 10001 automex \
    && mkdir -p /app/media /app/staticfiles \
    && chown -R automex:automex /app
USER automex

ENV DJANGO_SETTINGS_MODULE=config.settings.prod

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=20s \
    CMD curl -fsS http://127.0.0.1:8000/healthz || exit 1

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
