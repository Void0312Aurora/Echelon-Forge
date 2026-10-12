"""Contract-based Policy admission pilot.

Policy categories are author metadata only.  Field/action compatibility and
Agent authority are supplied by their owning catalogues and binding; this
module does not import Gym/SB3 or alter the legacy DecisionModel lifecycle.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any, Callable, Mapping, Sequence

SCHEMA_VERSION = "echelon_forge.policy_contract.v1"


@dataclass(frozen=True)
class FieldSpec:
    name: str
    schema: str
    shape: tuple[int, ...] = ()
    unit: str | None = None
    source_layer: str = "agent_observation"
    required: bool = True
    frame: str | None = None

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
        if (
            isinstance(self.dimension, bool)
            or not isinstance(self.dimension, int)
            or self.dimension < 0
        ):
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
        if self.decision_period_s is not None and (
            not math.isfinite(self.decision_period_s) or self.decision_period_s <= 0
        ):
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


class PolicyRuntimeBinding:
    """Bind one admitted Policy to an existing decision-model lifecycle.

    The wrapper owns contract checks and observation provenance only. The
    wrapped model remains the owner of reset/decision/close behavior and its
    action DTO; no second runtime or action interface is introduced.
    """

    def __init__(
        self,
        policy: PolicyDescriptor,
        admission: PolicyAdmission,
        model: Any,
        *,
        bounds: Sequence[tuple[float, float]],
        timing: str,
        optional_defaults: Mapping[str, Any] | None = None,
        observation_projector: Callable[[tuple[Any, ...], tuple[str, ...]], Any] | None = None,
        action_values: Callable[[Any], Sequence[float]] | None = None,
    ) -> None:
        if not admission.admitted or admission.policy_id != policy.policy_id:
            raise ValueError("policy.runtime_binding_not_admitted")
        if not all(callable(getattr(model, name, None)) for name in ("reset", "decide", "close")):
            raise TypeError("policy runtime model must implement reset/decide/close")
        if timing != policy.action.timing:
            raise ValueError("policy.action_timing_mismatch:action.timing")
        if len(bounds) != policy.action.dimension:
            raise ValueError("policy.action_dimension_mismatch:action.bounds")
        self.policy = policy
        self.admission = admission
        self.model = model
        self.bounds = tuple(bounds)
        self.timing = timing
        self.optional_defaults = dict(optional_defaults or {})
        self._observation_projector = observation_projector or (lambda values, _sources: values)
        self._action_values = action_values or self._default_action_values

    @property
    def model_kind(self) -> str | None:
        value = getattr(self.model, "model_kind", getattr(self.model, "_decision_model_kind", None))
        return None if value is None else str(value)

    @staticmethod
    def _default_action_values(action: Any) -> Sequence[float]:
        if isinstance(action, (str, bytes)) or not isinstance(action, Sequence):
            raise TypeError("policy action extractor is required for non-sequence owner actions")
        return action

    def reset(self, *, context: Any) -> None:
        self.model.reset(context=context)

    def decide(self, *, observation: Any, context: Any, dt: float) -> Any:
        if not isinstance(observation, Mapping):
            raise TypeError("policy runtime observation must be a field mapping")
        projected, sources = project_policy_observation(
            self.policy,
            self.admission,
            observation,
            optional_defaults=self.optional_defaults,
        )
        owner_observation = self._observation_projector(projected, sources)
        model_context = dict(context) if isinstance(context, Mapping) else {}
        model_context.update(
            {
                "policy_id": self.policy.policy_id,
                "policy_version": self.policy.version,
                "observation_provenance": sources,
            }
        )
        action = self.model.decide(
            observation=owner_observation,
            context=model_context,
            dt=dt,
        )
        errors = validate_policy_action(
            self.policy,
            self._action_values(action),
            bounds=self.bounds,
            timing=self.timing,
        )
        if errors:
            raise ValueError(";".join(errors))
        return action

    def close(self) -> None:
        self.model.close()


def _version_diagnostic(
    path: str, expected_major: int, actual_major: int, expected_minor: int, actual_minor: int
) -> str | None:
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
    action_timings: Mapping[str, str] | None = None,
) -> PolicyAdmission:
    """Validate policy/Agent compatibility before any runtime side effect."""

    diagnostics: list[str] = []
    version_error = _version_diagnostic(
        "observation",
        policy.observation.major,
        observation_version[0],
        policy.observation.minor,
        observation_version[1],
    )
    if version_error:
        diagnostics.append(version_error)
    for field in policy.observation.required:
        available = field_catalogue.get(field.name)
        if available is None:
            diagnostics.append(f"policy.required_field_missing:observation.required.{field.name}")
            continue
        if (
            available.schema,
            available.shape,
            available.unit,
            available.source_layer,
            available.frame,
        ) != (field.schema, field.shape, field.unit, field.source_layer, field.frame):
            diagnostics.append(f"policy.field_semantics_mismatch:observation.required.{field.name}")
        if available.source_layer not in binding.allowed_source_layers:
            diagnostics.append(
                f"policy.field_source_unauthorized:observation.required.{field.name}"
            )
    for field in policy.observation.optional:
        available = field_catalogue.get(field.name)
        if available is None:
            continue
        if (
            available.schema,
            available.shape,
            available.unit,
            available.source_layer,
            available.frame,
        ) != (field.schema, field.shape, field.unit, field.source_layer, field.frame):
            diagnostics.append(f"policy.field_semantics_mismatch:observation.optional.{field.name}")
        if available.source_layer not in binding.allowed_source_layers:
            diagnostics.append(
                f"policy.field_source_unauthorized:observation.optional.{field.name}"
            )
    action_version = action_versions.get(policy.action.interface_ref)
    if action_version is None:
        diagnostics.append(
            f"policy.action_interface_unknown:action.interface_ref.{policy.action.interface_ref}"
        )
    else:
        version_error = _version_diagnostic(
            "action", policy.action.major, action_version[0], policy.action.minor, action_version[1]
        )
        if version_error:
            diagnostics.append(version_error)
    if action_version is not None:
        dimension = action_dimensions.get(policy.action.interface_ref)
        if dimension is None:
            diagnostics.append(
                f"policy.action_dimension_missing:action.dimension.{policy.action.interface_ref}"
            )
        elif dimension != policy.action.dimension:
            diagnostics.append(
                f"policy.action_dimension_mismatch:action.dimension:{policy.action.dimension}!={dimension}"
            )
    if policy.action.interface_ref not in binding.allowed_action_interfaces:
        diagnostics.append(
            f"policy.action_interface_unauthorized:action.interface_ref.{policy.action.interface_ref}"
        )
    if policy.action.authority_scope not in binding.allowed_authority_scopes:
        diagnostics.append(
            f"policy.authority_scope_unauthorized:action.authority_scope.{policy.action.authority_scope}"
        )
    if (
        action_timings is not None
        and action_timings.get(policy.action.interface_ref) != policy.action.timing
    ):
        diagnostics.append("policy.action_timing_mismatch:action.timing")
    return PolicyAdmission(not diagnostics, policy.policy_id, tuple(diagnostics))


def validate_policy_action(
    policy: PolicyDescriptor,
    values: Sequence[float],
    *,
    bounds: Sequence[tuple[float, float]],
    timing: str,
) -> tuple[str, ...]:
    """Check a pilot action before invoking its existing owner projection."""
    errors: list[str] = []
    if timing != policy.action.timing:
        errors.append("policy.action_timing_mismatch:action.timing")
    if len(values) != policy.action.dimension or len(bounds) != policy.action.dimension:
        return tuple(errors + ["policy.action_dimension_mismatch:action.values"])
    for index, (value, (low, high)) in enumerate(zip(values, bounds)):
        if not math.isfinite(low) or not math.isfinite(high) or low > high:
            raise ValueError("owner action bounds must be finite and ordered")
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
            or not low <= value <= high
        ):
            errors.append(f"policy.action_out_of_bounds:action.values[{index}]")
    return tuple(errors)


def select_policy(
    policies: Mapping[str, PolicyDescriptor],
    *,
    policy_ref: str | None = None,
    categories: frozenset[str] = frozenset(),
    legacy_model_kind: str | None = None,
) -> PolicyDescriptor:
    """Resolve metadata supplied by an existing registry; never import code."""
    candidates = (
        [policies[policy_ref]]
        if policy_ref in policies
        else ([] if policy_ref else list(policies.values()))
    )
    candidates = [p for p in candidates if categories.issubset(p.categories)]
    if not candidates:
        raise ValueError("policy.selection_missing")
    if len(candidates) != 1:
        raise ValueError("policy.selection_ambiguous")
    selected = candidates[0]
    if legacy_model_kind is not None and selected.legacy_model_kind != legacy_model_kind:
        raise ValueError("policy.legacy_model_kind_mismatch")
    return selected


def project_policy_observation(
    policy: PolicyDescriptor,
    admission: PolicyAdmission,
    values: Mapping[str, Any],
    *,
    optional_defaults: Mapping[str, Any],
) -> tuple[tuple[Any, ...], tuple[str, ...]]:
    """Preserve declared field order and explicitly identify default provenance.

    This bounded numeric projection follows admission; domain owners still own
    normalization/tensor encoding. Absent optional values are never invented.
    """
    if not admission.admitted or admission.policy_id != policy.policy_id:
        raise ValueError("policy.projection_not_admitted")

    def checked(value: Any, shape: tuple[int, ...], name: str) -> Any:
        if not shape:
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(value)
            ):
                raise ValueError(f"policy.field_value_invalid:{name}")
            return value
        if not isinstance(value, (list, tuple)) or len(value) != shape[0]:
            raise ValueError(f"policy.field_shape_mismatch:{name}")
        return tuple(checked(child, shape[1:], name) for child in value)

    projected: list[Any] = []
    provenance: list[str] = []
    required_names = {field.name for field in policy.observation.required}
    for field in policy.observation.required + policy.observation.optional:
        if field.name in values:
            value = values[field.name]
            provenance.append(f"{field.source_layer}:{field.name}")
        elif field.name not in required_names and field.name in optional_defaults:
            value = optional_defaults[field.name]
            provenance.append(f"explicit_default:{field.name}")
        else:
            raise ValueError(f"policy.field_value_missing:{field.name}")
        projected.append(checked(value, field.shape, field.name))
    return tuple(projected), tuple(provenance)


__all__ = [
    "ActionContract",
    "AgentBinding",
    "FieldSpec",
    "ObservationContract",
    "PolicyAdmission",
    "PolicyDescriptor",
    "PolicyRuntimeBinding",
    "SCHEMA_VERSION",
    "admit_policy",
    "select_policy",
    "validate_policy_action",
    "project_policy_observation",
]
