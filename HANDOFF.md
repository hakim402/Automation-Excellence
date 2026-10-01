# Current checkpoint — October 1, 2026

Phase 1 corrections and the updated Blueprint scaffold are implemented. **Wait for
the user's review and explicit instruction before Phase 2.** The historical notes
below describe the earlier implementation and are superseded by
[docs/PHASE_1_CHECKPOINT.md](docs/PHASE_1_CHECKPOINT.md), particularly publication
rules, inline language editing, editor widgets, sidebar groups and theming.

---

# Handoff — Automex build

**For the agent taking over.** Phases 0 and 1 are built, committed and green.
Phases 2–7 remain. This file is the orientation; `CLAUDE.md` is the law and
`BUILD_PROMPT.md` is the spec and phase order. Read both in full before your
first edit — this file does not replace them, it tells you what already
happened and what will bite you.

---

## 1. Your opening instruction

> You are the lead engineer continuing the Automex build in this repository.
> `CLAUDE.md` holds the standing rules and `BUILD_PROMPT.md` holds the system
> design and phase order; read both fully first, then read `HANDOFF.md` for
> the current state and the known landmines.
>
> Phases 0 and 1 are complete and committed. **Begin Phase 2 only.** Stop at
> the checkpoint, report what you built, what you assumed, and what you need.
> Do not run ahead into Phase 3.
>
> Hard rules, from experience on this repo: never invent a business fact
> (client names, metrics, certifications, founded year, team size, taglines);
> leave unsupplied values empty and ask. Every model with a translatable
> field must inherit `TranslationTracked`. Every rich-text field must be
> sanitised on save. `objects.published()` is the only gate the public API
> may use. Check every layout at `/ar` before calling it done.

---

## 2. Current state

Two commits, nothing pushed, no remote configured.

| | |
|---|---|
| `fd270bd` | Phase 0 — scaffold |
| `a918615` | Phase 1 — core + services, modeltranslation, Unfold language tabs |

**Gates, all passing as of `a918615`:**

```
cd backend  && ruff check . && ruff format --check . && python manage.py test     # 73 tests
cd backend  && DJANGO_SETTINGS_MODULE=config.settings.prod \
               SECRET_KEY=<any-50-chars> ALLOWED_HOSTS=automex.tech \
               python manage.py check --deploy                                   # clean
cd frontend && npm run typecheck && npm run lint && npm audit && npm run build   # 0 vulns
```

Keep all of these green. `npm run build` takes ~100s because `next/font`
fetches font files; that is normal, not a hang.

### Versions actually installed

Backend: Django 5.2.17 · DRF 3.18.1 · django-unfold 0.108.0 ·
django-modeltranslation 0.20.6 · psycopg 3.3.6 · nh3 0.3.7 · Pillow 12.3.0 ·
ruff 0.16.9.
Frontend: Next 15.5.26 · next-intl 4.14.7 · React 19.3.0 · Tailwind 4.3.3.

### Local setup

```bash
cd backend && python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # set SECRET_KEY, DATABASE_URL
createdb automex                # role `automex`, password `automex` in dev
python manage.py migrate        # also seeds company facts + the six services
python manage.py createsuperuser
```

Use your existing local admin account; credentials are not stored in this repository.
Database is PostgreSQL only — there is no SQLite fallback.

---

## 3. What exists

### Backend

`backend/apps/core/`

| file | contents |
|---|---|
| `models.py` | abstracts + `SiteSettings`, `Tool`, `Industry`, `Testimonial`, `TeamMember`, `Stat` |
| `sanitize.py` | `clean_html(value, profile=)`, profiles `default` and `faq`, plus `tag_signature()` |
| `uploads.py` | `UploadTo(prefix, allowed)`, `validate_upload_size` |
| `admin_mixins.py` | `LanguageTabsMixin`, `TranslationStatusMixin`, `PublishStatusMixin`, `image_preview`, `render_image`, `translated_fields_for` |
| `admin.py`, `translation.py` | admin classes and modeltranslation registration |

Abstracts, all in `apps/core/models.py`:

| abstract | gives |
|---|---|
| `TimeStamped` | `created_at`, `updated_at` |
| `TranslationTracked` | `translation_status` (`none` / `machine` / `reviewed`) |
| `Publishable` | `status`, `published_at`, `objects.published()`, `.drafts()`, `.awaiting_translation_review()` |
| `SEOFields` | `meta_title*`, `meta_description*`, `og_image`, `noindex` |
| `Ordered` | `order`, `ordering = ["order", "pk"]` |
| `RichTextSanitised` | cleans `rich_text_fields` on save, per `rich_text_profiles` |

`backend/apps/services/` — `ServiceKey` (the six slugs as a closed choice
set), `Service`, `ServiceOffering`, `ProcessStep`, `FAQ`. The last three are
inlines on the service form **and** have flat changelists.

`config/admin_navigation.py` — the Unfold sidebar. Currently `Site`,
`Services`, `System`.

