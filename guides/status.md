# Project Status & Progress Summary

This document tracks progress of the ISWMC AI Dashboard across working sessions with the AI assistant.

**Last Updated:** 2025-09-16

## Phase 1: Project Setup & Configuration (Complete)

We have successfully completed the initial setup and configuration of the project. This was a critical phase that involved resolving several dependency and versioning conflicts to ensure a stable development environment.

### Key Milestones Achieved:

1.  **Project Initialization:**
    -   Initialized a Django project (`iswmc_dashboard`) and a core application (`dashboard`).
    -   Established a clean and logical folder structure.

2.  **Dependency Management:**
    -   Resolved version conflicts between `django` and `djongo` by pinning specific, compatible versions (`django==3.2.25`, `djongo==1.3.6`) in `requirements.txt`.
    -   Identified and added necessary sub-dependencies (`pytz`, `sqlparse`).

3.  **Database Integration:**
    -   Successfully configured the Django project to connect to the MongoDB Atlas database using `djongo`.
    -   Implemented Django models (`Lorry`, `Transaction`) that map to the existing MongoDB collections.

4.  **Frontend & Styling Setup:**
    -   Integrated `django-tailwind` for modern, utility-first CSS.
    -   Created a dedicated `theme` app to manage frontend assets.
    -   Resolved `npm` and `tailwind` configuration issues by creating and correctly placing `package.json` and `tailwind.config.js`.

## Current Status:

The project is now a **functional MVP**. We have a running Django server that:
- Connects to the live MongoDB database.
- Fetches real transaction data.
- Renders the data in a styled HTML template using TailwindCSS.

The foundation is solid, and we are ready to build the interactive and AI-powered features.

## Phase 2: MVP Dashboard Iteration & Debugging (2025-09-15)

- Fixed template syntax error in `iswmc_dashboard/settings.py` and created `templates/dashboard/index.html`.
- Implemented aggregation views with HTMX partial updates and Tailwind UI polish.
- Added Chart.js bar chart for total waste by lorry type; updates with period changes.
- Added DRF endpoints: `/api/lorries/`, `/api/transactions/`, `/api/aggregated/`.
- Added dashboard chat box and backend endpoint; `dashboard/gemini.py` contains a placeholder, ready for Vertex AI wiring.
- Mapped existing Atlas collections:
  - `deliveries` -> `Transaction` (fields: `Transaction_ID`, `LORRY_ID`, `WEIGHT`, `DELIVERY_TIME` as string)
  - `lorries` -> `Lorry` (fields: `LORRY_ID`, `TYPES_ID`, `CLIENT_ID`, `MAKE_ID`)
- Removed `ForeignKey` to lorry; join performed in Python using `lorry_id`.
- Replaced ORM date truncation with Python-side aggregation for Djongo compatibility.
- Constrained the dashboard to a fixed trial window (UTC): 2025-01-01 to 2025-01-31.
- Implemented robust timestamp parsing for ISO 8601 strings with milliseconds and timezone offsets (e.g., `2025-01-01T08:16:00.000+00:00`).
- Updated README with setup steps, `.env` variables, endpoint list, and trial window.

### Outstanding / Next Session
- Verify Atlas connection via `.env` (`MONGO_DB_URL`, `MONGO_DB_NAME`) to ensure the app reads real data.
- If counts are still zero, confirm database name and credentials; validate sample document types.
- Wire up real Gemini API call with service account and `google-cloud-aiplatform`.
- Optional: add a "Trial Period" option in the UI period selector and show min/max detected timestamps for quick diagnostics.

## Phase 3: Data plumbing and UI fixes (2025-09-16)

- Removed nonexistent FK usage; `TransactionViewSet` no longer uses `select_related('lorry')`.
- Enriched latest transactions in the view with `lorry_types_id` via in-memory lookup.
- `TransactionSerializer` exposes computed `lorry_types_id`.
- Hardened `parse_delivery_time` to handle datetimes, `{'$date': ...}`, and epoch values.
- Replaced template references to `transaction.lorry.*` with enriched fields.

## Phase 4: Charts, HTMX behavior, and period windows (2025-09-16)

- Introduced KPI cards (Total Monthly Deliveries, Total Monthly Weight Kg/Tons, Unique Lorries).
- Added HTMX loading indicator and converted Latest Transactions to a table.
- Moved chart rendering to the base page; re-renders on `htmx:afterSwap/afterSettle`.
- Persisted selected period in the URL; ensured direct hits to `/aggregated-table/` redirect to `/?period=...`.
- Implemented fixed MVP clock: NOW = 2025-01-25 16:00 UTC; hourly shows today only; other periods are month-to-date.

## Phase 5: UX polish and numeric formatting (2025-09-16)

- Added thousands separators via `django.contrib.humanize` for KPIs and table values; Chart.js ticks use `toLocaleString`.
- Adjusted chart data:
  - Chart 1: totals grouped by period
  - Chart 2: totals grouped by lorry type
  - Chart 3: composition doughnut derived from total weight (Leachate 9%, Recyclecables 11%, Organic 45%, Inorganic 20%, Others 15%)
- Added blue banding for the Transaction View with stronger group borders.

## Phase 6: Chrome sidebar and logos (2025-09-16)

- Added fixed top-right Date & Time card; set from MVP NOW.
- Added vertical logos card under Date & Time (MBSP=Client, GSSB=Operator).
- Wired static serving for logos from `guides/assets` and project `static/`.
- Template now references `{% static 'mbsp.png' %}` and `{% static 'gssb.png' %}` which are backed by `guides/assets` via `STATICFILES_DIRS`.

## Known issues / follow-ups

- Migrations for Django admin/auth are not applied; not needed for dashboard, but required if admin is used.
- Composition chart uses fixed proportions; consider wiring to real composition data when available.
- Consider caching lookups for `lorry_types_id` for larger datasets.
