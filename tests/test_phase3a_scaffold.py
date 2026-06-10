from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from vilegal.training.scaffold_config import load_phase3a_scaffold_config
from vilegal.training.safety_gate import FORBIDDEN_NOTEBOOK_PATTERNS, validate_phase3a_scaffold


ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "configs" / "phase3a_qlora_scaffold.yaml"
NOTEBOOK_PATH = ROOT / "notebooks" / "phase3a_kaggle_qlora_scaffold.ipynb"
DOCS_PATH = ROOT / "docs" / "PHASE_3A_KAGGLE_QLORA_SCAFFOLD.md"
VALIDATOR_PATH = ROOT / "scripts" / "validate_phase3a_scaffold.py"


def _write_text(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def _unsafe_config_text() -> str:
    return """phase: "3A"
name: "Kaggle/QLoRA Scaffold Only"
mode: "scaffold_only"

safety:
  allow_training: true
  allow_qa_generation: false
  allow_rag_indexing: false
  allow_dataset_publish: false
  allow_model_download_by_default: false
  allow_hub_push: false
  allow_adapter_save: false
  require_future_human_gate: true

data:
  use_real_legal_corpus: false
  use_corpus_candidate_manifest: false
  require_approved_sft_dataset: true
  approved_sft_dataset_path: null

training:
  base_model_name: null
  output_dir: null
  lora_r: null
  lora_alpha: null
  lora_dropout: null
  max_seq_length: null
  train_batch_size: null
  gradient_accumulation_steps: null
  learning_rate: null
  num_train_epochs: null

blocked_until_future_gate:
  - "QA/SFT dataset gate approval"
  - "source viability decision"
  - "human approval for real legal corpus use"
  - "train/validation/test split approval"
  - "evaluation plan approval"
"""


def _unsafe_notebook_text() -> str:
    payload = {
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": ["# Phase 3A — Kaggle/QLoRA Scaffold Only\n", "SCAFFOLD ONLY — NO TRAINING EXECUTED\n"],
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": ["trainer.train()\n"],
            },
        ],
        "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}},
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def test_config_file_exists() -> None:
    assert CONFIG_PATH.is_file()


def test_config_parses_successfully() -> None:
    config = load_phase3a_scaffold_config(CONFIG_PATH)
    assert config.phase == "3A"
    assert config.mode == "scaffold_only"


def test_safety_flags_are_false() -> None:
    config = load_phase3a_scaffold_config(CONFIG_PATH)
    assert config.safety["allow_training"] is False
    assert config.safety["allow_qa_generation"] is False
    assert config.safety["allow_rag_indexing"] is False
    assert config.safety["allow_dataset_publish"] is False
    assert config.safety["allow_model_download_by_default"] is False
    assert config.safety["allow_hub_push"] is False
    assert config.safety["allow_adapter_save"] is False


def test_future_human_gate_is_required() -> None:
    config = load_phase3a_scaffold_config(CONFIG_PATH)
    assert config.safety["require_future_human_gate"] is True


def test_real_legal_corpus_usage_is_disabled() -> None:
    config = load_phase3a_scaffold_config(CONFIG_PATH)
    assert config.data["use_real_legal_corpus"] is False
    assert config.data["use_corpus_candidate_manifest"] is False


def test_notebook_file_exists_and_is_valid_json() -> None:
    assert NOTEBOOK_PATH.is_file()
    payload = json.loads(NOTEBOOK_PATH.read_text(encoding="utf-8"))
    assert payload["nbformat"] == 4


def test_notebook_contains_scaffold_only_warning() -> None:
    payload = json.loads(NOTEBOOK_PATH.read_text(encoding="utf-8"))
    text = json.dumps(payload, ensure_ascii=False)
    assert "SCAFFOLD ONLY — NO TRAINING EXECUTED" in text


def test_notebook_executable_cells_do_not_contain_forbidden_patterns() -> None:
    payload = json.loads(NOTEBOOK_PATH.read_text(encoding="utf-8"))
    code = "\n".join(
        "".join(cell.get("source", []))
        for cell in payload["cells"]
        if cell.get("cell_type") == "code"
    )
    for pattern in FORBIDDEN_NOTEBOOK_PATTERNS:
        assert pattern not in code


def test_validator_passes_on_current_safe_scaffold() -> None:
    report = validate_phase3a_scaffold(
        config_path=CONFIG_PATH,
        notebook_path=NOTEBOOK_PATH,
        docs_path=DOCS_PATH,
    )
    assert report.forbidden_hits == []


def test_validator_fails_on_temporary_unsafe_config(tmp_path: Path) -> None:
    config_path = _write_text(tmp_path / "unsafe.yaml", _unsafe_config_text())
    notebook_path = _write_text(tmp_path / "safe.ipynb", NOTEBOOK_PATH.read_text(encoding="utf-8"))
    docs_path = _write_text(tmp_path / "safe.md", DOCS_PATH.read_text(encoding="utf-8"))

    try:
        validate_phase3a_scaffold(
            config_path=config_path,
            notebook_path=notebook_path,
            docs_path=docs_path,
        )
    except ValueError as exc:
        assert "allow_training" in str(exc)
    else:
        raise AssertionError("Unsafe config should fail validation.")


def test_validator_fails_on_temporary_unsafe_notebook(tmp_path: Path) -> None:
    config_path = _write_text(tmp_path / "safe.yaml", CONFIG_PATH.read_text(encoding="utf-8"))
    notebook_path = _write_text(tmp_path / "unsafe.ipynb", _unsafe_notebook_text())
    docs_path = _write_text(tmp_path / "safe.md", DOCS_PATH.read_text(encoding="utf-8"))

    try:
        validate_phase3a_scaffold(
            config_path=config_path,
            notebook_path=notebook_path,
            docs_path=docs_path,
        )
    except ValueError as exc:
        assert "trainer.train(" in str(exc)
    else:
        raise AssertionError("Unsafe notebook should fail validation.")


def test_docs_mention_blocked_items_and_future_human_gate() -> None:
    content = DOCS_PATH.read_text(encoding="utf-8").lower()
    assert "qa generation blocked" in content
    assert "fine-tuning blocked" in content
    assert "rag/vector indexing blocked" in content
    assert "dataset publishing blocked" in content
    assert "future human gate required" in content


def test_validator_cli_passes() -> None:
    result = subprocess.run(
        [sys.executable, str(VALIDATOR_PATH)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "Phase 3A scaffold validation PASS" in result.stdout
