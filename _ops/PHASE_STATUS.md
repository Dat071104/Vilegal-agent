# Phase Status

**Current phase:** Track A2.2 - Kaggle 7B Unsloth Runtime Patch  
**Current verdict:** PASS - UNSLOTH 7B RUNTIME PATCH IMPLEMENTED

## Current readiness flags

- `phase3_scaffold_ready=true`
- `track_a_synthetic_demo_foundation_ready=true`
- `track_a_synthetic_dataset_audit_ready=true`
- `track_a_kaggle_finetune_demo_ready=true`
- `qa_generation_ready=false`
- `fine_tuning_ready=false`
- `rag_indexing_ready=false`
- `dataset_publishing_ready=false`
- `real_legal_corpus_use_ready=false`
- `track_b_safety_gates_unchanged=true`
- `approved_for_rag_index=true` remains blocked and must stay unset.

## Phase gates

| Phase | Status | Completed |
|---|---|---|
| Phase 0: Project bootstrap structure | PASS | 2026-06-09 |
| Phase 1: Data source audit and scaffolding | PASS WITH RISKS | 2026-06-09 |
| Phase 2: Data pipeline and processing | PASS WITH RISKS | 2026-06-10 |
| Phase 2M: Full Phase 3 readiness audit | PASS - PHASE 3 READY FOR SCAFFOLD ONLY | 2026-06-10 |
| Phase 2N: Roadmap and risk correction patch | PASS | 2026-06-10 |
| Track A0/A1: Synthetic demo foundation | PASS - SYNTHETIC DATA ONLY | 2026-06-10 |
| Track A1.5: Synthetic dataset expansion + quality audit | PASS - ARTIFACTS ONLY | 2026-06-10 |
| Track A2/A2.2: Kaggle Unsloth 7B Runtime Patch | PASS - SYNTHETIC ONLY | 2026-06-10 |
| Phase 3A: Kaggle/QLoRA scaffold only | PASS - VALIDATOR REQUIRED AND PASSED | 2026-06-10 |
| Phase 3B: QA/SFT dataset gate design | NOT STARTED - DESIGN ONLY | - |
| Phase 3D: Source viability decision | REQUIRED BEFORE REAL QA/SFT/RAG | - |
| Phase 3: RAG knowledge base | BLOCKED FOR REAL DATA | - |
| Phase 4: Fine-tuning | BLOCKED FOR REAL DATA | - |
| Phase 5: Agent orchestration | NOT STARTED | - |
| Phase 6: Evaluation and deployment | NOT STARTED | - |

## Phase 2M interpretation carried forward

- `CONFIRMED`: the prior stale license claims were corrected during the big audit.
- `CONFIRMED`: the current Hugging Face card labels are `MIT` for `undertheseanlp/UTS_VLC` and `CC-BY-4.0` for both `th1nhng0/vietnamese-legal-documents` and `duyet/vietnamese-legal-instruct`.
- `CONFIRMED`: generated instruction and QA datasets are not treated as legal ground truth in the updated audit docs.
- `NEEDS MANUAL REVIEW`: non-synthetic source provenance and relicensing remain unresolved.
- `CONFIRMED`: Phase 3 ready means Phase 3A scaffold-only. It does not mean ready for QA generation, fine-tuning, RAG/vector indexing, dataset publishing, or legal-ground-truth use.
- `CONFIRMED`: Phase 3A is completed only when the scaffold validator passes.
- `CONFIRMED`: real QA generation, fine-tuning, RAG indexing, dataset publishing, real legal corpus use, legal-ground-truth promotion, and `approved_for_rag_index=true` remain blocked.
- `CONFIRMED`: Track A synthetic demo branch exists for portfolio acceleration and does not change Track B safety gates.
- `CONFIRMED`: synthetic demo data is not legal advice and not official legal text.
- `CONFIRMED`: Track A1.5 expands the local synthetic dataset, audit, and split workflow under artifacts only.
- `CONFIRMED`: Track A2 now targets `unsloth/Qwen2.5-7B-Instruct` for the flagship Kaggle run, with `Qwen/Qwen2.5-3B-Instruct` as the local/dev baseline and `Qwen/Qwen2.5-0.5B-Instruct` as smoke-test only.

## Candidate interpretation

- The 150 accepted candidates are sample-scope accepted-for-later-review rows only.
- They are not enough for meaningful SFT.
- They are not approved for RAG.
- They are not legal ground truth.
- They are not approved for dataset publishing.

