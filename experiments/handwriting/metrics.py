"""Corpus metrics shared by the local baseline and Kaggle experiments."""
import re
import unicodedata


def normalize(text):
    return " ".join(unicodedata.normalize("NFC", str(text)).split())


def distance(a, b):
    previous = list(range(len(b) + 1))
    for i, left in enumerate(a, 1):
        current = [i]
        for j, right in enumerate(b, 1):
            current.append(min(current[-1] + 1, previous[j] + 1, previous[j - 1] + (left != right)))
        previous = current
    return previous[-1]


def score(pairs):
    """Case-sensitive corpus CER/WER; lower is better. Values may exceed 1."""
    rows = [(normalize(ref), normalize(pred)) for ref, pred in pairs]
    if not rows or any(not ref for ref, _ in rows):
        raise ValueError("Metrics require nonempty reference labels and predictions for every sample.")
    digit_rows = [(r, p) for r, p in rows if re.search(r"\d", r)]
    return {
        "samples": len(rows),
        "cer": sum(distance(r, p) for r, p in rows) / sum(len(r) for r, _ in rows),
        "wer": sum(distance(r.split(), p.split()) for r, p in rows) / sum(len(r.split()) for r, _ in rows),
        "exact_match": sum(r == p for r, p in rows) / len(rows),
        "digit_samples": len(digit_rows),
        "digit_sequence_match": (sum(re.findall(r"\d+", r) == re.findall(r"\d+", p) for r, p in digit_rows) / len(digit_rows)) if digit_rows else None,
        "normalization": "Unicode NFC, whitespace collapsed, case preserved",
    }
