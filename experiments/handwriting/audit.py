"""Audit official RxHandBD v3 ML data without silently repairing labels.

python experiments/handwriting/audit.py --archive data/runtime/rxhandbd-v3/RxHandBD-ML.zip --out data/runtime/rxhandbd-v3/audit
"""
from __future__ import annotations
import argparse
import base64
import csv
import hashlib
import html
import io
import json
import random
import zipfile
from collections import Counter, defaultdict
from pathlib import Path
from PIL import Image, ImageOps

EXPECTED_SHA256 = "c6371c0a3a89301c0b6b2eac1d2d49f6f3d8e559a7a71b338655dde0a6a63b51"


def audit(archive: Path, out: Path):
    out.mkdir(parents=True, exist_ok=True)
    archive_hash = hashlib.file_digest(archive.open("rb"), "sha256").hexdigest()
    if archive_hash != EXPECTED_SHA256:
        raise ValueError("Archive differs from the official v3 ML file. Do not mix dataset versions.")
    rows, issues, thumbnails = [], [], {}
    with zipfile.ZipFile(archive) as z:
        names = set(z.namelist())
        for split, label_file, image_dir in [("train", "Train_Label.csv", "Train_Set"), ("test", "Test_Label.csv", "Test_Set")]:
            prefix = "RxHandBD-ML/"
            reader = csv.DictReader(io.StringIO(z.read(prefix + label_file).decode("utf-8-sig"), newline=None))
            for item in reader:
                filename, label = item["Images"].strip(), item["Text"]
                name = prefix + image_dir + "/" + filename
                if not label.strip() or name not in names:
                    issues.append({"split": split, "file": filename, "reason": "missing image or empty label"})
                    continue
                raw = z.read(name)
                try:
                    im = Image.open(io.BytesIO(raw)).convert("RGB")
                    im.load()
                except Exception as exc:
                    issues.append({"split": split, "file": filename, "reason": str(exc)})
                    continue
                gray = ImageOps.grayscale(im).resize((9, 8))
                pixels = list(gray.getdata())
                bits = [pixels[y * 9 + x] > pixels[y * 9 + x + 1] for y in range(8) for x in range(8)]
                dhash = sum(int(bit) << i for i, bit in enumerate(bits))
                pixel_hash = hashlib.sha256(str(im.size).encode() + im.tobytes()).hexdigest()
                rows.append({"path": name, "filename": filename, "text": label, "official_split": split,
                             "width": im.width, "height": im.height, "sha256": hashlib.sha256(raw).hexdigest(),
                             "pixel_sha256": pixel_hash, "dhash": f"{dhash:016x}"})
                if split == "train":
                    # Contact sheet uses train images only; test labels never drive label repair.
                    thumb = im.copy(); thumb.thumbnail((220, 140))
                    buf = io.BytesIO(); thumb.save(buf, format="PNG")
                    thumbnails[name] = base64.b64encode(buf.getvalue()).decode()
        image_names = {n for n in names if n.lower().endswith((".jpg", ".jpeg", ".png"))}
    groups = defaultdict(list)
    for row in rows:
        groups[row["pixel_sha256"]].append(row)
    overlaps = [items for items in groups.values() if len({r["official_split"] for r in items}) > 1]
    conflicts = [items for items in groups.values() if len({r["text"] for r in items}) > 1]
    # Preserve the official test set; exclude exact duplicate test content from fitting and validation.
    test_hashes = {r["pixel_sha256"] for r in rows if r["official_split"] == "test"}
    eligible_groups = sorted(h for h, items in groups.items() if h not in test_hashes and items[0]["official_split"] == "train")
    random.Random(1019).shuffle(eligible_groups)
    val_hashes = set(eligible_groups[:max(1, round(len(eligible_groups) * 0.1))])
    conflicting_hashes = {items[0]["pixel_sha256"] for items in conflicts}
    for row in rows:
        h = row["pixel_sha256"]
        row["split"] = "test" if row["official_split"] == "test" else "excluded" if h in test_hashes or h in conflicting_hashes else "validation" if h in val_hashes else "train"
    train_candidates = [r for r in rows if r["split"] == "train"]
    eval_candidates = [r for r in rows if r["split"] in {"validation", "test"}]
    # dHash is only a triage flag: collisions do NOT prove duplication or trigger removal.
    near = []
    for left in train_candidates:
        lh = int(left["dhash"], 16)
        for right in eval_candidates:
            if left["pixel_sha256"] != right["pixel_sha256"] and (lh ^ int(right["dhash"], 16)).bit_count() <= 2:
                near.append({"train": left["filename"], "evaluation": right["filename"], "split": right["split"]})
    label_names = [r["path"] for r in rows]
    report = {
        "dataset": "RxHandBD v3 ML", "doi": "10.17632/dsb5r6vskg.3", "license": "CC BY 4.0",
        "source": "https://data.mendeley.com/datasets/dsb5r6vskg/3", "archive_sha256": archive_hash,
        "official_counts": dict(Counter(r["official_split"] for r in rows)),
        "experiment_counts": dict(Counter(r["split"] for r in rows)),
        "unique_labels": len({r["text"] for r in rows}), "image_shapes": dict(Counter(f'{r["width"]}x{r["height"]}' for r in rows)),
        "unlabeled_images": sorted(image_names - set(label_names)),
        "repeated_label_rows": len(label_names) - len(set(label_names)), "invalid_items": issues,
        "exact_duplicate_groups": sum(len(v) > 1 for v in groups.values()),
        "cross_official_split_duplicate_groups": len(overlaps), "conflicting_label_groups": len(conflicts),
        "near_duplicate_flags": len(near),
        "split_seed": 1019, "validation_fraction_groups": 0.1,
        "writer_independent": False, "writer_metadata": "Not supplied in archive labels; prescription/writer leakage cannot be ruled out.",
        "limitations": ["Word crops only; no full-page layout recognition benchmark.", "Near-duplicate flags need human inspection; they are not established duplicates.", "No writer-independent claim is supported.", "Official test set retained; exact test duplicates excluded from fitting/validation."]
    }
    for name, payload in [("audit.json", report), ("duplicate-groups.json", [[{k:r[k] for k in ("path","text","official_split")} for r in v] for v in groups.values() if len(v)>1]), ("near-duplicate-flags.json", near)]:
        (out / name).write_text(json.dumps(payload, indent=2), encoding="utf-8")
    with (out / "manifest.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    sample = random.Random(1019).sample(train_candidates, min(50, len(train_candidates)))
    contact = "<!doctype html><meta charset='utf-8'><title>RxHandBD training-label review</title><style>body{font:16px system-ui;margin:32px}section{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:20px}article{border:1px solid #aaa;padding:12px}img{max-width:100%;height:140px;object-fit:contain}label{display:block}</style><h1>Review 50 training labels</h1><p>Mark unreadable crops, wrong labels, ambiguous digits, and unexpected language in manual-review.csv. Do not silently correct test labels.</p><section>"
    for r in sample:
        contact += f'<article><img alt="Handwritten training crop" src="data:image/png;base64,{thumbnails[r["path"]]}"><h2>{html.escape(r["text"])}</h2><p>{html.escape(r["filename"])}</p></article>'
    (out / "review-50.html").write_text(contact + "</section>", encoding="utf-8")
    with (out / "manual-review.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f); writer.writerow(["filename", "provided_label", "decision", "notes"])
        writer.writerows((r["filename"], r["text"], "pending", "") for r in sample)
    print(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("--archive", type=Path, required=True); parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(); audit(args.archive, args.out)
