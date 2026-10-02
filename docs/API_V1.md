# Automex API v1

Base URL: `/api/v1/`. Discovery: `GET /api/v1/`. Phase 4, October 2, 2026.
Public content is read-only and requires no API key. Capture endpoints accept POST only and never
return private CRM records. Django admin authentication is separate.

## Content and locale contract

Every read accepts `?lang=en|es|fr|de|zh|ar`. Missing/invalid locale means English. A blank localized
field falls back to its saved English column. Slugs, client names, technical names, URLs and numbers
remain unchanged. Raw `_en`/`_ar` columns, workflow fields and internal record IDs are not exposed.
Missing images are `null`; populated media fields return absolute URLs using the request origin.

Publishable records must be published and not machine-translated. Services must also be active.
Nested features, images, metrics, categories, tags, industries, authors and other translated content
are filtered by review state. Hidden single references return `null`; hidden list items disappear.
Case studies and service-associated posts/testimonials require a public service. Videos require
public owners, including a case study's service. Independent products may remain public with hidden
service references removed.

Site settings return 404 while machine-translated. Team members must be active and reviewed or
untranslated. Models without a draft flag use their existing translation/active controls. The
Afghanistan phone returns an empty string until its explicit public switch is enabled.

Content responses include `Cache-Control: public, max-age=0, must-revalidate`. JSON responses also
carry an ETag; a matching `If-None-Match` returns 304. The API rechecks publication on every request.
Next.js ISR caches and publish-triggered invalidation are separate Phase 6 work.

## Read endpoints

| Endpoint | Response and filters |
|---|---|
| `GET /site/settings/` | Singleton company facts, public contact fields, branding and default SEO |
| `GET /services/` | Minimal service array: key, slug, name, icon, intro, hero image |
| `GET /services/{slug}/` | Complete service object with all sections below |
| `GET /services/{slug}/case-studies/` | Paginated cases for that public service |
| `GET /products/` | Paginated cards; `category`, `service` (slug), `page` |
| `GET /products/{slug}/` | Product, features, gallery, videos, stack, services, industries, SEO |
| `GET /videos/` | Array; `orientation`, `service`, `product`, `featured` |
| `GET /portfolio/case-studies/` | Paginated cards; `service`, `industry` (slugs), `page` |
| `GET /portfolio/case-studies/{slug}/` | Case, metrics, gallery, stack, videos, SEO |
| `GET /blog/posts/` | Paginated cards; `category`, `tag`, `service` (slugs), `page` |
| `GET /blog/posts/{slug}/` | Post body, public author/category/tags/service, SEO |
| `GET /blog/categories/` | Category array |
| `GET /team/` | Active team array, with no staff email addresses |
| `GET /testimonials/` | Public testimonial array |
| `GET /seo/sitemap/` | All six locale URLs, lastmod and language alternates including x-default |

Paginated endpoints use 12 records per page and the standard envelope:

```json
{"count": 0, "next": null, "previous": null, "results": []}
```

Other collections are arrays. A missing, draft, inactive or machine-only detail URL returns 404.
Unknown category/service/tag filters return empty results. Invalid page numbers return 404.
`featured` accepts `true`, `false`, `1` or `0`; other values return 400.
Sitemap excludes `noindex` and hidden detail records. It includes static Home/About/Contact/Products/
Work/Blog routes in each locale. Detail lastmod comes from the page record's `updated_at`; static
lastmod comes from public site settings. This is a JSON feed for the later Next.js sitemap route.

### Complete service response

Alongside service prose, imagery and SEO fields, the response includes these sibling keys:

`offerings`, `process_steps`, `faqs`, `tools`, `industries`, `stats`, `testimonials`, `case_studies`
(featured), `products`, `videos`, `specific_content`.

`specific_content` contains only the corresponding service family's fields:

| Service | Keys |
|---|---|
| digital-marketing | campaigns, creative_work, social_channels |
| ai-automation | use_cases, agent_types, integrations |
| custom-software | system_types, database_capabilities |
| web-development | capabilities |
| mobile-development | apps (including reviewed screenshots) |
| cyber-security | security_services, compliance_standards, certifications |

Querysets select/prefetch relations; expanding cases or use cases does not add a query per row.
Each service-specific content type uses its existing model's publication/review controls.

## Capture endpoints

