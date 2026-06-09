from __future__ import annotations

from scripts.audit_ingested_content import (
    count_article_markers,
    cross_source_summary,
    first_conversation_turn,
    has_citation_signal,
    summarize_duyet,
    summarize_uts,
)


def test_has_citation_signal_detects_legal_references():
    text = "Can cu Dieu 12 Luat Dat dai va Khoan 3 Dieu 5 Nghi dinh 12/2024/ND-CP."
    assert has_citation_signal(text) is True


def test_first_conversation_turn_returns_requested_role():
    raw_metadata = {
        "conversations": [
            {"role": "system", "content": "Huong dan."},
            {"role": "user", "content": "Cau hoi."},
            {"role": "assistant", "content": "Cau tra loi."},
        ]
    }
    assert first_conversation_turn(raw_metadata, "user") == "Cau hoi."
    assert first_conversation_turn(raw_metadata, "assistant") == "Cau tra loi."


def test_count_article_markers_counts_multiline_article_headings():
    text = "Mo dau\nDieu 1. Pham vi dieu chinh\nNoi dung\nDieu 2. Giai thich tu ngu"
    assert count_article_markers(text) == 2


def test_summarize_uts_flags_document_level_rows_with_article_markers():
    records = [
        {
            "document_type": "other",
            "document_number": "",
            "title": "Bo luat mau",
            "source_id": "91/2015/QH13",
            "source_url": "https://example.invalid/1",
            "article_number": None,
            "clause_number": None,
            "text": "Dieu 1. Mot\nNoi dung\nDieu 2. Hai",
        }
    ]
    manifest = {"license": "MIT", "attribution_required": False}
    summary = summarize_uts(records, manifest)
    assert summary["article_parsing_possible"] is True
    assert summary["records_with_multiple_article_markers"] == 1


def test_summarize_duyet_confirms_user_text_and_assistant_retention():
    records = [
        {
            "document_type": "other",
            "document_number": "",
            "title": "",
            "source_id": "123",
            "source_url": "https://example.invalid/2",
            "article_number": None,
            "clause_number": None,
            "text": "Giai thich Dieu 5.",
            "raw_metadata": {
                "qa_type": "explain_simple",
                "conversations": [
                    {"role": "system", "content": "Huong dan."},
                    {"role": "user", "content": "Giai thich Dieu 5."},
                    {"role": "assistant", "content": "Theo Dieu 5 Luat X, noi dung la ..."},
                ],
            },
        }
    ]
    manifest = {"license": "CC-BY-4.0", "attribution_required": True}
    summary = summarize_duyet(records, manifest)
    assert summary["normalized_text_matches_user_turn_count"] == 1
    assert summary["assistant_answers_in_raw_metadata_count"] == 1
    assert summary["assistant_answers_with_citation_signal_count"] == 1


def test_cross_source_summary_checks_role_separation_and_provenance():
    uts_records = [
        {
            "record_id": "a1",
            "source_dataset": "undertheseanlp/UTS_VLC",
            "source_url": "https://example.invalid/uts",
            "source_id": "91/2015/QH13",
            "license": "MIT",
            "retrieved_at": "2026-06-09T00:00:00Z",
            "text": "Dieu 1.",
            "raw_metadata": {},
        }
    ]
    duyet_records = [
        {
            "record_id": "b1",
            "source_dataset": "duyet/vietnamese-legal-instruct",
            "source_url": "https://example.invalid/duyet",
            "source_id": "123",
            "license": "CC-BY-4.0",
            "retrieved_at": "2026-06-09T00:00:00Z",
            "text": "Hoi ve Dieu 1.",
            "raw_metadata": {
                "conversations": [
                    {"role": "user", "content": "Hoi ve Dieu 1."},
                    {"role": "assistant", "content": "Tra loi."},
                ]
            },
        }
    ]
    uts_manifest = {"license": "MIT", "attribution_note": "MIT note"}
    duyet_manifest = {
        "license": "CC-BY-4.0",
        "attribution_note": "CC note",
        "attribution_required": True,
    }
    summary = cross_source_summary(uts_records, duyet_records, uts_manifest, duyet_manifest)
    assert summary["source_role_separation"]["uts_vlc_corpus_candidate_confirmed"] is True
    assert summary["source_role_separation"]["duyet_text_is_user_query_only"] is True
    assert summary["provenance_completeness"]["uts_vlc"]["all_records_complete"] is True
    assert summary["duplicate_source_ids_across_sources"] == 0
