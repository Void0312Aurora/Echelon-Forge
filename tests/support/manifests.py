from __future__ import annotations

from pathlib import Path
from typing import Any


def walk_payload(payload: Any) -> list[Any]:
  values = [payload]
  if isinstance(payload, dict):
    for value in payload.values():
      values.extend(walk_payload(value))
  elif isinstance(payload, list):
    for value in payload:
      values.extend(walk_payload(value))
  return values


def assert_authority_guards_false(
  payload: dict[str, Any],
  *,
  guards_key: str = "authority_guards",
) -> None:
  if "authority_guards_all_false" in payload:
    assert payload["authority_guards_all_false"] is True
  assert not any(payload[guards_key].values())


def assert_no_keys_anywhere(payload: Any, forbidden_keys: set[str]) -> None:
  for value in walk_payload(payload):
    if isinstance(value, dict):
      assert not (forbidden_keys & set(value))


def assert_retained_manifest_clean(
  integrity_module: Any,
  manifest_path: Path,
) -> dict[str, Any]:
  summary = integrity_module.check_retained_manifest_integrity(
    manifest_paths=[manifest_path],
  )
  assert summary["missing_total"] == 0
  assert summary["sha_mismatch_total"] == 0
  assert summary["guard_true_total"] == 0
  return summary