**Data migrations** (both idempotent, both fill blanks only so they never
clobber an admin's edits):
`core.0003_site_settings_company_facts`, `services.0002_the_six_services`.

**`/api/v1/` is still a stub** returning `{"version": "v1", "endpoints": []}`.
No serializers or viewsets exist yet — that is Phase 4.

### Frontend

Phase 0 scaffold only, no real pages. `src/app/[locale]/page.tsx` is a
placeholder that proves locale routing, `dir`, tokens and fonts; delete it in
Phase 6. `src/lib/api.ts` has the shared transport (`apiGet`,
`apiGetOptional`) with ISR `revalidate` and cache `tags` wired, but no
endpoint wrappers. `src/styles/tokens.css` is the single source of truth for
colour, type and spacing.

---

## 4. Landmines — read this section twice

These all cost real time to find. None are obvious from the code.

### Backend

1. **`TranslationTracked` is mandatory for any model with a translatable
   field.** Registering a field in `translation.py` and forgetting the
   abstract passes `manage.py check` and then 500s on the change form with
   `Unknown field(s) (translation_status)`. This bit me on three models.

2. **`prepopulated_fields` and `search_fields` must name `_en` columns.**
   modeltranslation replaces `name` with six real columns, so
   `{"slug": ("name",)}` raises `KeyError: Key 'name' not found` at render
   time, not at check time. Untranslated models (`Tool`) keep the bare name.

3. **Django has no language metadata for a bare `zh`.** Only `zh-hans` and
   `zh-hant`. `config/settings/base.py` registers `zh` in `LANG_INFO`
   explicitly; remove that line and every admin page that renders language
   info raises `KeyError`. The locale is `zh` everywhere — URL, `?lang=`, and
   modeltranslation's `_zh` columns — deliberately, so it is one spelling
   across all three layers.

4. **There is no `unfold.contrib.modeltranslation`.** Do not reach for
   modeltranslation's `TabbedTranslationAdmin` — it uses jQuery UI tabs that
   look foreign inside Unfold's Tailwind theme. Use the existing
   `LanguageTabsMixin`, which builds Unfold's native fieldset tabs (a
   fieldset with `"tab"` in `classes`).

5. **Unfold renders tab fieldsets after every untabbed one**, always. Each
   open `shared_fieldsets` entry pushes the language tabs further down. Give
   set-once fieldsets `"classes": ("collapse",)`.

6. **`translator.get_options_for_model(M).fields` is a tuple of names**, not
   a dict, and its order is arbitrary. `translated_fields_for()` reapplies
   the model's declaration order; `translated_field_order` on an admin
   overrides it, and any field omitted is appended rather than dropped.

7. **Unfold's `contrib` apps require their underlying packages.** Listing
   `unfold.contrib.import_export` without `django-import-export` installed
   passes `check` and fails later. Only `filters`, `forms` and `inlines` are
   enabled.

8. **nh3 refuses `rel` in the `a` allowlist when `link_rel` is set.** It owns
   `rel` and forces `noopener noreferrer`, which is stricter than honouring
   an author-supplied value. Do not add `rel` back.

9. **Inlines must extend `unfold.admin.StackedInline` / `TabularInline`**, not
   Django's, or they lose the theme silently.

10. **Never rename an applied migration.** I did, and the recorded name no
    longer matched, which needed a database rebuild. Nothing is deployed yet,
    so a rebuild is cheap now and will not be later.

### Frontend

11. **ESLint fails the build on physical direction utilities** — `ml-`, `mr-`,
    `pl-`, `pr-`, `left-`, `right-`, `text-left`, `text-right`, `border-l`,
    `border-r`, `rounded-l/r` — and on hard-coded hex in `className` or
    `style`. This is deliberate (CLAUDE.md §7 and §8) and the guards are
    tested. Use logical properties: `ms`/`me`, `ps`/`pe`, `start`/`end`,
    `text-start`/`text-end`, `border-s`/`border-e`. If a rule genuinely
    misfires, narrow it in `eslint.config.mjs` — do not disable it.

12. **There is no `src/app/layout.tsx`.** `<html>` lives in
    `src/app/[locale]/layout.tsx` because `lang` and `dir` are per-locale.
    Adding a root layout breaks the build.

13. **`postcss` is pinned to `^8.5.28` through `overrides`.** Next 15 bundles
    `<=8.5.22`, which carries four advisories. Removing the override puts a
    high finding back into `npm audit` on a security vendor's own site.

14. **The Arabic and Chinese fonts set `preload: false`** in
    `src/styles/fonts.ts`. All six locales share one `/[locale]` route, so
    preloading them made every visitor download both. Do not remove it.

15. **`Noto_Sans_SC` has no `chinese-simplified` subset in `next/font`** —
    only `latin` / `latin-ext` / `vietnamese` / `cyrillic`. The Han unicode
    ranges ship either way, so Chinese renders correctly, but ~200
    `@font-face` rules (**~64 KB gzipped of CSS**) go to all six locales.
    This is a known, measured Phase 7 item; the fix is self-hosting a subset
    or a locale-conditional stylesheet, and it cannot be done inside
    `next/font`.

---

## 5. Phase 2 — your next task

