# Handwriting experiment for FYP I

Use **RxHandBD v3 ML** to study handwritten prescription **word crops**. This experiment does not yet read a whole handwritten report. The app currently uses Tesseract; TrOCR training does not automatically replace its OCR provider.

Dataset: Md Masudul Islam, *RxHandBD: A Handwritten Prescription Word Image Dataset*, v3, DOI [10.17632/dsb5r6vskg.3](https://data.mendeley.com/datasets/dsb5r6vskg/3), CC BY 4.0. Keep this attribution with derivatives. Model: [Microsoft TrOCR-small handwritten](https://huggingface.co/microsoft/trocr-small-handwritten), already fine-tuned on IAM. Preserve its model-card license when distributing weights.

## What has actually been done

The official 128,067,769-byte ML archive was downloaded and its publisher SHA-256 verified. The local audit found:

- 5,578 readable 512×512 images; 4,463 official training images and 1,115 official test images.
- No missing labels, unlabeled images, repeated label rows, exact image duplicates, or conflicting labels on identical images.
- 1,787 distinct literal label strings. The publication describes 1,559 entries; that description differs from the archive's literal strings. Do not silently change labels to force agreement.
- Eight perceptual-similarity flags across training and evaluation. These require visual inspection; they are not proof of duplication.
- No writer/prescription IDs in the CSV files. We cannot claim writer-independent evaluation.

The deterministic experiment split is **4,017 train / 446 validation / 1,115 test** (seed 1019). Validation is selected from official training data by exact-image group. The official test set stays untouched. A later writer-aware split may be needed if reliable metadata becomes available.

Raw files, manifests, predictions, and weights are stored under ignored `data/runtime/rxhandbd-v3/`, outside Git. The aggregate audit is versioned alongside this README.

The actual local Tesseract validation baseline finished in 198.3 seconds: **78.7% CER, 111.3% WER, 1.1% exact match**, and 0/15 digit-containing crops with a matching digit sequence. This is evidence of a weak cropped-handwriting baseline. The official test set has not been scored. Use `local-baseline-results.json` with the app's Import results action; it remains explicitly labeled validation. The original run includes a generic TrOCR decoding-description field in its metadata; that field was not applied to Tesseract, which used `--psm 7`.

## Your steps in plain words

1. Open `D:/fyp/data/runtime/rxhandbd-v3/audit/review-50.html`. Check whether each picture matches its printed label. In `manual-review.csv`, mark `accept`, `ambiguous`, or `wrong`, and add a note. Do not guess unreadable medicine names.
2. Inspect the image pairs in `near-duplicate-flags.json`. Record whether each is the same crop, a different writing of the same word, or uncertain. Any split changes must happen before final testing and be recorded. Do not edit test labels after seeing model predictions.
3. Open Kaggle → create a notebook → import `MediSummarize_Handwriting_Kaggle.ipynb`. Enable Internet and one GPU. The notebook downloads the exact archive and verifies its checksum. Alternatively attach your copy as a private Kaggle dataset and change `ARCHIVE`.
4. Run the installation cell and restart the kernel. Run the setup/audit cells. Set `MANUAL_REVIEW_DONE=True` only after doing steps 1–2.
5. Run the baseline cell. It reads the validation images with Tesseract and with TrOCR before any training. These are starting scores, not final test scores.
6. Run training. It starts with batch size 4, gradient accumulation 4, learning rate 0.00005, and three epochs. It saves whichever epoch makes the fewest validation character errors. On GPU memory failure, start a fresh run directory using batch size 2 and accumulation 8; record that change.
7. Freeze those choices. Set `RUN_FINAL_TEST=True` and run the test cell once. It evaluates all three systems on the same 1,115 test images. Do not change settings based on these test scores.
8. Download `experiment-results.json`, the complete run folder, audit files, environment files, and `best-checkpoint`. Keep predictions even when they are wrong. The app result importer accepts aggregate JSON, not the model weights.
9. Review at least 50 incorrect predictions, including all interesting digit errors. Categorize missing text, extra text, confused letters, wrong numbers, and unreadable originals. Include representative failures in the report. Scores alone do not prove medical correctness.
10. Send the result JSON and your review notes back here. I can connect the results to the interface, write the actual results section, and integrate an OCR provider if the evidence supports doing so. Full-page reading then needs a separate text-detection/line-cropping stage and full-page evaluation data.

GPU time depends on Kaggle hardware, queues, download speed, and decoding. The notebook records actual duration; no completed training time is claimed before a run.

## Commands on this computer

From the repository root:

```powershell
.\backend\.venv\Scripts\python.exe experiments/handwriting/audit.py --archive data/runtime/rxhandbd-v3/RxHandBD-ML.zip --out data/runtime/rxhandbd-v3/audit
.\backend\.venv\Scripts\python.exe experiments/handwriting/run_experiment.py --phase baseline --engine tesseract --archive data/runtime/rxhandbd-v3/RxHandBD-ML.zip --manifest data/runtime/rxhandbd-v3/audit/manifest.csv --out data/runtime/rxhandbd-v3/runs/local-baseline
```

The baseline intentionally uses raw RGB images with Tesseract `--psm 7` for these cropped labels. It is distinct from the app's full-page preprocessing. Nothing autocorrects medication names or digits. Failed/empty predictions count as errors; exceptions stop the run rather than silently dropping samples.

Metrics: corpus character error rate (CER), word error rate (WER), exact crop match, and digit-sequence match among labels containing digits. CER/WER can exceed 100% when there are many inserted characters. Case is preserved; Unicode and whitespace normalization are documented in every export. Validation and test results must remain separately labeled.

`build_notebook.py` regenerates the notebook from the versioned modules. Notebook cells have not been run on a Kaggle GPU yet; verify the environment there before reporting training as complete.
