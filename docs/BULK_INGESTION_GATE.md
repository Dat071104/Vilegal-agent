# Phase 2 Bulk Ingestion Gate

This document serves as the formal checklist that must be completed and approved by a human reviewer **BEFORE** Phase 2D (Bulk Ingestion) can commence. 

> **WARNING:** Bulk ingestion of legal data involves significant bandwidth, storage, and legal compliance risks. Do not bypass these gates.

## The 7 Human Gates

| Gate ID | Requirement | Status | Reviewer Name | Date |
| :---: | :--- | :---: | :--- | :--- |
| **G1** | **License & Provenance Confirmed:** Have the licenses for target datasets been manually reviewed and confirmed acceptable for the project's goals? | [ ] | | |
| **G2** | **Attribution Template Committed:** Are the required attribution snippets documented in `docs/ATTRIBUTION.md`? | [ ] | | |
| **G3** | **Source-Specific Manifest Reviewed:** Are the provenance mechanisms in `src/vilegal/ingestion/provenance.py` sufficient to track data lineage? | [ ] | | |
| **G4** | **Storage Path Gitignored:** Is it confirmed that the target output directories for bulk data (e.g., `artifacts/`, `data/`) are properly ignored in `.gitignore`? | [ ] | | |
| **G5** | **Max-Record Override Approved:** Has a human explicitly approved overriding the hard cap (`MAX_RECORDS_HARD_CAP`) in the codebase for the bulk run? | [ ] | | |
| **G6** | **Quality Thresholds Approved:** Are the metrics and thresholds in `src/vilegal/ingestion/quality_checks.py` considered adequate for bulk data validation? | [ ] | | |
| **G7** | **Rollback & Deletion Plan Documented:** Is there a clear procedure to delete the ingested dataset if a license violation or critical defect is discovered post-ingestion? | [ ] | | |

## Rollback & Deletion Plan (G7)
*Reviewer to fill out or reference procedure before approving G7:*
- **To delete bulk data:** Run `rm -rf artifacts/bulk_ingestion_output/` and clear local Hugging Face caches via `rm -rf ~/.cache/huggingface/datasets/`.
- **To scrub git history:** (N/A if G4 was followed correctly, as data was never staged).

---

**Final Approval:**
Phase 2D (Bulk Ingestion) is **BLOCKED** until all gates above are checked `[x]` and signed off by an authorized human reviewer.
