# PIVOTAL POINT — Stable MVP Snapshot

Date: 2025-09-16

This document records the current stable, working state of the ISWMC Dashboard so we can quickly return to it if needed.

## What Works

- Fixed data window: 2025-01-01 — 2025-01-31 (UTC); fixed "today" as 2025-01-25 16:00 UTC.
- Periods: Hourly, Daily, Weekly, Monthly — HTMX updates the partial and the URL, and direct access to the partial redirects to the full page.
- Charts (Chart.js):
  - Aggregated Waste by Weight (grouped by the selected period)
  - Aggregated Waste by By Composition (derived from total weight: 9/11/45/20/15)
  - Aggregated Waste by Lorry Type (grouped by type within the current window)
- KPIs (month-to-date): Total Deliveries, Total Weight (Kg/Tons), Unique Lorries; numbers use thousands separators.
- Transaction table: alternates blue banding by period group, with a strong group top border.
- Logos panel under Date & Time (top-right): MBSP (Client) above GSSB (Operator).

## Key Code/Config

- Settings
  - `iswmc_dashboard/settings.py`
    - `DEBUG=True` (dev)
    - `django.contrib.humanize` enabled
    - `STATICFILES_DIRS = [ BASE_DIR/'static', BASE_DIR/'guides'/'assets' ]`

- Views & logic
  - `dashboard/views.py`
    - `NOW` fixed to 2025‑01‑25 16:00 UTC; `TRIAL_START/END` Jan 2025
    - `get_window(period)` determines date bounds by period
    - Robust `parse_delivery_time` handles datetime, `{'$date': ...}`, epoch, ISO strings
    - Enriched latest transactions with `lorry_types_id` via lookup
    - HTMX partial (`aggregated_table`) sets `HX-Push-Url` and redirects to `/?period=...` on non-HTMX
    - Adds `band`/`group_border` flags for table zebra banding

- API & serializers
  - `dashboard/serializers.py` → `TransactionSerializer` exposes computed `lorry_types_id`
  - DRF routes: `/api/lorries/`, `/api/transactions/`, `/api/aggregated/`

- Templates
  - `templates/dashboard/index.html`
    - Date & Time card (fixed, top-right)
    - Logos panel (uses `{% static 'mbsp.png' %}` and `{% static 'gssb.png' %}`)
    - KPI cards with `intcomma`
    - Global chart renderer re-draws after HTMX swaps
  - `templates/dashboard/_aggregated_table.html`
    - Embeds aggregated data JSON in `#agg-data`
    - Three chart sections (Weight, Composition, Lorry Type)
    - Transaction table with blue banding and formatted numbers

- Static assets (development)
  - Logos are served from `guides/assets` via static:
    - `guides/assets/mbsp.png` → `http://127.0.0.1:8000/static/mbsp.png`
    - `guides/assets/gssb.png` → `http://127.0.0.1:8000/static/gssb.png`
  - Alternative (also wired): put files in `static/img/mbsp.png`, `static/img/gssb.png`

## Environment

- `.env` expects (example):
  - `MONGO_DB_URL="mongodb+srv://<user>:<pass>@<cluster>/"`
  - `MONGO_DB_NAME="mongodb_iswmc"`
- Dependencies (see `requirements.txt`):
  - `django==3.2.25`, `djongo==1.3.6`, `pymongo==3.12.3`, `djangorestframework`, `python-dotenv`, `django-tailwind`

## Known Benign Warnings

- Favicon 404 in dev is expected.
- urllib3 LibreSSL warning on macOS is cosmetic.
- Django admin/auth migrations are unapplied (dashboard does not require them).

## How To Tag/Restore This State

Using git (recommended):

1) Stage and commit everything

```
git add -A
git commit -m "Pivotal Point: stable MVP UI + charts + logos (2025-09-16)"
```

2) Create a tag

```
git tag pivotal-2025-09-16
```

3) Restore later

```
git checkout pivotal-2025-09-16
# or enforce: git reset --hard pivotal-2025-09-16
```

Without git (archive):

- Create an archive (exclude `venv/` if desired):

```
tar --exclude=venv -czf pivotal-2025-09-16.tgz .
```

- To restore, unpack over the workspace and ensure `.env` and logos are present.

## Quick Verification Checklist

- Open `/` with `?period=hourly|daily|weekly|monthly` and see charts update
- Confirm URL persists period and partial URL redirects back to `/`
- Verify logos load via `/static/mbsp.png` and `/static/gssb.png`
- KPIs show month-to-date; numbers have commas
- Transaction table shows blue banding per period group