## UTS_VLC viability stop condition

- Risk: `UTS_VLC` may be non-viable for downstream SFT/RAG.
- Evidence: 300/300 sampled records typed as `other`; 300/300 sampled records missing `document_number`; 299/300 sampled records contain multiple article markers; parser produced 20,393 derived candidates but only 150 accepted-for-later-review candidates; acceptance rate is approximately 0.73%, suggesting a document-level source mismatch for downstream article-level SFT/RAG.
- If an expanded source viability sample still has acceptance rate below 2-5%, or `document_number` and legal metadata remain largely missing, freeze `UTS_VLC` for downstream SFT/RAG and treat it only as a governance/audit case study unless a future human approval gate overrides this.

## Phase 1 Reproducibility Patch

**Date:** 2026-06-09  
**Issue:** `data/processed/sample_legal_articles.jsonl` was gitignored, breaking the audit validation command on a fresh clone.  
**Fix:** Moved synthetic fixture to `tests/fixtures/synthetic_legal_articles.jsonl` (git-tracked). Updated default path in `scripts/inspect_data_source_sample.py` and all doc references.  
**Result:** PASS

## Phase 2A — Sample-only ingestion scaffold

**Date:** 2026-06-09
**Verdict:** PASS
- `src/vilegal/ingestion/` package created (5 modules).
- `scripts/ingest_hf_sample.py` CLI created.
- `tests/test_ingestion.py` — 44 new tests, all passing.
- `tests/fixtures/malformed_legal_articles.jsonl` created.
- Offline dry-run: 3 records, 0 rejected, quality gate PASS, all metrics 100%.
- `artifacts/` confirmed gitignored — no generated data committed.
- **Bulk download: BLOCKED** (unchanged).
- **Phase 2B: DO NOT START** until human approves bulk-download gates in `docs/PHASE_2_PRE_AUDIT.md`.

## Phase 2B — Online smoke test

**Date:** 2026-06-09
**Verdict:** PASS WITH DISCOVERIES

| Source | Records | Normalized | Rejected | Quality Gate | Notes |
|---|---|---|---|---|---|
| `undertheseanlp/UTS_VLC` | 10 | 10 | 0 | ✅ PASS | MIT license. Year-based splits (uses `2026`). Clean legal corpus. |
| `duyet/vietnamese-legal-instruct` | 10 | 10 | 0 | ✅ PASS | CC-BY-4.0, attribution preserved. Conversations schema normalized. NOT legal ground truth. |
| `th1nhng0/vietnamese-legal-documents` | — | — | — | DEFERRED | Not required for Phase 2B gate. |

**Key discoveries documented:**
1. UTS_VLC uses year-based HF splits (`2026`, `2026_01`, `2023`, `2021`), not `train`. Fixed via `default_split` in registry.
2. `duyet/vietnamese-legal-instruct` uses a `conversations` list schema. Normalizer updated to extract the `user` turn as primary text. Assistant turn is NOT promoted to legal ground truth.

**Code changes triggered by smoke test:**
- `source_registry.py` — `ALIASES` dict + `default_split` field
- `normalizers.py` — conversations format extractor
- `scripts/ingest_hf_sample.py` — `--hf-split` defaults to source `default_split`
- `tests/test_ingestion.py` — 3 new tests; total now 79/79 passing

**Bulk download: BLOCKED** (unchanged)
**Phase 2C: DO NOT START** until human approves bulk-download gates.

## Phase 2C — Human Gate Pack

**Date:** 2026-06-09
**Verdict:** PASS

- `docs/ATTRIBUTION.md` created with MIT and CC-BY-4.0 templates.
- `docs/DATA_USE_POLICY.md` created defining git tracking rules (no raw legal data).
- `docs/BULK_INGESTION_GATE.md` created establishing the 7 human-review gates.
- `docs/PHASE_2C_HUMAN_GATE_REPORT.md` created summarizing status.
- **Phase 2D (Bulk Ingestion): BLOCKED**. Must not start until the human reviewer completes the checklist in `docs/BULK_INGESTION_GATE.md`.

## Phase 2D — Controlled local ingestion

**Date:** 2026-06-09
**Verdict:** PASS WITH RISKS

