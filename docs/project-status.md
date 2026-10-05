# Project Status — MediSummarize AI

Last updated: 2026-10-05

## Current segment

Segments 1–11 have working code. Segment 9 now includes a generation-mode banner and a clickable evidence panel. Segment 10 has uploadable synthetic cases A–H. Segment 11 computes ROUGE, fact coverage, and citation metrics and **quarantines** mock scores. Segment 12 has API and security notes; Playwright E2E is still not added.

## Completed (tested)

| Segment | Result |
|---------|--------|
| 1 Foundation | Backend/frontend start, health/ready, CORS, Alembic. |
| 2 Auth + ownership | Register/login/JWT, record CRUD, isolation tests. |
| 3 Uploads | PDF/PNG/JPEG/text, magic-byte checks, owner-only download. |
| 4 Extraction/OCR | Text PDF, UTF-8, empty failure, mixed PDF + image OCR (Tesseract on PATH). |
| 5 Chunking/embeddings | Reproducible chunks; `test-hash-v1` test double; `hashed-token-v1` default without downloads. |
| 6 Retrieval | Per-record numpy exact cosine index. Cross-record 404. Idempotent reindex. |
| 7 Generation provider | Mock provider + OpenAI-compatible (Ollama) adapter. No silent mock fallback. `GET /api/v1/health/generation`. |
| 8 Summarization | Structured JSON, typed evidence with filenames, citation stripping. |
| 9 Reviewer UI | Login/records/upload/extract/summary; mock banner; click-to-source evidence. |
| 10 Synthetic data | Cases A–H under `data/synthetic/` with `manifest.json`. |
| 11 Evaluation | `scripts/evaluate.py` + metrics module; mock `reportable=false`. |

## Tests run (this session, actual)

Backend: `cd backend; .\.venv\Scripts\python -m pytest`

**58 passed**, 1 Starlette TestClient deprecation warning.

Frontend: `npm run test` — **6 passed**. `npm run typecheck` — passed.

Evaluation: `python ../scripts/evaluate.py` — wrote gitignored JSON/CSV; **reportable rows: 0/18** (`MOCK/TEST OUTPUT` quarantine).

Browser (localhost:5173): login showed the mock generation banner; Case E summary generated; clicking citation `255f6439` set `data-active` on the `discharge.txt` passage and opened the extracted page containing `denied chest pain`. File-chooser upload was not driven (document uploaded via API first).

Alembic head: `0006_summaries`.

## Remaining blockers

1. **PostgreSQL credentials unknown** — local `.env` uses SQLite. Switch `DATABASE_URL` for a multi-user demo.
2. **Ollama not installed** — real generation is **not** verified. Default `GENERATION_PROVIDER=mock` shows MOCK/TEST OUTPUT. Mock evaluation scores are quarantined.
3. **FAISS package not installed** — indexes use numpy exact cosine (`backend: numpy_exact`). Isolation still holds. Do not claim FAISS was run on this machine.
4. **No large embedding model downloaded** (intentional). Do not fetch MiniLM/BioBERT without stating size and license.
5. **Docker not installed.**
6. **Playwright E2E suite not added.** File-chooser upload was not driven in the browser tool.

## Current commands

```powershell
cd D:\fyp\backend
.\.venv\Scripts\python -m alembic upgrade head
.\.venv\Scripts\python -m pytest
.\.venv\Scripts\python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

cd D:\fyp\frontend
npm run dev
npm run test
npm run typecheck
```

Evaluation (mock-labeled unless you change the provider):

```powershell
cd D:\fyp\backend
.\.venv\Scripts\python ..\scripts\evaluate.py
```

OCR demo images (if missing):

```powershell
cd D:\fyp\backend
.\.venv\Scripts\python ..\data\synthetic\_render_images.py
```

## Next segment

Playwright E2E (optional), PostgreSQL credentials, and a real local generator if Ollama is installed. Do not invent evaluation numbers.

## Exact next implementation action

1. Configure Ollama or leave mock clearly labeled.
2. Switch `DATABASE_URL` to PostgreSQL when credentials are known.
3. Add Playwright coverage for login → upload → extract → generate → click citation.
4. Keep mock evaluation output quarantined until a real provider is used.
