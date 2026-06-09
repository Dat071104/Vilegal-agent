# Phase 1 Big Audit

**Date:** 2026-06-09  
**Audit scope:** Phase 1 re-audit plus Phase 2 pre-audit only  
**Executive verdict:** PASS WITH RISKS

## Blocking findings found and fixed

1. `CONFIRMED`: `duyet/vietnamese-legal-instruct` was previously documented as Apache-2.0. The current Hugging Face card lists `cc-by-4.0`, and the repo docs were corrected.
2. `CONFIRMED`: `undertheseanlp/UTS_VLC` was previously documented as license-unclear. The current Hugging Face card lists `mit`, and the repo docs were corrected.
3. `CONFIRMED`: `th1nhng0/vietnamese-legal-documents` was previously documented as license-unclear. The current Hugging Face card lists `cc-by-4.0`, and the repo docs were corrected.
4. `CONFIRMED`: generated instruction and QA datasets are now explicitly treated as generated supervision rather than legal ground truth.
5. `CONFIRMED`: the local sample inspector now accepts the required validation command and validates the sample against the schema.
6. `CONFIRMED`: the local contracts now capture source dataset, source id or URL, license, retrieval timestamp, effective status, document type, document number, article number, clause number, and text where applicable.

## Current source verdicts

| Source | Current repo position |
|---|---|
| `undertheseanlp/UTS_VLC` | `CONFIRMED`: license field currently `mit`; best limited-quality corpus candidate; `NEEDS MANUAL REVIEW`: provenance and relicensing basis. |
| `th1nhng0/vietnamese-legal-documents` | `CONFIRMED`: license field currently `cc-by-4.0`; broad document coverage including sub-law instruments; `NEEDS MANUAL REVIEW`: provenance and relicensing basis. |
| `duyet/vietnamese-legal-instruct` | `CONFIRMED`: license field currently `cc-by-4.0`; generated from `th1nhng0/vietnamese-legal-documents`; not ground truth; `NEEDS MANUAL REVIEW`: provenance and relicensing basis. |
| `thangvip/vietnamese-legal-qa` | `CONFIRMED`: generated QA dataset; `NEEDS MANUAL REVIEW`: exact downstream license scope. |
| `vbpl.vn` | `CONFIRMED`: official portal; `NEEDS MANUAL REVIEW`: repo-local evidence for API registration and automation constraints is still missing. |

## Schema and sample audit

- `CONFIRMED`: `src/vilegal/data_contracts.py` now carries provenance fields across document, article, clause, and source metadata.
- `CONFIRMED`: `tests/test_data_contracts.py` covers provenance, attribution, and synthetic-example handling.
- `CONFIRMED`: `tests/fixtures/synthetic_legal_articles.jsonl` contains three synthetic example article records only.
- `CONFIRMED`: `tests/fixtures/synthetic_legal_articles.jsonl` is tracked by git (moved from the gitignored `data/processed/` path).
- `CONFIRMED`: `git ls-files data` shows only `data/README.md`, `data/raw/.gitkeep`, and `data/processed/.gitkeep` as tracked data-path files.

## Validation results

| Command | Result |
|---|---|
| `python -m compileall src scripts -q` | PASS |
| `python -m pytest tests -v` | PASS - 24 tests passed |
| `python scripts/inspect_data_source_sample.py tests/fixtures/synthetic_legal_articles.jsonl` | PASS - 3 validated synthetic records |
| `git check-ignore -v data/processed/sample_legal_articles.jsonl` | PASS - ignored by `data/processed/*` in `.gitignore` |

## Remaining risks

1. `NEEDS MANUAL REVIEW`: provenance and relicensing for non-synthetic candidate datasets remain unresolved.
2. `NEEDS MANUAL REVIEW`: repo-local official evidence for VBPL API registration or restricted access is still absent.
3. `CONFIRMED`: CC-BY-4.0 sources require attribution handling in downstream artifacts.
4. `CONFIRMED`: `undertheseanlp/UTS_VLC` does not cover decrees, circulars, decisions, or other sub-law instruments.

## Git hygiene

- `CONFIRMED`: unrelated untracked items currently present are `UI_craft.md` and `ai-agent-workspace-pack/`.
- `CONFIRMED`: related but currently untracked implementation files are `conftest.py`, `src/vilegal/data_contracts.py`, `tests/test_data_contracts.py`, `scripts/inspect_data_source_sample.py`, `docs/PHASE_1_BIG_AUDIT.md`, and `docs/PHASE_2_PRE_AUDIT.md`.
- `CONFIRMED`: `_ops/PHASE_01_REPORT.md` is an untracked stale report with outdated source claims and should not be staged as part of this audit fix.

## Phase 2 recommendation

- Bulk download: **BLOCKED FOR BULK DOWNLOAD**
- Sample-only ingestion: **ALLOWED FOR SAMPLE-ONLY INGESTION**
- Implementation start: **NO-GO**

## Suggested commit inputs

Safe explicit git add command:

```powershell
git add conftest.py src/vilegal/data_contracts.py tests/test_data_contracts.py tests/fixtures/synthetic_legal_articles.jsonl scripts/inspect_data_source_sample.py docs/DATA_SOURCE_AUDIT.md docs/DECISIONS.md docs/PHASE_1_BIG_AUDIT.md docs/PHASE_2_PRE_AUDIT.md _ops/RISK_REGISTER.md _ops/PHASE_STATUS.md _ops/IMPLEMENTATION_LOG.md
```

Commit message suggestion:

```text
fix(phase-1): re-audit legal data licensing and block phase-2 bulk ingestion
```
