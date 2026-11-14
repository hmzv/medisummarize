# Project Status — MediSummarize AI

Last updated: 2026-11-10

## 10 November 2026 handoff

The frontend now uses the user-approved Clinical clarity design: teal navigation, Source Sans 3, a document strip, side-by-side summary/source panes, and a dedicated Experiments page. The user approved the original B layout and explicitly switched to a code-led build with the image as a visual guide. Experiment JSON import, model/split filters, run metadata, and planned-model states are implemented. Backend experiment imports are authenticated, owner-scoped, size-limited, and labeled as user-supplied measurements. Mock output cannot be imported as a real OCR run.

The checksum-verified RxHandBD v3 archive contains 5,578 readable 512×512 crops with complete labels. The reviewer accepted 50 sampled labels and inspected all eight similarity flags. The notebook applies the recorded decisions, retaining 4,012 training / 446 validation / 1,115 official test crops and excluding five training crops. No writer metadata is supplied, so writer independence is unverified. The literal archive contains 1,787 distinct label strings, differing from the publisher's described vocabulary size.

An actual Tesseract 5.3 validation run on the 446 crops measured CER 0.78659, WER 1.11310 and exact match 0.01121. These weak validation results are not final test scores or whole-page OCR performance. Aggregate results are in `experiments/handwriting/local-baseline-results.json`. The Kaggle notebook contains pretrained TrOCR comparison, three-epoch fine-tuning, validation checkpoint selection, final held-out testing, and aggregate export. **TrOCR has not been GPU-run or integrated into the app.**

Browser checks now cover login, record/summary loading, citation selection, full-source navigation, result-file chooser/import, and the empty final-test filter. Captures cover a desktop layout, the actual IAB width, and a 390px phone-width iframe. The native IAB viewport override did not resize its visible surface; phone evidence uses a real narrow iframe and viewport captures, rather than a claim of a native device test. Patient-document file upload/download still needs the full defense walkthrough; results import was driven through the browser picker.

A discovered automatic/manual extraction race is fixed with a per-record reentrant lock for this single-process prototype. This lock is not distributed; multi-worker deployment needs database/job coordination. It also rolls failed extraction transactions back before recording errors.

File-based SQLite now uses separate pooled connections rather than a global StaticPool connection; in-memory test databases retain sharing. Sixty parallel authenticated record/document/summary requests returned 200 after this correction. Final validation: **65 backend tests, 13 frontend tests and 3 handwriting metric tests pass**; frontend typecheck and production build pass; notebook JSON/Python cell syntax checked. GPU notebook execution is still pending. The frontend finish review accepted the visual direction and its scoped follow-up scored both requested fixes resolved: persisted design choice and reduced-motion source navigation. Design tokens are documented in `DESIGN.md` and `.impeccable/design.json`.

Next, run the updated Kaggle notebook and return the measured outputs for the report. Real summarization quality, neural retrieval, whole-page handwriting recognition, supervisor approval and signatures remain outstanding. The older handoffs below are historical and their test counts are superseded by this session's validation report.

## 9 November 2026 handoff

The current frontend implements workspace navigation, fictional record create/search/sort, batch upload and partial retry, processing refresh, document and summary tabs, page-text review, citation highlighting, separate source-page navigation, text/JSON export, demo help and system status. Source upload, re-extraction and deletion invalidate stored summaries; deletion removes derived page/chunk rows. The evaluation harness now uses the shared chunker and embeddings with section-query cosine retrieval instead of passing every file unchanged.

Executed checks: **60 backend tests passed**, **9 frontend tests passed**, TypeScript check passed and production build passed. The backend emits one Starlette TestClient deprecation warning. The corrected evaluation dry run produced **18 mock rows, 0 reportable**. The mechanical interface detector reported no findings. These checks establish application behavior, not clinical quality.

The supplied final-report, SRS and SDS templates are populated in `output/fyp-i/`. Project code: CS-FYP-1019. Supervisor: Dr. Muhammad Yaseen Khan. No co-supervisor. Source section structure and university branding are retained. The package includes implementation defense slides, synthetic fixtures, mock evidence and a submission checklist. Approval and signatures remain pending.

**Open FYP I criteria:** real-model paired baseline, manual desktop/mobile browser upload/download walkthrough, supervisor review and similarity/signature steps. IAB/CDP browser inspection timed out; native Windows browser automation ended because URL policy enforcement was unsupported. No browser visual sign-off is claimed.

Current default generation is mock. The embeddings are lexical hashing and the vector index uses NumPy exact cosine. Neural embeddings, clinical document classification/normalization and PostgreSQL remain gaps or unverified components. See `docs/fyp-i/next-steps.md` and `docs/fyp-i/submission-checklist.md` for the order of work.

The following record is retained as **historical evidence from 5 October 2026**. Its counts and next actions predate this update.

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
