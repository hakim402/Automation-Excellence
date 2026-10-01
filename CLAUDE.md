# CLAUDE.md — Automex

Rules for any agent working in this repository. Read fully before the first edit of a session.

---

## 1. What this is

Automex is a technology services company (Kent, WA — Seattle metro) selling six services worldwide:
Digital Marketing · AI & Automation · Custom Software & Database Systems · Web App Development ·
Mobile App Development · Cyber Security.

This repo is the company's public website and its content/lead backend.

**The problem being solved:** the previous site was too complex and visitors could not find what they
needed. Every decision in this repo is judged against *"does this make it faster for a visitor to
understand what Automex does and request it?"* When a feature adds cleverness but costs clarity, cut it.

**Primary business goal:** organic search traffic in six languages → qualified quote requests.
SEO is not a polish phase. It is a build constraint.

---

## 2. Repository layout

```
automex/
├── CLAUDE.md              ← this file
├── backend/               Django 5 + DRF. Content, i18n, admin, leads.
│   ├── manage.py
│   ├── .env               never committed
│   ├── .env.example       committed, every key present with a dummy value
│   ├── requirements.txt
│   ├── config/            settings/, urls.py, wsgi.py
│   ├── apps/              all Django apps live here
│   ├── media/             user uploads (gitignored)
│   └── static/
└── frontend/              Next.js 15 App Router + Tailwind. Public site only.
    ├── .env.local         never committed
    ├── .env.example
    ├── src/app/[locale]/
    ├── src/components/
    ├── src/lib/
    ├── src/styles/
    └── messages/          UI string JSON per locale
```

The backend never renders public HTML. The frontend never talks to the database.
The only contact surface is the versioned REST API at `/api/v1/`.

---

## 3. Commands

**Backend** (run from `backend/`, venv active):
```bash
source .venv/bin/activate
python manage.py runserver 8000
python manage.py makemigrations && python manage.py migrate
python manage.py createsuperuser
python manage.py seed_demo          # idempotent demo content
python manage.py test
ruff check . && ruff format .
```

**Frontend** (run from `frontend/`):
```bash
npm run dev          # localhost:3000
npm run build        # must pass before any task is called done
npm run lint
npm run typecheck
```

Never start a server to "check if it works" and leave it running. Build, verify, stop.

---

## 4. Non-negotiables

1. **No secrets in code.** Every key, URL, and credential comes from environment variables.
   Adding a new variable means adding it to `.env.example` in the same commit.
2. **No public page fetches data in the browser.** All SEO-relevant content is fetched server-side
   (RSC / `generateStaticParams`). A `useEffect` that loads page content is a bug — crawlers see an
   empty page. Client fetching is allowed only for the contact form POST and non-indexed widgets.
3. **Every public route ships complete metadata**: localized `<title>`, meta description,
   canonical URL, `hreflang` alternates for all six locales plus `x-default`, Open Graph, and JSON-LD.
   A page without these is not finished.
4. **English is the source of truth.** Other locales fall back to English when empty. A missing
   translation degrades; it never 404s and never renders blank.
5. **RTL is a first-class layout, not a stylesheet patch.** See §7.
6. **Never bypass the publish gate.** Draft and machine-translated content must not reach the public API.
7. **Migrations are committed** alongside the model change that caused them. Never edit an applied migration.
8. **Do not add a dependency** without stating why in the commit message. Prefer the framework's
   own solution over a package.

---

## 5. Backend conventions

### App structure
Every app under `backend/apps/` follows:
```
apps/<app>/
├── models.py
├── admin.py
├── serializers.py
├── views.py
├── urls.py
├── translation.py     # modeltranslation registration
└── migrations/
```
Apps are registered as `apps.<name>` in `INSTALLED_APPS`.

### Models
- Inherit the shared abstracts from `apps.core.models`:
  `TimeStamped` (created_at, updated_at), `Publishable` (status, published_at, translation_status),
  `SEOFields` (meta_title, meta_description, og_image, noindex).
- Every user-visible model has a `slug` (English, stable, unique) and an `order` integer where display
  sequence matters.
- Default manager returns everything; `objects.published()` returns only `status=PUBLISHED`.
  **API views use `.published()` without exception.**
