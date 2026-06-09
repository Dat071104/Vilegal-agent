"""Tests for the ViLegal data contracts."""

from datetime import date, datetime, timezone

import pytest

from vilegal.data_contracts import (
    DataSourceRecord,
    DataSourceType,
    DocumentType,
    LegalArticle,
    LegalClause,
    LegalDocument,
    SourceStatus,
)


class TestLegalClause:
    def test_valid_clause(self):
        clause = LegalClause(clause_number="1", text="Moi nguoi deu binh dang truoc phap luat.")
        assert clause.clause_number == "1"
        assert "phap luat" in clause.text

    def test_clause_text_is_stripped(self):
        clause = LegalClause(clause_number="a", text="  Van ban hop le.  ")
        assert clause.text == "Van ban hop le."

    def test_clause_blank_text_raises(self):
        with pytest.raises(Exception):
            LegalClause(clause_number="1", text="   ")

    def test_clause_provenance_fields_are_supported(self):
        retrieved_at = datetime(2026, 6, 9, 0, 0, tzinfo=timezone.utc)
        clause = LegalClause(
            clause_number="1",
            article_number=3,
            doc_id="DOC-001",
            doc_type=DocumentType.LUAT,
            number="91/2015/QH13",
            status=SourceStatus.IN_FORCE,
            text="Khoan 1 noi dung mau.",
            source_dataset="synthetic_example",
            source_id="SYNTH-CLAUSE-001",
            source_url="https://example.invalid/doc-001#clause-1",
            license="Internal Example Only",
            retrieved_at=retrieved_at,
            is_synthetic_example=True,
        )
        assert clause.source_dataset == "synthetic_example"
        assert clause.retrieved_at == retrieved_at
        assert clause.is_synthetic_example is True


class TestLegalArticle:
    def test_valid_article_no_clauses(self):
        article = LegalArticle(article_number=5, text="Quyen bat kha xam pham ve than the.")
        assert article.article_number == 5
        assert article.clauses == []

    def test_article_with_clauses(self):
        clause = LegalClause(clause_number="1", text="Khoan 1 dieu 5.")
        article = LegalArticle(article_number=5, text="Toan bo noi dung.", clauses=[clause])
        assert len(article.clauses) == 1
        assert article.clauses[0].clause_number == "1"

    def test_article_number_must_be_positive(self):
        with pytest.raises(Exception):
            LegalArticle(article_number=0, text="Noi dung.")

    def test_article_text_is_stripped(self):
        article = LegalArticle(article_number=1, text="  Noi dung co khoang trang.  ")
        assert article.text == "Noi dung co khoang trang."

    def test_article_blank_text_raises(self):
        with pytest.raises(Exception):
            LegalArticle(article_number=1, text="")

    def test_article_supports_document_metadata_and_provenance(self):
        article = LegalArticle(
            doc_id="DOC-001",
            doc_type=DocumentType.LUAT,
            number="91/2015/QH13",
            document_title="Bo luat Dan su 2015",
            status=SourceStatus.IN_FORCE,
            article_number=1,
            title="Pham vi dieu chinh",
            text="Noi dung dieu 1.",
            source_dataset="synthetic_example",
            source_id="SYNTH-ARTICLE-001",
            source_url="https://example.invalid/doc-001#article-1",
            license="Internal Example Only",
            retrieved_at=datetime(2026, 6, 9, 0, 0, tzinfo=timezone.utc),
            is_synthetic_example=True,
        )
        assert article.doc_type == DocumentType.LUAT
        assert article.number == "91/2015/QH13"
        assert article.source_id == "SYNTH-ARTICLE-001"
        assert article.is_synthetic_example is True


