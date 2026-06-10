from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .scaffold_config import Phase3AScaffoldConfig, load_phase3a_scaffold_config

FORBIDDEN_NOTEBOOK_PATTERNS = (
    "trainer.train(",
    "model.fit(",
    "push_to_hub(",
    "save_pretrained(",
    "AutoModelForCausalLM.from_pretrained(",
    "AutoTokenizer.from_pretrained(",
    "SFTTrainer(",
    "TrainingArguments(",
)

REQUIRED_DOC_PHRASES = (
    "scaffold-only",
    "qa generation blocked",
    "fine-tuning blocked",
    "rAG/vector indexing blocked",
    "dataset publishing blocked",
    "future human gate required",
)

SAFETY_FLAGS = (
    "allow_training",
    "allow_qa_generation",
    "allow_rag_indexing",
    "allow_dataset_publish",
    "allow_model_download_by_default",
    "allow_hub_push",
    "allow_adapter_save",
)


@dataclass(frozen=True)
class Phase3AScaffoldValidationReport:
    config: Phase3AScaffoldConfig
    notebook_path: Path
    docs_path: Path
    forbidden_hits: list[str]


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _collect_code_sources(notebook_payload: dict) -> list[str]:
    code_sources: list[str] = []
    for cell in notebook_payload.get("cells", []):
        if cell.get("cell_type") != "code":
            continue
        source = "".join(cell.get("source", []))
        code_sources.append(source)
    return code_sources


def _scan_forbidden_patterns(code_sources: list[str]) -> list[str]:
    hits: list[str] = []
    for source in code_sources:
        for pattern in FORBIDDEN_NOTEBOOK_PATTERNS:
            if pattern in source:
                hits.append(pattern)
    return sorted(set(hits))


def _validate_config(config: Phase3AScaffoldConfig) -> None:
    _require(config.phase == "3A", "Config phase must be '3A'.")
    _require(config.name == "Kaggle/QLoRA Scaffold Only", "Config name is unexpected.")
    _require(config.mode == "scaffold_only", "Config mode must be scaffold_only.")

    for key in SAFETY_FLAGS:
        _require(config.safety.get(key) is False, f"Safety flag must be false: {key}")

    _require(
        config.safety.get("require_future_human_gate") is True,
        "Safety flag require_future_human_gate must be true.",
    )
    _require(
        config.data.get("use_real_legal_corpus") is False,
        "Real legal corpus usage must remain disabled.",
    )
    _require(
        config.data.get("use_corpus_candidate_manifest") is False,
        "Corpus candidate manifest usage must remain disabled.",
    )
    _require(
        config.data.get("require_approved_sft_dataset") is True,
        "Approved SFT dataset gate must remain required.",
    )


def _validate_notebook(notebook_path: Path) -> list[str]:
    payload = json.loads(notebook_path.read_text(encoding="utf-8"))
    notebook_text = json.dumps(payload, ensure_ascii=False)
    _require(
        "SCAFFOLD ONLY — NO TRAINING EXECUTED" in notebook_text,
        "Notebook must contain the scaffold-only warning.",
    )
    code_sources = _collect_code_sources(payload)
    return _scan_forbidden_patterns(code_sources)


def _validate_docs(docs_path: Path) -> None:
    content = docs_path.read_text(encoding="utf-8").lower()
    for phrase in REQUIRED_DOC_PHRASES:
        normalized_phrase = phrase.lower()
        _require(normalized_phrase in content, f"Docs must mention: {phrase}")


def validate_phase3a_scaffold(
    *,
    config_path: str | Path,
    notebook_path: str | Path,
    docs_path: str | Path,
) -> Phase3AScaffoldValidationReport:
    config = load_phase3a_scaffold_config(config_path)
    _validate_config(config)

    notebook_path = Path(notebook_path)
    docs_path = Path(docs_path)
    forbidden_hits = _validate_notebook(notebook_path)
    _require(not forbidden_hits, f"Forbidden active notebook code found: {', '.join(forbidden_hits)}")
    _validate_docs(docs_path)

    return Phase3AScaffoldValidationReport(
        config=config,
        notebook_path=notebook_path,
        docs_path=docs_path,
        forbidden_hits=forbidden_hits,
    )
