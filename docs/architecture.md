# Architecture — LoopWise Waste Segregation Intelligence Platform

> **Status:** Initial draft — v0.1 | **Updated:** 2026-10
> This document is the authoritative technical reference. All implementation decisions must derive from it.
> When implementation diverges from this document, update the document first and record the reason.

---

## 1. Product Goals and Scope

### What we are building
A circular-economy waste segregation intelligence platform that helps residents classify waste correctly at the point of disposal, collects correction-aware model feedback, and provides ward-level analytics to society managers, waste-recovery operators, and municipal decision-makers.

### Core capabilities

| Capability | State |
|---|---|
| Waste classification via YOLO26 / ONNX inference | Planned — requires trained weights |
| Demo / mock classification mode | **Required before real model — first-class state** |
| Disposal guidance (bin, confidence, recovery potential, next life, recovery channel) | In scope |
| User corrections and feedback collection | In scope |
| Classification event data pipeline (consent-respecting) | In scope |
| Pre-aggregated ward-level analytics | In scope |
| Contamination and recovery potential dashboards | In scope |
| Society, operator, and municipal analytics views | In scope |
| Consent-gated image upload | In scope — opt-in only |
| Analytics retraining dataset export | Planned integration |

### Non-goals (explicit)
- Token rewards, gamification, or points systems
- Carbon credit estimation or trading
- A materials marketplace
- End-to-end lifecycle tracking beyond point of disposal
- Municipal waste collection routing (this release)
- Claimed model accuracy figures without benchmark evidence
- Raw GPS coordinates in any data path
- Automatic image storage without explicit opt-in per event

---

## 2. Users and Roles

| Role | Primary surface | Key tasks |
|---|---|---|
| **Resident** | Mobile-first classification UI | Scan or describe waste; receive disposal guidance; correct predictions |
| **Society Manager** | Analytics dashboard (society scope) | Monitor contamination trends; identify problem categories |
| **Waste Recovery Operator** | Analytics dashboard (material/channel scope) | Track recovery potential; identify material flows |
| **Municipal Official** | Analytics dashboard (ward/city scope) | Ward-level trends; contamination hotspots; model confusion analysis |
| **Platform Admin** | Admin panel — phase 2 | Model version management; taxonomy management |

Residents may be anonymous (session-only) or registered. All analytics roles require authenticated sessions. Authentication is JWT-based; the IdP is unresolved (see Section 17).

---

## 3. System Context

```mermaid
C4Context
    title LoopWise — System Context

    Person(resident, "Resident", "Classifies waste at point of disposal via mobile browser")
    Person(municipal, "Municipal Official", "Reviews ward-level analytics and contamination trends")
    Person(operator, "Waste Recovery Operator", "Monitors material recovery potential by channel")
    Person(society_mgr, "Society Manager", "Monitors contamination within their housing society")

    System(platform, "LoopWise Platform", "Classifies waste, collects corrections, aggregates analytics")

    System_Ext(onnx, "YOLO26 / ONNX Model", "Fine-tuned waste classification model — weights required for production mode")
    System_Ext(rds, "AWS RDS PostgreSQL", "Primary structured data store")
    System_Ext(redis, "AWS ElastiCache Redis", "Analytics cache and Celery broker")
    System_Ext(s3, "AWS S3", "Consent-gated image storage")
    System_Ext(ward_data, "Ward Boundary Lookup", "Static coarse geographic identifiers — source TBD")

    Rel(resident, platform, "Classifies waste; submits corrections")
    Rel(municipal, platform, "Views analytics dashboard")
    Rel(operator, platform, "Views recovery analytics")
    Rel(society_mgr, platform, "Views society analytics")
    Rel(platform, onnx, "Runs ONNX inference (only classification path)")
    Rel(platform, rds, "Reads/writes events, corrections, analytics rollups")
    Rel(platform, redis, "Caches analytics; stores Celery tasks")
    Rel(platform, s3, "Stores images — explicit consent required per event")
    Rel(platform, ward_data, "Resolves coarse ward from user-supplied identifier")
```

---

## 4. Component Architecture

