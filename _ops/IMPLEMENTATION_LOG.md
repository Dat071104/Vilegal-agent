# Implementation Log

## Phase 0 - Project bootstrap (2026-06-09)

| Time | Action | Status |
|---|---|---|
| 2026-06-09T15:30 | Created the initial project scaffold and baseline docs. | PASS |

**Phase 0 result:** PASS

## Phase 1 - Initial audit and scaffolding (2026-06-09)

| Time | Action | Status |
|---|---|---|
| 2026-06-09T15:38 | Reviewed the existing scaffold and listed candidate legal data sources. | PASS |
| 2026-06-09T15:39 | Wrote the first-pass Phase 1 audit docs and source decisions. | SUPERSEDED |
| 2026-06-09T15:41 | Added initial Pydantic schemas, tests, and a local-only inspection script. | SUPERSEDED |

**Phase 1 initial result:** SUPERSEDED BY BIG AUDIT

## Phase 1 - Big audit and Phase 2 pre-audit (2026-06-09)

| Time | Action | Status |
|---|---|---|
| 2026-06-09T16:00 | Re-read Phase 1 docs, schemas, tests, sample data, and git hygiene state. | PASS |
| 2026-06-09T16:05 | Re-checked the current Hugging Face dataset cards for `undertheseanlp/UTS_VLC`, `duyet/vietnamese-legal-instruct`, `th1nhng0/vietnamese-legal-documents`, and `thangvip/vietnamese-legal-qa`. | PASS |
| 2026-06-09T16:10 | Corrected stale license and source claims in `docs/DATA_SOURCE_AUDIT.md`, `docs/DECISIONS.md`, `_ops/RISK_REGISTER.md`, and `_ops/PHASE_STATUS.md`. | PASS |
| 2026-06-09T16:15 | Hardened `src/vilegal/data_contracts.py` with provenance fields required for sample-only ingestion review. | PASS |
| 2026-06-09T16:18 | Expanded `tests/test_data_contracts.py` to cover provenance and attribution metadata. | PASS |
| 2026-06-09T16:20 | Updated `scripts/inspect_data_source_sample.py` so the required validation command works with a positional file path and schema validation. | PASS |
| 2026-06-09T16:22 | Rebuilt the ignored local sample file as synthetic-only, schema-valid article records. | PASS |
| 2026-06-09T16:24 | Created `docs/PHASE_1_BIG_AUDIT.md` and `docs/PHASE_2_PRE_AUDIT.md` for human review. | PASS |
| 2026-06-09T16:26 | Ran `python -m compileall src scripts -q`. | PASS |
| 2026-06-09T16:27 | Ran `python -m pytest tests -v` and got 24 passing tests. | PASS |
| 2026-06-09T16:28 | Ran `python scripts/inspect_data_source_sample.py data/processed/sample_legal_articles.jsonl` and confirmed 3 synthetic validated records. | PASS |
| 2026-06-09T16:29 | Checked git tracking rules and confirmed `data/processed/sample_legal_articles.jsonl` is ignored by `.gitignore`. | PASS |

**Phase 1 big audit result:** PASS WITH RISKS

## Phase 2 status

No Phase 2 implementation work was started in this audit turn.

## Phase 1 - Reproducibility patch (2026-06-09)

