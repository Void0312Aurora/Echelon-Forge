from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Iterable

from .clone import _clone_scenario_value

if TYPE_CHECKING:
    from .service import CompiledScenario


SCENARIO_GENERATION_REQUEST_CONTRACT_VERSION = "scenario_generation_request.v1"

SCENARIO_GENERATION_KINDS = (
    "scenario_variation",
    "adversary_placement",
    "route_perturbation",
    "mission_perturbation",
    "stressor_injection",
)

SCENARIO_GENERATION_SOURCES = (
    "analyst_authored",
    "counterfactual_branch",
    "curriculum_generation",
    "evaluation_replay",
)

SCENARIO_GENERATION_EVIDENCE_KINDS = (
    "baseline_scenario",
    "branch_point",
    "capability_bundle",
    "learning_evidence",
    "replay_envelope",
    "review_note",
)


def _normalized_text(value: Any) -> str:
    return str(value or "").strip()


def _normalized_unique_texts(values: Iterable[Any]) -> tuple[str, ...]:
    seen: set[str] = set()
    normalized: list[str] = []
    for value in values:
        text = _normalized_text(value)
        if text in seen:
            continue
        seen.add(text)
        normalized.append(text)
    return tuple(sorted(normalized))


@dataclass(frozen=True)
class ScenarioGenerationEvidenceRef:
    ref_id: str
    evidence_kind: str
    provenance_label: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "ref_id", _normalized_text(self.ref_id))
        object.__setattr__(self, "evidence_kind", _normalized_text(self.evidence_kind))
        object.__setattr__(self, "provenance_label", _normalized_text(self.provenance_label))

    def to_metadata(self) -> dict[str, str]:
        return {
            "ref_id": self.ref_id,
            "evidence_kind": self.evidence_kind,
            "provenance_label": self.provenance_label,
        }


@dataclass(frozen=True)
class ScenarioGenerationRequest:
    request_id: str
    generation_kind: str
    source: str
    generator_version: str
    deterministic_seed: int
    baseline_scenario_ref: str
    request_version: str = "1"
    contract_version: str = SCENARIO_GENERATION_REQUEST_CONTRACT_VERSION
    replay_envelope_ref: str = ""
    branch_point_ref: str = ""
    capability_refs: tuple[str, ...] = ()
    evidence_refs: tuple[ScenarioGenerationEvidenceRef, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "request_id", _normalized_text(self.request_id))
        object.__setattr__(self, "generation_kind", _normalized_text(self.generation_kind))
        object.__setattr__(self, "source", _normalized_text(self.source))
        object.__setattr__(self, "generator_version", _normalized_text(self.generator_version))
        object.__setattr__(self, "baseline_scenario_ref", _normalized_text(self.baseline_scenario_ref))
        object.__setattr__(self, "request_version", _normalized_text(self.request_version))
        object.__setattr__(self, "contract_version", _normalized_text(self.contract_version))
        object.__setattr__(self, "replay_envelope_ref", _normalized_text(self.replay_envelope_ref))
        object.__setattr__(self, "branch_point_ref", _normalized_text(self.branch_point_ref))
        object.__setattr__(self, "capability_refs", _normalized_unique_texts(self.capability_refs))
        normalized_evidence = []
        for ref in self.evidence_refs:
            if isinstance(ref, ScenarioGenerationEvidenceRef):
                normalized_evidence.append(ref)
            elif isinstance(ref, dict):
                normalized_evidence.append(ScenarioGenerationEvidenceRef(**ref))
            else:
                raise TypeError("evidence_refs entries must be ScenarioGenerationEvidenceRef or dict")
        object.__setattr__(
            self,
            "evidence_refs",
            tuple(
                sorted(
                    normalized_evidence,
                    key=lambda ref: (ref.evidence_kind, ref.ref_id, ref.provenance_label),
                )
            ),
        )

    def to_metadata(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "request_version": self.request_version,
            "contract_version": self.contract_version,
            "generation_kind": self.generation_kind,
            "source": self.source,
            "generator_version": self.generator_version,
            "deterministic_seed": int(self.deterministic_seed),
            "baseline_scenario_ref": self.baseline_scenario_ref,
            "replay_envelope_ref": self.replay_envelope_ref,
            "branch_point_ref": self.branch_point_ref,
            "capability_refs": list(self.capability_refs),
            "evidence_refs": [ref.to_metadata() for ref in self.evidence_refs],
        }


@dataclass(frozen=True)
class ScenarioGenerationRequestValidationResult:
    valid: bool
    fail_closed: bool
    rejection_reason: str
    errors: tuple[str, ...]


@dataclass(frozen=True)
class ScenarioGenerationRequestArtifact:
    request: ScenarioGenerationRequest
    baseline_scenario_name: str
    baseline_source_path: str
    baseline_zone_count: int
    baseline_entity_count: int
    authoritative_state_mutation_allowed: bool = False

    def to_metadata(self) -> dict[str, Any]:
        return {
            "artifact_kind": "scenario_generation_request_metadata",
            "authoritative_state_mutation_allowed": bool(self.authoritative_state_mutation_allowed),
            "request": self.request.to_metadata(),
            "baseline_scenario": {
                "scenario_name": self.baseline_scenario_name,
                "source_path": self.baseline_source_path,
                "zone_count": int(self.baseline_zone_count),
                "entity_count": int(self.baseline_entity_count),
            },
            "evidence_metadata": [ref.to_metadata() for ref in self.request.evidence_refs],
        }