class TestLegalDocument:
    def _make_doc(self, **overrides):
        defaults = dict(
            doc_id="DOC-001",
            doc_type=DocumentType.LUAT,
            title="Bo luat Dan su 2015",
            number="91/2015/QH13",
            issuer="Quoc hoi",
            issued_date=date(2015, 11, 24),
            effective_date=date(2017, 1, 1),
            status=SourceStatus.IN_FORCE,
        )
        defaults.update(overrides)
        return LegalDocument(**defaults)

    def test_valid_document(self):
        doc = self._make_doc()
        assert doc.doc_id == "DOC-001"
        assert doc.doc_type == DocumentType.LUAT
        assert doc.language == "vi"

    def test_document_default_language(self):
        doc = self._make_doc()
        assert doc.language == "vi"

    def test_document_default_status_unknown(self):
        doc = LegalDocument(doc_id="D2", doc_type=DocumentType.OTHER, title="Van ban khac")
        assert doc.status == SourceStatus.UNKNOWN

    def test_document_empty_articles_by_default(self):
        doc = self._make_doc()
        assert doc.articles == []

    def test_document_with_articles(self):
        article = LegalArticle(article_number=1, text="Pham vi dieu chinh.")
        doc = self._make_doc(articles=[article])
        assert len(doc.articles) == 1

    def test_document_missing_required_fields_raises(self):
        with pytest.raises(Exception):
            LegalDocument(doc_id="D3", doc_type=DocumentType.LUAT)

    def test_document_all_doc_types(self):
        for doc_type in DocumentType:
            doc = LegalDocument(doc_id="DX", doc_type=doc_type, title="Tieu de")
            assert doc.doc_type == doc_type

    def test_document_provenance_fields_are_supported(self):
        retrieved_at = datetime(2026, 6, 9, 0, 0, tzinfo=timezone.utc)
        doc = self._make_doc(
            source_dataset="undertheseanlp/UTS_VLC",
            source_id="91/2015/QH13",
            source_url="https://huggingface.co/datasets/undertheseanlp/UTS_VLC",
            license="MIT",
            retrieved_at=retrieved_at,
        )
        assert doc.source_dataset == "undertheseanlp/UTS_VLC"
        assert doc.license == "MIT"
        assert doc.retrieved_at == retrieved_at


class TestDataSourceRecord:
    def _make_record(self, **overrides):
        defaults = dict(
            source_id="S3_UTS_VLC",
            name="undertheseanlp/UTS_VLC",
            source_type=DataSourceType.HUGGINGFACE,
            source_dataset="undertheseanlp/UTS_VLC",
            url="https://huggingface.co/datasets/undertheseanlp/UTS_VLC",
            license="MIT",
            license_confirmed=True,
            attribution_required=False,
            retrieved_at=datetime(2026, 6, 9, 0, 0, tzinfo=timezone.utc),
            risk_level="medium",
            approved_for_phase2=False,
        )
        defaults.update(overrides)
        return DataSourceRecord(**defaults)

    def test_valid_record(self):
        rec = self._make_record()
        assert rec.source_id == "S3_UTS_VLC"
        assert rec.source_type == DataSourceType.HUGGINGFACE
        assert rec.license_confirmed is True
        assert rec.risk_level == "MEDIUM"

    def test_record_can_require_attribution(self):
        rec = self._make_record(
            source_id="S2_VLD",
            name="th1nhng0/vietnamese-legal-documents",
            source_dataset="th1nhng0/vietnamese-legal-documents",
            license="CC-BY-4.0",
            attribution_required=True,
            attribution_note="Keep dataset card attribution in docs and downstream artifacts.",
        )
        assert rec.attribution_required is True
        assert "attribution" in rec.attribution_note.lower()

    def test_record_default_risk_unknown(self):
        rec = DataSourceRecord(
            source_id="SX",
            name="Unknown Source",
            source_type=DataSourceType.MANUAL,
        )
        assert rec.risk_level == "UNKNOWN"

    def test_record_estimated_doc_count_nonnegative(self):
        with pytest.raises(Exception):
            self._make_record(estimated_doc_count=-1)

    def test_record_estimated_doc_count_zero_ok(self):
        rec = self._make_record(estimated_doc_count=0)
        assert rec.estimated_doc_count == 0

    def test_all_source_types(self):
        for source_type in DataSourceType:
            rec = DataSourceRecord(source_id="T", name="Test", source_type=source_type)
            assert rec.source_type == source_type
