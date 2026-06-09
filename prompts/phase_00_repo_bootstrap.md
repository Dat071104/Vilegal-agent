"D:\Project cua Dat\vilegal-agent\ai-agent-workspace-pack\START_HERE.md" You are working inside the repository vilegal-agent.

Goal:
Bootstrap a safe, phase-based AI engineering workspace for the ViLegal Agent flagship project. This repository will become a Vietnamese Legal AI Agent with structured legal data processing, QLoRA fine-tuning, LangGraph orchestration, RAG retrieval, citation verification, reproducible evaluation, and public deployment documentation.

Operating rules:

Chat first, file later. Before writing or modifying files, summarize the exact intended file changes.
Do not use git add ..
Do not commit raw datasets, API keys, model weights, generated large files, cache folders, or local secrets.
Keep implementation logs in _ops/.
Every phase must follow: PLAN -> IMPLEMENT -> TEST -> SELF-AUDIT -> REPORT -> COMMIT SUGGESTION.
Do not start a later phase until the current phase passes its gate.
Prefer small, reviewable commits.
If a claim is uncertain, mark it as an assumption and add it to _ops/RISK_REGISTER.md.

Phase 0 task:
Create only the project bootstrap structure and documentation. Do not implement scraper, training, RAG, or deployment code yet.

Required files/folders:

README.md
LICENSE if not already present
.gitignore
docs/ROADMAP.md
docs/ARCHITECTURE.md
docs/DATA_SOURCE_AUDIT.md
docs/EVALUATION_PLAN.md
docs/DECISIONS.md
_ops/IMPLEMENTATION_LOG.md
_ops/PHASE_STATUS.md
_ops/DECISION_LOG.md
_ops/RISK_REGISTER.md
_ops/PROMPT_HISTORY.md
prompts/phase_00_repo_bootstrap.md
prompts/phase_01_data_audit.md
data/README.md
data/raw/.gitkeep
data/processed/.gitkeep
notebooks/README.md
models/README.md
src/vilegal/__init__.py
tests/README.md
scripts/README.md

README requirements:

Explain the project as a portfolio-grade Vietnamese Legal AI Agent.
Clearly state current status: Phase 0 bootstrap, not production-ready.
Include planned architecture: Data Pipeline -> Fine-tuned LLM -> LangGraph Agent -> RAG + Citation Verification -> Evaluation -> Deployment.
Include safety/legal disclaimer: educational project, not legal advice.
Include data handling policy: raw legal data and generated model artifacts are not committed to git.
Include phase roadmap.

After creating files:

Run git status --short.
Run a lightweight sanity check appropriate for the created files.
Produce PHASE 0 BOOTSTRAP REPORT with:
Files created/changed
What was intentionally not implemented
Risks
Next recommended phase
Exact git add command with explicit file paths only
