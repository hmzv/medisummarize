# Handwriting experiment for FYP I

Use **RxHandBD v3 ML** to study handwritten prescription **word crops**. This experiment does not yet read a whole handwritten report. The app currently uses Tesseract; TrOCR training does not automatically replace its OCR provider.

Dataset: Md Masudul Islam, *RxHandBD: A Handwritten Prescription Word Image Dataset*, v3, DOI [10.17632/dsb5r6vskg.3](https://data.mendeley.com/datasets/dsb5r6vskg/3), CC BY 4.0. Keep this attribution with derivatives. Model: [Microsoft TrOCR-small handwritten](https://huggingface.co/microsoft/trocr-small-handwritten), already fine-tuned on IAM. Preserve its model-card license when distributing weights.

## What has actually been done

The official 128,067,769-byte ML archive was downloaded and its publisher SHA-256 verified. The local audit found:

- 5,578 readable 512×512 images; 4,463 official training images and 1,115 official test images.
- No missing labels, unlabeled images, repeated label rows, exact image duplicates, or conflicting labels on identical images.
- 1,787 distinct literal label strings. The publication describes 1,559 entries; that description differs from the archive's literal strings. Do not silently change labels to force agreement.
- Eight perceptual-similarity flags across training and evaluation. The reviewer inspected all eight pairs and accepted all 50 sampled training labels.
- No writer/prescription IDs in the CSV files. We cannot claim writer-independent evaluation.

The reviewed experiment split is **4,012 train / 446 validation / 1,115 test**, with five excluded training crops. The initial split used seed 1019 and grouped exact image matches. The recorded review excludes the training crops from pairs 1, 4, 5, and 6 and treats the thicker version in pair 8 as a possible duplicate. Pairs 2, 3, and 7 were judged distinct. The validation and official test sets retain their original membership. See [manual-review.json](manual-review.json) for filenames and decisions.

Raw files, manifests, predictions, and weights are stored under ignored `data/runtime/rxhandbd-v3/`, outside Git. The aggregate audit is versioned alongside this README.

The actual local Tesseract validation baseline finished in 198.3 seconds: **78.7% CER, 111.3% WER, 1.1% exact match**, and 0/15 digit-containing crops with a matching digit sequence. This is evidence of a weak cropped-handwriting baseline. The official test set has not been scored. Use `local-baseline-results.json` with the app's Import results action; it remains explicitly labeled validation. The original run includes a generic TrOCR decoding-description field in its metadata; that field was not applied to Tesseract, which used `--psm 7`.

## Your steps in plain words

1. Import the updated `MediSummarize_Handwriting_Kaggle.ipynb` into Kaggle. Enable Internet and one GPU. The notebook downloads the archive and verifies its checksum. If you attach your own copy, set `ARCHIVE` to its path.
2. Run installation, restart the kernel, and run the setup and audit cells. The notebook applies the saved review automatically and writes the exclusions to the audit folder.
3. Run the baseline cell to score Tesseract and pretrained TrOCR on the 446 validation crops.
4. Run training. It starts with batch size 4, gradient accumulation 4, learning rate 0.00005, and three epochs. It saves the checkpoint with the lowest validation character error rate. If the GPU runs out of memory, start a fresh run directory, use batch size 2 and accumulation 8, and record the change.
5. After choosing your settings using validation, set `RUN_FINAL_TEST=True` and run the test cell once. It evaluates all three systems on the same 1,115 test images.
6. Download `experiment-results.json`, the run folder, audit and environment files, and `best-checkpoint`. Import the aggregate JSON in the app's Experiments page.
7. Review at least 50 incorrect predictions, including digit errors. Inspect missing text, extra text, confused letters, wrong numbers, and unreadable originals. Keep representative failures for the report.
8. Send the result JSON, training history, and review notes back here to update the report with measured outcomes.

GPU time depends on Kaggle hardware, queues, download speed, and decoding. The notebook records actual duration; no completed training time is claimed before a run.

## Commands on this computer

From the repository root:

```powershell
.\backend\.venv\Scripts\python.exe experiments/handwriting/audit.py --archive data/runtime/rxhandbd-v3/RxHandBD-ML.zip --out data/runtime/rxhandbd-v3/audit-reviewed --review experiments/handwriting/manual-review.json
.\backend\.venv\Scripts\python.exe experiments/handwriting/run_experiment.py --phase baseline --engine tesseract --archive data/runtime/rxhandbd-v3/RxHandBD-ML.zip --manifest data/runtime/rxhandbd-v3/audit-reviewed/manifest.csv --out data/runtime/rxhandbd-v3/runs/local-baseline-reviewed
```

The baseline intentionally uses raw RGB images with Tesseract `--psm 7` for these cropped labels. It is distinct from the app's full-page preprocessing. Nothing autocorrects medication names or digits. Failed/empty predictions count as errors; exceptions stop the run rather than silently dropping samples.

Metrics: corpus character error rate (CER), word error rate (WER), exact crop match, and digit-sequence match among labels containing digits. CER/WER can exceed 100% when there are many inserted characters. Case is preserved; Unicode and whitespace normalization are documented in every export. Validation and test results must remain separately labeled.

`build_notebook.py` regenerates the notebook from the versioned modules. Notebook cells have not been run on a Kaggle GPU yet; verify the environment there before reporting training as complete.
