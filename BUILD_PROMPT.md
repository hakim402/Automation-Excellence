# Automex — Build Prompt for Claude Code

Paste this as your opening message in Claude Code, from the `automex/` directory.
`CLAUDE.md` holds the standing rules. This file holds the system design and the build order.

---

## Your role

You are the lead engineer building the Automex company website and content backend from scratch,
in this repository, following `CLAUDE.md`.

Build it in the phases below. **Stop at every checkpoint**, report what you built, what you assumed,
and what you need from me. Do not run ahead.

---

## The business

Automex is a technology services company in Kent, Washington (Seattle metro), selling worldwide across
six service lines. Clients span SaaS, e-commerce, logistics, healthcare, finance, education, and government.

| Service | Slug | Covers |
|---|---|---|
| Digital Marketing | `digital-marketing` | Campaigns, social media, video and poster design, SEO, paid ads, content |
| AI & Automation | `ai-automation` | ML projects, AI agents, chatbots, RAG assistants, workflow automation, integrations |
| Custom Software Development | `custom-software` | ERP, CRM, MIS, CMS, reporting systems, database design, SaaS platforms |
| Web App Development | `web-development` | Corporate sites, e-commerce, portals, SaaS frontends, headless builds |
| Mobile App Development | `mobile-development` | iOS, Android, cross-platform |
| Cyber Security | `cyber-security` | Pen testing, VAPT, audits, compliance, monitoring, incident response |

The existing site fails because visitors cannot find what they need. **Clarity is the product requirement.**

---

## Confirmed decisions

| Area | Decision |
|---|---|
| Backend | Django 5 + Django REST Framework + PostgreSQL |
| Admin theme | **django-unfold** (required) |
| Frontend | Next.js 15 App Router + TypeScript + Tailwind CSS |
| Coupling | Headless. REST only, at `/api/v1/` |
| Rendering | Static generation + ISR, with on-demand revalidation on publish |
| Hosting | Single VPS, **no Docker for now**. Write `Dockerfile`s and `docker-compose.yml` but do not wire the workflow to them |
| Locales | `en`, `es`, `fr`, `de`, `zh`, `ar` — public site. **Admin English only.** Full RTL |
| Theming | **Light and dark modes, as equals.** Semantic tokens, `next-themes`, three-state toggle (light / dark / system). Brand palette is "Blueprint" — see `CLAUDE.md` §8 |
| Translation | `django-modeltranslation` + Groq API admin action → machine draft → human review → publish |
| CRM | Lead capture only. Form → Django admin list, tagged by service |
| Pricing | Not shown. Everything is a quote request |
| Portfolio | Real client work — names, results, screenshots (I supply content) |
| Blog | Yes, all six languages |
| Media | Local disk, `/media`, abstracted so S3 is a settings swap |
| Email | SMTP via env vars (Resend recommended) |
| Spam | Cloudflare Turnstile + honeypot + throttling |
| Analytics | GA4 + Google Search Console |

---

## Architecture

```
Visitor ──▶ Next.js (SSG/ISR, six locales, RTL)
               │  fetch at build + revalidate
               ▼
          Django REST API  /api/v1/  (public, read-only, English-fallback)
               │
               ├── PostgreSQL
               ├── /media (local disk)
               └── Groq API (admin-triggered translation only)

Staff ────▶ Django Admin (Unfold, English) ──▶ publish ──▶ webhook ──▶ Next.js revalidate
Visitor ──▶ Contact form ──▶ POST /api/v1/crm/leads/ ──▶ Lead row + email alert
```

---

## Backend design

### App list (`backend/apps/`)

```
core             SiteSettings, Tool, Industry, Testimonial, TeamMember, Stat, Video, abstracts
services         Service, ServiceOffering, ProcessStep, FAQ  (shared across all six)
products         Product, ProductFeature, ProductImage        ready-to-use offerings
portfolio        CaseStudy, CaseStudyMetric, CaseStudyImage  (shared, FK to Service)
digital_marketing   Campaign, SocialChannel, CreativeWork
ai_automation       AutomationUseCase, AgentType, Integration
custom_software     SystemType, DatabaseCapability
web_development     WebCapability
mobile_development  MobileApp, MobileAppScreenshot
cyber_security      SecurityService, ComplianceStandard, Certification
blog             Category, Tag, Post
crm              Lead, NewsletterSubscriber
translations     GroqTranslator, TranslationLog, admin action
```

