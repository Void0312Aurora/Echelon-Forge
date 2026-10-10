"""Contract-based Policy admission pilot.

Policy categories are author metadata only.  Field/action compatibility and
Agent authority are supplied by their owning catalogues and binding; this
module does not import Gym/SB3 or alter the legacy DecisionModel lifecycle.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

SCHEMA_VERSION = "echelon_forge.policy_contract.v1"


@dataclass(frozen=True)
class FieldSpec:
    name: str
    schema: str
    shape: tuple[int, ...] = ()
    unit: str | None = None
    source_layer: str = "agent_observation"
    required: bool = True

    def __post_init__(self) -> None:
        if not self.name.strip() or not self.schema.strip():
            raise ValueError("field name and schema are required")
        if any(isinstance(dim, bool) or not isinstance(dim, int) or dim < 0 for dim in self.shape):
            raise ValueError("field shape must contain non-negative integers")
        if self.source_layer not in {"agent_observation", "belief", "world_truth", "diagnostics"}:
            raise ValueError(f"unsupported source_layer: {self.source_layer!r}")


@dataclass(frozen=True)
class ObservationContract:
    view_ref: str
    major: int
    minor: int
    required: tuple[FieldSpec, ...] = ()
    optional: tuple[FieldSpec, ...] = ()

    def __post_init__(self) -> None:
        if not self.view_ref.strip() or self.major < 0 or self.minor < 0:
            raise ValueError("observation view identity/version is invalid")
        names = [field.name for field in self.required + self.optional]
        if len(names) != len(set(names)):
            raise ValueError("observation field names must be unique")


@dataclass(frozen=True)
class ActionContract:
    interface_ref: str
    major: int
    minor: int
    dimension: int
    authority_scope: str
    timing: str = "window"

    def __post_init__(self) -> None:
        if not self.interface_ref.strip() or self.major < 0 or self.minor < 0:
            raise ValueError("action interface identity/version is invalid")
        if isinstance(self.dimension, bool) or self.dimension < 0:
            raise ValueError("action dimension must be non-negative")
        if self.timing not in {"window", "per_tick", "per_second"}:
            raise ValueError("unsupported action timing")
        if not self.authority_scope.strip():
            raise ValueError("authority_scope is required")


@dataclass(frozen=True)
class PolicyDescriptor:
    policy_id: str
    version: str
    categories: tuple[str, ...]
    observation: ObservationContract
    action: ActionContract
    stateful: bool = False
    decision_period_s: float | None = None
    legacy_model_kind: str | None = None

    def __post_init__(self) -> None:
        if not self.policy_id.strip() or not self.version.strip():
            raise ValueError("policy identity is required")
        if any(not category.strip() for category in self.categories):
            raise ValueError("policy categories must be non-empty strings")
        if self.decision_period_s is not None and self.decision_period_s <= 0:
            raise ValueError("decision_period_s must be positive")


@dataclass(frozen=True)
class AgentBinding:
    role_id: str
    allowed_source_layers: frozenset[str]
    allowed_action_interfaces: frozenset[str]
    allowed_authority_scopes: frozenset[str]


@dataclass(frozen=True)
class PolicyAdmission:
    admitted: bool
    policy_id: str
    diagnostics: tuple[str, ...]
    schema_version: str = SCHEMA_VERSION

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "admitted": self.admitted,
            "policy_id": self.policy_id,
            "diagnostics": list(self.diagnostics),
        }


def _version_diagnostic(path: str, expected_major: int, actual_major: int, expected_minor: int, actual_minor: int) -> str | None:
    if expected_major != actual_major:
        return f"policy.version_major_mismatch:{path}:{expected_major}!={actual_major}"
    if actual_minor < expected_minor:
        return f"policy.version_minor_too_old:{path}:{actual_minor}<{expected_minor}"
    return None


def admit_policy(
    policy: PolicyDescriptor,
    binding: AgentBinding,
    *,
    field_catalogue: Mapping[str, FieldSpec],
    observation_version: tuple[int, int],
    action_versions: Mapping[str, tuple[int, int]],
    action_dimensions: Mapping[str, int],
) -> PolicyAdmission:
    """Validate policy/Agent compatibility before any runtime side effect."""

    diagnostics: list[str] = []
    version_error = _version_diagnostic(
        "observation", policy.observation.major, observation_version[0], policy.observation.minor, observation_version[1]
    )
    if version_error:
        diagnostics.append(version_error)
    for field in policy.observation.required:
        available = field_catalogue.get(field.name)
        if available is None:
            diagnostics.append(f"policy.required_field_missing:observation.required.{field.name}")
            continue
        if available.schema != field.schema or available.shape != field.shape or available.unit != field.unit:
            diagnostics.append(f"policy.field_semantics_mismatch:observation.required.{field.name}")
        if available.source_layer not in binding.allowed_source_layers:
            diagnostics.append(f"policy.field_source_unauthorized:observation.required.{field.name}")
    for field in policy.observation.optional:
        available = field_catalogue.get(field.name)
        if available is not None and available.source_layer not in binding.allowed_source_layers:
            diagnostics.append(f"policy.field_source_unauthorized:observation.optional.{field.name}")
    action_version = action_versions.get(policy.action.interface_ref)
    if action_version is None:
        diagnostics.append(f"policy.action_interface_unknown:action.interface_ref.{policy.action.interface_ref}")
    else:
        version_error = _version_diagnostic(
            "action", policy.action.major, action_version[0], policy.action.minor, action_version[1]
        )
        if version_error:
            diagnostics.append(version_error)
    dimension = action_dimensions.get(policy.action.interface_ref)
    if dimension is not None and dimension != policy.action.dimension:
        diagnostics.append(f"policy.action_dimension_mismatch:action.dimension:{policy.action.dimension}!={dimension}")
    if policy.action.interface_ref not in binding.allowed_action_interfaces:
        diagnostics.append(f"policy.action_interface_unauthorized:action.interface_ref.{policy.action.interface_ref}")
    if policy.action.authority_scope not in binding.allowed_authority_scopes:
        diagnostics.append(f"policy.authority_scope_unauthorized:action.authority_scope.{policy.action.authority_scope}")
    return PolicyAdmission(not diagnostics, policy.policy_id, tuple(diagnostics))


__all__ = [
    "ActionContract",
    "AgentBinding",
    "FieldSpec",
    "ObservationContract",
    "PolicyAdmission",
    "PolicyDescriptor",
    "SCHEMA_VERSION",
    "admit_policy",
]
