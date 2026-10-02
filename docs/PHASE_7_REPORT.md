# Phase 7 — SEO and performance review

Date: October 2, 2026.

The SEO integration and performance/accessibility fixes are implemented. **Final acceptance remains
open until Home and a service page consistently meet the requested 95+ mobile Performance score.**
GA4 and Search Console are ready to configure; the user confirmed that neither ID is available yet.
No real content was published, no real lead was created, and no secrets belong in this commit.

## What changed

- Frontend `/sitemap.xml` maps the publish-gated API sitemap onto the frontend origin, with six
  locales, `zh-Hans`, `x-default` and source modification timestamps. `/robots.txt` advertises it.
  Publishing invalidates the sitemap as well as localized page layouts; 300-second ISR remains.
- Metadata includes localized title/description, canonical URL, seven language alternates,
  Open Graph locale variants, Twitter large-image cards and favicon. Image preference is page
  override, site default, then the supplied 1200×630 Automex wordmark fallback. Blog Open Graph
  uses article dates and author. Existing Organization/LocalBusiness, Service, Article, Product,
  BreadcrumbList, FAQPage and VideoObject markup remains tied to actual API content.
- Optional GA4 sends one explicit pageview per pathname change after its script is ready. IDs
  are validated before being interpolated into scripts. Explicit pageview URLs omit queries,
  fragments and referrers; no lead values or submission payloads are sent to analytics by our code.
  Blank/invalid IDs load no Google analytics script. Search Console verification is optional metadata.
- Arabic and Chinese font stylesheets are linked only for their respective locales. Full Unicode
  coverage and fallback metrics are preserved, with OFL licenses and immutable hashed font assets.
  Latin visitors no longer receive the large CJK font stylesheet. Only Latin heading/body faces
  preload; technical monospace is loaded on demand.
- Hero images keep responsive Next image optimization, aspect-ratio space reservation, preload and
  explicit high fetch priority. Disposable image fixtures verify real AVIF optimization. Other images
  remain lazy. No image is inverted by the theme switch.
- Quote forms defer Turnstile loading until the widget approaches the viewport. Submission still
  requires a valid token and Django verification; no CAPTCHA bypass was added.
- Navigation stops speculative link prefetching by default; client navigation and locale switching
  remain functional. The homepage status illustration animates transforms rather than border paint.
- Dark muted text contrast was increased; listing card headings now follow the page heading hierarchy.
  Rejected hydration experiments are not included because they did not improve the measured result.

## Verification

- Django: **177 tests passed**, including API publish gates, translation handling, lead protections,
  admin operations and revalidation behavior. No backend model/schema change was required.
- Frontend production build, ESLint and TypeScript checks pass. **11 unit tests** cover API transport,
  webhook authentication/invalidation, capture errors, video URLs and SEO/analytics helpers.
- Populated HTTP checks cover **90 routes** across all six locales, plus unknown routes, filtering and
  pagination. HTML includes content, metadata and structured data without executing JavaScript.
- SEO HTTP checks pass for sitemap/robots, social defaults, favicon, conditional font CSS and disabled GA4.
- Live disposable database lifecycle: publish includes URLs, unpublish removes the service and dependent
  case study, noindex removes the URL and renders a noindex tag, and republishing restores it.
- Browser: Home and service at 390×844 in six locales × two themes (24 checks); no horizontal overflow.
  Arabic uses RTL and IBM Plex Sans Arabic; Chinese uses Noto Sans SC. Service hero images loaded.
  Desktop Arabic/Chinese and English screenshots were inspected. Client language switching correctly
  changes direction and font CSS. Keyboard skip-to-content, menu Enter/Escape and FAQ expansion work.
- Turnstile was absent on initial service load, loaded when the form came into view, and enabled the
  submit button after verification. No new form request was submitted during Phase 7.

This is a scoped automated and manual accessibility review, not a claim of comprehensive WCAG
certification. Real long-form content, final artwork, real video captions and production infrastructure
must be checked again when supplied. Browser details are in [phase7-browser-checks.json](phase7-browser-checks.json).

## Lighthouse

Results below use Lighthouse 12.8.2, headless Chrome, production Next server, default **mobile simulated
throttling** and an isolated populated Django database. They are local lab measurements, not production
Core Web Vitals. No audit category or CPU throttle was relaxed. Browser/test/build activity was stopped
while recording the final measurements. Host timing varies, so all final runs are retained in the compact
[audit record](phase7-lighthouse.json), with individual scores rather than only the best result.