- All 7 gates in `docs/BULK_INGESTION_GATE.md` checked.
- `MAX_RECORDS_HARD_CAP` updated to 1000 and tests passing.
- Controlled ingestion run for `uts_vlc` (300 records) and `duyet_legal_instruct` (1000 records). 
- All 1300 ingested records passed the quality gates with 100% success rate.
- Optional ingestion for `th1nhng0_legal_documents` failed (HF config required) and deferred.
- **Phase 2E (QA/RAG/Fine-Tuning): DO NOT START**

## Phase 2E - Data Content Quality Audit

**Date:** 2026-06-10
**Verdict:** PASS WITH RISKS

- Required Phase 2D artifacts for `uts_vlc` and `duyet_legal_instruct` were present locally and audited in place.
- `UTS_VLC` findings:
  - `300/300` normalized rows are typed as `other`.
  - `300/300` rows are missing `document_number`.
  - `0/300` rows have empty or near-empty text.
  - `299/300` rows contain multiple article markers, so article parsing is possible, but only from the long-form text field.
- `duyet_legal_instruct` findings:
  - Normalized `text` matches the user turn in `1000/1000` rows.
  - Assistant answers remain in `raw_metadata` in `1000/1000` rows.
  - `935/1000` assistant answers contain citation-like signals, but this does not establish correctness.
  - `1000/1000` rows are missing `title` and `document_number`.
- Cross-source findings:
  - Provenance fields are complete across all `1300` audited records.
  - Cross-source duplicate `record_id`: `0`
  - Cross-source duplicate `source_id`: `0`
  - Cross-source exact duplicate normalized text: `0`
- Readiness matrix:
  - RAG corpus readiness: **PASS WITH RISKS** for `UTS_VLC` only
  - SFT dataset readiness: **BLOCKED**
  - Evaluation dataset readiness: **BLOCKED**
  - Public release readiness: **BLOCKED**
- Allowed next steps:
  - `UTS_VLC`: article/chunk parsing design only
  - `duyet_legal_instruct`: SFT filtering review only
- **Phase 3 remains NOT STARTED. Do not generate QA. Do not fine-tune. Do not build RAG/vector indexes.**

## Phase 2F - UTS_VLC Article/Chunk Parser Design and Validation

**Date:** 2026-06-10
**Verdict:** PASS WITH RISKS

- A deterministic secondary parser was added for the existing Phase 2D `UTS_VLC` normalized outputs only.
- The parser preserves parent provenance and fails closed if required provenance fields are missing.
- Measured Phase 2F output:
  - `300` input documents
  - `299` documents with article markers
  - `1` document without article markers
  - `20,393` derived article/chunk candidates
  - `0` empty candidates
  - `10` near-empty candidates
  - `490` duplicate article hashes
  - `87` suspicious-length candidates
  - `299` parse warnings, all `preamble_before_first_article`
  - `article_number_parse_success_rate = 1.0`
  - `parent_provenance_coverage = 1.0`
- All output candidates are explicitly marked:
  - `is_legal_ground_truth = false`
  - `approved_for_rag_index = false`
- Phase boundary remains unchanged:
  - Phase 3 is still blocked
  - no QA generation
  - no fine-tuning
  - no RAG/vector index construction
- Recommended next step: **Phase 2G filtering rules**


## Phase 2G - UTS Article Candidate Filtering Rules

**Date:** 2026-06-10
**Verdict:** PASS WITH RISKS

- Deterministic filtering and review labeling added for Phase 2F article/chunk candidates.
- Measured filter output:
  - `20,393` input candidates
  - `511` rejected
  - `3,249` needs review
  - `16,633` keep as clean review candidates
  - `339` duplicate hash groups
  - `490` duplicate candidates rejected
  - `21` near-empty candidates rejected
  - `299` parent document warnings carried as metadata only
  - provenance coverage preserved at `1.0`
  - `approved_for_rag_index_true_count = 0`
  - `is_legal_ground_truth_true_count = 0`
- Phase 3 remains blocked.
- Recommendation: use the Phase 2G outputs only through the Phase 2H manual-review pack; Phase 3 remains blocked.

## Phase 2H - Manual Review Pack / Sampling Audit

**Date:** 2026-06-10
**Verdict:** PASS WITH RISKS

- Deterministic Phase 2H review sampler added for existing Phase 2G outputs only.
- Measured review-pack output:
  - `20,393` total available candidates
  - `150` sampled rows
  - `duplicate_related=10`
  - `suspicious_length=10`
  - `keep_candidate_for_human_review=60`
  - `needs_review=50`
  - `rejected=20`
  - `128` distinct parent documents covered
  - `128` distinct `source_id` values covered
  - `approved_for_rag_index_true_count = 0`
  - `is_legal_ground_truth_true_count = 0`
