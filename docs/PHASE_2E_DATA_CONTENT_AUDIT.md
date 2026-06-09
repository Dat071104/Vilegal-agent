# Phase 2E Data Content Quality Audit Report

**Date:** 2026-06-10
**Executive verdict:** PASS WITH RISKS

## Scope

This audit reviewed only the existing Phase 2D local artifacts:

- `artifacts/phase_2d_controlled_ingestion/uts_vlc/`
- `artifacts/phase_2d_controlled_ingestion/duyet_legal_instruct/`

No QA data was generated. No fine-tuning was started. No RAG or vector index was built. No new ingestion or scraping was performed.

## Measured Inputs

- `uts_vlc`: 300 normalized records
- `duyet_legal_instruct`: 1000 normalized records
- Generated read-only audit report: `artifacts/phase_2e_content_audit_report.json`
- Near-empty threshold used in this audit: `<= 50` stripped characters

## Content-Quality Findings

### UTS_VLC

- Document types in the normalized output: `other=300`
- Missing title: `0/300`
- Missing document number: `300/300`
- Missing document type: `0/300`
- Average text length: `82,426.64` chars
- Median text length: `56,202.5` chars
- Empty text: `0/300`
- Near-empty text: `0/300`
- Citation metadata availability:
  - `source_id`: `300/300`
  - `source_url`: `300/300`
  - `title`: `300/300`
  - `document_number`: `0/300`
  - `article_number`: `0/300`
  - `clause_number`: `0/300`
- Article marker scan:
  - Records with article markers: `299/300`
  - Records with multiple article markers: `299/300`

Conclusion:
The current UTS normalized rows are long document-level text blobs, not article rows. Article-level parsing is possible from the current text field, but only as a secondary parsing step because the normalized metadata does not preserve `document_number`, `article_number`, or `clause_number`.

Coverage limitation confirmed:
UTS_VLC remains a limited legal corpus candidate for Constitution, Codes, and Laws only. It does not represent the full Vietnamese legal universe and should not be presented as covering decrees, circulars, decisions, or other sub-law instruments.

### duyet_legal_instruct

- Document types in the normalized output: `other=1000`
- Missing title: `1000/1000`
- Missing document number: `1000/1000`
- Missing document type: `0/1000`
- Average normalized text length: `3,507.04` chars
- Median normalized text length: `3,614.5` chars
- Empty text: `0/1000`
- Near-empty text: `0/1000`
- Citation metadata availability:
  - `source_id`: `1000/1000`
  - `source_url`: `1000/1000`
  - `document_number`: `0/1000`
  - `article_number`: `0/1000`
  - `clause_number`: `0/1000`
  - `title`: `0/1000`
- Normalized text matches user turn: `1000/1000`
- Assistant answer retained in `raw_metadata`: `1000/1000`
- Assistant answers with citation-like signals: `935/1000` (`93.5%`)
- `qa_type` mix:
  - `explain_simple=165`
  - `summarize=160`
  - `qa_practical=152`
  - `scope=130`
  - `classify=122`
  - `key_provisions=118`
  - `legal_basis=89`
  - `amounts=32`
  - `full_text=32`

Conclusion:
The normalized `text` field is correctly limited to the user query, and the assistant answer remains stored only inside `raw_metadata`. That is the correct source-role separation for this phase.

However, this dataset is still generated supervision, not ground-truth legal content. Citation-like wording in assistant answers is common, but citation presence does not establish legal correctness.

### Hallucination-Risk Categories

The current `duyet_legal_instruct` sample contains several task types that increase hallucination risk even if the output looks legally formatted:

- `explain_simple`: may omit exceptions or conditions
- `summarize`: may compress away scope limits
- `qa_practical`: may add unsupported application advice
- `full_text`: may truncate or invent omitted sections

These are risk categories only. This audit does not make any claim about legal correctness of the assistant answers.

## Cross-Source Checks