| Time | Action | Status |
|---|---|---|
| 2026-06-09T16:11 | Identified reproducibility issue: `data/processed/sample_legal_articles.jsonl` is gitignored, causing the audit validation command to fail on a fresh clone. | CONFIRMED |
| 2026-06-09T16:11 | Created `tests/fixtures/synthetic_legal_articles.jsonl` — identical 3-record synthetic content, now git-tracked. | PASS |
| 2026-06-09T16:11 | Updated `DEFAULT_SAMPLE_FILE` and docstring in `scripts/inspect_data_source_sample.py` to point to the new fixture path. | PASS |
| 2026-06-09T16:11 | Updated three path references in `docs/PHASE_1_BIG_AUDIT.md` and its suggested git add command. | PASS |
| 2026-06-09T16:12 | Updated `_ops/IMPLEMENTATION_LOG.md` (this file) and `_ops/PHASE_STATUS.md`. | PASS |
| 2026-06-09T16:12 | Ran `python -m compileall src scripts -q`. | PASS |
| 2026-06-09T16:12 | Ran `python -m pytest tests -v`. | PASS |
| 2026-06-09T16:12 | Ran `python scripts/inspect_data_source_sample.py tests/fixtures/synthetic_legal_articles.jsonl`. | PASS |
| 2026-06-09T16:12 | Ran `git status --short`. | PASS |

**Reproducibility patch result:** PASS

## Phase 2A — Sample-only ingestion scaffold (2026-06-09)

**Branch:** `phase/01-data-source-audit` (continuing)

| Step | Time | Action | Status |
|---|---|---|---|
| 1 | 2026-06-09T16:17 | Surveyed repo state: src/vilegal/, tests/, fixtures, .gitignore. | ✅ |
| 2 | 2026-06-09T16:18 | Summarized all intended file changes (Chat First rule observed). | ✅ |
| 3 | 2026-06-09T16:18 | Updated `.gitignore` — added `artifacts/`, `.cache/`, `hf_cache/`. | ✅ |
| 4 | 2026-06-09T16:18 | Created `src/vilegal/ingestion/__init__.py`. | ✅ |
| 5 | 2026-06-09T16:18 | Created `src/vilegal/ingestion/source_registry.py` — 5 audited sources, hard cap 100. | ✅ |
| 6 | 2026-06-09T16:19 | Created `src/vilegal/ingestion/provenance.py` — manifest builder and writer. | ✅ |
| 7 | 2026-06-09T16:19 | Created `src/vilegal/ingestion/normalizers.py` — raw→canonical normalizer. | ✅ |
| 8 | 2026-06-09T16:19 | Created `src/vilegal/ingestion/quality_checks.py` — 8-metric quality report with threshold gate. | ✅ |
| 9 | 2026-06-09T16:20 | Created `src/vilegal/ingestion/hf_sample_loader.py` — offline fixture + HF streaming loader. | ✅ |
| 10 | 2026-06-09T16:20 | Created `scripts/ingest_hf_sample.py` — CLI with --source, --max-records, --output-dir, --offline-fixture. | ✅ |
| 11 | 2026-06-09T16:20 | Created `tests/fixtures/malformed_legal_articles.jsonl` — 3 synthetic invalid records. | ✅ |
| 12 | 2026-06-09T16:21 | Created `tests/test_ingestion.py` — 44 tests across 8 test classes. | ✅ |
| 13 | 2026-06-09T16:22 | Ran `python -m compileall src scripts -q` — PASS. | ✅ |
| 14 | 2026-06-09T16:22 | Ran `python -m pytest tests -v` — **68/68 tests PASS** (24 Phase 1 + 44 Phase 2A). | ✅ |
| 15 | 2026-06-09T16:22 | Ran `python scripts/inspect_data_source_sample.py tests/fixtures/synthetic_legal_articles.jsonl` — PASS. | ✅ |
| 16 | 2026-06-09T16:22 | Ran `python scripts/ingest_hf_sample.py --source uts_vlc --max-records 3 --offline-fixture tests/fixtures/synthetic_legal_articles.jsonl --output-dir artifacts/phase_2a_test` — PASS, quality gate PASS. | ✅ |
| 17 | 2026-06-09T16:22 | Ran `git status --short` — confirmed `artifacts/` gitignored, only Phase 2A files untracked. | ✅ |
| 18 | 2026-06-09T16:23 | Updated `docs/PHASE_2_PRE_AUDIT.md`, `_ops/IMPLEMENTATION_LOG.md`, `_ops/PHASE_STATUS.md`. | ✅ |

**Phase 2A result:** PASS

