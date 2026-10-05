# 5-minute demo script

Research prototype for clinical-document summarization only. Not for diagnosis, prescribing, treatment recommendations, or autonomous clinical decision-making.

1. Start PostgreSQL or keep the SQLite `DATABASE_URL` in `.env`.
2. `cd backend` → install extras → `alembic upgrade head` → `uvicorn app.main:app --reload --host 127.0.0.1 --port 8000`
3. `cd frontend` → `npm install` → `npm run dev`
4. Open http://localhost:5173 and read the disclaimer banner plus the generation-mode banner.
5. Register a fictional email (for example `reviewer@synthetic.example`).
6. Create a record labeled `Case E — negation (SYNTHETIC)`.
7. Upload `data/synthetic/case_e_negation/discharge.txt`.
8. Click **Extract text**, confirm the negation (`denied chest pain`) is visible.
9. Click **Generate summary**. If `GENERATION_PROVIDER=mock`, the red **MOCK/TEST OUTPUT** label must be visible.
10. Click a citation ID. The evidence panel should highlight the passage, show the original filename and page, and is not clinical proof.
11. Optional: create a second account and open the first record URL — the API must return 404.
12. Sign out. The record list requires authentication.

If Ollama is not running, do not describe the demo as a fully verified AI system.
