# Project Roadmap

This document reflects the audited safe path, not the original aspirational roadmap.

- [x] **Phase 0: Project Bootstrap Structure**
- [x] **Phase 1: Data Source Audit & Scaffolding**
- [x] **Phase 2: Data Pipeline & Processing (through 2M readiness audit)**
- [ ] **Phase 3: RAG Knowledge Base**
  Phase 3 execution remains blocked. Only Phase 3A scaffold-only work is currently allowed, and Phase 3A is completed only if the scaffold validator passes.
- [ ] **Phase 4: Fine-tuning (QLoRA) (blocked)**
- [ ] **Phase 5: LangGraph Agent Orchestration (blocked)**
- [ ] **Phase 6: Evaluation & Deployment (blocked)**

This document records the current post-Phase-2M and Phase-2N roadmap posture.

## Current interpretation
- Phase 2M final verdict: `PHASE 3 READY FOR SCAFFOLD ONLY`.
- `phase3_scaffold_ready=true`
- `qa_generation_ready=false`
- `fine_tuning_ready=false`
- `rag_indexing_ready=false`
- Phase 3 ready means Phase 3A scaffold-only. It does not mean ready for QA generation, fine-tuning, RAG/vector indexing, dataset publishing, or legal-ground-truth use.
- Phase 3A completion requires the scaffold validator to pass before the scaffold can be treated as complete.
- The 150 accepted candidates are sample-scope accepted-for-later-review rows only. They are not enough for meaningful SFT, not approved for RAG, not legal ground truth, and not approved for dataset publishing.

## Source viability concern

Risk: UTS_VLC may be non-viable for downstream SFT/RAG.

Evidence:
- 300/300 sampled records typed as `other`.
- 300/300 sampled records missing `document_number`.
- 299/300 sampled records contain multiple article markers.
- Parser produced 20,393 derived candidates but only 150 accepted-for-later-review candidates.
- Acceptance rate is approximately 0.73%, suggesting a document-level source mismatch for downstream article-level SFT/RAG.

Stop condition:
- If an expanded source viability sample still has acceptance rate below 2-5%, or `document_number` and legal metadata remain largely missing, freeze `UTS_VLC` for downstream SFT/RAG and treat it only as a governance/audit case study unless a future human approval gate overrides this.

## Track A - Synthetic Demo / Portfolio Track
- Must run on an isolated branch, e.g. `phase/demo-synthetic-track`.
- May use synthetic QA and synthetic/legal-like fixtures.
- May build a public demo, Kaggle fine-tune demo, benchmark table, screenshots, and CV evidence.
- Must label all data as `synthetic-demo`.
- Track A synthetic demo branch exists for portfolio acceleration.
- Synthetic demo data is not legal advice and not official legal text.
- Track A does not change Track B safety gates.
- Track A1.5 adds local synthetic dataset expansion, audit, and split workflow under `artifacts/` only.
- Future Track A2 may do a Kaggle fine-tune demo using synthetic data only.
- Must not claim legal correctness, legal-ground-truth status, production readiness, or official legal advice.
- Must not use `UTS_VLC` candidates or real candidate manifest as training/RAG ground truth.

## Track B - Governance / Real Legal Corpus Track
- Continues the current safety-gated legal data pipeline.
- Phase 3A is Kaggle/QLoRA scaffold only and validator-gated.
- Phase 3B is QA/SFT dataset gate design.
- Phase 3D or equivalent source viability decision is required before real QA/SFT/RAG.
- Real QA generation, fine-tuning, RAG indexing, dataset publishing, real legal corpus use, legal-ground-truth promotion, and `approved_for_rag_index=true` remain blocked.
- Track A synthetic demo work does not unblock Track B real QA, SFT, or RAG.

## Delivery risk

Risk: A purely linear governance pipeline may produce strong docs/tests but no public demo artifact in time for portfolio/CV use.

Mitigation: run Track A synthetic demo branch separately from Track B governance.

## Phase summary

| Phase | Status |
|---|---|
| Phase 0: Project Bootstrap Structure | Complete |
| Phase 1: Data Source Audit & Scaffolding | Complete with risks |
| Phase 2N: Roadmap and Risk Correction Patch | Complete |
| Track A0/A1: Synthetic demo foundation | Complete on `phase/demo-synthetic-track` only |
| Track A1.5: Synthetic dataset expansion + quality audit | Complete on `phase/demo-synthetic-track` only |
| Track A2: Kaggle synthetic fine-tune demo | Planned |
| Phase 3A: Kaggle/QLoRA scaffold | Complete only if validator passes |
| Phase 3B: QA/SFT dataset gate design | Planned |
| Phase 3D: Source viability decision | Required before real QA/SFT/RAG |
| Real QA generation / fine-tuning / RAG / publishing | Blocked |
