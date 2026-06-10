# Track A2 — Kaggle Synthetic Fine-Tune Demo

## Executive Verdict

**SYNTHETIC FINE-TUNE DEMO PATH ONLY.**

> **This is synthetic-demo only. Not legal advice. Not official legal text.**
> No real legal corpus is used. No UTS_VLC candidates. No corpus manifest.
> Track B real legal corpus governance remains **blocked**.

Track A2 enables a Kaggle-hosted synthetic fine-tune demonstration using only the
`synthetic-demo` data generated under Track A1.5. This is a portfolio AI engineering
demo. It does not demonstrate legal correctness, legal-ground-truth capability, or
real legal corpus training.

The flagship Track A2 portfolio run is **Qwen2.5-7B QLoRA on Kaggle** via
`unsloth/Qwen2.5-7B-Instruct`. `Qwen/Qwen2.5-3B-Instruct` is the local/dev baseline
because the user can already run 3B locally. `Qwen/Qwen2.5-0.5B-Instruct` remains
smoke-test only.

Track B real legal corpus governance remains **blocked** for QA, SFT, and RAG.

---

## Safety Boundaries

> [!IMPORTANT]
> All outputs from this track are **synthetic-demo artifacts only**.
> They do NOT constitute legal advice, official legal text, or legal-ground-truth data.

| Boundary | Status |
|---|---|
| Use real legal corpus | ❌ BLOCKED |
| Use UTS_VLC candidates | ❌ BLOCKED |
| Use corpus_candidate_manifest | ❌ BLOCKED |
| Mark as legal ground truth | ❌ BLOCKED |
| approved_for_rag_index=true | ❌ BLOCKED |
| Local fine-tuning | ❌ BLOCKED |
| Kaggle fine-tuning (synthetic only) | ✅ ALLOWED |
| Model download on Kaggle | ✅ ALLOWED |
| Push to Hub by default | ❌ BLOCKED (requires explicit opt-in) |
| Track B unblocked by Track A2 | ❌ NO |

---

## Prerequisites

1. **Track A1.5 split artifacts** must exist locally:
   - `artifacts/track_a_synthetic_demo/splits/train.jsonl` (2000 rows)
   - `artifacts/track_a_synthetic_demo/splits/validation.jsonl` (250 rows)
   - `artifacts/track_a_synthetic_demo/splits/test.jsonl` (250 rows)

   If these do not exist, run the Track A1.5 split workflow first:
   ```powershell
   python scripts/split_synthetic_demo_qa.py --input artifacts/track_a_synthetic_demo/qa_pairs.synthetic-demo.jsonl --output-dir artifacts/track_a_synthetic_demo/splits
   ```

2. **Kaggle account** with GPU access (T4 or better recommended for the demo).

3. **Python 3.10+** for local packaging and validation.

---

## How to Prepare Kaggle Dataset Locally

Run the packaging script to create a Kaggle-ready dataset folder:

```powershell
python scripts/prepare_kaggle_synthetic_dataset.py `
    --split-dir artifacts/track_a_synthetic_demo/splits `
    --output-dir artifacts/track_a_kaggle_dataset `
    --zip-out artifacts/track_a_kaggle_dataset.zip
```

The script will:
1. Validate all split files for synthetic-only constraints.
2. Confirm expected row counts (train=2000, validation=250, test=250).
3. Confirm `source == synthetic-demo`, `is_synthetic == true`,
   `is_legal_ground_truth == false`, `approved_for_rag_index == false` for all rows.
4. Copy split files to `artifacts/track_a_kaggle_dataset/`.
5. Write a `DATASET_CARD.md` with the synthetic-only disclaimer.
6. Optionally create `artifacts/track_a_kaggle_dataset.zip`.

> [!WARNING]
> Do NOT run `git add artifacts/`. The dataset folder is listed in `.gitignore`
> and must remain untracked. It is for local manual upload to Kaggle only.

---

## How to Upload Dataset Manually to Kaggle

1. Log in to [kaggle.com](https://www.kaggle.com).
2. Navigate to **Datasets** → **New Dataset**.
3. Set dataset title to `vilegal-synthetic-demo` (or your preferred name).
4. Upload the contents of `artifacts/track_a_kaggle_dataset/` or the zip archive.
5. Set visibility to **Private**.
6. Add the disclaimer to the dataset description:
   `SYNTHETIC DEMO ONLY — NOT LEGAL ADVICE — NOT OFFICIAL LEGAL TEXT`
7. Note the dataset slug (e.g. `yourusername/vilegal-synthetic-demo`).

---

## How to Run the Notebook

1. Upload the notebook `notebooks/track_a_kaggle_synthetic_finetune_demo.ipynb`
   to Kaggle as a new notebook.
2. Attach your `vilegal-synthetic-demo` dataset as input at path:
   `/kaggle/input/vilegal-synthetic-demo`
3. Enable GPU (T4 × 2 recommended for QLoRA demo).
4. The default `BASE_MODEL_NAME` in Section 1 is `unsloth/Qwen2.5-7B-Instruct`.
   Change it only if you intentionally need the 3B local/dev baseline or the 0.5B smoke-test profile.
5. Run all cells in order:
   - Section 1: Configuration
   - Section 2: Dataset Validation (fails closed if safety constraints violated)
   - Section 3: Data Formatting
   - Section 4: LoRA/QLoRA Setup
   - Section 5: Fine-Tuning (synthetic data, Kaggle GPU only)
   - Section 6: Evaluation (base vs. adapter)
   - Section 7: Benchmark Export
   - Section 8: Portfolio Evidence Checklist

---

## Expected Outputs

| Output | Path | Description |
|---|---|---|
| LoRA adapter files | `/kaggle/working/vilegal-synthetic-demo-adapter/` | Adapter weights from synthetic fine-tuning |
| Benchmark JSON | `/kaggle/working/track_a_benchmark_results.json` | Base vs adapter comparison on synthetic test set |
| Training log | Kaggle notebook output | Loss curve and epoch metrics |
| Screenshots | Manual capture | Portfolio evidence |

> [!NOTE]
> Adapter files are saved to Kaggle's working directory only.
> They must **NOT** be committed to git.
> Download them from Kaggle if needed for further local inspection.

---

## Validation Before Committing

Run the validator to confirm all safety constraints:

```powershell
python scripts/validate_track_a_kaggle_demo.py
```

Run the full test suite:

```powershell
python -m pytest tests/test_track_a_kaggle_demo.py -v
```

---

## Portfolio Interpretation

Track A2 **demonstrates:**
- ML fine-tune workflow mechanics (dataset loading, validation, formatting, LoRA, SFT)
- QLoRA setup for the flagship 7B Kaggle target, with 3B retained as the local/dev baseline
- Benchmark comparison methodology (base vs. adapter)
- Fail-closed synthetic-only safety validation pipeline

Track A2 does **NOT** demonstrate:
- Real legal accuracy
- Legal correctness
- Ground-truth legal text processing
- Production-ready legal AI capability

### Required disclaimer for any public use

> **SYNTHETIC DEMO ONLY — NOT LEGAL ADVICE — NOT OFFICIAL LEGAL TEXT**
>
> Track A demonstrates AI engineering mechanics, not real legal capability.
> Track B real legal corpus governance remains blocked for QA/SFT/RAG.
