# Design Decisions — MediSummarize AI

Record significant choices, the reason, and the tradeoff. Date is the calendar day the decision was written.

## ADR-001 — Monorepo at the workspace root

**Status:** Accepted  
**Date:** 2026-10-05

The workspace `D:\fyp` was empty. The application lives at the repository root (`backend/`, `frontend/`, `docs/`) rather than a nested `medisummarize-ai/` folder, so tooling and README paths stay short.

**Tradeoff.** If this repo is later published as a nested package, paths in the README would need a one-line update.

## ADR-002 — PostgreSQL as the intended database, SQLite for tests and bootstrap

**Status:** Accepted  
**Date:** 2026-10-05

PostgreSQL matches the FYP-I default and is already installed (version 18, accepting connections on port 5432). Automated tests use SQLite so they do not require database credentials.

On this development machine, PostgreSQL is running but local credentials were not available to the agent. SQLite is therefore documented as a first-run fallback so the API can start without guessing a password.

**Tradeoff.** SQLite does not exercise PostgreSQL-specific types or concurrency. Alembic migrations must stay reasonably portable. Developers should switch `DATABASE_URL` to PostgreSQL before any multi-user demo.

## ADR-003 — Sync SQLAlchemy with FastAPI

**Status:** Accepted  
**Date:** 2026-10-05

FYP-I traffic is low. Sync sessions keep Alembic, tests, and request handlers on one programming model and avoid a second async driver stack.

**Tradeoff.** Less throughput than async ORM usage. Acceptable for a prototype.

## ADR-004 — No LangChain / LlamaIndex / Redis / Celery

**Status:** Accepted  
**Date:** 2026-10-05

The pipeline stages (ingest, extract, chunk, embed, retrieve, generate, evaluate) will be ordinary Python services. That keeps the defense explanation honest and the evaluation harness inspectable.

**Tradeoff.** More code to write than wrapping a RAG framework. Worth it for academic transparency.

## ADR-005 — Development CORS allowlist, Vite proxy

**Status:** Accepted  
**Date:** 2026-10-05

The frontend may call the API through the Vite `/api` proxy (same origin) or directly at `http://127.0.0.1:8000` if `VITE_API_BASE_URL` is set. CORS allows only configured origins. Wildcards are rejected.

**Tradeoff.** Extra configuration versus `allow_origins=["*"]`. Required for a security-aware prototype.

## ADR-006 — Do not download models in Segment 1

**Status:** Accepted  
**Date:** 2026-10-05

Embedding and generation models are large and separately licensed. Segment 1 does not fetch them. Later segments will document size, license, and destination before any download, and tests will use labeled doubles.

## ADR-007 — Docker Compose is optional

**Status:** Accepted  
**Date:** 2026-10-05

Docker is not installed on the current Windows development machine. Native PostgreSQL and native Python/Node instructions are the primary path. `docker-compose.yml` is provided for other environments.

## ADR-008 — JWT access tokens for the prototype

**Status:** Accepted  
**Date:** 2026-10-05

The prototype uses PyJWT HS256 access tokens in the `Authorization: Bearer` header. Tokens are not placed in URLs. The frontend stores the token in `sessionStorage` (cleared when the tab closes).

**XSS vs CSRF.** `sessionStorage` is readable by any JavaScript on the origin, so an XSS bug could steal the token. HttpOnly cookies would reduce XSS token theft but would require CSRF defenses (SameSite, anti-CSRF tokens) that this SPA does not yet implement. Bearer tokens avoid CSRF on cross-site form posts. Password hashing uses bcrypt, not a custom scheme.

**Tradeoff.** Tokens are not revocable until expiry (default 8 hours). Acceptable for a single-machine academic prototype.

## ADR-011 — Exact cosine index (numpy) instead of FAISS on this machine

**Status:** Accepted for FYP-I on the current Windows / Python 3.13 environment  
**Date:** 2026-10-05

Indexes are **per patient record**, stored under `INDEX_DIR/{record_id}/`. Search uses cosine similarity (dot product of L2-normalized vectors). Isolation is enforced by authorizing the record **before** opening that folder; there is no global search.

FAISS `IndexFlatIP` on normalized vectors is mathematically the same operation. The FAISS wheel was not installed here. Do not claim FAISS was executed in the recorded tests.

## ADR-012 — Default generation provider is mock until a local model exists

**Status:** Accepted  
**Date:** 2026-10-05

Ollama is not installed. The default `GENERATION_PROVIDER=mock` always labels output `MOCK/TEST OUTPUT` and never silently substitutes for a real model. Setting `openai_compatible` without a reachable server returns an error rather than mock text.

**Status:** Accepted  
**Date:** 2026-10-05

After upload, FastAPI `BackgroundTasks` run extraction in the same process (`EXTRACT_ON_UPLOAD=true` by default). Tests disable this and call `/extract` explicitly.

**Durability limit.** If the API process restarts during extraction, the document may remain `processing` until a reviewer clicks Extract text again. This is not a production job queue (no Celery/Redis). Acceptable for FYP-I.

**Status:** Accepted  
**Date:** 2026-10-05

If record `{id}` exists but is owned by someone else, the API returns 404, not 403. That avoids confirming that another user's opaque ID is valid. Application code filters by `owner_id`; it does not trust a client-supplied owner field.

## ADR-013 — Typed evidence passages for click-to-source review

**Status:** Accepted  
**Date:** 2026-10-05

`SummaryResponse.evidence` is a list of `EvidencePassage` objects (`id`, `document_id`, `original_filename`, `page`, `method`, `text`) instead of untyped dictionaries. The reviewer UI uses those IDs as buttons that scroll to the passage and toward the matching extracted page.

**Tradeoff.** Older stored `evidence_json` without `original_filename` would fail to load until regenerated. FYP-I has no production data to migrate.

## ADR-014 — Quarantine automatic scores from mock generation

**Status:** Accepted  
**Date:** 2026-10-05

ROUGE-1/2/L, reference-fact coverage, and citation-validity rates are implemented in `app/services/evaluation/metrics.py`. If `is_mock` is true, those numbers are stored only under `debug_scores` with `reportable: false`. They must not appear in a thesis results table as experimental findings.

**Tradeoff.** The pipeline can still be tested end-to-end without a local LLM. Real scores require `GENERATION_PROVIDER=openai_compatible` (or equivalent) and a reachable model.

