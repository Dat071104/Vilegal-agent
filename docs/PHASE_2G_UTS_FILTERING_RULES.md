# Phase 2G UTS Filtering Rules Report

**Date:** 2026-06-10
**Executive verdict:** PASS WITH RISKS

## Why Phase 2G Exists

Phase 2G filters the parser-derived UTS article/chunk candidates from Phase 2F into transparent review buckets. It is a review layer, not a corpus approval step.

## Input Artifacts

- `artifacts/phase_2f_uts_article_candidates/article_candidates.jsonl`
- `artifacts/phase_2f_uts_article_candidates/parse_report.json`
- `artifacts/phase_2f_uts_article_candidates/parse_warnings.jsonl`
- `artifacts/phase_2d_controlled_ingestion/uts_vlc/provenance_manifest.json`

## Output Artifacts

- `artifacts/phase_2g_uts_filtering/filtered_candidates.jsonl`
- `artifacts/phase_2g_uts_filtering/rejected_candidates.jsonl`
- `artifacts/phase_2g_uts_filtering/needs_review_candidates.jsonl`
- `artifacts/phase_2g_uts_filtering/filter_report.json`
- `artifacts/phase_2g_uts_filtering/decision_counts.json`

## Filtering Rules

Rule buckets used:

- `reject_empty`
- `reject_near_empty`
- `reject_duplicate_hash`
- `reject_missing_parent_provenance`
- `reject_missing_required_text`
- `reject_missing_required_hash`
- `needs_review_suspicious_length`
- `needs_review_preamble_or_header_noise`
- `needs_review_marker_uncertainty`
- `keep_candidate_for_human_review`

Parent document warnings are retained in `risk_flags` and `parent_document_warning_codes`, but they do not automatically force `needs_review`.

## Safety Guarantees

- `is_legal_ground_truth` stays `false`.
- `approved_for_rag_index` stays `false`.
- Parent provenance is preserved.
- Required provenance failures fail closed.
- Phase 2D and Phase 2F artifacts are not modified.
- `artifacts/` output paths are enforced.

## Measured Run

Measured from `artifacts/phase_2g_uts_filtering/filter_report.json`.

| Metric | Value |
|---|---|
| total_input_candidates | `20,393` |
| total_output_records | `20,393` |
| total_rejected | `511` |
| total_needs_review | `3,249` |
| total_keep_candidate_for_human_review | `16,633` |
| duplicate_hash_groups | `339` |
| duplicate_candidates_rejected | `490` |
| parent_document_warning_count | `299` |
| near_empty_count | `22` |
| suspicious_length_count | `87` |
| preamble_warning_count | `0` |
| parent_provenance_coverage | `1.0` |
| approved_for_rag_index_true_count | `0` |
| is_legal_ground_truth_true_count | `0` |

## Metric Notes

- `duplicate_hash_groups` counts distinct `article_hash` values with more than one candidate.
- `duplicate_candidates_rejected` is `sum(count - 1)` across those groups.
- `suspicious_length_count` is recomputed from candidate text using the Phase 2F thresholds (`< 100` or `> 50,000` chars).
- `parent_document_warning_count` tracks the 299 Phase 2F preamble warnings separately from candidate-level review flags.
- `preamble_warning_count` is now candidate-level only and is `0` for this corpus.

## Known Risks

- Duplicate content remains present.
- Parent document preamble warnings remain present, but they are metadata only.
- Some candidates still need human review for marker uncertainty or suspicious length.
- Phase 3 remains blocked.

## Validation Commands

```bash
python -m compileall src scripts -q
python -m pytest tests -v
python -m pytest tests/test_article_filter.py -v
python scripts/filter_uts_article_candidates.py --input-dir artifacts/phase_2f_uts_article_candidates --output-dir artifacts/phase_2g_uts_filtering --report-out artifacts/phase_2g_uts_filtering_report.json
git status --short
```

## Safe Git Add Command

```bash
git add docs/PHASE_2G_UTS_FILTERING_RULES.md scripts/filter_uts_article_candidates.py src/vilegal/ingestion/article_filter.py tests/test_article_filter.py
```

## Commit Message Suggestion

```text
chore: add phase 2g uts filtering rules
```

## Recommendation

Phase 2H is not started in this repo state. Any later manual review pack should be approved separately; Phase 3 remains blocked.
