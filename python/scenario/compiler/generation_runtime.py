from __future__ import annotations

import hashlib
import json
import random
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Iterable

from .clone import _clone_scenario_value
from .generation_request import (
    ScenarioGenerationRequest,
    validate_scenario_generation_request,
)

if TYPE_CHECKING:
    from .service import CompiledScenario


SCENARIO_GENERATION_RUNTIME_ARTIFACT_KIND = "scenario_generation_runtime_artifact"
SCENARIO_GENERATION_RUNTIME_CONTRACT_VERSION = "wp21.scenario_generation_runtime.v1"
SCENARIO_GENERATION_VARIATION_OPERATIONS = (
    "choice",
    "set",
    "uniform_float",
    "uniform_int",
)
SCENARIO_GENERATION_INTERVENTION_MUTATION_BOUNDARY = "setup_admission_only"


def _normalized_text(value: Any) -> str:
    return str(value or "").strip()


def _normalized_unique_texts(values: Iterable[Any]) -> tuple[str, ...]:
    seen: set[str] = set()
    normalized: list[str] = []
    for value in values:
        text = _normalized_text(value)
        if not text or text in seen:
            continue
        seen.add(text)
        normalized.append(text)
    return tuple(sorted(normalized))


def _normalize_path(path: Iterable[Any]) -> tuple[str | int, ...]:
    normalized: list[str | int] = []
    for component in path:
        if isinstance(component, bool):
            raise TypeError("path components must be str or int")
        if isinstance(component, int):
            normalized.append(int(component))
            continue
        text = _normalized_text(component)
        if not text:
            raise ValueError("path components must not be blank")
        normalized.append(text)
    return tuple(normalized)


def _path_to_text(path: Iterable[str | int]) -> str:
    pieces: list[str] = []
    for component in path:
        if isinstance(component, int):
            if not pieces:
                pieces.append(f"[{component}]")
            else:
                pieces[-1] = f"{pieces[-1]}[{component}]"
        else:
            pieces.append(str(component))
    return ".".join(pieces)