**Design note — read this before building.** The requirement is "design the backend separately for each
service." I am deliberately splitting it two ways rather than duplicating six near-identical apps:

- **Shared content types** (offerings, process steps, FAQs, tools, case studies, testimonials) live once,
  with a foreign key to `Service`. Six copies of the same model would be six times the maintenance for
  one solo maintainer, and the admin would drift out of sync.
- **Genuinely distinct content types** get their own app — a Digital Marketing campaign is nothing like
  a mobile app store listing, and forcing them into one model would produce a form full of blank fields.

In the Unfold sidebar this still reads as six separate sections, because navigation is grouped by service.
The admin user sees "Digital Marketing → Campaigns / Creative Work / Social Channels / Case Studies / FAQs"
regardless of which app the model lives in. **Do not change this structure without telling me why.**

### Models

Abstract bases in `core`:
- `TimeStamped` — created_at, updated_at
- `Publishable` — status (draft/published), published_at, translation_status (none/machine/reviewed)
- `SEOFields` — meta_title*, meta_description*, og_image, noindex

`*` = translatable. Translatable fields are marked `*` throughout below.

**core**
- `SiteSettings` (singleton) — company_name, tagline*, about_short*, logo, logo_dark, favicon,
  address lines, city, state, zip, country, phone_us, phone_af, email, domain,
  founded_year, team_size, social links (linkedin, x, github, instagram, youtube, facebook),
  ga4_measurement_id, default meta fields*
- `Tool` — name, slug, logo, category (choice: marketing/ai/backend/frontend/mobile/security/data/cloud), url
- `Industry` — name*, slug, icon, description*
- `Testimonial` — client_name, client_role*, client_company, company_logo, quote*, rating, service FK, is_featured
- `TeamMember` — name, role*, bio*, photo, linkedin, github, order
- `Stat` — label*, value, unit, service FK (nullable), order
- `Video` — title*, description*, orientation (landscape/portrait), source (youtube/vimeo/file),
  external_url, video_file, poster_image, duration_seconds, captions_url,
  service FK (nullable), product FK (nullable), case_study FK (nullable), is_featured, order

`Video` is one shared model with three nullable foreign keys — not generic relations, and not a
separate video model per app. Orientation is required because the frontend renders the two shapes
differently (see Frontend design). Default to YouTube/Vimeo embeds; self-hosted files on the VPS will
damage LCP, so treat `source=file` as the exception.

### Rich text fields — the complete list
Rich HTML is allowed **only** on these fields. Everything else is plain text. Sanitisation rules
are in `CLAUDE.md` §5.

```
Service.body
Product.body
CaseStudy.challenge / .solution / .outcome
Post.body
FAQ.answer            (links and lists only — no headings, no images)
```

If you think another field needs rich text, ask me first.

**services**
- `Service` — key (choice, matches the six slugs), name*, slug, icon,
  hero_headline*, hero_subline*, hero_image, intro*, body*, order, is_active,
  tools M2M(Tool), industries M2M(Industry), + `SEOFields`
- `ServiceOffering` — service FK, title*, description*, icon, order  ← the "what we do" cards
- `ProcessStep` — service FK, order, title*, description*  ← genuinely a sequence, so numbering is allowed here
- `FAQ` — service FK (nullable = general), question*, answer*, order

**products** — ready-to-use offerings sold alongside custom work
- `Product` — name*, slug, tagline*, category (choice: database / web-app / mobile-app / dashboard /
  automation / template / integration), summary*, body* (rich text),
  cover_image, icon, delivery (choice: ready-to-deploy / customisable / white-label),
  demo_url, docs_url, tech_stack M2M(Tool), services M2M(Service), industries M2M(Industry),
  is_featured, order, + `Publishable` + `SEOFields`
- `ProductFeature` (inline) — product FK, title*, description*, icon, order
- `ProductImage` (inline) — product FK, image, caption*, order

No pricing fields. Products follow the same rule as services: the CTA is "Request a demo" or
"Request a quote", and it posts to the same `crm.Lead` endpoint with the product recorded in the
message context. **Do not build a cart, a checkout, or a pricing table.**

**portfolio**
- `CaseStudy` — service FK, title*, slug, client_name, client_logo, industry FK, country,
  challenge*, solution*, outcome*, cover_image, project_url, duration_months,
  tech_stack M2M(Tool), is_featured, + `Publishable` + `SEOFields`