```mermaid
graph TD
    subgraph FE["Frontend — React + TypeScript"]
        CUI["Classification UI\n(mobile-first)"]
        DASH["Analytics Dashboard\n(desktop-first)"]
        DS["Design System\nComponent Library"]
        CUI --> DS
        DASH --> DS
    end

    subgraph BE["Backend — FastAPI / Python"]
        GW["API Gateway\n/api/v1/"]
        INF["Inference Service"]
        FB["Feedback Service"]
        ANA["Analytics Service"]
        MAT["Materials Service"]
        PM["Privacy & Consent\nMiddleware"]
        GW --> INF
        GW --> FB
        GW --> ANA
        GW --> MAT
        PM --> GW
    end

    subgraph ML["ML Pipeline"]
        ONNX_RT["ONNXClassifier\n(only classification path)"]
        PRE["Image Preprocessor\nPIL — resize / normalise"]
        INF --> PRE
        PRE --> ONNX_RT
    end

    subgraph STORE["Storage"]
        PG[("PostgreSQL\nEvents · Materials\nCorrections · Analytics")]
        CACHE[("Redis\nAnalytics cache\nSessions · Rate limits")]
        S3B[("S3\nConsent-gated\nImages")]
    end

    subgraph JOBS["Async — Celery"]
        AGG["Analytics Aggregator\nWard/day rollup"]
        EXP["Dataset Exporter\nFeedback → training candidates"]
    end

    FE -->|HTTPS / JSON| GW
    INF --> PG
    FB --> PG
    ANA --> PG
    ANA --> CACHE
    AGG --> PG
    AGG --> CACHE
    INF -->|opt-in only| S3B
    EXP --> PG
    EXP -->|export| S3B
```

---

## 5. Data Models

### 5.1 ClassificationEvent

Primary record of every classification request. Written at inference time; updated on user correction.

```
classification_events
├── event_id             UUID            PK
├── session_id           UUID            NOT NULL    -- anonymous; not linked to user without consent
├── user_id              UUID            FK users, nullable
├── created_at           TIMESTAMPTZ     NOT NULL
├── ward_id              VARCHAR(32)     nullable    -- coarse identifier only; never raw GPS
├── input_type           ENUM            (image, text) NOT NULL
├── model_version        VARCHAR(32)     NOT NULL    -- e.g. 'yolo26n-cls-v1'
├── predicted_class      VARCHAR(64)     NOT NULL    -- material_id from materials table
├── confidence           FLOAT           NOT NULL    -- 0.0 – 1.0
├── top3_predictions     JSONB           -- [{class, confidence}, {}, {}]
├── material_category    ENUM            (plastic, glass, metal, organic, paper, e_waste,
│                                         composite, hazardous, other)
├── disposal_bin         ENUM            (wet, dry, hazardous, e_waste, rejected)
├── recovery_potential   ENUM            (high, medium, low, none)
├── recovery_channel     VARCHAR(64)     -- 'informal_sector', 'municipality_dry', 'specialized'
├── is_corrected         BOOLEAN         DEFAULT FALSE
├── correction_id        UUID            FK user_corrections, nullable
├── image_stored         BOOLEAN         DEFAULT FALSE
├── image_key            TEXT            nullable    -- S3 key; null unless image_stored = true
├── consent_flags        JSONB           -- {image_upload: bool, analytics: bool, location: bool}
└── demo_mode            BOOLEAN         DEFAULT FALSE    -- legacy; always FALSE for new rows
```

**Indexes:** `(ward_id, created_at)` · `(session_id, created_at)` · `(predicted_class, created_at)` · `(is_corrected, created_at)` · `(demo_mode, created_at)`

> `demo_mode` is retained for schema stability only. Demo/mock classification
> was removed; the column is always `False` for events written now, and the
> aggregator still excludes any legacy rows that predate the removal.

---

### 5.2 UserCorrection

Records a resident's correction of a predicted classification.

```
user_corrections
├── correction_id        UUID            PK
├── event_id             UUID            FK classification_events NOT NULL
├── session_id           UUID            NOT NULL
├── user_id              UUID            FK users, nullable
├── corrected_class      VARCHAR(64)     NOT NULL    -- material_id
├── correction_note      TEXT            nullable
├── created_at           TIMESTAMPTZ     NOT NULL
└── reviewed             BOOLEAN         DEFAULT FALSE    -- set by human reviewer before retraining use
```

> ⚠ **A correction is a signal about model error, not a verified fact about physical waste.** It is a training data candidate subject to human review before being used in any retraining workflow. The `reviewed` flag must be `true` before any correction is included in a training dataset export.

---

### 5.3 Material

Static taxonomy reference. Seeded from a curated materials list. Class labels must be cross-referenced against actual YOLO26 output classes when weights become available — do not hard-code mappings until then.

```
materials
├── material_id          VARCHAR(64)     PK    -- e.g. 'plastic_pet_bottle'
├── name                 VARCHAR(128)    NOT NULL
├── category             ENUM            (matches material_category in §5.1)
├── subcategory          VARCHAR(64)
├── disposal_bin         ENUM            (matches disposal_bin in §5.1)
├── recovery_potential   ENUM            (matches recovery_potential in §5.1)
├── next_life            TEXT            -- e.g. "Recycled into polyester fibre or new PET bottles"
├── recovery_channel     VARCHAR(64)
├── contamination_notes  TEXT
├── icon_slug            VARCHAR(64)     -- maps to UI icon set
├── demo_seed            BOOLEAN         DEFAULT FALSE   -- true if inserted by seed script
└── updated_at           TIMESTAMPTZ
```

