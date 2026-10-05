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


def _run_condition(name: str, user_prompt: str, allowed_ids: set[str], case) -> dict:
    provider = get_generation_provider()
    result = provider.generate(SYSTEM_PROMPT, user_prompt)
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
    }


def _rag_evidence(case) -> list[dict[str, object]]:
    items: list[dict[str, object]] = []
    for index, (filename, text) in enumerate(case.documents, start=1):
        items.append(
            {
                "id": f"{case.id}-chunk-{index}",
                "document_id": f"{case.slug}-{filename}",
                "original_filename": filename,
                "page": 1,
                "method": "utf8_text",
                "text": text,
            }
        )
    return items


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
        rag_evidence = _rag_evidence(case)
        baseline_evidence = _baseline_evidence(case)
        rag_prompt = build_user_prompt(rag_evidence, [f"{case.id}: file-level passages"] + list(case.notes))
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