- `CaseStudyMetric` (inline) — case_study FK, label*, value, unit, order
- `CaseStudyImage` (inline) — case_study FK, image, caption*, order

**digital_marketing**
- `Campaign` — title*, client_name, objective*, summary*, results*, platforms (multi-choice),
  start_date, end_date, cover_image, reach, engagement_rate, conversions, is_featured, + Publishable
- `SocialChannel` — platform (choice), handle, url, follower_count, is_managed_for_clients, order
- `CreativeWork` — kind (choice: video/poster/graphic/reel/banner/motion), title*, description*,
  thumbnail, file, external_url, client_name, order, + Publishable

**ai_automation**
- `AutomationUseCase` — title*, description*, industry FK, icon, order
- `AgentType` — name*, description*, icon, example_prompt*, order  (chatbot, voice agent, RAG assistant, scraper…)
- `Integration` — name, logo, url, category (choice: llm/workflow/data/crm/comms), order

**custom_software**
- `SystemType` — name*, description*, icon, order  (ERP, CRM, MIS, CMS, reporting, inventory, HR, POS)
- `DatabaseCapability` — name*, description*, icon, order

**web_development**
- `WebCapability` — name*, description*, icon, order

**mobile_development**
- `MobileApp` — name, client_name, platforms (multi-choice), description*, features*,
  app_store_url, play_store_url, icon_image, downloads, rating, + Publishable
- `MobileAppScreenshot` (inline) — app FK, image, caption*, order

**cyber_security**
- `SecurityService` — name*, description*, icon, order  (pen test, VAPT, audit, monitoring, IR, training)
- `ComplianceStandard` — name, description*, logo, order  (ISO 27001, SOC 2, GDPR, HIPAA, PCI-DSS)
- `Certification` — name, issuer, logo, credential_url, order

**blog**
- `Category` — name*, slug, description*
- `Tag` — name*, slug
- `Post` — title*, slug, excerpt*, body* (WYSIWYG), cover_image, author FK(TeamMember),
  service FK (nullable), category FK, tags M2M, reading_minutes, is_featured,
  + `Publishable` + `SEOFields`

**crm**
- `Lead` — full_name, email, phone, company, country, service FK (nullable), message,
  preferred_contact (choice), locale, source_path, utm_source/medium/campaign,
  status (new/contacted/qualified/won/lost), internal_notes, ip_address, user_agent, created_at
- `NewsletterSubscriber` — email, locale, is_confirmed, created_at

### API surface (`/api/v1/`)

All read endpoints accept `?lang=<locale>` and fall back to English per field.

```
GET  /site/settings/
GET  /services/                         list, minimal
GET  /services/{slug}/                  FULL page payload: service + offerings + process +
                                        faqs + tools + industries + stats + testimonials +
                                        featured case studies + service-specific content
GET  /services/{slug}/case-studies/
GET  /products/                         ?category=&service=&page=
GET  /products/{slug}/                  full payload: product + features + gallery + videos
GET  /videos/                           ?orientation=&service=&product=&featured=
GET  /portfolio/case-studies/           ?service=&industry=&page=
GET  /portfolio/case-studies/{slug}/
GET  /blog/posts/                       ?category=&tag=&service=&page=
GET  /blog/posts/{slug}/
GET  /blog/categories/
GET  /team/
GET  /testimonials/
GET  /seo/sitemap/                      every published URL + lastmod, all locales
POST /crm/leads/                        throttled, Turnstile-verified
POST /crm/newsletter/                   throttled
```

`/services/{slug}/` returning one complete payload is deliberate — one API call renders one page,
which keeps ISR builds fast across six locales.

### Admin (Unfold)

Sidebar grouped by service, then by function:

```
Dashboard
Site
  Site Settings · Team · Testimonials · Tools · Industries · Stats
Services
  All Services · Offerings · Process Steps · FAQs
Products
  All Products · Features · Gallery
Media
  Videos
Digital Marketing
  Campaigns · Creative Work · Social Channels · Case Studies
AI & Automation
  Use Cases · Agent Types · Integrations · Case Studies
Custom Software
  System Types · Database Capabilities · Case Studies
Web Development
  Capabilities · Case Studies
Mobile Development
  Apps · Case Studies
Cyber Security
  Security Services · Compliance · Certifications · Case Studies
Content
  Blog Posts · Categories · Tags
Leads
  Leads · Newsletter
System
  Translation Log · Users
```

Per-service case study entries are the same model with a preset service filter — implement with
proxy models so each appears under its own service group.

