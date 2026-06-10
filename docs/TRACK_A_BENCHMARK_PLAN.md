# Track A Benchmark Plan

## Benchmark Goal

Demonstrate a reproducible evaluation methodology for the Track A synthetic fine-tune demo.

This benchmark compares a base instruct model against a LoRA-adapted model trained on
the `synthetic-demo` dataset. All metrics are **proxy metrics on synthetic data only**
and do not represent real legal accuracy or legal-ground-truth evaluation.

> [!IMPORTANT]
> This benchmark does NOT measure real legal capability.
> All data used is `synthetic-demo` only. Not legal advice. Not official legal text.
> Track B real legal corpus benchmarking remains blocked until Track B safety gates are cleared.

---

## Synthetic Test Set

| Property | Value |
|---|---|
| Source | `synthetic-demo` |
| Split | `test` |
| Rows | 250 |
| `is_synthetic` | `true` |
| `is_legal_ground_truth` | `false` |
| `approved_for_rag_index` | `false` |
| Disclaimer | present on every row |
| Tasks | classification, explanation, retrieval_style_qa, drafting_demo |
| Difficulties | easy, medium, hard |

Evaluation uses a random sample of 50 rows from the 250-row test split (configurable).

---

## Baseline vs Adapter Comparison

| Step | Description |
|---|---|
| 1. Load base model | Load `unsloth/Qwen2.5-7B-Instruct` for the flagship Kaggle run. Use `Qwen/Qwen2.5-3B-Instruct` only as the local/dev baseline or `Qwen/Qwen2.5-0.5B-Instruct` for smoke tests. |
| 2. Evaluate base | Run inference on `EVAL_SAMPLE_SIZE` test rows using inference-style prompts. |
| 3. Load adapter | Load the LoRA adapter from `/kaggle/working/vilegal-synthetic-demo-adapter/`. |
| 4. Evaluate adapter | Run inference on the same rows with the adapter applied. |
| 5. Compute metrics | Compute format validity, synthetic task pass rate, disclaimer rate. |
| 6. Export | Save results to `/kaggle/working/track_a_benchmark_results.json`. |

---

## Suggested Metrics

| Metric | Description | How Computed |
|---|---|---|
| `format_valid_rate` | Fraction of responses that are non-empty and exceed minimum length. | `len(response) > 10` |
| `disclaimer_compliance_rate` | Fraction of prompts that included the synthetic disclaimer in context. | All prompts include disclaimer by design → 1.0 |
| `synthetic_task_pass_rate` | Proxy accuracy: fraction of responses with ≥15% word overlap with reference output. | Word overlap ratio ≥ 0.15 |
| `refusal_safety_rate` | Fraction of responses that do NOT claim to be official legal advice. | Check for absence of "this is official legal advice" and similar patterns. |

> [!NOTE]
> These are proxy metrics only. They measure format compliance and keyword overlap
> on synthetic data, not real legal accuracy.

---

## Suggested Benchmark Table

| Model | Dataset | Examples | format_valid_rate | synthetic_task_pass_rate | disclaimer_present_rate | Notes |
|---|---|---|---|---|---|---|
| `unsloth/Qwen2.5-7B-Instruct` (base) | synthetic-demo/test | 50 | — | — | 1.0 | Flagship Kaggle baseline |
| `unsloth/Qwen2.5-7B-Instruct` + LoRA (Track A2) | synthetic-demo/test | 50 | — | — | 1.0 | Flagship Kaggle 7B QLoRA demo |

*Fill in metric values from `track_a_benchmark_results.json` after running the Kaggle notebook.*

---

## Screenshot / Evidence Checklist for Portfolio

Collect these screenshots from the Kaggle notebook run:

- [ ] **Dataset validation output** — shows all splits passing synthetic-only constraints.
- [ ] **Training loss curve** — from the Kaggle training log (Section 5).
- [ ] **Base model evaluation output** — `format_valid_rate` and `synthetic_task_pass_rate` for base model.
- [ ] **Adapter evaluation output** — same metrics after fine-tuning.
- [ ] **Benchmark JSON contents** — full `track_a_benchmark_results.json` from `/kaggle/working/`.
- [ ] **Adapter directory listing** — shows adapter files saved in `/kaggle/working/vilegal-synthetic-demo-adapter/`.
- [ ] **Notebook disclaimer cell** — shows the synthetic-only warning prominently displayed.

---

## Safety Reminders

> [!CAUTION]
> Do not present benchmark results as evidence of real legal AI capability.
> Do not use the phrase "legal accuracy" without explicitly noting it refers to synthetic-demo proxy metrics only.
> Do not mark any output as `is_legal_ground_truth=true` or `approved_for_rag_index=true`.

### Required disclaimer for all benchmark presentations

```
SYNTHETIC DEMO ONLY — NOT LEGAL ADVICE — NOT OFFICIAL LEGAL TEXT

All metrics are proxy metrics on synthetic data.
They do NOT represent real legal accuracy or legal-ground-truth capability.
Track A demonstrates AI engineering mechanics only.
Track B real legal corpus governance remains blocked.
```

---

## Future Benchmark Extensions (Track A3+)

These are planned but not yet implemented:

| Extension | Description | Track |
|---|---|---|
| Retrieval demo benchmark | Compare synthetic-demo RAG retrieval on canned QA | Track A3 |
| Disclaimer refusal rate | Measure rate of safety refusals on legal-advice-like prompts | Track A3+ |
| Multi-model comparison | Compare 7B Kaggle run vs 3B local/dev baseline on the same synthetic test set | Track A2+ |
| Full test set evaluation | Evaluate on all 250 test rows (not just 50-row sample) | Track A2 refresh |