> ⚠ **Assumption:** Material taxonomy class labels are provisional. When YOLO26 weights are available, cross-reference model output indices against this table and update the class-index mapping file. Do not claim material mappings are accurate until this is done.

---

### 5.4 WardAnalyticsRollup

Pre-aggregated daily snapshots per ward. Computed by Celery task — never at query time.

```
ward_analytics_rollups
├── rollup_id            UUID            PK
├── ward_id              VARCHAR(32)     NOT NULL
├── date                 DATE            NOT NULL
├── total_events         INTEGER
├── unique_sessions      INTEGER
├── correction_rate      FLOAT           -- corrections / total_events
├── contamination_rate   FLOAT           -- events with recovery_potential ∈ {low, none} / total
├── recovery_potential_avg FLOAT         -- normalised 0–1 (high=1.0, medium=0.6, low=0.2, none=0.0)
├── low_confidence_rate  FLOAT           -- events with confidence < 0.55 / total
├── material_breakdown   JSONB           -- {category_enum: count, ...}
├── top_misclassifications JSONB         -- [{predicted, corrected, count}, ...]
└── computed_at          TIMESTAMPTZ
```

**Unique constraint:** `(ward_id, date)`

---

### 5.5 User (registered; optional)

```
users
├── user_id              UUID            PK
├── email                VARCHAR(255)    UNIQUE nullable
├── role                 ENUM            (resident, society_manager, operator, municipal, admin)
├── ward_id              VARCHAR(32)     nullable    -- default analytics scope
├── society_id           VARCHAR(64)     nullable
├── consent_flags        JSONB
├── created_at           TIMESTAMPTZ
└── last_active_at       TIMESTAMPTZ
```

---

## 6. API Contracts

### Base URL: `/api/v1/`

### Standard response envelope

```json
{
  "status": "ok | error",
  "data": { "..." } ,
  "error": { "code": "ERROR_CODE", "message": "Human-readable detail" },
  "meta": {
    "request_id": "uuid",
    "model_version": "yolo26n-cls-v1"
  }
}
```

`error` is null when status is `"ok"`. `data` is null when status is `"error"`.

---

### 6.1 POST /api/v1/classify

**Auth:** None required. Session ID in body.

**Request**
```json
{
  "session_id": "uuid",
  "input_type": "image | text",
  "image_b64": "base64string | null",
  "description": "string | null",
  "ward_id": "WD-001 | null",
  "consent": {
    "image_upload": false,
    "analytics": true,
    "location": false
  }
}
```

**Validation rules**
- At least one of `image_b64` or `description` must be non-null
- `image_b64` decoded size ≤ 5 MB; accepted formats: JPEG, PNG, WebP only
- `ward_id` must match a known ward identifier or be null
- `consent.image_upload` must be explicitly `true` for image to be stored; absent or false = do not store

**Response 200**
```json
{
  "status": "ok",
  "data": {
    "event_id": "uuid",
    "predicted_class": "plastic_pet_bottle",
    "confidence": 0.87,
    "confidence_label": "high",
    "top3": [
      { "class": "plastic_pet_bottle",     "confidence": 0.87 },
      { "class": "plastic_hdpe_container", "confidence": 0.09 },
      { "class": "composite_tetrapack",    "confidence": 0.04 }
    ],
    "material": {
      "name": "PET Plastic Bottle",
      "category": "plastic",
      "disposal_bin": "dry",
      "recovery_potential": "high",
      "next_life": "Recycled into polyester fibre or new PET bottles",
      "recovery_channel": "informal_sector",
      "contamination_notes": "Rinse and crush before disposal. Remove cap."
    },
    "guidance": {
      "bin_label": "Blue Dry Waste Bin",
      "action": "Rinse, crush, and place in the dry waste bin.",
      "do":     ["Rinse out residue", "Remove the plastic cap", "Crush to save space"],
      "do_not": ["Do not include if contaminated with food", "Do not mix with wet waste"]
    }
  },
  "meta": { "model_version": "yolo26n-cls-v1" }
}
```

**Confidence thresholds**

| Score | Label | UI treatment |
|---|---|---|
| ≥ 0.80 | `high` | Show result directly |
| 0.55 – 0.79 | `medium` | Show with confirmation prompt |
| < 0.55 | `low` | Show top-3 alternatives; prompt correction |

**Error codes**