Admin requirements:
- Six language tabs on every translatable form, English tab first.
- Bulk action: *Auto-translate to all languages* (Groq) — fills empty non-English fields only,
  marks `translation_status = machine`, never publishes.
- Coloured translation-status badge in every list view.
- Dashboard: new leads this week, leads by service, unpublished drafts, items awaiting translation review.
- Image fields show a thumbnail preview.

---

## Frontend design

### Routes

```
/[locale]                        Home
/[locale]/digital-marketing
/[locale]/ai-automation
/[locale]/custom-software
/[locale]/web-development
/[locale]/mobile-development
/[locale]/cyber-security
/[locale]/products               Ready-to-use products (filterable by category)
/[locale]/products/[slug]
/[locale]/work                   All case studies (filterable)
/[locale]/work/[slug]
/[locale]/blog
/[locale]/blog/[slug]
/[locale]/about
/[locale]/contact
```

Top navigation is exactly: **Home · Digital Marketing · AI & Automation · Custom Software ·
Web App Development · Mobile App Development · Cyber Security · About · Contact**.
On mobile and narrow desktop, the six services collapse into one "Services" mega-menu with a short
descriptor under each — a nine-item bar is the old site's findability problem repeating itself.
`/work` lives in the footer and in cross-links, not the top bar.

### Service page template (the core of the site)

Every service page shares one structure, filled with that service's content. A visitor who
understands one service page understands all six.

```
┌──────────────────────────────────────────────────────────────┐
│  HERO — headline, subline, one primary CTA (Request a quote) │
│  and one secondary (See our work). Service-specific visual.  │
├────────────┬─────────────────────────────────────────────────┤
│  LEFT RAIL │  What we do        offering cards               │
│  sticky    │  How we work       numbered process (a sequence)│
│  scroll-   │  Service-specific  campaigns / agents / systems │
│  spy       │                    / apps / security services   │
│  anchors   │  Watch it work     landscape demo + reel strip  │
│            │  Ready-made        products tied to this service│
│            │  Industries        who we build this for        │
│            │  Tools             stack we use                 │
│            │  Selected work     2–3 case studies             │
│            │  FAQ               accordion                    │
├────────────┴─────────────────────────────────────────────────┤
│  QUOTE FORM — service pre-selected, inline, not a separate   │
│  page. This is the conversion point.                         │
└──────────────────────────────────────────────────────────────┘
```

The left rail is the fix for the findability problem, and it mirrors the admin's per-service structure.
It collapses to a horizontal sticky chip bar under 1024px.

### Video rendering

Two shapes, two components, one model:

- **Landscape (16:9)** — `<VideoFeature>`. One main demo per service or product, full content width,
  poster image shown until clicked. Never autoplay with sound.
- **Portrait (9:16)** — `<VideoReelStrip>`. A horizontally scrollable strip of short vertical clips,
  the format used for social. Muted autoplay on the in-view clip is acceptable; everything else is
  paused. Snap scrolling, keyboard arrow navigation, and RTL-aware scroll direction.

Both must: lazy-load the embed (poster image first, iframe only on interaction — a YouTube iframe
on load costs you Core Web Vitals), reserve the aspect ratio so nothing shifts, expose captions,
and respect `prefers-reduced-motion` by never autoplaying.

Add `VideoObject` JSON-LD for every embedded video — it is one of the cheaper ways to win rich results.

### Products page

`/products` is a filterable grid by category (database, web app, mobile app, dashboard, automation,
template, integration). Each card shows cover, name, tagline, delivery type, and stack.
`/products/[slug]` follows the same left-rail template as a service page:
overview → features → screenshots → demo video → tech stack → related services → related case
studies → FAQ → request-a-demo form.

Products appear in the header mega-menu as a separate column beside the six services, and get a
section on the Home page after the service grid. **They are not in the nine-item top bar** —
see my note in the open items.

### Home page
Hero → what Automex does in one sentence → the six services as a scannable grid (each linking
straight to its page) → featured case studies → industries served → trust row (certifications,
compliance, tools) → recent posts → quote form.

Hero treatment: build a calm, live **systems readout** — a small instrument panel showing running
processes with steady state changes. It says "we build systems that run on their own" without a
sentence of marketing copy. Honour `prefers-reduced-motion` with a static state. Do **not** build
a big-number-plus-gradient hero.

