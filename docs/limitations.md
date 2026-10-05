# Limitations — MediSummarize AI

This is a research prototype for clinical-document summarization only. It is not for diagnosis, prescribing, treatment recommendations, or autonomous clinical decision-making. Verify all generated information against the original records.

## Academic and clinical

- Demonstration records must be synthetic or de-identified. Real patient documents are out of scope for FYP-I.
- The system will not be clinically validated in FYP-I. Synthetic-data scores are not clinical validation.
- RAG does not eliminate hallucinations. A citation ID means a source was attached, not that the claim is medically correct.
- The application does not diagnose disease, prescribe medication, or recommend treatment.

## Regulatory and privacy

- No HIPAA, GDPR, or Pakistan-specific regulatory certification is claimed.
- There is no hospital integration and no live EHR connection.
- Production encryption, key management, and comprehensive audit logging are FYP-II items. Basic secure coding (password hashing, ownership checks, safe uploads, isolation) is required in FYP-I.

## Technical (current)

- Authentication is implemented.
- Uploads, OCR, retrieval, clickable evidence, and mock-labeled summarization are implemented.
- PostgreSQL credentials were not available on the development machine; SQLite is used for bootstrap.
- Docker is not installed here. Compose files are untested on this machine.
- Ollama is not installed. Real model inference is **not** verified. Mock summaries are not evaluation results. Automatic ROUGE/fact scores from mock runs are quarantined.
- The vector index used in tests is numpy exact cosine, not a FAISS binary.
- In-process `BackgroundTasks` for extraction are not durable across process restarts.
- Similarity scores are not calibrated clinical confidence.
- Frontend token storage uses `sessionStorage` and has XSS tradeoffs (ADR-008).

## Technical (planned, will remain after FYP-I)

- In-process background jobs (when added) will not be durable across process restarts.
- Similarity scores from FAISS are not calibrated clinical confidence.
- OCR quality depends on scan quality; uncertain extraction must remain uncertain.
- A locally hosted 7–8B model may not fit the available hardware; a smaller documented fallback may be required.
- Frontend token storage uses `sessionStorage` and has XSS tradeoffs if the origin is compromised.