def validate_scenario_generation_request(
    request: ScenarioGenerationRequest,
) -> ScenarioGenerationRequestValidationResult:
    if not isinstance(request, ScenarioGenerationRequest):
        raise TypeError("request must be a ScenarioGenerationRequest")

    failures: list[tuple[str, str]] = []

    if not request.request_id:
        failures.append(
            ("scenario_generation_request_id_required", "request_id is required")
        )
    if not request.request_version:
        failures.append(
            ("scenario_generation_request_version_required", "request_version is required")
        )
    if not request.contract_version:
        failures.append(
            ("scenario_generation_contract_version_required", "contract_version is required")
        )
    if request.generation_kind not in SCENARIO_GENERATION_KINDS:
        if not request.generation_kind:
            failures.append(
                ("scenario_generation_kind_required", "generation_kind is required")
            )
        else:
            failures.append(
                (
                    "scenario_generation_kind_unsupported",
                    f"generation_kind {request.generation_kind!r} is unsupported",
                )
            )
    if request.source not in SCENARIO_GENERATION_SOURCES:
        if not request.source:
            failures.append(
                ("scenario_generation_source_required", "request_source is required")
            )
        else:
            failures.append(
                (
                    "scenario_generation_source_unsupported",
                    f"source {request.source!r} is unsupported",
                )
            )
    if not request.generator_version:
        failures.append(
            (
                "scenario_generation_generator_version_required",
                "generator_version is required",
            )
        )
    if type(request.deterministic_seed) is not int or int(request.deterministic_seed) < 0:
        failures.append(
            (
                "scenario_generation_seed_required",
                "deterministic_seed must be a non-negative integer",
            )
        )
    if not request.baseline_scenario_ref:
        failures.append(
            (
                "scenario_generation_baseline_scenario_required",
                "baseline_scenario_ref is required",
            )
        )
    if not request.replay_envelope_ref and not request.branch_point_ref:
        failures.append(
            (
                "scenario_generation_lineage_ref_required",
                "replay_envelope_ref or branch_point_ref is required",
            )
        )
    if not request.evidence_refs:
        failures.append(
            (
                "scenario_generation_evidence_required",
                "at least one evidence_refs entry is required",
            )
        )
    for index, capability_ref in enumerate(request.capability_refs):
        if not capability_ref:
            failures.append(
                (
                    "scenario_generation_capability_ref_invalid",
                    f"capability_refs[{index}] must not be blank",
                )
            )
            break
    for index, evidence_ref in enumerate(request.evidence_refs):
        if not evidence_ref.ref_id:
            failures.append(
                (
                    "scenario_generation_evidence_ref_required",
                    f"evidence_refs[{index}].ref_id is required",
                )
            )
            break
        if evidence_ref.evidence_kind not in SCENARIO_GENERATION_EVIDENCE_KINDS:
            failures.append(
                (
                    "scenario_generation_evidence_kind_unsupported",
                    f"evidence_refs[{index}].evidence_kind {evidence_ref.evidence_kind!r} is unsupported",
                )
            )
            break
        if not evidence_ref.provenance_label:
            failures.append(
                (
                    "scenario_generation_evidence_provenance_required",
                    f"evidence_refs[{index}].provenance_label is required",
                )
            )
            break

    if failures:
        return ScenarioGenerationRequestValidationResult(
            valid=False,
            fail_closed=True,
            rejection_reason=failures[0][0],
            errors=tuple(message for _, message in failures),
        )

    return ScenarioGenerationRequestValidationResult(
        valid=True,
        fail_closed=False,
        rejection_reason="",
        errors=(),
    )


def build_scenario_generation_request_artifact(
    request: ScenarioGenerationRequest,
    *,
    compiled_scenario: CompiledScenario | None = None,
) -> ScenarioGenerationRequestArtifact:
    validation = validate_scenario_generation_request(request)
    if not validation.valid:
        raise ValueError(
            f"invalid scenario generation request: {validation.rejection_reason}"
        )

    if compiled_scenario is not None:
        baseline_scenario_name = _normalized_text(compiled_scenario.scenario_name)
        baseline_source_path = _normalized_text(compiled_scenario.source_path)
        baseline_zone_count = int(compiled_scenario.zone_count)
        baseline_entity_count = int(compiled_scenario.entity_count)
    else:
        baseline_scenario_name = request.baseline_scenario_ref
        baseline_source_path = ""
        baseline_zone_count = 0
        baseline_entity_count = 0

    artifact = ScenarioGenerationRequestArtifact(
        request=request,
        baseline_scenario_name=baseline_scenario_name,
        baseline_source_path=baseline_source_path,
        baseline_zone_count=baseline_zone_count,
        baseline_entity_count=baseline_entity_count,
    )
    metadata = artifact.to_metadata()
    cloned = _clone_scenario_value(metadata)
    return ScenarioGenerationRequestArtifact(
        request=ScenarioGenerationRequest(**cloned["request"]),
        baseline_scenario_name=str(cloned["baseline_scenario"]["scenario_name"]),
        baseline_source_path=str(cloned["baseline_scenario"]["source_path"]),
        baseline_zone_count=int(cloned["baseline_scenario"]["zone_count"]),
        baseline_entity_count=int(cloned["baseline_scenario"]["entity_count"]),
        authoritative_state_mutation_allowed=bool(
            cloned["authoritative_state_mutation_allowed"]
        ),
    )


__all__ = [
    "SCENARIO_GENERATION_EVIDENCE_KINDS",
    "SCENARIO_GENERATION_REQUEST_CONTRACT_VERSION",
    "SCENARIO_GENERATION_KINDS",
    "SCENARIO_GENERATION_SOURCES",
    "ScenarioGenerationEvidenceRef",
    "ScenarioGenerationRequest",
    "ScenarioGenerationRequestArtifact",
    "ScenarioGenerationRequestValidationResult",
    "build_scenario_generation_request_artifact",
    "validate_scenario_generation_request",
]
