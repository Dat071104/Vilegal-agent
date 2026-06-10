from __future__ import annotations

from dataclasses import asdict, dataclass

DEFAULT_DISCLAIMER = "Synthetic demo data only. Not legal advice. Not official legal text."
DEFAULT_SOURCE = "synthetic-demo"
DEFAULT_FORMAT = "alpaca"
DEFAULT_DOMAIN = "vietnamese-legal-demo"

ALLOWED_TASK_TYPES = (
    "classification",
    "explanation",
    "retrieval_style_qa",
    "drafting_demo",
)

ALLOWED_DIFFICULTIES = ("easy", "medium", "hard")

REQUIRED_FIELDS = (
    "id",
    "instruction",
    "input",
    "output",
    "source",
    "format",
    "domain",
    "task_type",
    "difficulty",
    "is_synthetic",
    "is_legal_ground_truth",
    "approved_for_rag_index",
    "disclaimer",
)


@dataclass(frozen=True)
class SyntheticDemoRow:
    id: str
    instruction: str
    input: str
    output: str
    source: str = DEFAULT_SOURCE
    format: str = DEFAULT_FORMAT
    domain: str = DEFAULT_DOMAIN
    task_type: str = "explanation"
    difficulty: str = "easy"
    is_synthetic: bool = True
    is_legal_ground_truth: bool = False
    approved_for_rag_index: bool = False
    disclaimer: str = DEFAULT_DISCLAIMER

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def row_id_from_index(index: int) -> str:
    return f"synthetic-demo-{index:06d}"
