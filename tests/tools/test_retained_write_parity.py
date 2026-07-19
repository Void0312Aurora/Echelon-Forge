"""I19 byte-parity proof: every write_retained_* refactored to use
``write_and_hash_json`` must produce identical files to the old per-module
write pattern it replaced.

Strategy — inline the OLD write primitives as reference functions, then
compare file bytes produced by the shared helper for representative
payloads.  Each test class covers one JSON-serialisation variant.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from tools.maintenance.retained_artifacts.manifest_integrity import (
  _sha256_file,
  _sha256_text,
  write_and_hash_json,
)

SAMPLE_ASCII: dict[str, Any] = {
  "schema_version": "test.v1",
  "status": "retained_blocked",
  "nested": {"key": "value", "list": [1, 2, 3]},
  "authority_guards_all_false": True,
  "numbers": {"pi": 3.141592653589793, "neg": -42},
}

SAMPLE_UNICODE: dict[str, Any] = {
  "schema_version": "test.v1",
  "status": "retained_unicode_payload",
  "label": "校验中文与日本語",
  "emoji": "⚠️🔒",
  "nested": {"key": "wert_über_alles"},
}

SAMPLE_EMPTY: dict[str, Any] = {}

PAYLOADS = [SAMPLE_ASCII, SAMPLE_UNICODE, SAMPLE_EMPTY]


def _old_write_json_ensure_ascii_false_with_encoding(
  path: Path, payload: dict[str, Any],
) -> None:
  """Reference: benchmark_evidence (spreadsheet_replacement_tolerance, etc.)
  and external_signoff_evidence — ``ensure_ascii=False, encoding='utf-8'``."""
  path.parent.mkdir(parents=True, exist_ok=True)
  path.write_text(
    json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
  )


def _old_write_json_ensure_ascii_false_no_encoding(
  path: Path, payload: dict[str, Any],
) -> None:
  """Reference: benchmark_evidence (debris_admission, comparison_hashes,
  benchmark_execution_admission, spreadsheet_recalculation_admission)
  — ``ensure_ascii=False``, no explicit encoding."""
  path.parent.mkdir(parents=True, exist_ok=True)
  path.write_text(
    json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
  )


def _old_canonical_json_no_ensure_ascii(
  path: Path, payload: dict[str, Any],
) -> None:
  """Reference: independent_review, release_governance,
  candidate_artifacts, source_governance — default ``ensure_ascii=True``."""
  path.parent.mkdir(parents=True, exist_ok=True)
  text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
  path.write_text(text, encoding="utf-8")


def _old_canonical_json_ensure_ascii_false(
  path: Path, payload: dict[str, Any],
) -> None:
  """Reference: scope_provenance closeouts (warhead, target_geometry)
  — ``ensure_ascii=False``."""
  path.parent.mkdir(parents=True, exist_ok=True)
  text = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
  path.write_text(text, encoding="utf-8")


def _old_json_dump_geometry_warhead(
  path: Path, payload: dict[str, Any],
) -> None:
  """Reference: scope_provenance/geometry_warhead_row_provenance
  — ``_json_dump`` via ``_write_json``."""
  path.parent.mkdir(parents=True, exist_ok=True)
  text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
  path.write_text(text, encoding="utf-8")


# ---------------------------------------------------------------------------
# Module → (old_write_fn, helper kwargs) mapping
# ---------------------------------------------------------------------------

_NO_ENCODING_MODULES = frozenset({
  "benchmark_evidence.debris_admission",
  "benchmark_evidence.comparison_hashes",
  "benchmark_evidence.benchmark_execution_admission",
  "benchmark_evidence.spreadsheet_recalculation_admission",
})

MODULE_WRITE_SPECS: list[tuple[str, Any, dict[str, Any]]] = [
  # benchmark_evidence — ensure_ascii=False, no explicit encoding (4 modules)
  # Old code used ``write_text(text)`` without encoding; on Windows/GBK this
  # crashes with non-ASCII.  The helper now uses ``encoding='utf-8'`` which
  # is a strict improvement — tested for ASCII parity below; unicode parity
  # is skipped because the OLD code was broken for that case.
  ("benchmark_evidence.debris_admission",
   _old_write_json_ensure_ascii_false_no_encoding, {"ensure_ascii": False}),
  ("benchmark_evidence.comparison_hashes",
   _old_write_json_ensure_ascii_false_no_encoding, {"ensure_ascii": False}),
  ("benchmark_evidence.benchmark_execution_admission",
   _old_write_json_ensure_ascii_false_no_encoding, {"ensure_ascii": False}),
  ("benchmark_evidence.spreadsheet_recalculation_admission",
   _old_write_json_ensure_ascii_false_no_encoding, {"ensure_ascii": False}),

  # benchmark_evidence — ensure_ascii=False, explicit encoding (4 modules)
  ("benchmark_evidence.spreadsheet_replacement_tolerance",
   _old_write_json_ensure_ascii_false_with_encoding, {"ensure_ascii": False}),
  ("benchmark_evidence.spreadsheet_lineage_tolerance_packet",
   _old_write_json_ensure_ascii_false_with_encoding, {"ensure_ascii": False}),
  ("benchmark_evidence.selected_debris_case_packet",
   _old_write_json_ensure_ascii_false_with_encoding, {"ensure_ascii": False}),
  ("benchmark_evidence.selected_debris_case_admission",
   _old_write_json_ensure_ascii_false_with_encoding, {"ensure_ascii": False}),

  # external_signoff_evidence — ensure_ascii=False, explicit encoding (4 modules)
  ("external_signoff_evidence.signoff_request",
   _old_write_json_ensure_ascii_false_with_encoding, {"ensure_ascii": False}),
  ("external_signoff_evidence.packet_template",
   _old_write_json_ensure_ascii_false_with_encoding, {"ensure_ascii": False}),
  ("external_signoff_evidence.intake_contract",
   _old_write_json_ensure_ascii_false_with_encoding, {"ensure_ascii": False}),
  ("external_signoff_evidence.admission_preflight",
   _old_write_json_ensure_ascii_false_with_encoding, {"ensure_ascii": False}),

  # independent_review — default ensure_ascii (3 modules)
  ("independent_review.uncertainty_review",
   _old_canonical_json_no_ensure_ascii, {}),
  ("independent_review.scope_bucket_review",
   _old_canonical_json_no_ensure_ascii, {}),
  ("independent_review.review_closeout",
   _old_canonical_json_no_ensure_ascii, {}),

  # scope_provenance — ensure_ascii=False (3 modules)
  ("scope_provenance.warhead_scope_closeout",
   _old_canonical_json_ensure_ascii_false, {"ensure_ascii": False}),
  ("scope_provenance.target_geometry_closeout",
   _old_canonical_json_ensure_ascii_false, {"ensure_ascii": False}),
  ("scope_provenance.geometry_warhead_row_provenance",
   _old_json_dump_geometry_warhead, {"ensure_ascii": False}),

  # release_governance — default ensure_ascii (2 modules; source_release_signoff skipped)
  ("release_governance.scoped_release_identity",
   _old_canonical_json_no_ensure_ascii, {}),
  ("release_governance.provenance_identity_review",
   _old_canonical_json_no_ensure_ascii, {}),

  # candidate_artifacts — default ensure_ascii (2 modules)
  ("candidate_artifacts.component_fragility_review_gate",
   _old_canonical_json_no_ensure_ascii, {}),
  ("candidate_artifacts.component_fragility_benchmark",
   _old_canonical_json_no_ensure_ascii, {}),

  # source_governance — default ensure_ascii (1 module)
  ("source_governance.rights_output_policy",
   _old_canonical_json_no_ensure_ascii, {}),
]


@pytest.mark.parametrize(
  "module_name,old_fn,helper_kwargs",
  MODULE_WRITE_SPECS,
  ids=[s[0] for s in MODULE_WRITE_SPECS],
)
@pytest.mark.parametrize("payload", PAYLOADS, ids=["ascii", "unicode", "empty"])
def test_byte_parity(
  tmp_path: Path,
  module_name: str,
  old_fn: Any,
  helper_kwargs: dict[str, Any],
  payload: dict[str, Any],
) -> None:
  old_path = tmp_path / "old" / "artifact.json"
  new_path = tmp_path / "new" / "artifact.json"

  if payload is SAMPLE_UNICODE and module_name in _NO_ENCODING_MODULES:
    pytest.skip(
      "old code used write_text without encoding; crashes on "
      "Windows/GBK with non-ASCII — helper now uses utf-8 (strict fix)"
    )
  old_fn(old_path, payload)
  new_sha = write_and_hash_json(new_path, payload, **helper_kwargs)

  old_bytes = old_path.read_bytes()
  new_bytes = new_path.read_bytes()

  assert old_bytes == new_bytes, (
    f"Byte mismatch for {module_name}: "
    f"old {len(old_bytes)} bytes vs new {len(new_bytes)} bytes"
  )

  old_sha = hashlib.sha256(old_bytes).hexdigest()
  assert new_sha == old_sha, (
    f"SHA256 mismatch for {module_name}: helper returned {new_sha}, "
    f"file hash is {old_sha}"
  )


def test_sha256_file_vs_sha256_text_windows_newline(tmp_path: Path) -> None:
  """On Windows ``write_text`` translates ``\\n`` → ``\\r\\n``.
  ``_sha256_file`` reads raw bytes (with ``\\r\\n``), while
  ``_sha256_text`` encodes the original text (with ``\\n``).

  candidate_artifacts modules use ``_sha256_text`` for manifest hashes,
  so the refactored code preserves ``_sha256_text`` calls for those modules
  rather than substituting ``_sha256_file``."""
  import sys

  text = json.dumps(SAMPLE_ASCII, indent=2, sort_keys=True) + "\n"
  path = tmp_path / "check.json"
  path.write_text(text, encoding="utf-8")

  if sys.platform == "win32":
    assert _sha256_file(path) != _sha256_text(text), (
      "on Windows write_text translates newlines"
    )
    raw = text.encode("utf-8").replace(b"\n", b"\r\n")
    assert _sha256_file(path) == hashlib.sha256(raw).hexdigest()
  else:
    assert _sha256_file(path) == _sha256_text(text)


def test_content_sha256_without_newline(tmp_path: Path) -> None:
  """release_governance modules store ``content_sha256 = sha256(text WITHOUT
  trailing newline)`` separately from ``sha256 = _sha256_file(path)``.
  Verify these are always distinct (the content hash uses ``_sha256_text``
  which never includes OS-level newline translation)."""
  canonical = json.dumps(SAMPLE_ASCII, indent=2, sort_keys=True)
  file_text = canonical + "\n"
  path = tmp_path / "check.json"
  path.write_text(file_text, encoding="utf-8")

  content_sha = _sha256_text(canonical)
  file_sha = _sha256_file(path)
  assert content_sha != file_sha, "content vs file sha256 should differ"


def test_write_and_hash_json_creates_parent_dirs(tmp_path: Path) -> None:
  deep_path = tmp_path / "a" / "b" / "c" / "artifact.json"
  sha = write_and_hash_json(deep_path, SAMPLE_ASCII)
  assert deep_path.is_file()
  assert sha == _sha256_file(deep_path)


def test_residual_source_release_signoff_not_converted() -> None:
  """source_release_signoff.write_retained_artifacts is intentionally
  NOT converted (complex 3-pass manifest stabilisation).  This test
  documents that decision."""
  from tools.maintenance.release_governance import source_release_signoff

  import inspect

  src = inspect.getsource(source_release_signoff.write_retained_artifacts)
  assert "write_and_hash_json" not in src, (
    "source_release_signoff should NOT use the shared helper (residual)"
  )
