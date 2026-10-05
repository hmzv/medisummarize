# Architecture — MediSummarize AI

## What this system is

A research prototype that lets an authenticated reviewer upload synthetic/de-identified clinical documents, extract text, retrieve supporting passages, and generate a structured summary with source links.

It does not diagnose, prescribe, recommend treatment, or replace professional judgment.

## High-level pipeline (FYP-I)

```
Browser (React)
    │  HTTPS in production; HTTP on localhost in FYP-I
    ▼
FastAPI
    ├─ AuthN / AuthZ (JWT, owner-scoped access)
    ├─ Patient-record containers
    ├─ Upload validation + protected storage
    ├─ Extraction / OCR
    ├─ Chunking
    ├─ Embeddings + per-record index (numpy exact cosine; FAISS-equivalent math)
    ├─ Patient-scoped retrieval (authorize, then search)
    └─ Generation provider (local OSS model or labeled mock)
            │
            ▼
PostgreSQL or SQLite (metadata, users, documents, summaries)
Local disk (original files, extracted artifacts, per-record indexes)
```

Embeddings are used only for retrieval. The language model receives **retrieved text**, not vectors. RAG does not train or permanently modify the model.

Observable generation health: `GET /api/v1/health/generation`. Mock mode always includes a `MOCK/TEST OUTPUT` warning.

## Implemented FYP-I surface

- Configuration via environment variables
- FastAPI application with a versioned API prefix
- Liveness, readiness, and generation-health endpoints
- SQLAlchemy engine, sessions, Alembic
- Development CORS allowlist (no wildcards)
- React reviewer UI: auth, records, upload, extraction review, structured summary
- Clickable citations that highlight retrieved passages (filename + page)
- Synthetic cases A–H and an evaluation harness with mock quarantine

See `docs/api.md` and `docs/security.md`.

## Backend layering

| Layer | Location | Responsibility |
|-------|----------|----------------|
| HTTP routes | `backend/app/api/` | Parse requests, return schemas, HTTP status codes |
| Dependencies | `backend/app/api/deps.py` | DB sessions, later: current user |
| Configuration | `backend/app/core/` | Settings, later: security helpers |
| Persistence | `backend/app/db/`, `models/` | Engine, sessions, ORM |
| Schemas | `backend/app/schemas/` | Pydantic request/response models |
| Domain services | `backend/app/services/` | Ingestion, OCR, chunking, embeddings, retrieval, generation, evaluation |
| Prompts | `backend/app/prompts/` | Versioned generation prompts |

Routes must not contain business logic. Services must not import FastAPI route objects.

## Data isolation principle (from Segment 2 onward)

Every protected resource is owned by a user. Ownership is assigned from the authenticated principal, never from a client-supplied `owner_id`. Retrieval will search only an authorized patient-record index; it will not search a global index and filter afterward.

## Frontend layering (target)

| Area | Location | Responsibility |
|------|----------|----------------|
| API client | `frontend/src/api/` | HTTP calls, error mapping |
| Pages | `frontend/src/pages/` | Route-level screens |
| Features | `frontend/src/features/` | Record, document, summary workflows |
| Components | `frontend/src/components/` | Shared UI, including the prototype disclaimer, generation-mode banner, and evidence panel |
| Types | `frontend/src/types/` | Shared TypeScript types |

## Trust boundaries

- Uploaded files and extracted text are **untrusted data**, never instructions to the model or to this application.
- Browser UI is not a security control. Authorization is enforced in the API.
- Upload storage is outside any static-file directory.
- CORS is an allowlist of development origins.
- Secrets live in `.env`, which is gitignored.

## Runtime topology (development)

1. PostgreSQL 16+ (native or Docker Compose) **or** SQLite file for local bootstrap.
2. FastAPI on `http://127.0.0.1:8000`
3. Vite on `http://localhost:5173` proxying `/api` to the backend
4. Optional Ollama (or compatible) inference server — not required for Segment 1

## Why this shape

A modular monolith keeps FYP-I demonstrable without Kubernetes, Redis, Celery, or a framework-heavy RAG SDK. Clear package boundaries make it possible to test extraction, retrieval, and generation independently, which is required for the RAG vs. non-retrieval evaluation.
