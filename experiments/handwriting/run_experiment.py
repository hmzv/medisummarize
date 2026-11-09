"""Run cropped-word OCR experiments locally or in Kaggle. No cloud API key.

Commands: audit first, baseline (validation), train (validation selection), test (held-out once).
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import io
import json
import platform
import random
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image
from metrics import score

MODEL = "microsoft/trocr-small-handwritten"


def read_rows(path, split):
    with path.open(encoding="utf-8", newline="") as f:
        return [r for r in csv.DictReader(f) if r["split"] == split]


def image_from(archive, row):
    return Image.open(io.BytesIO(archive.read(row["path"]))).convert("RGB")


def load_trocr(checkpoint, device):
    from transformers import TrOCRProcessor, VisionEncoderDecoderModel
    processor = TrOCRProcessor.from_pretrained(checkpoint)
    model = VisionEncoderDecoderModel.from_pretrained(checkpoint).to(device)
    model.config.decoder_start_token_id = processor.tokenizer.cls_token_id
    model.config.pad_token_id = processor.tokenizer.pad_token_id
    model.config.eos_token_id = processor.tokenizer.sep_token_id
    model.generation_config.decoder_start_token_id = processor.tokenizer.cls_token_id
    model.generation_config.pad_token_id = processor.tokenizer.pad_token_id
    model.generation_config.eos_token_id = processor.tokenizer.sep_token_id
    return processor, model


def predict_trocr(processor, model, archive, rows, device, batch_size):
    import torch
    predictions = []
    model.eval()
    with torch.inference_mode():
        for start in range(0, len(rows), batch_size):
            images = [image_from(archive, row) for row in rows[start:start+batch_size]]
            values = processor(images=images, return_tensors="pt").pixel_values.to(device)
            tokens = model.generate(values, max_new_tokens=64, num_beams=1)
            predictions.extend(processor.batch_decode(tokens, skip_special_tokens=True))
    return predictions


def evaluate(name, archive, rows, out, split, predictor, metadata):
    destination = out / f"{name}-{split}.json"
    if destination.exists():
        raise FileExistsError(f"{destination} already exists. Keep the recorded result; do not overwrite test evidence.")
    started = time.perf_counter(); predictions = predictor()
    if len(predictions) != len(rows):
        raise ValueError("A prediction is required for every sample, including OCR failures.")
    seconds = time.perf_counter() - started
    metrics = score([(r["text"], p) for r, p in zip(rows, predictions)])
    payload = {
        "schema_version": 1, "task": "handwriting_word_ocr", "model": name,
        "dataset": "RxHandBD v3 ML", "dataset_sha256": metadata["archive_sha256"],
        "split": split, "samples": len(rows), "metrics": metrics, "elapsed_seconds": seconds,
        "created_at": datetime.now(timezone.utc).isoformat(), "is_mock": False,
        "provenance": metadata, "limitations": ["Cropped words, not whole handwritten pages.", "No verified writer-independent split.", "Imported results require researcher review."],
    }
    destination.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    with (out / f"{name}-{split}-predictions.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f); writer.writerow(["filename", "reference", "prediction", "exact_match"])
        writer.writerows((r["filename"], r["text"], p, r["text"] == p) for r, p in zip(rows, predictions))
    print(name, json.dumps(metrics))
    return payload


def train(args, archive, audit):
    import torch
    from torch.utils.data import DataLoader, Dataset
    random.seed(1019); torch.manual_seed(1019)
    if torch.cuda.is_available(): torch.cuda.manual_seed_all(1019)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    if device == "cpu" and not args.allow_cpu:
        raise RuntimeError("Enable Kaggle GPU first. CPU training requires explicit --allow-cpu.")
    processor, model = load_trocr(MODEL, device)
    train_rows = read_rows(args.manifest, "train")
    validation = read_rows(args.manifest, "validation")
    if not train_rows or not validation:
        raise ValueError("Nonempty train and validation splits are required.")
    # Fail rather than silently truncating medical labels.
    if any(len(processor.tokenizer(r["text"]).input_ids) > 64 for r in train_rows + validation):
        raise ValueError("A label exceeds 64 tokens. Review lengths before changing this protocol.")
    class Words(Dataset):
        def __len__(self): return len(train_rows)
        def __getitem__(self, index):
            row = train_rows[index]
            pixels = processor(images=image_from(archive, row), return_tensors="pt").pixel_values.squeeze(0)
            labels = processor.tokenizer(row["text"], padding="max_length", max_length=64, return_tensors="pt").input_ids.squeeze(0)
            labels[labels == processor.tokenizer.pad_token_id] = -100
            return {"pixel_values": pixels, "labels": labels}
    loader = DataLoader(Words(), batch_size=args.batch_size, shuffle=True, num_workers=0)
    optimizer = torch.optim.AdamW(model.parameters(), lr=5e-5, weight_decay=0.01)
    model.gradient_checkpointing_enable()
    model.config.use_cache = False
    scaler = torch.amp.GradScaler("cuda", enabled=device == "cuda")
    best, history = float("inf"), []
    checkpoint = args.out / "best-checkpoint"
    if checkpoint.exists(): raise FileExistsError("Use a new output directory for another training run.")
    configuration = {
        "checkpoint": MODEL, "revision": getattr(model.config, "_commit_hash", None),
        "archive_sha256": audit["archive_sha256"],
        "manifest_sha256": hashlib.file_digest(args.manifest.open("rb"), "sha256").hexdigest(),
        "seed": 1019, "epochs": args.epochs, "batch_size": args.batch_size,
        "gradient_accumulation": args.accumulation, "learning_rate": 5e-5,
        "weight_decay": 0.01, "selection_metric": "validation CER", "device": device,
        "train_samples": len(train_rows), "validation_samples": len(validation),
    }
    (args.out / "training-config.json").write_text(json.dumps(configuration, indent=2), encoding="utf-8")
    for epoch in range(args.epochs):
        model.train(); optimizer.zero_grad(); total_loss = 0.0
        for step, batch in enumerate(loader):
            batch = {key: value.to(device) for key, value in batch.items()}
            with torch.autocast(device_type=device, enabled=device == "cuda"):
                loss = model(**batch).loss
            if not torch.isfinite(loss): raise ValueError("Non-finite training loss; stop and inspect.")
            # Correct scaling for the final, possibly partial accumulation group.
            group_size = min(args.accumulation, len(loader) - (step // args.accumulation) * args.accumulation)
            scaler.scale(loss / group_size).backward(); total_loss += loss.item()
            if (step + 1) % args.accumulation == 0 or step + 1 == len(loader):
                scaler.unscale_(optimizer); torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                scaler.step(optimizer); scaler.update(); optimizer.zero_grad()
        predictions = predict_trocr(processor, model, archive, validation, device, args.batch_size)
        validation_metrics = score([(r["text"], p) for r, p in zip(validation, predictions)])
        history.append({"epoch": epoch + 1, "train_loss": total_loss / len(loader), "validation": validation_metrics})
        print(json.dumps(history[-1]))
        if validation_metrics["cer"] < best:
            best = validation_metrics["cer"]
            model.save_pretrained(checkpoint); processor.save_pretrained(checkpoint)
    (args.out / "training-history.json").write_text(json.dumps(history, indent=2), encoding="utf-8")
    print("Saved best validation checkpoint:", checkpoint)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=["baseline", "train", "test"], required=True)
    parser.add_argument("--archive", type=Path, required=True); parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True); parser.add_argument("--engine", choices=["tesseract", "trocr", "all"], default="all")
    parser.add_argument("--batch-size", type=int, default=4); parser.add_argument("--accumulation", type=int, default=4)
    parser.add_argument("--epochs", type=int, default=3); parser.add_argument("--allow-cpu", action="store_true")
    args = parser.parse_args()
    if min(args.batch_size, args.accumulation, args.epochs) < 1: parser.error("Batch size, accumulation and epochs must be positive.")
    args.out.mkdir(parents=True, exist_ok=True)
    audit = json.loads((args.manifest.parent / "audit.json").read_text(encoding="utf-8"))
    if hashlib.file_digest(args.archive.open("rb"), "sha256").hexdigest() != audit["archive_sha256"]:
        raise ValueError("Dataset changed after audit.")
    if audit["invalid_items"] or audit["repeated_label_rows"] or audit["unlabeled_images"]:
        raise ValueError("Resolve invalid/missing/repeated label rows before running experiments.")
    manifest_sha = hashlib.file_digest(args.manifest.open("rb"), "sha256").hexdigest()
    with zipfile.ZipFile(args.archive) as archive:
        if args.phase == "train": return train(args, archive, audit)
        split = "validation" if args.phase == "baseline" else "test"
        rows = read_rows(args.manifest, split)
        metadata = {"archive_sha256": audit["archive_sha256"], "manifest_sha256": manifest_sha, "seed": 1019, "python": platform.python_version(), "normalization": "NFC + whitespace; case preserved", "tesseract_psm": 7, "decoder": "greedy; max_new_tokens=64", "writer_independent": False}
        if args.engine in {"tesseract", "all"}:
            import pytesseract
            metadata["tesseract_version"] = str(pytesseract.get_tesseract_version())
            def tesseract():
                # An empty OCR prediction still counts as an error; exceptions abort the run.
                return [pytesseract.image_to_string(image_from(archive, r), config="--psm 7", lang="eng").strip() for r in rows]
            evaluate("Tesseract", archive, rows, args.out, split, tesseract, metadata)
        if args.engine in {"trocr", "all"}:
            import torch, transformers
            device = "cuda" if torch.cuda.is_available() else "cpu"
            metadata.update(torch=torch.__version__, transformers=transformers.__version__, device=torch.cuda.get_device_name(0) if device == "cuda" else "CPU")
            for label, checkpoint in [("Pretrained TrOCR-small", MODEL)] + ([("Fine-tuned TrOCR-small", str(args.out / "best-checkpoint"))] if args.phase == "test" else []):
                if label.startswith("Fine-tuned"):
                    training = json.loads((args.out / "training-config.json").read_text(encoding="utf-8"))
                    if training["manifest_sha256"] != manifest_sha or training["archive_sha256"] != audit["archive_sha256"]:
                        raise ValueError("Training and evaluation must use the same frozen archive and split manifest.")
                    metadata["training"] = training
                processor, model = load_trocr(checkpoint, device)
                metadata["checkpoint"] = checkpoint
                metadata["checkpoint_revision"] = getattr(model.config, "_commit_hash", None)
                evaluate(label, archive, rows, args.out, split, lambda: predict_trocr(processor, model, archive, rows, device, args.batch_size), metadata.copy())
                del model
                if device == "cuda": torch.cuda.empty_cache()


if __name__ == "__main__": main()