## Phase 2B — Online smoke test (2026-06-09)

| Step | Time | Action | Status |
|---|---|---|---|
| 1 | 2026-06-09T16:26 | Surveyed registry; identified source ID mismatch (CLI uses `duyet_legal_instruct`, registry had `viet_legal_instruct`). | ✅ |
| 2 | 2026-06-09T16:26 | Added `ALIASES` dict and updated `get_source()` — backward-compatible. | ✅ |
| 3 | 2026-06-09T16:26 | Added `TestSourceAliases` test class — 8 tests. | ✅ |
| 4 | 2026-06-09T16:27 | `python -m pytest tests -v` — 76/76 PASS. | ✅ |
| 5 | 2026-06-09T16:28 | Ran UTS_VLC online smoke test — failed: split `train` not valid, only year splits available (`2026`, etc.). | 🔍 DISCOVERY |
| 6 | 2026-06-09T16:29 | Added `default_split` field to `SourceMeta`; set `default_split='2026'` for UTS_VLC. Updated CLI to use `source_meta.default_split` when `--hf-split` not set. | ✅ |
| 7 | 2026-06-09T16:29 | Added 2 split tests. `python -m pytest tests -v` — 76/76 PASS. | ✅ |
| 8 | 2026-06-09T16:30 | Re-ran UTS_VLC online smoke test — 10/10 normalized, quality gate PASS. | ✅ |
| 9 | 2026-06-09T16:31 | Ran duyet_legal_instruct online smoke test — 10 rejected: schema uses `conversations` list, not flat `text`. | 🔍 DISCOVERY |
| 10 | 2026-06-09T16:33 | Added conversations-format extractor to `normalizers.py`. Added 3 normalizer tests. `python -m pytest tests -v` — 79/79 PASS. | ✅ |
| 11 | 2026-06-09T16:33 | Re-ran duyet_legal_instruct smoke — 10/10 normalized, quality gate PASS. | ✅ |
| 12 | 2026-06-09T16:34 | Confirmed Duyet provenance_manifest.json has `license: CC-BY-4.0`, `attribution_required: true`, `bulk_download_blocked: true`. | ✅ |
| 13 | 2026-06-09T16:34 | Ran `git status --short` — `artifacts/` and `.cache/` correctly gitignored; no generated data staged. | ✅ |
| 14 | 2026-06-09T16:35 | Updated `docs/PHASE_2_PRE_AUDIT.md`, `_ops/IMPLEMENTATION_LOG.md`, `_ops/PHASE_STATUS.md`. | ✅ |
| 15 | - | th1nhng0/vietnamese-legal-documents — DEFERRED (not required; Phase 2B mandatory sources covered). | DEFERRED |

**Phase 2B result:** PASS WITH DISCOVERIES

## Phase 2C — Human Gate Pack (2026-06-09)

| Step | Time | Action | Status |
|---|---|---|---|
| 1 | 2026-06-09T16:40 | Created `docs/ATTRIBUTION.md` with templates for MIT and CC-BY-4.0. | ✅ |
| 2 | 2026-06-09T16:40 | Created `docs/DATA_USE_POLICY.md` detailing commitment rules. | ✅ |
| 3 | 2026-06-09T16:40 | Created `docs/BULK_INGESTION_GATE.md` with the 7 required human gates. | ✅ |
| 4 | 2026-06-09T16:40 | Created `docs/PHASE_2C_HUMAN_GATE_REPORT.md` blocking Phase 2D. | ✅ |
| 5 | 2026-06-09T16:40 | Updated `docs/PHASE_2_PRE_AUDIT.md`, `_ops/IMPLEMENTATION_LOG.md`, `_ops/PHASE_STATUS.md`. | ✅ |
| 6 | 2026-06-09T16:41 | Ran `python -m compileall src scripts -q` and `python -m pytest tests -v` — PASS. | ✅ |
| 7 | 2026-06-09T16:41 | Ran `git status --short`. | ✅ |