| Code | Condition |
|---|---|
| `INVALID_INPUT` | Neither image nor description provided |
| `IMAGE_TOO_LARGE` | Decoded image exceeds 5 MB |
| `UNSUPPORTED_FORMAT` | Format is not JPEG, PNG, or WebP |
| `INFERENCE_FAILED` | Model returned no usable result |
| `WARD_UNKNOWN` | `ward_id` not found in lookup table |

---

### 6.2 POST /api/v1/feedback

**Auth:** None required.

**Request**
```json
{
  "event_id": "uuid",
  "session_id": "uuid",
  "feedback_type": "correction | confirmation",
  "corrected_class": "material_id | null",
  "note": "string | null"
}
```

**Validation**
- `corrected_class` required when `feedback_type == "correction"`
- `corrected_class` must be a known `material_id`
- `event_id` must reference an existing event owned by the same `session_id`
- Rate limit: max 10 feedback submissions per session per hour (enforced via Redis counter)

**Response 200**
```json
{
  "status": "ok",
  "data": { "correction_id": "uuid", "acknowledged": true }
}
```

---

### 6.3 GET /api/v1/analytics/ward/{ward_id}

**Auth required:** `society_manager`, `operator`, `municipal`, `admin`

**Query params**
- `date_from` — ISO date, required
- `date_to` — ISO date, required; max range 90 days
- `aggregation` — `day | week | month`; default `day`

**Response 200**
```json
{
  "status": "ok",
  "data": {
    "ward_id": "WD-001",
    "period": { "from": "2026-09-01", "to": "2026-09-30" },
    "demo_data": true,
    "summary": {
      "total_events": 1423,
      "correction_rate": 0.12,
      "contamination_rate": 0.18,
      "recovery_potential_avg": 0.74,
      "low_confidence_rate": 0.09
    },
    "timeseries": [
      {
        "date": "2026-09-01",
        "total_events": 47,
        "correction_rate": 0.10,
        "contamination_rate": 0.21,
        "recovery_potential_avg": 0.71
      }
    ],
    "material_breakdown": {
      "plastic": 0.38, "paper": 0.22, "organic": 0.19,
      "glass": 0.08, "metal": 0.07, "other": 0.06
    },
    "top_misclassifications": [
      { "predicted": "composite_tetrapack", "corrected": "plastic_pet_bottle", "count": 23 }
    ]
  }
}
```

---

### 6.4 GET /api/v1/analytics/overview

**Auth:** Anonymous allowed; role determines data resolution (anonymous receives city-level only).

Returns platform-wide summary. Shape mirrors ward analytics summary block without `ward_id` or `timeseries`.

---

### 6.5 GET /api/v1/materials

**Auth:** None required.

Returns full materials taxonomy as a flat list. Used by the frontend for correction picker and disposal guidance rendering. Cached with a long TTL (24 hours).

---

### 6.6 GET /api/v1/health

```json
{
  "status": "ok",
  "components": {
    "database":        "ok | degraded | unavailable",
    "inference_engine":"ok | unavailable",
    "cache":           "ok | degraded | unavailable",
    "image_store":     "ok | unconfigured"
  },
  "model_version": "yolo26n-cls-v1",
  "inference_error": null
}
```

When the ONNX model failed to load, `components.inference_engine` is
`"unavailable"`, top-level `status` is `"degraded"`, `inference_error` carries
the plain-language cause, and `POST /api/v1/classify` returns
`503 INFERENCE_NOT_CONFIGURED`.

---

## 7. ML Inference Architecture

### 7.1 Operational mode

There is a single operational mode. ONNX inference is the only classification
path — no demo or mock simulator exists, and no fallback can answer a request
when the model is unavailable.

- Loads YOLO26 weights in ONNX format (default `yolo26n-cls-v1`); if the file
  is missing, corrupt or incompatible the API still starts, `/health` reports
  `inference_engine: "unavailable"` and `status: "degraded"`, and
  `POST /classify` returns an explicit `503 INFERENCE_NOT_CONFIGURED`
- Preprocessing: decode → validate format → resize to model input dimensions →
  divide by 255 (no ImageNet mean/std — matches the reference transform)
- ONNX inference with a 5-second hard timeout; exceeded → `INFERENCE_FAILED`
- Maps class index to `material_id` using a class-index mapping file (must be
  verified against actual model)
- Output is consumed as a probability distribution — never re-softmaxed

### 7.2 Preprocessing pipeline

```
Input bytes
  → Decode base64
  → Validate format (JPEG / PNG / WebP)
  → Validate size (≤ 5 MB)
  → Open with PIL
  → Resize to [640, 640]  ← ASSUMED; verify from ONNX model metadata
  → Normalise: pixel / 255.0 → mean=[0.485,0.456,0.406], std=[0.229,0.224,0.225]  ← ASSUMED
  → Convert to numpy float32 array [1, 3, 640, 640]
  → ONNX run → output tensor
  → Parse class index + confidence
  → Map index to material_id
  → Return ClassificationResult
```

