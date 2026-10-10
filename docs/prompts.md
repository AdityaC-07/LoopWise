# Implementation Playbook — LoopWise Waste Segregation Intelligence Platform

> **For:** Antigravity IDE agent
> **Before any prompt:** Read `architecture.md`, `design.md`, and this file completely.
> Re-read the relevant sections of `architecture.md` and `design.md` at the start of every prompt.
>
> **Working principles:**
> - Do not mark a prompt complete until its acceptance criteria pass.
> - Do not invent API contracts, data models, or component responsibilities — follow `architecture.md`.
> - Do not deviate from `design.md` — it is a specification, not a suggestion.
> - Do not claim a test passes unless you ran it and pasted the output.
> - Inspect actual repository state and existing cloud resources before creating or modifying files.
> - Local development (Docker Compose) operates offline in Mock Inference mode and MUST NOT create AWS cloud resources.
> - AWS cloud provisioning occurs ONLY in the AWS Deployment stage (Prompts 14–19) and REQUIRES explicit user approval.
> - Every prompt ends with a checkpoint. Do not advance past a failed checkpoint.

---

# Part 1: Local Development & Application Implementation

---

## Prompt 0 — Repository Inspection and Project Setup

**Prerequisites:** None
**Reads:** `architecture.md` (complete), `design.md` (complete), this file (complete)
**Deliverables:** Verified directory structure, `.env.example`, confirmed no conflicting state

---

Read `architecture.md` completely. Then read `design.md` completely. Then read this file completely.

Inspect the repository:
1. List all files and directories at the root.
2. Check for existing `backend/`, `frontend/`, `docker-compose.yml`, `pyproject.toml`, `package.json`, Alembic migrations, and any `.onnx` or model weight files.
3. If model weights exist, note their filename, size, and file extension. Do not open or run them.
4. Report findings as a numbered list before taking any action.

Create the directory structure from `architecture.md` Section 14 if it does not exist. Use empty `__init__.py` files as placeholders — do not write application code yet.

Create `.env.example` with all variables from `architecture.md` Section 16. Values must be blank or clearly marked `# generate with: ...`. Do not commit real credentials.

**Checkpoint:**
- Report the complete directory tree at two levels deep.
- Confirm `.env.example` exists and contains every variable listed in Section 16.
- State explicitly whether any model weight files were found.

---

## Prompt 1 — Dependency and Infrastructure Files

**Prerequisites:** Prompt 0 complete
**Reads:** `architecture.md` Sections 11, 12
**Deliverables:** `pyproject.toml`, `package.json`, `docker-compose.yml` — all parseable and correct

---

Re-read `architecture.md` Sections 11 and 12 before writing any file.

Create `backend/pyproject.toml`:
- Python ≥ 3.12
- Pin exact verified versions for: `fastapi`, `uvicorn[standard]`, `sqlalchemy[asyncio]`, `asyncpg`, `alembic`, `pydantic-settings`, `pydantic[email]`, `celery[redis]`, `redis`, `pillow`, `onnxruntime`, `python-jose[cryptography]`, `httpx`, `pytest`, `pytest-asyncio`, `pytest-cov`
- Include `[tool.pytest.ini_options]` with `asyncio_mode = "auto"`.

Create `frontend/package.json`:
- Node ≥ 22
- Pin exact verified versions for: `react`, `react-dom`, `react-router-dom`, `typescript`, `vite`, `@vitejs/plugin-react`, `tailwindcss`, `postcss`, `autoprefixer`, `recharts`, `@types/react`, `@types/react-dom`, `vitest`, `@testing-library/react`, `@testing-library/user-event`, `uuid`, `@types/uuid`

Create `docker-compose.yml`:
- Services: `api`, `worker`, `db` (`postgres:16-alpine`), `cache` (`redis:7-alpine`), `frontend`
- `api` and `worker` share the same image built from `backend/Dockerfile`
- `worker` overrides the command to run Celery
- `db` and `cache` have named volumes
- `api` depends on `db` and `cache` with health checks
- All services read from a `.env` file
- Frontend service uses `node:22-alpine`, Vite dev server on port 5173
- *Note:* This Docker Compose file is for local development only and must not create cloud resources.

Create `backend/Dockerfile` and `frontend/Dockerfile` (dev-stage only).

**Checkpoint:**
- Run `docker compose config` and paste the output. Must parse without errors.
- Verify all backend packages resolve (dry-run or pip install check).
- State the exact version of every dependency that will be installed.

---

## Prompt 2 — Backend Scaffold and Database Models

**Prerequisites:** Prompt 1 complete
**Reads:** `architecture.md` Sections 5, 8, 16
**Deliverables:** All ORM models, Alembic migration, seed data — verified against schema spec

---

Re-read `architecture.md` Sections 5 and 8 in full before writing any file.

Create `backend/app/core/config.py`:
- `Settings` class using `pydantic-settings`, loading from environment.
- Fields: `DEMO_MODE: bool = True`, `DATABASE_URL: str`, `REDIS_URL: str`, `MODEL_PATH: str | None = None`, `CLASS_INDEX_MAP: str | None = None`, `S3_BUCKET: str | None = None`, `AWS_REGION: str = "ap-south-1"`, `SECRET_KEY: str`, `ENVIRONMENT: Literal["development","staging","production"] = "development"`, `ACCESS_TOKEN_EXPIRE_MINUTES: int = 480`
- Single `get_settings()` function with `lru_cache`.

Create `backend/app/models/database.py`:
- Async SQLAlchemy engine using `asyncpg`.
- `AsyncSessionLocal` factory.
- `Base` declarative base.
- `get_db()` async dependency.

Create ORM models matching `architecture.md` Section 5 exactly:
- `models/events.py` — `ClassificationEvent` with all enums as Python `enum.Enum` AND PostgreSQL enum types. All indexes as specified.
- `models/corrections.py` — `UserCorrection`
- `models/materials.py` — `Material`
- `models/analytics.py` — `WardAnalyticsRollup` with `UniqueConstraint("ward_id", "date")`
- `models/users.py` — `User`

Configure Alembic: reads `DATABASE_URL` from settings; imports all models for autogenerate.
Generate initial migration: `alembic revision --autogenerate -m "initial_schema"`.

Create `backend/app/seeds/materials.py`:
- 25 material entries covering all `MaterialCategory` values.
- Representative of Indian urban waste streams.
- `demo_seed = True` on every row.
- Runnable as `python -m app.seeds.materials`.

**Checkpoint:**
- Run `alembic upgrade head`. Paste complete output.
- Query the database and list all tables with column counts.
- Run the seed script. Confirm 25+ rows. Report any errors.

---

## Prompt 3 — ML Inference Service and Demo Mode

**Prerequisites:** Prompt 2 complete
**Reads:** `architecture.md` Sections 7, 9
**Deliverables:** `inference/` package, unit tests — all passing without model weights

