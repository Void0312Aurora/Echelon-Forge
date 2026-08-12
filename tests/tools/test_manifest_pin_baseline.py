"""Shrink-only CI guard for the hash pins in the retained A2 manifests.

``tests/tools/test_a2_packet_paths_contract.py`` asserts that every pinned
path still resolves, but deliberately says nothing about the digests: the
sealed packet inherited a set of mismatched pins that pre-date the
ownership-first documentation migration, so a plain "zero mismatches"
assertion could never go green. That left the pins with no CI guard at all --
breaking a new one was free.

This module closes that hole without demanding the inherited debt be paid
first. ``tests/tools/manifest_pin_baseline.json`` records the mismatches that
exist today; the tests below allow that set to shrink and refuse to let it
grow. Repairing a pin is therefore a two-part change: fix the manifest and
delete the corresponding baseline entry in the same commit. Both directions
fail closed, so neither half can be forgotten.

The baseline splits mismatches into two tiers because the legacy raw-byte
counter in ``check_retained_manifest_integrity`` is checkout-dependent. A
Windows working tree (``core.autocrlf=true``) carries CRLF while the commit
carries LF, so 100 pins that hold the correct committed digest still fail a
raw-byte comparison there and pass on Linux CI. Those live in the
``newline_representation_mismatches`` tier and are only asserted on a CRLF
checkout. The nine ``content_mismatches`` disagree under every newline
representation and are asserted everywhere.

This suite carries no ``governance_audit`` marker on purpose: it guards pin
correctness, so it belongs in the default developer regression rather than
behind the governance gate. It hashes ~117 pinned files and runs in seconds.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pytest

from tools.maintenance import a2_packet_paths as paths
from tools.maintenance.retained_artifacts import manifest_integrity as integrity


BASELINE_PATH = Path(__file__).with_name("manifest_pin_baseline.json")

# The pin chain repaired on 2026-08-13 (see the A2 README evidence-integrity
# note). It is the one chain known to be correct end to end, so it doubles as a
# positive control: if the newline-tolerant comparison ever regresses, this is
# the first assertion to notice.
REPAIRED_CONTROL_TARGET = (
  "docs/systems/effects/reviews/a2_high_fidelity_damage_model_20260602"
  "/data_collection/f16c_block50_target_geometry/source_ledger.zh.md"
)

HASH_PREFIX_RE = re.compile(r"^[0-9a-f]{16}$")

BaselineKey = tuple[str, str, str, str]


def _baseline_key(row: dict[str, Any]) -> BaselineKey:
  # The target belongs to the identity: dropping it would let a pin be
  # repointed at a different file (digest kept) without tripping either
  # ratchet direction.
  return (
    row["manifest"],
    row["field_path"],
    row["target"],
    row["recorded_prefix"],
  )


def _describe(key: BaselineKey) -> str:
  manifest, field_path, target, recorded_prefix = key
  return f"{manifest}  {field_path}  target={target}  recorded={recorded_prefix}"


@pytest.fixture(scope="module")
def baseline() -> dict[str, Any]:
  return json.loads(BASELINE_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def pin_index() -> dict[str, list[integrity.PinEntry]]:
  return integrity.build_pin_index()


@pytest.fixture(scope="module")
def measured(
  pin_index: dict[str, list[integrity.PinEntry]],
) -> dict[str, list[integrity.PinEntry]]:
  return integrity.classify_pin_mismatches(pin_index)


# ---------------------------------------------------------------------------
# Baseline file hygiene
# ---------------------------------------------------------------------------


def test_baseline_file_is_internally_consistent(baseline: dict[str, Any]) -> None:
  assert baseline["schema_version"] == 1
  for field in ("generated_on", "generated_by", "packet", "policy", "tiers"):
    assert baseline[field], f"baseline is missing its {field!r} provenance field"

  content = baseline["content_mismatches"]
  newline = baseline["newline_representation_mismatches"]
  assert len(content) == baseline["content_mismatch_total"]
  assert len(newline) == baseline["newline_representation_total"]
  assert baseline["legacy_raw_mismatch_total"] == len(content) + len(newline)

  keys = [_baseline_key(row) for row in content + newline]
  assert len(keys) == len(set(keys)), "the baseline lists the same pin twice"
  for row in content + newline:
    assert HASH_PREFIX_RE.match(row["recorded_prefix"]), row
    assert row["target"], row


def test_baseline_packet_matches_the_canonical_packet_location(
  baseline: dict[str, Any],
) -> None:
  """A baseline generated against a stale packet root would guard nothing."""
  assert baseline["packet"] == paths.CANDIDATE_PACKAGE_RELATIVE_DIR.as_posix()
  assert baseline["manifest_globs"] == [paths.MANIFEST_GLOB]


# ---------------------------------------------------------------------------
# The scan itself must not fail open
# ---------------------------------------------------------------------------


def test_pin_index_sees_a_non_empty_inventory(
  pin_index: dict[str, list[integrity.PinEntry]],
  baseline: dict[str, Any],
) -> None:
  """An empty index would make every "no new mismatch" assertion vacuous."""
  pin_total = sum(len(entries) for entries in pin_index.values())

  assert pin_total > 0, "the pin index is empty; the packet moved or the glob is stale"
  assert pin_total >= baseline["legacy_raw_mismatch_total"], (
    f"the index holds {pin_total} pins but the baseline tracks "
    f"{baseline['legacy_raw_mismatch_total']} mismatches; the scan lost coverage"
  )


def test_every_pinned_target_still_exists(
  pin_index: dict[str, list[integrity.PinEntry]],
) -> None:
  absent = sorted(
    {entry.target for entry in integrity.iter_pin_entries(pin_index) if not entry.target_exists}
  )

  assert not absent, "these pinned targets no longer exist:\n  " + "\n  ".join(absent)


# ---------------------------------------------------------------------------
# Tier 1: content mismatches (checkout-independent, asserted everywhere)
# ---------------------------------------------------------------------------


def test_no_new_content_mismatch(
  baseline: dict[str, Any],
  measured: dict[str, list[integrity.PinEntry]],
) -> None:
  known = {_baseline_key(row) for row in baseline["content_mismatches"]}
  found = {entry.key for entry in measured["content"]}

  unexpected = sorted(found - known)
  assert not unexpected, (
    f"{len(unexpected)} pin(s) no longer match the file they pin, and none of "
    "them is an inherited condition recorded in "
    f"{BASELINE_PATH.name}:\n  "
    + "\n  ".join(_describe(key) for key in unexpected)
    + "\n\nRepoint the pin with:\n  python "
    "tools/maintenance/retained_artifacts/manifest_integrity.py --cascade "
    "<changed file> --write"
  )


def test_repaired_content_mismatch_is_removed_from_the_baseline(
  baseline: dict[str, Any],
  measured: dict[str, list[integrity.PinEntry]],
) -> None:
  """Fail closed on a shrunk mismatch set so the baseline cannot rot open."""
  known = {_baseline_key(row) for row in baseline["content_mismatches"]}
  found = {entry.key for entry in measured["content"]}

  repaired = sorted(known - found)
  assert not repaired, (
    f"{len(repaired)} baseline entr(y/ies) no longer mismatch. Delete them "
    f"from the 'content_mismatches' list in {BASELINE_PATH.name} and lower "
    "'content_mismatch_total' and 'legacy_raw_mismatch_total' to match:\n  "
    + "\n  ".join(_describe(key) for key in repaired)
  )


# ---------------------------------------------------------------------------
# Tier 2: newline-representation mismatches (only present on a CRLF checkout)
# ---------------------------------------------------------------------------


def test_no_new_newline_representation_mismatch(
  baseline: dict[str, Any],
  measured: dict[str, list[integrity.PinEntry]],
) -> None:
  known = {_baseline_key(row) for row in baseline["newline_representation_mismatches"]}
  found = {entry.key for entry in measured["newline"]}

  unexpected = sorted(found - known)
  assert not unexpected, (
    f"{len(unexpected)} pin(s) hold a committed-LF digest that the raw-byte "
    "checker cannot reproduce from this working tree, and are not recorded in "
    f"{BASELINE_PATH.name}:\n  " + "\n  ".join(_describe(key) for key in unexpected)
  )


def test_stale_newline_baseline_entries_are_removed_on_a_crlf_checkout(
  baseline: dict[str, Any],
  measured: dict[str, list[integrity.PinEntry]],
) -> None:
  """Only assertable where the working tree actually carries CRLF.

  On an LF checkout (Linux CI) every entry in this tier is absent by
  construction, which is not staleness. An entry is only stale when its target
  still has CRLF on disk yet the pin stopped being reported.
  """
  known = {_baseline_key(row): row for row in baseline["newline_representation_mismatches"]}
  found = {entry.key for entry in measured["newline"]}

  stale: list[BaselineKey] = []
  for key, row in known.items():
    if key in found:
      continue
    target = paths.REPO_ROOT / row["target"]
    if target.is_file() and b"\r\n" in target.read_bytes():
      stale.append(key)

  assert not stale, (
    f"{len(stale)} baseline entr(y/ies) are stale on this CRLF checkout. "
    f"Delete them from 'newline_representation_mismatches' in "
    f"{BASELINE_PATH.name} and lower 'newline_representation_total' and "
    "'legacy_raw_mismatch_total' to match:\n  "
    + "\n  ".join(_describe(key) for key in stale)
  )


# ---------------------------------------------------------------------------
# The two tiers must add up to the number the legacy tool reports
# ---------------------------------------------------------------------------


def test_legacy_counter_is_fully_explained_by_the_two_tiers(
  baseline: dict[str, Any],
  measured: dict[str, list[integrity.PinEntry]],
) -> None:
  summary = integrity.check_retained_manifest_integrity()
  present_content = [entry for entry in measured["content"] if entry.target_exists]

  assert summary["sha_mismatch_total"] == len(present_content) + len(measured["newline"]), (
    "the raw-byte counter and the pin index disagree about which pins are "
    "mismatched; one of the two row models drifted"
  )
  assert summary["sha_mismatch_total"] <= baseline["legacy_raw_mismatch_total"], (
    f"the raw-byte counter rose to {summary['sha_mismatch_total']} from the "
    f"baselined {baseline['legacy_raw_mismatch_total']}"
  )


def test_who_pins_reports_the_repaired_control_chain(
  pin_index: dict[str, list[integrity.PinEntry]],
) -> None:
  """The 2026-08-13 repair is the known-good chain; it must stay clean."""
  entries = integrity.who_pins(REPAIRED_CONTROL_TARGET, pin_index)

  assert len(entries) == 2, [entry.field_path for entry in entries]
  assert {entry.field for entry in entries} == {"sha256", "content_hash"}
  assert all(entry.matched for entry in entries), [
    (entry.field_path, entry.recorded_sha256, entry.canonical_sha256) for entry in entries
  ]
  assert all(entry.recorded_size == entry.canonical_size for entry in entries)


# ---------------------------------------------------------------------------
# Behaviour of the reverse index and the cascade, on synthetic packets
# ---------------------------------------------------------------------------


def _write_manifest(path: Path, payload: dict[str, Any]) -> None:
  path.parent.mkdir(parents=True, exist_ok=True)
  text = json.dumps(payload, indent=2, ensure_ascii=True, sort_keys=True) + "\n"
  path.write_text(text, encoding="utf-8", newline="\n")


def _canonical_digest(path: Path) -> str:
  return integrity._digest_target(path).canonical_sha256


def test_build_pin_index_groups_every_pin_under_its_target(tmp_path: Path) -> None:
  repo_root = tmp_path / "repo"
  manifest_path = repo_root / "package" / "retained_artifacts" / "s" / "manifest.json"
  artifact = repo_root / "artifact.md"
  artifact.parent.mkdir(parents=True, exist_ok=True)
  artifact.write_bytes(b"one\ntwo\n")
  digest = _canonical_digest(artifact)
  _write_manifest(
    manifest_path,
    {"inputs": [{"path": "artifact.md", "sha256": digest, "content_hash": f"sha256:{digest}"}]},
  )

  index = integrity.build_pin_index(repo_root=repo_root, manifest_paths=[manifest_path])

  assert list(index) == ["artifact.md"]
  entries = index["artifact.md"]
  assert [entry.field_path for entry in entries] == [
    "$.inputs[0].content_hash",
    "$.inputs[0].sha256",
  ]
  assert all(entry.matched and not entry.newline_only for entry in entries)


def test_a_crlf_working_copy_still_matches_its_committed_lf_pin(tmp_path: Path) -> None:
  repo_root = tmp_path / "repo"
  manifest_path = repo_root / "package" / "retained_artifacts" / "s" / "manifest.json"
  artifact = repo_root / "artifact.md"
  artifact.parent.mkdir(parents=True, exist_ok=True)
  artifact.write_bytes(b"one\r\ntwo\r\n")
  _write_manifest(
    manifest_path,
    {"inputs": [{"path": "artifact.md", "sha256": _canonical_digest(artifact)}]},
  )

  entry = integrity.build_pin_index(
    repo_root=repo_root, manifest_paths=[manifest_path]
  )["artifact.md"][0]

  assert entry.matched
  assert entry.newline_only
  assert entry.actual_sha256 != entry.canonical_sha256


def test_binary_payloads_are_never_newline_normalised(tmp_path: Path) -> None:
  """A CRLF pair inside a PDF or XLSX is payload, not a line ending."""
  repo_root = tmp_path / "repo"
  manifest_path = repo_root / "package" / "retained_artifacts" / "s" / "manifest.json"
  artifact = repo_root / "payload.bin"
  artifact.parent.mkdir(parents=True, exist_ok=True)
  artifact.write_bytes(b"%PDF\x00stream\r\nendstream\x00")
  _write_manifest(
    manifest_path,
    {"inputs": [{"path": "payload.bin", "sha256": _canonical_digest(artifact)}]},
  )

  entry = integrity.build_pin_index(
    repo_root=repo_root, manifest_paths=[manifest_path]
  )["payload.bin"][0]

  assert entry.matched
  assert not entry.newline_only
  assert entry.actual_sha256 == entry.canonical_sha256


def test_who_pins_accepts_windows_separators_and_absolute_paths(tmp_path: Path) -> None:
  repo_root = tmp_path / "repo"
  manifest_path = repo_root / "package" / "retained_artifacts" / "s" / "manifest.json"
  artifact = repo_root / "nested" / "artifact.md"
  artifact.parent.mkdir(parents=True, exist_ok=True)
  artifact.write_bytes(b"body\n")
  _write_manifest(
    manifest_path,
    {"inputs": [{"path": "nested/artifact.md", "sha256": _canonical_digest(artifact)}]},
  )
  index = integrity.build_pin_index(repo_root=repo_root, manifest_paths=[manifest_path])

  for spelling in ("nested/artifact.md", "nested\\artifact.md", "./nested/artifact.md"):
    assert len(integrity.who_pins(spelling, index)) == 1, spelling
  assert integrity.who_pins("nested/absent.md", index) == []


def _chained_package(tmp_path: Path) -> tuple[Path, Path, Path, Path]:
  """Build repo/artifact.md <- inner/manifest.json <- outer/manifest.json."""
  repo_root = tmp_path / "repo"
  retained = repo_root / "package" / "retained_artifacts"
  inner = retained / "inner" / "manifest.json"
  outer = retained / "outer" / "manifest.json"
  artifact = repo_root / "artifact.md"
  artifact.parent.mkdir(parents=True, exist_ok=True)
  artifact.write_bytes(b"original\n")

  _write_manifest(
    inner,
    {
      "inputs": [
        {
          "path": "artifact.md",
          "sha256": _canonical_digest(artifact),
          "content_hash": f"sha256:{_canonical_digest(artifact)}",
          "size_bytes": len(artifact.read_bytes()),
        }
      ]
    },
  )
  _write_manifest(
    outer,
    {
      "artifacts": [
        {
          "path": "package/retained_artifacts/inner/manifest.json",
          "sha256": _canonical_digest(inner),
        }
      ]
    },
  )
  return repo_root, artifact, inner, outer


def test_cascade_dry_run_plans_the_whole_chain_without_touching_disk(
  tmp_path: Path,
) -> None:
  repo_root, artifact, inner, outer = _chained_package(tmp_path)
  artifact.write_bytes(b"revised\r\nbody\r\n")
  before = (inner.read_bytes(), outer.read_bytes())

  plan = integrity.plan_pin_cascade(
    "artifact.md",
    repo_root=repo_root,
    manifest_paths=[inner, outer],
  )

  assert plan["mode"] == "dry-run"
  assert plan["closed"] and not plan["errors"]
  assert {edit["field_path"] for edit in plan["edits"]} == {
    "$.inputs[0].sha256",
    "$.inputs[0].content_hash",
    "$.inputs[0].size_bytes",
    "$.artifacts[0].sha256",
  }
  assert (inner.read_bytes(), outer.read_bytes()) == before


def test_cascade_write_closes_the_chain_and_records_lf_digests(tmp_path: Path) -> None:
  repo_root, artifact, inner, outer = _chained_package(tmp_path)
  artifact.write_bytes(b"revised\r\nbody\r\n")

  plan = integrity.plan_pin_cascade(
    "artifact.md",
    repo_root=repo_root,
    manifest_paths=[inner, outer],
    write=True,
  )

  assert sorted(plan["written_manifests"]) == [
    "package/retained_artifacts/inner/manifest.json",
    "package/retained_artifacts/outer/manifest.json",
  ]
  reindexed = integrity.build_pin_index(repo_root=repo_root, manifest_paths=[inner, outer])
  assert all(entry.matched for entry in integrity.iter_pin_entries(reindexed))

  row = json.loads(inner.read_text(encoding="utf-8"))["inputs"][0]
  assert row["sha256"] == _canonical_digest(artifact)
  assert row["content_hash"] == f"sha256:{_canonical_digest(artifact)}"
  assert row["size_bytes"] == len(artifact.read_bytes().replace(b"\r\n", b"\n"))

  settled = integrity.plan_pin_cascade(
    "artifact.md", repo_root=repo_root, manifest_paths=[inner, outer]
  )
  assert settled["edits"] == []


def test_cascade_refuses_to_rewrite_a_manifest_it_cannot_reserialise(
  tmp_path: Path,
) -> None:
  """Reformatting a sealed manifest would invalidate every pin held against it."""
  repo_root, artifact, inner, outer = _chained_package(tmp_path)
  inner.write_text(
    json.dumps(json.loads(inner.read_text(encoding="utf-8")), indent=4, sort_keys=True) + "\n",
    encoding="utf-8",
    newline="\n",
  )
  artifact.write_bytes(b"revised\n")
  before = inner.read_bytes()

  plan = integrity.plan_pin_cascade(
    "artifact.md",
    repo_root=repo_root,
    manifest_paths=[inner, outer],
    write=True,
  )

  assert plan["errors"]
  assert plan["written_manifests"] == []
  assert inner.read_bytes() == before


def test_cascade_pins_an_untouched_non_round_trip_manifest_by_its_disk_bytes(
  tmp_path: Path,
) -> None:
  """An untouched pinned manifest must be hashed from the bytes on disk.

  When a pinned manifest does not reserialise byte-for-byte (indent=4 here)
  but needs no edits of its own, upstream pins must record the digest of its
  actual on-disk bytes. Hashing the canonical reserialisation instead would
  write a digest that exists nowhere, leaving the freshly rewritten upstream
  pin mismatched the moment it lands.
  """
  repo_root = tmp_path / "repo"
  retained = repo_root / "package" / "retained_artifacts"
  inner = retained / "inner" / "manifest.json"
  outer = retained / "outer" / "manifest.json"
  artifact = repo_root / "artifact.md"
  artifact.parent.mkdir(parents=True, exist_ok=True)
  artifact.write_bytes(b"body\n")

  inner.parent.mkdir(parents=True, exist_ok=True)
  inner.write_text(
    json.dumps(
      {"inputs": [{"path": "artifact.md", "sha256": _canonical_digest(artifact)}]},
      indent=4,
      sort_keys=True,
    )
    + "\n",
    encoding="utf-8",
    newline="\n",
  )
  _write_manifest(
    outer,
    {
      "artifacts": [
        {
          "path": "package/retained_artifacts/inner/manifest.json",
          "sha256": "0" * 64,
        }
      ]
    },
  )

  plan = integrity.plan_pin_cascade(
    "package/retained_artifacts/inner/manifest.json",
    repo_root=repo_root,
    manifest_paths=[inner, outer],
    write=True,
  )

  assert not plan["errors"]
  assert plan["written_manifests"] == ["package/retained_artifacts/outer/manifest.json"]
  rewritten = json.loads(outer.read_text(encoding="utf-8"))
  assert rewritten["artifacts"][0]["sha256"] == _canonical_digest(inner)
  # The non-round-trip inner manifest itself stays untouched on disk.
  assert "    " in inner.read_text(encoding="utf-8")

  reindexed = integrity.build_pin_index(repo_root=repo_root, manifest_paths=[inner, outer])
  assert all(entry.matched for entry in integrity.iter_pin_entries(reindexed))


def test_baseline_identity_distinguishes_pins_by_target(tmp_path: Path) -> None:
  """Repointing a known-mismatched pin at another file must trip the ratchet.

  The manifest, field path, and recorded digest all stay identical here; only
  the pinned target moves. Without the target in the identity key the new
  provenance would satisfy both the new-mismatch and the repaired-entry
  checks simultaneously.
  """
  repo_root = tmp_path / "repo"
  manifest_path = repo_root / "package" / "retained_artifacts" / "s" / "manifest.json"
  for name in ("original.md", "moved.md"):
    target = repo_root / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(b"content of %s\n" % name.encode())
  stale_digest = "f" * 64

  _write_manifest(
    manifest_path,
    {"inputs": [{"path": "original.md", "sha256": stale_digest}]},
  )
  index = integrity.build_pin_index(repo_root=repo_root, manifest_paths=[manifest_path])
  key_original = index["original.md"][0].key

  _write_manifest(
    manifest_path,
    {"inputs": [{"path": "moved.md", "sha256": stale_digest}]},
  )
  index = integrity.build_pin_index(repo_root=repo_root, manifest_paths=[manifest_path])
  key_moved = index["moved.md"][0].key

  assert key_original != key_moved
