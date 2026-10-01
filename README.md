# Automex

Public website and content backend for Automex — a technology services company in Kent, WA,
selling six service lines worldwide in six languages.

Headless: Django owns content and leads, Next.js owns presentation, and the only contact
surface between them is the versioned REST API at `/api/v1/`.

Standing rules for working in this repo are in [CLAUDE.md](CLAUDE.md). The system design and
build order are in `BUILD_PROMPT.md`.

---

## Requirements

| | version |
|---|---|
| Python | 3.12 |
| Node | 22 |
| PostgreSQL | 14+ |

---

## First-time setup

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env          # then set SECRET_KEY and DATABASE_URL
createdb automex              # or: psql -d postgres -c "CREATE DATABASE automex OWNER automex;"

python manage.py migrate
python manage.py createsuperuser
python manage.py runserver 8000
```

Admin at <http://127.0.0.1:8000/admin/>, API at <http://127.0.0.1:8000/api/v1/>.

### Frontend

```bash
cd frontend
npm install
cp .env.example .env.local    # API_URL must point at the running backend
npm run dev
```

Site at <http://localhost:3000> — `/` redirects to `/en`.

---

## Day-to-day commands

Backend, from `backend/` with the venv active:

```bash
python manage.py runserver 8000
python manage.py makemigrations && python manage.py migrate
python manage.py test
ruff check . && ruff format .
```

Frontend, from `frontend/`:

```bash
npm run dev
npm run build        # must pass before any task is called done
npm run lint
npm run typecheck
```

---

## Layout

```
backend/
  config/settings/     base.py / dev.py / prod.py
  config/urls.py       admin + /api/v1/ only; never public HTML
  apps/                all Django apps, registered as apps.<name>
  tests/               scaffold contract tests
frontend/
  src/app/[locale]/    every route, six locales
  src/components/      sections/ and ui/
  src/i18n/            routing, request config, locale-aware navigation
  src/lib/             api.ts — the only place that talks to Django
  src/styles/          tokens.css is the single source of truth for design
  messages/            UI strings per locale (not page content)
docs/screenshots/      checkpoint evidence
```

---

## Things that will bite you

- **`npm run lint` fails on `ml-4`, `text-left`, `pr-6` and friends.** That is deliberate. Shared
  components must use logical properties (`ms`/`me`, `ps`/`pe`, `text-start`, `border-s`) or the
  Arabic layout breaks. Same rule rejects hard-coded hex colours — use a token.
- **Locale is `zh`, not `zh-hans`.** Django has no language metadata for a bare `zh`, so
  `config/settings/base.py` registers it. Removing that breaks any admin page that renders
  language info.
- **The frontend has no `src/app/layout.tsx`.** `<html>` lives in `src/app/[locale]/layout.tsx`
  because `lang` and `dir` are per-locale.
- **Unfold must stay ahead of `django.contrib.admin`** in `INSTALLED_APPS`, or the admin falls
  back to Django's own templates.
- **Docker files are reference only.** Deployment is a single VPS; nothing in the workflow uses
  `docker-compose.yml`.
