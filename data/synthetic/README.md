# Synthetic demonstration data

All files here are **SYNTHETIC — NOT A REAL PATIENT**. Do not copy private records into this folder.

Upload the files under each case folder into a **separate** record container (except Case A and Case D, which are multi-document records). Case G is two patients: `patient_1.txt` and `patient_2.txt` must never share a record.

`manifest.json` is the source of truth for splits, files, and reference facts. Reference facts belong with the case. They are not experimental results.

| Case | Folder | Split | Purpose | Upload |
|------|--------|-------|---------|--------|
| A | `case_a_longitudinal/` | development | Labs, prescription, discharge | all three `.txt` files into one record |
| B | `case_b_ocr/` | held-out | Scanned-style image requiring OCR | `scan.png` |
| C | `case_c_missing/` | held-out | Missing allergy and medication sections | `discharge_no_allergies.txt` |
| D | `case_d_conflict/` | held-out | Conflicting medications across dates | both notes into one record |
| E | `case_e_negation/` | development | Documented denial of a symptom | `discharge.txt` |
| F | `case_f_poor_ocr/` | held-out | Poor OCR affecting a number | `noisy_scan.png` and/or `noisy_ocr_transcript.txt` |
| G | `case_g_isolation/` | held-out | Similar wording, two patients | `patient_1.txt` and `patient_2.txt` in **two** records |
| H | `case_h_injection/` | development | Prompt-injection text inside a document | `injected_note.txt` |

If `scan.png` or `noisy_scan.png` is missing, generate them:

```powershell
cd D:\fyp\backend
.\.venv\Scripts\python ..\data\synthetic\_render_images.py
```
