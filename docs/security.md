# Security and defense notes — MediSummarize AI

This is a research prototype, not a certified hospital product. The notes below are what FYP-I actually implements and what it does not claim.

## What is enforced in the API

- **Authentication.** Email + password. Passwords are stored as bcrypt hashes. JWT access tokens travel in the `Authorization` header only.
- **Ownership.** `owner_id` is assigned from the authenticated principal. Clients cannot set it. Cross-user IDs return 404.
- **Patient isolation for retrieval.** The record is authorized before the per-record index folder is opened. There is no global search-then-filter path.
- **Uploads.** Content is validated by magic bytes, size, page, and pixel limits. Storage is outside the web root. Original files are downloadable only by the owner.
- **Untrusted documents.** Extracted text is data, not instructions. Prompt-injection fixtures (Case H) must still produce structured JSON from the mock provider; a real model must be reviewed the same way.
- **Mock generation.** `GENERATION_PROVIDER=mock` labels output `MOCK/TEST OUTPUT` and never silently replaces a missing Ollama server.
- **Citation checks.** Unknown source IDs are stripped. Uncited claims are moved to unresolved information. A remaining citation is not clinical proof.

## Token storage tradeoff

The browser keeps the access token in `sessionStorage`. That avoids putting secrets in URLs and clears the token when the tab closes. Any XSS on the origin could still read it. HttpOnly cookies were not used because this SPA does not yet ship CSRF defenses. See ADR-008.

## What is not claimed

- HIPAA, GDPR, or Pakistan-specific certification
- Production key management, disk encryption of uploads, or a durable audit log
- Hospital or EHR integration
- That RAG removes hallucinations
- That automatic ROUGE / fact-coverage scores are clinical validation
- That mock-provider scores are experimental results (they are quarantined)

## Defense talking points

1. Show the disclaimer banner and generation-mode banner before any summary.
2. Register two users and show that Bob receives 404 for Alice's record and summary URLs.
3. Upload Case E; extract; generate; click a citation; the evidence panel scrolls to the passage and filename/page are visible.
4. Upload Case H; the application still returns JSON with the prototype disclaimer rather than following the injected instruction (verified for the mock provider).
5. Upload Case G patient 1 and patient 2 in **separate** records; retrieval cannot see the other record.
6. If generation is mock, say so. Do not present the demo as a fully verified AI system.
