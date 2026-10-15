"""Opt-in resolved experiment input-lock prototype.

The lock is a static, non-authoritative projection of an Experiment and its
referenced inputs.  It never replaces native composition identity or a
RunReceipt.  Its purpose is to make dependency closure and comparison rules
inspectable before a run is claimed comparable.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from python.experiment.composition import compose_config
from python.json_value import freeze_json_mapping, thaw_json_value
from python.experiment.definition import Experiment, ExperimentRegistry
from python.tasking_contracts.failure_domains import BatchOperationOutcome, BatchResult

SCHEMA_VERSION = "echelon_forge.resolved_experiment.v1"
_LOCK_STATES = frozenset({"static_candidate", "completed", "failed", "unknown"})
_TERMINAL_COMPARABLE_STATE = "completed"
_REQUIRED_NATIVE_IDENTITY_FIELDS = (
    "resolved_manifest_sha256",
    "executable_graph_sha256",
    "realized_topology_digest",
)
_RECEIPT_BINDING_FIELDS = (
    "receipt_id",
    "run_id",
    "attempt_id",
    "host_boot_id",
    "writer_generation",
    "backend_system_graph_sha256",
    "native_validation_evidence_sha256",
    "durable_ack",
)
_COMPLETION_EVIDENCE_FIELDS = frozenset(
    {"receipt_id", "receipt_sha256", "terminal_state", "outcome", "receipt_binding", "world_scope"}
)


class InputLockError(ValueError):
    """Raised when a resolved input-lock cannot be constructed safely."""


def _canonical(value: Any) -> Any:
    """Return JSON-safe data with mapping order removed from identity."""

    if isinstance(value, Mapping):
        if any(not isinstance(key, str) or not key for key in value):
            raise TypeError("input-lock keys must be non-empty strings")
        return {key: _canonical(child) for key, child in sorted(value.items())}
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


def _completion_evidence_is_structurally_complete(value: Any) -> bool:
    """Check the exact shape emitted by ``join_run_receipt``.

    This is deliberately a structural gate. Receipt schema validation and
    host durability remain owned by ``validate_run_receipt`` and the runtime
    host; the comparator must nevertheless reject an arbitrary truthy mapping
    supplied by a caller as completed evidence.
    """

    if not isinstance(value, Mapping) or set(value) != _COMPLETION_EVIDENCE_FIELDS:
        return False
    if not isinstance(value["receipt_id"], str) or not value["receipt_id"].strip():
        return False
    if not isinstance(value["receipt_sha256"], str) or re.fullmatch(
        r"[0-9a-f]{64}", value["receipt_sha256"]
    ) is None:
        return False
    if value["terminal_state"] != "completed":
        return False
    outcome = value["outcome"]
    if not isinstance(outcome, Mapping) or outcome.get("result") != "completed":
        return False
    binding = value["receipt_binding"]
    if not isinstance(binding, Mapping) or set(binding) != set(_RECEIPT_BINDING_FIELDS):
        return False
    if binding.get("durable_ack") is not True:
        return False
    if binding.get("receipt_id") != value["receipt_id"]:
        return False
    for field in (
        "receipt_id",
        "run_id",
        "attempt_id",
        "host_boot_id",
        "writer_generation",
    ):
        if not isinstance(binding.get(field), str) or not binding[field].strip():
            return False
    for field in ("backend_system_graph_sha256", "native_validation_evidence_sha256"):
        if not isinstance(binding.get(field), str) or re.fullmatch(
            r"[0-9a-f]{64}", binding[field]
        ) is None:
            return False
    scope = value["world_scope"]
    if not isinstance(scope, Mapping) or set(scope) != {
        "host_boot_id", "incarnation_epoch", "world_epoch", "world_ids", "bindings"
    } or scope["host_boot_id"] != binding["host_boot_id"]:
        return False
    try:
        _validate_world_bindings(scope["bindings"], scope, outcome["expected_world_indices"])
        worlds = outcome["worlds"]
        if not isinstance(worlds, (list, tuple)) or any(
            not isinstance(world, Mapping) or world.get("state") != "completed"
            or world.get("step_committed") is not True
            or type(world.get("world_index")) is not int for world in worlds
        ):
            return False
        if sorted(world["world_index"] for world in worlds) != outcome["expected_world_indices"]:
            return False
    except (InputLockError, KeyError, TypeError):
        return False
    return True


def _validate_world_bindings(
    bindings: Any, receipt_scope: Mapping[str, Any], expected_indices: Sequence[int]
) -> None:
    """Verify a native-owner association; never derive IDs from array order."""
    if not isinstance(bindings, (list, tuple)) or not bindings:
        raise InputLockError("input_lock.receipt_world_binding_invalid")
    if not isinstance(receipt_scope["host_boot_id"], str) or not receipt_scope["host_boot_id"].strip():
        raise InputLockError("input_lock.receipt_world_binding_invalid")
    for field in ("incarnation_epoch", "world_epoch"):
        if not isinstance(receipt_scope[field], str) or re.fullmatch(
            r"[1-9][0-9]*", receipt_scope[field]
        ) is None:
            raise InputLockError("input_lock.receipt_world_binding_invalid")
    world_ids = receipt_scope["world_ids"]
    if not isinstance(world_ids, (list, tuple)) or any(
        not isinstance(identity, str) or not identity.strip() for identity in world_ids
    ) or len(set(world_ids)) != len(world_ids):
        raise InputLockError("input_lock.receipt_world_binding_invalid")
    expected = list(expected_indices)
    if not expected or any(type(index) is not int or index < 0 for index in expected):
        raise InputLockError("input_lock.receipt_world_index_invalid")
    if expected != sorted(set(expected)):
        raise InputLockError("input_lock.receipt_world_index_invalid")
    indexes, identities = [], []
    for item in bindings:
        if not isinstance(item, Mapping) or set(item) != {
            "world_index", "world_id", "host_boot_id", "incarnation_epoch", "world_epoch"
        }:
            raise InputLockError("input_lock.receipt_world_binding_invalid")
        if type(item["world_index"]) is not int or item["world_index"] < 0:
            raise InputLockError("input_lock.receipt_world_index_invalid")
        if not isinstance(item["world_id"], str) or not item["world_id"].strip():
            raise InputLockError("input_lock.receipt_world_identity_invalid")
        for field in ("host_boot_id", "incarnation_epoch", "world_epoch"):
            if item[field] != receipt_scope[field]:
                raise InputLockError(f"input_lock.receipt_world_binding_mismatch:{field}")
        indexes.append(item["world_index"])
        identities.append(item["world_id"])
    if sorted(indexes) != expected or len(set(indexes)) != len(indexes):
        raise InputLockError("input_lock.receipt_world_index_mismatch")
    if len(set(identities)) != len(identities) or set(identities) != set(receipt_scope["world_ids"]):
        raise InputLockError("input_lock.receipt_world_identity_mismatch")


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
        raise InputLockError(
            f"scenario reference is not valid JSON: {experiment.scenario.path}"
        ) from exc
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

    def __post_init__(self) -> None:
        object.__setattr__(self, "document", freeze_json_mapping(self.document))
        if self.identity_digest != _digest(self.document["input_lock"]):
            raise InputLockError("input_lock.identity_mismatch")

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
        raise InputLockError(
            "effective_seed_set_required: empty declared seeds need an explicit effective_seeds"
        )
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
    # Pre-run input identity is independent of later observed runtime evidence.
    return ResolvedInputLock(document=document, identity_digest=_digest(input_lock))


def project_compiled_scenario_dependencies(
    compiled: Any, *, repo_root: str | Path
) -> dict[str, Any]:
    """Read the dependency closure already resolved by ScenarioCompiler.

    OOB existence prerequisites retain their distinct role. No import/group
    traversal or scenario compilation is repeated by this projection.
    """
    root = Path(repo_root).resolve()
    if not compiled.is_fresh():
        raise InputLockError("input_lock.scenario_dependencies_stale")
    semantic_paths = {
        compiled.source_path,
        *compiled.imported_files,
        *(path for path, _ in compiled.dependency_mtimes_ns),
    }
    existence_paths = set(compiled.dependency_existence_paths)
    result: dict[str, Any] = {}
    for source in sorted(semantic_paths | existence_paths):
        path = Path(source).resolve()
        try:
            logical_id = path.relative_to(root).as_posix()
        except ValueError as exc:
            raise InputLockError("input_lock.dependency_outside_repository") from exc
        if not path.is_file():
            raise InputLockError(f"input_lock.dependency_missing:{logical_id}")
        if source not in semantic_paths:
            result[logical_id] = {"role": "existence_prerequisite", "exists": True}
            continue
        contents = path.read_bytes()
        digest = (
            _digest(json.loads(contents))
            if path.suffix == ".json"
            else hashlib.sha256(contents).hexdigest()
        )
        result[logical_id] = {"role": "semantic_input", "content_digest": digest}
    if not compiled.is_fresh():
        raise InputLockError("input_lock.scenario_dependencies_stale")
    return result


def join_run_receipt(
    candidate: ResolvedInputLock,
    *,
    receipt: Mapping[str, Any],
    native_runtime: Mapping[str, Any],
    outcome: BatchOperationOutcome,
) -> ResolvedInputLock:
    """Reference a validated existing RunReceipt; do not create a new receipt.

    The host must bind the candidate digest in inputs.artifacts. Receipt schema
    validation does not verify signatures, durability or scientific validity.
    A completed outcome also needs explicit native-owner world associations;
    equal world counts alone leave the joined status unknown.
    """
    from tools.maintenance.runtime_run_receipt import validate_run_receipt

    validated = validate_run_receipt(thaw_json_value(receipt))
    payload = validated["payload"]
    if payload["inputs"]["artifacts"].get("resolved_input_lock") != candidate.digest:
        raise InputLockError("input_lock.receipt_input_binding_mismatch")
    if len(payload["execution_scope"]["world_ids"]) != len(outcome.expected_world_indices):
        raise InputLockError("input_lock.receipt_world_scope_mismatch")
    world_bindings = native_runtime.get("receipt_world_bindings")
    world_scope = None
    if world_bindings is not None:
        world_scope = {
            "host_boot_id": payload["host_boot_id"],
            "incarnation_epoch": payload["incarnation_epoch"],
            "world_epoch": payload["execution_scope"]["epochs"]["world"],
            "world_ids": payload["execution_scope"]["world_ids"],
            "bindings": thaw_json_value(world_bindings),
        }
        _validate_world_bindings(world_bindings, world_scope, outcome.expected_world_indices)
    receipt_binding = {
        "receipt_id": payload["receipt_id"],
        "run_id": payload["run_id"],
        "attempt_id": payload["attempt_id"],
        "host_boot_id": payload["host_boot_id"],
        "writer_generation": payload["writer_generation"],
        "backend_system_graph_sha256": payload["backend"]["system_graph_sha256"],
        "native_validation_evidence_sha256": payload["results"]["native_validation"][
            "evidence_sha256"
        ],
        "durable_ack": payload["completion"]["durable_ack"],
    }
    supplied_binding = native_runtime.get("receipt_binding")
    if supplied_binding is not None:
        if not isinstance(supplied_binding, Mapping):
            raise InputLockError("input_lock.receipt_binding_invalid")
        if set(supplied_binding) != set(_RECEIPT_BINDING_FIELDS):
            raise InputLockError("input_lock.receipt_binding_fields_invalid")
        if dict(supplied_binding) != receipt_binding:
            raise InputLockError("input_lock.receipt_binding_mismatch")
    for field in _RECEIPT_BINDING_FIELDS:
        supplied_value = native_runtime.get(field)
        if supplied_value is not None and supplied_value != receipt_binding[field]:
            raise InputLockError(f"input_lock.native_receipt_binding_mismatch:{field}")
    data = candidate.as_dict()
    complete = (
        payload["terminal_state"] == "completed"
        and outcome.result is BatchResult.COMPLETED
        and world_scope is not None
    )
    data["status"] = "completed" if complete else "unknown"
    data["native_runtime"] = dict(native_runtime)
    data["completion_evidence"] = {
        "receipt_id": payload["receipt_id"],
        "receipt_sha256": validated["payload_sha256"],
        "terminal_state": payload["terminal_state"],
        "outcome": outcome.as_dict(),
        "receipt_binding": receipt_binding,
        "world_scope": world_scope,
    }
    return ResolvedInputLock(data, candidate.digest)


def join_run_receipt_path(
    candidate: ResolvedInputLock,
    *,
    receipt_path: str | Path,
    native_runtime: Mapping[str, Any],
    outcome: BatchOperationOutcome,
    native_topology_path: str | Path | None = None,
    native_world_scope_path: str | Path | None = None,
) -> ResolvedInputLock:
    """Load one host-published canonical receipt, then use the same join.

    The file is treated as an owner output: bytes must be canonical JSON before
    schema validation and no receipt is synthesized by this projection. A
    native topology or world-scope artifact claim requires its owner output
    bytes as well.
    """

    source = Path(receipt_path)
    try:
        raw = source.read_bytes()
        document = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise InputLockError(f"input_lock.receipt_unreadable:{source}") from exc
    if not isinstance(document, Mapping):
        raise InputLockError("input_lock.receipt_document_invalid")
    if canonical_json_bytes(document) != raw:
        raise InputLockError("input_lock.receipt_not_canonical")
    if "topology_artifact_digest" in native_runtime and native_topology_path is None:
        raise InputLockError("input_lock.receipt_topology_artifact_required")
    if "world_scope_artifact_digest" in native_runtime and native_world_scope_path is None:
        raise InputLockError("input_lock.receipt_world_scope_artifact_required")
    joined = join_run_receipt(
        candidate,
        receipt=document,
        native_runtime=native_runtime,
        outcome=outcome,
    )
    if native_topology_path is not None:
        _verify_receipt_topology_artifact(document, native_runtime, Path(native_topology_path))
    if native_world_scope_path is not None:
        _verify_receipt_world_scope_artifact(document, native_runtime, Path(native_world_scope_path))
    return joined


def _verify_receipt_topology_artifact(
    receipt: Mapping[str, Any], native_runtime: Mapping[str, Any], source: Path
) -> None:
    """Check owner output bytes against the existing receipt and topology identity."""
    raw = _read_receipt_evidence_artifact(
        receipt, source, name="runtime-cpu-scheduler-topology",
        media="application/vnd.echelon-forge.runtime-cpu-scheduler-topology.v1+json",
        claimed_digest=native_runtime.get("topology_artifact_digest"),
        error_prefix="input_lock.receipt_topology",
    )
    try:
        observed = json.loads(raw)
        topology = observed["topology"]
        if (
            topology["contract"] != "echelon_forge.cpu_scheduler_topology.v1"
            or observed["sha256"] != _digest(topology)
            or observed["sha256"] != native_runtime.get("realized_topology_digest")
        ):
            raise InputLockError("input_lock.receipt_topology_identity_mismatch")
    except (UnicodeDecodeError, json.JSONDecodeError, KeyError, TypeError) as exc:
        raise InputLockError("input_lock.receipt_topology_document_invalid") from exc


def _verify_receipt_world_scope_artifact(
    receipt: Mapping[str, Any], native_runtime: Mapping[str, Any], source: Path
) -> None:
    raw = _read_receipt_evidence_artifact(
        receipt, source, name="runtime-world-scope-binding",
        media="application/vnd.echelon-forge.runtime-world-scope-binding.v1+json",
        claimed_digest=native_runtime.get("world_scope_artifact_digest"),
        error_prefix="input_lock.receipt_world_scope",
    )
    try:
        observed = json.loads(raw)
        if observed["schema_version"] != "echelon_forge.runtime_world_scope_binding.v1":
            raise InputLockError("input_lock.receipt_world_scope_schema_invalid")
        if observed["world_bindings"] != thaw_json_value(native_runtime.get("receipt_world_bindings")):
            raise InputLockError("input_lock.receipt_world_scope_identity_mismatch")
    except (UnicodeDecodeError, json.JSONDecodeError, KeyError, TypeError) as exc:
        raise InputLockError("input_lock.receipt_world_scope_document_invalid") from exc


def _read_receipt_evidence_artifact(
    receipt: Mapping[str, Any], source: Path, *, name: str, media: str,
    claimed_digest: Any, error_prefix: str,
) -> bytes:
    references = [
        item for item in receipt["payload"]["results"]["output_artifacts"] if item["name"] == name
    ]
    if len(references) != 1:
        raise InputLockError(f"{error_prefix}_reference_missing")
    reference = references[0]
    if (
        reference["media_type"] != media or reference["availability"] != "durable"
        or reference["retention_class"] != "run-retained" or reference["digest"] != claimed_digest
    ):
        raise InputLockError(f"{error_prefix}_binding_mismatch")
    try:
        raw = source.read_bytes()
    except OSError as exc:
        raise InputLockError(f"{error_prefix}_unreadable") from exc
    if len(raw) != reference["size"] or hashlib.sha256(raw).hexdigest() != reference["digest"]:
        raise InputLockError(f"{error_prefix}_artifact_mismatch")
    return raw


def project_native_composition_evidence(result: Any) -> dict[str, Any]:
    """Consume RuntimeFacade's manifest and separate realized topology export."""
    if not result.available:
        raise InputLockError(f"input_lock.native_evidence_unavailable:{result.error_code}")
    snapshots = [json.loads(value) for value in result.cpu_scheduler_topology_json]
    if not snapshots or len(snapshots) != len(result.evidence.world_instances):
        raise InputLockError("input_lock.native_topology_scope_incomplete")
    for snapshot in snapshots:
        if snapshot["sha256"] != _digest(snapshot["topology"]):
            raise InputLockError("input_lock.native_topology_identity_mismatch")
    identities = {snapshot["sha256"] for snapshot in snapshots}
    if len(identities) != 1:
        raise InputLockError("input_lock.native_topology_worlds_differ")
    return {
        "resolved_manifest_sha256": result.evidence.resolved_manifest_sha256,
        "executable_graph_sha256": result.evidence.executable_graph_sha256,
        "realized_topology_digest": next(iter(identities)),
        "composition_evidence_sha256": result.evidence.evidence_sha256,
        "host_mode": result.evidence.host_mode,
    }


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
    if not _completion_evidence_is_structurally_complete(
        left_data.get("completion_evidence")
    ) or not _completion_evidence_is_structurally_complete(right_data.get("completion_evidence")):
        return ComparisonResult(
            False,
            ("completion_evidence",),
            "claimed status requires a bound validated RunReceipt and complete outcome",
        )
    for data in (left_data, right_data):
        if data["native_runtime"].get("receipt_world_bindings") != (
            data["completion_evidence"]["world_scope"]["bindings"]
        ):
            return ComparisonResult(
                False, ("completion_evidence",), "native world association differs from joined receipt scope"
            )
    differences: list[str] = []
    for axis in (
        "scenario",
        "config",
        "dependencies",
        "force_package",
        "mechanism",
        "policy",
        "effective_seed_set",
        "evaluation_protocol",
    ):
        if (
            left_data["input_lock"][axis] != right_data["input_lock"][axis]
            and axis not in intentional_axes
        ):
            differences.append(axis)
    left_native = left_data["native_runtime"]
    right_native = right_data["native_runtime"]
    if (
        left_native.get("input_lock_semantics_executed") is not True
        or right_native.get("input_lock_semantics_executed") is not True
    ):
        differences.append("input_lock_semantics_executed")
    left_mode = left_native.get("host_mode")
    right_mode = right_native.get("host_mode")
    if (
        not isinstance(left_mode, str)
        or not left_mode.strip()
        or not isinstance(right_mode, str)
        or not right_mode.strip()
        or left_mode != right_mode
    ):
        differences.append("host_mode")
    for field in _REQUIRED_NATIVE_IDENTITY_FIELDS:
        left_value = left_native.get(field)
        right_value = right_native.get(field)
        if (
            not isinstance(left_value, str)
            or re.fullmatch(r"[0-9a-f]{64}", left_value) is None
            or not isinstance(right_value, str)
            or re.fullmatch(r"[0-9a-f]{64}", right_value) is None
        ):
            differences.append(field)
        elif left_value != right_value:
            differences.append(field)
    if differences:
        return ComparisonResult(
            False,
            tuple(sorted(set(differences))),
            "missing or mismatched truth-affecting native identity",
        )
    return ComparisonResult(True, (), "same resolved inputs and complete realized native identity")


__all__ = [
    "ComparisonResult",
    "InputLockError",
    "ResolvedInputLock",
    "SCHEMA_VERSION",
    "build_resolved_input_lock",
    "canonical_json_bytes",
    "compare_resolved_input_locks",
    "join_run_receipt",
    "join_run_receipt_path",
    "project_compiled_scenario_dependencies",
    "project_native_composition_evidence",
]
