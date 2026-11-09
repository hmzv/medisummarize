"""Evaluation must select chunks instead of supplying every file unchanged."""
import importlib.util
from pathlib import Path
from app.services.evaluation.cases import SyntheticCase

spec = importlib.util.spec_from_file_location("evaluation_script", Path(__file__).resolve().parents[2] / "scripts" / "evaluate.py")
harness = importlib.util.module_from_spec(spec)
spec.loader.exec_module(harness)

def test_rag_selects_chunk_subset_without_cross_case_data():
    case = SyntheticCase(id="TEST",slug="isolated",split="held-out",purpose="retrieval",files=(),companion_files=(),reference_facts=(),reference_summary="",folder=Path("."),documents=(("long.txt", "medications amlodipine 5 mg. " * 200),),notes=())
    selected = harness._rag_evidence(case)
    assert 0 < len(selected) <= 20
    assert all(p["original_filename"] == "long.txt" for p in selected)
    assert all(len(p["text"]) <= 80 for p in selected)
    assert len({p["id"] for p in selected}) == len(selected)
