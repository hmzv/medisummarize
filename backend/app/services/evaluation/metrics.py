"""Automatic evaluation metrics. These are not clinical validation."""

from __future__ import annotations

import re
from collections import Counter
from typing import Any

TOKEN_RE = re.compile(r"[a-z0-9]+")
CLAIM_FIELDS = (
    "key_history",
    "current_documented_findings",
    "medications",
    "allergies",
    "laboratory_findings",
)


def tokenize(text: str) -> list[str]:
    return TOKEN_RE.findall(text.lower())


def ngrams(tokens: list[str], n: int) -> list[tuple[str, ...]]:
    if n <= 0 or len(tokens) < n:
        return []
    return [tuple(tokens[i : i + n]) for i in range(len(tokens) - n + 1)]


def _f1(overlap: int, pred_count: int, ref_count: int) -> dict[str, float]:
    precision = overlap / pred_count if pred_count else 0.0
    recall = overlap / ref_count if ref_count else 0.0
    if precision + recall == 0:
        f1 = 0.0
    else:
        f1 = 2 * precision * recall / (precision + recall)
    return {"precision": precision, "recall": recall, "f1": f1}


def rouge_n(prediction: str, reference: str, n: int) -> dict[str, float]:
    pred = ngrams(tokenize(prediction), n)
    ref = ngrams(tokenize(reference), n)
    if not pred and not ref:
        return {"precision": 1.0, "recall": 1.0, "f1": 1.0}
    pred_counts = Counter(pred)
    ref_counts = Counter(ref)
    overlap = sum((pred_counts & ref_counts).values())
    return _f1(overlap, sum(pred_counts.values()), sum(ref_counts.values()))


def rouge_l(prediction: str, reference: str) -> dict[str, float]:
    pred = tokenize(prediction)
    ref = tokenize(reference)
    if not pred and not ref:
        return {"precision": 1.0, "recall": 1.0, "f1": 1.0}
    return _f1(_lcs_length(pred, ref), len(pred), len(ref))


def _lcs_length(left: list[str], right: list[str]) -> int:
    if not left or not right:
        return 0
    previous = [0] * (len(right) + 1)
    for token in left:
        current = [0]
        for index, other in enumerate(right, start=1):
            if token == other:
                current.append(previous[index - 1] + 1)
            else:
                current.append(max(previous[index], current[-1]))
        previous = current
    return previous[-1]


def flatten_summary_text(summary: dict[str, Any] | None) -> str:
    if not summary:
        return ""
    parts: list[str] = []
    for field in CLAIM_FIELDS:
        for claim in summary.get(field) or []:
            text = claim.get("text") if isinstance(claim, dict) else ""
            if text:
                parts.append(str(text))
    parts.extend(str(item) for item in (summary.get("unresolved_or_unavailable") or []))
    return " ".join(parts)


def fact_coverage(generated_text: str, reference_facts: list[str]) -> dict[str, Any]:
    generated_lower = generated_text.lower()
    generated_tokens = set(tokenize(generated_text))
    covered: list[str] = []
    missing: list[str] = []
    for fact in reference_facts:
        tokens = tokenize(fact)
        hit = fact.lower() in generated_lower
        if not hit and tokens:
            hit = all(token in generated_tokens for token in tokens)
        (covered if hit else missing).append(fact)
    total = len(reference_facts)
    return {
        "covered": covered,
        "missing": missing,
        "coverage": (len(covered) / total) if total else 1.0,
        "n_facts": total,
    }


def citation_metrics(summary: dict[str, Any] | None, allowed_ids: set[str]) -> dict[str, Any]:
    claims: list[dict[str, Any]] = []
    if summary:
        for field in CLAIM_FIELDS:
            for claim in summary.get(field) or []:
                if isinstance(claim, dict):
                    claims.append(claim)
    n_claims = len(claims)
    valid = 0
    unsupported = 0
    unknown = 0
    for claim in claims:
        source_ids = [str(item) for item in (claim.get("source_ids") or [])]
        if not source_ids:
            unsupported += 1
            continue
        if any(item not in allowed_ids for item in source_ids):
            unknown += 1
        else:
            valid += 1
    return {
        "n_claims": n_claims,
        "valid_citation_rate": (valid / n_claims) if n_claims else 1.0,
        "unsupported_claim_rate": (unsupported / n_claims) if n_claims else 0.0,
        "unknown_citation_rate": (unknown / n_claims) if n_claims else 0.0,
    }


def compute_debug_scores(
    *,
    prediction_text: str,
    reference_summary: str,
    reference_facts: list[str],
    summary: dict[str, Any] | None,
    allowed_ids: set[str],
) -> dict[str, Any]:
    return {
        "rouge1": rouge_n(prediction_text, reference_summary, 1),
        "rouge2": rouge_n(prediction_text, reference_summary, 2),
        "rougeL": rouge_l(prediction_text, reference_summary),
        "fact_coverage": fact_coverage(prediction_text, reference_facts),
        "citations": citation_metrics(summary, allowed_ids),
    }


def quarantine_scores(scores: dict[str, Any], is_mock: bool) -> dict[str, Any]:
    """Mock/test providers must never enter reportable experimental metrics."""
    if is_mock:
        return {
            "reportable": False,
            "quarantine_reason": (
                "MOCK/TEST OUTPUT: automatic scores are quarantined and must not "
                "be cited as experimental results."
            ),
            "debug_scores": scores,
        }
    return {"reportable": True, "scores": scores}


def score_summary(
    *,
    summary: dict[str, Any] | None,
    reference_summary: str,
    reference_facts: list[str],
    allowed_ids: set[str],
    is_mock: bool,
) -> dict[str, Any]:
    prediction_text = flatten_summary_text(summary)
    debug = compute_debug_scores(
        prediction_text=prediction_text,
        reference_summary=reference_summary,
        reference_facts=reference_facts,
        summary=summary,
        allowed_ids=allowed_ids,
    )
    return quarantine_scores(debug, is_mock)
