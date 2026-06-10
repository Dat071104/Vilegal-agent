# Track A Synthetic Demo

## Purpose

Track A is separate from Track B. Track A exists for portfolio/demo mechanics only and does not change Track B governance or safety gates.

## Scope

- Data is synthetic-demo only.
- It is not legal advice.
- It is not official legal text.
- It is not legal-ground-truth.
- It does not use `UTS_VLC` candidates.
- It does not use `corpus_candidate_manifest`.
- It does not unblock Track B real QA, SFT, or RAG work.

## What this branch adds

- A synthetic-demo config with fail-closed safety flags.
- A small tracked sample JSONL file for tests and portfolio previews.
- An offline generator for template-based synthetic rows.
- A validator that enforces labels, disclaimers, and non-authoritative wording.

## How to generate sample data

Tracked sample refresh:

```powershell
python scripts/generate_synthetic_demo_qa.py --dry-run --count 10 --output data/synthetic_demo/sample_qa.jsonl
```

Larger local synthetic artifact:

```powershell
python scripts/generate_synthetic_demo_qa.py --count 2500 --output artifacts/track_a_synthetic_demo/qa_pairs.synthetic-demo.jsonl
```

## How to validate data

```powershell
python scripts/validate_synthetic_demo_qa.py data/synthetic_demo/sample_qa.jsonl
python scripts/validate_synthetic_demo_qa.py artifacts/track_a_synthetic_demo/qa_pairs.synthetic-demo.jsonl
```

## Safety boundary

- Every row must keep `source=synthetic-demo`.
- Every row must keep `is_synthetic=true`.
- Every row must keep `is_legal_ground_truth=false`.
- Every row must keep `approved_for_rag_index=false`.
- Every row must keep the disclaimer that states synthetic demo only, not legal advice, and not official legal text.
- Generated full outputs belong under `artifacts/` and are not committed by default.

## Future phases

- Track A2: Kaggle synthetic fine-tune demo using synthetic data only.
- Track A3: Local demo or RAG-like synthetic retrieval using synthetic content only.
- Track A4: Public portfolio packaging with screenshots, README assets, and benchmark presentation.
