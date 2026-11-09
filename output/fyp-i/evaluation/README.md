# Mock evaluation evidence

This is a 9 November 2026 integration dry run, not a clinical or language-model quality result.

- Nine synthetic manifest entries, two conditions each: 18 rows.
- All rows use mock-test-v1, is_mock=true, metrics.reportable=false.
- Numeric debug scores are quarantined and must not enter reported experimental findings.
- The retrieved condition actually chunks, embeds and selects top-four hits per section query with exact cosine ranking. Default embeddings are lexical hashing, not a biomedical encoder.
- The baseline receives concatenated full text from the same case. Both conditions use the same provider and output schema.
- Raw JSON preserves input prompts, allowed source IDs, output, settings, split, input size and durations.
- Cases B and F use companion text files; this run does not benchmark live OCR.
- ID validity is not semantic citation support. Lexical coverage and ROUGE do not establish clinical correctness.

Run the same harness with a real provider and record failures and independent source-support review before claiming a completed FYP I baseline assessment.
