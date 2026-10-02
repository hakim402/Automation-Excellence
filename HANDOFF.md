# Handoff — Phase 5 checkpoint, October 2, 2026

**Phase 5 is implemented. Wait for user review and explicit approval before Phase 6.**
Read CLAUDE.md and BUILD_PROMPT.md before editing.
See [Phase 5 checkpoint](docs/PHASE_5_CHECKPOINT.md) for scope, tests, screenshots and review steps.

## Current state

- Shared localized frontend shell, responsive services/products menu, public API footer, theme and
  route-preserving locale controls are implemented. Real pages remain Phase 6.
- Frontend build, lint, typecheck, four API transport tests and HTTP checks across 72 shell URLs pass.
  Backend suite: 171 tests pass. English/Arabic light/dark screenshots are in docs/screenshots/.
- Development compiler output is `.next-dev`, separate from production `.next`. Do not merge them:
  concurrent dev/build output previously caused missing-chunk 500 responses.
- `lib/api.ts` and environment access are server-only. Public form transport is future Phase 6 work.
  Shell API reads revalidate every 300 seconds. Publish-triggered invalidation is not implemented yet.
- All navigation placeholders are noindex. Replace the `[page]` allowlisted routes with real pages in
  Phase 6; unknown paths correctly 404. Service labels/descriptors in messages are navigation UI;
  full service content still belongs to Django and its publish/review gates.
- Real Turnstile keys are configured locally. Live browser verification followed by curl saved one
  labeled test lead with HTTP 201; invalid token returned 400. Test alerts were disabled. Live SMTP
  and newsletter confirmation delivery remain outstanding. Never include keys in Git or reports.
- Existing content remains untouched. Draft public collections can legitimately be empty.
- Stop at the Phase 5 checkpoint. No dependencies added or secrets committed.

## Phase 4 architecture

core/api.py provides explicit localized fields, safe nested relations and public query helpers.
core/public_queries.py defines shared owner gates and prefetch plans. Service page serialization
lives in services/page.py to avoid circular imports with service summary serializers used by products,
portfolio and blog. All public models have allowlisted serializers. No CRM read view exists.

Publishable records use .published(); nonpublishable children use translation/active flags.
Cases require public services, posts/testimonials respect optional service visibility, and videos
check owners (including case-study service). Site settings return 404 while machine-translated;
the private Afghanistan phone is never exposed unless its explicit flag is enabled.

crm/turnstile.py sends only token and optional client IP to Cloudflare and verifies exact hostname
and action. The widget must set action lead/newsletter. No bypass is provided. Dummy Cloudflare
responses returned example.com/no action, tested only in a separate process with those expectations.

crm/throttling.py uses atomic PostgreSQL counters shared across workers. X-Real-IP is trusted only
from configured direct proxy CIDRs; X-Forwarded-For is ignored. Counters use HMAC keys. Configure
proxy rewriting and run prune_capture_throttles periodically during deployment.

seed_demo is DEBUG-only, idempotent via reserved demo identities, skips children of published
services and does not rewrite existing records. Publishable demos stay drafts; the demo author is
inactive. The category has no draft flag and is clearly labeled DEMO. Keep demo names/slugs stable
for reruns. No media, certifications or CRM data were fabricated.

JSON ETags revalidate on every API read. Frontend ISR/publish webhook is still Phase 6. Sitemap
includes six locales and alternates; lastmod tracks page rows, not nested child edits.

## Existing translation implementation

apps.translations fills missing fields from saved English, validates HTML/protected names, and
rechecks source/targets under row locks. Machine text returns publishable records to draft. Groq
model/key are environment-only; audit logs omit content and raw provider responses. Current model
is qwen/qwen3.8-27b (preview; recheck before launch). Restart Django fully after .env edits:
automatic code reload may inherit the old reloader parent's environment.

## Next phase, only after approval

Phase 6: real homepage, service/product templates and content pages, forms, video components,
ISR publish webhook. Follow the complete BUILD_PROMPT.md route list, including Products.

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