- Generated review artifacts stay under ignored `artifacts/phase_2h_manual_review_pack/`.
- Review rubric created in `docs/MANUAL_REVIEW_RUBRIC.md`.
- Phase 3 remains blocked.
- Recommendation: proceed only to a future Phase 2I human-review results schema or adjudication workflow, not to Phase 3.

## Phase 2I - Human Review Results Schema + Adjudication Workflow

**Date:** 2026-06-10
**Verdict:** PASS

- Added a deterministic review-results validator for the Phase 2H
  `reviewer_decision_template.csv` workflow.
- Accepted decision labels are enforced:
  - `accept_for_later_corpus_candidate`
  - `reject_not_article`
  - `reject_duplicate`
  - `reject_too_short`
  - `reject_too_long`
  - `reject_missing_metadata`
  - `needs_legal_expert_review`
  - `needs_parser_fix`
  - `uncertain`
- Accepted confidence values are enforced: `high`, `medium`, `low`.
- Required review fields are enforced:
  - `reviewer_id`
  - `review_date`
  - `candidate_id`
  - `decision_label`
  - `confidence`
  - `notes`
  - `legal_ground_truth_approved`
  - `rag_index_approved`
- Safety guards remain fail-closed:
  - `legal_ground_truth_approved` must remain `false`
  - `rag_index_approved` must remain `false`
- Candidate-level adjudication statuses are now defined:
  - `consensus`
  - `parser_fix_required`
  - `legal_expert_review_required`
  - `uncertain_requires_adjudication`
  - `label_conflict_requires_adjudication`
- No QA generation.
- No fine-tuning.
- No RAG or vector indexing.
- No automatic legal-ground-truth promotion.
- **Phase 3 remains blocked. Stop after Phase 2I unless explicitly instructed to continue.**

## Phase 2J - Review Results Import + Human Label Quality Audit

**Date:** 2026-06-10
**Verdict:** PASS WITH RISKS

- Added a Phase 2J audit layer on top of the Phase 2I validator.
- Added a safe local bulk-fill helper for the Phase 2H reviewer template:
  `scripts/fill_review_decisions.py`.
- The audit tool computes:
  - `total_rows`
  - `valid_rows`
  - `invalid_rows`
  - `decision_counts`
  - `confidence_counts`
  - `low_confidence_rate`
  - `missing_candidate_id_count`
  - `duplicate_candidate_review_count`
  - `conflict_count`
  - `accepted_for_later_corpus_candidate_count`
  - `rejected_count`
  - `unresolved_count`
  - `legal_ground_truth_approved_true_count`
  - `rag_index_approved_true_count`
- Output files are restricted to `artifacts/` only.
- Bulk-fill helper safety rules:
  - explicit human confirmation flags are required before writing any completed CSV
  - the default bulk label `accept_for_later_corpus_candidate` means only later corpus-candidate review
  - `legal_ground_truth_approved` is forced to `false`
  - `rag_index_approved` is forced to `false`
  - existing output is protected unless `--overwrite` is passed
- Current local Phase 2J support run:
  - `artifacts/phase_2h_manual_review_pack/reviewer_decisions_completed.csv` was generated locally under ignored `artifacts/`
  - `rows_written = 150`
  - `decision_label = accept_for_later_corpus_candidate`
  - `confidence = medium`
  - `legal_ground_truth_approved_true_count = 0`
  - `rag_index_approved_true_count = 0`
  - Phase 2I validation result: `PASS`
  - Phase 2J audit CLI result: `PASS`
- Final Phase 2J interpretation:
  - overall phase verdict remains `PASS WITH RISKS`
  - the completed review covers the Phase 2H sample only
  - the review is bulk-filled after explicit human confirmation flags
  - the review is not recorded as legal-expert adjudication
  - `accept_for_later_corpus_candidate` means later corpus-candidate review only
  - no legal-ground-truth approval exists
  - no RAG approval exists
- Safety boundary remains unchanged:
  - no fake human labels
  - no QA generation
  - no fine-tuning
  - no RAG or vector indexing
  - no legal-ground-truth approval
  - no RAG approval
