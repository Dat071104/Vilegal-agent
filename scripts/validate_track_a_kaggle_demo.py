#!/usr/bin/env python3
"""
Validate the Track A2 Kaggle synthetic fine-tune demo scaffold.

Checks:
1. Config exists and all safety flags are set correctly.
2. Notebook exists and is valid JSON.
3. Notebook contains synthetic-only warning.
4. Notebook does NOT contain forbidden real-corpus references.
5. Notebook does NOT contain an active push_to_hub( call.
6. Docs contain required synthetic-only wording.

Usage:
    python scripts/validate_track_a_kaggle_demo.py

Does NOT import torch, transformers, peft, trl, datasets, or any GPU libraries.
Does NOT require internet.
Exits nonzero on failure.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    import yaml  # type: ignore[import-untyped]
except ImportError:
    yaml = None  # type: ignore[assignment]

ROOT = Path(__file__).resolve().parent.parent

CONFIG_PATH = ROOT / "configs" / "track_a_kaggle_finetune_demo.yaml"
NOTEBOOK_PATH = ROOT / "notebooks" / "track_a_kaggle_synthetic_finetune_demo.ipynb"
DOCS = [
    ROOT / "docs" / "TRACK_A_KAGGLE_SYNTHETIC_FINETUNE.md",
    ROOT / "docs" / "TRACK_A_BENCHMARK_PLAN.md",
    ROOT / "README.md",
]

# Required safety flag values in config
REQUIRED_CONFIG_FLAGS: dict[str, object] = {
    "use_real_legal_corpus": False,
    "use_uts_vlc_candidates": False,
    "use_corpus_candidate_manifest": False,
    "mark_as_legal_ground_truth": False,
    "approved_for_rag_index": False,
    "allow_local_training": False,
    "allow_kaggle_training": True,
    "allow_hub_push_by_default": False,
}

REQUIRED_PRIMARY_MODEL = "unsloth/Qwen2.5-7B-Instruct"
REQUIRED_MODEL_PROFILES: dict[str, dict[str, str]] = {
    "primary_kaggle": {
        "name": "unsloth/Qwen2.5-7B-Instruct",
        "purpose": "primary flagship Kaggle QLoRA portfolio demo",
        "expected_location": "Kaggle GPU",
    },
    "local_baseline": {
        "name": "Qwen/Qwen2.5-3B-Instruct",
        "purpose": "local/dev baseline because user can run 3B locally",
        "expected_location": "local machine",
    },
    "smoke_test": {
        "name": "Qwen/Qwen2.5-0.5B-Instruct",
        "purpose": "low-memory smoke test only, not portfolio target",
        "expected_location": "Kaggle or local smoke test",
    },
}

# Forbidden patterns in notebook CODE cells only (as training data references)
NOTEBOOK_FORBIDDEN_CODE_PATTERNS: list[str] = [
    "UTS_VLC",
    "artifacts/corpus_candidate_manifest",
    "artifacts/phase_2",
    "approved_for_rag_index=true",
    "approved_for_rag_index = true",
    'approved_for_rag_index": true',
    "is_legal_ground_truth=true",
    "is_legal_ground_truth = true",
    'is_legal_ground_truth": true',
]

# Pattern for active push_to_hub call (not commented out)
ACTIVE_PUSH_TO_HUB_PATTERN = "push_to_hub("

# Required wording in notebook (at least one must appear)
NOTEBOOK_SYNTHETIC_WARNINGS = [
    "SYNTHETIC DEMO ONLY",
    "synthetic demo only",
    "NOT LEGAL ADVICE",
    "not legal advice",
]

# Required wording in docs (case-insensitive — all must appear somewhere)
DOCS_REQUIRED_PHRASES = [
    "synthetic-demo only",
    "not legal advice",
    "not official legal text",
    "track b",
    "real legal corpus",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _load_yaml(path: Path) -> dict[str, object]:
    """Load a YAML file, falling back to a minimal parser if PyYAML is unavailable."""
    if yaml is not None:
        with path.open("r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
        return data if isinstance(data, dict) else {}
    # Minimal fallback: parse nested key/value mappings based on indentation.
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


def _notebook_code_source_text(nb: dict[str, object]) -> str:
    """Extract source text from notebook CODE cells only."""
    parts: list[str] = []
    cells = nb.get("cells", [])
    if not isinstance(cells, list):
        return ""
    for cell in cells:
        if not isinstance(cell, dict):
            continue
        if cell.get("cell_type") != "code":
            continue
        source = cell.get("source", [])
        if isinstance(source, list):
            parts.append("".join(source))
        elif isinstance(source, str):
            parts.append(source)
    return "\n".join(parts)


def _notebook_source_text(nb: dict[str, object]) -> str:
    """Extract all source text from all notebook cells as one string."""
    parts: list[str] = []
    cells = nb.get("cells", [])
    if not isinstance(cells, list):
        return ""
    for cell in cells:
        if not isinstance(cell, dict):
            continue
        source = cell.get("source", [])
        if isinstance(source, list):
            parts.append("".join(source))
        elif isinstance(source, str):
            parts.append(source)
    return "\n".join(parts)


def _is_active_push_to_hub(text: str) -> bool:
    """Return True if text contains an uncommented push_to_hub( call."""
    for line in text.splitlines():
        stripped = line.strip()
        if ACTIVE_PUSH_TO_HUB_PATTERN in stripped and not stripped.startswith("#"):
            return True
    return False



# Checks
# ---------------------------------------------------------------------------


def check_config(errors: list[str]) -> None:
    """Check 1-2: Config exists and has correct safety flags."""
    if not CONFIG_PATH.exists():
        errors.append(f"[CONFIG] Missing config file: {CONFIG_PATH}")
        return

    cfg = _load_yaml(CONFIG_PATH)
    safety = cfg.get("safety", {})
    if not isinstance(safety, dict):
        errors.append("[CONFIG] 'safety' section is missing or malformed.")
        return

    for flag, expected in REQUIRED_CONFIG_FLAGS.items():
        actual = safety.get(flag)
        if actual != expected:
            errors.append(
                f"[CONFIG] safety.{flag} = {actual!r}, expected {expected!r}"
            )

    model = cfg.get("model", {})
    if not isinstance(model, dict):
        errors.append("[CONFIG] 'model' section is missing or malformed.")
        return

    base_model_name = model.get("base_model_name")
    if base_model_name != REQUIRED_PRIMARY_MODEL:
        errors.append(
            "[CONFIG] model.base_model_name = "
            f"{base_model_name!r}, expected {REQUIRED_PRIMARY_MODEL!r}"
        )

    model_profiles = model.get("model_profiles", {})
    if not isinstance(model_profiles, dict):
        errors.append("[CONFIG] 'model.model_profiles' section is missing or malformed.")
    else:
        for profile_name, expected_profile in REQUIRED_MODEL_PROFILES.items():
            actual_profile = model_profiles.get(profile_name)
            if not isinstance(actual_profile, dict):
                errors.append(
                    f"[CONFIG] model.model_profiles.{profile_name} is missing or malformed."
                )
                continue
            for key, expected_value in expected_profile.items():
                actual_value = actual_profile.get(key)
                if actual_value != expected_value:
                    errors.append(
                        "[CONFIG] model.model_profiles."
                        f"{profile_name}.{key} = {actual_value!r}, "
                        f"expected {expected_value!r}"
                    )

    runtime = cfg.get("runtime", {})
    if not isinstance(runtime, dict):
        errors.append("[CONFIG] 'runtime' section is missing or malformed.")
    else:
        required_runtime = {
            "target_platform": "kaggle",
            "require_gpu": True,
            "require_internet_for_model_download": True,
            "local_training_allowed": False,
            "output_adapter_dir": "/kaggle/working/vilegal-synthetic-demo-adapter",
            "benchmark_output": "/kaggle/working/track_a_benchmark_results.json",
        }
        for k, v in required_runtime.items():
            actual = runtime.get(k)
            if actual != v:
                errors.append(f"[CONFIG] runtime.{k} = {actual!r}, expected {v!r}")

    print(f"  [CONFIG] Loaded: {CONFIG_PATH.name}")
    print(f"  [CONFIG] Safety flags checked: {len(REQUIRED_CONFIG_FLAGS)}")
    print(f"  [CONFIG] Model target checked: {REQUIRED_PRIMARY_MODEL}")



def check_notebook_exists_and_valid_json(errors: list[str]) -> dict[str, object] | None:
    """Check 3: Notebook exists and is valid JSON."""
    if not NOTEBOOK_PATH.exists():
        errors.append(f"[NOTEBOOK] Missing notebook: {NOTEBOOK_PATH}")
        return None

    try:
        with NOTEBOOK_PATH.open("r", encoding="utf-8") as fh:
            nb = json.load(fh)
    except json.JSONDecodeError as exc:
        errors.append(f"[NOTEBOOK] Invalid JSON in notebook: {exc}")
        return None

    if not isinstance(nb, dict):
        errors.append("[NOTEBOOK] Notebook root must be a JSON object.")
        return None

    print(f"  [NOTEBOOK] Loaded and valid JSON: {NOTEBOOK_PATH.name}")
    return nb


def check_notebook_warnings(
    nb: dict[str, object], nb_text: str, errors: list[str]
) -> None:
    """Check 4: Notebook contains synthetic-only warning."""
    found = any(w in nb_text for w in NOTEBOOK_SYNTHETIC_WARNINGS)
    if not found:
        errors.append(
            "[NOTEBOOK] Missing synthetic-only warning. "
            "Expected at least one of: " + ", ".join(repr(w) for w in NOTEBOOK_SYNTHETIC_WARNINGS)
        )
    else:
        print("  [NOTEBOOK] Synthetic-only warning found.")


def check_notebook_forbidden_patterns(nb: dict[str, object], errors: list[str]) -> None:
    """Check 5: Notebook CODE cells do NOT contain forbidden real-corpus training references.

    Comment lines (# ...) are excluded because explanatory comments such as
    '# Does NOT use corpus_candidate_manifest' are allowed.
    """
    code_text = _notebook_code_source_text(nb)
    # Strip comment lines before checking
    active_lines = "\n".join(
        line for line in code_text.splitlines()
        if not line.strip().startswith("#")
    )
    for pattern in NOTEBOOK_FORBIDDEN_CODE_PATTERNS:
        if pattern in active_lines:
            errors.append(
                f"[NOTEBOOK] Forbidden pattern found in active code cell line: {pattern!r}"
            )
    found_count = sum(1 for p in NOTEBOOK_FORBIDDEN_CODE_PATTERNS if p in active_lines)
    if found_count == 0:
        print(
            f"  [NOTEBOOK] No forbidden real-corpus patterns found in active code cell lines "
            f"({len(NOTEBOOK_FORBIDDEN_CODE_PATTERNS)} patterns checked)."
        )


def check_notebook_no_active_hub_push(nb: dict[str, object], errors: list[str]) -> None:
    """Check 6: Notebook does not contain an active push_to_hub( call in code cells."""
    code_text = _notebook_code_source_text(nb)
    if _is_active_push_to_hub(code_text):
        errors.append(
            "[NOTEBOOK] Active push_to_hub( call detected in code cell. "
            "Comment it out or remove it before committing."
        )
    else:
        print("  [NOTEBOOK] No active push_to_hub( call found.")


def check_notebook_unsloth_runtime(nb: dict[str, object], errors: list[str]) -> None:
    """Check that the notebook contains the Unsloth 7B QLoRA runtime requirements."""
    code_text = _notebook_code_source_text(nb)
    required_patterns = [
        "FastLanguageModel.from_pretrained",
        "load_in_4bit=True",
        'use_gradient_checkpointing="unsloth"',
        "SFTTrainer",
        "unsloth/Qwen2.5-7B-Instruct",
    ]
    for pattern in required_patterns:
        if pattern not in code_text:
            errors.append(f"[NOTEBOOK] Required Unsloth runtime pattern not found in code cells: {pattern!r}")
    
    # Check that model profiles tiers are explained
    lowered = _notebook_source_text(nb).lower()
    if "7b is the flagship kaggle target" not in lowered:
        errors.append("[NOTEBOOK] Model profile tier '7b is the flagship kaggle target' description missing.")
    if "3b is the local/dev baseline" not in lowered:
        errors.append("[NOTEBOOK] Model profile tier '3b is the local/dev baseline' description missing.")
    if "0.5b is smoke-test only" not in lowered:
        errors.append("[NOTEBOOK] Model profile tier '0.5b is smoke-test only' description missing.")


def check_docs(errors: list[str]) -> None:
    """Check 7: Docs mention required synthetic-only phrases."""
    # Combine all doc text
    combined = ""
    for doc_path in DOCS:
        if doc_path.exists():
            combined += doc_path.read_text(encoding="utf-8", errors="replace").lower()
        else:
            errors.append(f"[DOCS] Missing doc file: {doc_path.name}")

    for phrase in DOCS_REQUIRED_PHRASES:
        if phrase.lower() not in combined:
            errors.append(
                f"[DOCS] Required phrase not found in any doc: {phrase!r}"
            )

    missing_docs = [d for d in DOCS if not d.exists()]
    present_docs = [d for d in DOCS if d.exists()]
    if present_docs:
        print(
            f"  [DOCS] Checked {len(present_docs)} doc files for required wording."
        )
    if missing_docs:
        print(
            f"  [DOCS] Missing docs: {[d.name for d in missing_docs]}", file=sys.stderr
        )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    errors: list[str] = []

    print("=" * 60)
    print("Track A2 — Kaggle Synthetic Fine-Tune Demo Validator")
    print("SYNTHETIC DEMO ONLY — NOT LEGAL ADVICE")
    print("=" * 60)

    print("\n[1/4] Checking config...")
    check_config(errors)

    print("\n[2/4] Checking notebook (JSON validity)...")
    nb = check_notebook_exists_and_valid_json(errors)

    if nb is not None:
        nb_text = _notebook_source_text(nb)

        print("\n[3/4] Checking notebook content (warnings + forbidden patterns + Unsloth runtime)...")
        check_notebook_warnings(nb, nb_text, errors)
        check_notebook_forbidden_patterns(nb, errors)
        check_notebook_no_active_hub_push(nb, errors)
        check_notebook_unsloth_runtime(nb, errors)
    else:
        print("\n[3/4] Skipped notebook content checks (notebook unavailable).")
        errors.append("[NOTEBOOK] Notebook unavailable — content checks skipped.")


    print("\n[4/4] Checking docs...")
    check_docs(errors)

    print("\n" + "=" * 60)
    if errors:
        print(f"VALIDATOR RESULT: FAIL  ({len(errors)} error(s))")
        for e in errors:
            print(f"  ERROR: {e}", file=sys.stderr)
        return 1

    print("VALIDATOR RESULT: PASS")
    print("All Track A2 safety checks passed.")
    print("SYNTHETIC DEMO ONLY — NOT LEGAL ADVICE — NOT OFFICIAL LEGAL TEXT")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