JSON and URL-encoded forms are accepted; file uploads are not. Responses have `Cache-Control:
no-store`. Unrecognized input fields are rejected, so clients cannot set status, notes, IPs or
confirmation flags.

### POST /crm/leads/

Example request shape (the token must come from a real configured frontend widget):

```json
{
  "full_name": "Your name",
  "email": "you@example.com",
  "phone": "",
  "company": "",
  "country": "",
  "service": "web-development",
  "message": "Describe your project",
  "preferred_contact": "email",
  "locale": "en",
  "source_path": "/en/web-development",
  "utm_source": "",
  "utm_medium": "",
  "utm_campaign": "",
  "turnstile_token": "TOKEN_FROM_WIDGET",
  "website": ""
}
```

Required: `full_name`, valid `email`, nonblank `message` (maximum 10,000 characters), and
`turnstile_token` (maximum 2,048 characters). Optional `service`/`product` accept public slugs;
use null or omit when unselected. Optional `product` adds its canonical slug to the saved message.
`locale` defaults to en and `preferred_contact` to email. Phone/WhatsApp preference requires a phone.
`source_path` must be a relative `/path`, without query or fragment; UTM values have separate fields.

Success is 201 with only `{"detail":"Thank you. Your request has been received."}`. New leads start
as `new`. IP and user-agent come from the server request. The existing after-commit staff alert
contains an admin link, not the submitted personal details.

### POST /crm/newsletter/

Required: `email`, `turnstile_token`. Optional: `locale`, `website`. Turnstile widget action is
`newsletter`. Success is 202 with the same generic detail. Repeating a subscription with different
email casing gives the same response and leaves existing locale/confirmation state unchanged.
New subscribers remain **unconfirmed**; confirmation-email delivery is not implemented in this phase.

### Spam checks and errors

Both endpoints use independent per-IP limits (default 5/hour each). PostgreSQL counters are atomic
and shared across workers. The fixed window starts with the first request; requests at the window
boundary can form a short burst. Counters contain HMAC identifiers, not raw IPs. Invalid and
honeypot requests also consume quota. Run `python manage.py prune_capture_throttles` periodically
to remove expired counters. There is no new Redis dependency.

`website` is the honeypot: the frontend must keep it hidden and blank. A filled value receives the
normal success shape but creates no record, sends no email and does not contact Cloudflare.

The server sends the token and optional client IP to Cloudflare; it does not send lead text or
contact details. A successful response must match the allowed hostname and the endpoint's exact
widget action (`lead` or `newsletter`). Verification uses a timeout and refuses redirects.

- 400: validation error, invalid/expired/replayed token, wrong hostname/action.
- 405: unsupported method, including GET on CRM endpoints.
- 429: rate limit, with a Retry-After header.
- 503: missing provider configuration, unavailable provider or malformed provider response.

These checks follow [Cloudflare's server-side validation contract](https://developers.cloudflare.com/turnstile/get-started/server-side-validation/).
Tokens expire after five minutes and are single-use; the future frontend must reset its widget
when retrying. No development bypass is included.

## Turnstile and reverse-proxy setup

In the ignored backend `.env`, configure `TURNSTILE_SECRET_KEY`, `TURNSTILE_ALLOWED_HOSTNAMES`,
and optionally `TURNSTILE_TIMEOUT` (default 10 seconds). Configure the frontend's matching public
site key when implementing its forms. Restart Django completely after environment changes.
Do not paste real secrets into documentation or Git.

Allowed hostnames are exact names without scheme or port. They default to FRONTEND_ORIGIN's host.
For a deployment at automex.tech/www.automex.tech, explicitly allow the hostnames your widget uses.

By default, incoming forwarded-IP headers are ignored. If a reverse proxy is used, add **only its
direct IP/CIDR** to `CAPTURE_TRUSTED_PROXIES` and ensure it overwrites `X-Real-IP` from a verified
client source. Do not copy arbitrary client-supplied headers. Restrict direct backend access in
production. Otherwise all proxied visitors will share the proxy's rate-limit bucket.

Cloudflare's [public test credentials](https://developers.cloudflare.com/turnstile/troubleshooting/testing/)
were used only in an isolated probe. Its dummy success response returned `example.com` with no
action, so the probe supplied those expected values. Public endpoint actions remain strict and do
not accept that dummy response as a real lead/newsletter verification. A production widget/domain
integration still needs the real key and frontend form.
