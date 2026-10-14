"""Contract-based Policy admission pilot.

Policy categories are author metadata only.  Field/action compatibility and
Agent authority are supplied by their owning catalogues and binding; this
module does not import Gym/SB3 or alter the legacy DecisionModel lifecycle.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import math
import string
from typing import Any, Callable, Mapping, Sequence

SCHEMA_VERSION = "echelon_forge.policy_contract.v1"
CHECKPOINT_SCHEMA_VERSION = "echelon_forge.policy_checkpoint_binding.v1"


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
class PolicyCheckpoint:
    """Owner-issued metadata for an external policy artifact.

    This records compatibility and content identity only.  Loading the model
    bytes and implementing the domain action endpoint remain owner operations.
    """

    checkpoint_ref: str
    artifact_sha256: str
    policy_id: str
    policy_version: str
    observation_view_ref: str
    observation_major: int
    observation_minor: int
    action_interface_ref: str
    action_major: int
    action_minor: int
    owner_ref: str
    schema_version: str = CHECKPOINT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for field_name in (
            "checkpoint_ref",
            "policy_id",
            "policy_version",
            "observation_view_ref",
            "action_interface_ref",
            "owner_ref",
        ):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} must be a non-empty string")
        if self.schema_version != CHECKPOINT_SCHEMA_VERSION:
            raise ValueError("unsupported policy checkpoint schema version")
        if not isinstance(self.artifact_sha256, str):
            raise ValueError("artifact_sha256 must be a 64-character hexadecimal digest")
        digest = self.artifact_sha256.lower()
        if len(digest) != 64 or any(character not in string.hexdigits for character in digest):
            raise ValueError("artifact_sha256 must be a 64-character hexadecimal digest")
        object.__setattr__(self, "artifact_sha256", digest)
        for field_name in (
            "observation_major",
            "observation_minor",
            "action_major",
            "action_minor",
        ):
            value = getattr(self, field_name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"{field_name} must be a non-negative integer")

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "checkpoint_ref": self.checkpoint_ref,
            "artifact_sha256": self.artifact_sha256,
            "policy_id": self.policy_id,
            "policy_version": self.policy_version,
            "observation_view_ref": self.observation_view_ref,
            "observation_major": self.observation_major,
            "observation_minor": self.observation_minor,
            "action_interface_ref": self.action_interface_ref,
            "action_major": self.action_major,
            "action_minor": self.action_minor,
            "owner_ref": self.owner_ref,
        }


class PolicyCheckpointLoadError(ValueError):
    """Raised when verified checkpoint bytes cannot be handed to the owner."""


def load_policy_checkpoint(
    checkpoint: PolicyCheckpoint,
    artifact: bytes | bytearray | memoryview,
    *,
    owner_loader: Callable[[bytes], Any],
) -> Any:
    """Verify checkpoint bytes, then delegate model loading to the owner.

    The contract layer owns byte identity and the model protocol boundary. It
    deliberately does not deserialize frameworks, import model code, or create
    an action endpoint; ``owner_loader`` remains responsible for those domain
    operations and receives an immutable byte copy only after digest checking.
    """

    if not isinstance(checkpoint, PolicyCheckpoint):
        raise TypeError("policy checkpoint loader requires PolicyCheckpoint")
    if not callable(owner_loader):
        raise TypeError("policy checkpoint owner_loader must be callable")
    try:
        payload = bytes(artifact)
    except (TypeError, ValueError) as exc:
        raise PolicyCheckpointLoadError("policy.checkpoint_artifact_bytes_invalid") from exc
    digest = hashlib.sha256(payload).hexdigest()
    if digest != checkpoint.artifact_sha256:
        raise PolicyCheckpointLoadError(
            "policy.checkpoint_artifact_digest_mismatch:"
            f"{digest}!={checkpoint.artifact_sha256}"
        )
    try:
        model = owner_loader(payload)
    except Exception as exc:  # pragma: no cover - owner-specific failure
        raise PolicyCheckpointLoadError("policy.checkpoint_owner_load_failed") from exc
    if not all(callable(getattr(model, name, None)) for name in ("reset", "decide", "close")):
        raise PolicyCheckpointLoadError("policy.checkpoint_owner_model_protocol_invalid")
    return model


@dataclass(frozen=True)
class _AdmissionValidationToken:
    """Private snapshot binding an admission marker to its validated fields."""

    admitted: bool
    policy_id: str
    diagnostics: tuple[str, ...]
    checkpoint: PolicyCheckpoint | None
    observation_view_ref: str | None
    observation_view_schema_version: str | None


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
    checkpoint: PolicyCheckpoint | None = None

    def __post_init__(self) -> None:
        if not self.policy_id.strip() or not self.version.strip():
            raise ValueError("policy identity is required")
        if any(not category.strip() for category in self.categories):
            raise ValueError("policy categories must be non-empty strings")
        if self.decision_period_s is not None and (
            not math.isfinite(self.decision_period_s) or self.decision_period_s <= 0
        ):
            raise ValueError("decision_period_s must be positive")
        if self.checkpoint is not None:
            if not isinstance(self.checkpoint, PolicyCheckpoint):
                raise TypeError("checkpoint must be a PolicyCheckpoint")
            if self.checkpoint.policy_id != self.policy_id:
                raise ValueError("checkpoint policy_id does not match policy")
            if self.checkpoint.policy_version != self.version:
                raise ValueError("checkpoint policy_version does not match policy")
            if (
                self.checkpoint.observation_view_ref != self.observation.view_ref
                or self.checkpoint.observation_major != self.observation.major
                or self.checkpoint.observation_minor != self.observation.minor
            ):
                raise ValueError("checkpoint observation contract does not match policy")
            if (
                self.checkpoint.action_interface_ref != self.action.interface_ref
                or self.checkpoint.action_major != self.action.major
                or self.checkpoint.action_minor != self.action.minor
            ):
                raise ValueError("checkpoint action contract does not match policy")


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
    checkpoint: PolicyCheckpoint | None = None
    observation_view_ref: str | None = None
    observation_view_schema_version: str | None = None
    _validation_marker: _AdmissionValidationToken | None = field(
        default=None, repr=False, compare=False
    )

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "admitted": self.admitted,
            "policy_id": self.policy_id,
            "diagnostics": list(self.diagnostics),
            "checkpoint": None if self.checkpoint is None else self.checkpoint.as_dict(),
            "observation_view_ref": self.observation_view_ref,
            "observation_view_schema_version": self.observation_view_schema_version,
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
        action_authorizer: Callable[[Any, Mapping[str, Any], float], Sequence[str] | str | bool | None]
        | None = None,
        action_projector: Callable[[Any], Any] | None = None,
    ) -> None:
        if not admission.admitted or admission.policy_id != policy.policy_id:
            raise ValueError("policy.runtime_binding_not_admitted")
        expected_validation_token = _AdmissionValidationToken(
            admitted=admission.admitted,
            policy_id=admission.policy_id,
            diagnostics=admission.diagnostics,
            checkpoint=admission.checkpoint,
            observation_view_ref=admission.observation_view_ref,
            observation_view_schema_version=admission.observation_view_schema_version,
        )
        if admission._validation_marker != expected_validation_token:
            raise ValueError("policy.runtime_binding_admission_not_owner_validated")
        if admission.checkpoint != policy.checkpoint:
            raise ValueError("policy.runtime_binding_checkpoint_mismatch")
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
        self._action_authorizer = action_authorizer
        self._action_projector = action_projector or (lambda value: value)
        if self._action_authorizer is not None and not callable(self._action_authorizer):
            raise TypeError("policy action_authorizer must be callable")
        if not callable(self._action_projector):
            raise TypeError("policy action_projector must be callable")

    @classmethod
    def from_checkpoint_artifact(
        cls,
        policy: PolicyDescriptor,
        admission: PolicyAdmission,
        artifact: bytes | bytearray | memoryview,
        *,
        owner_loader: Callable[[bytes], Any],
        bounds: Sequence[tuple[float, float]],
        timing: str,
        optional_defaults: Mapping[str, Any] | None = None,
        observation_projector: Callable[[tuple[Any, ...], tuple[str, ...]], Any] | None = None,
        action_values: Callable[[Any], Sequence[float]] | None = None,
        action_authorizer: Callable[[Any, Mapping[str, Any], float], Sequence[str] | str | bool | None]
        | None = None,
        action_projector: Callable[[Any], Any] | None = None,
    ) -> "PolicyRuntimeBinding":
        """Load verified owner bytes and construct the admitted binding."""

        if policy.checkpoint is None:
            raise PolicyCheckpointLoadError("policy.checkpoint_required_for_artifact_binding")
        model = load_policy_checkpoint(
            policy.checkpoint,
            artifact,
            owner_loader=owner_loader,
        )
        return cls(
            policy,
            admission,
            model,
            bounds=bounds,
            timing=timing,
            optional_defaults=optional_defaults,
            observation_projector=observation_projector,
            action_values=action_values,
            action_authorizer=action_authorizer,
            action_projector=action_projector,
        )

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
        if self.admission.observation_view_ref is not None:
            model_context.update(
                {
                    "policy_observation_view_ref": self.admission.observation_view_ref,
                    "policy_observation_view_schema_version": (
                        self.admission.observation_view_schema_version
                    ),
                }
            )
        if self.admission.checkpoint is not None:
            model_context.update(
                {
                    "policy_checkpoint_ref": self.admission.checkpoint.checkpoint_ref,
                    "policy_checkpoint_sha256": self.admission.checkpoint.artifact_sha256,
                    "policy_checkpoint_owner": self.admission.checkpoint.owner_ref,
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
        if self._action_authorizer is not None:
            try:
                owner_errors = self._action_authorizer(action, model_context, dt)
            except Exception as exc:  # pragma: no cover - owner-specific failure
                raise ValueError("policy.action_owner_validation_failed") from exc
            if owner_errors is False:
                owner_errors = ("policy.action_owner_rejected",)
            elif owner_errors is True or owner_errors is None:
                owner_errors = ()
            elif isinstance(owner_errors, str):
                owner_errors = (owner_errors,)
            else:
                try:
                    owner_errors = tuple(str(error) for error in owner_errors)
                except TypeError as exc:
                    raise TypeError(
                        "policy action_authorizer must return bool, str, sequence or None"
                    ) from exc
            if owner_errors:
                raise ValueError(";".join(owner_errors))
        return self._action_projector(action)

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


def _schema_version_parts(version: Any) -> tuple[int, int] | None:
    text = str(version)
    major_text, separator, minor_text = text.partition(".")
    if not separator or not major_text.isdecimal() or not minor_text.isdecimal():
        return None
    return int(major_text), int(minor_text)


def _admit_selected_observation_view(
    observation_view: Any,
    observation_view_admitter: Callable[[Any], Any] | None = None,
) -> tuple[str, str, tuple[int, int]]:
    """Admit an observation view through an injected owner seam.

    The neutral contract performs only shape checks when no owner callback is
    supplied.  Runtime adapters can inject their maintained owner validator
    without making this contracts package import a runtime implementation.
    """

    try:
        admitted = (
            observation_view
            if observation_view_admitter is None
            else observation_view_admitter(observation_view)
        )
        schema_version = str(getattr(admitted, "schema_version", ""))
        version = _schema_version_parts(schema_version)
        if version is None or version[0] != 1:
            raise ValueError("observation view schema version must be a valid 1.x value")
        if not str(getattr(admitted, "view_id", "")):
            raise ValueError("observation view must declare a non-empty view_id")
    except Exception as exc:
        raise ValueError(f"policy.observation_view_invalid:{exc}") from exc
    view_ref = str(getattr(admitted, "view_id", ""))
    if not view_ref or version is None:
        raise ValueError("policy.observation_view_identity_invalid")
    return view_ref, schema_version, version


def admit_policy(
    policy: PolicyDescriptor,
    binding: AgentBinding,
    *,
    field_catalogue: Mapping[str, FieldSpec],
    observation_version: tuple[int, int],
    action_versions: Mapping[str, tuple[int, int]],
    action_dimensions: Mapping[str, int],
    action_timings: Mapping[str, str] | None = None,
    checkpoint: PolicyCheckpoint | None = None,
    observation_view: Any | None = None,
    observation_view_admitter: Callable[[Any], Any] | None = None,
) -> PolicyAdmission:
    """Validate policy/Agent compatibility before any runtime side effect."""

    diagnostics: list[str] = []
    if policy.checkpoint is None:
        if checkpoint is not None:
            diagnostics.append("policy.checkpoint_unexpected")
    elif checkpoint is None:
        diagnostics.append("policy.checkpoint_missing")
    elif checkpoint != policy.checkpoint:
        diagnostics.append("policy.checkpoint_identity_mismatch")
    admitted_view_ref: str | None = None
    admitted_view_schema_version: str | None = None
    effective_observation_version = observation_version
    if observation_view is not None:
        try:
            admitted_view_ref, admitted_view_schema_version, view_version = (
                _admit_selected_observation_view(
                    observation_view, observation_view_admitter
                )
            )
        except ValueError as exc:
            diagnostics.append(str(exc))
        else:
            if admitted_view_ref != policy.observation.view_ref:
                diagnostics.append(
                    "policy.observation_view_ref_mismatch:"
                    f"{policy.observation.view_ref}!={admitted_view_ref}"
                )
            if view_version != observation_version:
                diagnostics.append(
                    "policy.observation_view_version_mismatch:"
                    f"{observation_version}!={view_version}"
                )
            effective_observation_version = view_version
    version_error = _version_diagnostic(
        "observation",
        policy.observation.major,
        effective_observation_version[0],
        policy.observation.minor,
        effective_observation_version[1],
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
    admitted = not diagnostics
    admitted_checkpoint = checkpoint if checkpoint == policy.checkpoint else None
    return PolicyAdmission(
        admitted,
        policy.policy_id,
        tuple(diagnostics),
        checkpoint=admitted_checkpoint,
        observation_view_ref=admitted_view_ref,
        observation_view_schema_version=admitted_view_schema_version,
        _validation_marker=_AdmissionValidationToken(
            admitted=admitted,
            policy_id=policy.policy_id,
            diagnostics=tuple(diagnostics),
            checkpoint=admitted_checkpoint,
            observation_view_ref=admitted_view_ref,
            observation_view_schema_version=admitted_view_schema_version,
        ),
    )


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
    "PolicyCheckpoint",
    "PolicyCheckpointLoadError",
    "PolicyDescriptor",
    "PolicyRuntimeBinding",
    "SCHEMA_VERSION",
    "CHECKPOINT_SCHEMA_VERSION",
    "admit_policy",
    "load_policy_checkpoint",
    "select_policy",
    "validate_policy_action",
    "project_policy_observation",
]
