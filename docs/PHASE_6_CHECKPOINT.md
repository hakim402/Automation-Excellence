# Phase 6 — Content pages and quote requests

Implemented October 2, 2026. Stop here for user review before Phase 7.

## Delivered

- Server-rendered home, six services through one shared template, product catalog/details,
  work catalog/details, blog catalog/articles, about/team and contact pages.
- Conditional content sections, desktop section rail, mobile anchor strip, scroll tracking,
  server-side filters/pagination, related content, sanitized rich text and empty states.
- Shared landscape player and portrait reel strip: reserved aspect ratios, click-to-load embeds,
  no autoplay, captions when supplied, keyboard scrolling and reduced-motion support.
- Six-language UI, English content fallback, Arabic layout, light/dark/system tokens.
- Quote forms with service/product attribution, source path, language and UTM fields; native
  validation, pending/error/success states, honeypot and real server-verified Turnstile.
- Metadata, canonical/hreflang, Open Graph and applicable structured data are included with pages.
  Phase 7 still owns the sitemap/robots frontend routes, analytics and formal performance/accessibility audit.
- Gated homepage aggregation at `/api/v1/home/`. Optional translated `SiteSettings.response_time`
  is editable in admin; migration `core.0010` is applied locally. It remains blank until a real
  business response-time expectation is supplied.

## Publication and cache behavior

Django content saves, deletes and relation changes notify Next **after transaction commit**.
The webhook uses an Authorization Bearer secret and accepts only `{"scope":"content"}`.
It clears the public-content cache tag and localized route layout. The broad scope intentionally
keeps navigation, related content and homepage collections consistent after unpublishing.
CRM saves and rolled-back content transactions do not trigger it. Redirects are refused;
provider error details and credentials are not logged. Failures do not undo an admin save.

Set `REVALIDATE_WEBHOOK_URL` to the frontend `/api/revalidate` endpoint and use the same strong
value for backend `REVALIDATE_WEBHOOK_SECRET` and frontend `REVALIDATE_SECRET`. Local secrets
were synchronized only in ignored environment files. Restart both development processes to load them.
Retry an unsuccessful notification with `python manage.py revalidate_frontend`.
QuerySet bulk updates bypass Django signals and must be followed by that command.

Reads have a 300-second ISR fallback; failed invalidation can leave previously public cached
content visible until a subsequent successful refresh. This is not an immediate removal guarantee
when the frontend or backend is unavailable. Build concurrency is bounded for the single-VPS API.

## Verification

- Backend full suite: **177 tests passed**; Ruff, system checks and migration drift checked.
- Frontend: production builds against both development content and isolated populated fixtures;
  ESLint, TypeScript and **8 unit tests** for API transport, capture, safe video hosts and webhook handling.
- HTTP checks cover **90 populated localized URLs** (15 paths × 6 locales), headings, canonical and
  language metadata, structured data, missing-page 404s, filters, pagination and lazy video embeds.
- Real browser quote submission: Cloudflare completed automatically, POST returned **201**, and the
  success message appeared. The disposable database row had the expected service, locale, source
  path and UTM source. Alert delivery was disabled; no real customer record was created.
- Live publish lifecycle: isolated service unpublish triggered webhook and returned **404**;
  republish triggered webhook and returned **200**.
- Browser review: English/Arabic service pages in light/dark, mobile Arabic at 390px with no page
  overflow, mobile product detail, homepage, article, Arabic case study and contact success.
  Formal WCAG, Lighthouse, real uploaded media and provider playback audits remain Phase 7 work.

Screenshots use explicitly labeled **TEST** content from a separate database, not company claims:

| View | Screenshot |
|---|---|
| English light | [Service](screenshots/phase6-en-light.png) |
| English dark | [Service](screenshots/phase6-en-dark.png) |
| Arabic light | [Service](screenshots/phase6-ar-light.png) |
| Arabic dark | [Service](screenshots/phase6-ar-dark.png) |
| Arabic mobile | [Service](screenshots/phase6-ar-mobile.png) |
| Home | [Home](screenshots/phase6-home.png) |
| Quote success | [Success](screenshots/phase6-form-success.png) |

## Review locally

1. Restart Django on port 8000: `cd backend && .venv/bin/python manage.py runserver 8000`.
2. Restart Next: `cd frontend && npm run dev`.
3. Open `http://localhost:3000/en` and `/ar`; review home, contact, about and catalog routes.
4. Publish **human-reviewed** service/product/article records in admin to review populated pages.
   Draft/machine content remains gated and detail URLs correctly return 404. No existing drafts
   were published during this phase.
5. Submit a clearly labeled quote request and inspect CRM → Leads. Normal local alert settings
   apply outside the isolated test harness.

`backend/tests/preview_phase6.py` recreates the disposable populated preview on port 8002 and
removes its database on normal shutdown. Use `API_URL=http://127.0.0.1:8002/api/v1` and, only when
checking form writes, `NEXT_PUBLIC_API_URL=http://127.0.0.1:8002/api/v1` for a temporary build on
port 3001. `PHASE6_FIXTURES=1 npm run test:shell` checks populated routes. Stop temporary servers
and rebuild with normal environment values afterwards; do not deploy fixture builds.

Live SMTP delivery and newsletter confirmation remain outstanding from Phase 4. No dependencies
were added. Phase 7 requires explicit user approval.
