# Evaluation Protocol — MediSummarize AI

**Status:** Harness implemented. No reportable experimental results have been collected on this machine while generation is mock. Do not treat debug scores as evidence of performance.

## Research question

Does basic RAG improve completeness, faithfulness, and traceability compared with a non-retrieval summarization approach on synthetic clinical-document cases?

## Fair comparison rule

The non-retrieval baseline **must still receive clinical document content**. Comparing RAG to a model with no record access would be uninformative.

- Short cases: the complete extracted record text is given to the same generation model.
- Long cases: a documented deterministic truncation strategy is used, and lost coverage is reported.
- The same model identifier, output schema, and comparable generation settings are used in both conditions unless a deviation is recorded.

The corrected script (`scripts/evaluate.py`, 9 November 2026) uses the shared page-aware chunker, configured embedding provider, exact cosine ranking and the runtime's five section queries. It takes up to four chunks per query and deduplicates them. This offline in-memory retrieval avoids user/runtime data while exercising real chunk selection. The non-retrieval condition receives concatenated full text. Both prompts use the same generator and output schema. Small cases may retrieve almost all their chunks, limiting experimental discrimination. The harness is a pilot rather than an independent clinical benchmark.

Live OCR is not executed inside the script. Image cases B and F use explicitly labeled companion transcripts, so OCR quality needs a separate assessment. The current prompt builder supplies all selected text without explicit truncation. Larger cases can exceed a provider's context window. Record the emitted input character count, failures and any provider-side truncation, and implement a shared documented context-budget policy before extending the pilot.

## Conditions

1. **RAG** — record/case-scoped retrieval of chunks, then structured generation.
2. **Non-retrieval baseline** — extracted text (or truncated extracted text) supplied directly.

Mock/test providers must never be mixed into real evaluation metrics.

## Data

- Development fixtures (A, E, H) may be used for prompt and retrieval tuning.
- Held-out cases (B, C, D, F, G1, G2) are reserved for reported scores.
- Splits are by patient/case, not by document within the same case, so longitudinal information does not leak across conditions.
- All cases are synthetic and labeled `SYNTHETIC — NOT A REAL PATIENT`. Manifest: `data/synthetic/manifest.json`.

## Metrics (implemented)

| Metric | What it measures | What it does not measure |
|--------|------------------|--------------------------|
| ROUGE-1 / ROUGE-2 / ROUGE-L | Surface overlap with a reference summary | Clinical correctness |
| Reference-fact coverage | Whether listed reference facts appear | Whether extra claims are true |
| Unsupported-claim rate | Claims without a source_id | Expert medical accuracy |
| Citation validity | Whether cited IDs were supplied to the model | Semantic support |
| Citation support (rubric) | Human/heuristic check that the passage actually backs the claim | Board-certified review unless the reviewer is one |
| Retrieval recall@K | Retrieval of labeled relevant chunks | Generation quality (not computed in the offline harness) |
| Extraction/OCR accuracy | Where reference text exists | Downstream summary quality |
| Latency | Retrieval and generation time | Accuracy |

Automatic heuristics must not be described as clinical expert validation. Human rubric review must state reviewer qualifications.

## Mock quarantine

If `is_mock` is true:

- `metrics.reportable` is `false`
- numeric overlap scores live only under `metrics.debug_scores`
- CSV records `reportable=false`
- stdout prints `MOCK/TEST OUTPUT`

Do not copy debug F1 values into a results chapter.

## Stored artifacts

Each run stores case ID/split, model and prompt versions, provider, chunk parameters, retrieval backend, outputs, metric objects, input character count, generation duration and retrieval duration. Export formats: JSON and CSV under `data/evaluation/results/` (gitignored). Mock or invalid structured output is excluded from reportable results. The packaged FYP I evidence is an explicitly labeled mock dry run.

## Reporting rules

- Do not invent improvements, sample sizes, confidence intervals, or passed tests.
- If real inference is unavailable, say so. A mock-only pipeline is not a fully verified AI system.
- Distinguish development vs held-out results.