### 7.3 Critical assumptions pending verification

| # | Assumption | Required action when weights available |
|---|---|---|
| A1 | Model input dimensions are 640×640 | Read from ONNX model metadata |
| A2 | Output is class-confidence pairs | Verify output tensor shape and interpretation |
| A3 | Class labels match materials taxonomy | Cross-reference class-index mapping against `materials` table |
| A4 | Confidence values are normalised 0–1 after softmax | Verify — may require explicit softmax post-processing |
| A5 | "YOLO26" refers to a YOLO-architecture model in ONNX format | Confirm model architecture and export format |

---

## 8. Privacy and Consent Architecture

| Data type | Default behaviour | Opt-in required |
|---|---|---|
| Classification result | Recorded anonymously | No |
| Session ID | Ephemeral UUID per browser session | No |
| Ward ID (coarse) | Recorded only if user supplies it | No (but user must actively provide) |
| Raw GPS coordinates | **Never collected under any circumstances** | N/A |
| Uploaded image (bytes) | Processed in memory; discarded immediately | Yes — explicit `consent.image_upload: true` per event |
| User account linkage | Not linked | Yes — user registration |
| Analytics aggregation | Anonymous event data only | No |

**Consent flags are stored per classification event**, not as a global user setting. Consent can vary between sessions and contexts.

**Image handling rule:** Images received by the API are decoded and preprocessed in memory. If `consent.image_upload` is not explicitly `true`, the image bytes are never written to disk, logged, or sent to S3 under any code path. This must be enforced in the inference service, not left to a downstream check.

**Corrections are training signals, not ground truth.** The `UserCorrection` table records what the resident believes the correct classification is. It is not a verified fact about real-world waste composition. A correction must pass human review (`reviewed = true`) before it may be used in any training dataset export.

---

## 9. Inference Availability Strategy

There is no demo mode. ONNX inference is the only classification path, so the
question at startup is only ever "did the model load?".

### Loading
- `MODEL_PATH` / `CLASS_INDEX_MAP` default to the approved artefacts in
  `ml/models/`; deployments override them via environment variables
- The classifier is loaded once at startup and cached, so readiness has a
  stable answer rather than being re-probed per request

### When the model cannot be loaded
- The API still starts (a crash loop would hide the cause) and logs a clear
  startup error
- `GET /health` reports `status: "degraded"` and
  `components.inference_engine: "unavailable"` — never a hardcoded "ok"
- `POST /classify` returns `503 INFERENCE_NOT_CONFIGURED` with a plain-language
  message. **No result is ever fabricated, and no simulator can answer.**
- The frontend shows "Image classification is temporarily unavailable. Please
  check the server and try again." — never an "unknown item" prediction

### Distinction: unknown answer vs. outage
- A **genuine low-confidence answer** is a normal `200` whose
  `predicted_class` is `"unknown"`, with `confidence_label: "low"` and
  manual-review guidance plus the runner-up materials to pick from
- A **service error** is a non-200 with `error.code` `INFERENCE_FAILED` (500)
  or `INFERENCE_NOT_CONFIGURED` (503) and `data: null`
- These two are never conflated: an outage cannot surface as "unknown", and a
  low-confidence answer is not reported as an outage

### Seeded analytics data (separate concern)
- 30 days of synthetic ward analytics for 3 named demo wards
- Narrative structure:
  - **Ward A:** Improving contamination trend — model learning effect
  - **Ward B:** Mid-period contamination spike — realistic operational event
  - **Ward C:** Consistently high recovery potential — good-segregation reference
- Responses carry `demo_data: true` when the rollups came from the seed
  generator rather than the database, so analytics provenance stays honest

---

## 10. Analytics Architecture

### 10.1 Aggregation pipeline

```
ClassificationEvent written to DB
  → Celery task: aggregate_ward_day(ward_id, date)
  → Upsert WardAnalyticsRollup for (ward_id, date)
  → Invalidate Redis cache keys for affected ward/period
  
Nightly Celery beat task:
  → Recompute previous day's rollup for all active wards
  → Ensures eventual consistency even if async tasks were missed
```

### 10.2 Computed metrics

| Metric | Formula |
|---|---|
| Correction rate | `corrections / total_events` |
| Contamination rate | `events where recovery_potential ∈ {low, none} / total_events` |
| Recovery potential avg | `mean({high:1.0, medium:0.6, low:0.2, none:0.0}[recovery_potential])` |
| Low-confidence rate | `events where confidence < 0.55 / total_events` |
| Material breakdown | Category distribution as proportion of total events |
| Top misclassifications | `(predicted, corrected)` pairs sorted by count, top 10 |