---

Re-read `architecture.md` Sections 7 and 9 before writing any file.

Create `backend/app/services/inference/result.py`:
- `ClassificationResult` dataclass matching the `/classify` 200 response `data` block in Section 6.1.
- Nested: `MaterialGuidance`, `DisposalGuidance`.

Create `backend/app/services/inference/base.py`:
- Abstract `BaseClassifier` with `classify(image_bytes, description)`, `model_version`, `is_demo`.

Create `backend/app/services/inference/mock.py` — `MockClassifier`:
- Pool of 25 items covering all `MaterialCategory` values.
- Each item has predefined confusion-pair alternatives (plausible, not random).
- MD5 hash of input → deterministic result selection.
- Confidence distribution: ~60% high / ~25% medium / ~15% low across the pool.
- `model_version = "mock-v1"`, `is_demo = True`.
- All guidance text uses plain language per `design.md` Section 11. No technical jargon in mock data.

Create `backend/app/services/inference/onnx_classifier.py` — `ONNXClassifier`:
- Load from `MODEL_PATH` at init. Raise `ModelNotFoundError` if absent.
- Log assumption warning at startup: `"⚠ ASSUMPTION: input shape [1,3,640,640] — verify from model metadata"`.
- Preprocessing per `architecture.md` Section 7.2.
- 5-second inference timeout.
- `is_demo = False`.

Create `backend/app/services/inference/factory.py` — `get_classifier()`:
- `DEMO_MODE=true` OR no model file → `MockClassifier()`. Log clearly.
- `DEMO_MODE=false` AND model found → `ONNXClassifier()`. On `ModelNotFoundError`: fall back to mock, set `_FALLBACK_TO_MOCK = True`.

Create `backend/tests/test_inference.py` (7 tests as specified in the original playbook).

**Checkpoint:**
- Run `pytest tests/test_inference.py -v`. All 7 tests must pass. Paste output.
- Demo mode must function with zero model weight files present.

---

## Prompt 4 — API Endpoints: Classify, Feedback, Health

**Prerequisites:** Prompt 3 complete
**Reads:** `architecture.md` Sections 6.1, 6.2, 8
**Deliverables:** All endpoints, integration tests passing

---

Re-read `architecture.md` Sections 6.1, 6.2, and 8 before writing any file.

Create:
- `backend/app/core/response.py` — standard response envelope functions.
- `backend/app/core/errors.py` — `LoopWiseException` hierarchy; FastAPI exception handlers. All user-facing error messages must use plain language from `design.md` Section 11.
- `backend/app/api/schemas/classify.py` — Pydantic v2 models for classify request/response with all validators from Section 6.1.
- `backend/app/api/schemas/feedback.py` — Pydantic v2 models for feedback request/response.
- `backend/app/api/routers/classify.py` — `POST /api/v1/classify` with full privacy enforcement from Section 8.
- `backend/app/api/routers/feedback.py` — `POST /api/v1/feedback` with Redis rate limit (max 10/session/hour).
- `backend/app/api/routers/health.py` — `GET /api/v1/health` checking DB, inference engine, Redis, S3.
- `backend/app/main.py` — FastAPI app, routers, exception handlers, CORS.

Create `backend/tests/test_api.py` (9 integration tests as in the original playbook).

**Checkpoint:**
- Run `pytest tests/test_api.py -v`. All 9 tests must pass. Paste output.
- POST to `/api/v1/classify` manually. Paste the full JSON response.
- Verify the response envelope matches Section 6.1 field-by-field.
- GET `/api/v1/health` — confirm `"inference_engine": "mock"` and `"demo_mode": true`.

---

## Prompt 5 — Analytics Pipeline and Endpoints

**Prerequisites:** Prompt 4 complete
**Reads:** `architecture.md` Sections 6.3, 6.4, 10
**Deliverables:** Aggregator, Celery tasks, analytics endpoints, demo seed data

---

Re-read `architecture.md` Sections 6.3, 6.4, and 10 in full.

Create:
- `backend/app/analytics/aggregator.py` — `compute_ward_rollup(db, ward_id, date)`. Filters `demo_mode=false` events only. Computes all Section 10.2 metrics.
- `backend/app/analytics/tasks.py` — Celery tasks: `aggregate_ward_day` and `nightly_rollup` (Celery Beat, 01:00).
- `backend/app/api/schemas/analytics.py` — `WardAnalyticsResponse`, `OverviewResponse`.
- `backend/app/api/routers/analytics.py` — ward detail, overview, and materials endpoints. Auth stub clearly marked `# TODO: enforce JWT in production`.
- `backend/app/seeds/demo_analytics.py` — 30 days × 3 wards with the narratives from `architecture.md` Section 9 (Ward A: improving trend; Ward B: spike days 14–18; Ward C: consistently good). Realistic day-of-week variation.

Create `backend/tests/test_analytics.py` (5 tests as specified).

**Checkpoint:**
- Run `pytest tests/test_analytics.py -v`. All 5 tests must pass. Paste output.
- Seed demo analytics. GET `/api/v1/analytics/ward/WD-DEMO-B` for 30 days. Paste response.
- Confirm contamination spike is visible on days 14–18 in the timeseries.
- Confirm demo events are excluded from production analytics rollups.

---

## Prompt 6 — Frontend Scaffold and Design System

**Prerequisites:** Prompt 5 complete; `design.md` finalised
**Reads:** `design.md` (complete), `architecture.md` Section 6
**Deliverables:** React scaffold, design tokens, API client, routing, layout shells

---

**Read `design.md` completely before writing a single line of code.**
Every token, font, colour, and component specification in `design.md` must be implemented exactly.

**Fonts (in `index.html` `<head>`, NOT CSS @import):**
```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,600;9..144,700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400&display=swap" rel="stylesheet">
```

**Create `frontend/src/design-system/tokens.css`:**
- Every CSS custom property from `design.md` Sections 2, 3, 4, 5 — exact values, exact names.
- This file is the single source of truth for all colours, fonts, spacing, and radii.
- No hardcoded colour or spacing values anywhere else in the codebase — all values reference these tokens.

**Create `frontend/src/design-system/components/`:**

`Button.tsx` — primary, secondary, ghost, danger variants (Section 6.1). Disabled state (opacity 0.4). Loading state (spinner inside). Min touch target 44×44px. Label always visible — no icon-only.

`Badge.tsx` — material category badge (Section 6.3). Accepts `category: MaterialCategory`. Background and colour from `--color-mat-*` tokens.

`Card.tsx` — surface card (Section 6.2). Optional `interactive` prop for hover state.

`Spinner.tsx` — 3-dot pulse animation in `--color-amber`. Used for loading states.

`ConfidenceBar.tsx` — (Section 6.4). Accepts `score: number`. Displays ONLY the plain-language label ("Very sure" / "Fairly sure" / "Not very sure") — never the numeric score. Animated fill width.

