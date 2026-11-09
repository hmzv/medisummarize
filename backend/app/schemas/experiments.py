"""Aggregate experiment exports. Imported measurements remain user-supplied."""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, JsonValue


class OCRMetrics(BaseModel):
    model_config = ConfigDict(extra="ignore", allow_inf_nan=False)
    samples: int = Field(gt=0, le=10_000_000)
    cer: float = Field(ge=0)
    wer: float = Field(ge=0)
    exact_match: float = Field(ge=0, le=1)
    digit_samples: int = Field(default=0, ge=0)
    digit_sequence_match: float | None = Field(default=None, ge=0, le=1)
    normalization: str = Field(default="NFC + collapsed whitespace; case preserved", max_length=300)


class ExperimentRun(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    schema_version: Literal[1]
    task: Literal["handwriting_word_ocr"]
    model: str = Field(min_length=1, max_length=160)
    dataset: str = Field(min_length=1, max_length=160)
    dataset_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    split: Literal["validation", "test"]
    samples: int = Field(gt=0, le=10_000_000)
    metrics: OCRMetrics
    elapsed_seconds: float = Field(ge=0)
    created_at: datetime
    is_mock: Literal[False]
    provenance: dict[str, JsonValue]
    limitations: list[str] = Field(default_factory=list, max_length=20)


class ExperimentImport(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: Literal[1]
    runs: list[ExperimentRun] = Field(min_length=1, max_length=20)