| Page | Performance runs | Median Performance | SEO | Accessibility | Best practices | CLS |
|---|---|---:|---:|---:|---:|---:|
| Home | 78, 73, 95 | 78 | 100 | 100 | 100 | 0 |
| Service | 95, 71, 94 | 94 | 100 | 100 | 100 | 0 |

The remaining work is reducing initial JavaScript/hydration blocking and hero render delay, then
repeating the same mobile audit on the actual deployment and final content. Do not hide below-target
runs or present the SEO score as the Performance score. Google rich-result eligibility and indexing
cannot be guaranteed by valid markup or a Lighthouse score.

## Configure analytics and Search Console later

1. Create a GA4 property and web data stream for the public site. Put its `G-...` measurement ID in
   `NEXT_PUBLIC_GA4_MEASUREMENT_ID` in the ignored frontend environment file, or the admin Site Settings
   GA4 field. The environment value takes precedence. Leave both blank to keep tracking disabled.
2. Disable enhanced-measurement automatic pageviews/history tracking in that stream, because this app
   sends explicit pageviews. Review/disable other automatic form or outbound-event collection before
   enabling analytics; stream-level behavior is outside this repository. Google's
   [pageview documentation](https://developers.google.com/analytics/devguides/collection/ga4/views)
   explains the duplicate-event risk with manual tracking.
3. Rebuild/restart when changing frontend environment values. Verify initial load and client navigation
   in GA4 Realtime/DebugView, including that query parameters and form fields are absent. Live Google
   event delivery is **unverified** because no measurement ID was supplied. Add any required consent
   behavior before enabling tracking for audiences that require it.
4. For Search Console URL-prefix verification, put only the HTML tag's `content` value in
   `GOOGLE_SITE_VERIFICATION`, rebuild and verify ownership in Google. A Domain property can instead
   use Google's DNS verification. Submit `https://automex.tech/sitemap.xml` after deployment; set
   `NEXT_PUBLIC_SITE_URL=https://automex.tech` first so canonical/sitemap URLs use the real origin.

Do not send passwords, service-account keys or private Google credentials. Measurement IDs and HTML
verification values are public identifiers, and neither has been invented or added to your local files.

## Run and review

Start Django in one terminal:

```sh
cd backend
source .venv/bin/activate
python manage.py runserver 8000
```

Start Next in another:

```sh
cd frontend
npm run dev
```

Visit `http://localhost:3000/en`, `/ar`, `/zh`, `/sitemap.xml` and `/robots.txt`.
Existing drafts stay private. A service route can return 404 until its real content is reviewed and
published through admin. A local development server is not the right target for Lighthouse scoring.
All agent-started preview servers are stopped after verification.

For a reproducible populated preview, run `backend/tests/preview_phase6.py` with the backend venv.
It creates an isolated database and temporary TEST media on port 8002; Ctrl-C removes both. Override
`API_URL=http://127.0.0.1:8002/api/v1`, `NEXT_PUBLIC_MEDIA_URL=http://127.0.0.1:8002/media/` and
`NEXT_PUBLIC_SITE_URL=http://localhost:3001` for both the frontend build and `npm run start -- --port 3001`.
Clear only `.next/cache/fetch-cache` when replacing disposable fixtures, to avoid stale fixture media.
Run `PHASE6_FIXTURES=1 npm run test:shell` and `npm run test:seo:http`. Do not build fixture URLs into
production; rebuild using normal deployment environment values afterwards.

Example mobile audit (one page at a time, no concurrent build or tests):

```sh
npx --yes lighthouse@12.8.2 http://localhost:3001/en \
  --chrome-flags='--headless' \
  --only-categories=performance,accessibility,best-practices,seo \
  --output=json --output-path=/tmp/automex-home-lighthouse.json
```

Repeat for `/en/ai-automation`. Re-run after adding real images, analytics or hosted videos.
The generator `node scripts/generate-social-image.mjs` recreates the fallback social image/favicon
from semantic brand tokens, using Sharp already installed by Next; no dependency was added.

## Screenshots

These are disposable TEST fixtures, not claims about Automex's services or clients.

- [English, dark desktop](screenshots/phase7-en-dark-desktop.png)
- [Arabic, light desktop](screenshots/phase7-ar-light-desktop.png)
- [Arabic, dark mobile](screenshots/phase7-ar-dark-mobile.png)
- [Chinese, light desktop](screenshots/phase7-zh-light-desktop.png)

Production deployment, live SMTP/newsletter delivery, verified business content, approved logo artwork,
GA4 receipt and Search Console ownership remain outside the verified local result.