### 10.3 Honesty requirements for analytics

Every displayed metric must be accompanied by a brief description of what it actually measures. The following claims must never appear in the UI:

- ❌ "Contamination rate" measured as physical bin contamination
- ❌ "Correction rate" used as a model accuracy benchmark
- ❌ "Recovery potential" described as actual recovery outcomes
- ❌ Any efficiency or impact figure not derived from verified data

These metrics describe **classification behaviour at the point of disposal** as recorded through the platform, not ground-truth waste-stream measurements.

---

## 11. Infrastructure

## 11. Infrastructure and Deployment Strategy

### 11.1 Overview & Architecture Topology
LoopWise supports two distinct operational environments: a **Local Development Environment** (using Docker Compose for rapid iteration and testing) and an **AWS Production Target Architecture** (leveraging managed cloud services in `ap-south-1`). Local containers allow developers to build and test features offline, while AWS managed services provide the secure, scalable infrastructure for production deployment.

---

### 11.2 Local Development Environment (Docker Compose)
The local development setup uses Docker Compose to run the full application stack on a developer's machine without cloud dependencies.

**Local Stack Components:**
- `api`: FastAPI backend running via Uvicorn with hot-reload enabled on port 8000.
- `worker`: Celery worker running background aggregation tasks (built from `backend/Dockerfile`).
- `db`: PostgreSQL 16 Alpine container on port 5432 with persistent volume (`postgres_data`).
- `cache`: Redis 7 Alpine container on port 6379 with persistent volume (`redis_data`) for analytics caching and Celery task broker.
- `frontend`: Node 22 + Vite development server running on port 5173.

**Local Development Prerequisites:**
- Local tools required: Docker Desktop (with Docker Compose v2+), Python 3.12+, Node.js 22+.
- **Zero Cloud Credentials Required:** Local development runs the real ONNX
  classifier against the checked-in artefacts in `ml/models/` — no AWS
  credentials and no internet connection are needed. Only image uploads stored
  with explicit consent require S3 in production.
- **Scope Isolation:** Local containers are strictly for local development and testing; they do NOT represent or replace the AWS cloud deployment topology.

---

### 11.3 AWS Production Target Architecture
The production cloud deployment maps LoopWise components onto AWS managed services in the `ap-south-1` (Mumbai) region for high availability, security, and operational simplicity.

**AWS Managed Service Mapping:**
| Component | AWS Service | Architecture & Security Specifications |
|---|---|---|
| **API & Worker** | ECS Fargate | Dual container task definitions running in private subnets behind an Application Load Balancer (ALB). Managed via ECS Task Execution and Task Roles. |
| **Database** | Amazon RDS for PostgreSQL 16 | Primary relational datastore for events, materials, corrections, and analytics rollups. Encrypted at rest (AWS KMS). Provisioned in private database subnets; **never publicly accessible**. |
| **Cache & Task Broker** | Amazon ElastiCache for Redis 7 | Managed Redis cluster for analytics query caching, rate-limiting, and Celery task broker. Provisioned in private subnets; **never publicly accessible**. |
| **Image & Data Storage** | Amazon S3 | Private bucket (`loopwise-media-storage-*`) for consent-gated image uploads and training dataset exports. Configured with Block Public Access enabled and SSE-S3 encryption. |
| **Frontend CDN** | Amazon CloudFront | Global Edge CDN delivering static React frontend assets from S3 with HTTPS enforced via AWS Certificate Manager (ACM). |
| **Secrets & Config** | AWS Secrets Manager | Centralized, encrypted secret storage for `DATABASE_URL`, `REDIS_URL`, `SECRET_KEY`, and runtime configurations. Injected into ECS container environments at startup. |
| **Network & Isolation** | AWS VPC & Security Groups | Custom VPC (`10.0.0.0/16`) spanning 2 Availability Zones in `ap-south-1` with public and private subnets. Security Groups enforce strict least-privilege network access. |
| **Identity & IAM** | AWS IAM | Dedicated IAM Deployment User (`loopwise-deployer`) for CLI administration, separate ECS Task Execution Role (`ecsTaskExecutionRole`), and ECS Task Role (`loopwise-task-role`). |

**Network Dependencies & Security Isolation:**
- **Private Network Access:** RDS PostgreSQL (port 5432) and ElastiCache Redis (port 6379) reside strictly in private subnets with no public IP addresses. Inbound network rules explicitly restrict access ONLY to the ECS Task Security Group (`ecs-task-sg`).
- **Outbound Connectivity:** ECS Fargate tasks in private subnets access external services and AWS endpoints (S3, Secrets Manager, ECR, CloudWatch) via NAT Gateway or VPC Endpoints.

