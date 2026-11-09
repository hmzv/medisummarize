# FYP I submission checklist

Project **CS-FYP-1019**, MediSummarize AI. Supervisor: **Dr. Muhammad Yaseen Khan**. No co-supervisor. Prepared 9 November 2026.

The supplied proposal defines the academic scope. The three supplied university templates define the report structure. This checklist distinguishes prepared deliverables from acceptance items that still require evidence or human approval.

| Deliverable | Location | Status |
|---|---|---|
| Protected web prototype | `frontend/`, `backend/` | Implemented; component/backend tests pass; full browser walkthrough pending |
| Final report | `output/fyp-i/MediSummarize_AI_FYP-I_Final_Report.docx` | Prepared in supplied template; supervisor review pending |
| Software requirements specification | `output/fyp-i/MediSummarize_AI_FYP-I_SRS.docx` | 16 FRs, 12 NFRs, 8 use cases and traceability |
| Software design specification | `output/fyp-i/MediSummarize_AI_FYP-I_SDS.docx` | Architecture, schema dictionary, 14 design figures and traceability |
| Updated implementation defense | `output/fyp-i/MediSummarize_AI_FYP-I_Defense.pptx` | Prepared with current implementation and research limits |
| Synthetic dataset | `data/synthetic/` | A–H, nine manifest entries including G1/G2; labeled fictional |
| Reproducible evaluation | `scripts/evaluate.py` | Corrected chunk retrieval versus full-text baseline |
| Evaluation evidence | `output/fyp-i/evaluation/` | 18 mock rows, all non-reportable; real-model results pending |
| Demo and configuration | README, `docs/demo-script.md`, `.env.example` | Included; real secrets excluded |
| FYP II plan | `docs/fyp-ii-roadmap.md` and final report | Documented |

Before declaring FYP I fully complete:

1. Select and run a real compatible language model. Record checkpoint/tag, license, model size, hardware, inference settings and versions. Do not represent mock output as real RAG results.
2. Execute paired retrieved-context/full-text conditions on the fixed held-out split, review unsupported claims manually, and add actual findings to the report and slides. Separate development and held-out results. The tiny synthetic set supports a pilot, not clinical validation.
3. Walk through register → record → browser file selection → extraction → generation → citation → source page → text/JSON download at desktop and mobile widths. Verify keyboard navigation and error recovery. Automated Computer Use was unavailable: IAB/CDP timed out and the Windows browser tool blocked URL policy enforcement.
4. Review the semantic embedding and clinical document-classification gaps with the supervisor. Current defaults are lexical hashing and exact NumPy cosine, with file-kind detection. Date/clinical-field normalization is incomplete. These are deviations from the broader proposed design.
5. Review the three editable documents, refresh Word fields after edits (Ctrl+A, F9), collect signatures, obtain supervisor approval and complete the institutional similarity check. No signatures or approval have been fabricated.

PostgreSQL, FAISS, Docker, encrypted storage, production TLS, role-based permissions, audit events, durable jobs and model adaptation are not prerequisites for the current local mock demonstration. Their intended delivery and any changed FYP I expectations must follow the agreed scope.
