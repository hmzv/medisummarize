"""Load labeled synthetic cases. All cases are fictional."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from app.core.config import REPO_ROOT

IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg"}


@dataclass(frozen=True)
class SyntheticCase:
    id: str
    slug: str
    split: str
    purpose: str
    files: tuple[str, ...]
    companion_files: tuple[str, ...]
    reference_facts: tuple[str, ...]
    reference_summary: str
    folder: Path
    documents: tuple[tuple[str, str], ...]
    notes: tuple[str, ...]


def synthetic_root() -> Path:
    return REPO_ROOT / "data" / "synthetic"


def load_manifest() -> dict:
    path = synthetic_root() / "manifest.json"
    return json.loads(path.read_text(encoding="utf-8"))


def load_cases() -> list[SyntheticCase]:
    payload = load_manifest()
    cases: list[SyntheticCase] = []
    for raw in payload["cases"]:
        folder = synthetic_root() / raw["slug"]
        documents, notes = _documents_for_case(folder, raw)
        cases.append(
            SyntheticCase(
                id=raw["id"],
                slug=raw["slug"],
                split=raw["split"],
                purpose=raw["purpose"],
                files=tuple(raw["files"]),
                companion_files=tuple(raw.get("companion_files") or []),
                reference_facts=tuple(raw.get("reference_facts") or []),
                reference_summary=raw.get("reference_summary") or "",
                folder=folder,
                documents=tuple(documents),
                notes=tuple(notes),
            )
        )
    return cases


def _documents_for_case(folder: Path, raw: dict) -> tuple[list[tuple[str, str]], list[str]]:
    documents: list[tuple[str, str]] = []
    notes: list[str] = []
    for name in raw["files"]:
        path = folder / name
        if not path.exists():
            notes.append(f"Missing file: {name}")
            continue
        if path.suffix.lower() in IMAGE_SUFFIXES:
            notes.append(f"Skipped image {name}; this harness does not run live OCR.")
            continue
        documents.append((name, path.read_text(encoding="utf-8")))
    if not documents:
        for name in raw.get("companion_files") or []:
            path = folder / name
            if path.exists() and path.suffix.lower() == ".txt":
                documents.append((name, path.read_text(encoding="utf-8")))
                notes.append(
                    f"Used companion {name} as a text stand-in because the upload file is an image."
                )
    return documents, notes