`BinCard.tsx` — (Section 6.5). Accepts `bin: "wet"|"dry"|"hazardous"|"e_waste"|"rejected"`. Uses bin-specific `--color-bin-*` tokens. Shows friendly bin name (not enum value). Sub-label with plain instruction.

`StatusLight.tsx` — (Section 6.7). Accepts `value: number` (contamination_rate). Pulsing animation on "bad" state only.

`RecoveryBar.tsx` — (Section 6.8). Accepts `potential: "high"|"medium"|"low"|"none"`. Plain-language label. No numeric scores.

`DemoModeIndicator.tsx` — (Section 6.6). Renders "Practice Mode — not live data" badge. Fixed position top-right. Visible on all analytics screens. Click opens tooltip.

`SkeletonShimmer.tsx` — chart loading state. Animated shimmer matching `design.md` Section 10 loading spec.

`DataHonestyFootnote.tsx` — the fixed footnote from Section 9.3. Non-removable. Accepts optional custom text.

**Create `frontend/src/api/client.ts`:**
- Base URL from `import.meta.env.VITE_API_BASE_URL`.
- `generateSessionId()`: UUID v4 persisted to `sessionStorage`. Returned on subsequent calls.
- Typed functions: `classify`, `submitFeedback`, `getWardAnalytics`, `getOverview`, `getMaterials`, `getHealth`.
- All requests include `session_id` automatically.
- Errors parsed into typed `APIError` with plain-language message (from `design.md` Section 11 table).

**Create routing in `frontend/src/main.tsx`:**
- `/` → `<ClassificationPage />`
- `/result/:eventId` → `<ResultPage />`
- `/analytics` → `<AnalyticsOverviewPage />`
- `/analytics/ward/:wardId` → `<WardDetailPage />`
- `/help` → `<HelpPage />`

**Create layout components:**

`ResidentLayout.tsx` — mobile-first. TopBar (logo + `DemoModeIndicator`). No sidebar. Bottom tab bar on mobile.

`AnalyticsLayout.tsx` — desktop sidebar (240px, collapsible to 64px per `design.md` Section 7). TopBar. Bottom tab bar on mobile. Sidebar items: Classify Waste, Overview, My Ward, All Wards, Help — with plain-language labels.

Create stub page components (layout + placeholder heading only, no content).

**Checkpoint:**
- Run `npm run dev`. Paste terminal output — zero errors.
- Open each of the 5 routes. Confirm they load without console errors.
- Open browser inspector on any page. Confirm `--color-bg`, `--color-amber`, `--font-display` custom properties are present with correct values.
- Run `npm run build`. Zero TypeScript errors.

---

## Prompt 7 — Onboarding Tour

**Prerequisites:** Prompt 6 complete
**Reads:** `design.md` Section 8 (Onboarding Tour — Full Specification)
**Deliverables:** Working 8-step tour, localStorage persistence, Help page replay

---

**Read `design.md` Section 8 completely before writing any code.**

Create `frontend/src/components/tour/TourOverlay.tsx`:

**Architecture:**
- Single `TourOverlay` component rendered at the root of `App.tsx`.
- Manages its own state: `active: boolean`, `currentStep: number`.
- On mount: check `localStorage.getItem('loopwise_tour_complete')`. If absent or `"false"`: set `active = true` after 500ms delay.
- Export `useTour()` hook: `{ startTour, skipTour, isActive }` — used by Help page to replay.

**Spotlight implementation:**
```typescript
// Calculate target element bounding rect
// Apply backdrop via a full-screen fixed div with box-shadow cutout:
// box-shadow: 0 0 0 9999px rgba(10,31,13,0.85)
// Update rect on window resize (debounced 100ms)
// Animate rect change: CSS transition on top/left/width/height, 250ms ease-in-out
// Apply amber border on highlighted element: use an absolutely positioned overlay div
```

**Tour steps (exactly per design.md Section 8):**
Implement all 8 steps with the exact heading and body text from `design.md` Section 8 tour table.

Each step:
- Finds its target element by the selector defined in the step config.
- Step 1 (`targetSelector: null`): render a centred card in the middle of the screen (no spotlight).
- All other steps: spotlight the target element.
- Tooltip positioned below target on desktop; above target on mobile. Never overflows viewport.
- Arrow pointing at target element.

**Controls:**
- "Skip tour" ghost button — calls `skipTour()` on every step. Sets localStorage immediately.
- "Next →" primary amber button — advances to next step.
- "Got it ✓" primary amber button — on final step only. Calls `completeTour()`.
- Step counter "Step 3 of 8" — `--type-label`, `--color-text-secondary`.

**Accessibility (required):**
```typescript
// Focus trap: Tab key cycles only between "Skip tour" and "Next" buttons while tour is open
// Escape key: calls skipTour()
// aria-live="polite" on tooltip content div
// aria-modal="true" on the overlay wrapper
// Return focus to the tour trigger element after tour completes
```

**Responsive:**
- Mobile (< 768px): tooltip max-width 280px; always position above target if target is in bottom 40% of screen.
- Desktop: tooltip max-width 320px; position below target unless target is near the bottom of viewport.

**Help page integration:**
- `HelpPage.tsx` has a "Replay the app tour" card (top of page, per design.md Section 9.5).
- Tapping it calls `startTour()` from `useTour()`, which resets `currentStep = 0` and sets `active = true`.
- Tour replay does NOT reset the localStorage flag until the user completes or skips again.

**Write tests in `frontend/src/components/tour/__tests__/TourOverlay.test.tsx`:**
- `test_tour_shows_on_first_visit`: localStorage empty → tour renders after 500ms.
- `test_tour_does_not_show_on_return`: localStorage `loopwise_tour_complete = "true"` → tour does not render.
- `test_skip_tour_sets_localStorage`: click "Skip tour" → `loopwise_tour_complete = "true"` in localStorage.
- `test_tour_advances_steps`: click "Next" 7 times → step counter reads "Step 8 of 8".
- `test_escape_skips_tour`: press Escape → tour closes.
- `test_help_page_replays_tour`: call `startTour()` → tour renders at step 1 regardless of localStorage.

**Checkpoint:**
- Clear localStorage in browser. Load the app. Confirm tour appears after 500ms.
- Step through all 8 steps. Confirm each targets the correct element.
- Confirm tooltip never overflows the viewport at 375px width.
- Press Escape on step 3. Confirm tour closes.
- Reload page. Confirm tour does NOT reappear (localStorage flag set).
- Go to Help page. Tap "Replay the app tour." Confirm tour starts at step 1.
- Run `npm run test -- --reporter=verbose`. All 6 tour tests must pass. Paste output.

---

## Prompt 8 — Resident Classification UI

