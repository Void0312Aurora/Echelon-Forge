"""Opt-in resolved experiment input-lock prototype.

The lock is a static, non-authoritative projection of an Experiment and its
referenced inputs.  It never replaces native composition identity or a
RunReceipt.  Its purpose is to make dependency closure and comparison rules
inspectable before a run is claimed comparable.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from python.experiment.composition import compose_config, thaw_json_value
from python.experiment.definition import Experiment, ExperimentRegistry

SCHEMA_VERSION = "echelon_forge.resolved_experiment.v1"
_LOCK_STATES = frozenset({"static_candidate", "completed", "failed", "unknown"})
_TERMINAL_COMPARABLE_STATE = "completed"


class InputLockError(ValueError):
    """Raised when a resolved input-lock cannot be constructed safely."""


def _canonical(value: Any) -> Any:
    """Return JSON-safe data with mapping order removed from identity."""

    if isinstance(value, Mapping):
        return {str(key): _canonical(child) for key, child in sorted(value.items(), key=lambda item: str(item[0]))}
    if isinstance(value, (list, tuple)):
        return [_canonical(child) for child in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    raise TypeError(f"input-lock value is not JSON-compatible: {type(value).__name__}")


def canonical_json_bytes(value: Any) -> bytes:
    """Serialize a lock component using stable JSON rules."""

    return json.dumps(
        _canonical(value),
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
    ).encode("utf-8")


def _digest(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def _scenario_projection(experiment: Experiment, repo_root: str | Path | None) -> dict[str, Any]:
    projection: dict[str, Any] = {"path": experiment.scenario.path}
    if repo_root is None:
        return projection
    path = Path(repo_root) / experiment.scenario.path
    if not path.is_file():
        raise InputLockError(f"scenario reference does not exist: {experiment.scenario.path}")
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise InputLockError(f"scenario reference is not valid JSON: {experiment.scenario.path}") from exc
    projection["content_digest"] = _digest(document)
    return projection


def _sorted_dependency_refs(dependencies: Mapping[str, Any] | None) -> dict[str, Any]:
    if dependencies is None:
        return {}
    if not isinstance(dependencies, Mapping):
        raise TypeError("dependencies must be a mapping of logical id to digest/reference")
    result: dict[str, Any] = {}
    for logical_id, reference in dependencies.items():
        if not isinstance(logical_id, str) or not logical_id.strip():
            raise InputLockError("dependency logical ids must be non-empty strings")
        if isinstance(reference, Mapping):
            result[logical_id] = dict(reference)
        elif isinstance(reference, str) and reference.strip():
            result[logical_id] = reference
        else:
            raise InputLockError(f"dependency {logical_id!r} has no usable reference")
    return result


@dataclass(frozen=True)
class ResolvedInputLock:
    """Immutable candidate lock plus its canonical identity digest."""

    document: Mapping[str, Any]
    identity_digest: str

    @property
    def status(self) -> str:
        return str(self.document["status"])

    @property
    def digest(self) -> str:
        return self.identity_digest

    def as_dict(self) -> dict[str, Any]:
        return thaw_json_value(self.document)


def build_resolved_input_lock(
    experiment: Experiment,
    registry: ExperimentRegistry,
    *,
    repo_root: str | Path | None = None,
    effective_seeds: Sequence[int] | None = None,
    dependencies: Mapping[str, Any] | None = None,
    native_runtime: Mapping[str, Any] | None = None,
    policy: Mapping[str, Any] | None = None,
    force_package: Mapping[str, Any] | None = None,
    mechanism: Mapping[str, Any] | None = None,
    provenance: Mapping[str, Any] | None = None,
    status: str = "static_candidate",
) -> ResolvedInputLock:
    """Build a static lock without changing any runtime or report authority.

    Empty declared seeds are rejected unless ``effective_seeds`` is supplied;
    the bootstrap default is recorded by the caller rather than guessed here.
    ``repo_root`` is optional so callers can construct a non-running candidate
    from references alone, while a supplied root verifies and canonicalizes the
    referenced scenario document.
    """

    if not isinstance(experiment, Experiment):
        raise TypeError("experiment must be an Experiment")
    if not isinstance(registry, ExperimentRegistry):
        raise TypeError("registry must be an ExperimentRegistry")
    if status not in _LOCK_STATES:
        raise InputLockError(f"unsupported input-lock status: {status!r}")
    try:
        base = registry.config_base(experiment.config.base_id)
        protocol = registry.evaluation_protocol(experiment.evaluation_protocol)
    except KeyError as exc:
        raise InputLockError(str(exc)) from exc

    seeds = tuple(experiment.seeds.values if effective_seeds is None else effective_seeds)
    if not seeds:
        raise InputLockError("effective_seed_set_required: empty declared seeds need an explicit effective_seeds")
    if any(isinstance(seed, bool) or not isinstance(seed, int) or seed < 0 for seed in seeds):
        raise InputLockError("effective seeds must be non-negative integers")
    if tuple(sorted(set(seeds))) != seeds:
        raise InputLockError("effective seeds must be sorted and unique")

    scenario = _scenario_projection(experiment, repo_root)
    config = compose_config(base, experiment.config.delta)
    input_lock = {
        "scenario": scenario,
        "config": config,
        "dependencies": _sorted_dependency_refs(dependencies),
        "force_package": force_package or {},
        "mechanism": mechanism or {},
        "policy": policy or {},
        "effective_seed_set": list(seeds),
        "evaluation_protocol": {
            "name": protocol.name,
            "description": protocol.description,
        },
    }
    native = dict(native_runtime or {})
    document = {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "experiment_ref": experiment.experiment_id,
        "intent": {
            "scenario_ref": experiment.scenario.path,
            "config_base_id": experiment.config.base_id,
            "declared_seed_set": list(experiment.seeds.values),
            "evaluation_protocol": experiment.evaluation_protocol,
        },
        "input_lock": input_lock,
        "native_runtime": native,
        "provenance": dict(provenance or {}),
    }
    # The digest is over the lock and native references, never over status or
    # report-only provenance.  This keeps a candidate and an observed receipt
    # tied to the same inputs without pretending they are the same evidence.
    identity_payload = {"input_lock": input_lock, "native_runtime": native}
    return ResolvedInputLock(document=document, identity_digest=_digest(identity_payload))


@dataclass(frozen=True)
class ComparisonResult:
    comparable: bool
    differences: tuple[str, ...]
    reason: str


def compare_resolved_input_locks(
    left: ResolvedInputLock,
    right: ResolvedInputLock,
    *,
    intentional_axes: frozenset[str] = frozenset(),
) -> ComparisonResult:
    """Compare completed locks without treating hashes as scientific validity."""

    if left.status != _TERMINAL_COMPARABLE_STATE or right.status != _TERMINAL_COMPARABLE_STATE:
        return ComparisonResult(False, ("status",), "only completed runs are ordinarily comparable")
    left_data = left.as_dict()
    right_data = right.as_dict()
    differences: list[str] = []
    for axis in ("scenario", "config", "dependencies", "force_package", "mechanism", "policy", "effective_seed_set", "evaluation_protocol"):
        if left_data["input_lock"][axis] != right_data["input_lock"][axis] and axis not in intentional_axes:
            differences.append(axis)
    if left_data["native_runtime"].get("realized_topology_digest") != right_data["native_runtime"].get("realized_topology_digest"):
        differences.append("realized_topology_digest")
    if differences:
        return ComparisonResult(False, tuple(sorted(set(differences))), "unexplained truth-affecting input differences")
    return ComparisonResult(True, (), "same resolved inputs and realized topology")


__all__ = [
    "ComparisonResult",
    "InputLockError",
    "ResolvedInputLock",
    "SCHEMA_VERSION",
    "build_resolved_input_lock",
    "canonical_json_bytes",
    "compare_resolved_input_locks",
]
