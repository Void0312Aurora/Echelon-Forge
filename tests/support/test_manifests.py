from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from tests.architecture.damage_model import helpers as damage_model_helpers
from tests.support.manifests import (
  assert_authority_guards_false,
  assert_no_keys_anywhere,
  assert_retained_manifest_clean,
  walk_payload,
)


def test_walk_payload_traverses_nested_dicts_and_lists() -> None:
  payload = {"outer": [{"leaf": 3}, 4]}

  assert walk_payload(payload) == [
    payload,
    payload["outer"],
    payload["outer"][0],
    3,
    4,
  ]


def test_authority_guard_assertion_supports_summary_and_custom_key() -> None:
  assert_authority_guards_false(
    {
      "authority_guards_all_false": True,
      "release_guards": {"pk": False, "fuze": False},
    },
    guards_key="release_guards",
  )


@pytest.mark.parametrize(
  "payload",
  [
    {"authority_guards_all_false": False, "authority_guards": {"pk": False}},
    {"authority_guards": {"pk": True}},
  ],
)
def test_authority_guard_assertion_fails_closed(payload: dict[str, object]) -> None:
  with pytest.raises(AssertionError):
    assert_authority_guards_false(payload)


def test_no_keys_anywhere_checks_nested_payloads() -> None:
  assert_no_keys_anywhere({"rows": [{"status": "clean"}]}, {"pk_authority"})

  with pytest.raises(AssertionError):
    assert_no_keys_anywhere(
      {"rows": [{"nested": {"pk_authority": True}}]},
      {"pk_authority"},
    )


def test_retained_manifest_clean_returns_integrity_summary(tmp_path: Path) -> None:
  manifest_path = tmp_path / "manifest.json"
  calls: list[list[Path]] = []

  def check_retained_manifest_integrity(*, manifest_paths: list[Path]):
    calls.append(manifest_paths)
    return {
      "missing_total": 0,
      "sha_mismatch_total": 0,
      "guard_true_total": 0,
    }

  integrity_module = SimpleNamespace(
    check_retained_manifest_integrity=check_retained_manifest_integrity,
  )

  summary = assert_retained_manifest_clean(integrity_module, manifest_path)

  assert calls == [[manifest_path]]
  assert summary["missing_total"] == 0


@pytest.mark.parametrize(
  "field",
  ["missing_total", "sha_mismatch_total", "guard_true_total"],
)
def test_retained_manifest_clean_rejects_each_integrity_failure(
  tmp_path: Path,
  field: str,
) -> None:
  summary = {
    "missing_total": 0,
    "sha_mismatch_total": 0,
    "guard_true_total": 0,
  }
  summary[field] = 1
  integrity_module = SimpleNamespace(
    check_retained_manifest_integrity=lambda **kwargs: summary,
  )

  with pytest.raises(AssertionError):
    assert_retained_manifest_clean(integrity_module, tmp_path / "manifest.json")


def test_damage_model_helpers_reexport_shared_manifest_api() -> None:
  assert damage_model_helpers.walk_payload is walk_payload
  assert (
    damage_model_helpers.assert_authority_guards_false
    is assert_authority_guards_false
  )
  assert damage_model_helpers.assert_no_keys_anywhere is assert_no_keys_anywhere
  assert (
    damage_model_helpers.assert_retained_manifest_clean
    is assert_retained_manifest_clean
  )