**Prerequisites:** Prompt 7 complete
**Reads:** `design.md` Sections 9.1, 9.2, 11; `architecture.md` Sections 6.1, 6.2, 8
**Deliverables:** Complete classification flow verified end-to-end with demo mode

---

**Read `design.md` Sections 9.1 and 9.2 completely before writing any code.**
Every screen state, layout rule, and interaction is specified there. Do not improvise.

Implement `frontend/src/pages/ClassificationPage.tsx` per `design.md` Section 9.1:
- Camera/upload area: large round button on mobile; drag-and-drop zone on desktop.
- Image preview with "Remove" link after selection.
- Text description fallback input. Label above the field (not placeholder-only).
- Ward dropdown: label "Which ward? (optional)"; 3 demo ward friendly names.
- Consent checkbox: unchecked by default. Label: "Save photo to help improve LoopWise." Info tooltip on "?".
- "Identify this item" button: disabled until at least one input provided. Full-width on mobile.
- Loading state: inline spinner over the form area, text "Checking the item…". Buttons disabled.
- Error states: inline error per field for input errors; full-page error card for inference/network failures.

Implement `frontend/src/hooks/useClassify.ts`:
- Wraps `classify()` API call.
- Manages loading, error, and result states.
- On success: navigate to `/result/:eventId` with classification data in router state.

Implement `frontend/src/pages/ResultPage.tsx` per `design.md` Section 9.2:

**All confidence states share:**
- "← Back to classify" ghost button top-left.
- Material name (Fraunces 28px), category badge.
- `BinCard` — visually dominant.
- `ConfidenceBar` with plain-language label (no numeric score ever).
- `RecoveryBar`.
- "What happens next" text.
- "How to sort it" do/don't list with ✓ and ✗ icons.
- Recovery channel label.
- `DemoModeIndicator` if `meta.demo_mode`.

**Medium confidence additions:** `⚠ We're not completely sure.` confirmation prompt with two buttons.

**Low confidence state:** top-3 picker with bin colour dot per option. "None of these / I don't know" always included.

**Correction submitted state:** acknowledgement card (plain language, no rewards). Single button: "Classify another item →".

Implement `frontend/src/hooks/useCorrection.ts`:
- Wraps `submitFeedback()`.
- Handles 429 rate-limit response: show `design.md` Section 11 plain-language message.
- Tracks loading, error, submitted states.

**Language check (mandatory before checkpoint):**
Scan every string literal in these two page files. If any of the following appear, replace them immediately:
- "confidence" → "How sure we are"
- "contamination" → "wrongly sorted"
- "classification" → "identifying the item"
- "model" (referring to AI) → "LoopWise"
- Any enum value visible to the user → replace with plain label

**Checkpoint:**
- Complete the full flow at mobile viewport (375px):
  1. Text description → submit → loading → result (high confidence).
  2. Submit correction → correction acknowledged state.
- Verify in database: `is_corrected = true`, `correction_id` set on the event row.
- Verify: consent checkbox is unchecked by default.
- Verify: `image_stored = false` when checkbox is unchecked.
- Verify: `DemoModeIndicator` is visible on result screen.
- Verify: no numeric confidence score is visible anywhere on screen.
- Verify: no technical jargon appears in any visible text (scan all text nodes).
- Take screenshot at 375px. Verify BinCard is the most visually dominant element on the result screen.

---

## Prompt 9 — Analytics Dashboard

**Prerequisites:** Prompt 8 complete
**Reads:** `design.md` Sections 9.3, 9.4, 10, 11; `architecture.md` Sections 6.3, 6.4, 10.3
**Deliverables:** Analytics overview + ward detail, seeded demo data, plain-language labels throughout

---

**Read `design.md` Sections 9.3 and 9.4 before writing any code.**

Implement `frontend/src/pages/AnalyticsOverviewPage.tsx` per `design.md` Section 9.3:

**Summary cards (4):** Use plain-language labels from the replacement table in Section 9.3. Every card has a `sub-label` element describing what the metric measures. Sub-labels are in `--type-label`, `--color-text-secondary`.

**Ward status table (desktop) / Ward status cards (mobile):**
- `StatusLight` component per row.
- Status text labels from Section 9.3: "Excellent", "Good", "Needs attention", "Needs work".
- Tap/click a row → navigate to `/analytics/ward/:wardId`.
- No action buttons on the table — navigation only.

**Material breakdown chart (Recharts):**
- Horizontal stacked bar. `--color-mat-*` tokens for segments.
- Legend below. No percentages on the bar — tooltip only.
- Chart title: "What's being sorted."

**Commonly confused items table:**
- Columns: "Item we guessed", "→", "Item it actually was", "Times reported."
- Max 5 rows visible. "See all" link expands to 10.
- No action buttons.

**`DemoModeIndicator`**: persistent at top-right. Also show a banner below the page title: "Using practice data for demonstration purposes — not live ward data."

**`DataHonestyFootnote`**: always at the bottom of the page. Use exact text from `design.md` Section 9.3.

Implement `frontend/src/pages/WardDetailPage.tsx` per `design.md` Section 9.4:

**Header:** ward friendly name (not the ID code); breadcrumb "← Overview"; date range selector.

**Date range selector:**
- Preset options: "Last 7 days", "Last 30 days", "Last 90 days", "Custom."
- Default: "Last 30 days."
- Custom range: date picker; confirm button; error if > 90 days.
- Changing a preset fires the API call immediately — no separate "Apply" button.

**Timeseries chart (Recharts LineChart):**
- Two lines: "Wrongly sorted" (`--color-signal-bad`) and "Recycling opportunity" (`--color-signal-good`).
- Y-axis: `--type-label` "Percentage of items sorted", 0%–100%.
- X-axis: sensible date intervals (every 5 days for 30-day view; every 14 days for 90-day view).
- Reference line at 20%: dashed, labelled "20% — needs attention."
- Tooltip: plain-language metric names, percentage values, date.
- No grid lines. Only the reference line.
- Loading state: `SkeletonShimmer` over the chart area.

**Empty state:** gentle message (per `design.md` Section 9.4). Not a blank screen. Single navigation link.

**`DataHonestyFootnote`**: always at the bottom. Same text as overview.

Implement `frontend/src/hooks/useWardAnalytics.ts`:
- Fetches from `/api/v1/analytics/ward/:wardId`.
- Debounces date range changes 300ms before firing API call.
- Caches last-fetched result in component state.

**Language audit (required before checkpoint):**
Scan every visible string in both analytics page files. Replace any technical terms per `design.md` Section 11.

**Checkpoint:**
- Load `/analytics` with demo seed data. Verify:
  - All 4 summary cards have plain-language labels and sub-labels.
  - Ward status table shows `StatusLight` components with text labels.
  - Material breakdown chart renders with correct colours.
  - "Commonly confused items" table shows data from demo seed.
  - `DemoModeIndicator` and practice data banner are both present.
  - `DataHonestyFootnote` is at the bottom of the page.
