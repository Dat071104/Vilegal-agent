# Track A Synthetic Dataset Quality Report

## Executive verdict

PASS - synthetic-only dataset expansion audit passed on the local 2,500-row artifact.

## Dataset scope

Synthetic-demo QA dataset generated locally under `artifacts/track_a_synthetic_demo/qa_pairs.synthetic-demo.jsonl`.

## Synthetic-only status

- `source=synthetic-demo`
- `is_synthetic=true`
- `is_legal_ground_truth=false`
- `approved_for_rag_index=false`

## Row count

- Total rows: `2500`
- Valid rows: `2500`
- Invalid rows: `0`

## Task type distribution

- `classification`: `625`
- `explanation`: `625`
- `retrieval_style_qa`: `625`
- `drafting_demo`: `625`

## Difficulty distribution

- `easy`: `834`
- `medium`: `833`
- `hard`: `833`

## Duplicate check

- Duplicate IDs: `0`
- Duplicate instruction hashes: `0`
- Duplicate input hashes: `0`
- Duplicate output hashes: `0`
- Duplicate instruction/input/output triplet hashes: `0`

## Safety flag check

- `source_mismatch_count = 0`
- `synthetic_false_count = 0`
- `legal_ground_truth_true_count = 0`
- `approved_for_rag_index_true_count = 0`
- `disclaimer_missing_count = 0`
- `official_authority_claim_count = 0`

## Split summary

- Train: `2000`
- Validation: `250`
- Test: `250`
- Seed: `42`

## Blocked claims

- Not legal advice
- Not official legal text
- Not legal-ground-truth
- Does not unblock Track B

## Artifact policy

The full generated dataset, audit report, and split files remain under `artifacts/` and are not committed.

## Next step

Track A2 Kaggle synthetic fine-tune demo using local synthetic split artifacts only.
