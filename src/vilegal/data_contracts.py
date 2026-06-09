"""
ViLegal Agent data contracts.

These Pydantic models define the minimum metadata and provenance required for
sample-only ingestion of Vietnamese legal records during the audit phases.
"""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class DocumentType(str, Enum):
    """Top-level document classification."""

    HIEN_PHAP = "hien_phap"
    BO_LUAT = "bo_luat"
    LUAT = "luat"
    NGHI_DINH = "nghi_dinh"
    THONG_TU = "thong_tu"
    QUYET_DINH = "quyet_dinh"
    NGHI_QUYET = "nghi_quyet"
    OTHER = "other"


class SourceStatus(str, Enum):
    """Effective status of a legal document or fragment."""

    IN_FORCE = "in_force"
    EXPIRED = "expired"
    AMENDED = "amended"
    UNKNOWN = "unknown"


class DataSourceType(str, Enum):
    """Origin class for an audited source."""

    HUGGINGFACE = "huggingface"
    VBPL_API = "vbpl_api"
    VBPL_SCRAPE = "vbpl_scrape"
    MANUAL = "manual"
    SYNTHETIC = "synthetic"


class ProvenanceMixin(BaseModel):
    """Reusable provenance fields for document, article, and clause records."""

    source_dataset: Optional[str] = Field(
        default=None,
        description="Dataset or collection name that produced this record.",
    )
    source_id: Optional[str] = Field(
        default=None,
        description="Stable source-side identifier for the record.",
    )
    source_url: Optional[str] = Field(
        default=None,
        description="Direct source URL when available.",
    )
    license: Optional[str] = Field(
        default=None,
        description="License label attached to the source record or dataset.",
    )
    retrieved_at: Optional[datetime] = Field(
        default=None,
        description="Timestamp when the source record or source card was retrieved.",
    )
    is_synthetic_example: bool = Field(
        default=False,
        description="True only for local synthetic/example records.",
    )

    @field_validator("source_dataset", "source_id", "source_url", "license")
    @classmethod
    def normalize_optional_text(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        value = value.strip()
        return value or None


class LegalClause(ProvenanceMixin):
    """A single clause nested under a legal article."""

    clause_number: str = Field(
        ...,
        description="Clause identifier, for example '1' or 'a'.",
        min_length=1,
    )
    article_number: Optional[int] = Field(
        default=None,
        description="Parent article number when the clause is stored standalone.",
        ge=1,
    )
    doc_id: Optional[str] = Field(
        default=None,
        description="Parent document identifier when the clause is stored standalone.",
    )
    doc_type: Optional[DocumentType] = Field(
        default=None,
        description="Parent document type when the clause is stored standalone.",
    )
    number: Optional[str] = Field(
        default=None,
        description="Parent document number when the clause is stored standalone.",
    )
    status: SourceStatus = Field(
        default=SourceStatus.UNKNOWN,
        description="Parent document effective status.",
    )
    text: str = Field(
        ...,
        description="Full clause text in Vietnamese.",
        min_length=1,
    )
    notes: Optional[str] = Field(
        default=None,
        description="Optional editorial or amendment notes.",
    )

    @field_validator("text")
    @classmethod
    def text_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Clause text must not be blank or whitespace only.")
        return value


class LegalArticle(ProvenanceMixin):
    """A legal article with enough metadata for standalone sample ingestion."""

    doc_id: Optional[str] = Field(
        default=None,
        description="Parent document identifier.",
    )
    doc_type: Optional[DocumentType] = Field(
        default=None,
        description="Parent document type.",
    )
    number: Optional[str] = Field(
        default=None,
        description="Parent document number.",
    )
    document_title: Optional[str] = Field(
        default=None,
        description="Parent document title when the article is stored standalone.",
    )
    status: SourceStatus = Field(
        default=SourceStatus.UNKNOWN,
        description="Parent document effective status.",
    )
    article_number: int = Field(
        ...,
        description="Article number.",
        ge=1,
    )
    title: Optional[str] = Field(
        default=None,
        description="Article title or heading.",
    )
    text: str = Field(
        ...,
        description="Full article text.",
        min_length=1,
    )
    clauses: list[LegalClause] = Field(
        default_factory=list,
        description="Parsed clauses nested under the article.",
    )
    language: str = Field(
        default="vi",
        description="ISO 639-1 language code.",
    )

    @field_validator("text")
    @classmethod
    def article_text_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Article text must not be blank or whitespace only.")
        return value


class LegalDocument(ProvenanceMixin):
    """A full Vietnamese legal document."""

    doc_id: str = Field(
        ...,
        description="Unique document identifier.",
        min_length=1,
    )
    doc_type: DocumentType = Field(
        ...,
        description="Top-level document type.",
    )
    number: Optional[str] = Field(
        default=None,
        description="Official document number.",
    )
    title: str = Field(
        ...,
        description="Official Vietnamese document title.",
        min_length=1,
    )
    issuer: Optional[str] = Field(
        default=None,
        description="Issuing authority.",
    )
    issued_date: Optional[date] = Field(
        default=None,
        description="Document issue date.",
    )
    effective_date: Optional[date] = Field(
        default=None,
        description="Document effective date.",
    )
    status: SourceStatus = Field(
        default=SourceStatus.UNKNOWN,
        description="Current effective status.",
    )
    articles: list[LegalArticle] = Field(
        default_factory=list,
        description="Parsed document articles.",
    )
    raw_text: Optional[str] = Field(
        default=None,
        description="Unparsed full text retained as fallback.",
    )
    language: str = Field(
        default="vi",
        description="ISO 639-1 language code.",
    )


class DataSourceRecord(BaseModel):
    """Metadata about a source reviewed during the audit."""

    source_id: str = Field(
        ...,
        description="Short unique source identifier, for example 'S3_UTS_VLC'.",
    )
    name: str = Field(
        ...,
        description="Human-readable source name.",
    )
    source_type: DataSourceType = Field(
        ...,
        description="Source category.",
    )
    source_dataset: Optional[str] = Field(
        default=None,
        description="Dataset handle or source collection name.",
    )
    url: Optional[str] = Field(
        default=None,
        description="Dataset card URL, API endpoint, or source landing page.",
    )
    license: Optional[str] = Field(
        default=None,
        description="License identifier stated by the source.",
    )
    license_confirmed: bool = Field(
        default=False,
        description="True when the license field was re-checked manually.",
    )
    attribution_required: bool = Field(
        default=False,
        description="True when downstream use requires visible attribution.",
    )
    attribution_note: Optional[str] = Field(
        default=None,
        description="Short attribution instruction for downstream use.",
    )
    retrieved_at: Optional[datetime] = Field(
        default=None,
        description="Timestamp when the source card or policy page was checked.",
    )
    estimated_doc_count: Optional[int] = Field(
        default=None,
        description="Estimated number of documents or records.",
        ge=0,
    )
    risk_level: str = Field(
        default="UNKNOWN",
        description="LOW, MEDIUM, HIGH, or UNKNOWN.",
    )
    notes: Optional[str] = Field(
        default=None,
        description="Audit notes, caveats, or next actions.",
    )
    approved_for_phase2: bool = Field(
        default=False,
        description="True only when sample-only or bulk ingestion is approved.",
    )

    @field_validator("risk_level")
    @classmethod
    def normalize_risk_level(cls, value: str) -> str:
        value = value.strip().upper()
        return value or "UNKNOWN"
