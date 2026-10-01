# Phase 1 review checkpoint

October 1, 2026. Phase 2 has not started. The user's modified CLAUDE.md and
BUILD_PROMPT.md are preserved.

## Delivered

- Six-language main and inline admin forms, English required for required prose,
  Arabic RTL fields, and English fallback for empty translations.
- Unfold's bundled WYSIWYG for service bodies and FAQ answers. FAQ controls are
  restricted; server sanitisation remains authoritative for every locale.
- Six service sidebar groups linking to the existing overview, offerings,
  process and FAQ screens. Distinct service models arrive in Phase 2.
- Publication queries reject machine translations. Services now use draft/
  published status plus the active switch. English-only published records remain
  eligible; machine translations require review. Existing services migrate as drafts.
- Correct badge colours, editable SiteSettings review status, and deterministic
  team/stat ordering. Two new migrations were applied locally.
- Blueprint semantic tokens, light/dark/system selection, persisted preferences,
  print tokens, and localized theme labels. `next-themes` is required by the revised
  specification and supplies the pre-content theme script. The unapproved tagline
  was removed. Placeholder metadata now includes description, canonical and alternates.

## Validation

- 82 Django tests passed, including real admin POSTs for translated inline content,
  rich-text sanitisation, English validation, publication gates and service filters.
- Ruff lint and format checks passed; production Django deployment checks passed.
- Migrations applied successfully; migration drift check reports no changes.
- Frontend lint, TypeScript and production build passed; six locales are prerendered.
- npm installation audit reported zero vulnerabilities.
- Static HTML checked across all six locales: one h1, correct language/direction,
  theme bootstrap and three-state selector.
- Browser: English/Arabic light and dark rendering, reload persistence and system
  selection verified. Admin Arabic input direction, dynamic FAQ language tabs,
  restricted toolbar and hidden-input binding verified. No captured browser errors.
- New browser test content was left unsaved and discarded by reload; no demo
  content was added to the working database.
- Dark muted text on a raised surface is only 3.52:1 with the supplied palette;
  card labels therefore use the stronger supporting-text token. The palette is unchanged.

Limitations: the in-app browser's mobile viewport override did not take effect,
so a fresh 390px visual check remains for manual review. The frontend is still a
scaffold, and the API is still a stub. Full page SEO/JSON-LD, production pages,
translation automation and content endpoints belong to later phases. No Lighthouse
or complete site accessibility pass is claimed at this checkpoint.

## Run locally

PostgreSQL must be running. Existing local environment files and dependencies
were used; do not replace them with example files.

Terminal 1:

```bash
cd "/Users/admin/Documents/Projects/Automation Excellence/backend"
source .venv/bin/activate
python manage.py migrate
python manage.py runserver 8000
```

Terminal 2:

```bash
cd "/Users/admin/Documents/Projects/Automation Excellence/frontend"
npm run dev
```

Open http://127.0.0.1:8000/admin/ and sign in with your existing local admin.
Open http://localhost:3000/en and http://localhost:3000/ar for the scaffold.
Stop each process with Ctrl+C when finished. Verification servers were stopped
before handoff.

## Manual review

1. Open Site settings. Check company facts and all six language tabs. Unsupplied
   facts remain empty; Afghanistan phone visibility remains off pending a decision.
2. Open Cyber Security. Inspect all language tabs and Arabic editor direction.
3. Add an offering, process step or FAQ. Check that each inline has independent
   language tabs and that English required fields cannot be left blank.
4. Enter formatted text in the service body and a FAQ answer. Save and reload;
   confirm that only the permitted formatting remains.
5. Follow each service sidebar group and verify its filtered content lists.
6. Review draft/published and machine/reviewed controls. Actual public API delivery
   will be tested when the endpoints are built in Phase 4.
7. Check English/Arabic in light, dark and system modes; reload to confirm the
   selection persists. Resize your browser to a phone width for the outstanding
   mobile visual check.

After user approval, proceed to Phase 2 only.