### Contact page
One form, service dropdown, both phone numbers with country labels, email, the Kent address,
an embedded map, and response-time expectation. Posts to `/api/v1/crm/leads/` with the source path
and locale attached.

---

## Build phases

### Phase 0 — Scaffold
Both projects running, empty. Django with split settings (`base`/`dev`/`prod`), PostgreSQL connected,
DRF + CORS + Unfold installed and themed, `apps/` package created. Next.js with TypeScript, Tailwind
mapped to the tokens in `CLAUDE.md` §8, fonts loaded, `next-intl` routing live for six locales,
`dir` switching working, `.env.example` on both sides. Semantic light/dark tokens in place with
`next-themes` and the three-state toggle, no flash of wrong theme on load.
Prove it: `/en` and `/ar` render a styled placeholder with correct direction, in both modes;
`/admin` shows the Unfold theme.
**→ CHECKPOINT. Show me the admin, both locales, and both modes.**

### Phase 1 — Core backend and i18n
`core` and `services` apps, abstracts, `django-modeltranslation` wired, Unfold admin with six language
tabs and service-grouped sidebar, `SiteSettings` populated with the real company facts from `CLAUDE.md`.
**→ CHECKPOINT. I want to click through the admin before you build on it.**

### Phase 2 — Service content, products, video, portfolio, blog, CRM
All remaining apps and models, admin classes, inlines, proxy models for per-service case studies,
dashboard widgets, lead model with email alerting. Includes the `products` app, the shared `Video`
model, and HTML sanitisation on every rich-text field.
**→ CHECKPOINT.**

### Phase 3 — Translation pipeline
`apps.translations`, Groq client, admin bulk action, translation log, status badges, retry and logging.
Test on real records in all five non-English locales, including Arabic and Chinese, and show me output
quality before I commit to it.
**→ CHECKPOINT.**

### Phase 4 — API and seed data
Every endpoint above, English-fallback serializers, throttling, Turnstile verification,
`seed_demo` management command with obviously-placeholder content (never fake client names).
**→ CHECKPOINT.**

### Phase 5 — Frontend shell
Layout, header with services mega-menu, footer, language switcher, design tokens, UI primitives,
`lib/api.ts`, RTL verified. No page content yet.
**→ CHECKPOINT. Screenshots in `en` and `ar`, light and dark — four images.**

### Phase 6 — Pages
Home, the six service pages from one shared template, `/work`, `/work/[slug]`, `/blog`,
`/blog/[slug]`, `/about`, `/contact`. ISR with revalidation webhook from Django.
**→ CHECKPOINT.**

### Phase 7 — SEO and performance
Metadata and `hreflang` on every route, JSON-LD, sitemap, `robots.txt`, GA4, image optimisation,
Lighthouse pass, accessibility pass, all six locales checked.
**→ FINAL REPORT.**

---

## Acceptance criteria

- A visitor lands on any service page and can tell within five seconds what Automex does for them
  and how to ask for it.
- Every public page returns complete, correct HTML with JavaScript disabled.
- All six locales render, Arabic mirrors correctly, no font substitution.
- Light and dark modes both pass: no unreadable text, no inverted screenshots, no flash of the wrong
  theme on first paint, and contrast checked on every accent and link.
- A non-developer can add a campaign, a case study, and a blog post, machine-translate them, review,
  and publish — without touching code.
- A submitted quote request appears in the admin within seconds, tagged with service, locale, and page.
- Lighthouse: Performance and SEO both 95+ on Home and a service page.
- `npm run build` and `python manage.py test` both pass clean.

---

## Open items — ask me, do not guess

- Founded year and team size
- Social profile URLs
- Real case study content (clients, metrics, screenshots) — placeholders until I supply them
- Logo files — design a wordmark as a placeholder and show me options
- Certifications and compliance standards Automex actually holds
- Whether the Afghanistan phone number should be public on the site or internal only
- Whether **Products** belongs in the top navigation bar. Right now it sits in the mega-menu, the
  Home page, and the footer. Putting it in the bar makes ten top-level items, which is the
  findability problem the redesign exists to fix. Recommend leaving it out — confirm either way.
- Video hosting: YouTube (best for SEO and free bandwidth) vs Vimeo (no branding, no suggested
  videos) vs self-hosted. Default is YouTube unless you say otherwise.

---

## Start here

Confirm you have read `CLAUDE.md`. Summarise the architecture back to me in your own words, list any
disagreements you have with the design above, then begin **Phase 0 only**.