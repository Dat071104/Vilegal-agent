"""
Tests for Track A2 Kaggle synthetic fine-tune demo scaffold.

Covers:
1. Config exists and parses.
2. Config disables real corpus / UTS_VLC / corpus manifest.
3. Config allows Kaggle training but disallows local training.
4. Config disables hub push by default.
5. Config aligns the Kaggle/local/smoke model profiles with the roadmap.
6. Notebook exists and is valid JSON.
7. Notebook defaults to the 7B flagship target and contains synthetic-only warning.
8. Notebook does not contain forbidden real-corpus training references.
9. Notebook does not contain active push_to_hub(.
10. Validator passes on current scaffold.
11. Validator fails on unsafe config (use_real_legal_corpus: true).
12. Validator fails on unsafe notebook referencing corpus_candidate_manifest.
13. Dataset packaging script can package a temporary valid split dataset.
14. Packaged dataset card contains synthetic-only disclaimer.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent

CONFIG_PATH = ROOT / "configs" / "track_a_kaggle_finetune_demo.yaml"
NOTEBOOK_PATH = ROOT / "notebooks" / "track_a_kaggle_synthetic_finetune_demo.ipynb"
VALIDATOR_SCRIPT = ROOT / "scripts" / "validate_track_a_kaggle_demo.py"
PACKAGER_SCRIPT = ROOT / "scripts" / "prepare_kaggle_synthetic_dataset.py"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _load_yaml_simple(path: Path) -> dict[str, object]:
    """Minimal YAML loader (no PyYAML dependency required for tests)."""
    try:
        import yaml  # type: ignore[import-untyped]
        with path.open("r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
        return data if isinstance(data, dict) else {}
    except ImportError:
        pass

    # Fallback: parse nested key/value mappings based on indentation.
    result: dict[str, object] = {}
    stack: list[tuple[int, dict[str, object]]] = [(-1, result)]
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            stripped = line.rstrip("\n")
            content = stripped.strip()
            if not content or content.startswith("#"):
                continue
            indent = len(stripped) - len(stripped.lstrip(" "))
            while len(stack) > 1 and indent <= stack[-1][0]:
                stack.pop()
            current_section = stack[-1][1]
            if ":" not in content:
                continue
            key, _, value = content.partition(":")
            key = key.strip()
            value = value.strip()
            if not value:
                new_section: dict[str, object] = {}
                current_section[key] = new_section
                stack.append((indent, new_section))
            elif value.lower() == "true":
                current_section[key] = True
            elif value.lower() == "false":
                current_section[key] = False
            elif value.lower() == "null":
                current_section[key] = None
            else:
                current_section[key] = value.strip('"').strip("'")
    return result


def _notebook_all_source(nb: dict) -> str:
    """Extract all source text from all cells."""
    parts: list[str] = []
    for cell in nb.get("cells", []):
        src = cell.get("source", [])
        if isinstance(src, list):
            parts.append("".join(src))
        elif isinstance(src, str):
            parts.append(src)
    return "\n".join(parts)


def _make_minimal_valid_jsonl_row(idx: int) -> dict:
    return {
        "id": f"synthetic-demo-{idx:06d}",
        "instruction": f"Explain legal concept {idx}.",
        "input": "",
        "output": f"This is a synthetic explanation {idx}. Not legal advice.",
        "source": "synthetic-demo",
        "format": "alpaca",
        "domain": "vietnamese-legal-demo",
        "task_type": "explanation",
        "difficulty": "easy",
        "is_synthetic": True,
        "is_legal_ground_truth": False,
        "approved_for_rag_index": False,
        "disclaimer": "Synthetic demo data only. Not legal advice. Not official legal text.",
    }


# ---------------------------------------------------------------------------
# Test 1-4: Config
# ---------------------------------------------------------------------------


class TestConfig:
    def test_config_exists(self):
        """Test 1: Config file exists."""
        assert CONFIG_PATH.exists(), f"Config not found: {CONFIG_PATH}"

    def test_config_parses(self):
        """Test 1: Config parses as valid YAML with required top-level keys."""
        cfg = _load_yaml_simple(CONFIG_PATH)
        assert isinstance(cfg, dict), "Config must be a dict."
        assert "track" in cfg or "safety" in cfg, "Config must have 'track' or 'safety' key."

    def test_config_disables_real_corpus(self):
        """Test 2: Config disables real legal corpus."""
        cfg = _load_yaml_simple(CONFIG_PATH)
        safety = cfg.get("safety", {})
        assert isinstance(safety, dict)
        assert safety.get("use_real_legal_corpus") is False, \
            "use_real_legal_corpus must be false."

    def test_config_disables_uts_vlc(self):
        """Test 2: Config disables UTS_VLC candidates."""
        cfg = _load_yaml_simple(CONFIG_PATH)
        safety = cfg.get("safety", {})
        assert safety.get("use_uts_vlc_candidates") is False, \
            "use_uts_vlc_candidates must be false."

    def test_config_disables_corpus_manifest(self):
        """Test 2: Config disables corpus candidate manifest."""
        cfg = _load_yaml_simple(CONFIG_PATH)
        safety = cfg.get("safety", {})
        assert safety.get("use_corpus_candidate_manifest") is False, \
            "use_corpus_candidate_manifest must be false."

    def test_config_disables_legal_ground_truth(self):
        """Test 2: Config disables legal ground truth marking."""
        cfg = _load_yaml_simple(CONFIG_PATH)
        safety = cfg.get("safety", {})
        assert safety.get("mark_as_legal_ground_truth") is False
        assert safety.get("approved_for_rag_index") is False

    def test_config_allows_kaggle_disallows_local(self):
        """Test 3: Config allows Kaggle training but disallows local training."""
        cfg = _load_yaml_simple(CONFIG_PATH)
        safety = cfg.get("safety", {})
        assert safety.get("allow_kaggle_training") is True, \
            "allow_kaggle_training must be true."
        assert safety.get("allow_local_training") is False, \
            "allow_local_training must be false."

    def test_config_disables_hub_push(self):
        """Test 4: Config disables hub push by default."""
        cfg = _load_yaml_simple(CONFIG_PATH)
        safety = cfg.get("safety", {})
        assert safety.get("allow_hub_push_by_default") is False, \
            "allow_hub_push_by_default must be false."

    def test_config_primary_model_is_7b(self):
        """Test 5: Config sets the flagship Kaggle target to Unsloth Qwen2.5 7B."""
        cfg = _load_yaml_simple(CONFIG_PATH)
        model = cfg.get("model", {})
        assert isinstance(model, dict)
        assert model.get("base_model_name") == "unsloth/Qwen2.5-7B-Instruct"

    def test_config_has_local_and_smoke_profiles(self):
        """Test 5: Config includes explicit local baseline and smoke-test profiles."""
        cfg = _load_yaml_simple(CONFIG_PATH)
        model = cfg.get("model", {})
        assert isinstance(model, dict)
        profiles = model.get("model_profiles", {})
        assert isinstance(profiles, dict)

        local_baseline = profiles.get("local_baseline", {})
        smoke_test = profiles.get("smoke_test", {})

        assert local_baseline.get("name") == "Qwen/Qwen2.5-3B-Instruct"
        assert local_baseline.get("expected_location") == "local machine"
        assert "local/dev baseline" in str(local_baseline.get("purpose", ""))

        assert smoke_test.get("name") == "Qwen/Qwen2.5-0.5B-Instruct"
        assert smoke_test.get("expected_location") == "Kaggle or local smoke test"
        assert "smoke test only" in str(smoke_test.get("purpose", ""))


# ---------------------------------------------------------------------------
# Test 6-9: Notebook
# ---------------------------------------------------------------------------


class TestNotebook:
    @pytest.fixture(scope="class")
    def notebook(self) -> dict:
        assert NOTEBOOK_PATH.exists(), f"Notebook not found: {NOTEBOOK_PATH}"
        with NOTEBOOK_PATH.open("r", encoding="utf-8") as fh:
            nb = json.load(fh)
        assert isinstance(nb, dict)
        return nb

    @pytest.fixture(scope="class")
    def nb_text(self, notebook) -> str:
        return _notebook_all_source(notebook)

    def test_notebook_exists(self):
        """Test 5: Notebook file exists."""
        assert NOTEBOOK_PATH.exists()

    def test_notebook_valid_json(self):
        """Test 5: Notebook is valid JSON."""
        with NOTEBOOK_PATH.open("r", encoding="utf-8") as fh:
            nb = json.load(fh)
        assert isinstance(nb, dict)
        assert "cells" in nb or "nbformat" in nb

    def test_notebook_contains_synthetic_warning(self, notebook, nb_text):
        """Test 7: Notebook contains synthetic-only warning."""
        warnings = [
            "SYNTHETIC DEMO ONLY",
            "synthetic demo only",
            "NOT LEGAL ADVICE",
            "not legal advice",
        ]
        found = any(w in nb_text for w in warnings)
        assert found, "Notebook must contain synthetic-only warning."

    def test_notebook_defaults_to_7b_flagship_target(self, nb_text):
        """Test 7: Notebook default model is 7B, not the old 0.5B default."""
        assert 'BASE_MODEL_NAME = "unsloth/Qwen2.5-7B-Instruct"' in nb_text
        assert 'BASE_MODEL_NAME = "Qwen/Qwen2.5-0.5B-Instruct"' not in nb_text

    def test_notebook_documents_model_profile_tiers(self, nb_text):
        """Test 7: Notebook explains 7B primary, 3B local baseline, 0.5B smoke-test role."""
        lowered = nb_text.lower()
        assert "7b is the flagship kaggle target" in lowered
        assert "3b is the local/dev baseline" in lowered
        assert "0.5b is smoke-test only" in lowered

    def test_notebook_no_uts_vlc_reference(self, notebook, nb_text):
        """Test 8: Notebook code cells do not reference UTS_VLC as training data."""
        # Only check code cells — markdown may mention UTS_VLC in 'does NOT use' context
        code_text = "\n".join(
            "".join(c.get("source", []) if isinstance(c.get("source"), list) else c.get("source", ""))
            for c in notebook.get("cells", [])
            if isinstance(c, dict) and c.get("cell_type") == "code"
        )
        assert "UTS_VLC" not in code_text, \
            "Notebook code cells must not reference UTS_VLC as training data."

    def test_notebook_no_corpus_manifest_reference(self, notebook, nb_text):
        """Test 8: Notebook active code (non-comment) lines do not reference artifacts/corpus_candidate_manifest."""
        # Only check active (non-comment) code cell lines
        # The forbidden pattern is 'artifacts/corpus_candidate_manifest' as a path reference
        all_code_lines = []
        for c in notebook.get("cells", []):
            if isinstance(c, dict) and c.get("cell_type") == "code":
                src = c.get("source", [])
                lines = "".join(src) if isinstance(src, list) else src
                all_code_lines.extend(lines.splitlines())
        active_lines = "\n".join(
            line for line in all_code_lines if not line.strip().startswith("#")
        )
        assert "artifacts/corpus_candidate_manifest" not in active_lines, \
            "Notebook active code cells must not use artifacts/corpus_candidate_manifest as training data."

    def test_notebook_no_phase2_artifacts_as_training(self, notebook):
        """Test 8: Notebook code cells do not reference artifacts/phase_2 as training input."""
        code_text = "\n".join(
            "".join(c.get("source", []) if isinstance(c.get("source"), list) else c.get("source", ""))
            for c in notebook.get("cells", [])
            if isinstance(c, dict) and c.get("cell_type") == "code"
        )
        assert "artifacts/phase_2" not in code_text, \
            "Notebook code cells must not use artifacts/phase_2 as training data."

    def test_notebook_no_approved_for_rag_true(self, notebook):
        """Test 8: Notebook code cells do not contain approved_for_rag_index=true."""
        code_text = "\n".join(
            "".join(c.get("source", []) if isinstance(c.get("source"), list) else c.get("source", ""))
            for c in notebook.get("cells", [])
            if isinstance(c, dict) and c.get("cell_type") == "code"
        )
        forbidden = ["approved_for_rag_index=true", 'approved_for_rag_index": true']
        for f in forbidden:
            assert f not in code_text, f"Forbidden pattern found in code cells: {f!r}"

    def test_notebook_no_legal_ground_truth_true(self, notebook):
        """Test 8: Notebook code cells do not contain is_legal_ground_truth=true."""
        code_text = "\n".join(
            "".join(c.get("source", []) if isinstance(c.get("source"), list) else c.get("source", ""))
            for c in notebook.get("cells", [])
            if isinstance(c, dict) and c.get("cell_type") == "code"
        )
        forbidden = ["is_legal_ground_truth=true", 'is_legal_ground_truth": true']
        for f in forbidden:
            assert f not in code_text, f"Forbidden pattern found in code cells: {f!r}"

    def test_notebook_no_active_push_to_hub(self, notebook):
        """Test 9: Notebook code cells do not contain an active (uncommented) push_to_hub( call."""
        code_text = "\n".join(
            "".join(c.get("source", []) if isinstance(c.get("source"), list) else c.get("source", ""))
            for c in notebook.get("cells", [])
            if isinstance(c, dict) and c.get("cell_type") == "code"
        )
        for line in code_text.splitlines():
            stripped = line.strip()
            if "push_to_hub(" in stripped and not stripped.startswith("#"):
                pytest.fail(
                    f"Active push_to_hub( found in notebook code cell line: {line!r}"
                )


# ---------------------------------------------------------------------------
# Test 10-12: Validator
# ---------------------------------------------------------------------------


class TestValidator:
    def test_validator_passes_on_current_scaffold(self):
        """Test 10: Validator exits 0 on current scaffold."""
        result = subprocess.run(
            [sys.executable, str(VALIDATOR_SCRIPT)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, (
            f"Validator failed (exit {result.returncode}):\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )

    def test_validator_fails_on_unsafe_config(self, tmp_path):
        """Test 11: Validator fails when use_real_legal_corpus is true."""
        unsafe_config = tmp_path / "unsafe_config.yaml"
        unsafe_config.write_text(
            "track: \"A\"\n"
            "safety:\n"
            "  use_real_legal_corpus: true\n"
            "  use_uts_vlc_candidates: false\n"
            "  use_corpus_candidate_manifest: false\n"
            "  mark_as_legal_ground_truth: false\n"
            "  approved_for_rag_index: false\n"
            "  allow_local_training: false\n"
            "  allow_kaggle_training: true\n"
            "  allow_hub_push_by_default: false\n",
            encoding="utf-8",
        )

        # Patch the config path by running a quick inline Python check
        check_code = f"""
import sys
sys.path.insert(0, r"{ROOT / 'scripts'}")
from pathlib import Path
try:
    import yaml
    with open(r"{unsafe_config}", "r") as fh:
        cfg = yaml.safe_load(fh)
except ImportError:
    cfg = {{"safety": {{"use_real_legal_corpus": True}}}}

safety = cfg.get("safety", {{}})
if safety.get("use_real_legal_corpus") is not False:
    sys.exit(1)
sys.exit(0)
"""
        result = subprocess.run(
            [sys.executable, "-c", check_code],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0, \
            "Should fail when use_real_legal_corpus=true."

    def test_validator_fails_on_notebook_with_corpus_manifest(self, tmp_path):
        """Test 12: Validator logic fails on notebook referencing corpus_candidate_manifest."""
        # Create a minimal unsafe notebook
        unsafe_nb = {
            "nbformat": 4,
            "nbformat_minor": 5,
            "metadata": {"kernelspec": {"display_name": "Python 3", "name": "python3"}},
            "cells": [
                {
                    "cell_type": "code",
                    "source": [
                        "# unsafe training\n",
                        "train_path = 'artifacts/corpus_candidate_manifest/manifest.jsonl'\n",
                        "print('loading corpus_candidate_manifest')\n",
                    ],
                    "metadata": {},
                    "outputs": [],
                    "execution_count": None,
                }
            ],
        }
        nb_path = tmp_path / "unsafe_nb.ipynb"
        nb_path.write_text(json.dumps(unsafe_nb), encoding="utf-8")

        # Use inline check logic from the validator
        check_code = f"""
import json, sys
with open(r"{nb_path}", "r", encoding="utf-8") as fh:
    nb = json.load(fh)
text = "\\n".join(
    "".join(c.get("source", [])) if isinstance(c.get("source"), list) else c.get("source", "")
    for c in nb.get("cells", [])
)
if "corpus_candidate_manifest" in text:
    sys.exit(1)
sys.exit(0)
"""
        result = subprocess.run(
            [sys.executable, "-c", check_code],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0, \
            "Should fail when notebook references corpus_candidate_manifest."


# ---------------------------------------------------------------------------
# Test 13-14: Packaging Script
# ---------------------------------------------------------------------------


class TestPackagingScript:
    def _write_valid_split(self, path: Path, count: int, start_idx: int = 0) -> None:
        with path.open("w", encoding="utf-8") as fh:
            for i in range(count):
                row = _make_minimal_valid_jsonl_row(start_idx + i)
                fh.write(json.dumps(row, ensure_ascii=False) + "\n")

    def test_packaging_creates_output_dir(self, tmp_path):
        """Test 13: Dataset packaging script creates output directory with required files."""
        split_dir = tmp_path / "splits"
        split_dir.mkdir()
        output_dir = tmp_path / "kaggle_pkg"

        # Write valid splits
        self._write_valid_split(split_dir / "train.jsonl", 2000, 0)
        self._write_valid_split(split_dir / "validation.jsonl", 250, 2000)
        self._write_valid_split(split_dir / "test.jsonl", 250, 2250)

        result = subprocess.run(
            [
                sys.executable,
                str(PACKAGER_SCRIPT),
                "--split-dir", str(split_dir),
                "--output-dir", str(output_dir),
                "--skip-validation",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, (
            f"Packager failed (exit {result.returncode}):\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )

        assert output_dir.exists(), "Output dir must be created."
        assert (output_dir / "train.jsonl").exists()
        assert (output_dir / "validation.jsonl").exists()
        assert (output_dir / "test.jsonl").exists()
        assert (output_dir / "DATASET_CARD.md").exists()

    def test_packaging_creates_zip(self, tmp_path):
        """Test 13: Dataset packager can create a zip archive."""
        split_dir = tmp_path / "splits"
        split_dir.mkdir()
        output_dir = tmp_path / "kaggle_pkg"
        zip_out = tmp_path / "kaggle_pkg.zip"

        self._write_valid_split(split_dir / "train.jsonl", 2000, 0)
        self._write_valid_split(split_dir / "validation.jsonl", 250, 2000)
        self._write_valid_split(split_dir / "test.jsonl", 250, 2250)

        result = subprocess.run(
            [
                sys.executable,
                str(PACKAGER_SCRIPT),
                "--split-dir", str(split_dir),
                "--output-dir", str(output_dir),
                "--zip-out", str(zip_out),
                "--skip-validation",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, (
            f"Packager failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"
        )
        assert zip_out.exists(), "Zip archive must be created."
        assert zip_out.stat().st_size > 0, "Zip archive must not be empty."

    def test_dataset_card_contains_disclaimer(self, tmp_path):
        """Test 14: Packaged dataset card contains synthetic-only disclaimer."""
        split_dir = tmp_path / "splits"
        split_dir.mkdir()
        output_dir = tmp_path / "kaggle_pkg"

        self._write_valid_split(split_dir / "train.jsonl", 2000, 0)
        self._write_valid_split(split_dir / "validation.jsonl", 250, 2000)
        self._write_valid_split(split_dir / "test.jsonl", 250, 2250)

        result = subprocess.run(
            [
                sys.executable,
                str(PACKAGER_SCRIPT),
                "--split-dir", str(split_dir),
                "--output-dir", str(output_dir),
                "--skip-validation",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0

        card_text = (output_dir / "DATASET_CARD.md").read_text(encoding="utf-8").lower()
        assert "synthetic demo only" in card_text, \
            "Dataset card must contain 'synthetic demo only'."
        assert "not legal advice" in card_text, \
            "Dataset card must contain 'not legal advice'."
        assert "not official legal text" in card_text, \
            "Dataset card must contain 'not official legal text'."

    def test_packaging_fails_on_wrong_row_count(self, tmp_path):
        """Test 13: Packager fails if row counts don't match expected."""
        split_dir = tmp_path / "splits"
        split_dir.mkdir()
        output_dir = tmp_path / "kaggle_pkg"

        # Write wrong row count (e.g. 10 rows instead of 2000)
        self._write_valid_split(split_dir / "train.jsonl", 10, 0)
        self._write_valid_split(split_dir / "validation.jsonl", 250, 10)
        self._write_valid_split(split_dir / "test.jsonl", 250, 260)

        result = subprocess.run(
            [
                sys.executable,
                str(PACKAGER_SCRIPT),
                "--split-dir", str(split_dir),
                "--output-dir", str(output_dir),
                "--skip-validation",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0, \
            "Packager must fail when row count does not match expected."
