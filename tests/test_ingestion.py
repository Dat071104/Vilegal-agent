"""
tests/test_ingestion.py — Phase 2A ingestion scaffold tests.

Covers:
  - Source registry contains correct dataset metadata.
  - max-record cap rejects / clamps values above 100.
  - Offline fixture ingestion works with no network.
  - Provenance manifest includes license and attribution fields.
  - Quality report computes required metrics correctly.
  - Malformed records are rejected and written separately.
  - No raw/bulk data path is ever used.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

import pytest

from vilegal.ingestion.hf_sample_loader import load_from_fixture
from vilegal.ingestion.normalizers import normalize_record
from vilegal.ingestion.provenance import build_manifest, write_manifest
from vilegal.ingestion.quality_checks import run_quality_checks, write_quality_report
from vilegal.ingestion.source_registry import (
    MAX_RECORDS_HARD_CAP,
    REGISTRY,
    enforce_max_records,
    get_source,
)

# ---------------------------------------------------------------------------
# Fixture paths (git-tracked synthetic files only)
# ---------------------------------------------------------------------------

FIXTURES_DIR = Path(__file__).parent / "fixtures"
VALID_FIXTURE = FIXTURES_DIR / "synthetic_legal_articles.jsonl"
MALFORMED_FIXTURE = FIXTURES_DIR / "malformed_legal_articles.jsonl"

SYNTHETIC_SOURCE = get_source("synthetic_example")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_valid_record(idx: int = 1) -> dict:
    """Return a minimal synthetic raw record suitable for normalization."""
    return {
        "doc_id": f"SYNTH-DOC-{idx:03d}",
        "doc_type": "luat",
        "number": f"SYN/2024/QH{idx:02d}",
        "document_title": f"Luat mau so {idx}",
        "status": "in_force",
        "article_number": idx,
        "title": f"Dieu {idx}",
        "text": f"Noi dung dieu {idx} chi danh cho muc dich kiem thu.",
        "source_dataset": "synthetic_example",
        "source_id": f"SYNTH-ARTICLE-{idx:03d}",
        "source_url": f"https://example.invalid/doc-{idx:03d}#article-{idx}",
        "license": "Internal Example Only",
        "retrieved_at": "2026-06-09T00:00:00Z",
        "is_synthetic_example": True,
        "language": "vi",
    }


def _normalize(raw: dict) -> dict:
    return normalize_record(
        raw=raw,
        source_dataset=SYNTHETIC_SOURCE.name,
        source_url=SYNTHETIC_SOURCE.url,
        license_str=SYNTHETIC_SOURCE.license,
    )


# ---------------------------------------------------------------------------
# 1. Source registry tests
# ---------------------------------------------------------------------------

class TestSourceRegistry:
    def test_all_required_sources_present(self):
        required = {"uts_vlc", "viet_legal_instruct", "viet_legal_docs", "viet_legal_qa", "synthetic_example"}
        assert required.issubset(REGISTRY.keys())

    def test_uts_vlc_metadata(self):
        src = get_source("uts_vlc")
        assert src.hf_handle == "undertheseanlp/UTS_VLC"
        assert src.license == "MIT"
        assert src.license_confirmed is True
        assert src.bulk_download_blocked is True
        assert src.approved_for_sample is True

    def test_viet_legal_instruct_has_attribution(self):
        src = get_source("viet_legal_instruct")
        assert src.attribution_required is True
        assert src.license == "CC-BY-4.0"
        assert "CC-BY-4.0" in src.attribution_note or "cc-by" in src.attribution_note.lower()

    def test_viet_legal_qa_not_approved(self):
        src = get_source("viet_legal_qa")
        assert src.approved_for_sample is False
        assert src.license == "UNKNOWN"

    def test_all_sources_have_bulk_download_blocked(self):
        """Every HF source must have bulk_download_blocked=True in Phase 2A."""
        for src_id, src in REGISTRY.items():
            if src_id != "synthetic_example":
                assert src.bulk_download_blocked is True, (
                    f"Source '{src_id}' must have bulk_download_blocked=True in Phase 2A."
                )

    def test_unknown_source_raises_key_error(self):
        with pytest.raises(KeyError, match="Unknown source"):
            get_source("nonexistent_source_xyz")

    def test_synthetic_example_has_no_hf_handle(self):
        src = get_source("synthetic_example")
        assert src.hf_handle is None


# ---------------------------------------------------------------------------
# 2. Max-records cap tests
# ---------------------------------------------------------------------------

class TestMaxRecordsCap:
    def test_hard_cap_value_is_1000(self):
        assert MAX_RECORDS_HARD_CAP == 1000

    def test_valid_value_passes_through(self):
        assert enforce_max_records(50) == 50
        assert enforce_max_records(1) == 1
        assert enforce_max_records(100) == 100

    def test_zero_raises(self):
        with pytest.raises(ValueError, match="positive integer"):
            enforce_max_records(0)

    def test_negative_raises(self):
        with pytest.raises(ValueError):
            enforce_max_records(-5)

    def test_above_cap_is_clamped(self, capsys):
        result = enforce_max_records(2000)
        assert result == MAX_RECORDS_HARD_CAP
        captured = capsys.readouterr()
        assert "Clamping" in captured.out

    def test_default_remains_conservative(self):
        from vilegal.ingestion.source_registry import DEFAULT_MAX_RECORDS
        assert DEFAULT_MAX_RECORDS == 50

    def test_above_cap_prints_warning_with_source(self, capsys):
        enforce_max_records(1999, "uts_vlc")
        captured = capsys.readouterr()
        assert "uts_vlc" in captured.out


# ---------------------------------------------------------------------------
# 3. Offline fixture loading tests
# ---------------------------------------------------------------------------

class TestOfflineFixtureLoader:
    def test_loads_valid_fixture(self):
        records = load_from_fixture(VALID_FIXTURE, max_records=10)
        assert len(records) == 3
        assert all(isinstance(r, dict) for r in records)

    def test_max_records_respected(self):
        records = load_from_fixture(VALID_FIXTURE, max_records=2)
        assert len(records) == 2

    def test_missing_fixture_raises(self, tmp_path):
        missing = tmp_path / "nonexistent.jsonl"
        with pytest.raises(FileNotFoundError):
            load_from_fixture(missing, max_records=10)

    def test_fixture_records_have_text(self):
        records = load_from_fixture(VALID_FIXTURE, max_records=10)
        for r in records:
            assert "text" in r and r["text"].strip()

    def test_no_network_call_is_needed(self):
        """Loading fixture must never import or call any networking library."""
        import importlib
        loader_module = importlib.import_module("vilegal.ingestion.hf_sample_loader")
        source = Path(loader_module.__file__).read_text()
        # The fixture path in load_from_fixture must not contain urllib/requests/httpx
        assert "urllib.request.urlopen" not in source
        assert "requests.get" not in source


# ---------------------------------------------------------------------------
# 4. Normalizer tests
# ---------------------------------------------------------------------------

class TestNormalizer:
    def test_valid_record_normalizes(self):
        raw = _make_valid_record(1)
        normalized = _normalize(raw)
        assert normalized["text"] == raw["text"].strip()
        assert normalized["source_dataset"] == SYNTHETIC_SOURCE.name
        assert normalized["license"] == SYNTHETIC_SOURCE.license
        assert normalized["transform_version"] == "phase_2a_v1"
        assert "record_id" in normalized
        assert len(normalized["record_id"]) == 16

    def test_record_id_is_deterministic(self):
        raw = _make_valid_record(1)
        id1 = _normalize(raw)["record_id"]
        id2 = _normalize(raw)["record_id"]
        assert id1 == id2

    def test_missing_text_raises(self):
        raw = _make_valid_record(1)
        del raw["text"]
        with pytest.raises(ValueError, match="no usable text"):
            _normalize(raw)

    def test_whitespace_only_text_raises(self):
        raw = _make_valid_record(1)
        raw["text"] = "   "
        with pytest.raises(ValueError, match="no usable text"):
            _normalize(raw)

    def test_unknown_doc_type_coerces_to_other(self):
        raw = _make_valid_record(1)
        raw["doc_type"] = "some_unknown_type"
        normalized = _normalize(raw)
        assert normalized["document_type"] == "other"

    def test_article_number_preserved(self):
        raw = _make_valid_record(7)
        normalized = _normalize(raw)
        assert normalized["article_number"] == 7

    def test_all_required_fields_present(self):
        required = {
            "record_id", "source_dataset", "source_url", "source_id",
            "license", "retrieved_at", "transform_version",
            "document_type", "text", "effective_status", "raw_metadata",
        }
        raw = _make_valid_record(1)
        normalized = _normalize(raw)
        for field in required:
            assert field in normalized, f"Missing required field: {field}"

    def test_conversations_format_extracts_user_turn(self):
        """duyet/vietnamese-legal-instruct schema: conversations list → user turn → text."""
        raw = {
            "qa_type": "explain_simple",
            "source_id": "67007",
            "document_type": "Quyết định",
            "conversations": [
                {"role": "system", "content": "Bạn phiên dịch pháp luật."},
                {"role": "user", "content": "Điều 1. Phạm vi điều chỉnh: Quy định về quyền cơ bản."},
                {"role": "assistant", "content": "Điều này quy định quyền cơ bản của công dân."},
            ],
        }
        normalized = _normalize(raw)
        assert "Phạm vi điều chỉnh" in normalized["text"]
        assert normalized["source_id"] == "67007"

    def test_conversations_format_assistant_not_promoted(self):
        """Assistant response must NOT become the primary text (not legal ground truth)."""
        raw = {
            "qa_type": "explain_simple",
            "source_id": "99999",
            "conversations": [
                {"role": "system", "content": "Hướng dẫn."},
                {"role": "user", "content": "Luật số 91/2015/QH13, Điều 1."},
                {"role": "assistant", "content": "Đây là câu trả lời tổng hợp."},
            ],
        }
        normalized = _normalize(raw)
        # text must be the user turn, not the assistant turn
        assert "Luật số 91" in normalized["text"]
        assert "tổng hợp" not in normalized["text"]

    def test_conversations_format_no_user_turn_raises(self):
        """If conversations has no user turn at all, must raise ValueError."""
        raw = {
            "source_id": "X",
            "conversations": [
                {"role": "system", "content": "Hướng dẫn."},
                {"role": "assistant", "content": "Câu trả lời."},
            ],
        }
        with pytest.raises(ValueError, match="no usable text"):
            _normalize(raw)


# ---------------------------------------------------------------------------
# 5. Provenance manifest tests
# ---------------------------------------------------------------------------

class TestProvenanceManifest:
    def test_manifest_has_license(self):
        src = get_source("uts_vlc")
        manifest = build_manifest(src, max_records=10, actual_records_seen=10)
        assert manifest.license == "MIT"
        assert manifest.license_confirmed is True

    def test_manifest_has_attribution_fields(self):
        src = get_source("viet_legal_instruct")
        manifest = build_manifest(src, max_records=5, actual_records_seen=5)
        assert manifest.attribution_required is True
        assert "CC-BY-4.0" in manifest.attribution_note

    def test_manifest_bulk_download_blocked(self):
        src = get_source("uts_vlc")
        manifest = build_manifest(src, max_records=10, actual_records_seen=5)
        assert manifest.bulk_download_blocked is True

    def test_manifest_offline_fixture_recorded(self, tmp_path):
        fixture = tmp_path / "fixture.jsonl"
        fixture.write_text("")
        src = get_source("synthetic_example")
        manifest = build_manifest(src, max_records=3, actual_records_seen=3, offline_fixture=fixture)
        assert manifest.offline_fixture_used == str(fixture)

    def test_manifest_written_to_disk(self, tmp_path):
        src = get_source("uts_vlc")
        manifest = build_manifest(src, max_records=10, actual_records_seen=10)
        out_path = write_manifest(manifest, tmp_path)
        assert out_path.exists()
        data = json.loads(out_path.read_text(encoding="utf-8"))
        assert data["license"] == "MIT"
        assert data["bulk_download_blocked"] is True
        assert "sample-only" in data["notes"].lower()

    def test_manifest_contains_source_url(self):
        src = get_source("uts_vlc")
        manifest = build_manifest(src, max_records=10, actual_records_seen=10)
        assert "huggingface.co" in manifest.dataset_url


# ---------------------------------------------------------------------------
# 6. Quality report tests
# ---------------------------------------------------------------------------

class TestQualityReport:
    def _make_normalized_batch(self, n: int = 3) -> list[dict]:
        return [_normalize(_make_valid_record(i + 1)) for i in range(n)]

    def test_all_valid_records_pass_gate(self):
        normalized = self._make_normalized_batch(3)
        report = run_quality_checks(normalized, [], "synthetic_example", max_records=10)
        assert report.total_normalized == 3
        assert report.total_rejected == 0
        assert report.parse_success_rate == 1.0
        assert report.quality_gate_passed is True

    def test_rejected_records_counted(self):
        normalized = self._make_normalized_batch(2)
        rejected = [{"error": "no text", "raw": {"doc_id": "BAD-001"}}]
        report = run_quality_checks(normalized, rejected, "synthetic_example", max_records=10)
        assert report.total_rejected == 1
        assert report.total_seen == 3
        assert report.parse_success_rate < 1.0

    def test_duplicate_records_detected(self):
        record = _normalize(_make_valid_record(1))
        normalized = [record, record]  # exact duplicate
        report = run_quality_checks(normalized, [], "synthetic_example", max_records=10)
        assert report.duplicate_rate > 0.0

    def test_missing_license_detected(self):
        normalized = self._make_normalized_batch(3)
        normalized[0]["license"] = ""
        report = run_quality_checks(normalized, [], "synthetic_example", max_records=10)
        assert report.missing_license_rate > 0.0

    def test_bulk_download_blocked_always_true(self):
        report = run_quality_checks([], [], "synthetic_example", max_records=10)
        assert report.bulk_download_blocked is True

    def test_quality_report_written_to_disk(self, tmp_path):
        normalized = self._make_normalized_batch(2)
        report = run_quality_checks(normalized, [], "synthetic_example", max_records=10)
        out_path = write_quality_report(report, tmp_path)
        assert out_path.exists()
        data = json.loads(out_path.read_text(encoding="utf-8"))
        assert data["bulk_download_blocked"] is True
        assert "parse_success_rate" in data

    def test_threshold_violation_reported(self):
        """Synthetic: introduce many rejections → parse_success_rate fails threshold."""
        normalized = self._make_normalized_batch(1)
        rejected = [{"error": "no text", "raw": {}} for _ in range(99)]
        report = run_quality_checks(normalized, rejected, "synthetic_example", max_records=100)
        assert report.quality_gate_passed is False
        assert any("parse_success_rate" in v for v in report.threshold_violations)


# ---------------------------------------------------------------------------
# 7. Malformed record rejection tests
# ---------------------------------------------------------------------------

class TestMalformedRejection:
    def test_records_without_text_are_rejected(self):
        """Record 1 in malformed fixture has no text field → must be rejected."""
        raw_records = load_from_fixture(MALFORMED_FIXTURE, max_records=10)
        rejected = []
        normalized = []
        for raw in raw_records:
            try:
                normalized.append(_normalize(raw))
            except ValueError as exc:
                rejected.append({"error": str(exc), "raw": raw})
        # records 1 and 2 are malformed (no text / whitespace-only text)
        # record 3 has text and should normalize
        assert len(rejected) >= 2
        assert len(normalized) >= 1

    def test_rejected_records_have_error_field(self):
        raw_records = load_from_fixture(MALFORMED_FIXTURE, max_records=10)
        for raw in raw_records:
            try:
                _normalize(raw)
            except ValueError as exc:
                rejected_entry = {"error": str(exc), "raw": raw}
                assert "error" in rejected_entry
                assert isinstance(rejected_entry["error"], str)
                break


# ---------------------------------------------------------------------------
# 8. No bulk data path tests
# ---------------------------------------------------------------------------

class TestNoBulkDataPath:
    def test_hf_loader_does_not_import_dataset_at_module_level(self):
        """The datasets library must not be imported at module level."""
        import importlib
        loader = importlib.import_module("vilegal.ingestion.hf_sample_loader")
        assert not hasattr(loader, "load_dataset"), (
            "load_dataset must not be imported at module level in hf_sample_loader."
        )

    def test_source_registry_has_no_download_call(self):
        """source_registry.py must not contain any download or HF load call."""
        import importlib
        reg_module = importlib.import_module("vilegal.ingestion.source_registry")
        source = Path(reg_module.__file__).read_text()
        assert "load_dataset" not in source
        assert "snapshot_download" not in source

    def test_artifacts_dir_is_not_in_fixtures(self):
        """artifacts/ output path must never overlap with git-tracked tests/fixtures/."""
        artifacts = Path("artifacts").resolve()
        fixtures = FIXTURES_DIR.resolve()
        assert not str(fixtures).startswith(str(artifacts)), (
            "tests/fixtures/ must never be inside artifacts/."
        )

    def test_synthetic_source_has_no_hf_handle(self):
        """synthetic_example must never trigger an HF download."""
        src = get_source("synthetic_example")
        assert src.hf_handle is None


# ---------------------------------------------------------------------------
# 9. Phase 2B alias resolution tests
# ---------------------------------------------------------------------------

class TestSourceAliases:
    """Phase 2B: CLI-friendly aliases resolve to the canonical registry entries."""

    def test_duyet_legal_instruct_alias_resolves(self):
        src = get_source("duyet_legal_instruct")
        assert src.source_id == "viet_legal_instruct"
        assert src.hf_handle == "duyet/vietnamese-legal-instruct"

    def test_th1nhng0_legal_documents_alias_resolves(self):
        src = get_source("th1nhng0_legal_documents")
        assert src.source_id == "viet_legal_docs"
        assert src.hf_handle == "th1nhng0/vietnamese-legal-documents"

    def test_canonical_ids_still_work_after_alias_patch(self):
        """Original canonical IDs must not break."""
        for canonical in ("uts_vlc", "viet_legal_instruct", "viet_legal_docs",
                          "viet_legal_qa", "synthetic_example"):
            src = get_source(canonical)
            assert src.source_id == canonical

    def test_alias_preserves_license(self):
        src_alias = get_source("duyet_legal_instruct")
        src_canonical = get_source("viet_legal_instruct")
        assert src_alias.license == src_canonical.license
        assert src_alias.attribution_required == src_canonical.attribution_required

    def test_alias_preserves_bulk_blocked(self):
        src = get_source("duyet_legal_instruct")
        assert src.bulk_download_blocked is True

    def test_unknown_alias_raises(self):
        with pytest.raises(KeyError, match="Unknown source"):
            get_source("completely_unknown_alias_xyz")

    def test_uts_vlc_default_split_is_2026(self):
        """UTS_VLC uses year-based splits; default must not be 'train'."""
        src = get_source("uts_vlc")
        assert src.default_split == "2026"

    def test_other_sources_default_split_is_train(self):
        """Sources other than UTS_VLC should default to 'train'."""
        for src_id in ("viet_legal_instruct", "viet_legal_docs", "synthetic_example"):
            src = get_source(src_id)
            assert src.default_split == "train", (
                f"Expected default_split='train' for '{src_id}', got '{src.default_split}'"
            )


