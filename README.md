# ViLegal Agent

A portfolio-grade Vietnamese Legal AI Agent.

**Current Status:** Phase 2 readiness audit complete through Phase 2M. **PHASE 3 READY FOR SCAFFOLD ONLY**. Actual QA generation, fine-tuning, and RAG indexing remain blocked.

## Disclaimer
**SAFETY & LEGAL DISCLAIMER:** This is an educational project and does not provide legal advice. Do not use for actual legal compliance without consulting a qualified attorney.

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
- **Phase 3:** RAG Knowledge Base (Phase 3A scaffold only allowed; execution blocked)
- **Phase 4:** Fine-tuning (QLoRA) (Blocked)
- **Phase 5:** LangGraph Agent Orchestration (Blocked)
- **Phase 6:** Evaluation & Deployment (Blocked)
