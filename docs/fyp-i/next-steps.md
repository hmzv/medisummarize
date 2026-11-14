# Where to proceed from here

The software workflow and documentation package are prepared. The most important remaining FYP I task is a real-model baseline assessment, followed by a manual browser demonstration and supervisor review.

## Handwriting experiment prepared on 10 November

Start with `experiments/handwriting/README.md` and import the updated `experiments/handwriting/MediSummarize_Handwriting_Kaggle.ipynb` into Kaggle. The official RxHandBD v3 ML archive is downloaded and verified locally. The notebook applies the completed review of 50 training labels and eight flagged pairs. Its reviewed split contains 4,012 training, 446 validation, and 1,115 test crops.

The local Tesseract validation baseline has actually run: 446 crops, 78.7% CER and 1.1% exact match. Import `experiments/handwriting/local-baseline-results.json` from the app's Experiments page to display it in your own account. The isolated UI-review account already contains it; no existing user's records were changed. TrOCR is still unrun. This OCR work does not replace the separate summarization baseline requirement below.

Start a Kaggle GPU session, run the notebook, and download its outputs. The experiment measures handwriting recognition on cropped words.

## Start the existing application

From `D:\fyp` in PowerShell:

```powershell
.\scripts\start-demo.ps1
```

Open http://localhost:5173. Create a fictional demonstration account. Create Case A and upload the three files from `data/synthetic/case_a_longitudinal/`. Extract and review text, generate a summary, then follow a citation and open its source page. Mock output is expected with the present configuration.

## Close the research gap

The code already supports a local OpenAI-compatible inference server. It does not require a commercial API. A 7–8B model was proposed, but its weights are not present and have not been downloaded. Choose a licensed checkpoint that fits the available GPU/RAM and record its download/storage requirements before fetching it. Use university compute if the local machine is insufficient.

In the existing ignored `.env`, configure the matching values:

```dotenv
GENERATION_PROVIDER=openai_compatible
GENERATION_BASE_URL=http://127.0.0.1:11434/v1
GENERATION_MODEL=<the exact installed model tag>
```

The tag above is a configuration placeholder, not an installed model. Restart the backend. Confirm `/api/v1/health/generation` reports a real provider and that a summary returns `is_mock=false`. Then run:

```powershell
.\backend\.venv\Scripts\python.exe .\scripts\evaluate.py
```

The JSON contains generation/retrieval duration, prompt version, input size, provider, case split and scores. Mock or malformed output remains excluded. Keep raw outputs, review claim support against source text, report failures, and avoid drawing clinical conclusions from lexical overlap or citation IDs alone.

For semantic retrieval, the optional backend extra now exists:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pip install -e ".[embeddings]"
```

Select an appropriate embedding model, check its license/download size, configure `EMBEDDING_PROVIDER=sentence_transformers` and `EMBEDDING_MODEL`, and re-extract/reindex records. Existing vectors cannot be mixed with a different model or dimension. Keep a lexical-baseline comparison. No encoder choice or quality result is assumed by this package.

## Submit the prepared documents

Use the final report, SRS and SDS under `output/fyp-i/`. Their cover fields include project code CS-FYP-1019 and supervisor Dr. Muhammad Yaseen Khan. Sign-off remains pending. The report accurately states that real-model results are absent. Update that chapter and the defense slides only after the experiment actually runs.

Follow `submission-checklist.md` for the exact acceptance gaps. Continue with the existing `docs/fyp-ii-roadmap.md` after the FYP I research criterion and review steps close.
