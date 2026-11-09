# MediSummarize AI

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

FYP I demonstrators and reviewers examining a medical-document summarization prototype. The source-review workflow is intended for people checking extracted medical text and summaries.

## Product Purpose

Upload a fictional patient's documents, check extracted text, and review a structured summary against its cited sources. Show experiment results inside the app while model training runs in Kaggle.

## Operating Context

Existing React/TypeScript frontend and FastAPI backend. Users sign in, create isolated patient records, upload documents, inspect OCR text, generate summaries, and open cited source pages. Experiments are conducted externally and their results should be visible in the application.

## Capabilities and Constraints

Preserve authentication, record isolation, upload validation, extraction status, retry behavior, source review, summary exports, and deletion confirmations. Tesseract currently handles OCR; handwriting recognition has not been validated. Generation currently uses an explicit mock mode. Trained-model quality and handwriting benchmarks are not established. Never present planned experiments or synthetic mock output as measured results.

## Brand Commitments

Keep the name MediSummarize AI. The user requested a frontend redesign, image mockups before implementation, and design options to choose from.

## Evidence on Hand

The existing local prototype and FYP I submission package are in this repository. Model training and real evaluation results remain outstanding. Use clearly labeled synthetic examples in design mockups.

## Product Principles

- Keep sources visible and easy to check.
- Distinguish extracted text, generated summaries, and measured results.
- Report processing failures and unrun experiments honestly.
- Keep Kaggle training separate from everyday document review.

## Open Decisions

The user approved Clinical clarity (B), original split-review layout, then explicitly chose a code-led build with the image as a visual guide and no strict matching gates. The implemented Experiments view imports owner-scoped aggregate JSON, distinguishes validation/test splits, and displays planned models without invented scores. Real-model quality and whole-page handwriting recognition remain open research questions.
