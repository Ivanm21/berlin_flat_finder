# Flat Finder POC – AI Assistant Prompt Library

Use these atomic prompts in GitHub Copilot or Cursor to implement the Supabase-backed POC step by step.

---

## Initial Project Setup

**Prompt: Monorepo Scaffolding**
> Create a monorepo with `backend/` and `frontend/` folders. In `backend/`, initialize Poetry targeting Python 3.11 with dependencies `requests`, `beautifulsoup4`, `aiohttp`, `selenium`, `playwright`, `pydantic`, `supabase`, `python-dotenv`, `httpx`. In `frontend/`, bootstrap a Next.js 14 app (TypeScript, App Router) with Tailwind CSS and Supabase client libraries. Add a root `README.md` describing repo structure and setup steps.

**Prompt: Supabase Environment Setup**
> Under `infra/`, add instructions in `SUPABASE_SETUP.md` for creating a Supabase project, enabling email/password auth, configuring Row Level Security, and generating service role/key files. Include SQL snippets for initial tables `users`, `user_preferences`, `listings`, `applications`, `application_events`.

---

## Backend – Phase 1 Global Listing Monitoring

**Prompt: Backend Environment Config**
> In `backend/src/config.py`, load environment variables (Supabase URL/key, proxy list, polling intervals) via `python-dotenv`. Provide typed accessors with sensible defaults for local development.

**Prompt: Supabase Client Wrapper**
> Implement `backend/src/db/supabase_client.py` exposing an async-friendly wrapper around Supabase REST (using `httpx.AsyncClient`). Include helper methods `upsert_listing`, `record_seen_listing`, and `fetch_active_preferences`.

**Prompt: Session Manager**
> Inside `backend/src/monitoring/session_manager.py`, implement a `SessionManager` managing HTTP sessions with rotating headers, optional proxies, adaptive backoff, and retry logic for 403/429 responses.

**Prompt: HTML Fetcher**
> Create `backend/src/monitoring/html_fetcher.py` with async function `fetch_search_page(url, session_manager)` that downloads ImmobilienScout24 pages, handles gzip/deflate, retries on transient failures, and returns raw HTML.

**Prompt: Listing Parser**
> Add `backend/src/monitoring/listing_parser.py` parsing HTML into `ListingSummary` pydantic models (fields: `external_id`, `title`, `price_eur`, `rooms`, `size_sqm`, `district`, `detail_url`, `first_seen_at`).

**Prompt: Change Detector**
> Implement `backend/src/monitoring/change_detector.py` maintaining a local cache plus Supabase `seen_listings` table. Provide `async filter_new_listings(listings)` that returns unseen items and persists state.

**Prompt: Global Monitor Orchestrator**
> Build `backend/src/monitoring/global_monitor.py` exposing `async monitor_all_listings()` that iterates through predefined search endpoints, yields new listings, and logs metrics (latency, success rate).

---

## Backend – Phase 2 Preference Matching & Applications

**Prompt: Preference Models**
> In `backend/src/matching/models.py`, define pydantic models for `UserPreference`, `Listing`, `MatchResult`, enforcing value ranges and optional amenities (pet-friendly, furnished, balcony).

**Prompt: Preference Repository**
> Implement `backend/src/matching/preference_repository.py` fetching active preferences from Supabase, caching them in-memory with TTL, and supporting incremental refresh.

**Prompt: Matching Engine**
> Write `backend/src/matching/engine.py` with function `match_listing_to_users(listing, preferences)` returning ordered matches using weighted scoring (price fit, district priority, rooms/size, amenities).

**Prompt: Application Queue**
> Create `backend/src/applications/queue.py` that records application intents into Supabase `application_jobs` table and logs state transitions.

**Prompt: Notification Stub**
> Add `backend/src/notifications/notifier.py` providing async functions to enqueue email/push notifications (placeholder logging). Structure payloads with listing summary and match score.

**Prompt: Pipeline Runner**
> In `backend/src/main.py`, assemble the monitoring pipeline: start monitor loop, persist listings to Supabase, compute matches, create `user_matches` rows, enqueue notifications, and queue auto-apply jobs when enabled.

---

## Frontend – Supabase Auth & Preference Intake

**Prompt: Supabase Client Setup**
> In `frontend/src/lib/supabaseClient.ts`, initialize Supabase browser/client instances with env variables, including helper for server-side client creation.

**Prompt: Auth Layout**
> Build `frontend/src/app/(auth)/layout.tsx` integrating Supabase Auth UI for sign-up/login with email verification messaging and redirect on success.

**Prompt: Onboarding Questionnaire**
> Implement `frontend/src/app/onboarding/page.tsx` rendering a multi-step form (Tailwind + React Hook Form) asking for Berlin districts, price range, property type, rooms, size, pets, auto-apply toggle. On submit, call Supabase RPC or REST to upsert preferences.

**Prompt: Protected Dashboard Layout**
> Create `frontend/src/app/(dashboard)/layout.tsx` that checks Supabase session server-side, redirects unauthenticated users, and provides sidebar navigation (Preferences, Matches, Applications).

**Prompt: Matches Page**
> Add `frontend/src/app/(dashboard)/matches/page.tsx` fetching `user_matches` with listing details and match scores via Supabase, displaying cards with quick actions (view listing, trigger application).

**Prompt: Applications Page**
> Implement `frontend/src/app/(dashboard)/applications/page.tsx` showing timeline of application status from `application_events`, grouped by listing, highlighting pending actions.

**Prompt: Preference Editor**
> Build `frontend/src/app/(dashboard)/preferences/page.tsx` allowing users to edit search criteria, toggle auto-apply thresholds, and persist changes back to Supabase.

---

## Infrastructure & Testing

**Prompt: Supabase SQL Migration**
> Under `infra/sql/`, add `0001_schema.sql` containing final table definitions with RLS policies granting users access to their own rows and service role access for backend ingestion.

**Prompt: Backend Unit Tests**
> Configure `backend/pytest.ini`, add fixtures in `backend/tests/conftest.py` for mocked Supabase client and sample preferences, and write tests for parser, matching engine, and change detector.

**Prompt: Frontend Component Tests**
> Set up Vitest/Testing Library in `frontend/`, add tests for onboarding form validation and dashboard data rendering with mocked Supabase responses.

**Prompt: Development Scripts**
> Provide `scripts/dev_backend.sh` to export env vars and run the backend pipeline locally, plus `scripts/dev_frontend.sh` to launch Next.js with Supabase keys injected.

---

## Operational Tools

**Prompt: Seed Script**
> Create `backend/scripts/seed_supabase.py` that inserts demo users, preferences, and listings via Supabase service key for local testing (mark demo data for cleanup).

**Prompt: Monitoring Smoke Test**
> Add `backend/scripts/run_smoke_monitor.py` executing a single monitor cycle, printing discovered listings, and exiting with status code reflecting success/failure.

**Prompt: Dashboard Demo Data Loader**
> Implement `frontend/scripts/seed_demo_matches.ts` seeding sample matches/applications through Supabase client to showcase UI without running backend.