- Field names are business language, not database language: `client_name`, not `cust_nm`.
- `__str__` returns something a non-technical admin user recognizes.

### Translatable fields
- Handled by `django-modeltranslation`. Register in the app's `translation.py`.
- Translate human prose only: titles, descriptions, body, CTA labels, meta fields.
  **Never translate** slugs, enum keys, tech stack names, client names, URLs, or numbers.
- Adding a translated field means running `makemigrations` — it creates six columns.

### Rich text — allowed, but restricted
Rich HTML is permitted **only on long-form body fields**, listed explicitly in `BUILD_PROMPT.md`.
Short fields — titles, taglines, card descriptions, offering blurbs, metric labels, FAQ questions —
stay plain text. A rich-text card description will break the grid the first time someone pastes
from Word.

Rules:
- Editor is Unfold's built-in WYSIWYG. Do not add a second editor package.
- **Sanitise on save** with an allowlist: `p, h2, h3, h4, ul, ol, li, strong, em, a, blockquote,
  code, pre, br, hr, table, thead, tbody, tr, th, td, img, figure, figcaption`.
  Strip everything else, including `style`, `class`, `script`, and inline event attributes.
- `a` tags keep only `href`, `title`, `target`, `rel`. External links get `rel="noopener noreferrer"`.
- The Groq translation prompt must be told to preserve HTML tags and attributes exactly and translate
  only the text between them. Verify tag counts match before saving a translation.
- Frontend renders it inside a single scoped `.prose` container styled from the design tokens.
  Never `dangerouslySetInnerHTML` on anything that has not passed the backend sanitiser.

### Video
One reusable `Video` model in `core`, attached by nullable foreign key to a service, product, or
case study. **No generic relations** — explicit nullable FKs are simpler to read and to filter in admin.
Every video records its `orientation` (landscape or portrait), because the frontend treats them
differently: landscape is a 16:9 inline player, portrait is a 9:16 reel shown in a horizontal strip.
Prefer external hosting (YouTube/Vimeo) over self-hosted files; a VPS serving video will hurt LCP.

### Admin (django-unfold)
- `unfold` and its `contrib` apps are listed **before** `django.contrib.admin` in `INSTALLED_APPS`.
- Admin classes extend `unfold.admin.ModelAdmin` (never `django.contrib.admin.ModelAdmin`),
  and combine with modeltranslation's tabbed admin so the six languages appear as tabs on one form.
- Inlines extend Unfold's inline classes so they keep the theme.
- **Admin UI is English only.** Do not localize admin labels.
- Sidebar navigation is configured in the `UNFOLD` settings dict and grouped **by service**, so each
  service reads as its own section. This is the "sidebar navigator per service" requirement —
  it is a navigation config, not six separate admin sites.
- Every list view gets useful `list_display`, `list_filter`, `search_fields`, and a
  translation-status indicator. An admin screen a non-developer cannot operate is not done.
- Rich text uses Unfold's WYSIWYG widget. Do not add a second editor package.

### API (DRF)
- Read endpoints are `ReadOnlyModelViewSet`, public, unauthenticated, cacheable.
- Locale comes from the `?lang=<code>` query parameter. Invalid or missing → `en`.
- Serializers resolve the requested language with English fallback per field.
- Write endpoints exist only in `crm` and are throttled + spam-checked.
- Responses are flat and frontend-shaped. One request should fill one page — prefer a single
  `/services/{slug}/` payload over six round trips.
- Never expose: draft content, admin IDs used as secrets, lead data, internal notes, email addresses
  of staff.

### Translation pipeline (Groq)
- Lives in `apps.translations`. One service class wraps the Groq client; model name and API key are
  env vars (`GROQ_API_KEY`, `GROQ_MODEL`).
- Exposed as an admin action: select rows → *Auto-translate to all languages*.
- It fills **only empty** non-English fields and sets `translation_status = MACHINE`.
- Machine-translated content is still gated by `status`. A human sets `status = PUBLISHED` and
  `translation_status = REVIEWED`. **The agent never auto-publishes machine translations.**
