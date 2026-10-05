"""Evaluation metrics and synthetic fixtures."""

from __future__ import annotations

from app.services.evaluation.cases import load_cases, load_manifest, synthetic_root
from app.services.evaluation.metrics import (
    fact_coverage,
    quarantine_scores,
    rouge_n,
    score_summary,
)


def test_rouge_identical_strings_are_one() -> None:
    assert rouge_n("denied chest pain", "denied chest pain", 1)["f1"] == 1.0


def test_rouge_disjoint_strings_are_zero() -> None:
    assert rouge_n("alpha beta", "gamma delta", 1)["f1"] == 0.0


def test_fact_coverage_finds_negation_phrase() -> None:
    result = fact_coverage("The patient denied chest pain.", ["denied chest pain"])
    assert result["coverage"] == 1.0
    assert result["missing"] == []


def test_mock_scores_are_quarantined() -> None:
    wrapped = quarantine_scores({"rouge1": {"f1": 1.0}}, is_mock=True)
    assert wrapped["reportable"] is False
    assert "MOCK/TEST OUTPUT" in wrapped["quarantine_reason"]
    assert wrapped["debug_scores"]["rouge1"]["f1"] == 1.0


def test_real_provider_scores_are_reportable() -> None:
    wrapped = quarantine_scores({"rouge1": {"f1": 0.5}}, is_mock=False)
    assert wrapped["reportable"] is True
    assert wrapped["scores"]["rouge1"]["f1"] == 0.5


def test_score_summary_quarantines_mock_output() -> None:
    result = score_summary(
        summary={
            "key_history": [
                {"text": "denied chest pain", "source_ids": ["e1"], "evidence_status": "citation_present"}
            ]
        },
        reference_summary="denied chest pain",
        reference_facts=["denied chest pain"],
        allowed_ids={"e1"},
        is_mock=True,
    )
    assert result["reportable"] is False


def test_manifest_lists_cases_a_through_h() -> None:
    ids = {item["id"] for item in load_manifest()["cases"]}
    assert {"A", "B", "C", "D", "E", "F", "G1", "G2", "H"} <= ids


def test_synthetic_upload_files_exist_and_are_labeled() -> None:
    root = synthetic_root()
    for case in load_cases():
        assert case.folder.is_dir(), case.slug
        for name in case.files:
            path = case.folder / name
            assert path.is_file(), path
            if path.suffix.lower() in {".png", ".jpg", ".jpeg"}:
                continue
            text = path.read_text(encoding="utf-8")
            assert "SYNTHETIC" in text
            assert "NOT A REAL PATIENT" in text
        notice = (root / "README.md").read_text(encoding="utf-8")
        assert "NOT A REAL PATIENT" in notice
