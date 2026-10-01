# Handoff — Phase 2 checkpoint, October 2, 2026

**Phase 2 is implemented. Wait for the user's review and explicit instruction before Phase 3.**
Read `CLAUDE.md` and `BUILD_PROMPT.md` before editing. The current acceptance report is
[docs/PHASE_2_CHECKPOINT.md](docs/PHASE_2_CHECKPOINT.md).

## Current state

- Phase 1 baseline: `5c84df2`, pushed to the configured GitHub remote.
- Phase 2 implementation: `882d55c`, committed locally. No Phase 3 work has started.
- 106 backend tests, Ruff checks, migration drift check, production Django checks, frontend build,
  lint and typecheck passed. New migrations are applied locally.
- Browser checks covered the dashboard in light/dark, dynamic Arabic product-feature inline
  editing, and the existing frontend in English/Arabic. Temporary test servers were stopped.
- No new dependencies, real client claims or demo content were added.
- Never store credentials in this file, Git, screenshots or reports. Use the existing local admin
  account. PostgreSQL is required; there is no SQLite fallback.

## What exists

Ten Phase 2 apps now join `core` and `services`: `products`, `portfolio`, `digital_marketing`,
`ai_automation`, `custom_software`, `web_development`, `mobile_development`, `cyber_security`,
`blog` and `crm`. Shared video lives in `core`. All have admin screens and committed migrations.

`core/content_admin.py` reuses native Unfold language tabs and translated inline templates.
Its inline constructor receives the parent model, so field introspection must use `self.model`.
Case-study proxy models are explicitly registered with modeltranslation; their admins filter
lookups and force the corresponding service when saving.

`config/admin_navigation.py` groups all implemented content. `config/dashboard.py` counts only
permitted records and excludes proxies to prevent duplication. `templates/admin/index.html`
renders its four widgets. The translation-review count already works for machine-marked rows;
Groq actions and logs remain Phase 3.

`crm/notifications.py` sends minimal staff alerts after commit. Unsent alerts can be retried from
admin. No durable queue exists. Live SMTP has not been tested. Configure `ADMIN_BASE_URL`,
`LEAD_ALERT_RECIPIENTS`, SMTP values and `EMAIL_TIMEOUT` in `.env`; never copy real values into Git.

Videos permit zero or one owner. Mobile features use plain text, one item per line. Editorial
reference models reuse publication gates. Phase 4 must also filter machine-translated nested
features, metrics, images, categories and tags, not only their published parents.

`/api/v1/` remains a stub. No public serializers, capture endpoints or `seed_demo` have been
implemented. The frontend remains the six-locale Blueprint scaffold with persisted light/dark/system
selection. API transport lives in `src/lib/api.ts`; components use semantic design tokens.

## Next phase, only after approval

Phase 3 adds `apps.translations`, the Groq service, admin actions, translation logging and retry
behavior. Fill only empty non-English fields, preserve proper nouns and HTML structure, record
machine status, and never auto-publish. Show the user output quality in all five non-English
locales before moving on. The existing `tag_signature()` helper supports HTML verification.

## Implementation constraints

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

## Business inputs still needed

These inputs are not supplied; leave their public content empty until confirmed.

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
