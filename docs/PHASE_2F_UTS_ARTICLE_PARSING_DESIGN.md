# Phase 2F UTS Article/Chunk Parser Report

**Date:** 2026-06-10
**Executive verdict:** PASS WITH RISKS

## Scope

Phase 2F implements a secondary parser over the existing document-level Phase 2D `UTS_VLC` normalized outputs only.

This work is limited to parser design and validation:

- it is not QA generation;
- it is not fine-tuning;
- it is not RAG or vector index construction;
- it does not verify legal correctness;
- it does not convert parser candidates into legal ground truth.

All generated outputs are written only under ignored `artifacts/`.

## Inputs Used

- `artifacts/phase_2d_controlled_ingestion/uts_vlc/sample_normalized.jsonl`
- `artifacts/phase_2d_controlled_ingestion/uts_vlc/provenance_manifest.json`
- `artifacts/phase_2d_controlled_ingestion/uts_vlc/quality_report.json`

No new ingestion was run.

## Implementation

### Code added

- `src/vilegal/ingestion/article_parser.py`
- `scripts/parse_uts_vlc_articles.py`
- `tests/test_article_parser.py`

### Parser behavior

The parser is deterministic and read-only with respect to Phase 2D inputs.

It:

1. reads existing normalized UTS document records;
2. detects article markers such as:
   - `Dieu 1.`
   - `Dieu 1:`
   - `Dieu 1 ...`
   - markdown heading variants like `# Dieu 1. ...`
   - mojibake marker variants visible in terminal output;
3. splits document text into article/chunk candidates;
4. preserves parent provenance:
   - `source_dataset`
   - `source_id`
   - `source_url`
   - `license`
   - `retrieved_at`
   - `title`
   - `parent_record_id`
5. derives candidate metadata where possible:
   - `article_number`
   - `article_title`
   - `chunk_index`
   - `text`
   - `text_hash`
   - `parser_version`
6. marks uncertainty explicitly through `parse_flags` and `uncertain_parse`;
7. sets:
   - `is_legal_ground_truth=false`
   - `approved_for_rag_index=false`

### Output safety

The CLI refuses output paths outside `artifacts/`.

It also refuses:

- writing into the input directory;
- nesting output under the Phase 2D input path;
- reporting to a path outside `artifacts/`.

### Fail-closed provenance behavior

Required parent provenance fields:

- `source_dataset`
- `record_id`
- `license`
- `retrieved_at`
- `source_id` or `source_url`

If any parent record is missing those fields, the CLI exits non-zero, writes a blocked `parse_report.json` if safe, and does not emit `article_candidates.jsonl`.

## Measured Results

Measured from:

- `artifacts/phase_2f_uts_article_candidates/parse_report.json`
- `artifacts/phase_2f_uts_article_parse_report.json`

### Metrics summary

| Metric | Value |
|---|---|
| input_document_count | `300` |
| documents_with_article_markers | `299` |
| documents_without_article_markers | `1` |
| derived_article_count | `20,393` |
| empty_derived_article_count | `0` |
| near_empty_derived_article_count | `10` |
| duplicate_article_hash_count | `490` |
| documents_with_single_article | `0` |
| documents_with_multiple_articles | `299` |
| article_number_parse_success_rate | `1.0` |
| parent_provenance_coverage | `1.0` |
| suspicious_article_length_count | `87` |
| parse_warning_count | `299` |

### Safety gate results

- Empty derived article rate `<= 0.5%`: PASS
- Parent provenance coverage `== 100%`: PASS
- Source provenance retained on output candidates: PASS
- All output candidates marked not ground truth: PASS
- All output candidates marked not approved for RAG index: PASS

## Interpretation

The parser successfully derives a large article/chunk candidate set from the document-level UTS records without losing parent provenance.

However, the output is still parser-derived and carries clear residual risk:

- `490` duplicate article hashes indicate repeated or structurally identical segments across the corpus;
- `87` suspicious-length candidates need downstream filtering rules;
- `299` documents emit preamble warnings before the first article marker;
- `1` document yielded no article markers and was rejected.

These outputs are parser candidates only. They are not legal ground truth and are not approved for RAG indexing.

## Output Files

Under `artifacts/phase_2f_uts_article_candidates/`:

- `article_candidates.jsonl`
- `parse_report.json`
- `rejected_documents.jsonl`
- `parse_warnings.jsonl`

Additional report copy:

- `artifacts/phase_2f_uts_article_parse_report.json`

## Validation Results

1. `python -m compileall src scripts -q` -> PASS
2. `python -m pytest tests -v` -> PASS
3. `python scripts/parse_uts_vlc_articles.py --input-dir artifacts/phase_2d_controlled_ingestion/uts_vlc --output-dir artifacts/phase_2f_uts_article_candidates --report-out artifacts/phase_2f_uts_article_parse_report.json` -> PASS
4. `git status --short` -> PASS

## Phase Boundary

- Phase 3 remains blocked.
- Do not generate QA.
- Do not fine-tune.
- Do not build RAG or vector indexes.
- Do not treat parser-derived article/chunk records as legally authoritative.

## Recommendation

Proceed to **Phase 2G filtering rules** only.

The next phase should focus on:

1. duplicate-hash handling;
2. suspicious-length filtering rules;
3. preamble and no-marker rejection policy;
4. conservative rules for retaining only parser candidates suitable for later review.
