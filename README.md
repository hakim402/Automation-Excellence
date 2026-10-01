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

python manage.py migrate       # also seeds company facts and the six services
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
  tests/               scaffold, content, admin, CRM and dashboard regressions
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

## Content model

Shared abstracts live in `apps/core/models.py` and everything inherits them:

| abstract | gives you |
|---|---|
| `TimeStamped` | `created_at`, `updated_at` |
| `TranslationTracked` | `translation_status` — **any model with a translatable field needs this** |
| `Publishable` | `status`, `published_at`, plus `objects.published()` |
| `SEOFields` | `meta_title`, `meta_description`, `og_image`, `noindex` |
| `Ordered` | `order`, with `ordering = ["order", "pk"]` |
| `RichTextSanitised` | sanitises the fields in `rich_text_fields` on every save |

`Service` uses the shared draft/published lifecycle plus `is_active`. Public queries
exclude machine-translated records until reviewed. Newly migrated services remain drafts.

Rich text is allowed on `Service.body`, `Product.body`, `CaseStudy.challenge`,
`CaseStudy.solution`, `CaseStudy.outcome`, `Post.body` and `FAQ.answer`. Every locale
is sanitised on model save by `apps/core/sanitize.py`. FAQ answers use a narrower
profile: links and lists, no headings.

Two data migrations seed real facts, not demo content, and both fill blanks
only so they never overwrite an admin's edits:

- `core.0003` — company name, address, phones, email, domain
- `services.0002` — the six service lines

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
- **A model with a translatable field must inherit `TranslationTracked`.** Otherwise the Groq
  pipeline has nowhere to record its work and the admin badge has nothing to read. Registering a
  field in `translation.py` and forgetting the abstract is a 500 on the change form, not a
  check-time error.
- **`prepopulated_fields` and `search_fields` must name the `_en` column**, not the bare field.
  modeltranslation replaces `name` with six real columns, so `{"slug": ("name",)}` raises
  `KeyError` at render time.
- **Unfold renders tab fieldsets after every untabbed one**, so each open `shared_fieldsets` entry
  pushes the language tabs further down. Collapse the set-once ones.
- **Adding a translatable field means a migration** — it creates six columns, one per locale.

## Phase 3 review checkpoint

Phase 3 adds Groq translations from saved English into five languages, missing-field-only admin
actions, bounded retries, strict HTML validation and an audit log. Generated text stays in draft
until reviewed. See [the checkpoint](docs/PHASE_3_CHECKPOINT.md) for setup and manual review,
and [live translation samples](docs/PHASE_3_TRANSLATION_SAMPLES.md) for all five languages.
Phase 4 awaits your explicit approval.

The public frontend remains the localized Blueprint scaffold. Content APIs arrive in Phase 4,
and the public shell and pages in Phases 5–6. Live SMTP delivery still needs configured credentials
and recipient verification; automated email behavior is covered by tests.

Earlier theme/admin work is recorded in [docs/PHASE_1_CHECKPOINT.md](docs/PHASE_1_CHECKPOINT.md).