- Navigate to Ward B (`/analytics/ward/WD-DEMO-B`). Verify:
  - Contamination spike is visible on the timeseries for days 14–18.
  - "Wrongly sorted" line peaks above the 20% reference line on those days.
  - Chart tooltip shows plain-language labels.
  - "Recycling opportunity" line stays relatively stable.
- Change date range to "Last 7 days." Verify chart updates.
- Take screenshot at 1280px. Verify against `design.md` Section 9.4 layout.
- No numeric scores (0.18, 0.74, etc.) visible anywhere in the UI — values displayed as percentages or plain labels only.

---

## Prompt 10 — Help Page

**Prerequisites:** Prompt 9 complete
**Reads:** `design.md` Section 9.5
**Deliverables:** Help page with tour replay, material guide, practice mode explanation

---

**Read `design.md` Section 9.5 before writing any code.**

Implement `frontend/src/pages/HelpPage.tsx`:

**Tour replay card:**
- Large, tappable card at the top of the page.
- Icon: map/route icon (SVG, amber).
- Heading: "Replay the app tour."
- Sub-label: "Walk through how LoopWise works."
- On click: calls `startTour()` from `useTour()`.

**Material guide:**
- Section heading: "Material Guide."
- Sub-heading: "Quick reference for common items."
- Category filter tabs: "All", "Plastic", "Paper", "Organic", "Glass", "Metal", "E-waste", "Other."
- Material list: one row per material. Columns: `Badge` (category), material name, bin label, recycling symbol.
- Tap a row: expand an inline drawer showing full disposal instructions (do/don't list, next life text, recovery channel). No navigation — drawer within the page.
- Filter tabs change which rows are visible. "All" shows all 25+ materials.
- Search not required for MVP — filter tabs are sufficient.

**About Practice Mode section:**
- Heading: "About Practice Mode."
- Body: exact text from `design.md` Section 9.5.
- Style: `--color-surface-2` background block with amber left border.

**Checkpoint:**
- Navigate to `/help`. Confirm tour replay card is at the top.
- Click "Replay the app tour." Confirm tour starts at step 1.
- Select "Plastic" filter. Confirm only plastic materials appear.
- Tap a material row. Confirm the drawer expands with disposal instructions.
- Confirm "About Practice Mode" section is present with accurate text.

---

## Prompt 11 — Local End-to-End Integration Verification

**Prerequisites:** Prompts 8, 9, 10 complete
**Reads:** `architecture.md` (complete), `design.md` (complete)
**Deliverables:** Full system running locally under Docker Compose, all integration gaps resolved, test suite clean

---

Re-read `architecture.md` completely.

Start the full system: `docker compose up --build`. Wait for all health checks to pass.

**Integration sequence:**

1. POST `/api/v1/classify` (text, no consent). Verify response shape matches `architecture.md` Section 6.1 field-by-field. Verify `image_stored = false` in DB.
2. POST `/api/v1/feedback` with returned `event_id`. Verify `acknowledged: true`. Verify DB state.
3. GET `/api/v1/analytics/ward/WD-DEMO-B` for 30 days. Verify response shape, `demo_data: true`.
4. GET `/api/v1/health`. Verify `demo_mode: true`, all components OK or mock.
5. POST `/api/v1/feedback` 11 times with same session. Verify 11th returns HTTP 429.

**Privacy checks:**
6. POST classify with no `ward_id` → DB row has `ward_id = null`.
7. POST classify with `consent.image_upload: false` → no image reference in `docker compose logs api`.

**Frontend integration checks:**
8. Frontend API client base URL is configurable (not hardcoded to localhost).
9. Session ID is consistent across classify and feedback calls in the same browser session.
10. Error responses from the backend render as plain-language messages in the UI (not error codes).
11. `DemoModeIndicator` is present on analytics pages. Absent on classification result pages.

**Build and test:**
```bash
docker compose exec api pytest -v --tb=short
npm run test
npm run build
```

**Checkpoint:**
- All pytest tests pass. Paste output with count.
- All frontend tests pass. Paste output.
- `npm run build` — zero TypeScript errors. Paste output.
- Report any integration gaps found and confirmed resolved.

---

## Prompt 12 — Visual QA and Design Fidelity

**Prerequisites:** Prompt 11 complete
**Reads:** `design.md` (complete) — the only reference standard for this prompt
**Deliverables:** All screens verified at 3 breakpoints, all discrepancies corrected

---

Read `design.md` completely. This prompt only verifies and corrects.

**Take screenshots at 375px, 768px, and 1280px for these 8 screens:**
1. Classification entry — empty state
2. Classification entry — image selected
3. Result — high confidence
4. Result — low confidence (top-3 picker visible)
5. Correction submitted state
6. Analytics overview
7. Ward detail — timeseries with spike visible
8. Help page

**For each screenshot, verify this checklist:**

```
□ Background is --color-bg (#0A1F0D) — no light backgrounds
□ All text is --color-text-primary or --color-text-secondary — no off-token colours
□ Primary action button uses --color-amber background
□ Fraunces is used for: display heading, material name on result. Nothing else.
□ Inter is used for: all other text
□ Tabular numerals on all numeric values
□ BinCard is the most visually dominant element on result screens
□ ConfidenceBar shows NO numeric score — only plain-language label
□ RecoveryBar shows NO numeric score — only plain-language label
□ DemoModeIndicator ("Practice Mode — not live data") present on all analytics screens
□ DataHonestyFootnote present on analytics overview and ward detail
□ Practice data banner present on analytics overview
□ Ward status table shows StatusLight + text label (not just colour)
□ Timeseries chart: two lines, amber reference line at 20%, no grid lines
□ Chart tooltip shows plain-language labels (not variable names)
□ No gradient backgrounds anywhere
□ No glowing effects or neon borders
□ No placeholder text ("Lorem ipsum", "TODO", "Coming soon", "Demo text")
□ No percentage rings or donut progress indicators (use bars instead)
□ No numeric scores visible to the user (0.87, 0.18, etc.) — only labels and %
□ No technical jargon visible in any text node
□ All buttons have full plain-language labels
□ Mobile (375px): no horizontal scroll
□ Mobile (375px): bottom tab bar visible with 4 items
□ Desktop (1280px): left sidebar visible with 5 items
□ Tour overlay renders correctly if triggered on the page
□ Tour tooltip does not overflow viewport on any breakpoint
□ All interactive elements: visible 44×44px minimum touch target
□ Focus rings visible on keyboard navigation (test with Tab key)
```

**Report format per screen:**
```
Screen: [name] | Breakpoint: [px]
Failing items: [list any □ that failed with specific description]
```

Fix every failing item before marking complete. Re-screenshot after fixes.

**Checkpoint:** All 24 screenshots pass all checklist items. No open failures.

---

## Prompt 13 — Documentation and Local Demo Script

**Prerequisites:** Prompt 12 complete
**Reads:** `architecture.md`, `design.md`
**Deliverables:** Updated `architecture.md`, `README.md`, `docs/demo-script.md`, clean Docker startup

---

**Update `architecture.md`:**
- Record actual package versions installed.
- Record any API contract or data model changes made during implementation.
- Update Section 17 (Unresolved Questions) — mark resolved ones; add any new ones discovered.
- Do not document planned features as implemented.

**Create `README.md`:**

Include exactly:
- 2-paragraph product overview (plain language; no technical jargon)
- Quick start (5 steps: clone, copy env, docker compose up, seed, open browser)
- How to run in practice/demo mode (it's the default)
- How to run tests
- What is real vs. practice data — honest table matching `architecture.md` Section 2
- How to replay the onboarding tour (go to Help page)

**Create `docs/demo-script.md`:**

Structure:
1. **Setup** (2 minutes): confirm app is running, practice mode is on
2. **Resident track** (4 minutes):
   - Show classification entry (point out consent checkbox)
   - Submit text description → show result
   - Point out BinCard, ConfidenceBar, RecoveryBar — all plain language
   - Submit a correction → show acknowledgement
   - Note: "LoopWise is running in Practice Mode — these classifications come from a test system, not a live model."
3. **Municipal track** (4 minutes):
   - Overview page: ward status table, material breakdown
   - Navigate to Ward B: show contamination spike on timeseries
   - Navigate to Ward C: show consistently good recovery potential
   - Point out `DataHonestyFootnote` — be honest with the audience
4. **Help and tour** (1 minute): replay tour from Help page

Every demo step must note which features are real (working code, real API) and which are practice data (seeded).

**Final clean-start test:**
```bash
docker compose down -v
docker compose up --build
docker compose exec api alembic upgrade head
docker compose exec api python -m app.seeds.materials
docker compose exec api python -m app.seeds.demo_analytics
```
Open the app. Confirm:
- Practice mode indicator visible.
- Onboarding tour launches automatically (localStorage cleared by clean start is not automatic — instruct the reviewer to clear it manually first).
- Classification flow works.
- Analytics shows ward data with the correct narrative.
- No errors in console or API logs.

**Checkpoint:**
- README quick start instructions work from a clean checkout — test them literally.
- `architecture.md` reflects actual implementation.
- `docs/demo-script.md` covers both tracks with honest practice-mode disclosures.
- Clean-start test completes without errors.
- No secrets in any committed file.

---

# Part 2: AWS Cloud Provisioning & Deployment Playbook

---

## Prompt 14 — AWS Account Readiness & Non-Root IAM Setup

**Prerequisites:** Local application verified (Prompts 0–13 complete); active AWS CLI access.
**Reads:** `architecture.md` Sections 11.3, 11.4, 11.5
**Deliverables:** Preflight check results, identity confirmation, budget alert setup, non-root IAM deployment identity, explicit Provisioning Plan presented to user for approval.

---

Inspect current AWS CLI state and caller identity BEFORE running any cloud setup commands:

1. **Run Preflight Verification Commands:**
```bash
aws sts get-caller-identity --profile personal
aws configure get region --profile personal
aws --version
```

2. **Evaluate Identity & Enforce Security Boundary:**
   - Parse the `Arn` returned by `get-caller-identity`.
   - **HALT CONDITION:** If the ARN ends with `:root`, flag the security risk immediately.
   - Do NOT execute resource creation using root credentials.
   - Instruct/guide creation of a dedicated non-root IAM deployment user (`loopwise-deployer`) with an attached infrastructure policy (or `AdministratorAccess` scoped for hackathon deployment).

3. **Configure AWS Budget Alert Safeguards:**
   - Set up an AWS Budget alert in `us-east-1` (the global billing region) to trigger email alerts if spending exceeds $10.
   - *Reminder:* Budget alerts notify the developer of spending; they do not automatically terminate running AWS resources or guarantee zero cost.

4. **Prepare Provisioning Plan for User Approval:**
   Draft a clear, explicit summary covering:
   - Target Region: `ap-south-1` (Mumbai)
   - Profile: `personal`
   - Non-root IAM Identity: `loopwise-deployer`
   - Resources to be provisioned: S3 private bucket, custom VPC, RDS PostgreSQL (`db.t4g.micro`), ElastiCache Redis (`cache.t4g.micro`), ECS Fargate services, CloudFront distribution.
   - Estimated monthly baseline cost and credit coverage.

5. **DO NOT CREATE ANY AWS RESOURCES** until the user explicitly reviews and approves the Provisioning Plan.

**Checkpoint:**
- Report preflight output (`caller-identity`, `region`, `aws-version`).
- State explicitly whether caller identity is root or non-root.
- Confirm budget alert configuration is staged.
- Present Provisioning Plan and state: "Awaiting user approval before proceeding to Prompt 15."

---

## Prompt 15 — AWS S3 Private Storage & Security Configuration

**Prerequisites:** Prompt 14 complete and user approval granted.
**Reads:** `architecture.md` Sections 8, 11.3, 11.4
**Deliverables:** Private, encrypted S3 bucket for consent-gated image uploads and dataset exports.

---

Inspect existing S3 buckets in `ap-south-1` before creation:
```bash
aws s3api list-buckets --profile personal --region ap-south-1
```

1. **Create Private S3 Bucket:**
```bash
aws s3api create-bucket \
  --profile personal \
  --region ap-south-1 \
  --bucket loopwise-media-storage-ap-south-1-<ACCOUNT_ID> \
  --create-bucket-configuration LocationConstraint=ap-south-1
```
2. **Apply Block Public Access Configuration (All 4 Flags True):**
```bash
aws s3api put-public-access-block \
  --profile personal \
  --region ap-south-1 \
  --bucket loopwise-media-storage-ap-south-1-<ACCOUNT_ID> \
  --public-access-block-configuration "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"
```
3. **Configure Default SSE-S3 Encryption:**
```bash
aws s3api put-bucket-encryption \
  --profile personal \
  --region ap-south-1 \
  --bucket loopwise-media-storage-ap-south-1-<ACCOUNT_ID> \
  --server-side-encryption-configuration '{"Rules": [{"ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}}]}'
```
4. **Verify Bucket Operations via Test Write & Clean Up:**
```bash
echo "loopwise-s3-test" > scratch/s3-test.txt
aws s3 cp scratch/s3-test.txt s3://loopwise-media-storage-ap-south-1-<ACCOUNT_ID>/scratch/s3-test.txt --profile personal --region ap-south-1
aws s3 rm s3://loopwise-media-storage-ap-south-1-<ACCOUNT_ID>/scratch/s3-test.txt --profile personal --region ap-south-1
```

**Checkpoint:**
- Paste `aws s3api get-public-access-block` output. Confirm all 4 settings are `true`.
- Paste `aws s3api get-bucket-encryption` output. Confirm `AES256` SSE-S3 encryption.
- Confirm test write/read/delete succeeded without exposing public access.

---

## Prompt 16 — AWS VPC Networking & Private Infrastructure Setup

**Prerequisites:** Prompt 15 complete.
**Reads:** `architecture.md` Sections 5, 11.3, 11.4
**Deliverables:** Custom VPC, subnets, Security Groups, private RDS PostgreSQL 16 instance, private ElastiCache Redis 7 cluster, AWS Secrets Manager secret.

---

Inspect existing VPCs and network resources before creation:
```bash
aws ec2 describe-vpcs --profile personal --region ap-south-1
aws rds describe-db-instances --profile personal --region ap-south-1
```

1. **Provision Custom VPC & Subnets:**
   - Create VPC `loopwise-vpc` (`10.0.0.0/16`) in `ap-south-1`.
   - Create 2 Public Subnets (`10.0.1.0/24` in `ap-south-1a`, `10.0.2.0/24` in `ap-south-1b`) with Internet Gateway.
   - Create 2 Private Subnets (`10.0.10.0/24`, `10.0.20.0/24`) with NAT Gateway.
   - Create 2 Private DB Subnets (`10.0.100.0/24`, `10.0.200.0/24`) for RDS & ElastiCache.

2. **Configure Security Groups (Strict Isolation):**
   - `alb-sg`: Inbound HTTP/HTTPS from `0.0.0.0/0`.
   - `ecs-task-sg`: Inbound port 8000 from `alb-sg`.
   - `rds-sg`: Inbound port 5432 ONLY from `ecs-task-sg`. **No public access**.
   - `redis-sg`: Inbound port 6379 ONLY from `ecs-task-sg`. **No public access**.

3. **Provision Private RDS PostgreSQL 16 Instance:**
   - DB Instance Identifier: `loopwise-db`
   - Class: `db.t4g.micro`; Subnet Group: private DB subnets; `PubliclyAccessible = false`.
   - Encrypted at rest using default KMS key.

4. **Provision Private ElastiCache Redis 7 Cluster:**
   - Cluster Identifier: `loopwise-cache`
   - Node Type: `cache.t4g.micro`; Subnet Group: private DB subnets; `redis-sg`.

5. **Store Credentials in AWS Secrets Manager:**
```bash
aws secretsmanager create-secret \
  --profile personal \
  --region ap-south-1 \
  --name "loopwise/production/secrets" \
  --description "LoopWise production database, redis, and JWT secrets" \
  --secret-string '{"DATABASE_URL":"postgresql+asyncpg://<USER>:<PASS>@<RDS_ENDPOINT>:5432/loopwise","REDIS_URL":"redis://<REDIS_ENDPOINT>:6379/0","SECRET_KEY":"<GENERATE_HEX_32>"}'
```

**Checkpoint:**
- Paste `aws rds describe-db-instances` output confirming `PubliclyAccessible: false`.
- Verify ElastiCache security group allows inbound traffic ONLY from `ecs-task-sg`.
- Confirm secret exists in Secrets Manager (`aws secretsmanager describe-secret`). Paste secret ARN (do NOT print secret string value).

---

## Prompt 17 — AWS ECS Fargate Containerization & Backend Deployment

**Prerequisites:** Prompt 16 complete.
**Reads:** `architecture.md` Sections 4, 11.3, 11.4
**Deliverables:** Amazon ECR repo, built backend image, IAM Task Roles, ECS Task Definitions, ECS Fargate API Service and Celery Worker Service running in private subnets.

---

Inspect existing ECR repos and ECS clusters:
```bash
aws ecr describe-repositories --profile personal --region ap-south-1
aws ecs list-clusters --profile personal --region ap-south-1
```

1. **Create Amazon ECR Repository & Push Container Image:**
```bash
aws ecr create-repository --repository-name loopwise-backend --profile personal --region ap-south-1
aws ecr get-login-password --profile personal --region ap-south-1 | docker login --username AWS --password-stdin <ACCOUNT_ID>.dkr.ecr.ap-south-1.amazonaws.com
docker build -t loopwise-backend -f backend/Dockerfile backend/
docker tag loopwise-backend:latest <ACCOUNT_ID>.dkr.ecr.ap-south-1.amazonaws.com/loopwise-backend:latest
docker push <ACCOUNT_ID>.dkr.ecr.ap-south-1.amazonaws.com/loopwise-backend:latest
```

2. **Configure IAM Roles:**
   - `ecsTaskExecutionRole`: permissions for ECR image pull and CloudWatch log streaming.
   - `loopwise-task-role`: attached to ECS task for runtime access to S3 (`loopwise-media-storage-*`) and Secrets Manager.

3. **Register ECS Task Definitions:**
   - `loopwise-api-task`: runs `loopwise-backend:latest` on port 8000; injects secrets from Secrets Manager.
   - `loopwise-worker-task`: runs `loopwise-backend:latest` with command `celery -A app.analytics.tasks worker --loglevel=info`.

4. **Launch ECS Fargate Services:**
   - Create ECS Cluster `loopwise-cluster`.
   - Deploy `loopwise-api-service` (2 tasks, private subnets, registered with ALB target group).
   - Deploy `loopwise-worker-service` (1 task, private subnets).

5. **Run Alembic Migrations & Seed Data via One-Off ECS Task:**
```bash
aws ecs run-task \
  --profile personal \
  --region ap-south-1 \
  --cluster loopwise-cluster \
  --task-definition loopwise-api-task \
  --overrides '{"containerOverrides": [{"name": "api", "command": ["alembic", "upgrade", "head"]}]}'
```

6. **Verify API Health via ALB Endpoint:**
   - `GET http://<ALB_DNS_NAME>/api/v1/health`

**Checkpoint:**
- Confirm container image digest in ECR.
- Confirm ECS Fargate tasks are `RUNNING`.
- Paste HTTP 200 response from `/api/v1/health`. Confirm `"database": "ok"` and `"cache": "ok"`.

---

## Prompt 18 — AWS CloudFront Edge Delivery & Frontend Distribution

**Prerequisites:** Prompt 17 complete.
**Reads:** `architecture.md` Sections 6, 11.3
**Deliverables:** Production React SPA build, S3 frontend hosting bucket, CloudFront distribution with HTTPS and API proxy routing.

---

Inspect existing CloudFront distributions:
```bash
aws cloudfront list-distributions --profile personal
```

1. **Build Production React SPA:**
```bash
cd frontend && npm run build && cd ..
```
2. **Create Frontend Hosting S3 Bucket & Sync Assets:**
```bash
aws s3api create-bucket \
  --profile personal \
  --region ap-south-1 \
  --bucket loopwise-frontend-hosting-ap-south-1-<ACCOUNT_ID> \
  --create-bucket-configuration LocationConstraint=ap-south-1
aws s3 sync frontend/dist/ s3://loopwise-frontend-hosting-ap-south-1-<ACCOUNT_ID>/ --profile personal --region ap-south-1
```
3. **Deploy CloudFront Distribution:**
   - Origin 1 (Default): S3 hosting bucket (`/*` → index.html fallback for SPA router).
   - Origin 2: ALB DNS endpoint (`/api/*` → forward all headers/cookies to API backend; no caching).
   - Viewer Protocol Policy: Redirect HTTP to HTTPS.
4. **Verify Live Application Deployment:**
   - Test CloudFront distribution domain in browser.
   - Execute classification flow and check analytics dashboards.

**Checkpoint:**
- Paste CloudFront distribution domain URL.
- Confirm SPA routes (`/`, `/analytics`, `/help`) load without 404 errors.
- Confirm API calls `/api/v1/classify` proxy through CloudFront to ALB backend successfully.

---

## Prompt 19 — Observability, Monitoring, & Teardown Documentation

**Prerequisites:** Prompt 18 complete.
**Reads:** `architecture.md` Sections 11.3, 11.4, 13
**Deliverables:** CloudWatch Log Groups, metric alarms, operational readiness report, and explicit resource teardown script.

---

1. **Configure CloudWatch Log Groups & Retention:**
```bash
aws logs create-log-group --log-group-name /ecs/loopwise-api --profile personal --region ap-south-1
aws logs put-retention-policy --log-group-name /ecs/loopwise-api --retention-in-days 14 --profile personal --region ap-south-1
aws logs create-log-group --log-group-name /ecs/loopwise-worker --profile personal --region ap-south-1
aws logs put-retention-policy --log-group-name /ecs/loopwise-worker --retention-in-days 14 --profile personal --region ap-south-1
```
2. **Audit Logs for Privacy Compliance:**
   - Inspect CloudWatch logs to verify zero raw coordinates, zero PII, and no unencrypted image data.

3. **Create Disposable Resource Teardown Automation (`aws/teardown.sh`):**

> ⚠️ **CRITICAL SECURITY RULE:** Never execute teardown commands or delete cloud resources/data without explicit, written confirmation from the user.

Create helper script `aws/teardown.sh`:
```bash
#!/usr/bin/env bash
# LoopWise Disposable AWS Infrastructure Teardown Script
# REQUIRES MANUAL CONFIRMATION BEFORE EXECUTION

echo "⚠️ WARNING: This will permanently delete all LoopWise AWS resources!"
read -p "Are you sure you want to delete all cloud resources? (type YES to confirm): " CONFIRM
if [ "$CONFIRM" != "YES" ]; then
    echo "Teardown cancelled."
    exit 1
fi

echo "Teardown confirmed. Destroying resources in ap-south-1..."
# 1. Scale ECS services to 0 and delete services
# 2. Delete CloudFront distribution
# 3. Empty and delete S3 buckets
# 4. Delete RDS instance and ElastiCache cluster
# 5. Delete VPC, NAT Gateway, subnets, and Security Groups
```

4. **Execute Final End-to-End Verification Sweep:**
   - Verify health endpoint `/api/v1/health`.
   - Verify zero hardcoded secrets across codebase.

**Checkpoint:**
- Confirm CloudWatch Log Groups active with 14-day retention.
- Confirm `aws/teardown.sh` script exists with explicit confirmation prompt guards.
- State final operational readiness status across all 19 prompts.

---

## Appendix A — Shared Rules for All Prompts

1. Never claim a test passed without running it and pasting output.
2. Never display numeric confidence, contamination, or recovery scores to users — only plain-language labels and percentages.
3. Never invent model accuracy figures or environmental impact numbers.
4. Never use technical terms in the UI. See `design.md` Section 11 terminology table.
5. Demo mode is always labelled "Practice Mode" in the UI. Never hide it.
6. Images are never stored without explicit per-event consent.
7. GPS coordinates are never accepted, stored, or echoed.
8. User corrections are training signal candidates — not ground truth.
9. When `architecture.md` or `design.md` conflicts with the codebase, update the document first.
10. The onboarding tour must be completable by someone using only a keyboard (no mouse).
11. Every chart must have a plain-language title, labelled axes, a legend, and a `DataHonestyFootnote`.
12. Always use explicit `--profile personal` and `--region ap-south-1` for AWS CLI commands.
13. Never delete AWS resources or user data without explicit written confirmation from the user.
14. Incomplete work must be reported as incomplete — never papered over.

---

## Appendix B — API Error Code to Plain Language Map

| Code | HTTP | User-facing message (from design.md Section 11) |
|---|---|---|
| `INVALID_INPUT` | 422 | "Please add a photo or describe the item before submitting." |
| `IMAGE_TOO_LARGE` | 413 | "That photo is too large. Please try a smaller photo." |
| `UNSUPPORTED_FORMAT` | 415 | "We couldn't read that file. Please use a JPEG or PNG photo." |
| `INFERENCE_FAILED` | 500 | "We couldn't identify this item. Try a clearer photo or describe it instead." |
| `WARD_UNKNOWN` | 422 | "We don't recognise that ward. Please choose a ward from the list." |
| `EVENT_NOT_FOUND` | 404 | Internal only — should not reach the UI. |
| `SESSION_MISMATCH` | 403 | Internal only — retry with correct session. |
| `INVALID_CORRECTION` | 422 | "We couldn't save that correction. Please try selecting a different option." |
| `RATE_LIMITED` | 429 | "You've submitted several corrections recently. Please wait a few minutes." |
| Network error | — | "We couldn't connect. Please check your internet and try again." |

---

## Appendix C — Plain Language Terminology Reference

| Never show to users | Always show instead |
|---|---|
| Confidence score / confidence: 0.87 | "How sure we are" / "Very sure" |
| Contamination rate | "Wrongly sorted" / "Items put in wrong bin" |
| Recovery potential | "Recycling opportunity" / "Can this be recycled?" |
| Classification | "Identifying the item" |
| Correction | "Tell us if we got it wrong" |
| Demo mode / Mock mode | "Practice Mode" |
| Model / AI model | "LoopWise" |
| Material category | "Type of material" |
| Low confidence rate | "Uncertain answers" |
| Top misclassifications | "Commonly confused items" |
| Ward ID / ward code | Ward's friendly name |
| Event, Session, Rollup | Never shown to users |
| Any enum value | Friendly label from design.md |

---

## Appendix D — Demo Ward Reference

| Ward ID | Friendly name | Narrative | Use in demo |
|---|---|---|---|
| `WD-DEMO-A` | Ward A | Contamination rate improving over 30 days | Show: progress is possible |
| `WD-DEMO-B` | Ward B | Contamination spike on days 14–18 | Show: anomaly detection value |
| `WD-DEMO-C` | Ward C | Consistently high recycling opportunity | Show: what good looks like |
