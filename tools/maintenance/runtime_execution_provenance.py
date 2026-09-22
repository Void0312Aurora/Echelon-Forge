"""Collect and verify RunReceipt bindings from observed execution material."""

from __future__ import annotations

import hashlib
import json
import platform
import sys
import sysconfig
from collections.abc import Iterator
from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping


class ExecutionProvenanceError(ValueError):
  """Raised when actual execution material cannot be measured safely."""


def _sha256_bytes(payload: bytes) -> str:
  return hashlib.sha256(payload).hexdigest()


MEASURED_SECTIONS = ("executable", "package", "platform", "inputs")
_OBSERVATION_TOKEN = object()


@dataclass(frozen=True)
class ExecutionObservation(Mapping[str, Any]):
  """Collector-issued execution observation accepted by the ledger.

  The private token prevents a caller from substituting an arbitrary mapping
  at the finalization boundary. Nested values are copied on construction and
  access so later caller mutation cannot rewrite the observation.
  """

  _values: dict[str, Any]
  _token: object = field(repr=False, compare=False)

  def __post_init__(self) -> None:
    if self._token is not _OBSERVATION_TOKEN:
      raise ExecutionProvenanceError("execution observations must come from the collector")
    object.__setattr__(self, "_values", deepcopy(self._values))

  def __getitem__(self, key: str) -> Any:
    return deepcopy(self._values[key])

  def __iter__(self) -> Iterator[str]:
    return iter(self._values)

  def __len__(self) -> int:
    return len(self._values)


def _observation(values: Mapping[str, Any]) -> ExecutionObservation:
  return ExecutionObservation(dict(values), _OBSERVATION_TOKEN)


def observed_measurement_sha256(observed: Mapping[str, Any]) -> str:
  """Digest the byte-backed provenance sections in their canonical order."""

  try:
    material = {section: observed[section] for section in MEASURED_SECTIONS}
  except KeyError as error:
    raise ExecutionProvenanceError(f"measured provenance section is absent: {error.args[0]}") from error
  canonical = json.dumps(
    material, ensure_ascii=False, separators=(",", ":"), sort_keys=True,
  ).encode("utf-8")
  return _sha256_bytes(canonical)


def sha256_file(path: str | Path) -> str:
  candidate = Path(path)
  if not candidate.is_file():
    raise ExecutionProvenanceError(f"provenance file is absent: {candidate}")
  digest = hashlib.sha256()
  with candidate.open("rb") as stream:
    for chunk in iter(lambda: stream.read(1024 * 1024), b""):
      digest.update(chunk)
  return digest.hexdigest()