- Calls are batched, retried with backoff, and logged. A failed translation never corrupts existing text.
- Prompt instructs: preserve HTML structure, preserve proper nouns and product names, adapt tone
  rather than translate literally, return only the translated text.

---

## 6. Frontend conventions

- **Next.js App Router, Server Components by default.** Add `"use client"` only for genuine
  interactivity, and push it as far down the tree as possible.
- All routes live under `src/app/[locale]/`. Locales: `en`, `es`, `fr`, `de`, `zh`, `ar`.
- Routing and UI strings use `next-intl`. Page *content* comes from the Django API; `messages/*.json`
  holds only interface strings (nav, buttons, form labels, errors).
- **Slugs stay English across all locales** (`/ar/cyber-security`, not `/ar/الأمن-السيبراني`).
  Deliberate tradeoff: simpler routing and stable links, with `hreflang` doing the SEO work.
- Data access goes through `src/lib/api.ts`. No `fetch` to the backend from inside a component file.
- Rendering: static generation with ISR. Set `revalidate` per route; Django triggers on-demand
  revalidation on publish via a shared-secret webhook.
- Images always use `next/image` with `remotePatterns` pointed at the backend media host.
  Every image needs meaningful localized alt text.
- Component files: one component per file, PascalCase name matching the filename.
  Sections in `components/sections/`, primitives in `components/ui/`.
- No component library ships design decisions for us — tokens in `src/styles/tokens.css` are the
  single source of truth for color, type, and spacing. Tailwind config maps to those tokens.
  A hard-coded hex in a component is a bug.

---

## 7. Internationalization and RTL

- Six locales, equal status: `en`, `es`, `fr`, `de`, `zh`, `ar`.
- `<html lang>` and `<html dir>` are set per locale. `ar` → `dir="rtl"`.
- **Use CSS logical properties everywhere**: `ms-*`/`me-*`, `ps-*`/`pe-*`, `start-*`/`end-*`,
  `text-start`/`text-end`. `ml-4`, `pr-6`, `left-0`, and `text-left` are forbidden in shared components.
- Directional icons (arrows, chevrons, carousel controls) mirror in RTL. Logos, screenshots,
  charts, and numerals do not.
- Load only the font subsets a locale needs. Arabic uses the Arabic family; Chinese uses the SC family.
  Never let a Latin font render Arabic or Chinese.
- Check every layout at `ar` before calling it done. Most RTL bugs are invisible in English.

---

## 8. Design system

Dark-first. The brand reference is precision instrumentation and industrial control panels —
Automex builds systems that run on their own. Calm, dense, engineered. Not a gradient SaaS landing page.

### Brand palette — "Deep Harbor"
This is the official Automex brand palette. It governs the website, decks, posters, social posts,
and print. Do not introduce colours outside it.

```
--ax-petrol:   #0A2830   brand anchor. Dark backgrounds, logo lockup, text on light
--ax-harbor:   #0E4553   raised surfaces, cards, panels, borders
--ax-amber:    #FFB627   signature accent. CTAs, key metrics, highlights
--ax-cyan:     #3FC9CE   secondary accent. Links, data, diagrams, icons
--ax-mist:     #F2F6F6   light background — print, decks, light mode
--ax-slate:    #8FA9AE   secondary text, captions, muted UI
--ax-paper:    #EAF2F2   primary text on dark
```

Semantic: success `#3DBE8B` · warning `#FFB627` (reuses amber) · error `#E5484D` · info `#3FC9CE`.

**Usage ratio:** petrol ~55%, mist ~25%, cyan ~12%, amber ~8%. Amber is the loudest element on any
surface and must stay rare — more than a handful of amber elements on a page means the hierarchy failed.

**Contrast rules, non-negotiable:**
- Amber never carries text on white or mist — it fails AA. Amber is always a *fill*, with petrol text on it.
- Cyan is for links and data on dark only; on mist use petrol.
- Body text is `--ax-paper` on dark, `--ax-petrol` on mist.

**Marketing gradient** (decks, posters only, never UI chrome): `#0A2830 → #0E4553`, with amber as the
only warm note. No gradients in the product UI.

