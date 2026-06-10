# ViLegal Agent

A portfolio-grade Vietnamese Legal AI Agent.

**Current Status:** Phase 3A Kaggle/QLoRA scaffold-only implemented. Phase 3A is completed only if the scaffold validator passes. `Phase 3 ready` still means `Phase 3A scaffold-only`. **NOT PRODUCTION READY**.

## Disclaimer
**SAFETY & LEGAL DISCLAIMER:** This is an educational project and does not provide legal advice. Do not use for actual legal compliance without consulting a qualified attorney.

## Current Safety Boundary
- Phase 2M final verdict: `PHASE 3 READY FOR SCAFFOLD ONLY`.
- Phase 3A scaffold verdict: `SCAFFOLD ONLY - VALIDATOR REQUIRED`.
- `phase3_scaffold_ready=true`
- `qa_generation_ready=false`
- `fine_tuning_ready=false`
- `rag_indexing_ready=false`
- Phase 3 ready means Phase 3A scaffold-only. It does not mean ready for QA generation, fine-tuning, RAG/vector indexing, dataset publishing, real legal corpus use, or legal-ground-truth use.
- The 150 accepted candidates are sample-scope accepted-for-later-review rows only. They are not enough for meaningful SFT, not approved for RAG, not legal ground truth, and not approved for dataset publishing.
- Phase 3A completion requires `python scripts/validate_phase3a_scaffold.py` to pass.

## Current Roadmap Tracks
### Track A - Synthetic Demo / Portfolio Track
- Must run on an isolated branch, e.g. `phase/demo-synthetic-track`.
- May use synthetic QA and synthetic/legal-like fixtures.
- May build a public demo, Kaggle fine-tune demo, benchmark table, screenshots, and CV evidence.
- Must label all data as `synthetic-demo`.
- Must not claim legal correctness, legal-ground-truth status, production readiness, or official legal advice.
- Must not use `UTS_VLC` candidates or the real candidate manifest as training or RAG ground truth.

### Track B - Governance / Real Legal Corpus Track
- Continues the current safety-gated legal data pipeline.
- Phase 3A is Kaggle/QLoRA scaffold only and is complete only when the scaffold validator passes.
- Phase 3B is QA/SFT dataset gate design.
- Phase 3D or equivalent source viability decision is required before real QA/SFT/RAG.
- Real QA generation, fine-tuning, RAG indexing, dataset publishing, real legal corpus use, legal-ground-truth promotion, and `approved_for_rag_index=true` remain blocked.

## Planned Architecture
1. **Data Pipeline:** Sample-only ingestion, provenance gates, and deterministic review buckets.
2. **Fine-tuned LLM:** Scaffold planning only. Actual training blocked.
3. **LangGraph Agent:** Blocked for now.
4. **RAG + Citation Verification:** Scaffold planning only. Actual indexing blocked.
5. **Evaluation:** Blocked for now.
6. **Deployment:** Blocked for now.

## Data Handling Policy
**Raw legal data and generated model artifacts are NOT committed to git.** Please refer to `data/README.md` and `.gitignore` for details.

## Phase Roadmap
- **Phase 0:** Project Bootstrap Structure (Complete)
- **Phase 1:** Data Source Audit & Scaffolding (Complete)
- **Phase 2:** Data Pipeline & Processing (Complete through 2M readiness audit)
- **Phase 2N:** Roadmap and Risk Correction Patch (Complete)
- **Phase 3:** RAG Knowledge Base (Phase 3A scaffold only allowed; validator-gated; execution blocked)
- **Phase 4:** Fine-tuning (QLoRA) (Blocked)
- **Phase 5:** LangGraph Agent Orchestration (Blocked)
- **Phase 6:** Evaluation & Deployment (Blocked)
See [docs/ROADMAP.md](/D:/Project%20cua%20Dat/vilegal-agent/docs/ROADMAP.md), [docs/PHASE_2N_ROADMAP_RISK_PATCH.md](/D:/Project%20cua%20Dat/vilegal-agent/docs/PHASE_2N_ROADMAP_RISK_PATCH.md), and [docs/PHASE_3A_KAGGLE_QLORA_SCAFFOLD.md](/D:/Project%20cua%20Dat/vilegal-agent/docs/PHASE_3A_KAGGLE_QLORA_SCAFFOLD.md) for the current governance and synthetic-demo split.
