# Data Source Audit - Phase 1

**Audit date:** 2026-06-09  
**Phase status:** PASS WITH RISKS  
**Scope:** Re-audit of Phase 1 source decisions only. No Phase 2 implementation, no scraping, no bulk download.

## Claim labels

Every data and license claim in this document is tagged as one of:

- `CONFIRMED`: verified from the current source card or from the local repository state.
- `ASSUMPTION`: plausible but not directly verified during this audit.
- `NEEDS MANUAL REVIEW`: cannot be treated as settled for this repo.

## Re-check method

- `CONFIRMED`: Current Hugging Face dataset cards for the datasets below were re-checked on 2026-06-09.
- `CONFIRMED`: Local repository files were re-read on 2026-06-09.
- `NEEDS MANUAL REVIEW`: No official VBPL policy or API access document is stored inside this repo, so any claim about registration, restricted access, or permitted automation remains unresolved here.

## Source register

| ID | Source | Source class | Current license field | Provenance note | Coverage note | Audit status |
|---|---|---|---|---|---|---|
| S1 | `vbpl.vn` | Official source | `NEEDS MANUAL REVIEW`: no repo-local official license or API policy document | `CONFIRMED`: VBPL is the official Vietnamese legal document portal. `NEEDS MANUAL REVIEW`: access constraints, API registration, and automation limits for this repo. | `CONFIRMED`: official portal covers broad legal document types. | Not approved for automated acquisition from this repo. |
| S2 | `th1nhng0/vietnamese-legal-documents` | Derived dataset | `CONFIRMED`: Hugging Face card currently lists `cc-by-4.0` | `CONFIRMED`: dataset card says it is sourced from `vbpl.vn`. `NEEDS MANUAL REVIEW`: downstream right to redistribute a broad VBPL snapshot under CC-BY-4.0. | `CONFIRMED`: broad snapshot including laws, decrees, circulars, decisions, and other normative acts. | Sample-only candidate after attribution planning; bulk download blocked pending provenance review. |
| S3 | `undertheseanlp/UTS_VLC` | Derived dataset | `CONFIRMED`: Hugging Face card currently lists `mit` | `CONFIRMED`: dataset card says the corpus is sourced from VBPL and cross-referenced with official and aggregator sites. `NEEDS MANUAL REVIEW`: downstream provenance and relicensing basis still need human review. | `CONFIRMED`: scope is limited to Constitution, Codes, and Laws. `CONFIRMED`: no decrees, circulars, or decisions in this corpus. | Highest-quality limited corpus candidate; bulk download blocked pending provenance review. |
| S4 | `duyet/vietnamese-legal-instruct` | Generated instruction dataset | `CONFIRMED`: Hugging Face card currently lists `cc-by-4.0` | `CONFIRMED`: dataset card says it is built from `th1nhng0/vietnamese-legal-documents`. `CONFIRMED`: this is generated instruction data, not source-of-truth law text. `NEEDS MANUAL REVIEW`: downstream relicensing and source-chain rights still need human review. | `CONFIRMED`: broad instruction coverage across multiple legal document types, but answer quality depends on the generator and source snapshot. | Sample-only candidate after attribution planning; bulk download blocked pending provenance review. |
| S5 | `thangvip/vietnamese-legal-qa` | Generated QA dataset | `CONFIRMED`: dataset card does not expose an SPDX-style license field and instead states "appropriate license for Vietnamese legal documents" | `CONFIRMED`: generated QA pairs are not authoritative legal text. `NEEDS MANUAL REVIEW`: exact downstream license scope is unresolved. | `CONFIRMED`: useful for evaluation-style QA, not for source-of-truth legal ingestion. | Evaluation-only candidate after manual review. |
| S6 | Third-party legal sites | Third-party source | `ASSUMPTION`: site-specific automation terms may restrict scraping | `ASSUMPTION`: provenance may mix official text with editorial material. | `ASSUMPTION`: broad coverage varies by site. | Rejected for this phase. |
| S7 | Local synthetic examples | Synthetic example source | `CONFIRMED`: locally authored examples only | `CONFIRMED`: records in `data/processed/sample_legal_articles.jsonl` are synthetic and schema-valid. | `CONFIRMED`: only for local testing. | Approved for sample-only validation. |

## Blocking corrections applied in this re-audit

1. `CONFIRMED`: `duyet/vietnamese-legal-instruct` is no longer documented as Apache-2.0 in this repo. The current Hugging Face card lists `cc-by-4.0`.
2. `CONFIRMED`: `undertheseanlp/UTS_VLC` is no longer documented as license-unclear in this repo. The current Hugging Face card lists `mit`.
3. `CONFIRMED`: `th1nhng0/vietnamese-legal-documents` is no longer documented as license-unclear in this repo. The current Hugging Face card lists `cc-by-4.0`.
4. `CONFIRMED`: generated instruction and QA datasets are now described as generated supervision, not as ground-truth legal text.
5. `NEEDS MANUAL REVIEW`: any repo claim that VBPL API registration or restricted access is required remains unresolved until an official source document is stored in the repo.

## Coverage assessment

- `CONFIRMED`: `undertheseanlp/UTS_VLC` is the cleanest currently cited corpus in the repo.
- `CONFIRMED`: `undertheseanlp/UTS_VLC` is narrow. It covers Constitution, Codes, and Laws only.
- `CONFIRMED`: decrees, circulars, decisions, and other sub-law instruments are represented in `th1nhng0/vietnamese-legal-documents`, not in `undertheseanlp/UTS_VLC`.
- `CONFIRMED`: `duyet/vietnamese-legal-instruct` inherits its breadth from `th1nhng0/vietnamese-legal-documents`.
- `ASSUMPTION`: broad snapshots are not automatically clean simply because they are large or structured.

## Licensing and attribution controls

- `CONFIRMED`: CC-BY-4.0 datasets require attribution, a link to the license, and an indication of changes made.
- `CONFIRMED`: this applies to `th1nhng0/vietnamese-legal-documents` and `duyet/vietnamese-legal-instruct` as currently labeled on Hugging Face.
- `NEEDS MANUAL REVIEW`: the existence of a CC-BY-4.0 label on a derived legal-text dataset does not by itself settle the upstream right to relicense the underlying corpus.

### Minimum attribution rule for any Phase 2 sample-only use

For every CC-BY-4.0 dataset sample or derivative artifact, keep:

1. Dataset name and maintainer.
2. Dataset card URL.
3. The label `CC-BY-4.0`.
4. A note stating whether records were filtered, transformed, or reformatted.

## Phase 2 readiness decision

- `CONFIRMED`: Phase 2 implementation has not started.
- `NEEDS MANUAL REVIEW`: unresolved provenance and relicensing questions remain for every non-synthetic candidate source.
- `CONFIRMED`: Phase 2 is **BLOCKED FOR BULK DOWNLOAD**.
- `CONFIRMED`: Phase 2 is **ALLOWED FOR SAMPLE-ONLY INGESTION** if the default safety limit stays at `--max-records 100` and provenance fields are captured for every record.