- **Next allowed phase: Phase 2K - Reviewed Corpus Candidate Manifest.**
- **Phase 2L and Phase 2M remain required before any Phase 3 scaffold or training decision.**
- **Phase 2K is not started.**
- **Phase 3 remains blocked. Stop here unless explicitly instructed to continue later.**

## Phase 2K - Reviewed Corpus Candidate Manifest

**Date:** 2026-06-10
**Verdict:** PASS WITH RISKS

- Added deterministic corpus-candidate manifest tooling for the Phase 2J
  accepted sample subset only.
- Current local Phase 2K manifest run:
  - `accepted_candidate_ids_input_count = 150`
  - `manifest_records_written = 150`
  - `missing_review_metadata_count = 0`
  - `missing_filter_metadata_count = 0`
  - `rejected_from_manifest_count = 0`
  - `unresolved_from_manifest_count = 0`
  - `unique_parent_documents = 128`
  - `unique_source_ids = 128`
  - `decision_counts = {"accept_for_later_corpus_candidate": 150}`
  - `confidence_counts = {"medium": 150}`
  - `legal_ground_truth_true_count = 0`
  - `rag_index_approved_true_count = 0`
  - `qa_generation_approved_true_count = 0`
  - `fine_tuning_approved_true_count = 0`
  - `phase3_ready_true_count = 0`
- Every manifest record remains constrained to:
  - `review_scope = phase_2h_sample_only`
  - `approval_scope = later_corpus_candidate_review_only`
  - `is_legal_ground_truth = false`
  - `approved_for_rag_index = false`
  - `approved_for_qa_generation = false`
  - `approved_for_fine_tuning = false`
  - `phase3_ready = false`
- Interpretation:
  - the manifest is structurally valid for later review planning only;
  - the reviewed set still covers the Phase 2H sample only;
  - no corpus-wide approval exists;
  - no QA, fine-tuning, or RAG approval exists.
- **Next allowed phase: Phase 2L - SFT/RAG Readiness Gate.**
- **Phase 3 remains blocked.**

## Phase 2L - SFT/RAG Readiness Gate

**Date:** 2026-06-10
**Verdict:** PASS WITH RISKS

- Added a deterministic readiness gate for the Phase 2K manifest and the
  Phase 2J/2K limitation docs.
- Current local Phase 2L gate output:
  - `corpus_candidate_manifest_ready = true`
  - `qa_generation_ready = false`
  - `fine_tuning_ready = false`
  - `rag_indexing_ready = false`
  - `phase3_scaffold_ready = true`
  - `readiness_verdict = PASS WITH RISKS`
- Supporting checks:
  - `accepted_candidate_count = 150`
  - `unique_parent_documents = 128`
  - `provenance_coverage = 1.0`
  - `attribution_docs_present = true`
  - `data_use_policy_present = true`
  - `license_fields_present = true`
  - `legal_ground_truth_true_count = 0`
  - `rag_index_approved_true_count = 0`
  - `qa_generation_approved_true_count = 0`
  - `fine_tuning_approved_true_count = 0`
  - `phase3_ready_true_count = 0`
  - `review_coverage_limitation_documented = true`
  - `bulk_review_limitation_documented = true`
- Interpretation:
  - scaffold planning is safe;
  - actual QA generation remains blocked;
  - actual fine-tuning remains blocked;
  - actual RAG indexing remains blocked.
- **Next allowed phase: Phase 2M - Full Phase 3 Readiness Audit.**
- **Phase 3 execution remains blocked.**

## Phase 2M - Full Phase 3 Readiness Audit

**Date:** 2026-06-10
**Verdict:** PHASE 3 READY FOR SCAFFOLD ONLY

- Final audit confirms:
  - Phase 2K manifest exists and is valid.
  - Phase 2L scaffold-planning gate passed with risks.
  - QA generation remains blocked.
  - Fine-tuning remains blocked.
  - RAG indexing remains blocked.
  - sample-scope limitations remain explicit.
  - artifact hygiene remains intact.
- Current final boundary:
  - allowed next step is **Phase 3A Kaggle/QLoRA scaffold only**
  - notebook/config/docs planning is allowed
  - actual training is not allowed
  - actual QA generation is not allowed
  - actual vector/RAG indexing is not allowed
  - dataset publication is not allowed
- **Phase 3 is not ready for execution.**

## Phase 3A - Kaggle/QLoRA Scaffold Only

**Date:** 2026-06-10
**Verdict:** PASS - VALIDATOR REQUIRED AND PASSED