def sha256_path(path: str | Path) -> str:
  candidate = Path(path)
  if candidate.is_file():
    return sha256_file(candidate)
  if not candidate.is_dir():
    raise ExecutionProvenanceError(f"provenance path is absent: {candidate}")
  entries: list[dict[str, str]] = []
  for child in sorted(candidate.rglob("*")):
    if child.is_file():
      entries.append({
        "path": child.relative_to(candidate).as_posix(),
        "sha256": sha256_file(child),
      })
  if not entries:
    raise ExecutionProvenanceError(f"provenance directory is empty: {candidate}")
  canonical = json.dumps(entries, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
  return _sha256_bytes(canonical)


def _digest_map(paths: Mapping[str, str | Path], field: str) -> dict[str, str]:
  if not paths:
    raise ExecutionProvenanceError(f"{field} must contain at least one observed path")
  result: dict[str, str] = {}
  for identity in sorted(paths):
    if not isinstance(identity, str) or not identity:
      raise ExecutionProvenanceError(f"{field} contains an invalid identity")
    result[identity] = sha256_path(paths[identity])
  return result


def collect_actual_bindings(
  *,
  executable_path: str | Path,
  executable_identity: str,
  executable_version: str,
  package_path: str | Path,
  package_identity: str,
  package_version: str,
  wheel_path: str | Path,
  native_module_paths: Mapping[str, str | Path],
  plugin_paths: Mapping[str, str | Path] | None = None,
  runtime_dependency_paths: Mapping[str, str | Path] | None = None,
  input_artifact_paths: Mapping[str, str | Path] | None = None,
  gpu: str | None = None,
  driver: str | None = None,
  compiler: str | None = None,
  standard_library: str | None = None,
) -> ExecutionObservation:
  """Return receipt fragments backed by bytes and host observations.

  Required paths are measured at collection time. GPU/driver are explicit
  inputs because this local collector cannot safely infer an installed device
  or driver identity on every supported Windows/Linux host.
  """

  for value, field in (
    (executable_identity, "executable_identity"), (executable_version, "executable_version"),
    (package_identity, "package_identity"), (package_version, "package_version"),
  ):
    if not isinstance(value, str) or not value:
      raise ExecutionProvenanceError(f"{field} is required")
  if not gpu or not driver:
    raise ExecutionProvenanceError("gpu and driver observations are required")

  native_digests = _digest_map(native_module_paths, "native_module_paths")
  plugin_digests = _digest_map(plugin_paths or {"none": executable_path}, "plugin_paths") if plugin_paths else {}
  dependency_digests = _digest_map(runtime_dependency_paths or {}, "runtime_dependency_paths")
  input_digests = _digest_map(input_artifact_paths or {}, "input_artifact_paths")
  dependency_graph = _sha256_bytes(
    json.dumps(dependency_digests, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
  )
  package_digest = sha256_path(package_path)
  wheel_digest = sha256_file(wheel_path)
  host_os = platform.system().lower()
  architecture = platform.machine().lower()
  cpu = platform.processor() or architecture
  if not cpu:
    raise ExecutionProvenanceError("CPU observation is unavailable")
  observed = {
    "executable": {
      "identity": executable_identity,
      "version": executable_version,
      "digest": sha256_path(executable_path),
      "native_module_digests": native_digests,
      "plugin_digests": plugin_digests,
    },
    "package": {
      "identity": package_identity,
      "version": package_version,
      "digest": package_digest,
      "wheel_digest": wheel_digest,
      "dependency_graph_sha256": dependency_graph,
    },
    "platform": {
      "os": host_os,
      "architecture": architecture,
      "compiler": compiler or platform.python_compiler(),
      "standard_library": standard_library or f"{platform.python_implementation()}-{sys.version_info.major}.{sys.version_info.minor}",
      "cpu": cpu,
      "gpu": gpu,
      "driver": driver,
      "runtime_dependency_digests": dependency_digests,
    },
    "inputs": {"artifacts": input_digests},
  }
  observed["observed_measurement_sha256"] = observed_measurement_sha256(observed)
  return _observation(observed)


def verify_actual_bindings(
  receipt_payload: Mapping[str, Any], observed: ExecutionObservation,
) -> None:
  """Reject a receipt whose measured execution facts do not match.

  Completed receipts must carry observations for both byte-level provenance and
  runtime semantics. Keeping these as one typed observation object prevents a
  caller from supplying only the easy executable/package subset and calling the
  result "actual".
  """

  if not isinstance(observed, ExecutionObservation):
    raise ExecutionProvenanceError("actual execution provenance is not collector-issued")
  required_sections = MEASURED_SECTIONS
  missing = [section for section in required_sections if section not in observed]
  if missing:
    raise ExecutionProvenanceError(
      "observed execution is incomplete: " + ",".join(missing)
    )
  expected_measurement = observed_measurement_sha256(observed)
  if observed.get("observed_measurement_sha256") != expected_measurement:
    raise ExecutionProvenanceError("observed byte provenance digest is inconsistent")
  for section in required_sections:
    expected = observed[section]
    actual = (
      {"artifacts": receipt_payload["inputs"]["artifacts"]}
      if section == "inputs"
      else receipt_payload[section]
    )
    if actual != expected:
      raise ExecutionProvenanceError(f"receipt {section} differs from observed execution")
