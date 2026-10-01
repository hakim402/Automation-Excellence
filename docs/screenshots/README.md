# Checkpoint screenshots

Captured headless at 2x. Regenerate by starting both servers and re-running the capture script
from the phase report.

## Phase 0 — scaffold

| file | what it shows |
|---|---|
| `frontend-en.png` | Placeholder page, English, 1440px |
| `frontend-ar.png` | Same page in Arabic — mirrored layout, RTL |
| `frontend-zh.png` | Same page in Chinese — Noto Sans SC |
| `frontend-en-mobile.png` | English at 390px |
| `frontend-ar-mobile.png` | Arabic at 390px — where RTL bugs actually surface |
| `admin-login.png` | Unfold login, brand palette, light |
| `admin-dashboard-dark.png` | Unfold admin on brand petrol |
| `admin-changelist-dark.png` | A changelist with themed list tooling |

## Phase 1 — core backend and i18n

| file | what it shows |
|---|---|
| `p1-dashboard.png` | Sidebar grouped Site · Services · System |
| `p1-services-list.png` | Six services, translation badges, "how complete is this page" column |
| `p1-site-settings.png` | The singleton, with the real company facts seeded |
| `p1-tabs-english.png` | Six language tabs on one form, English first |
| `p1-tabs-arabic.png` | Arabic tab active, inputs switched to RTL |

## Revised Phase 1 — Blueprint

Fresh browser captures for the revised checkpoint:

- `p1-blueprint-en-light.jpg` and `p1-blueprint-en-dark.jpg`
- `p1-blueprint-ar-light.jpg` and `p1-blueprint-ar-dark.jpg`
- `p1-blueprint-admin-ar.jpg` — Arabic rich-text editor

These use the in-app browser's default viewport. Its 390px override did not
apply correctly; no fresh mobile screenshot is claimed. Earlier PNGs document
the old palette and are retained as historical evidence.

## Phase 2 review

- `phase-2-dashboard-light.png`, `phase-2-dashboard-dark.png`: live local admin dashboard;
  six existing service drafts and empty lead/review queues.
- `phase-2-product-inline-ar-dark.png`: newly added Arabic product-feature inline with unsaved
  test text. The browser sample was discarded; no product was created in the development database.
