"""Evaluation harness (Segment 11).

Runs RAG-style passage prompts and a non-retrieval baseline with the same
generation provider. Does not invent scores. Mock results are quarantined.

Usage (from backend/ with venv):

    python ../scripts/evaluate.py
"""

from __future__ import annotations

import csv
import json
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.core.config import get_settings  # noqa: E402
from app.prompts.summarize_v1 import PROMPT_VERSION, SYSTEM_PROMPT, build_user_prompt  # noqa: E402
from app.schemas.summaries import StructuredSummary  # noqa: E402
from app.services.evaluation.cases import load_cases  # noqa: E402
from app.services.evaluation.metrics import flatten_summary_text, score_summary  # noqa: E402
from app.services.generation.providers import get_generation_provider  # noqa: E402
from app.services.chunking.service import chunk_extracted_pages  # noqa: E402
from app.services.embeddings.providers import get_embedding_provider  # noqa: E402
from app.models.extracted_page import ExtractedPage  # noqa: E402
from app.services.summarization import SECTION_QUERIES  # noqa: E402
import numpy as np  # noqa: E402


def _run_condition(name: str, user_prompt: str, allowed_ids: set[str], case) -> dict:
    provider = get_generation_provider()
    started = time.perf_counter()
    result = provider.generate(SYSTEM_PROMPT, user_prompt)
    generation_ms = round((time.perf_counter() - started) * 1000, 3)
    try:
        summary = StructuredSummary.model_validate_json(result.text)
        payload = summary.model_dump()
        valid = True
        error = None
    except Exception as exc:  # noqa: BLE001 — evaluation must record parse failures
        payload = None
        valid = False
        error = str(exc)
    metrics = score_summary(
        summary=payload,
        reference_summary=case.reference_summary,
        reference_facts=list(case.reference_facts),
        allowed_ids=allowed_ids,
        is_mock=result.is_mock,
    )
    if not valid and not result.is_mock:
        metrics = {"reportable": False, "quarantine_reason": "Invalid structured JSON", "debug_scores": metrics.get("scores", {})}
    return {
        "condition": name,
        "provider": result.provider,
        "model": result.model_id,
        "is_mock": result.is_mock,
        "prompt_version": PROMPT_VERSION,
        "valid_json": valid,
        "error": error,
        "output": result.text,
        "summary": payload,
        "prediction_text": flatten_summary_text(payload),
        "metrics": metrics,
        "generation_ms": generation_ms,
        "input_characters": len(user_prompt),
        "input_prompt": user_prompt,
        "allowed_source_ids": sorted(allowed_ids),
    }


def _rag_evidence(case) -> list[dict[str, object]]:
    settings = get_settings()
    pages = []
    record_id = uuid.uuid5(uuid.NAMESPACE_URL, case.slug)
    for index, (filename, text) in enumerate(case.documents, start=1):
        pages.append(ExtractedPage(owner_id=record_id, record_id=record_id,
            document_id=uuid.uuid5(record_id, filename), page_number=1, text=text,
            extraction_method="fixture_text", warnings_json="[]"))
    chunks = chunk_extracted_pages(pages, settings.chunk_size, settings.chunk_overlap)
    if not chunks:
        return []
    provider = get_embedding_provider()
    matrix = np.asarray(provider.embed([c.text for c in chunks]), dtype=float)
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    matrix = matrix / np.maximum(norms, 1e-12)
    selected: dict[int, None] = {}
    for _, query in SECTION_QUERIES:
        vector = np.asarray(provider.embed([query])[0], dtype=float)
        vector /= max(float(np.linalg.norm(vector)), 1e-12)
        scores = matrix @ vector
        for i in np.argsort(-scores, kind="stable")[:4]:
            selected[int(i)] = None
    names = {uuid.uuid5(record_id, filename): filename for filename, _ in case.documents}
    return [{"id": str(chunks[i].chunk_id), "document_id": str(chunks[i].document_id),
        "original_filename": names[chunks[i].document_id], "page": 1,
        "method": "fixture_text", "text": chunks[i].text} for i in selected]


def _baseline_evidence(case) -> list[dict[str, object]]:
    combined = "\n\n".join(text for _, text in case.documents)
    if not combined:
        return []
    return [
        {
            "id": f"{case.id}-fulltext",
            "document_id": case.slug,
            "original_filename": "concatenated-record.txt",
            "page": 1,
            "method": "utf8_text",
            "text": combined,
        }
    ]


def main() -> None:
    settings = get_settings()
    rows: list[dict] = []
    for case in load_cases():
        retrieval_started = time.perf_counter()
        rag_evidence = _rag_evidence(case)
        retrieval_ms = round((time.perf_counter() - retrieval_started) * 1000, 3)
        baseline_evidence = _baseline_evidence(case)
        rag_prompt = build_user_prompt(rag_evidence, [f"{case.id}: section-query cosine retrieval, top 4 per section"] + list(case.notes))
        baseline_prompt = build_user_prompt(
            baseline_evidence,
            [f"{case.id}: non-retrieval full extracted text"] + list(case.notes),
        )
        rag = _run_condition("rag", rag_prompt, {item["id"] for item in rag_evidence if isinstance(item["id"], str)}, case)
        baseline = _run_condition(
            "non_retrieval",
            baseline_prompt,
            {item["id"] for item in baseline_evidence if isinstance(item["id"], str)},
            case,
        )
        for item in (rag, baseline):
            item.update(
                {
                    "case_id": case.id,
                    "slug": case.slug,
                    "split": case.split,
                    "purpose": case.purpose,
                    "reference_facts": list(case.reference_facts),
                    "harness_notes": list(case.notes),
                    "embedding_provider": settings.embedding_provider,
                    "generation_provider_setting": settings.generation_provider,
                    "retrieval_ms": retrieval_ms if item["condition"] == "rag" else 0,
                    "run_at": datetime.now(timezone.utc).isoformat(),
                    "retrieval_backend": "numpy_exact",
                    "chunk_size": settings.chunk_size,
                    "chunk_overlap": settings.chunk_overlap,
                }
            )
            rows.append(item)

    out_dir = ROOT / "data" / "evaluation" / "results"
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "latest.json"
    csv_path = out_dir / "latest.csv"
    json_path.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "case_id",
                "split",
                "condition",
                "is_mock",
                "reportable",
                "valid_json",
                "provider",
                "model",
            ],
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "case_id": row["case_id"],
                    "split": row["split"],
                    "condition": row["condition"],
                    "is_mock": row["is_mock"],
                    "reportable": row["metrics"]["reportable"],
                    "valid_json": row["valid_json"],
                    "provider": row["provider"],
                    "model": row["model"],
                }
            )
    mocked = any(row["is_mock"] for row in rows)
    reportable = sum(1 for row in rows if row["metrics"]["reportable"])
    print(f"wrote {json_path}")
    print(f"wrote {csv_path}")
    if mocked:
        print("MOCK/TEST OUTPUT: scores are quarantined (reportable=false).")
    print(f"reportable rows: {reportable}/{len(rows)}")
    print("No clinical performance claims are implied by this run.")


if __name__ == "__main__":
    main()
