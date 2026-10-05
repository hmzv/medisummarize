# Implementation Plan — MediSummarize AI

Secure Clinical Document Summarization Using Retrieval-Augmented Generation (RAG).

Academic prototype for FYP-I (Fall 2026). Not a production hospital system.

## Working rules

Work proceeds in numbered segments. Each segment has purpose, dependencies, and acceptance criteria. A segment is complete only when its tests have been executed and documented in `docs/project-status.md`.

Do not skip ownership checks, password hashing, safe file handling, or patient isolation. FYP-II items (LoRA, reranking, hospital integration, production key management) are documented, not built now.

## Chosen architecture (FYP-I)

Monorepo:

- `backend/` — FastAPI, SQLAlchemy, Alembic
- `frontend/` — React, TypeScript, Vite, Tailwind CSS
- `docs/` — plan, status, architecture, decisions, limitations, evaluation
- `data/synthetic/` — labeled fictional demonstration records
- `storage/` — local protected uploads (gitignored)

Datastore: PostgreSQL is the intended database. SQLite is supported for automated tests and as a documented local fallback when PostgreSQL credentials are unavailable.

Retrieval: SentenceTransformers embeddings + per-record FAISS indexes (Segment 6). Retrieved **text passages** are sent to the generator, not embedding vectors.

Generation: provider abstraction targeting a locally reachable open-source instruction model (Ollama or compatible). Tests use a labeled mock provider. Commercial APIs are not the default.

Auth: email + password, hashed with bcrypt, JWT access tokens in `sessionStorage` documented with XSS tradeoffs (Segment 2 / ADR-008).

## Segment map

| Segment | Name | Status |
|---------|------|--------|
| 1 | Foundation and runnable skeleton | Completed (tested, manually verified) |
| 2 | Authentication and record ownership | Completed (tested, manually verified) |
| 3 | Document upload and protected storage | Completed (tested, manually verified) |
| 4 | Text extraction and OCR | Completed (tested) |
| 5 | Chunking and embeddings | Completed (tested; no large model download) |
| 6 | FAISS index and isolated retrieval | Completed with numpy exact cosine (tested). FAISS package not installed on this machine. |
| 7 | Open-source model provider | Completed (mock tested; Ollama adapter untested — Ollama not installed) |
| 8 | Structured, evidence-linked summarization | Completed (tested with mock provider) |
| 9 | Frontend summary review workflow | Completed (disclaimer, mock banner, clickable evidence panel, tests) |
| 10 | Synthetic demonstration data | Completed (uploadable cases A–H + manifest) |
| 11 | Non-retrieval baseline and evaluation | Completed (ROUGE / fact coverage / citation validity; mock scores quarantined) |
| 12 | Integration, safety tests, and documentation | Partial (API + security notes, 49+ backend tests; no Playwright suite) |

## Segment 1 — Foundation

**Purpose.** Runnable backend and frontend with configuration, health checks, database wiring, CORS allowlist, Alembic, and smoke tests.

**Dependencies.** Python 3.11+, Node.js 20+, optional PostgreSQL.

**Acceptance criteria.**

- Backend starts with documented commands.
- Frontend starts with documented commands.
- Health endpoint responds successfully.
- Database connectivity can be checked.
- Configuration fails clearly when required values are missing.
- Frontend can display backend connection status.
- Smoke tests pass.
- No secrets are committed.

## Segment 2 — Authentication and record ownership

**Purpose.** Register/login, current-user endpoint, user-owned synthetic patient-record containers, ownership enforced on the server.

**Dependencies.** Segment 1.

## Segment 3 — Document upload and protected storage

**Purpose.** PDF / PNG / JPEG / UTF-8 text upload with content-based validation and ownership-checked storage.

**Dependencies.** Segment 2.

## Segment 4 — Text extraction and OCR

**Purpose.** Page-aware PDF extraction, OCR fallback for scans/images, provenance-preserving extracted text.

**Dependencies.** Segment 3. Tesseract is already installed on the development machine.

## Segment 5 — Chunking and embeddings

**Purpose.** Reproducible chunking with provenance metadata; embedding service with a deterministic test double.

**Dependencies.** Segment 4.

## Segment 6 — FAISS index and isolated retrieval

**Purpose.** Per-record indexes, authorize-then-search, deletion consistency, persistence.

**Dependencies.** Segment 5.

## Segment 7 — Open-source model provider

**Purpose.** Generation-provider abstraction, mock provider for tests, health/error handling. No automatic model downloads.

**Dependencies.** Segment 1 configuration patterns. Ollama is not currently installed; real inference is optional until configured.

## Segment 8 — Structured, evidence-linked summarization

**Purpose.** RAG summary service with section-aware retrieval, Pydantic-validated JSON, citation checks, missing-information behavior.

**Dependencies.** Segments 6 and 7.

## Segment 9 — Frontend summary review workflow

**Purpose.** End-to-end clinician-reviewer UI including disclaimer, evidence panel, and processing states.

**Dependencies.** Segments 2–8 API surface.

## Segment 10 — Synthetic demonstration data

**Purpose.** Clearly labeled fictional cases covering OCR, missing data, conflicts, negation, isolation, and prompt injection.

**Dependencies.** Useful from Segment 4 onward; finalized for evaluation.

## Segment 11 — Non-retrieval baseline and evaluation

**Purpose.** Fair RAG vs. full-text (or truncated) baseline harness. No invented metrics.

**Dependencies.** Segments 8 and 10.

## Segment 12 — Integration, safety tests, and documentation

**Purpose.** Close the proof of concept: safety tests, demo script, defense notes, FYP-II roadmap.

**Dependencies.** Segments 1–11.

## Out of scope for FYP-I

LoRA / PEFT, advanced reranking, production encryption and key management, hospital integration, HIPAA claims, live patient data, commercial-API-default inference.
