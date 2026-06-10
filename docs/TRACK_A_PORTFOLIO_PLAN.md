# Track A Portfolio Plan

## Final portfolio target

Show a complete AI engineering demo path that includes synthetic dataset design, validation, optional synthetic fine-tune scaffolding, offline-safe generation tooling, and deployment-ready presentation assets without claiming real legal capability.

## Demo deliverables

- Synthetic-demo dataset config and validator.
- Small tracked sample JSONL for repo inspection.
- Larger local synthetic artifact generation path under `artifacts/`.
- Portfolio screenshots of dataset rows, validation output, and demo workflow.
- README section describing Track A mechanics and Track B governance separation.
- **Track A2:** Kaggle synthetic fine-tune demo notebook, dataset packaging script, validator, tests, and docs.
  - Synthetic fine-tune of a small instruct model on synthetic-demo data (Kaggle-only).
  - Benchmark comparison: base vs LoRA adapter on synthetic test set.
  - Screenshot evidence from Kaggle notebook run.
  - Benchmark JSON exported from `/kaggle/working/`.
  - `SYNTHETIC DEMO ONLY — NOT LEGAL ADVICE` disclaimer on all outputs.

## Suggested README screenshots section

- Synthetic sample preview table.
- Validator PASS output screenshot.
- Dry-run generator output screenshot.
- Track A2 Kaggle notebook screenshot (training loss curve + benchmark table).
- Benchmark JSON screenshot from `/kaggle/working/track_a_benchmark_results.json`.

## Suggested benchmark table structure

| Demo asset | Metric | Notes |
|---|---|---|
| Synthetic generator | rows generated | Track A only |
| Synthetic validator | valid/invalid rows | Fail-closed safety checks |
| Track A2 fine-tune demo | training loss / eval proxy | Synthetic data only — not legal accuracy |
| Future Track A3 retrieval demo | canned QA accuracy | Synthetic retrieval corpus only |

## Suggested CV bullet points

- Built a fail-closed synthetic data generation and validation pipeline for a Vietnamese legal AI portfolio demo, with explicit separation from real-corpus governance work.
- Added offline-safe CLI tooling, JSONL schema validation, and branch-isolated Track A documentation for synthetic-only QA dataset creation.
- Designed a two-track repository workflow separating synthetic AI engineering demos from legal data governance and readiness auditing.

## Clear disclaimer wording

Use this wording in README, slides, and portfolio pages:

`Synthetic demo data only. Not legal advice. Not official legal text. Track A demonstrates AI engineering mechanics, not real legal capability.`

## Separation of project narratives

- AI engineering demo: synthetic fine-tune, synthetic retrieval, demo deployment, screenshots, and benchmark presentation.
- Data governance project: legal corpus readiness pipeline, provenance controls, review gates, and blocked real-corpus QA/SFT/RAG decisions.