- Added scaffold-only config, notebook, validator, tests, and governance documentation.
- `python scripts/validate_phase3a_scaffold.py` is now the completion gate for this phase.
- The validator blocks active training/model/hub patterns in executable notebook cells.
- The validator requires all scaffold safety flags to remain fail-closed.
- The validator requires docs to preserve the scaffold-only boundary.
- QA generation remains blocked.
- Fine-tuning remains blocked.
- RAG/vector indexing remains blocked.
- Dataset publishing remains blocked.
- Real legal corpus use remains blocked.
- Track A synthetic demo remains separate from Track B governance.

## Track A0/A1 - Synthetic Demo Foundation

**Date:** 2026-06-10
**Verdict:** PASS - SYNTHETIC DATA ONLY

- Added Track A synthetic-demo config, schema, generator, validator, sample file, and tests.
- Synthetic demo data is explicitly labeled `synthetic-demo`.
- Synthetic demo data is not legal advice and not official legal text.
- Track A does not use `UTS_VLC` candidates or `corpus_candidate_manifest`.
- Track A does not change Track B safety gates.
- Future Track A2 may do a Kaggle fine-tune demo using synthetic data only.
- Real legal corpus QA, SFT, and RAG remain blocked.

## Track A1.5 - Synthetic Dataset Expansion + Quality Audit

**Date:** 2026-06-10
**Verdict:** PASS - ARTIFACTS ONLY

- Added local audit and deterministic split tooling for the synthetic-demo dataset.
- Generated the 2,500-row synthetic artifact locally under `artifacts/track_a_synthetic_demo/`.
- Full synthetic artifact, audit report, and split files remain untracked.
- Track A synthetic dataset remains synthetic-demo only and not legal advice.
- Track A does not unblock Track B real QA, SFT, or RAG.
- Next allowed Track A step is Track A2 Kaggle synthetic fine-tune demo using local synthetic split artifacts only.

## Track A2/A2.2 - Kaggle Unsloth 7B Runtime Patch

**Date:** 2026-06-10
**Verdict:** PASS - UNSLOTH 7B RUNTIME PATCH IMPLEMENTED

- Added Kaggle fine-tune demo notebook using Unsloth 7B QLoRA runtime, dataset packaging script, validator, tests, and governance documentation.
- `configs/track_a_kaggle_finetune_demo.yaml` updated to add runtime block with `target_platform: "kaggle"`, `local_training_allowed: false`, and output paths.
- `notebooks/track_a_kaggle_synthetic_finetune_demo.ipynb` overwritten to implement Unsloth `FastLanguageModel.from_pretrained` (loading `unsloth/Qwen2.5-7B-Instruct` in 4-bit with gradient checkpointing) and `SFTTrainer` path.
- Primary portfolio model target remains `unsloth/Qwen2.5-7B-Instruct` for Kaggle QLoRA.
- `Qwen/Qwen2.5-3B-Instruct` documented as the local/dev baseline because the user can already run 3B locally.
- `Qwen/Qwen2.5-0.5B-Instruct` retained only for smoke testing.
- `scripts/prepare_kaggle_synthetic_dataset.py` added — packages splits for Kaggle upload.
- `scripts/validate_track_a_kaggle_demo.py` added — validates config + notebook safety.
- `tests/test_track_a_kaggle_demo.py` added — extended coverage for model-profile alignment and safety checks.
- `docs/TRACK_A_KAGGLE_SYNTHETIC_FINETUNE.md` added — full runbook.
- `docs/TRACK_A_BENCHMARK_PLAN.md` added — benchmark methodology and portfolio checklist.
- Safety confirmation:
  - `use_real_legal_corpus=false` (confirmed)
  - `use_uts_vlc_candidates=false` (confirmed)
  - `use_corpus_candidate_manifest=false` (confirmed)
  - `mark_as_legal_ground_truth=false` (confirmed)
  - `approved_for_rag_index=false` (confirmed)
  - `allow_local_training=false` (confirmed)
  - `allow_kaggle_training=true` (Kaggle-only)
  - `allow_hub_push_by_default=false` (confirmed)
- Full 2,500-row synthetic dataset remains an artifact, not committed.
- Model/adapters/checkpoints are not committed.
- Track A2 does not unblock Track B real legal QA/SFT/RAG.
- Any public demo must preserve the synthetic-only disclaimer.
- Next allowed Track A step: Track A3 public portfolio packaging.
