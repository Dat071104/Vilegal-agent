# Data Use & Commitment Policy

This policy governs the handling, storage, and publishing of data within the ViLegal Agent project to ensure compliance with licenses, copyright, and safe engineering practices.

## 1. What MUST Stay Local (Never Committed)
The following items must **NEVER** be committed to the Git repository or published publicly without explicit, documented legal approval:
- **Raw or Full Legal Datasets**: e.g., massive `.jsonl`, `.parquet`, or `.csv` files containing the full text of legal corpora.
- **Downloaded Hugging Face Caches**: The `.cache/huggingface/` or `hf_cache/` directories.
- **Generated Local Artifacts**: Any data generated in the `artifacts/` folder (except for explicitly tracked test fixtures).
- **Model Weights & Checkpoints**: Any `.bin`, `.safetensors`, `.pt`, or related model files.
- **Secrets & API Keys**: `.env` files or tokens.

*Rule: Raw/full legal datasets are NOT committed to Git.*

## 2. What CAN Be Committed (Git Tracked)
The following items are safe to commit to version control:
- **Source Code**: Python scripts, modules, and tests (`src/`, `scripts/`, `tests/`).
- **Documentation**: Markdown files (`docs/`, `_ops/`), including audit reports, architecture plans, and logs.
- **Synthetic Test Fixtures**: Small, hand-crafted, or synthetic files containing fictitious data (e.g., `tests/fixtures/synthetic_legal_articles.jsonl`) used exclusively for unit testing.
- **Aggregated Metrics**: JSON reports detailing quality metrics or validation results, provided they do not contain raw legal text.

## 3. Publishing to GitHub
- The repository must strictly adhere to the rules above.
- Ensure that `artifacts/`, `.cache/`, and `hf_cache/` remain effectively ignored by `.gitignore`.

## 4. Publishing to Hugging Face (Future Phases)
If fine-tuned models or derived datasets are published to Hugging Face in the future:
- **License Inheritance**: The published artifact must respect the licenses of the source data (e.g., CC-BY-4.0 requirements).
- **Attribution**: The Hugging Face Model Card or Dataset Card must include the precise snippets defined in `docs/ATTRIBUTION.md`.
- **Data Sanitization**: No PII or restricted state secrets may be included.

## 5. Human Review Requirements
- **Bulk Ingestion**: Requires explicit sign-off on the 7 gates defined in `docs/BULK_INGESTION_GATE.md`.
- **Public Release**: Any deployment of models or data to public hubs requires manual review of the exact artifacts to ensure no restricted data "leaked" into the release payload.
