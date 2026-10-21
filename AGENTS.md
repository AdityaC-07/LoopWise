# LoopWise — Agent Notes

This file contains project-specific information for agents working on LoopWise.

## Project Structure

```
LoopWise/
├── backend/          # FastAPI backend (Python 3.12)
│   ├── app/
│   │   ├── api/      # API routers and schemas
│   │   ├── core/     # Config, errors, response helpers
│   │   ├── models/   # SQLAlchemy ORM models
│   │   ├── services/ # Inference, storage, analytics
│   │   └── seeds/    # Database seed data
│   ├── alembic/      # Database migrations
│   ├── tests/        # Backend tests
│   ├── requirements.txt
│   ├── pyproject.toml
│   └── Dockerfile
├── frontend/         # React + TypeScript + Vite frontend
│   ├── src/
│   │   ├── api/      # API client
│   │   ├── components/
│   │   ├── pages/
│   │   ├── types/
│   │   └── utils/
│   ├── package.json
│   ├── vite.config.ts
│   └── Dockerfile
├── ml/               # ML pipeline (Agniv's domain - DO NOT TOUCH)
├── docs/             # Architecture, design, deployment docs
└── .env.example      # Environment variables template
```

## Local Development Commands

### Backend (FastAPI)

```powershell
# Navigate to backend
cd backend

# Create virtual environment (first time only)
python -m venv .venv
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Run development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html
```

### Frontend (React + Vite)

```powershell
# Navigate to frontend
cd frontend

# Install dependencies (first time only)
npm install

# Run development server
npm run dev

# Run tests
npm run test

# Run tests in watch mode
npm run test:watch

# Lint
npm run lint

# Production build
npm run build

# Preview production build
npm run preview
```

## Database Configuration

### Local Development (SQLite)

Default configuration in `.env.example`:
```bash
DATABASE_URL=sqlite+aiosqlite:///./loopwise.db
```

### Production (PostgreSQL)

For AWS RDS deployment:
```bash
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/loopwise
```

**Important:** The codebase uses SQLite for local development with full PostgreSQL compatibility. UUIDs are stored as strings in SQLite for compatibility, but will be stored as native UUID types in PostgreSQL.

## Key Technical Decisions

### Database Abstraction

- **SQLite for local dev**: Uses `aiosqlite` driver with string-based UUIDs
- **PostgreSQL for production**: Uses `asyncpg` driver with native UUID types
- **Alembic migrations**: Batch mode enabled for SQLite compatibility
- **Models**: All UUID columns use `String(36)` with `str(uuid.uuid4())` defaults

### API Contract

- **Base URL**: `/api/v1/`
- **Response envelope**: Standardized with `status`, `data`, `error`, `meta`
- **Error handling**: Plain-language messages for all user-facing errors
- **Inference**: ONNX is the only classification path; no demo/mock mode exists. A service failure returns an explicit error, never a fabricated result

### Image Upload Validation

- **Max size**: 5 MB
- **Accepted formats**: JPEG, PNG, WebP (validated via magic bytes)
- **Consent**: Images only stored if `consent.image_upload = true`
- **Storage**: S3 in production; discarded in local dev

### CORS Configuration

- **Origins**: Configured via `CORS_ORIGINS` environment variable
- **Default**: `http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173`
- **Methods**: All methods allowed
- **Headers**: All headers allowed

## ML Integration (DO NOT MODIFY)

The ML pipeline in the `ml/` directory is Agniv's responsibility. Do not:
- Retrain the model
- Modify model weights
- Change preprocessing logic
- Alter inference architecture

## Deployment Preparation

### Docker Images

Backend and frontend have Dockerfiles ready for production:
- **Backend**: Multi-stage build with Python 3.12-slim
- **Frontend**: Multi-stage build with nginx:alpine

### Environment Variables

Required for production (see `.env.example`):
- `DATABASE_URL` (PostgreSQL)
- `REDIS_URL`
- `S3_BUCKET`
- `AWS_REGION`
- `SECRET_KEY`
- `MODEL_PATH`
- `CLASS_INDEX_MAP`

### AWS Deployment

See `docs/deployment.md` for complete AWS architecture and deployment guide.

## Verification Steps

Before marking a task complete:

1. **Backend tests**: Run `pytest` in backend directory
2. **Frontend tests**: Run `npm run test` in frontend directory
3. **Production build**: Run `npm run build` in frontend directory
4. **Lint**: Run `npm run lint` in frontend directory
5. **API audit**: Verify frontend API calls match backend schemas
6. **Classifier health**: Verify `GET /api/v1/health` reports `inference_engine: "ok"` and the top-bar status indicator shows ready

## Common Issues

### Database Migration Errors

If Alembic fails on SQLite:
```bash
# Reset database (WARNING: deletes all data)
rm backend/loopwise.db
alembic upgrade head
```

### Frontend Build Errors

If Vite build fails:
```powershell
# Clear cache and reinstall
rm -r node_modules
rm package-lock.json
npm install
npm run build
```

### CORS Errors

If frontend cannot connect to backend:
- Verify `CORS_ORIGINS` includes frontend URL
- Check backend is running on expected port (8000)
- Verify no firewall blocking connections

## Important Notes

- **Never commit**: `.env` files, database files (`*.db`), model weights, or secrets
- **Always preserve**: React + TypeScript + Vite stack, FastAPI backend, Material Flows design
- **Real inference only**: Never reintroduce a demo/mock classifier or present a simulated prediction as real
- **Privacy**: Images only stored with explicit consent; respect user consent flags
- **Error handling**: Use plain language for all user-facing errors; no technical jargon