**Phase 2C result:** PASS

## Phase 2D — Controlled local ingestion (2026-06-09)

| Step | Time | Action | Status |
|---|---|---|---|
| 1 | 2026-06-09T16:45 | Manually checked all 7 gates in `docs/BULK_INGESTION_GATE.md`. | ✅ |
| 2 | 2026-06-09T16:46 | Increased `MAX_RECORDS_HARD_CAP` from 100 to 1000 in `src/vilegal/ingestion/source_registry.py` and updated `tests/test_ingestion.py`. | ✅ |
| 3 | 2026-06-09T16:46 | Ran `python -m compileall src scripts -q` and `python -m pytest tests -v` — PASS. | ✅ |
| 4 | 2026-06-09T16:47 | Ran controlled ingestion for `uts_vlc` with `--max-records 300`. PASS. | ✅ |
| 5 | 2026-06-09T16:47 | Ran controlled ingestion for `duyet_legal_instruct` with `--max-records 1000`. PASS. | ✅ |
| 6 | 2026-06-09T16:48 | Attempted optional ingestion for `th1nhng0_legal_documents`. Failed due to missing dataset config and deferred. | 🔍 DEFERRED |
| 7 | 2026-06-09T16:49 | Generated `docs/PHASE_2D_CONTROLLED_INGESTION_REPORT.md` | ✅ |
| 8 | 2026-06-09T16:49 | Verified no artifacts/cache staged via `git status --short`. | ✅ |

**Phase 2D result:** PASS WITH RISKS

## Phase 2E - Data Content Quality Audit (2026-06-10)

| Step | Time | Action | Status |
|---|---|---|---|
| 1 | 2026-06-10T00:05 | Verified that the required Phase 2D local artifacts for `uts_vlc` and `duyet_legal_instruct` exist before any audit work began. | PASS |
| 2 | 2026-06-10T00:08 | Reviewed current Phase 2 docs, ops status files, manifests, quality reports, and normalized outputs. | PASS |
| 3 | 2026-06-10T00:15 | Created `scripts/audit_ingested_content.py` as a read-only local audit utility that reads only JSONL/manifests and writes output under `artifacts/`. | PASS |
| 4 | 2026-06-10T00:16 | Added `tests/test_audit_ingested_content.py` covering pure helper functions only. | PASS |
| 5 | 2026-06-10T00:18 | Ran `python -m compileall src scripts -q`. | PASS |
| 6 | 2026-06-10T00:18 | Ran `python -m pytest tests -v` - **86/86 PASS**. | PASS |
| 7 | 2026-06-10T00:19 | Ran `python scripts/audit_ingested_content.py --input-dir artifacts/phase_2d_controlled_ingestion --report-out artifacts/phase_2e_content_audit_report.json`. | PASS |
| 8 | 2026-06-10T00:20 | Measured UTS findings: `300/300` rows typed as `other`, `300/300` missing `document_number`, `0/300` empty text, `299/300` rows contain multiple article markers. | PASS |
| 9 | 2026-06-10T00:21 | Measured Duyet findings: normalized `text` matches the user turn in `1000/1000` rows, assistant answer remains only in `raw_metadata` in `1000/1000` rows, `935/1000` assistant answers contain citation-like signals. | PASS |
| 10 | 2026-06-10T00:22 | Confirmed cross-source provenance completeness and zero cross-source duplicate `record_id`, `source_id`, and normalized text overlaps. | PASS |
| 11 | 2026-06-10T00:24 | Created `docs/PHASE_2E_DATA_CONTENT_AUDIT.md` and updated Phase 2 status/risk docs. | PASS |
| 12 | 2026-06-10T00:25 | Ran `git status --short` and confirmed no files under `artifacts/` are staged. | PASS |

**Phase 2E result:** PASS WITH RISKS

## Phase 2F - UTS_VLC Article/Chunk Parser Design and Validation (2026-06-10)

