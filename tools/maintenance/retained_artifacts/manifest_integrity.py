#!/usr/bin/env python3
"""Check retained A2 manifest artifact hashes and authority guards."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
  sys.path.insert(0, str(REPO_ROOT))

from tools.maintenance.a2_packet_paths import (  # noqa: E402
  CANDIDATE_PACKAGE_DIR,
  MANIFEST_GLOB as DEFAULT_MANIFEST_GLOB,
  translate_logical_a2_path,
)

PATH_FIELDS = ("path", "relative_path", "filename")
HASH_FIELDS = ("sha256", "content_sha256", "content_hash")
GUARD_TERMS = ("authority", "stock", "pk", "fuze")
SAFE_AGGREGATE_GUARD_MARKERS = ("all_false", "none_granted", "not_granted")


@dataclass(frozen=True)
class ManifestFinding:
  manifest_path: Path
  row_path: str
  field: str
  expected: str
  actual: str
  target_path: str
  fixable: bool = False


def _sha256_file(path: Path) -> str:
  digest = hashlib.sha256()
  with path.open("rb") as handle:
    while True:
      chunk = handle.read(1024 * 1024)
      if not chunk:
        break
      digest.update(chunk)
  return digest.hexdigest()


def _sha256_text(text: str) -> str:
  return hashlib.sha256(text.encode("utf-8")).hexdigest()


def write_and_hash_json(
  path: Path,
  payload: dict[str, Any],
  *,
  ensure_ascii: bool = True,
  indent: int = 2,
  sort_keys: bool = True,
  encoding: str = "utf-8",
) -> str:
  """Write *payload* as JSON with trailing newline and return the sha256 of the written file."""
  path.parent.mkdir(parents=True, exist_ok=True)
  text = json.dumps(payload, ensure_ascii=ensure_ascii, indent=indent, sort_keys=sort_keys) + "\n"
  path.write_text(text, encoding=encoding)
  return _sha256_file(path)


def add_retained_gate_output_args(
  parser: argparse.ArgumentParser,
  *,
  retained_dir_default: Path,
  output_dir_help: str = "Directory for retained JSON artifacts.",
  stdout_help: str = "Also print the gate JSON to stdout after writing retained artifacts.",
) -> None:
  """Add the shared "always write retained gate, optionally echo" CLI options.

  Covers ``--output-dir`` (defaults to *retained_dir_default*) and
  ``--stdout``, shared verbatim by the independent-review retained-gate CLIs
  (review closeout, scope-bucket review, uncertainty review). Each caller's
  own help text stays an explicit override where it diverges from the most
  common wording.
  """
  parser.add_argument("--output-dir", type=Path, default=retained_dir_default, help=output_dir_help)
  parser.add_argument("--stdout", action="store_true", help=stdout_help)


def _display_path(path: Path, repo_root: Path) -> str:
  try:
    return path.resolve().relative_to(repo_root.resolve()).as_posix()
  except ValueError:
    return str(path)


def _is_relative_to(path: Path, base: Path) -> bool:
  try:
    path.resolve().relative_to(base.resolve())
  except ValueError:
    return False
  return True


def _iter_dict_rows(value: Any, row_path: str = "$"):
  if isinstance(value, dict):
    yield row_path, value
    for key, child in value.items():
      yield from _iter_dict_rows(child, f"{row_path}.{key}")
  elif isinstance(value, list):
    for index, child in enumerate(value):
      yield from _iter_dict_rows(child, f"{row_path}[{index}]")


def _iter_true_guards(value: Any, row_path: str = "$"):
  if isinstance(value, dict):
    for key, child in value.items():
      child_path = f"{row_path}.{key}"
      key_lower = str(key).lower()
      if (
        isinstance(child, bool)
        and child is True
        and any(term in key_lower for term in GUARD_TERMS)
        and not any(
          marker in key_lower for marker in SAFE_AGGREGATE_GUARD_MARKERS
        )
      ):
        yield child_path
      yield from _iter_true_guards(child, child_path)
  elif isinstance(value, list):
    for index, child in enumerate(value):
      yield from _iter_true_guards(child, f"{row_path}[{index}]")


def _path_field_for_row(row: dict[str, Any]) -> str | None:
  for field in PATH_FIELDS:
    value = row.get(field)
    if isinstance(value, str) and value.strip():
      return field
  return None


def _hash_fields_for_row(row: dict[str, Any]) -> list[str]:
  return [
    field
    for field in HASH_FIELDS
    if isinstance(row.get(field), str) and str(row[field]).strip()
  ]


def _resolve_manifest_target(
  *,
  path_value: str,
  path_field: str,
  manifest_path: Path,
  repo_root: Path,
) -> Path:
  # Sealed evidence artifacts record the pre-migration logical prefix; apply
  # the logical→physical translation before building a Path object.
  translated = translate_logical_a2_path(path_value)
  raw = Path(translated)
  if raw.is_absolute():
    return raw

  if path_field == "filename":
    return manifest_path.parent / raw

  repo_candidate = repo_root / raw
  if repo_candidate.exists():
    return repo_candidate

  if raw.parent == Path("."):
    return manifest_path.parent / raw

  return repo_candidate


def _normalize_hash(value: str) -> str:
  text = value.strip().lower()
  if text.startswith("sha256:"):
    return text.split(":", 1)[1]
  return text


def _hash_value_for_field(field: str, digest: str, previous_value: str) -> str:
  if field == "content_hash" and previous_value.strip().lower().startswith("sha256:"):
    return f"sha256:{digest}"
  return digest


def _collect_manifest_findings(
  *,
  manifest_path: Path,
  repo_root: Path,
  payload: dict[str, Any],
) -> tuple[list[ManifestFinding], list[ManifestFinding], list[str]]:
  missing: list[ManifestFinding] = []
  mismatches: list[ManifestFinding] = []
  guards = list(_iter_true_guards(payload))

  for row_path, row in _iter_dict_rows(payload):
    path_field = _path_field_for_row(row)
    hash_fields = _hash_fields_for_row(row)
    if path_field is None or not hash_fields:
      continue

    path_value = str(row[path_field])
    target = _resolve_manifest_target(
      path_value=path_value,
      path_field=path_field,
      manifest_path=manifest_path,
      repo_root=repo_root,
    )
    target_display = _display_path(target, repo_root)
    fixable = _is_relative_to(target, manifest_path.parent)
    if not target.is_file():
      missing.append(
        ManifestFinding(
          manifest_path=manifest_path,
          row_path=row_path,
          field=path_field,
          expected="file_exists",
          actual="missing",
          target_path=target_display,
          fixable=False,
        )
      )
      continue

    digest = _sha256_file(target)
    for hash_field in hash_fields:
      actual = str(row[hash_field])
      if _normalize_hash(actual) != digest:
        mismatches.append(
          ManifestFinding(
            manifest_path=manifest_path,
            row_path=row_path,
            field=hash_field,
            expected=digest,
            actual=actual,
            target_path=target_display,
            fixable=fixable,
          )
        )

  return missing, mismatches, guards


def _apply_manifest_fixes(
  *,
  manifest_path: Path,
  repo_root: Path,
  payload: dict[str, Any],
) -> int:
  fixed = 0
  for _, row in _iter_dict_rows(payload):
    path_field = _path_field_for_row(row)
    hash_fields = _hash_fields_for_row(row)
    if path_field is None or not hash_fields:
      continue

    target = _resolve_manifest_target(
      path_value=str(row[path_field]),
      path_field=path_field,
      manifest_path=manifest_path,
      repo_root=repo_root,
    )
    if not target.is_file() or not _is_relative_to(target, manifest_path.parent):
      continue

    digest = _sha256_file(target)
    for hash_field in hash_fields:
      previous = str(row[hash_field])
      if _normalize_hash(previous) == digest:
        continue
      row[hash_field] = _hash_value_for_field(hash_field, digest, previous)
      fixed += 1
  return fixed


def _manifest_paths(package_dir: Path) -> list[Path]:
  return sorted(package_dir.glob(DEFAULT_MANIFEST_GLOB))


def check_retained_manifest_integrity(
  *,
  repo_root: Path = REPO_ROOT,
  package_dir: Path = CANDIDATE_PACKAGE_DIR,
  manifest_paths: list[Path] | None = None,
  fix: bool = False,
) -> dict[str, Any]:
  manifests = manifest_paths if manifest_paths is not None else _manifest_paths(package_dir)
  loaded: list[tuple[Path, dict[str, Any]]] = []
  for manifest_path in manifests:
    loaded.append(
      (
        manifest_path,
        json.loads(manifest_path.read_text(encoding="utf-8")),
      )
    )

  fixed_hash_fields = 0
  if fix:
    for manifest_path, payload in loaded:
      fixed_for_manifest = _apply_manifest_fixes(
        manifest_path=manifest_path,
        repo_root=repo_root,
        payload=payload,
      )
      if fixed_for_manifest:
        manifest_path.write_text(
          json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
          encoding="utf-8",
        )
        fixed_hash_fields += fixed_for_manifest

    loaded = [
      (
        manifest_path,
        json.loads(manifest_path.read_text(encoding="utf-8")),
      )
      for manifest_path, _ in loaded
    ]

  all_missing: list[ManifestFinding] = []
  all_mismatches: list[ManifestFinding] = []
  all_guards: list[tuple[Path, str]] = []
  for manifest_path, payload in loaded:
    missing, mismatches, guards = _collect_manifest_findings(
      manifest_path=manifest_path,
      repo_root=repo_root,
      payload=payload,
    )
    all_missing.extend(missing)
    all_mismatches.extend(mismatches)
    all_guards.extend((manifest_path, guard) for guard in guards)

  return {
    "manifest_count": len(loaded),
    "missing_total": len(all_missing),
    "sha_mismatch_total": len(all_mismatches),
    "guard_true_total": len(all_guards),
    "fixed_hash_fields": fixed_hash_fields,
    "missing": [
      {
        "manifest": _display_path(finding.manifest_path, repo_root),
        "row": finding.row_path,
        "target": finding.target_path,
      }
      for finding in all_missing
    ],
    "sha_mismatches": [
      {
        "manifest": _display_path(finding.manifest_path, repo_root),
        "row": finding.row_path,
        "field": finding.field,
        "target": finding.target_path,
        "expected": finding.expected,
        "actual": finding.actual,
        "fixable": finding.fixable,
      }
      for finding in all_mismatches
    ],
    "guard_true": [
      {
        "manifest": _display_path(manifest_path, repo_root),
        "field": guard_path,
      }
      for manifest_path, guard_path in all_guards
    ],
  }


# ---------------------------------------------------------------------------
# Reverse pin index, cascade recomputation, and the CI mismatch baseline
# ---------------------------------------------------------------------------
# ``check_retained_manifest_integrity`` answers "is every pin still valid".
# Repairing a pinned file needs the inverse question -- "who pins this file" --
# because one edit invalidates every manifest field that recorded the old
# digest, and manifests pin each other, so a repair is a chain rather than a
# single field.
#
# Newline policy. The repository is checked out with ``core.autocrlf=true`` on
# Windows, so a text artifact carries CRLF on disk while the same commit
# carries LF. The sealed manifests record the LF digest and the LF byte count
# (``size_bytes``) -- the only representation two platforms agree on.
# ``_canonical_bytes`` reproduces it, and every helper added in this section
# uses it. ``_sha256_file``, ``_collect_manifest_findings`` and ``--fix`` keep
# their raw-byte semantics untouched, which is why the legacy
# ``sha_mismatch_total`` counts 109 rows on a CRLF checkout but only 9 on an LF
# one; see tests/tools/manifest_pin_baseline.json for the split.

SIZE_FIELDS = ("size_bytes",)
BINARY_SNIFF_BYTES = 8192
DEFAULT_CASCADE_ROUNDS = 16
BASELINE_HASH_PREFIX = 16

# Every retained manifest round-trips through exactly this serialisation, which
# is what lets the cascade predict a rewritten manifest's digest before
# touching the disk. A manifest that does not round-trip is refused rather than
# reformatted, because reformatting would invalidate every pin it carries.
_MANIFEST_JSON_STYLE = {"indent": 2, "ensure_ascii": True, "sort_keys": True}


def _canonical_bytes(data: bytes) -> bytes:
  """Return *data* in the platform-independent representation manifests pin.

  Text artifacts are normalised to LF. Binary artifacts are returned verbatim:
  a ``\\r\\n`` pair inside a PDF or XLSX is payload, not a line ending, and
  rewriting it would produce a digest no checkout ever reproduces.
  """
  if b"\x00" in data[:BINARY_SNIFF_BYTES]:
    return data
  return data.replace(b"\r\n", b"\n")


@dataclass(frozen=True)
class TargetDigest:
  """Both digests of one pinned file plus its canonical byte count."""

  raw_sha256: str
  canonical_sha256: str
  canonical_size: int


def _digest_bytes(data: bytes) -> TargetDigest:
  canonical = _canonical_bytes(data)
  return TargetDigest(
    raw_sha256=hashlib.sha256(data).hexdigest(),
    canonical_sha256=hashlib.sha256(canonical).hexdigest(),
    canonical_size=len(canonical),
  )


def _digest_target(path: Path) -> TargetDigest:
  return _digest_bytes(path.read_bytes())


@dataclass(frozen=True)
class PinEntry:
  """One hash-pinned manifest field and the file it points at.

  The leading five attributes are the reverse-index tuple callers ask for:
  manifest path, JSON field path, recorded digest, on-disk digest, verdict.
  """

  manifest: str
  field_path: str
  recorded_sha256: str
  actual_sha256: str
  matched: bool
  target: str
  target_exists: bool
  row_path: str
  field: str
  recorded_value: str
  canonical_sha256: str
  newline_only: bool
  size_field: str | None
  recorded_size: int | None
  canonical_size: int | None

  @property
  def key(self) -> tuple[str, str, str, str]:
    """Checkout-independent identity used by the CI mismatch baseline.

    The pinned target is part of the identity: without it, repointing a
    known-mismatched field at a different file while keeping the recorded
    digest would slip past both the new-mismatch and the repaired-entry
    checks.
    """
    return (
      self.manifest,
      self.field_path,
      self.target,
      self.recorded_sha256[:BASELINE_HASH_PREFIX],
    )


@dataclass(frozen=True)
class _PinRow:
  """A manifest row that carries both a path field and hash fields."""

  row: dict[str, Any]
  row_path: str
  path_field: str
  hash_fields: tuple[str, ...]
  size_fields: tuple[str, ...]
  target: Path
  target_display: str


def _iter_pin_rows(
  *,
  manifest_path: Path,
  repo_root: Path,
  payload: dict[str, Any],
) -> Iterator[_PinRow]:
  for row_path, row in _iter_dict_rows(payload):
    path_field = _path_field_for_row(row)
    hash_fields = tuple(_hash_fields_for_row(row))
    if path_field is None or not hash_fields:
      continue
    target = _resolve_manifest_target(
      path_value=str(row[path_field]),
      path_field=path_field,
      manifest_path=manifest_path,
      repo_root=repo_root,
    )
    yield _PinRow(
      row=row,
      row_path=row_path,
      path_field=path_field,
      hash_fields=hash_fields,
      size_fields=tuple(
        field for field in SIZE_FIELDS if isinstance(row.get(field), int)
      ),
      target=target,
      target_display=_display_path(target, repo_root),
    )


def _pin_manifest_paths(package_dir: Path, manifest_globs: Sequence[str]) -> list[Path]:
  found: set[Path] = set()
  for pattern in manifest_globs:
    found.update(package_dir.glob(pattern))
  return sorted(found)


def normalize_repo_relative(value: str, repo_root: Path = REPO_ROOT) -> str:
  """Return *value* as the repo-relative POSIX path the pin index is keyed by.

  Accepts Windows separators, absolute paths, and the retired logical prefixes
  that sealed manifests still record.
  """
  candidate = Path(translate_logical_a2_path(value.strip().replace("\\", "/")))
  if not candidate.is_absolute():
    candidate = repo_root / candidate
  return _display_path(candidate, repo_root)


def build_pin_index(
  *,
  repo_root: Path = REPO_ROOT,
  package_dir: Path = CANDIDATE_PACKAGE_DIR,
  manifest_paths: list[Path] | None = None,
  manifest_globs: Sequence[str] = (DEFAULT_MANIFEST_GLOB,),
) -> dict[str, list[PinEntry]]:
  """Return a reverse index mapping each pinned file to the pins that hold it.

  Keys are repo-relative POSIX paths after ``translate_logical_a2_path``, so a
  manifest that records a retired logical prefix indexes under the file's live
  location. Values are sorted ``PinEntry`` lists.
  """
  manifests = (
    manifest_paths
    if manifest_paths is not None
    else _pin_manifest_paths(package_dir, manifest_globs)
  )

  digests: dict[str, TargetDigest | None] = {}
  index: dict[str, list[PinEntry]] = {}
  for manifest_path in manifests:
    manifest_display = _display_path(manifest_path, repo_root)
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    for pin_row in _iter_pin_rows(
      manifest_path=manifest_path,
      repo_root=repo_root,
      payload=payload,
    ):
      if pin_row.target_display not in digests:
        digests[pin_row.target_display] = (
          _digest_target(pin_row.target) if pin_row.target.is_file() else None
        )
      digest = digests[pin_row.target_display]
      size_field = pin_row.size_fields[0] if pin_row.size_fields else None
      for hash_field in pin_row.hash_fields:
        recorded_value = str(pin_row.row[hash_field])
        recorded = _normalize_hash(recorded_value)
        raw = digest.raw_sha256 if digest else ""
        canonical = digest.canonical_sha256 if digest else ""
        matched = digest is not None and recorded in {raw, canonical}
        index.setdefault(pin_row.target_display, []).append(
          PinEntry(
            manifest=manifest_display,
            field_path=f"{pin_row.row_path}.{hash_field}",
            recorded_sha256=recorded,
            actual_sha256=raw,
            matched=matched,
            target=pin_row.target_display,
            target_exists=digest is not None,
            row_path=pin_row.row_path,
            field=hash_field,
            recorded_value=recorded_value,
            canonical_sha256=canonical,
            newline_only=matched and recorded != raw,
            size_field=size_field,
            recorded_size=pin_row.row.get(size_field) if size_field else None,
            canonical_size=digest.canonical_size if digest else None,
          )
        )

  return {
    target: sorted(entries, key=lambda entry: (entry.manifest, entry.field_path))
    for target, entries in sorted(index.items())
  }


def iter_pin_entries(index: dict[str, list[PinEntry]]) -> Iterator[PinEntry]:
  """Yield every pin in *index* in stable (target, manifest, field) order."""
  for target in sorted(index):
    yield from index[target]


def who_pins(target: str, index: dict[str, list[PinEntry]]) -> list[PinEntry]:
  """Return every pin holding *target*, which may be any accepted path spelling."""
  return list(index.get(normalize_repo_relative(target), ()))


def _format_pin_entry(entry: PinEntry) -> str:
  if not entry.target_exists:
    verdict, detail = "MISSING", "target file does not exist"
  elif not entry.matched:
    verdict = "MISMATCH"
    detail = f"on disk raw={entry.actual_sha256[:16]} canonical={entry.canonical_sha256[:16]}"
  elif entry.newline_only:
    verdict = "match"
    detail = (
      f"canonical={entry.canonical_sha256[:16]}; on-disk CRLF digest "
      f"{entry.actual_sha256[:16]} differs by newline representation only"
    )
  else:
    verdict, detail = "match", f"on disk {entry.actual_sha256[:16]}"

  lines = [
    f"[{verdict}] {entry.manifest}",
    f"          field    {entry.field_path}",
    f"          recorded {entry.recorded_sha256[:16]}  ({detail})",
  ]
  if entry.size_field is not None and entry.canonical_size is not None:
    size_verdict = "ok" if entry.recorded_size == entry.canonical_size else "STALE"
    lines.append(
      f"          {entry.size_field}  {entry.recorded_size} "
      f"(canonical {entry.canonical_size}) [{size_verdict}]"
    )
  return "\n".join(lines)


def format_who_pins(
  target: str,
  index: dict[str, list[PinEntry]],
  *,
  manifest_count: int,
) -> str:
  """Render the ``--who-pins`` report for *target*."""
  resolved = normalize_repo_relative(target)
  entries = who_pins(target, index)
  matched = sum(1 for entry in entries if entry.matched)
  lines = [
    f"pin index: {manifest_count} manifests, "
    f"{sum(len(rows) for rows in index.values())} pinned hash fields, "
    f"{len(index)} distinct targets",
    f"target: {resolved}",
    f"pins: {len(entries)} (match {matched} / mismatch {len(entries) - matched})",
  ]
  if not entries:
    lines.append("no manifest in the scanned inventory pins this path")
  lines.extend(_format_pin_entry(entry) for entry in entries)
  return "\n".join(lines)


def _serialize_manifest(payload: dict[str, Any]) -> str:
  return json.dumps(payload, **_MANIFEST_JSON_STYLE) + "\n"


@dataclass
class _ManifestState:
  """In-memory view of one manifest during a cascade."""

  path: Path
  display: str
  payload: dict[str, Any]
  round_trips: bool
  dirty: bool = False

  def canonical_text(self) -> str:
    return _serialize_manifest(self.payload)

  def digest(self) -> TargetDigest:
    return _digest_bytes(self.canonical_text().encode("utf-8"))


def _load_manifest_state(manifest_path: Path, repo_root: Path) -> _ManifestState:
  text = _canonical_bytes(manifest_path.read_bytes()).decode("utf-8")
  payload = json.loads(text)
  return _ManifestState(
    path=manifest_path,
    display=_display_path(manifest_path, repo_root),
    payload=payload,
    round_trips=_serialize_manifest(payload) == text,
  )


def plan_pin_cascade(
  target: str,
  *,
  repo_root: Path = REPO_ROOT,
  package_dir: Path = CANDIDATE_PACKAGE_DIR,
  manifest_paths: list[Path] | None = None,
  manifest_globs: Sequence[str] = (DEFAULT_MANIFEST_GLOB,),
  write: bool = False,
  max_rounds: int = DEFAULT_CASCADE_ROUNDS,
) -> dict[str, Any]:
  """Recompute every pin reachable from *target* and report the plan.

  Walks the transitive closure: pins of *target* are re-derived from the file's
  canonical bytes, a manifest that had to change joins the closure because it
  is itself a pinned artifact, and the walk repeats until nothing changes.
  Nothing touches the disk unless *write* is true, and a write is refused
  outright when any manifest in the closure cannot be reserialised byte-for-byte.
  """
  manifests = (
    manifest_paths
    if manifest_paths is not None
    else _pin_manifest_paths(package_dir, manifest_globs)
  )
  states = {
    state.display: state
    for state in (_load_manifest_state(path, repo_root) for path in manifests)
  }

  root = normalize_repo_relative(target, repo_root)
  affected = {root}
  edits: list[dict[str, Any]] = []
  already_current: list[dict[str, Any]] = []
  reported_current: set[tuple[str, str]] = set()
  errors: list[str] = []
  rounds = 0
  closed = False

  root_path = repo_root / root
  if not root_path.is_file() and root not in states:
    errors.append(f"cascade target does not exist: {root}")

  def digest_for(display: str, path: Path) -> TargetDigest | None:
    state = states.get(display)
    if state is not None:
      if state.dirty:
        # A manifest this cascade already edited will be written back in
        # canonical form, so upstream pins must record the digest of those
        # future bytes.
        return state.digest()
      # An untouched manifest is pinned by its on-disk bytes. Hashing the
      # reserialised payload instead would record a digest that exists
      # nowhere on disk whenever the manifest does not round-trip.
      return _digest_target(state.path) if state.path.is_file() else None
    return _digest_target(path) if path.is_file() else None

  while rounds < max_rounds:
    rounds += 1
    changed = False
    for display in sorted(states):
      state = states[display]
      for pin_row in _iter_pin_rows(
        manifest_path=state.path,
        repo_root=repo_root,
        payload=state.payload,
      ):
        if pin_row.target_display not in affected:
          continue
        digest = digest_for(pin_row.target_display, pin_row.target)
        if digest is None:
          message = f"{display}: pinned target is missing: {pin_row.target_display}"
          if message not in errors:
            errors.append(message)
          continue

        updates: list[tuple[str, Any, Any]] = []
        for hash_field in pin_row.hash_fields:
          previous = str(pin_row.row[hash_field])
          if _normalize_hash(previous) == digest.canonical_sha256:
            continue
          updates.append(
            (
              hash_field,
              previous,
              _hash_value_for_field(hash_field, digest.canonical_sha256, previous),
            )
          )
        for size_field in pin_row.size_fields:
          if pin_row.row[size_field] != digest.canonical_size:
            updates.append((size_field, pin_row.row[size_field], digest.canonical_size))

        if not updates:
          # A row can be revisited on later rounds once it is already correct;
          # report it once so the plan stays readable.
          if (display, pin_row.row_path) not in reported_current:
            reported_current.add((display, pin_row.row_path))
            already_current.append(
              {
                "manifest": display,
                "row": pin_row.row_path,
                "target": pin_row.target_display,
                "fields": list(pin_row.hash_fields) + list(pin_row.size_fields),
              }
            )
          continue

        if not state.round_trips:
          message = (
            f"{display}: cannot be reserialised byte-for-byte; refusing to "
            "rewrite pins in it"
          )
          if message not in errors:
            errors.append(message)
          continue

        for field, old, new in updates:
          pin_row.row[field] = new
          edits.append(
            {
              "round": rounds,
              "manifest": display,
              "field_path": f"{pin_row.row_path}.{field}",
              "target": pin_row.target_display,
              "old": old,
              "new": new,
            }
          )
        state.dirty = True
        changed = True
        affected.add(display)

    if not changed:
      closed = True
      break

  written: list[str] = []
  if write and not errors:
    for display in sorted(states):
      state = states[display]
      if not state.dirty:
        continue
      state.path.write_text(state.canonical_text(), encoding="utf-8", newline="\n")
      written.append(display)

  return {
    "target": root,
    "mode": "write" if write else "dry-run",
    "manifest_count": len(states),
    "rounds": rounds,
    "closed": closed,
    "edits": edits,
    "already_current": already_current,
    "written_manifests": written,
    "errors": errors,
  }


def format_cascade_plan(plan: dict[str, Any]) -> str:
  """Render ``plan_pin_cascade`` output as a step-by-step operator report."""
  lines = [
    f"cascade target: {plan['target']}",
    f"mode: {plan['mode']} | manifests scanned: {plan['manifest_count']} | "
    f"rounds: {plan['rounds']}",
  ]
  for row in plan["already_current"]:
    lines.append(f"[current] {row['manifest']}  {row['row']}  -> {row['target']}")
  for edit in plan["edits"]:
    old = str(edit["old"])
    new = str(edit["new"])
    if len(old) > 24:
      old, new = old[:24] + "...", new[:24] + "..."
    lines.append(
      f"[round {edit['round']}] {edit['manifest']}  {edit['field_path']}  "
      f"{old} -> {new}"
    )
  if not plan["edits"]:
    lines.append("no field required an update; the pin chain for this target is closed")
  elif plan["mode"] == "dry-run":
    lines.append(
      f"{len(plan['edits'])} field(s) would change; re-run with --write to apply"
    )
  for manifest in plan["written_manifests"]:
    lines.append(f"[written] {manifest}")
  if not plan["closed"]:
    lines.append("WARNING: the cascade did not converge within the round limit")
  for error in plan["errors"]:
    lines.append(f"ERROR: {error}")
  return "\n".join(lines)


def classify_pin_mismatches(
  index: dict[str, list[PinEntry]],
) -> dict[str, list[PinEntry]]:
  """Split the index into the two mismatch tiers the CI baseline tracks.

  ``content`` pins disagree with the file under every newline representation
  and are checkout-independent. ``newline`` pins hold the committed LF digest
  while the working tree carries CRLF; they are what the legacy raw-byte
  counter reports on Windows and not on Linux.
  """
  content: list[PinEntry] = []
  newline: list[PinEntry] = []
  for entry in iter_pin_entries(index):
    if not entry.matched:
      content.append(entry)
    elif entry.newline_only:
      newline.append(entry)
  return {"content": content, "newline": newline}


def _baseline_row(entry: PinEntry, *, include_observed: bool) -> dict[str, Any]:
  row = {
    "manifest": entry.manifest,
    "field_path": entry.field_path,
    "target": entry.target,
    "recorded_prefix": entry.recorded_sha256[:BASELINE_HASH_PREFIX],
  }
  if include_observed:
    row["observed_prefix"] = entry.canonical_sha256[:BASELINE_HASH_PREFIX]
  return row


def build_pin_baseline(
  *,
  repo_root: Path = REPO_ROOT,
  package_dir: Path = CANDIDATE_PACKAGE_DIR,
  manifest_globs: Sequence[str] = (DEFAULT_MANIFEST_GLOB,),
  generated_on: str,
) -> dict[str, Any]:
  """Build the shrink-only mismatch baseline consumed by the CI guard test."""
  manifests = _pin_manifest_paths(package_dir, manifest_globs)
  index = build_pin_index(
    repo_root=repo_root,
    package_dir=package_dir,
    manifest_globs=manifest_globs,
  )
  tiers = classify_pin_mismatches(index)
  return {
    "schema_version": 1,
    "generated_on": generated_on,
    "generated_by": (
      "python tools/maintenance/retained_artifacts/manifest_integrity.py "
      "--pin-baseline"
    ),
    "packet": _display_path(package_dir, repo_root),
    "policy": (
      "Shrink-only. tests/tools/test_manifest_pin_baseline.py fails when a "
      "measured mismatch is absent from this file (a newly broken pin) and "
      "when a listed mismatch is no longer measured (a repaired pin whose "
      "line must be deleted here in the same change)."
    ),
    "tiers": {
      "content_mismatches": (
        "The recorded digest matches the target under no newline "
        "representation. Checkout-independent: identical on CRLF and LF "
        "working trees."
      ),
      "newline_representation_mismatches": (
        "The recorded digest is the committed LF digest, which the raw-byte "
        "checker in check_retained_manifest_integrity() cannot reproduce from "
        "a CRLF working tree. Present on Windows checkouts "
        "(core.autocrlf=true), absent on Linux CI."
      ),
    },
    "manifest_globs": list(manifest_globs),
    "manifest_count": len(manifests),
    "pin_total": sum(len(rows) for rows in index.values()),
    "target_total": len(index),
    "content_mismatch_total": len(tiers["content"]),
    "newline_representation_total": len(tiers["newline"]),
    "legacy_raw_mismatch_total": len(tiers["content"]) + len(tiers["newline"]),
    "content_mismatches": [
      _baseline_row(entry, include_observed=True) for entry in tiers["content"]
    ],
    "newline_representation_mismatches": [
      _baseline_row(entry, include_observed=False) for entry in tiers["newline"]
    ],
  }


def _summary_failed(summary: dict[str, Any]) -> bool:
  # An empty inventory is a failure, not a pass. When the production package
  # directory is renamed or pruned without updating a2_packet_paths.py, the
  # manifest glob matches nothing and every counter below reads zero -- a
  # "clean" result that verified no artifact at all.
  if summary["manifest_count"] == 0:
    return True
  return any(
    summary[field] != 0
    for field in ("missing_total", "sha_mismatch_total", "guard_true_total")
  )


def main(argv: list[str] | None = None) -> int:
  parser = argparse.ArgumentParser(
    description="Check retained damage-model candidate manifest artifact integrity."
  )
  parser.add_argument(
    "--package-dir",
    type=Path,
    default=CANDIDATE_PACKAGE_DIR,
    help=(
      "Candidate package directory to scan. Defaults to the retained A2 "
      "packet under its owner root."
    ),
  )
  parser.add_argument(
    "--fix",
    action="store_true",
    help=(
      "Update mismatched hash fields only when the referenced artifact is "
      "inside the manifest directory."
    ),
  )
  parser.add_argument(
    "--pin-glob",
    action="append",
    dest="pin_globs",
    metavar="GLOB",
    help=(
      "Extra glob (relative to --package-dir) whose JSON files also carry "
      "pins, for --who-pins/--cascade/--pin-baseline. Repeatable. Defaults to "
      f"{DEFAULT_MANIFEST_GLOB!r}; widen it to reach companion gate files that "
      "sit beside a manifest."
    ),
  )
  parser.add_argument(
    "--who-pins",
    metavar="PATH",
    help=(
      "Report every manifest field that hash-pins the repo-relative PATH, "
      "with its match status, then exit without running the full scan."
    ),
  )
  parser.add_argument(
    "--cascade",
    metavar="PATH",
    help=(
      "Recompute every pin reachable from the repo-relative PATH, recursing "
      "through manifests that are themselves pinned until the chain closes. "
      "Prints a plan and changes nothing unless --write is given."
    ),
  )
  parser.add_argument(
    "--write",
    action="store_true",
    help="Apply the --cascade plan instead of printing it as a dry run.",
  )
  parser.add_argument(
    "--pin-baseline",
    action="store_true",
    help=(
      "Print the shrink-only pin mismatch baseline JSON tracked by "
      "tests/tools/manifest_pin_baseline.json, then exit."
    ),
  )
  parser.add_argument(
    "--generated-on",
    metavar="YYYY-MM-DD",
    help="Value recorded in the --pin-baseline 'generated_on' field.",
  )
  args = parser.parse_args(argv)
  pin_globs = tuple(args.pin_globs or (DEFAULT_MANIFEST_GLOB,))

  if args.who_pins is not None:
    index = build_pin_index(package_dir=args.package_dir, manifest_globs=pin_globs)
    entries = who_pins(args.who_pins, index)
    print(
      format_who_pins(
        args.who_pins,
        index,
        manifest_count=len(_pin_manifest_paths(args.package_dir, pin_globs)),
      )
    )
    return 0 if entries and all(entry.matched for entry in entries) else 1

  if args.cascade is not None:
    plan = plan_pin_cascade(
      args.cascade,
      package_dir=args.package_dir,
      manifest_globs=pin_globs,
      write=args.write,
    )
    print(format_cascade_plan(plan))
    return 1 if plan["errors"] or not plan["closed"] else 0

  if args.pin_baseline:
    baseline = build_pin_baseline(
      package_dir=args.package_dir,
      manifest_globs=pin_globs,
      generated_on=args.generated_on or "unspecified",
    )
    print(json.dumps(baseline, indent=2, ensure_ascii=True, sort_keys=False))
    return 0

  summary = check_retained_manifest_integrity(
    package_dir=args.package_dir,
    fix=args.fix,
  )
  print(json.dumps(summary, indent=2, ensure_ascii=False))
  if summary["manifest_count"] == 0:
    print(
      f"error: no manifests matched {DEFAULT_MANIFEST_GLOB!r} under "
      f"{args.package_dir}; refusing to report a clean scan of an empty "
      "inventory.",
      file=sys.stderr,
    )
  return 1 if _summary_failed(summary) else 0


if __name__ == "__main__":
  raise SystemExit(main())
