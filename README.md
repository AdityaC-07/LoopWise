# LoopWise — Waste Segregation Intelligence Platform

A circular-economy platform that helps residents classify waste correctly at the
point of disposal, collects correction-aware model feedback, and provides
ward-level analytics to society managers, waste-recovery operators, and
municipal decision-makers.

LoopWise runs an **8-class image classifier** (YOLO26n-cls, exported to ONNX)
behind a **FastAPI** backend, with a **React + TypeScript + Vite** frontend.
Inference has two first-class modes: an honest, clearly-labelled **demo (mock)**
mode, and a genuine **ONNX production** mode.

> **Status:** the classifier is trained, exported, and wired into the backend.
> The deployed ONNX output contract and preprocessing were corrected and
> verified (see [ML Pipeline](#ml-pipeline) → [Evaluation](#evaluation--verified-metrics)
> and [ONNX output contract](#onnx-output-contract)). The backend still defaults
> to **demo mode** until `MODEL_PATH`/`CLASS_INDEX_MAP` are set and
> `DEMO_MODE=false` (`yolo26n-cls-v1`).

---

## Repository layout

```
LoopWise/
├── backend/          FastAPI + SQLAlchemy (Python 3.12)
│   ├── app/
│   │   ├── api/          API routers and schemas
│   │   ├── core/         config, errors, response helpers
│   │   ├── models/       SQLAlchemy ORM models (async)
│   │   ├── services/     inference, storage, analytics
│   │   └── seeds/        database seed data
│   ├── alembic/          database migrations
│   └── tests/            backend tests
├── frontend/         React 19 + TypeScript + Vite
│   ├── src/              api, components, pages, types, utils
│   └── package.json
├── ml/               Model pipeline (dataset prep, training, export, eval)
│   ├── classes.json      canonical index → class name (single source of truth)
│   ├── data.yaml         canonical dataset config (same order as classes.json)
│   ├── prepare_dataset.py / validate_dataset.py / train.py / export_onnx.py / evaluate.py
│   └── tests/            ML pytest suite
├── docs/             architecture.md · design.md · deployment.md · prompts.md
├── .env.example      environment variable template
└── LICENSE
```

**Deep-dive docs:** [Architecture](docs/architecture.md) ·
[Design spec](docs/design.md) · [Deployment](docs/deployment.md).

---

## Tech stack

| Layer | Technology |
|---|---|
| Backend | FastAPI, Uvicorn, SQLAlchemy 2 (async), Alembic, Pydantic |
| Frontend | React 19, TypeScript 6, Vite 8, Tailwind CSS 4, React Router, Recharts, Vitest + Testing Library, oxlint |
| ML | Ultralytics YOLO26n-cls, PyTorch, ONNX Runtime (`onnxruntime`), Pillow, NumPy |
| Data (local) | SQLite (`aiosqlite`) for development |
| Data (prod) | PostgreSQL (`asyncpg`), Redis, AWS S3 |
| Deploy | Docker, nginx; AWS ECS Fargate / RDS / ElastiCache / S3 / CloudFront |

---

## Backend (FastAPI)

### Local development

```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000   # http://localhost:8000
```

### Tests

```powershell
cd backend
pytest
pytest --cov=app --cov-report=html
```

### API contract

- **Base URL:** `/api/v1/`
- **Response envelope:** `{ "status", "data", "error", "meta" }`; `meta` carries
  `request_id`, `model_version`, and `demo_mode`.
- **Errors** use plain language for user-facing messages.

| Endpoint | Purpose |
|---|---|
| `POST /api/v1/classify` | Classify waste (image and/or description), return guidance + top-3 |
| `POST /api/v1/feedback` | Submit a correction / confirmation for an event |
| `GET  /api/v1/analytics/ward/{ward_id}` | Ward-level analytics for a period |
| `GET  /api/v1/analytics/*` | Society / operator / municipal rollups |
| `GET  /api/v1/materials` | Static material taxonomy for the UI |
| `GET  /api/v1/health` | Component health + model/demo status |

**Confidence labels (UI):** ≥ 0.80 `high` · 0.55–0.79 `medium` · < 0.55 `low`
(show top-3 and prompt correction). Low-confidence and unmapped predictions
return a safe `unknown` result — never a fabricated material.

### Database abstraction

- **SQLite for local dev:** `aiosqlite`, UUIDs stored as `String(36)`, Alembic
  batch mode enabled for SQLite compatibility.
- **PostgreSQL for production:** `asyncpg`, native UUID types.

### Image upload validation

- Max size 5 MB; JPEG / PNG / WebP only (validated via magic bytes).
- Images are only stored when `consent.image_upload = true`; otherwise bytes are
  processed in memory only. Storage is S3 in production; discarded locally.

### CORS

Configured via `CORS_ORIGINS` (default:
`http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173`).

---

## Frontend (React + TypeScript + Vite)

Minimal Vite setup with HMR. The stack is: React 19, TypeScript, Vite,
Tailwind CSS 4 (`@tailwindcss/vite`), and the [Oxc](https://oxc.rs)-based
`@vitejs/plugin-react`.

### Commands

```powershell
cd frontend
npm install

npm run dev          # dev server (http://localhost:5173)
npm run build        # tsc -b && vite build
npm run lint         # oxlint
npm run preview      # preview production build
npm run test         # vitest run
npm run test:watch   # vitest (watch)
```

### Notes

- **React Compiler** is not enabled (its effect on dev/build performance); enable
  per the [React docs](https://react.dev/learn/react-compiler/installation) if needed.
- For stricter **oxlint** type-aware rules, install `oxlint-tsgolint` and add to
  `.oxlintrc.json`:

  ```json
  {
    "$schema": "./node_modules/oxlint/configuration_schema.json",
    "plugins": ["react", "typescript", "oxc"],
    "options": { "typeAware": true },
    "rules": {
      "react/rules-of-hooks": "error"
    }
  }
  ```

### Design

The UI follows the approved **Material Flows** direction (see
[`docs/design.md`](docs/design.md) — authoritative visual/UX spec). Every screen
must be understandable by a ward sanitation officer in under 5 seconds without
training. Preserve the React + TypeScript + Vite stack and the Material Flows
design.

---

## ML pipeline

> Model pipeline lives in `ml/`. The pipeline is isolated to its own virtual
> environment (`ml/.venv`) and never pollutes the backend environment.
> **Do not retrain, modify weights, change preprocessing logic, or alter the
> inference architecture without explicit approval.**

### Taxonomy — 8 broad material classes

The model classifies **whole images into 8 broad material categories**. It does
**not** identify subtypes (PET vs HDPE, AA vs lithium, glass colour, exact
e-waste). Names are in **alphabetical order on purpose**: Ultralytics derives
classification class indices by sorting folder names, so `classes.json`,
`data.yaml`, the folder layout, and the exported `CLASS_INDEX_MAP` agree by
construction.

| idx | class | model meaning |
|---|---|---|
| 0 | `battery_hazardous` | batteries / household hazardous items |
| 1 | `glass` | glass containers (all colours) |
| 2 | `metal` | metal packaging (all types) |
| 3 | `organic` | food & garden waste |
| 4 | `other_residue` | mixed residual waste |
| 5 | `paper_cardboard` | paper & cardboard |
| 6 | `plastic` | plastic packaging |
| 7 | `textile` | clothes, shoes, fabric |

The backend renders guidance for these through
`backend/app/services/inference/broad_classes.py` (honest, subtype-free copy).
If a predicted class is neither in that layer nor the demo pool, the result is
`unknown` with safe "check local rules" guidance. A missing `CLASS_INDEX_MAP`
makes **every** prediction `unknown` (fail-safe, never guesses).

### Dataset provenance

- **Source:** Kaggle "Garbage Classification (12 classes)" — 15,515 JPEGs,
  read-only at `ml/data/raw/`.
- **Prepared dataset:** `ml/data/waste-classify/` — validated 8-class split
  (7,233 images) built by `prepare_dataset.py`; `validate_dataset.py` is the
  stdlib gate (exit 2 if not ready).
- **Build choices:** exact-duplicate + perceptual (dHash) dedupe; per-class cap
  `--max-per-class 1000` for balance; deterministic 80/10/10 split (`--seed 42`);
  EXIF stripped on copy.

| class | train | val | test |
|---|---|---|---|
| battery_hazardous | 754 | 94 | 94 |
| glass | 800 | 100 | 100 |
| metal | 612 | 77 | 77 |
| organic | 788 | 98 | 98 |
| other_residue | 540 | 68 | 68 |
| paper_cardboard | 800 | 100 | 100 |
| plastic | 693 | 86 | 86 |
| textile | 800 | 100 | 100 |

Source → model class mapping lives in `ml/source_mapping.json`. A short
candidates comparison (TrashBox, TACO, TrashBusters) and the label-noise caveat
are documented in the ML pipeline history.

### Workflow

```powershell
# 1. Prepare the dataset (raw → deduped, split, EXIF-stripped)
ml\.venv\Scripts\python ml\prepare_dataset.py --data <raw> --out ml\data\waste-classify

# 2. Validate (exit 0 required)
ml\.venv\Scripts\python ml\validate_dataset.py --data ml\data\waste-classify

# 3. Train (seeds + deterministic + early stopping + val/test metrics)
ml\.venv\Scripts\python ml\train.py --data ml\data\waste-classify --epochs 50 --device cpu

# 4. Export + verify ONNX, write the class-index map (name order checked)
ml\.venv\Scripts\python ml\export_onnx.py --weights ml\runs\<run>\weights\best.pt `
    --out ml\models\loopwise-yolo26n-cls.onnx

# 5. Evaluate an exported ONNX against the held-out splits
ml\.venv\Scripts\python ml\evaluate.py --onnx ml\models\loopwise-yolo26n-cls.onnx ^
    --class-map ml\models\loopwise-yolo26n-cls.class-index-map.json ^
    --data ml\data\waste-classify --splits test val --preprocess ultralytics --out <run-dir>
```

`train.py` writes its own canonical `data.yaml`; `export_onnx.py` refuses to
export if the checkpoint's class-name order differs from `ml/data.yaml`.
Training packages live in `ml/requirements-ml.txt` (installed into `ml/.venv`
only — the backend environment is never touched).

### Evaluation / verified metrics

Model version **`yolo26n-cls-v1`**, exported to
`ml/models/loopwise-yolo26n-cls.onnx` with
`ml/models/loopwise-yolo26n-cls.class-index-map.json`.

| Split | top-1 | top-5 | ECE | Brier |
|---|---|---|---|---|
| test | 0.9461 | 0.9986 | 0.0309 | 0.0851 |
| val | 0.9419 | 0.9986 | 0.0292 | 0.0924 |

Metrics are **in-distribution** (single Kaggle source) and are **not** real-world
accuracy. The classifier emits an already-softmaxed `[1, 8]` probability vector.

### ONNX output contract

The exported head already contains a Softmax, so its `[1, 8]` output **is** a
probability distribution (finite, within `[0, 1]`, sums to 1). The backend must
**not** softmax it again — doing so caps the maximum confidence at
`e / (e + 7) ≈ 0.28`, below `LOW_CONFIDENCE_THRESHOLD = 0.35`, forcing every
prediction to `unknown`.

- Default semantics is `probabilities`: output is validated (finite,
  non-negative, sum ≈ 1 within a 0.02 tolerance) and used **directly**.
- A genuinely different model that returns raw logits must opt in with
  `MODEL_OUTPUT=logits`; the classifier never guesses and never softmaxes twice.
- Malformed output (wrong shape/class count, NaN/inf, negatives, bad sum) is
  rejected as an honest `INFERENCE_FAILED` — never a fabricated prediction.

**Preprocessing** (`backend/app/services/inference/preprocess.py`, Pillow +
NumPy only) replicates the reference transform exactly: shortest-edge BILINEAR
resize → centre crop → `/255` (**no ImageNet mean/std**). `ml/evaluate.py
--preprocess backend` imports this same module, so backend inference and
evaluation cannot drift.

### Backend production wiring

After export, place the ONNX + class-index map on the server, install
`onnxruntime` + `numpy` in the backend env, and set:

```
MODEL_PATH=<abs path>/loopwise-yolo26n-cls.onnx
CLASS_INDEX_MAP=<abs path>/loopwise-yolo26n-cls.class-index-map.json
MODEL_VERSION=yolo26n-cls-v1
MODEL_OUTPUT=probabilities
DEMO_MODE=false
```

### Honest limitations

- Outputs are **broad material classes only** — the app never claims PET/AA/
  aluminium/charger specifics.
- Metrics are **in-distribution**; real-world accuracy is unmeasured.
- Source label noise (and flagged cross-class perceptual-hash groups) may cap
  accuracy; the `other_residue` (`trash` → other) class is the hardest.
- The 0.35 threshold cannot filter the model's confidently-wrong predictions;
  mid-range confidence is over-confident.
- CPU-only training on a dev machine is slow; a GPU (e.g. Colab T4) is recommended.

### Privacy & safety

- Raw images are never modified; prepared copies are EXIF-stripped.
- No user photos are uploaded or trained on without consent.
- No cloud deployment; the model runs locally in the backend's ONNX runtime.
- Low-confidence (`< LOW_CONFIDENCE_THRESHOLD = 0.35`) and unmapped classes
  return the safe `unknown` result.
- Corrections are **training signals, not ground truth**; human review
  (`reviewed = true`) is required before any retraining use.

---

## Configuration

Copy `.env.example` to `.env` and fill in values. Key variables:

```bash
DEMO_MODE=true                 # true → mock mode; false + MODEL_PATH → production
ENVIRONMENT=development

DATABASE_URL=sqlite+aiosqlite:///./loopwise.db   # prod: postgresql+asyncpg://...
REDIS_URL=redis://localhost:6379/0

MODEL_PATH=                    # leave blank to force demo mode
CLASS_INDEX_MAP=
MODEL_VERSION=yolo26-v1
MODEL_OUTPUT=probabilities     # or "logits" for a raw-logits model
S3_BUCKET=
AWS_REGION=ap-south-1

SECRET_KEY=loopwise-development-secret-key-32-chars-minimum!
ACCESS_TOKEN_EXPIRE_MINUTES=480

CORS_ORIGINS=http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173

VITE_API_BASE_URL=http://localhost:8000
```

**Never commit** `.env` files, database files (`*.db`), model weights, or
secrets — see `.gitignore`.

---

## Demo mode

Demo mode is a **first-class operational state**, not a stopgap. It activates
with `DEMO_MODE=true` or when no model file is found at `MODEL_PATH`.

- Returns plausible mock classifications for a pool of representative items,
  tagged `demo_mode: true` in `meta`.
- Deterministic: the same input hash → the same result.
- Confidence distribution is realistic (~60% high, ~25% medium, ~15% low); top-3
  alternatives use realistic confusion pairs.
- Must **never** claim real model performance, present mock confidences as
  accuracy, or leak demo events into production analytics (filtered by
  `demo_mode`).

---

## Deployment

- **Docker images:** `backend/Dockerfile` (multi-stage, Python 3.12-slim) and
  `frontend/Dockerfile` (multi-stage, nginx:alpine).
- **AWS target:** ECS Fargate (API + Celery worker), RDS PostgreSQL 16,
  ElastiCache Redis 7, S3 (consent-gated images), CloudFront (frontend), Secrets
  Manager, in `ap-south-1`. See [docs/deployment.md](docs/deployment.md) for the
  full topology, staged provisioning, security, monitoring and rollback guide.
- **Local full stack:** Docker Compose runs `api`, `worker`, `db` (Postgres),
  `cache` (Redis) and `frontend` with no cloud credentials required.

---

## Testing

| Surface | Command |
|---|---|
| Backend | `pytest` (in `backend/`) |
| Frontend | `npm run test` (in `frontend/`) |
| ML pipeline | `pytest` (in `ml/`, using `ml/.venv`) |
| Frontend build | `npm run build` |
| Frontend lint | `npm run lint` |

Before marking a task complete, run the backend and ML suites, the frontend
build/lint, and verify API responses against the OpenAPI schema.

---

## Documentation index

| Doc | Contents |
|---|---|
| [docs/architecture.md](docs/architecture.md) | Authoritative technical reference: goals, roles, data models, API contracts, inference architecture, privacy/consent, analytics, infrastructure |
| [docs/design.md](docs/design.md) | Approved "Material Flows" visual and UX specification |
| [docs/deployment.md](docs/deployment.md) | AWS architecture, prerequisites, CI/CD, security, cost, rollback |
| [docs/prompts.md](docs/prompts.md) | Project prompt history |

---

## License & attribution

See [LICENSE](LICENSE) for the repository license. The dataset
(Kaggle "Garbage Classification", 12 classes) is used under an ODbL-style license
requiring attribution. Review the third-party licenses of the pretrained
`yolo26n-cls` weights and all dependencies before distribution.
