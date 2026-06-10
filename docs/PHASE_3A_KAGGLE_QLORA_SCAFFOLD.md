# Phase 3A - Kaggle/QLoRA Scaffold Only

## Executive verdict

Phase 3A is **scaffold-only**. Completion means the scaffold validator passes and the scaffold-only boundary remains intact.

## What was added

- `configs/phase3a_qlora_scaffold.yaml` for the default scaffold-only gate.
- `notebooks/phase3a_kaggle_qlora_scaffold.ipynb` as a safe notebook shell with no training execution.
- `scripts/validate_phase3a_scaffold.py` to enforce config, notebook, and docs boundaries.
- `tests/test_phase3a_scaffold.py` to cover both safe and unsafe cases.
- `src/vilegal/training/` helpers for stdlib-only config parsing and safety validation.

## What this phase allows

- Scaffold-only planning for a future Kaggle/QLoRA workflow.
- Config review and safety validation.
- Notebook structure review with blocked examples documented only in markdown.
- Documentation of future gates and sequencing.

## What remains blocked

- QA generation blocked.
- Fine-tuning blocked.
- RAG/vector indexing blocked.
- Dataset publishing blocked.
- Real legal corpus use blocked.
- Model download by default blocked.
- Hub push blocked.
- Adapter or checkpoint saving blocked.
- Legal-ground-truth promotion blocked.
- `approved_for_rag_index=true` remains blocked.

## Why training is still blocked

The current Track B corpus governance state does not approve QA/SFT generation, real-corpus training, RAG indexing, or dataset publication. The reviewed corpus remains sample-scope and governance-focused, source viability is unresolved, and future human gate required status remains active before any real training decision.

## Relation to the Phase 2N two-track roadmap

Phase 2N split the project into two explicit tracks:

- Track B governance continues here.
- Track A synthetic demo is separate and must use an isolated branch.

This Phase 3A work belongs only to Track B. It preserves the audited boundary that scaffold planning is allowed while execution remains blocked.

## Future Phase 3B recommendation

Proceed to **QA/SFT Dataset Gate Design** before any real training work. That gate should define approved dataset inputs, review thresholds, train/validation/test split policy, evaluation criteria, and human approvals required to move beyond scaffold-only status.

## Boundary statement

This phase does **not** claim that any model is trained. This phase does **not** claim that any legal corpus is ready for SFT or RAG. The validator exists specifically to prevent the scaffold from being mistaken for training readiness.
