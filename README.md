# MediSummarize AI

**Secure Clinical Document Summarization Using Retrieval-Augmented Generation (RAG)**

Final Year Project I, Fall 2026  
FAST National University of Computer and Emerging Sciences, Karachi Campus

> Research prototype for clinical-document summarization only.  
> Not for diagnosis, prescribing, treatment recommendations, or autonomous clinical decision-making.  
> Verify all generated information against the original records.

This is an academic prototype, not a production hospital system. It does not claim HIPAA certification, and it does not use real patient records.

## Current status

**9 November 2026 update:** The frontend now includes record search/sorting, responsive workspace navigation, batch uploads with partial retry, processing-state refresh, document/summary tabs, evidence/source review, text/JSON export, demo help and system status. Source changes invalidate stored summaries. The evaluation harness now performs actual chunk retrieval for its retrieved condition.

**FYP I handoff:** Start with [the submission checklist](docs/fyp-i/submission-checklist.md) and [next steps](docs/fyp-i/next-steps.md). The three supplied university templates have been populated under `output/fyp-i/`, along with an implementation defense deck. The current real-model baseline requirement remains **open**. Mock output is not evidence of model performance.

**Implemented in this repository (FYP-I prototype):**

- FastAPI health/readiness, Alembic, React shell with the required disclaimer
- Register/login (bcrypt + JWT Bearer tokens in `sessionStorage`, never in URLs)
- User-owned synthetic patient-record containers with server-side ownership checks
- PDF / PNG / JPEG / UTF-8 upload with magic-byte validation and protected storage
- Page-aware PDF extraction, Tesseract OCR fallback, extracted-text review
- Chunking, labeled test embeddings, per-record retrieval (exact cosine index)
- Structured RAG summaries with citation validation and clickable evidence
- Mock generation labeled **MOCK/TEST OUTPUT** (Ollama is not installed on the original dev machine)
- Synthetic cases A–H and an evaluation harness that quarantines mock scores

See `docs/project-status.md` for tests that were actually run.

This is not a production hospital system and not a clinically validated AI.


## Repository layout

```
backend/     FastAPI application, Alembic migrations, pytest
frontend/    React + TypeScript + Vite + Tailwind CSS
docs/        Architecture, decisions, limitations, evaluation protocol
data/        Synthetic fixtures (later) and gitignored runtime files
storage/     Protected local uploads (gitignored)
scripts/     Developer helper scripts
```

## Requirements

- Python 3.11 or newer (developed on 3.13)
- Node.js 20 or newer
- PostgreSQL 16+ **or** SQLite for first-run / tests
- Git

Optional later:

- Tesseract OCR (already useful from Segment 4; installed on the original development machine)
- Docker Compose (optional; Docker is not required)
- Ollama or another local OpenAI-compatible inference server (Segment 7)

## Quick start (Windows / PowerShell)

If the environment and dependencies below already exist, run `.\scripts\start-demo.ps1` from the repository root. It starts local services and prints their URLs without changing generation settings.

### 1. Environment file

```powershell
Copy-Item .env.example .env
```

Edit `.env`:

- Set `SECRET_KEY` to a long random string (not the example placeholder).
- Set `DATABASE_URL` to PostgreSQL if you have credentials:

  `postgresql+psycopg://USER:PASSWORD@localhost:5432/medisummarize`

- If PostgreSQL credentials are not ready, SQLite is supported for local bootstrap:

  `DATABASE_URL=sqlite:///D:/fyp/data/runtime/medisummarize.dev.db`

  Create the folder if needed: `New-Item -ItemType Directory -Force data/runtime`

Create a PostgreSQL database when you are ready:

```sql
CREATE DATABASE medisummarize;
```

### 2. Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m alembic upgrade head
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Check:

- http://127.0.0.1:8000/api/v1/health
- http://127.0.0.1:8000/api/v1/health/ready
- http://127.0.0.1:8000/docs

### 3. Frontend (second terminal)

```powershell
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 — sign in (or register), read the disclaimer and generation-mode banner.

The Vite dev server proxies `/api` to `http://127.0.0.1:8000`. You can also set `VITE_API_BASE_URL=http://127.0.0.1:8000` to call the API directly (CORS allowlist must include the frontend origin).

## Tests

Backend (from `backend/` with the venv active):

```powershell
python -m pytest
```

Frontend (from `frontend/`):

```powershell
npm run test
npm run typecheck
npm run build
```

Do not report a test as passed unless you ran it.

## Security notes

- `.env` is gitignored. Never commit secrets.
- CORS is an allowlist. Wildcards are rejected.
- Passwords are bcrypt hashes. `owner_id` is assigned from the authenticated user.
- Uploads live under `STORAGE_DIR`, not in `frontend/public` or `dist`.
- Retrieval authorizes the record first; it does not search a global index and filter afterward.
- Tokens are not placed in URLs. `sessionStorage` is XSS-vulnerable; httpOnly cookies were not used because CSRF protections are not implemented.
- Default generation is **mock** until you configure a local OpenAI-compatible server. Mock output is labeled and must not enter real evaluation metrics.

## Running a summary

1. Upload and **Extract text** (or rely on `EXTRACT_ON_UPLOAD=true` in a running server).
2. Click **Generate summary**.
3. If you see **MOCK/TEST OUTPUT**, you are not running a real language model.

To use Ollama later: install it, pull a 7–8B instruct model (check size and license first), set `GENERATION_PROVIDER=openai_compatible` and `GENERATION_MODEL` to that tag. Do not auto-download weights from this repository.

## Evaluation

```powershell
cd backend
.\.venv\Scripts\python ..\scripts\evaluate.py
```

Results go to `data/evaluation/results/` (gitignored). Mock runs set `reportable=false`. The script does not invent clinical performance claims.

## Documentation

The redesigned app includes **Experiments** for importing measured Kaggle results. The handwriting experiment files and exact next steps are in [experiments/handwriting/README.md](experiments/handwriting/README.md). Import the prepared notebook into Kaggle; its GPU training has not been run yet. A measured local Tesseract validation baseline is included as aggregate JSON and can be imported into your account.

| Document | Purpose |
|----------|---------|
| `docs/implementation-plan.md` | Segment map |
| `docs/project-status.md` | What is done, tests run, next action |
| `docs/architecture.md` | How the system is structured |
| `docs/decisions.md` | Why specific defaults were chosen |
| `docs/limitations.md` | Academic, clinical, and technical limits |
| `docs/evaluation-protocol.md` | RAG vs. non-retrieval protocol |
| `docs/demo-script.md` | 5-minute demo |
| `docs/api.md` | HTTP endpoints |
| `docs/security.md` | Ownership, isolation, defense talking points |
| `docs/fyp-ii-roadmap.md` | Deferred work |

## Team

- Muhammad Humayun Dar — baseline LM research, RAG feasibility, evaluation
- Muhammad Hamza Siddiqui — ingestion, OCR, RAG services, backend/API
- Hassan Sheikh — authentication, frontend, initial security checks