---

### 11.4 Staged AWS Provisioning Sequence
Resource creation follows a strict dependency order. Infrastructure must be provisioned stage-by-stage only after manual preflight checks and explicit user approval.

1. **Stage 1: Identity & Security Verification**
   - Verify identity using `aws sts get-caller-identity --profile personal`. If the caller identity is the AWS root user, flag the risk and create a dedicated non-root IAM deployment user (`loopwise-deployer`) with least-privilege permissions.
   - Confirm target region is explicitly `ap-south-1`.

2. **Stage 2: Billing & Budget Safeguards**
   - Create AWS Budget and CloudWatch billing alerts in `us-east-1` (the global billing region) to monitor credit consumption and prevent unexpected costs.
   - *Note:* Budget alerts are notification triggers, not hard spending caps. Credits reduce out-of-pocket costs but do not eliminate billing responsibility.

3. **Stage 3: Private S3 Storage Provisioning**
   - Create private S3 bucket (`loopwise-media-storage-ap-south-1-<account_id>`) in `ap-south-1`.
   - Enable Block Public Access (all 4 settings true) and default Server-Side Encryption (SSE-S3).

4. **Stage 4: VPC & Network Security Provisioning**
   - Create custom VPC (`10.0.0.0/16`), 2 public subnets, 2 private subnets, Internet Gateway, and NAT Gateway.
   - Configure Security Groups: `alb-sg`, `ecs-task-sg`, `rds-sg` (allows 5432 from `ecs-task-sg`), `redis-sg` (allows 6379 from `ecs-task-sg`).

5. **Stage 5: Data & Cache Infrastructure Provisioning**
   - Provision RDS PostgreSQL 16 DB instance in private subnets (`db.t4g.micro` for dev/staging).
   - Provision ElastiCache Redis 7 cluster in private subnets (`cache.t4g.micro`).
   - Store connection strings securely in AWS Secrets Manager (`loopwise/production/secrets`).

6. **Stage 6: ECS Fargate Application Deployment**
   - Create ECR repository, build backend Docker image, tag, and push.
   - Define ECS Task Definition referencing Secrets Manager for `DATABASE_URL` and `REDIS_URL`.
   - Launch ECS Fargate API Service and Celery Worker Service in private subnets attached to ALB.

7. **Stage 7: CloudFront Frontend Distribution**
   - Build frontend React SPA (`npm run build`).
   - Upload build artifacts to S3 bucket for web hosting (`loopwise-frontend-hosting-*`).
   - Deploy CloudFront distribution with HTTPS, pointing API requests `/api/*` to the ALB endpoint and all other routes to S3 SPA fallback.

8. **Stage 8: Post-Deployment Verification**
   - Test `/api/v1/health` endpoint on live domain. Confirm DB, Redis, and Inference status.
   - Execute database migration (`alembic upgrade head`) via ECS task or ephemeral container.
   - Verify zero PII in CloudWatch logs.

---

### 11.5 Security & Secrets Governance Rules
- **No Hardcoded Secrets:** AWS credentials, secret keys, database passwords, or session tokens MUST NEVER be stored in git repositories, `.env.example` files, source code, or Markdown documentation.
- **Explicit CLI Profile Usage:** All AWS CLI commands and administrative scripts MUST explicitly append `--profile personal` and `--region ap-south-1`. Never rely on default profiles.
- **Runtime IAM Authorization:** Deployed ECS tasks MUST authenticate to AWS S3 and Secrets Manager using assigned IAM Task Roles (`loopwise-task-role`), never static AWS access keys.
- **Root User Isolation:** AWS Root account credentials must only be used to create initial non-root IAM administrative users. All deployment operations must execute under the dedicated `loopwise-deployer` IAM identity.

---

## 12. Testing Strategy

| Layer | Approach |
|---|---|
| Backend unit | pytest; ONNX inference path with a real session, validation, data model constraints |
| Backend integration | pytest + AsyncClient + isolated test database; classify → feedback → analytics chain |
| Frontend unit | Vitest + Testing Library; component states, confidence display, correction flow |
| Frontend E2E | Playwright; resident classification flow, analytics navigation at key breakpoints |
| API contract | Responses validated against OpenAPI schema in CI |
| Visual regression | Playwright screenshots at 375px / 768px / 1280px for all key screens |
| Analytics correctness | Seed known data; verify rollup computation output exactly |

---

## 13. Observability

