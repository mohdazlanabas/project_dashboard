# AI Dashboard for Integrated Solid Waste Management Center (ISWMC)

This project is an AI-powered dashboard for an Integrated Solid Waste Management Center (ISWMC). It provides aggregated insights from MongoDB and an AI assistant (Gemini) for natural-language analysis.

## Features

- Period selector (Hourly, Daily, Weekly, Monthly) with HTMX partial updates and URL persistence
- Charts (Chart.js):
  - Aggregated Waste by Weight (grouped by selected period)
  - Aggregated Waste by Lorry Type (grouped by type within the current window)
  - Aggregated Waste by Composition (derived from total weight: Leachate 9%, Recyclecables 11%, Organic 45%, Inorganic 20%, Others 15%)
- KPIs for the month-to-date window (Jan 2025): Total Deliveries, Total Weight (Kg/Tons), Unique Lorries
- Transaction view table with thousands separators and alternating period banding
- Robust timestamp parser for `DELIVERY_TIME` (supports datetime objects, dict `$date`, epoch, multiple string formats)
- REST API (DRF): lorries, transactions (with computed `lorry_types_id`), and aggregated data
- AI assistant: “Ask Mamu, Your AI Secret Agent”
  - Local NLQ tools: list/describe collections, totals by period, tables by day/week/month, by lorry type, delivery counts
  - Example question buttons + backend indicator (Local NLQ or Gemini)
  - Vertex AI Gemini scaffold with safe function-calling to local tools (optional)

## Tech Stack

- Backend: Django 3.2, Django REST Framework
- Frontend: HTMX, TailwindCSS, Chart.js
- Database: MongoDB Atlas via Djongo
- AI: Google Cloud Vertex AI (Gemini)

## Local Development Setup

1. Create and activate a virtual environment:
   - `python -m venv venv`
   - `source venv/bin/activate`
2. Install Python dependencies:
   - `pip install -r requirements.txt`
3. Install frontend dependencies:
   - `cd theme/static_src && npm install && cd ../..`
4. Create a `.env` file in the project root and add MongoDB credentials:
   ```
   MONGO_DB_URL="mongodb+srv://<user>:<pass>@<cluster>/"
   MONGO_DB_NAME="mongodb_iswmc"  # exact DB name shown in Atlas
   ```
5. Start the dev servers (in two terminals):
   - Terminal 1: `python manage.py tailwind start`
   - Terminal 2: `python manage.py runserver`

### Static Assets (Logos)

- During development, Django serves static from app folders and `BASE_DIR/static`.
- This project additionally serves `guides/assets` for convenience.
- Place logos at one of the following locations:
  - `guides/assets/mbsp.png` and `guides/assets/gssb.png` (recommended; already wired)
  - or `static/img/mbsp.png` and `static/img/gssb.png`
- Verify in browser:
  - `http://127.0.0.1:8000/static/mbsp.png`
  - `http://127.0.0.1:8000/static/gssb.png`

### AI Assistant

- Local NLQ (default): no cloud required. Supported intents:
  - “List collections”, “Describe deliveries”, “Totals monthly/daily/weekly/hourly”
  - “By lorry type weekly/daily…”, “Daily breakdown”, “How many deliveries weekly”
- Vertex AI (optional): set environment and restart server
  - `GOOGLE_CLOUD_PROJECT=<project>`
  - `GEMINI_LOCATION=us-central1` (or region)
  - `GOOGLE_APPLICATION_CREDENTIALS=/absolute/path/to/service_account.json`
  - The assistant auto-detects Gemini and displays “AI backend: Gemini”.

## Data Assumptions & Trial Window

- The dashboard reads from existing Atlas collections:
  - `deliveries` (transactions)
  - `lorries` (lorry metadata)
- Field mappings:
  - deliveries: `Transaction_ID` (string UUID), `LORRY_ID` (string), `WEIGHT` (number), `DELIVERY_TIME` (string ISO8601, e.g. `2025-01-01T08:16:00.000+00:00`)
  - lorries: `LORRY_ID`, `TYPES_ID`, `CLIENT_ID`, `MAKE_ID`
- The UI constrains data to a fixed trial window: 2025-01-01 — 2025-01-31 (UTC).
- A fixed "today" of 2025-01-25 16:00 UTC is used for MVP:
  - Hourly view: shows 2025-01-25 00:00 → 16:00 only
  - Daily/Weekly/Monthly: month-to-date (Jan 1 → Jan 25, capped at Jan 31)

## Layout Notes

- The Date & Time card and Logos panel track the right edge of the dashboard card so they remain visually adjacent on narrower screens.

## Endpoints

- UI: `/`
- HTMX partial: `/aggregated-table/?period=daily|hourly|weekly|monthly`
  - If opened directly (non-HTMX), it redirects to `/?period=...` to ensure full layout/scripts.
- API:
  - `/api/lorries/`
  - `/api/transactions/`
  - `/api/aggregated/?period=daily|hourly|weekly|monthly`

## AI Assistant (Gemini)

- Basic chat box on the dashboard posts to `/chat/`
- Placeholder implementation in `dashboard/gemini.py`
- To enable real responses, set:
  ```
  GOOGLE_APPLICATION_CREDENTIALS=/absolute/path/to/vertex_key.json
  GOOGLE_CLOUD_PROJECT=<your-gcp-project-id>
  GEMINI_LOCATION=us-central1
  ```
  and implement the call in `ask_gemini()` using `google-cloud-aiplatform`.

## Notes

- If no data appears, verify Atlas credentials in `.env` and confirm the database name matches Atlas exactly.
- Timestamps are parsed and normalized to aware UTC datetimes; non-string values are handled.
- Admin UI has been disabled to keep the footprint small and avoid extra migrations. If you need it later, re‑enable `django.contrib.admin` in `INSTALLED_APPS`, add the admin URL back, and run `python manage.py migrate admin`.

### Migrations (clearing the startup warning)

- With admin disabled, apply only the core apps:
  - `python manage.py migrate contenttypes`
  - `python manage.py migrate auth`
  - `python manage.py migrate sessions`
- If a collection already exists, use `--fake-initial` for that app.

### Developer Tips

- The charts are rendered from data embedded in the partial as JSON (`#agg-data`) and drawn in the base page after HTMX swaps (`htmx:afterSwap/afterSettle`).
- To avoid landing on the partial URL after period change, responses set `HX-Push-Url` to the root with `?period=...`.
- Transaction API returns a computed `lorry_types_id` to avoid Djongo FK issues.