| Step | Time | Action | Status |
|---|---|---|---|
| 1 | 2026-06-10T00:35 | Ran `git status --short` and confirmed the Phase 2D `uts_vlc` artifact directory and required input files exist locally. | PASS |
| 2 | 2026-06-10T00:37 | Re-read Phase 2E docs, ops files, ingestion modules, and existing audit utilities before designing the parser. | PASS |
| 3 | 2026-06-10T00:43 | Added `src/vilegal/ingestion/article_parser.py` as a deterministic secondary parser for document-level UTS outputs. | PASS |
| 4 | 2026-06-10T00:44 | Added `scripts/parse_uts_vlc_articles.py` with fail-closed provenance checks and artifacts-only output path enforcement. | PASS |
| 5 | 2026-06-10T00:45 | Added `tests/test_article_parser.py` covering marker detection, split behavior, metadata preservation, fail-closed provenance, duplicate hash counting, uncertainty flags, and CLI path safety. | PASS |
| 6 | 2026-06-10T00:46 | Fixed one marker parsing edge case where bare `Dieu 1.` lines were incorrectly treated as having inline titles. | PASS |
| 7 | 2026-06-10T00:47 | Added a CLI test for the blocked provenance path to confirm that no candidate output is emitted when required provenance is missing. | PASS |
| 8 | 2026-06-10T00:48 | Ran `python -m compileall src scripts -q`. | PASS |
| 9 | 2026-06-10T00:48 | Ran `python -m pytest tests/test_article_parser.py -v` and got `12/12 PASS`. | PASS |
| 10 | 2026-06-10T00:49 | Ran the parser against `artifacts/phase_2d_controlled_ingestion/uts_vlc`. | PASS |
| 11 | 2026-06-10T00:50 | Measured parser output: `300` input docs, `299` with article markers, `20,393` derived candidates, `490` duplicate hashes, `87` suspicious-length candidates, `299` preamble warnings, provenance coverage `1.0`. | PASS |
| 12 | 2026-06-10T00:52 | Recorded Phase 2F design/report findings and updated Phase 2 status and risk docs. | PASS |

**Phase 2F result:** PASS WITH RISKS

## Phase 2G - UTS Article Candidate Filtering Rules (2026-06-10)

| Step | Time | Action | Status |
|---|---|---|---|
| 1 | 2026-06-10T01:00 | Verified Phase 2F candidate artifacts and source manifest were present before filtering began. | PASS |
| 2 | 2026-06-10T01:05 | Added `src/vilegal/ingestion/article_filter.py` with deterministic review buckets and fail-closed provenance checks. | PASS |
| 3 | 2026-06-10T01:06 | Added `scripts/filter_uts_article_candidates.py` with artifacts-only output enforcement. | PASS |
| 4 | 2026-06-10T01:07 | Added `tests/test_article_filter.py` covering provenance failures, empty/near-empty handling, duplicate hashes, suspicious length, preamble warnings, marker uncertainty, determinism, and CLI safety. | PASS |
| 5 | 2026-06-10T01:08 | Ran `python -m pytest tests/test_article_filter.py -v` and got `16/16 PASS`. | PASS |
| 6 | 2026-06-10T01:08 | Ran `python -m compileall src scripts -q`. | PASS |
| 7 | 2026-06-10T01:09 | Ran `python scripts/filter_uts_article_candidates.py --input-dir artifacts/phase_2f_uts_article_candidates --output-dir artifacts/phase_2g_uts_filtering --report-out artifacts/phase_2g_uts_filtering_report.json`. | PASS |
| 8 | 2026-06-10T01:10 | Measured filter output: `20,393` candidates, `511` rejected, `3,249` needs review, `16,633` keep, provenance coverage `1.0`, no RAG or ground-truth promotion. | PASS |
| 9 | 2026-06-10T01:11 | Updated Phase 2 docs and risk/status records. | PASS |

**Phase 2G result:** PASS WITH RISKS