- Structured JSON logs on every request: `request_id`, `session_id` (hashed), `model_version`, `latency_ms`, `error_code`
- Key metrics: inference latency p50/p95/p99, correction rate trend, error rate by code, Celery task queue depth
- Health endpoint for uptime monitoring
- CloudWatch Log Groups: `/ecs/loopwise-api` and `/ecs/loopwise-worker` in `ap-south-1`
- **No PII in any log:** no email addresses, no image data, no coordinates

---

## 14. Repository Layout

```
/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── routers/        classify.py, feedback.py, analytics.py, health.py
│   │   │   └── schemas/        classify.py, feedback.py, analytics.py
│   │   ├── models/             events.py, corrections.py, materials.py, analytics.py, users.py
│   │   ├── services/
│   │   │   └── inference/      base.py, mock.py, onnx_classifier.py, factory.py, result.py
│   │   ├── analytics/          aggregator.py, tasks.py
│   │   ├── core/               config.py, response.py, errors.py, security.py
│   │   └── seeds/              materials.py, demo_analytics.py
│   ├── tests/
│   ├── alembic/
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── hooks/
│   │   ├── api/                client.ts
│   │   └── design-system/      tokens.css, typography.ts, components/
│   └── package.json
├── docs/
│   ├── architecture.md         ← this file
│   ├── design.md
│   └── prompts.md
├── docker-compose.yml
└── .env.example
```

---

## 15. Key Decisions and Rationale

| Decision | Rationale |
|---|---|
| FastAPI over Django/Flask | Native async support; auto-generated OpenAPI docs; natural fit for ML service integration |
| ONNX Runtime over live PyTorch | Smaller deployment footprint; faster cold start; portable across runtimes |
| ONNX-only inference path | A simulated classifier must never be answerable; a real low-confidence answer is honest, a fabricated one is not |
| Ward-level geography only | Privacy by design; GPS is unnecessary and creates data risk; ward granularity is sufficient for analytics |
| Pre-aggregated rollups | Analytics read paths must be cheap and predictable; recomputing on demand is not acceptable at scale |
| Consent per classification event | A user may consent to image upload for one session and not another; global flags are insufficient |
| Corrections are training signals | Treating corrections as ground truth would inflate confidence in unverified data; human review required |
| Seed data narratively structured | Demo must tell a coherent story; random synthetic data is not demonstrable |
| Staged AWS provisioning | Avoids surprise costs, isolates networking security, ensures non-root IAM deployment safety |

---

## 16. Environment Variables (.env.example)

```bash
# Runtime mode
ENVIRONMENT=development

# Database Configuration
# Local Docker Compose default:
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/loopwise
# AWS Deployed Note: Passed via AWS Secrets Manager (loopwise/production/secrets) to ECS tasks.

# Cache / Celery Configuration
# Local Docker Compose default:
REDIS_URL=redis://localhost:6379/0
# AWS Deployed Note: Passed via AWS Secrets Manager to ECS tasks.

# ML Model Configuration
MODEL_PATH=          # optional; defaults to ml/models/loopwise-yolo26n-cls.onnx
CLASS_INDEX_MAP=     # optional; defaults to ml/models/loopwise-yolo26n-cls.class-index-map.json

# Storage & AWS CLI Operator Settings
# Note: Operators use --profile personal for CLI commands. Deployed ECS tasks use IAM Task Roles.
AWS_REGION=ap-south-1
AWS_PROFILE=personal # Operator CLI default; DO NOT hardcode credentials in code or files
S3_BUCKET=           # Private bucket name (e.g. loopwise-media-storage-ap-south-1-123456789012)

# Security Configuration
SECRET_KEY=          # JWT signing secret — generate with: openssl rand -hex 32
ACCESS_TOKEN_EXPIRE_MINUTES=480

# Frontend Configuration
VITE_API_BASE_URL=http://localhost:8000
```

---

## 17. Unresolved Questions

| # | Question | Blocking what |
|---|---|---|
| U1 | YOLO26 model input dimensions and output tensor format | Production inference |
| U2 | Actual model class labels — must be cross-referenced against material taxonomy | Production inference + material mapping |
| U3 | Source and format of ward boundary data for Indian cities (GeoJSON? lookup table?) | Geographic features |
| U4 | Authentication provider — self-issued JWT vs. external IdP (Cognito, Auth0) | Analytics access control |
| U5 | Minimum material taxonomy class count for a credible MVP demo | Seed data scope |
| U6 | Whether society manager scope is a separate role or a ward-scoped municipal view | Role and access model |
| U7 | Celery broker in production — Redis (already present) vs. SQS | Production deployment |
| U8 | Image preprocessing normalisation parameters specific to YOLO26 | Production inference correctness |
| U9 | Specific subnet CIDR mapping and domain ACM certificate ARN for AWS production | CloudFront & Custom Domain setup |