From `BUILD_PROMPT.md`: the remaining apps and models, admin classes,
inlines, per-service case-study proxies, dashboard widgets, the lead model
with email alerting, the `products` app, the shared `Video` model, and HTML
sanitisation on every rich-text field.

Apps to create: `products`, `portfolio`, `digital_marketing`,
`ai_automation`, `custom_software`, `web_development`, `mobile_development`,
`cyber_security`, `blog`, `crm`. Field lists are in `BUILD_PROMPT.md`; follow
them exactly and reuse the `apps.core` abstracts rather than redeclaring
fields.

Specific things already decided or deliberately deferred:

- **`Video` lives in `core`** with three nullable FKs (`service`, `product`,
  `case_study`). It was deferred from Phase 1 only because `Product` and
  `CaseStudy` did not exist. **Add a `CheckConstraint` allowing at most one
  non-null owner**, plus a `clean()` so the admin shows a readable error —
  the spec as written permits a video attached to all three or to nothing,
  and the frontend has no defined behaviour for either. This was raised with
  the user and is **not yet confirmed**; implement it and flag it.
- **Rich text is allowed on exactly these fields** and nowhere else without
  asking: `Service.body`, `Product.body`, `CaseStudy.challenge/.solution/
  .outcome`, `Post.body`, `FAQ.answer`. Use `RichTextSanitised` with
  `rich_text_fields`; `FAQ.answer` already uses the narrower `faq` profile.
- **Per-service sidebar groups.** The six groups from `BUILD_PROMPT.md` were
  held back until there were models to fill them. Add them now, with proxy
  models for the per-service case-study views, and extend
  `config/admin_navigation.py`.
- **`MobileApp.features` is specified as translatable with no stated type.**
  A plain `TextField` rendered one item per line keeps it off the rich-text
  allowlist. Confirm with the user.
- **Dashboard "awaiting translation review"** spans ~15 unrelated tables with
  no common DB ancestor. Prefer a small registry of publishable models over
  hard-coding the list in the dashboard callable.
- **`Lead` must never be exposed through a GET endpoint**, and full lead
  payloads must never be logged. `internal_notes` never leaves the admin.
- **Seed `Certification` and `ComplianceStandard` as empty, not placeholder.**
  A fake "ISO 27001" badge in a security vendor's database is the kind of
  thing that gets screenshotted out of context. The user has not said what
  Automex actually holds.

Later phases, for context: 3 Groq translation pipeline (`tag_signature()` in
`sanitize.py` exists for verifying a translation did not mangle the markup);
4 API + `seed_demo` + Turnstile; 5 frontend shell; 6 pages + ISR webhook;
7 SEO, Lighthouse, accessibility.

---

## 6. Open questions — ask, do not guess

Still unanswered after two checkpoints. None block Phase 2; all block launch.

1. **Founded year and team size** — `SiteSettings` fields exist and are empty.
2. **Social profile URLs** — six fields exist, all empty. Only filled ones
   should render.
3. **Is the Afghanistan phone public or internal?** `show_phone_af_publicly`
   defaults to `False`, and `SiteSettings.public_phone_af` returns `""` until
   it is switched on. A test locks that default in.
4. **Certifications and compliance standards Automex actually holds.**
5. **Logo files** — a placeholder wordmark was never designed. `favicon.ico`
   was removed rather than shipping Next.js's default.
6. **Real case study content** — clients, metrics, screenshots.
7. **Products in the top nav** — recommended left out; ten items is the
   findability problem the redesign exists to fix. Unconfirmed.
8. **Next 15 vs 16.** `create-next-app` now ships 16; the spec says 15, so 15
   is pinned and `postcss` is overridden by hand. Worth revisiting.
9. **Video hosting** — YouTube is the assumed default.

### One thing that needs flagging explicitly

`frontend/messages/*.json` contains a `common.tagline` of **"Systems that run
on their own"**, translated into all six locales. **I wrote that line. It is
invented marketing copy**, added because the Phase 0 placeholder needed
something to render. It is not a supplied business fact. Either get it
approved, replace it, or drive it from `SiteSettings.tagline` (which is
deliberately empty). Do not let it reach production unexamined.

---

## 7. Conventions that are easy to get wrong

- Apps are registered as `apps.<name>`; `AppConfig.label` is the short name.
- Field names are business language: `client_name`, never `cust_nm`.
- `__str__` returns something a non-technical admin recognises.
- Slugs stay English in every locale. Never translate slugs, enum keys, tech
  stack names, client names, URLs or numbers.
- Adding a translatable field means a migration — it creates six columns.
- Migrations are committed with the model change that caused them.
- Admin UI is English only. There is no `LocaleMiddleware`, deliberately.
- Every list view needs `list_display`, `list_filter`, `search_fields` and a
  translation badge. A screen a non-developer cannot operate is not done.
- A new environment variable goes into `.env.example` in the same commit, on
  whichever side owns it.
- Do not add a dependency without saying why in the commit message.
- Screenshots for each checkpoint go in `docs/screenshots/`, indexed in the
  README there. A headless capture harness pattern is described in the Phase
  1 report; Chrome is at
  `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`.
- Never leave a dev server running after a check.