def _canonical_json_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(
        payload,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _stable_rng_seed(*parts: Any) -> int:
    digest = hashlib.sha256()
    for part in parts:
        if isinstance(part, bytes):
            digest.update(part)
        else:
            digest.update(str(part).encode("utf-8"))
        digest.update(b"\x00")
    return int.from_bytes(digest.digest()[:8], "big", signed=False)


def _resolve_path_value(root: Any, path: tuple[str | int, ...]) -> Any:
    current = root
    for component in path:
        if isinstance(component, int):
            if not isinstance(current, list) or component < 0 or component >= len(current):
                raise KeyError(f"path {_path_to_text(path)!r} does not exist")
            current = current[component]
            continue
        if not isinstance(current, dict) or component not in current:
            raise KeyError(f"path {_path_to_text(path)!r} does not exist")
        current = current[component]
    return current


def _assign_existing_path_value(
    root: Any,
    path: tuple[str | int, ...],
    value: Any,
) -> None:
    if not path:
        raise ValueError("target_path must not be empty")

    parent = root
    for component in path[:-1]:
        if isinstance(component, int):
            if not isinstance(parent, list) or component < 0 or component >= len(parent):
                raise KeyError(f"path {_path_to_text(path)!r} does not exist")
            parent = parent[component]
            continue
        if not isinstance(parent, dict) or component not in parent:
            raise KeyError(f"path {_path_to_text(path)!r} does not exist")
        parent = parent[component]

    final_component = path[-1]
    if isinstance(final_component, int):
        if not isinstance(parent, list) or final_component < 0 or final_component >= len(parent):
            raise KeyError(f"path {_path_to_text(path)!r} does not exist")
        parent[final_component] = value
        return
    if not isinstance(parent, dict) or final_component not in parent:
        raise KeyError(f"path {_path_to_text(path)!r} does not exist")
    parent[final_component] = value


def _ensure_list_container(root: dict[str, Any], path: tuple[str, ...]) -> list[Any]:
    if not path:
        raise ValueError("container_path must not be empty")

    current: Any = root
    for index, component in enumerate(path):
        is_last = index == len(path) - 1
        if not isinstance(current, dict):
            raise TypeError(f"container path {_path_to_text(path)!r} crossed a non-dict branch")
        if component not in current:
            current[component] = [] if is_last else {}
        next_value = current[component]
        if is_last:
            if not isinstance(next_value, list):
                raise TypeError(f"container path {_path_to_text(path)!r} must resolve to a list")
            return next_value
        if not isinstance(next_value, dict):
            raise TypeError(f"container path {_path_to_text(path)!r} crossed a non-dict branch")
        current = next_value
    raise RuntimeError("unreachable container path state")


@dataclass(frozen=True)
class ScenarioGenerationVariationSpec:
    variation_id: str
    target_path: tuple[str | int, ...]
    operation: str
    minimum_value: int | float | None = None
    maximum_value: int | float | None = None
    choices: tuple[Any, ...] = ()
    value: Any = None
    precision_digits: int = 6

    def __post_init__(self) -> None:
        object.__setattr__(self, "variation_id", _normalized_text(self.variation_id))
        object.__setattr__(self, "target_path", _normalize_path(self.target_path))
        object.__setattr__(self, "operation", _normalized_text(self.operation))
        object.__setattr__(self, "choices", tuple(_clone_scenario_value(item) for item in self.choices))
        object.__setattr__(self, "value", _clone_scenario_value(self.value))
        object.__setattr__(self, "precision_digits", int(self.precision_digits))

    @property
    def target_path_text(self) -> str:
        return _path_to_text(self.target_path)

    def to_metadata(self) -> dict[str, Any]:
        metadata: dict[str, Any] = {
            "variation_id": self.variation_id,
            "target_path": list(self.target_path),
            "target_path_text": self.target_path_text,
            "operation": self.operation,
        }
        if self.minimum_value is not None:
            metadata["minimum_value"] = self.minimum_value
        if self.maximum_value is not None:
            metadata["maximum_value"] = self.maximum_value
        if self.choices:
            metadata["choices"] = _clone_scenario_value(list(self.choices))
        if self.operation == "set":
            metadata["value"] = _clone_scenario_value(self.value)
        if self.operation == "uniform_float":
            metadata["precision_digits"] = int(self.precision_digits)
        return metadata


@dataclass(frozen=True)
class ScenarioAppliedVariation:
    spec: ScenarioGenerationVariationSpec
    baseline_value: Any
    applied_value: Any

    def __post_init__(self) -> None:
        object.__setattr__(self, "baseline_value", _clone_scenario_value(self.baseline_value))
        object.__setattr__(self, "applied_value", _clone_scenario_value(self.applied_value))

    def to_metadata(self) -> dict[str, Any]:
        metadata = self.spec.to_metadata()
        metadata["baseline_value"] = _clone_scenario_value(self.baseline_value)
        metadata["applied_value"] = _clone_scenario_value(self.applied_value)
        return metadata


@dataclass(frozen=True)
class ScenarioGenerationInterventionSpec:
    intervention_id: str
    intervention_kind: str
    payload: dict[str, Any] | None = None
    target_entity_ref: str = ""
    evidence_refs: tuple[str, ...] = ()
    container_path: tuple[str, ...] = ("meta", "generated_interventions")
    mutation_boundary: str = SCENARIO_GENERATION_INTERVENTION_MUTATION_BOUNDARY

    def __post_init__(self) -> None:
        object.__setattr__(self, "intervention_id", _normalized_text(self.intervention_id))
        object.__setattr__(self, "intervention_kind", _normalized_text(self.intervention_kind))
        payload = self.payload if isinstance(self.payload, dict) else {}
        object.__setattr__(self, "payload", _clone_scenario_value(payload))
        object.__setattr__(self, "target_entity_ref", _normalized_text(self.target_entity_ref))
        object.__setattr__(self, "evidence_refs", _normalized_unique_texts(self.evidence_refs))
        object.__setattr__(
            self,
            "container_path",
            tuple(_normalized_text(component) for component in self.container_path),
        )
        object.__setattr__(self, "mutation_boundary", _normalized_text(self.mutation_boundary))

    @property
    def container_path_text(self) -> str:
        return _path_to_text(self.container_path)

    def to_metadata(self) -> dict[str, Any]:
        return {
            "intervention_id": self.intervention_id,
            "intervention_kind": self.intervention_kind,
            "target_entity_ref": self.target_entity_ref,
            "container_path": list(self.container_path),
            "container_path_text": self.container_path_text,
            "mutation_boundary": self.mutation_boundary,
            "evidence_refs": list(self.evidence_refs),
            "payload": _clone_scenario_value(self.payload),
        }


@dataclass(frozen=True)
class ScenarioGeneratedIntervention:
    spec: ScenarioGenerationInterventionSpec
    generated_entry: dict[str, Any]

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_entry", _clone_scenario_value(self.generated_entry))

    def to_metadata(self) -> dict[str, Any]:
        metadata = self.spec.to_metadata()
        metadata["generated_entry"] = _clone_scenario_value(self.generated_entry)
        return metadata


@dataclass(frozen=True)
class ScenarioGenerationRuntimeValidationResult:
    valid: bool
    fail_closed: bool
    rejection_reason: str
    errors: tuple[str, ...]


@dataclass(frozen=True)
class ScenarioGenerationRuntimeArtifact:
    request: ScenarioGenerationRequest
    baseline_setup_ref: str
    baseline_scenario_name: str
    baseline_source_path: str
    baseline_zone_count: int
    baseline_entity_count: int
    baseline_digest_sha256: str
    applied_variations: tuple[ScenarioAppliedVariation, ...]
    generated_interventions: tuple[ScenarioGeneratedIntervention, ...]
    generated_scenario_data: dict[str, Any]
    authoritative_state_mutation_allowed: bool = False
    artifact_kind: str = SCENARIO_GENERATION_RUNTIME_ARTIFACT_KIND
    artifact_version: str = SCENARIO_GENERATION_RUNTIME_CONTRACT_VERSION

    def __post_init__(self) -> None:
        object.__setattr__(self, "baseline_setup_ref", _normalized_text(self.baseline_setup_ref))
        object.__setattr__(self, "baseline_scenario_name", _normalized_text(self.baseline_scenario_name))
        object.__setattr__(self, "baseline_source_path", _normalized_text(self.baseline_source_path))
        object.__setattr__(self, "baseline_zone_count", int(self.baseline_zone_count))
        object.__setattr__(self, "baseline_entity_count", int(self.baseline_entity_count))
        object.__setattr__(self, "baseline_digest_sha256", _normalized_text(self.baseline_digest_sha256))
        object.__setattr__(
            self,
            "generated_scenario_data",
            _clone_scenario_value(self.generated_scenario_data),
        )

    def instantiate_generated_scenario(self) -> dict[str, Any]:
        return _clone_scenario_value(self.generated_scenario_data)

    def compile_generated_scenario(self) -> CompiledScenario:
        from .service import ScenarioCompiler

        return ScenarioCompiler.compile_data(
            self.instantiate_generated_scenario(),
            source_path=None,
        )

    def to_metadata(self) -> dict[str, Any]:
        return {
            "artifact_kind": self.artifact_kind,
            "artifact_version": self.artifact_version,
            "authoritative_state_mutation_allowed": bool(self.authoritative_state_mutation_allowed),
            "generator": {
                "generator_version": self.request.generator_version,
                "deterministic_seed": int(self.request.deterministic_seed),
            },
            "lineage": {
                "replay_envelope_ref": self.request.replay_envelope_ref,
                "branch_point_ref": self.request.branch_point_ref,
            },
            "baseline": {
                "baseline_scenario_ref": self.request.baseline_scenario_ref,
                "baseline_setup_ref": self.baseline_setup_ref,
                "scenario_name": self.baseline_scenario_name,
                "source_path": self.baseline_source_path,
                "zone_count": int(self.baseline_zone_count),
                "entity_count": int(self.baseline_entity_count),
                "scenario_digest_sha256": self.baseline_digest_sha256,
            },
            "request": self.request.to_metadata(),
            "evidence_metadata": [
                _clone_scenario_value(ref.to_metadata()) for ref in self.request.evidence_refs
            ],
            "applied_variations": [
                variation.to_metadata() for variation in self.applied_variations
            ],
            "generated_interventions": [
                intervention.to_metadata() for intervention in self.generated_interventions
            ],
            "generated_scenario": self.instantiate_generated_scenario(),
        }

    def to_canonical_bytes(self) -> bytes:
        return _canonical_json_bytes(self.to_metadata())

    def to_canonical_json(self) -> str:
        return self.to_canonical_bytes().decode("utf-8")


def _normalize_variations(
    variations: Iterable[ScenarioGenerationVariationSpec | dict[str, Any]],
) -> tuple[ScenarioGenerationVariationSpec, ...]:
    normalized: list[ScenarioGenerationVariationSpec] = []
    for entry in variations:
        if isinstance(entry, ScenarioGenerationVariationSpec):
            normalized.append(entry)
        elif isinstance(entry, dict):
            normalized.append(ScenarioGenerationVariationSpec(**entry))
        else:
            raise TypeError(
                "variations entries must be ScenarioGenerationVariationSpec or dict"
            )
    return tuple(
        sorted(
            normalized,
            key=lambda spec: (spec.variation_id, spec.target_path_text, spec.operation),
        )
    )


def _normalize_interventions(
    interventions: Iterable[ScenarioGenerationInterventionSpec | dict[str, Any]],
) -> tuple[ScenarioGenerationInterventionSpec, ...]:
    normalized: list[ScenarioGenerationInterventionSpec] = []
    for entry in interventions:
        if isinstance(entry, ScenarioGenerationInterventionSpec):
            normalized.append(entry)
        elif isinstance(entry, dict):
            normalized.append(ScenarioGenerationInterventionSpec(**entry))
        else:
            raise TypeError(
                "interventions entries must be ScenarioGenerationInterventionSpec or dict"
            )
    return tuple(
        sorted(
            normalized,
            key=lambda spec: (spec.intervention_id, spec.container_path_text, spec.intervention_kind),
        )
    )


def _validate_variation_spec(
    spec: ScenarioGenerationVariationSpec,
) -> list[tuple[str, str]]:
    failures: list[tuple[str, str]] = []
    if not spec.variation_id:
        failures.append(
            (
                "scenario_generation_runtime_variation_id_required",
                "variations[].variation_id is required",
            )
        )
    if not spec.target_path:
        failures.append(
            (
                "scenario_generation_runtime_variation_path_required",
                "variations[].target_path is required",
            )
        )
    if spec.operation not in SCENARIO_GENERATION_VARIATION_OPERATIONS:
        failures.append(
            (
                "scenario_generation_runtime_variation_operation_unsupported",
                f"variations[].operation {spec.operation!r} is unsupported",
            )
        )
        return failures

    if spec.operation == "set":
        return failures
    if spec.operation == "choice":
        if not spec.choices:
            failures.append(
                (
                    "scenario_generation_runtime_variation_choice_required",
                    "choice variations require a non-empty choices tuple",
                )
            )
        return failures
    if spec.minimum_value is None or spec.maximum_value is None:
        failures.append(
            (
                "scenario_generation_runtime_variation_range_required",
                "uniform variations require minimum_value and maximum_value",
            )
        )
        return failures
    if spec.minimum_value > spec.maximum_value:
        failures.append(
            (
                "scenario_generation_runtime_variation_range_invalid",
                "uniform variation minimum_value must be <= maximum_value",
            )
        )
    if spec.operation == "uniform_int":
        if type(spec.minimum_value) is not int or type(spec.maximum_value) is not int:
            failures.append(
                (
                    "scenario_generation_runtime_variation_range_invalid",
                    "uniform_int variations require integer minimum_value and maximum_value",
                )
            )
    if spec.operation == "uniform_float" and int(spec.precision_digits) < 0:
        failures.append(
            (
                "scenario_generation_runtime_variation_precision_invalid",
                "uniform_float precision_digits must be >= 0",
            )
        )
    return failures


def _validate_intervention_spec(
    spec: ScenarioGenerationInterventionSpec,
) -> list[tuple[str, str]]:
    failures: list[tuple[str, str]] = []
    if not spec.intervention_id:
        failures.append(
            (
                "scenario_generation_runtime_intervention_id_required",
                "interventions[].intervention_id is required",
            )
        )
    if not spec.intervention_kind:
        failures.append(
            (
                "scenario_generation_runtime_intervention_kind_required",
                "interventions[].intervention_kind is required",
            )
        )
    if not spec.container_path or any(not component for component in spec.container_path):
        failures.append(
            (
                "scenario_generation_runtime_intervention_container_required",
                "interventions[].container_path is required",
            )
        )
    if spec.mutation_boundary != SCENARIO_GENERATION_INTERVENTION_MUTATION_BOUNDARY:
        failures.append(
            (
                "scenario_generation_runtime_intervention_boundary_invalid",
                "interventions[].mutation_boundary must remain setup_admission_only",
            )
        )
    return failures


def validate_scenario_generation_runtime_inputs(
    request: ScenarioGenerationRequest,
    *,
    baseline_setup_ref: str,
    compiled_scenario: CompiledScenario | None = None,
    baseline_scenario_data: dict[str, Any] | None = None,
    variations: Iterable[ScenarioGenerationVariationSpec | dict[str, Any]] = (),
    interventions: Iterable[ScenarioGenerationInterventionSpec | dict[str, Any]] = (),
) -> ScenarioGenerationRuntimeValidationResult:
    request_validation = validate_scenario_generation_request(request)
    if not request_validation.valid:
        return ScenarioGenerationRuntimeValidationResult(
            valid=False,
            fail_closed=True,
            rejection_reason=request_validation.rejection_reason,
            errors=request_validation.errors,
        )

    failures: list[tuple[str, str]] = []
    baseline_setup_ref = _normalized_text(baseline_setup_ref)
    if not baseline_setup_ref:
        failures.append(
            (
                "scenario_generation_runtime_baseline_setup_ref_required",
                "baseline_setup_ref is required",
            )
        )
    if compiled_scenario is not None and baseline_scenario_data is not None:
        failures.append(
            (
                "scenario_generation_runtime_baseline_ambiguous",
                "provide either compiled_scenario or baseline_scenario_data, not both",
            )
        )
    if compiled_scenario is None and baseline_scenario_data is None:
        failures.append(
            (
                "scenario_generation_runtime_baseline_required",
                "compiled_scenario or baseline_scenario_data is required",
            )
        )
    if baseline_scenario_data is not None and not isinstance(baseline_scenario_data, dict):
        failures.append(
            (
                "scenario_generation_runtime_baseline_invalid",
                "baseline_scenario_data must be a dict",
            )
        )

    normalized_variations = _normalize_variations(variations)
    normalized_interventions = _normalize_interventions(interventions)
    if not normalized_variations and not normalized_interventions:
        failures.append(
            (
                "scenario_generation_runtime_specs_required",
                "at least one variation or intervention is required",
            )
        )

    seen_variation_ids: set[str] = set()
    for spec in normalized_variations:
        if spec.variation_id in seen_variation_ids:
            failures.append(
                (
                    "scenario_generation_runtime_variation_id_duplicate",
                    f"duplicate variation_id {spec.variation_id!r}",
                )
            )
            break
        seen_variation_ids.add(spec.variation_id)
        failures.extend(_validate_variation_spec(spec))

    seen_intervention_ids: set[str] = set()
    for spec in normalized_interventions:
        if spec.intervention_id in seen_intervention_ids:
            failures.append(
                (
                    "scenario_generation_runtime_intervention_id_duplicate",
                    f"duplicate intervention_id {spec.intervention_id!r}",
                )
            )
            break
        seen_intervention_ids.add(spec.intervention_id)
        failures.extend(_validate_intervention_spec(spec))

    if failures:
        return ScenarioGenerationRuntimeValidationResult(
            valid=False,
            fail_closed=True,
            rejection_reason=failures[0][0],
            errors=tuple(message for _, message in failures),
        )
    return ScenarioGenerationRuntimeValidationResult(
        valid=True,
        fail_closed=False,
        rejection_reason="",
        errors=(),
    )


def _resolve_generated_value(
    spec: ScenarioGenerationVariationSpec,
    *,
    request: ScenarioGenerationRequest,
    baseline_digest_sha256: str,
) -> Any:
    if spec.operation == "set":
        return _clone_scenario_value(spec.value)
    if spec.operation == "choice":
        rng = random.Random(
            _stable_rng_seed(
                request.request_id,
                request.request_version,
                request.contract_version,
                request.generator_version,
                request.deterministic_seed,
                request.baseline_scenario_ref,
                baseline_digest_sha256,
                spec.variation_id,
                spec.target_path_text,
                spec.operation,
            )
        )
        return _clone_scenario_value(spec.choices[rng.randrange(len(spec.choices))])
    rng = random.Random(
        _stable_rng_seed(
            request.request_id,
            request.request_version,
            request.contract_version,
            request.generator_version,
            request.deterministic_seed,
            request.baseline_scenario_ref,
            baseline_digest_sha256,
            spec.variation_id,
            spec.target_path_text,
            spec.operation,
        )
    )
    if spec.operation == "uniform_int":
        return int(rng.randint(int(spec.minimum_value), int(spec.maximum_value)))
    if spec.operation == "uniform_float":
        generated = float(rng.uniform(float(spec.minimum_value), float(spec.maximum_value)))
        return round(generated, int(spec.precision_digits))
    raise ValueError(f"unsupported variation operation {spec.operation!r}")


def _build_generated_intervention_entry(
    spec: ScenarioGenerationInterventionSpec,
    *,
    request: ScenarioGenerationRequest,
    baseline_setup_ref: str,
) -> dict[str, Any]:
    return {
        "intervention_id": spec.intervention_id,
        "intervention_kind": spec.intervention_kind,
        "target_entity_ref": spec.target_entity_ref,
        "mutation_boundary": spec.mutation_boundary,
        "baseline_setup_ref": baseline_setup_ref,
        "baseline_scenario_ref": request.baseline_scenario_ref,
        "replay_envelope_ref": request.replay_envelope_ref,
        "branch_point_ref": request.branch_point_ref,
        "generator_version": request.generator_version,
        "deterministic_seed": int(request.deterministic_seed),
        "evidence_refs": list(spec.evidence_refs),
        "payload": _clone_scenario_value(spec.payload),
    }


def build_scenario_generation_runtime_artifact(
    request: ScenarioGenerationRequest,
    *,
    baseline_setup_ref: str,
    compiled_scenario: CompiledScenario | None = None,
    baseline_scenario_data: dict[str, Any] | None = None,
    variations: Iterable[ScenarioGenerationVariationSpec | dict[str, Any]] = (),
    interventions: Iterable[ScenarioGenerationInterventionSpec | dict[str, Any]] = (),
) -> ScenarioGenerationRuntimeArtifact:
    validation = validate_scenario_generation_runtime_inputs(
        request,
        baseline_setup_ref=baseline_setup_ref,
        compiled_scenario=compiled_scenario,
        baseline_scenario_data=baseline_scenario_data,
        variations=variations,
        interventions=interventions,
    )
    if not validation.valid:
        raise ValueError(
            f"invalid scenario generation runtime inputs: {validation.rejection_reason}"
        )

    normalized_variations = _normalize_variations(variations)
    normalized_interventions = _normalize_interventions(interventions)

    if compiled_scenario is not None:
        baseline_scenario_name = _normalized_text(compiled_scenario.scenario_name)
        baseline_source_path = _normalized_text(compiled_scenario.source_path)
        baseline_zone_count = int(compiled_scenario.zone_count)
        baseline_entity_count = int(compiled_scenario.entity_count)
        baseline_data = compiled_scenario.instantiate()
    else:
        baseline_data = _clone_scenario_value(baseline_scenario_data or {})
        baseline_scenario_name = _normalized_text(
            baseline_data.get("scenario_name") or request.baseline_scenario_ref
        )
        baseline_source_path = ""
        environment_cfg = baseline_data.get("environment", {})
        zones = environment_cfg.get("zones", []) if isinstance(environment_cfg, dict) else []
        entities = baseline_data.get("entities", [])
        baseline_zone_count = len(zones) if isinstance(zones, list) else 0
        baseline_entity_count = len(entities) if isinstance(entities, list) else 0

    baseline_clone = _clone_scenario_value(baseline_data)
    baseline_digest_sha256 = hashlib.sha256(
        _canonical_json_bytes(baseline_clone)
    ).hexdigest()
    generated_scenario_data = _clone_scenario_value(baseline_clone)

    applied_variations: list[ScenarioAppliedVariation] = []
    for spec in normalized_variations:
        baseline_value = _clone_scenario_value(
            _resolve_path_value(generated_scenario_data, spec.target_path)
        )
        applied_value = _resolve_generated_value(
            spec,
            request=request,
            baseline_digest_sha256=baseline_digest_sha256,
        )
        _assign_existing_path_value(
            generated_scenario_data,
            spec.target_path,
            _clone_scenario_value(applied_value),
        )
        applied_variations.append(
            ScenarioAppliedVariation(
                spec=spec,
                baseline_value=baseline_value,
                applied_value=applied_value,
            )
        )

    generated_interventions: list[ScenarioGeneratedIntervention] = []
    for spec in normalized_interventions:
        container = _ensure_list_container(
            generated_scenario_data,
            spec.container_path,
        )
        generated_entry = _build_generated_intervention_entry(
            spec,
            request=request,
            baseline_setup_ref=_normalized_text(baseline_setup_ref),
        )
        container.append(_clone_scenario_value(generated_entry))
        generated_interventions.append(
            ScenarioGeneratedIntervention(
                spec=spec,
                generated_entry=generated_entry,
            )
        )

    return ScenarioGenerationRuntimeArtifact(
        request=request,
        baseline_setup_ref=baseline_setup_ref,
        baseline_scenario_name=baseline_scenario_name,
        baseline_source_path=baseline_source_path,
        baseline_zone_count=baseline_zone_count,
        baseline_entity_count=baseline_entity_count,
        baseline_digest_sha256=baseline_digest_sha256,
        applied_variations=tuple(applied_variations),
        generated_interventions=tuple(generated_interventions),
        generated_scenario_data=generated_scenario_data,
    )


__all__ = [
    "SCENARIO_GENERATION_INTERVENTION_MUTATION_BOUNDARY",
    "SCENARIO_GENERATION_RUNTIME_ARTIFACT_KIND",
    "SCENARIO_GENERATION_RUNTIME_CONTRACT_VERSION",
    "SCENARIO_GENERATION_VARIATION_OPERATIONS",
    "ScenarioAppliedVariation",
    "ScenarioGeneratedIntervention",
    "ScenarioGenerationInterventionSpec",
    "ScenarioGenerationRuntimeArtifact",
    "ScenarioGenerationRuntimeValidationResult",
    "ScenarioGenerationVariationSpec",
    "build_scenario_generation_runtime_artifact",
    "validate_scenario_generation_runtime_inputs",
]
