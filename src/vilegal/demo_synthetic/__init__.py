"""Synthetic demo helpers for Track A portfolio scaffolding."""

from .generator import generate_synthetic_demo_rows, write_jsonl
from .schema import DEFAULT_DISCLAIMER, SyntheticDemoRow
from .validator import validate_jsonl_file

__all__ = [
    "DEFAULT_DISCLAIMER",
    "SyntheticDemoRow",
    "generate_synthetic_demo_rows",
    "validate_jsonl_file",
    "write_jsonl",
]
