# Track A Synthetic Dataset Expansion

## Purpose

Track A1.5 expands the synthetic-demo dataset path for portfolio use only. The generated data remains synthetic-demo only and does not use real legal corpus content, `UTS_VLC` candidates, or `corpus_candidate_manifest`.

## Why this dataset is synthetic-demo only

- It is generated from deterministic synthetic templates.
- It is labeled `synthetic-demo` on every row.
- It is not legal advice.
- It is not official legal text.
- It is not legal-ground-truth.

## Why this does not unblock Track B

Track B governance remains unchanged. Real legal corpus QA generation, real legal fine-tuning, RAG/vector indexing, dataset publication, legal-ground-truth promotion, and `approved_for_rag_index=true` remain blocked.

## How to regenerate the artifact locally

```powershell
python scripts/generate_synthetic_demo_qa.py --dry-run --count 2500 --output artifacts/track_a_synthetic_demo/qa_pairs.synthetic-demo.jsonl
```

## How to audit it

```powershell
python scripts/audit_synthetic_demo_qa.py artifacts/track_a_synthetic_demo/qa_pairs.synthetic-demo.jsonl --min-rows 2500 --report-out artifacts/track_a_synthetic_demo/audit_report.json
```

## How to split it

```powershell
python scripts/split_synthetic_demo_qa.py artifacts/track_a_synthetic_demo/qa_pairs.synthetic-demo.jsonl --output-dir artifacts/track_a_synthetic_demo/splits --seed 42
```

## Why full generated data is not committed

- The full generated dataset is a local demo artifact, not a governed dataset release.
- `artifacts/` remains untracked.
- Only summary metrics and small tracked synthetic samples belong in git at this stage.

## How Track A2 will use the split files

Track A2 may use the local synthetic split files under `artifacts/track_a_synthetic_demo/splits/` for a Kaggle synthetic fine-tune demo. That future step must still remain synthetic-only and must not claim real legal capability.
