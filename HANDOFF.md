# Handoff — Phase 3 checkpoint, October 2, 2026

**Phase 3 is implemented. Wait for translation-quality review and explicit approval before Phase 4.**
Read `CLAUDE.md` and `BUILD_PROMPT.md` before editing. See
[the checkpoint](docs/PHASE_3_CHECKPOINT.md) and [live samples](docs/PHASE_3_TRANSLATION_SAMPLES.md).

## Current state

- Phase 1 baseline `5c84df2` is on GitHub. Phase 2 implementation `882d55c` and its docs `e359b0a`
  are committed locally. Phase 3 implementation is `dd517e2`; inline fix is `0b5e045`. These are local, not pushed.
- 135 backend tests pass. Ruff, migration drift and production Django checks pass. Frontend build
  passes; no frontend code changes in Phase 3. TranslationLog migration is applied locally.
- Groq translations succeeded for AI & Automation and Cyber Security names in all five locales.
  Both records are draft/machine. Rich HTML samples are in the report, not saved as website copy.
- Use existing local credentials; never copy keys, passwords or raw provider errors into reports.
- No dependencies were added. PostgreSQL is required. No Phase 4 APIs or seed_demo exist yet.

## Implementation notes

`apps.translations.services.GroqTranslator` batches saved English fields with blank targets,
validates all output before each batch save, and checks concurrent edits under a row lock.
`LanguageTabsMixin` supplies confirmation-based bulk/detail actions to translated models.
Related children are translated separately. Machine text resets publishable records to draft.
Audit logs contain only field names, IDs, locale, outcome, attempts and fixed error codes.
Retry from the record action; completed fields are kept. The CLI supports explicit model/IDs/locales.

The Groq default changed to `qwen/qwen3.8-27b` because the previous model was retired. It is a
preview model; recheck availability before production. The endpoint cannot redirect credentials.
Requests use bounded retries and adaptive output budgets. Known protected names use opaque
placeholders; HTML, URLs, numbers and length limits are validated after restoration.

Admin operations are synchronous, limited to three records and 6,000 characters per batch by
configurable defaults. Oversized individual fields fail safely; they are not silently truncated.
There is no durable queue or global provider rate scheduler. Initial provider failures remain in
local audit history, followed by successful translations and five safe no-op entries.

Browser verification found unscoped `x-show="open"` in collapsible translated inlines. The condition
now applies only to nested inlines with matching Alpine state; top-level panels use native details.

Phase 2 content/CRM architecture remains described in docs/PHASE_2_CHECKPOINT.md. Live SMTP is still
unverified. Public serializers must gate both parent and child machine translations in Phase 4.
The public frontend remains the localized Blueprint scaffold; its transport is src/lib/api.ts.

## Next phase, only after approval

Phase 4: public API and seed data per BUILD_PROMPT.md. Do not start until the user approves the
Phase 3 output quality. Preserve all earlier phase constraints and real-fact boundaries.

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
