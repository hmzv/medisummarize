"""Generate the portable Kaggle notebook from the versioned experiment modules."""
import json
import hashlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
cells = []


def markdown(text):
    cells.append({"cell_type": "markdown", "metadata": {}, "source": text.splitlines(True)})


def code(text):
    cells.append({"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [], "source": text.splitlines(True)})


markdown("""# MediSummarize: handwritten word OCR experiment
Compare Tesseract, pretrained TrOCR-small, and TrOCR-small fine-tuned on RxHandBD v3.

**This notebook has been prepared, not GPU-executed.** It does not establish full-page handwriting recognition or clinical correctness.

1. In Kaggle create a notebook, enable Internet and a GPU, then import this notebook.
2. Run installation once and restart the kernel before continuing.
3. Download the official ML archive below, or attach your own copy as a private Kaggle dataset and set `ARCHIVE`.
4. Audit first. Open `review-50.html`, review the 50 training labels, and inspect the eight near-duplicate flags. Record decisions before training.
5. Run validation baselines; train for three epochs, selecting the checkpoint by validation CER.
6. Freeze settings, then enable the final test cell once. Download all output files, including predictions, audit, environment, and the model checkpoint.

Dataset: Md Masudul Islam, RxHandBD v3, DOI [10.17632/dsb5r6vskg.3](https://data.mendeley.com/datasets/dsb5r6vskg/3), CC BY 4.0. Model: [Microsoft TrOCR-small handwritten](https://huggingface.co/microsoft/trocr-small-handwritten), already fine-tuned on IAM. Keep their attribution and model license with exported weights. No API token or commercial model service is required.
""")
code('''%pip install "transformers==4.57.6" "accelerate==1.12.0" "sentencepiece==0.2.1" "pytesseract==0.3.13" "Pillow>=11,<13"
!apt-get update -qq && apt-get install -y -qq tesseract-ocr tesseract-ocr-eng
''')
markdown("Restart the kernel after installation. Kaggle supplies PyTorch; do not replace its CUDA build unnecessarily.")
code('''from pathlib import Path
import hashlib, json, subprocess, sys, urllib.request
WORK = Path('/kaggle/working/medisummarize-ocr')
WORK.mkdir(parents=True, exist_ok=True)
ARCHIVE = WORK / 'RxHandBD-ML.zip'
URL = 'https://data.mendeley.com/public-files/datasets/dsb5r6vskg/files/98acd360-ba4c-45d0-b614-5d66f4deee47/file_downloaded'
if not ARCHIVE.exists():
    urllib.request.urlretrieve(URL, ARCHIVE)
expected = 'c6371c0a3a89301c0b6b2eac1d2d49f6f3d8e559a7a71b338655dde0a6a63b51'
assert hashlib.file_digest(ARCHIVE.open('rb'), 'sha256').hexdigest() == expected, 'Wrong archive/version'
print('Verified official RxHandBD v3 ML archive')
''')
code("# Write the same audited modules kept in the repository.\nMODULES = " + repr({name: (HERE/name).read_text(encoding="utf-8") for name in ["metrics.py", "audit.py", "run_experiment.py"]}) + "\nfor name, source in MODULES.items():\n    (WORK / name).write_text(source, encoding='utf-8')\n")
code('''import torch, transformers
print('GPU available:', torch.cuda.is_available())
assert torch.cuda.is_available(), 'Enable a Kaggle GPU before training'
environment = {'torch': torch.__version__, 'transformers': transformers.__version__, 'gpu': torch.cuda.get_device_name(0)}
(WORK / 'environment.json').write_text(json.dumps(environment, indent=2))
(WORK / 'pip-freeze.txt').write_text(subprocess.check_output([sys.executable, '-m', 'pip', 'freeze'], text=True))
AUDIT = WORK / 'audit'
subprocess.run([sys.executable, str(WORK/'audit.py'), '--archive', str(ARCHIVE), '--out', str(AUDIT)], check=True)
''')
markdown("Open the generated HTML and CSV from Kaggle’s Output files. Inspect `near-duplicate-flags.json` against the corresponding images before freezing the split. Similarity hashes can collide; do not remove samples just because a flag exists. Any split revision must be documented and happen before final testing.")
code('''MANUAL_REVIEW_DONE = False  # Set True only after inspecting the label sample and near-duplicate flags.
assert MANUAL_REVIEW_DONE, 'Complete the manual dataset review first'
OUT = WORK / 'run-01'
BASE = [sys.executable, str(WORK/'run_experiment.py'), '--archive', str(ARCHIVE), '--manifest', str(AUDIT/'manifest.csv'), '--out', str(OUT)]
subprocess.run(BASE + ['--phase', 'baseline'], check=True)
''')
code('''# Start with batch size 4 and effective batch size 16. On out-of-memory, use batch size 2 and accumulation 8.
# Keep the same final settings for all scored runs; record any exploratory changes.
subprocess.run(BASE + ['--phase', 'train', '--epochs', '3', '--batch-size', '4', '--accumulation', '4'], check=True)
''')
markdown("Review training-history.json and validation predictions. Freeze preprocessing, decoding, and training settings. Do not choose settings by test performance. The final cell evaluates all three systems on the same held-out official test images; the script refuses to overwrite existing result files.")
code('''RUN_FINAL_TEST = False  # Enable once after settings are frozen; do not use test scores to tune the model.
if RUN_FINAL_TEST:
    subprocess.run(BASE + ['--phase', 'test'], check=True)
else:
    print('Final test not run. Validation results are not final test results.')
''')
code('''# Export only aggregate result JSON to the app. Keep raw predictions for your report/error review.
results = [json.loads(p.read_text()) for p in OUT.glob('*-test.json')]
if results:
    (WORK/'experiment-results.json').write_text(json.dumps({'schema_version': 1, 'runs': results}, indent=2))
    print('Download experiment-results.json plus the entire run-01 and audit folders.')
else:
    print('No final test results to export yet.')
''')
notebook = {"cells": cells, "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}, "language_info": {"name": "python", "version": "3.11"}}, "nbformat": 4, "nbformat_minor": 5}
for index, cell in enumerate(cells):
    cell["id"] = f"cell-{index}-" + hashlib.sha256("".join(cell["source"]).encode()).hexdigest()[:8]
(HERE / "MediSummarize_Handwriting_Kaggle.ipynb").write_text(json.dumps(notebook, indent=2), encoding="utf-8")
print("Wrote notebook with", len(cells), "cells")