- Duplicate `record_id` across sources: `0`
- Duplicate `source_id` across sources: `0`
- Exact duplicate normalized text across sources: `0`
- Provenance completeness:
  - `uts_vlc`: all `300/300` records have `source_dataset`, `source_url`, `source_id`, `license`, `retrieved_at`
  - `duyet_legal_instruct`: all `1000/1000` records have `source_dataset`, `source_url`, `source_id`, `license`, `retrieved_at`
- License attribution completeness:
  - `uts_vlc` manifest has license and attribution note
  - `duyet_legal_instruct` manifest has license, attribution note, and `attribution_required=true`
- Source roles are correctly separated in the current normalized outputs:
  - `UTS_VLC = legal corpus candidate`
  - `duyet_legal_instruct = instruction candidate, not ground-truth corpus`

## Source Readiness Matrix

| Area | Status | Basis |
|---|---|---|
| RAG corpus readiness | PASS WITH RISKS | `UTS_VLC` has complete provenance and long-form legal text, but current rows are document-level and coverage is limited to laws/codes/constitution. |
| SFT dataset readiness | BLOCKED | `duyet_legal_instruct` answer side is generated supervision and not verified legal ground truth. |
| Evaluation dataset readiness | BLOCKED | Neither source is a vetted answer key; UTS lacks article/chunk labels in current rows and Duyet answers carry hallucination risk. |
| Public release readiness | BLOCKED | Provenance is complete, but public redistribution/relicensing review remains open and CC-BY attribution duties must still be enforced. |

## Downstream Go/No-Go

- UTS_VLC article/chunking phase: **PASS WITH RISKS**
  - Safe to proceed only to article/chunk parsing work from current text fields.
  - Do not treat the current normalized rows as article-level records.

- `duyet_legal_instruct` SFT filtering phase: **PASS WITH RISKS**
  - Safe to proceed only to filtering/review work.
  - Not approved for direct fine-tuning.

## Remaining Blockers

1. UTS normalized content lacks preserved `document_number`, `article_number`, and `clause_number`, so article/chunk derivation still requires a parser stage.
2. `duyet_legal_instruct` remains generated supervision and cannot be treated as legal ground truth for SFT or evaluation.
3. Public-release and relicensing review remain unresolved for downstream publication.
4. Phase 3 work remains out of scope. Do not generate QA. Do not fine-tune. Do not build RAG/vector indexes from this audit turn.

## Files Changed

- `docs/PHASE_2E_DATA_CONTENT_AUDIT.md`
- `docs/PHASE_2_PRE_AUDIT.md`
- `_ops/IMPLEMENTATION_LOG.md`
- `_ops/PHASE_STATUS.md`
- `_ops/RISK_REGISTER.md`
- `scripts/audit_ingested_content.py`
- `tests/test_audit_ingested_content.py`

## Validation Results

1. `python -m compileall src scripts -q` -> PASS
2. `python -m pytest tests -v` -> PASS (`86 passed`)
3. `python scripts/audit_ingested_content.py --input-dir artifacts/phase_2d_controlled_ingestion --report-out artifacts/phase_2e_content_audit_report.json` -> PASS
4. `git status --short` -> PASS

## Git Tracking Confirmation

- Confirmed: no files under `artifacts/` were staged
- Confirmed: generated audit output remains under ignored `artifacts/`

## Exact Safe Git Add Command

```bash
git add docs/PHASE_2E_DATA_CONTENT_AUDIT.md docs/PHASE_2_PRE_AUDIT.md _ops/IMPLEMENTATION_LOG.md _ops/PHASE_STATUS.md _ops/RISK_REGISTER.md scripts/audit_ingested_content.py tests/test_audit_ingested_content.py
```

## Commit Message Suggestion

```text
chore: complete phase 2e data content quality audit
```

## Recommendation for Next Phase

Remain in Phase 2 follow-up work only:

1. For `UTS_VLC`, proceed only to article/chunk parsing design and validation.
2. For `duyet_legal_instruct`, proceed only to filtering criteria and human-review rules for potential future SFT use.
3. Do not start Phase 3. Do not generate QA. Do not fine-tune. Do not build RAG.
