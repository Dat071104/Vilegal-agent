# Track A Portfolio Plan

## Final portfolio target

Show a complete AI engineering demo path that includes synthetic dataset design, validation, optional synthetic fine-tune scaffolding, offline-safe generation tooling, and deployment-ready presentation assets without claiming real legal capability.

## Demo deliverables

- Synthetic-demo dataset config and validator.
- Small tracked sample JSONL for repo inspection.
- Larger local synthetic artifact generation path under `artifacts/`.
- Portfolio screenshots of dataset rows, validation output, and demo workflow.
- README section describing Track A mechanics and Track B governance separation.

## Suggested README screenshots section

- Synthetic sample preview table.
- Validator PASS output screenshot.
- Dry-run generator output screenshot.
- Optional future Kaggle notebook screenshot for Track A2.

## Suggested benchmark table structure

| Demo asset | Metric | Notes |
|---|---|---|
| Synthetic generator | rows generated | Track A only |
| Synthetic validator | valid/invalid rows | Fail-closed safety checks |
| Future Track A2 fine-tune demo | training loss / eval proxy | Synthetic data only |
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
