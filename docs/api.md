# HTTP API — MediSummarize AI

Research prototype. Not for diagnosis, prescribing, treatment, or autonomous clinical decisions. All document content is untrusted data.

Base URL in development: `http://127.0.0.1:8000`. The Vite app proxies `/api` to that origin. JSON error bodies use `{"detail": "..."}`.

Unauthorized access to another user's opaque ID returns **404**, not 403.

## Public

| Method | Path | Notes |
|--------|------|-------|
| GET | `/` | Name, docs link, disclaimer |
| GET | `/api/v1/health` | Process liveness |
| GET | `/api/v1/health/ready` | Database ping |
| GET | `/api/v1/health/generation` | Provider name, `is_mock`, warning. Mock mode is never silent. |

## Auth

Passwords are bcrypt hashes. Access tokens are JWT Bearer values. Do not put tokens in URLs.

| Method | Path | Notes |
|--------|------|-------|
| POST | `/api/v1/auth/register` | `{email, password}` → token + user |
| POST | `/api/v1/auth/login` | `{email, password}` → token + user |
| GET | `/api/v1/auth/me` | Current user |

Header: `Authorization: Bearer <token>`.

## Records

Synthetic containers only. `owner_id` is taken from the authenticated user.

| Method | Path | Notes |
|--------|------|-------|
| GET | `/api/v1/records` | `{items: [...]}` |
| POST | `/api/v1/records` | `{display_label}` |
| GET | `/api/v1/records/{record_id}` | Owner only |
| DELETE | `/api/v1/records/{record_id}` | Deletes the container and stored files |

## Documents

Allowed content: PDF, PNG, JPEG, UTF-8 text. Magic bytes are checked. Files are stored under `STORAGE_DIR`, not in a web root.

| Method | Path | Notes |
|--------|------|-------|
| GET | `/api/v1/records/{record_id}/documents` | List |
| POST | `/api/v1/records/{record_id}/documents` | `multipart/form-data` field `file` |
| DELETE | `/api/v1/records/{record_id}/documents/{document_id}` | Owner only |
| GET | `/api/v1/records/{record_id}/documents/{document_id}/file` | Original bytes |
| POST | `/api/v1/records/{record_id}/documents/{document_id}/extract` | Extract / OCR |
| GET | `/api/v1/records/{record_id}/documents/{document_id}/extracted` | Review extracted pages |

## Summaries

Retrieval is limited to the authorized record. Citation IDs mean a source was attached, not that a claim is clinically proven.

| Method | Path | Notes |
|--------|------|-------|
| POST | `/api/v1/records/{record_id}/summary` | Generate; `201` |
| GET | `/api/v1/records/{record_id}/summary` | Latest summary or `404` |

`SummaryResponse.evidence` is a list of `{id, document_id, original_filename, page, method, text}`. `is_mock` is true when the generation provider is the labeled mock.

## Experiment results

| Method | Path | Notes |
|--------|------|-------|
| GET | `/api/v1/experiments` | Authenticated owner's imported runs |
| POST | `/api/v1/experiments/import` | Schema-version 1 aggregate JSON; up to 20 runs and 1 MB |

The request wrapper is `{ "schema_version": 1, "runs": [...] }`. Use the handwriting notebook export or `experiments/handwriting/local-baseline-results.json`. Each run identifies task `handwriting_word_ocr`, model, dataset and SHA-256, validation/test split, sample count, metrics, timestamp, duration, provenance and limitations. `is_mock` must be false; sample counts must agree; non-finite metrics are rejected. CER/WER may exceed 1. Imported values are user-supplied, not independently verified. Content-based IDs prevent duplicate imports in the same workspace. Files are stored under the owner's UUID inside `STORAGE_DIR/experiments/` and are never served directly.