**Type**
- Display: **Archivo** (industrial American grotesque). Headlines, service names, numbers.
- Body: **Inter**. All running text and UI.
- Technical: **IBM Plex Mono** — restricted to real technical data (tech stacks, metrics, code).
  Never as a decorative label.
- Arabic: **IBM Plex Sans Arabic**. Chinese: **Noto Sans SC**.
- Body line length under 75 characters. Sentence case everywhere — no tracked-out all-caps eyebrows.

**Layout**
- Service pages use a persistent left rail (sticky, scroll-spy anchors) beside the content column.
  This is the direct answer to "customers can't find what they're looking for" and it mirrors the
  admin's per-service structure.
- Content is left-aligned (start-aligned). Centered text only in the hero and section intros.
- Spacing scale is 4px-based; section rhythm comes from a small set of vertical steps, not ad-hoc values.

**Motion**
- One orchestrated moment per page, at most. Fade-and-slide on every section is forbidden.
- Motion that responds to a user action (opening, expanding, confirming) is welcome.
- `prefers-reduced-motion` is respected everywhere.

**Avoid** (these read as templated): identical rounded cards for all content regardless of hierarchy,
the same soft grey shadow on everything, `01 / 02 / 03` markers on content that is not a sequence,
`→` appended to link text, gradient washes as decoration, one word of a headline in a different color.

---

## 9. SEO requirements

Treat these as acceptance criteria, not suggestions.

- Server-rendered HTML contains the full page content before any JavaScript runs.
- One `<h1>` per page; heading levels descend without skipping.
- `hreflang` alternates for all six locales plus `x-default` on every page.
- Canonical URL is absolute and self-referencing per locale.
- JSON-LD: `Organization` + `LocalBusiness` sitewide; `Service` on service pages;
  `BlogPosting` on posts; `BreadcrumbList` on nested routes; `FAQPage` where FAQs exist.
- `sitemap.xml` is generated from the API, includes every locale variant, and updates on publish.
- `robots.txt` allows crawling and points to the sitemap.
- Core Web Vitals: LCP under 2.5s, CLS under 0.1. Reserve image dimensions. No layout-shifting fonts
  (use `font-display: swap` with correct fallback metrics).
- Internal linking: every service page links to related case studies and relevant blog posts.
- Analytics loads via `next/script` with `strategy="afterInteractive"` and never blocks render.

---

## 10. Security and data handling

- Leads contain personal data. Never log full lead payloads. Never expose leads through a GET endpoint.
- Contact form: Cloudflare Turnstile verified **server-side** in Django, plus a honeypot field,
  plus DRF rate throttling per IP.
- CORS allows only the frontend origin, from an env var. Never `CORS_ALLOW_ALL_ORIGINS = True`.
- `DEBUG = False` and a real `ALLOWED_HOSTS` in the production settings module.
- Uploaded files are validated by type and size. Never trust a client-supplied filename.
- The revalidation webhook is authenticated with a shared secret.
- This is a cyber security vendor's own website. A vulnerability here is a sales problem, not just a bug.

---

## 11. Working style for agents

- **Read before writing.** Inspect existing models, tokens, and components before adding new ones.
  Duplicate patterns are worse than imperfect reuse.
- **Work in the phase order** given in `BUILD_PROMPT.md`. Stop at each checkpoint and report.
- **Small, coherent commits** with messages saying what changed and why.
- **Never invent business facts.** Client names, metrics, certifications, and testimonials come from
  the user. Seed data must be obviously placeholder, never a fabricated real client.
- **State assumptions out loud.** If the spec is silent, choose the simpler option, implement it,
  and say what you chose in your report.
- **A task is done when:** `npm run build` passes, `python manage.py test` passes, the admin screen is
  operable by a non-developer, the page renders correctly in `en` and `ar`, and metadata is present.

### Company facts (use these, do not invent alternatives)
```
Legal/brand name   Automex
Address            827 W Valley Hwy, Trlr #57, Kent, WA 98032, United States
US phone           +1 (206) 470-9284
AF phone           +93 776 320 765
Email              info@automex.tech
Domain             https://automex.tech
Service area       Worldwide
```
Founded year, team size, social profile URLs, and real client details are **not yet supplied**.
Leave them as clearly-marked placeholders in `SiteSettings` and ask rather than guess.