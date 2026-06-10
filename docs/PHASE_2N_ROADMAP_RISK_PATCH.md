# Phase 2N Roadmap and Risk Correction Patch

**Date:** 2026-06-10  
**Scope:** Documentation, status, and risk correction only.

## Executive summary
- Phase 2N patches the repo so future sessions do not misread the project as training-ready.
- Phase 2M final verdict remains `PHASE 3 READY FOR SCAFFOLD ONLY`.
- Real QA generation, fine-tuning, RAG/vector indexing, dataset publishing, legal-ground-truth promotion, and `approved_for_rag_index=true` remain blocked.

## Required corrections applied

### UTS_VLC viability risk

Risk: UTS_VLC may be non-viable for downstream SFT/RAG.

Evidence:
- 300/300 sampled records typed as `other`.
- 300/300 sampled records missing `document_number`.
- 299/300 sampled records contain multiple article markers.
- Parser produced 20,393 derived candidates but only 150 accepted-for-later-review candidates.
- Acceptance rate is approximately 0.73%, suggesting a document-level source mismatch for downstream article-level SFT/RAG.

Stop condition:
- If an expanded source viability sample still has acceptance rate below 2-5%, or `document_number` and legal metadata remain largely missing, freeze `UTS_VLC` for downstream SFT/RAG and treat it only as a governance/audit case study unless a future human approval gate overrides this.

### Two-track roadmap

Track A - Synthetic Demo / Portfolio Track
- Must run on an isolated branch, e.g. `phase/demo-synthetic-track`.
- May use synthetic QA and synthetic/legal-like fixtures.
- May build a public demo, Kaggle fine-tune demo, benchmark table, screenshots, and CV evidence.
- Must label all data as `synthetic-demo`.
- Must not claim legal correctness, legal-ground-truth status, production readiness, or official legal advice.
- Must not use `UTS_VLC` candidates or real candidate manifest as training/RAG ground truth.

Track B - Governance / Real Legal Corpus Track
- Continues the current safety-gated legal data pipeline.
- Phase 3A is Kaggle/QLoRA scaffold only.
- Phase 3B is QA/SFT dataset gate design.
- Phase 3D or equivalent source viability decision is required before real QA/SFT/RAG.
- Real QA generation, fine-tuning, RAG indexing, dataset publishing, legal-ground-truth promotion, and `approved_for_rag_index=true` remain blocked.

### Portfolio deadline risk

Risk: A purely linear governance pipeline may produce strong docs/tests but no public demo artifact in time for portfolio/CV use.

Mitigation: run Track A synthetic demo branch separately from Track B governance.

### 150-candidate interpretation
- The 150 accepted candidates are sample-scope accepted-for-later-review rows only.
- They are not enough for meaningful SFT.
- They are not approved for RAG.
- They are not legal ground truth.
- They are not approved for dataset publishing.

### Safety boundary preserved
- Phase 3 ready means Phase 3A scaffold-only.
- It does not mean ready for QA generation, fine-tuning, RAG/vector indexing, dataset publishing, or legal-ground-truth use.
