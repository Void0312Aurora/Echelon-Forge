from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping


class MechanismRole(str, Enum):
    EXECUTABLE = "executable"
    ADAPTER_COUPLED = "adapter_coupled"
    AUXILIARY_ONLY = "auxiliary_only"
    DIAGNOSTIC_ONLY = "diagnostic_only"


class FaultStage(str, Enum):
    OBSERVATION = "observation"
    SUPPORT = "support"
    LABEL = "label"
    REPRESENTATION = "representation"
    LOSS_OBJECT = "loss_object"
    OPTIMIZER = "optimizer"
    ADAPTER = "adapter"
    EVALUATION = "evaluation"


class SupportPopulation(str, Enum):
    POLICY_VISIBLE_SUPPORT = "policy_visible_support"
    RUNTIME_GATE_TRUTH = "runtime_gate_truth"
    COLLECTION_SUPPORT = "collection_support"
    REPLAY_SUPPORT = "replay_support"
    CALIBRATION_POPULATION = "calibration_population"
    EXECUTION_SUPPORT = "execution_support"


class ConfigExpectation(str, Enum):
    EQUALS = "equals"
    REQUIRED_TRUE = "required_true"
    REQUIRED_FALSE = "required_false"
    POSITIVE_NUMBER = "positive_number"


class LaunchDecisionMode(str, Enum):
    """Named executable-owner profiles for the hybrid event decision."""

    LEGACY_COMPOSED_V0 = "legacy_composed_v0"
    DIRECT_BOUNDARY_V1_STRICT = "direct_boundary_v1_strict"
    GOVERNED_COMPOSED_V1 = "governed_composed_v1"
    AUXILIARY_ONLY_V1 = "auxiliary_only_v1"
    ADAPTER_COUPLED_V1 = "adapter_coupled_v1"


class LaunchDecisionContributor(str, Enum):
    """Contributors that may appear in an event-delta composition trace."""

    BASE_ACTION = "base_action"
    HMOE_EVENT_SLICE = "hmoe_event_slice"
    HYBRID_EVENT_HEAD = "hybrid_event_head"
    WINDOW_CLASSIFIER_ADAPTER = "window_classifier_adapter"
    STOPPING_ADAPTER = "stopping_adapter"


class LaunchDecisionTrainingScope(str, Enum):
    """Update lanes whose parameter write set is owned by the contract."""

    COMPATIBILITY = "compatibility"
    ORDINARY_PPO = "ordinary_ppo"
    DIRECT_BOUNDARY = "direct_boundary"
    EVENT_POLICY_MARGIN = "event_policy_margin"
    AUXILIARY = "auxiliary"


LAUNCH_DECISION_CONTRACT_SCHEMA_VERSION = "launch_decision_owner_v1"
LAUNCH_DECISION_MODE_PATH = ("hyperparameters", "policy_kwargs", "launch_decision_mode")
LAUNCH_DECISION_OWNER_MODE_PATH = (
    "hyperparameters",
    "policy_kwargs",
    "launch_decision_owner_mode",
)


class LaunchDecisionContractError(ValueError):
    """Raised when a configuration cannot resolve to one owner contract."""

    def __init__(self, violations: tuple["ContractViolation", ...]):
        self.violations = violations
        detail = "; ".join(
            f"{violation.path}: {violation.reason}"
            for violation in violations
        )
        super().__init__(detail or "launch-decision contract resolution failed")


_MISSING = object()


@dataclass(frozen=True)
class FaultLocalizationResult:
    stage: FaultStage
    passed: bool
    verdict: str
    evidence: Mapping[str, float | int | str | bool] = field(default_factory=dict)
    blocks_feature_addition: bool = True
    checked: bool = True

    def as_dict(self) -> dict[str, Any]:
        return {
            "stage": self.stage.value,
            "passed": bool(self.passed),
            "verdict": self.verdict,
            "evidence": dict(self.evidence),
            "blocks_feature_addition": bool(self.blocks_feature_addition),
            "checked": bool(self.checked),
        }


@dataclass(frozen=True)
class ConfigGate:
    path: tuple[str, ...]
    expectation: ConfigExpectation
    reason: str
    expected: Any = None


@dataclass(frozen=True)
class ContractViolation:
    mechanism_id: str
    path: str
    expected: str
    actual: Any
    reason: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "mechanism_id": self.mechanism_id,
            "path": self.path,
            "expected": self.expected,
            "actual": self.actual,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class LaunchDecisionOwnerContract:
    """Resolved, serializable authority envelope for one launch-decision mode.

    The envelope deliberately describes ownership rather than tensor values.
    Forward-path code can use it to decide which contributors are admitted and
    training code can use it to audit the exact parameter roles allowed to
    receive a gradient in each update lane.
    """

    mode: LaunchDecisionMode
    contributors: tuple[LaunchDecisionContributor, ...]
    trainable_parameter_roles: tuple[str, ...]
    detached_parameter_roles: tuple[str, ...]
    allowed_training_scopes: tuple[LaunchDecisionTrainingScope, ...]
    compatibility_mode: str
    compatibility_precedence: str | None
    ignored_contributors: tuple[LaunchDecisionContributor, ...]
    acceptance_eligible: bool
    explicit_mode: bool
    schema_version: str = LAUNCH_DECISION_CONTRACT_SCHEMA_VERSION

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "mode": self.mode.value,
            "contributors": [item.value for item in self.contributors],
            "trainable_parameter_roles": list(self.trainable_parameter_roles),
            "detached_parameter_roles": list(self.detached_parameter_roles),
            "allowed_training_scopes": [item.value for item in self.allowed_training_scopes],
            "compatibility_mode": self.compatibility_mode,
            "compatibility_precedence": self.compatibility_precedence,
            "ignored_contributors": [item.value for item in self.ignored_contributors],
            "acceptance_eligible": bool(self.acceptance_eligible),
            "explicit_mode": bool(self.explicit_mode),
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "LaunchDecisionOwnerContract":
        """Restore an envelope and reject unknown/invalid enum values."""

        if not isinstance(payload, Mapping):
            raise TypeError("launch-decision owner contract must be a mapping")
        schema_version = str(payload.get("schema_version", ""))
        if schema_version != LAUNCH_DECISION_CONTRACT_SCHEMA_VERSION:
            raise ValueError(
                "unsupported launch-decision contract schema: "
                f"{schema_version!r}"
            )
        try:
            mode = LaunchDecisionMode(str(payload["mode"]))
            contributors = tuple(
                LaunchDecisionContributor(str(item))
                for item in payload.get("contributors", ())
            )
            scopes = tuple(
                LaunchDecisionTrainingScope(str(item))
                for item in payload.get("allowed_training_scopes", ())
            )
            ignored = tuple(
                LaunchDecisionContributor(str(item))
                for item in payload.get("ignored_contributors", ())
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("invalid launch-decision owner contract enum") from exc
        return cls(
            mode=mode,
            contributors=contributors,
            trainable_parameter_roles=tuple(
                str(item) for item in payload.get("trainable_parameter_roles", ())
            ),
            detached_parameter_roles=tuple(
                str(item) for item in payload.get("detached_parameter_roles", ())
            ),
            allowed_training_scopes=scopes,
            compatibility_mode=str(payload.get("compatibility_mode", "none")),
            compatibility_precedence=(
                None
                if payload.get("compatibility_precedence") is None
                else str(payload["compatibility_precedence"])
            ),
            ignored_contributors=ignored,
            acceptance_eligible=bool(payload.get("acceptance_eligible", False)),
            explicit_mode=bool(payload.get("explicit_mode", False)),
            schema_version=schema_version,
        )


@dataclass(frozen=True)
class ModelMechanismContract:
    mechanism_id: str
    role: MechanismRole
    owner: str
    activation_paths: tuple[tuple[str, ...], ...]
    fault_stages: tuple[FaultStage, ...]
    input_support: tuple[SupportPopulation, ...]
    loss_owner: str
    adapter_coupling: str
    required_probe_stages: tuple[FaultStage, ...]
    held_boundary: str
    config_gates: tuple[ConfigGate, ...] = ()
    normalization_population: SupportPopulation | None = None

    def is_active(self, config: Mapping[str, Any]) -> bool:
        return any(_activation_value(_value_at(config, path)) for path in self.activation_paths)


def _format_path(path: tuple[str, ...]) -> str:
    return ".".join(path)


def _value_at(config: Mapping[str, Any], path: tuple[str, ...]) -> Any:
    value: Any = config
    for key in path:
        if not isinstance(value, Mapping) or key not in value:
            return _MISSING
        value = value[key]
    return value


def _activation_value(value: Any) -> bool:
    if value is _MISSING or value is None:
        return False
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return float(value) > 0.0
    if isinstance(value, str):
        return bool(value.strip())
    return bool(value)


def _gate_passes(actual: Any, gate: ConfigGate) -> bool:
    if actual is _MISSING:
        return False
    if gate.expectation == ConfigExpectation.EQUALS:
        return actual == gate.expected
    if gate.expectation == ConfigExpectation.REQUIRED_TRUE:
        return bool(actual) is True
    if gate.expectation == ConfigExpectation.REQUIRED_FALSE:
        return bool(actual) is False
    if gate.expectation == ConfigExpectation.POSITIVE_NUMBER:
        return not isinstance(actual, bool) and isinstance(actual, (int, float)) and float(actual) > 0.0
    raise ValueError(f"Unhandled config expectation: {gate.expectation}")


def _expectation_label(gate: ConfigGate) -> str:
    if gate.expectation == ConfigExpectation.EQUALS:
        return repr(gate.expected)
    if gate.expectation == ConfigExpectation.REQUIRED_TRUE:
        return "true"
    if gate.expectation == ConfigExpectation.REQUIRED_FALSE:
        return "false"
    if gate.expectation == ConfigExpectation.POSITIVE_NUMBER:
        return "positive number"
    return gate.expectation.value


def _launch_decision_policy_kwargs(config: Mapping[str, Any]) -> Mapping[str, Any]:
    """Return the policy kwargs mapping from either supported config shape."""

    hyperparameters = config.get("hyperparameters", {})
    if isinstance(hyperparameters, Mapping):
        policy_kwargs = hyperparameters.get("policy_kwargs", {})
        if isinstance(policy_kwargs, Mapping):
            return policy_kwargs
    policy_kwargs = config.get("policy_kwargs", {})
    if isinstance(policy_kwargs, Mapping):
        return policy_kwargs
    return {}


def _launch_decision_value(config: Mapping[str, Any], key: str) -> Any:
    policy_kwargs = _launch_decision_policy_kwargs(config)
    if key in policy_kwargs:
        return policy_kwargs[key]
    hyperparameters = config.get("hyperparameters", {})
    if isinstance(hyperparameters, Mapping) and key in hyperparameters:
        return hyperparameters[key]
    if key in config:
        return config[key]
    return _MISSING


def _launch_decision_bool(value: Any) -> bool:
    return _activation_value(value)


def _launch_decision_positive(value: Any) -> bool:
    return (
        not isinstance(value, bool)
        and isinstance(value, (int, float))
        and float(value) > 0.0
    )


def _launch_decision_mode_value(
    config: Mapping[str, Any],
) -> tuple[LaunchDecisionMode | None, bool, str | None, Any]:
    """Resolve an explicit mode, keeping old configs in compatibility mode."""

    mode_raw = _launch_decision_value(config, "launch_decision_mode")
    owner_raw = _launch_decision_value(config, "launch_decision_owner_mode")
    raw = mode_raw if mode_raw is not _MISSING else owner_raw
    explicit = raw is not _MISSING and raw is not None and str(raw).strip() != ""
    path = (
        "hyperparameters.policy_kwargs.launch_decision_mode"
        if mode_raw is not _MISSING
        else "hyperparameters.policy_kwargs.launch_decision_owner_mode"
        if owner_raw is not _MISSING
        else None
    )
    if raw is _MISSING or raw is None or str(raw).strip() == "":
        return LaunchDecisionMode.LEGACY_COMPOSED_V0, False, path, raw
    if isinstance(raw, LaunchDecisionMode):
        return raw, explicit, path, raw
    try:
        return LaunchDecisionMode(str(raw)), explicit, path, raw
    except ValueError:
        return None, explicit, path, raw


def _launch_decision_mode_violation(
    *,
    path: str,
    expected: str,
    actual: Any,
    reason: str,
) -> ContractViolation:
    return ContractViolation(
        mechanism_id="launch_decision.owner_contract",
        path=path,
        expected=expected,
        actual=actual,
        reason=reason,
    )


def _launch_decision_active_flags(config: Mapping[str, Any]) -> dict[str, bool]:
    return {
        "base_action": _launch_decision_value(config, "hybrid_action_spec")
        == "air_combat_hybrid_v1",
        "hmoe_event_slice": any(
            _launch_decision_positive(_launch_decision_value(config, key))
            for key in ("hmoe_residual_scale", "hmoe_head_lr_scale")
        )
        or _launch_decision_bool(_launch_decision_value(config, "hmoe_enabled")),
        "hybrid_event_head": _launch_decision_positive(
            _launch_decision_value(config, "hybrid_event_head_lr_scale")
        ),
        "window_classifier_adapter": _launch_decision_bool(
            _launch_decision_value(config, "hybrid_event_use_window_classifier_head")
        ),
        "stopping_adapter": _launch_decision_bool(
            _launch_decision_value(config, "hybrid_event_use_stopping_head")
        ),
    }


def validate_launch_decision_contract(
    config: Mapping[str, Any],
) -> list[ContractViolation]:
    """Validate the explicit launch-decision owner and adapter boundaries.

    Configurations without the new mode key are intentionally treated as
    ``legacy_composed_v0``. This keeps existing checkpoints loadable while
    making every new configuration opt into a fail-closed mode.
    """

    violations: list[ContractViolation] = []
    mode, explicit, mode_path, raw_mode = _launch_decision_mode_value(config)
    owner_raw = _launch_decision_value(config, "launch_decision_owner_mode")
    mode_raw = _launch_decision_value(config, "launch_decision_mode")
    if (
        mode_raw is not _MISSING
        and owner_raw is not _MISSING
        and str(mode_raw) != str(owner_raw)
    ):
        violations.append(
            _launch_decision_mode_violation(
                path="hyperparameters.policy_kwargs.launch_decision_owner_mode",
                expected="same value as launch_decision_mode",
                actual=owner_raw,
                reason="Two owner-mode keys must not declare different profiles.",
            )
        )
    if mode is None:
        violations.append(
            _launch_decision_mode_violation(
                path=mode_path or "hyperparameters.policy_kwargs.launch_decision_mode",
                expected="one of the declared launch-decision modes",
                actual=raw_mode,
                reason="Unknown launch-decision owner mode.",
            )
        )
        return violations

    flags = _launch_decision_active_flags(config)
    window_enabled = flags["window_classifier_adapter"]
    stopping_enabled = flags["stopping_adapter"]
    if window_enabled and stopping_enabled and mode != LaunchDecisionMode.LEGACY_COMPOSED_V0:
        violations.append(
            _launch_decision_mode_violation(
                path="hyperparameters.policy_kwargs.hybrid_event_use_stopping_head",
                expected="false when the window-classifier adapter is enabled",
                actual=True,
                reason=(
                    "New owner modes reject competing window and stopping adapters; "
                    "legacy precedence is available only in legacy_composed_v0."
                ),
            )
        )

    if mode == LaunchDecisionMode.DIRECT_BOUNDARY_V1_STRICT:
        if not flags["hybrid_event_head"]:
            violations.append(
                _launch_decision_mode_violation(
                    path="hyperparameters.policy_kwargs.hybrid_event_head_lr_scale",
                    expected="positive number",
                    actual=_launch_decision_value(config, "hybrid_event_head_lr_scale"),
                    reason="Strict direct-boundary mode needs a trainable event head.",
                )
            )
        for key, label in (
            ("hybrid_event_use_window_classifier_head", "window-classifier"),
            ("hybrid_event_use_stopping_head", "stopping"),
        ):
            if _launch_decision_bool(_launch_decision_value(config, key)):
                violations.append(
                    _launch_decision_mode_violation(
                        path=f"hyperparameters.policy_kwargs.{key}",
                        expected="false in direct_boundary_v1_strict",
                        actual=True,
                        reason=f"Strict direct-boundary mode excludes the {label} adapter.",
                    )
                )

    if mode == LaunchDecisionMode.GOVERNED_COMPOSED_V1 and (window_enabled or stopping_enabled):
        violations.append(
            _launch_decision_mode_violation(
                path="hyperparameters.policy_kwargs.launch_decision_mode",
                expected="adapter_coupled_v1 for an executable adapter",
                actual=mode.value,
                reason=(
                    "The governed default admits base/HMoE/event-head contributors; "
                    "an executable window or stopping adapter needs its own coupled profile."
                ),
            )
        )

    if mode == LaunchDecisionMode.ADAPTER_COUPLED_V1:
        adapter_count = int(window_enabled) + int(stopping_enabled)
        if adapter_count != 1:
            violations.append(
                _launch_decision_mode_violation(
                    path="hyperparameters.policy_kwargs.hybrid_event_use_window_classifier_head",
                    expected="exactly one executable adapter",
                    actual=adapter_count,
                    reason="adapter_coupled_v1 cannot be empty or have competing adapters.",
                )
            )

    if mode == LaunchDecisionMode.AUXILIARY_ONLY_V1 and (window_enabled or stopping_enabled):
        violations.append(
            _launch_decision_mode_violation(
                path="hyperparameters.policy_kwargs.launch_decision_mode",
                expected="no executable adapter in auxiliary_only_v1",
                actual=mode.value,
                reason="Auxiliary-only mode must not rewrite sampled event logits.",
            )
        )
    return violations


def _launch_decision_contributor_tuple(
    flags: Mapping[str, bool],
) -> tuple[LaunchDecisionContributor, ...]:
    ordered = (
        ("base_action", LaunchDecisionContributor.BASE_ACTION),
        ("hmoe_event_slice", LaunchDecisionContributor.HMOE_EVENT_SLICE),
        ("hybrid_event_head", LaunchDecisionContributor.HYBRID_EVENT_HEAD),
        (
            "window_classifier_adapter",
            LaunchDecisionContributor.WINDOW_CLASSIFIER_ADAPTER,
        ),
        ("stopping_adapter", LaunchDecisionContributor.STOPPING_ADAPTER),
    )
    return tuple(contributor for key, contributor in ordered if flags.get(key, False))


def resolve_launch_decision_contract(
    config: Mapping[str, Any],
) -> LaunchDecisionOwnerContract:
    """Resolve a configuration into one deterministic owner envelope."""

    violations = validate_launch_decision_contract(config)
    if violations:
        raise LaunchDecisionContractError(tuple(violations))
    mode, explicit, _mode_path, _raw_mode = _launch_decision_mode_value(config)
    assert mode is not None
    flags = _launch_decision_active_flags(config)
    active = _launch_decision_contributor_tuple(flags)
    ignored: tuple[LaunchDecisionContributor, ...] = ()
    precedence: str | None = None
    compatibility_mode = "none"

    if mode == LaunchDecisionMode.LEGACY_COMPOSED_V0:
        compatibility_mode = "legacy"
        if flags["window_classifier_adapter"] and flags["stopping_adapter"]:
            precedence = "window_classifier_before_stopping"
            compatibility_mode = "legacy_window_precedence"
            ignored = (LaunchDecisionContributor.STOPPING_ADAPTER,)
            active = tuple(
                contributor
                for contributor in active
                if contributor != LaunchDecisionContributor.STOPPING_ADAPTER
            )
        trainable_roles = tuple(
            _launch_decision_parameter_role(contributor)
            for contributor in active
        )
        detached_roles: tuple[str, ...] = ()
        scopes = (LaunchDecisionTrainingScope.COMPATIBILITY,)
        acceptance_eligible = False
    elif mode == LaunchDecisionMode.DIRECT_BOUNDARY_V1_STRICT:
        active = tuple(
            contributor
            for contributor in (
                LaunchDecisionContributor.BASE_ACTION,
                LaunchDecisionContributor.HYBRID_EVENT_HEAD,
            )
            if contributor == LaunchDecisionContributor.BASE_ACTION
            or flags["hybrid_event_head"]
        )
        trainable_roles = ("hybrid_event_head",)
        detached_roles = ("action_net", "policy_trunk", "hmoe_event_slice")
        scopes = (LaunchDecisionTrainingScope.DIRECT_BOUNDARY,)
        acceptance_eligible = True
    elif mode == LaunchDecisionMode.GOVERNED_COMPOSED_V1:
        trainable_roles = tuple(
            _launch_decision_parameter_role(contributor)
            for contributor in active
        )
        detached_roles = ()
        scopes = (
            LaunchDecisionTrainingScope.ORDINARY_PPO,
            LaunchDecisionTrainingScope.EVENT_POLICY_MARGIN,
        )
        acceptance_eligible = True
    elif mode == LaunchDecisionMode.AUXILIARY_ONLY_V1:
        active = ()
        trainable_roles = ("auxiliary_heads",)
        detached_roles = ("action_net", "policy_trunk", "hmoe_event_slice", "hybrid_event_head")
        scopes = (LaunchDecisionTrainingScope.AUXILIARY,)
        acceptance_eligible = False
    else:
        trainable_roles = tuple(
            _launch_decision_parameter_role(contributor)
            for contributor in active
        )
        detached_roles = ()
        scopes = (
            LaunchDecisionTrainingScope.ORDINARY_PPO,
            LaunchDecisionTrainingScope.EVENT_POLICY_MARGIN,
        )
        acceptance_eligible = False

    return LaunchDecisionOwnerContract(
        mode=mode,
        contributors=active,
        trainable_parameter_roles=tuple(dict.fromkeys(trainable_roles)),
        detached_parameter_roles=tuple(dict.fromkeys(detached_roles)),
        allowed_training_scopes=scopes,
        compatibility_mode=compatibility_mode,
        compatibility_precedence=precedence,
        ignored_contributors=ignored,
        acceptance_eligible=acceptance_eligible,
        explicit_mode=explicit,
    )


def _launch_decision_parameter_role(
    contributor: LaunchDecisionContributor,
) -> str:
    return {
        LaunchDecisionContributor.BASE_ACTION: "action_net",
        LaunchDecisionContributor.HMOE_EVENT_SLICE: "hmoe_event_slice",
        LaunchDecisionContributor.HYBRID_EVENT_HEAD: "hybrid_event_head",
        LaunchDecisionContributor.WINDOW_CLASSIFIER_ADAPTER: "window_classifier_adapter",
        LaunchDecisionContributor.STOPPING_ADAPTER: "stopping_adapter",
    }[contributor]


WINDOW_CLASSIFIER_CONTRACT = ModelMechanismContract(
    mechanism_id="m3s2.window_classifier_event_adapter",
    role=MechanismRole.ADAPTER_COUPLED,
    owner=(
        "python/rl/policy_algo/policies.py::window_classifier_head + "
        "python/rl/policy_algo/ppo_adaptive_kl.py::event_window_window_classifier"
    ),
    activation_paths=(
        ("hyperparameters", "policy_kwargs", "hybrid_event_use_window_classifier_head"),
        ("hyperparameters", "policy_kwargs", "window_classifier_head_lr_scale"),
        ("hyperparameters", "window_classifier_coef"),
    ),
    fault_stages=(
        FaultStage.OBSERVATION,
        FaultStage.SUPPORT,
        FaultStage.LABEL,
        FaultStage.REPRESENTATION,
        FaultStage.LOSS_OBJECT,
        FaultStage.OPTIMIZER,
        FaultStage.ADAPTER,
        FaultStage.EVALUATION,
    ),
    input_support=(
        SupportPopulation.POLICY_VISIBLE_SUPPORT,
        SupportPopulation.COLLECTION_SUPPORT,
        SupportPopulation.REPLAY_SUPPORT,
        SupportPopulation.CALIBRATION_POPULATION,
        SupportPopulation.EXECUTION_SUPPORT,
    ),
    normalization_population=SupportPopulation.EXECUTION_SUPPORT,
    loss_owner="M3-S2 window-classifier auxiliary side update",
    adapter_coupling=(
        "hybrid_event_use_window_classifier_head rewrites hold/fire logits "
        "before _HybridActionDistribution; classifier adapter takes precedence over "
        "the M3 stopping adapter when both are enabled."
    ),
    required_probe_stages=(
        FaultStage.REPRESENTATION,
        FaultStage.OPTIMIZER,
        FaultStage.ADAPTER,
        FaultStage.EVALUATION,
    ),
    held_boundary=(
        "Replay/training-support separation and support-preserving collection are diagnostic guards; "
        "they do not release learned behavior without deterministic execution-support boundary probes."
    ),
    config_gates=(
        ConfigGate(
            ("policy",),
            ConfigExpectation.EQUALS,
            "The classifier adapter is defined only for the maintained HMoE policy surface.",
            expected="HierarchicalMoEExecutionPolicy",
        ),
        ConfigGate(
            ("hyperparameters", "policy_kwargs", "hybrid_action_spec"),
            ConfigExpectation.EQUALS,
            "The adapter must target the hybrid event action distribution.",
            expected="air_combat_hybrid_v1",
        ),
        ConfigGate(
            ("hyperparameters", "policy_kwargs", "hybrid_event_use_window_classifier_head"),
            ConfigExpectation.REQUIRED_TRUE,
            "An adapter-coupled classifier must explicitly enter the executable event path.",
        ),
        ConfigGate(
            ("hyperparameters", "policy_kwargs", "window_classifier_head_lr_scale"),
            ConfigExpectation.POSITIVE_NUMBER,
            "The executable classifier branch must have a trainable head.",
        ),
        ConfigGate(
            ("hyperparameters", "policy_kwargs", "window_classifier_head_norm_enabled"),
            ConfigExpectation.REQUIRED_TRUE,
            "The current executable classifier contract uses per-sample LayerNorm.",
        ),
        ConfigGate(
            ("hyperparameters", "policy_kwargs", "window_classifier_event_adapter_detach"),
            ConfigExpectation.REQUIRED_TRUE,
            "PPO action gradients must not self-imitation-train the supervised classifier adapter.",
        ),
        ConfigGate(
            ("hyperparameters", "policy_kwargs", "window_classifier_input_standardization_enabled"),
            ConfigExpectation.REQUIRED_FALSE,
            "Mutable population standardization is held after the execution-support mismatch diagnosis.",
        ),
        ConfigGate(
            ("hyperparameters", "window_classifier_coef"),
            ConfigExpectation.POSITIVE_NUMBER,
            "The classifier adapter needs an owned auxiliary objective.",
        ),
        ConfigGate(
            ("hyperparameters", "window_classifier_detach_latent"),
            ConfigExpectation.REQUIRED_TRUE,
            "The current classifier repair isolates classifier fitting from actor-latent drift.",
        ),
        ConfigGate(
            ("hyperparameters", "window_classifier_dedicated_optimizer_enabled"),
            ConfigExpectation.REQUIRED_TRUE,
            "The classifier update must not reuse PPO Adam state.",
        ),
        ConfigGate(
            ("hyperparameters", "window_classifier_replay_enabled"),
            ConfigExpectation.REQUIRED_TRUE,
            "Replay is part of the current classifier support contract and must be explicit.",
        ),
        ConfigGate(
            ("hyperparameters", "window_classifier_replay_storage"),
            ConfigExpectation.EQUALS,
            "Observation replay is required so samples pass through the current actor latent.",
            expected="observation",
        ),
        ConfigGate(
            ("hyperparameters", "event_window_support_preserving_collect_enabled"),
            ConfigExpectation.REQUIRED_TRUE,
            "Support-preserving collection remains a diagnostic guard for one-shot support collapse.",
        ),
        ConfigGate(
            ("hyperparameters", "event_window_support_preserving_hold_quality_enabled"),
            ConfigExpectation.REQUIRED_TRUE,
            "Quality-window rows must be preserved for classifier fault localization.",
        ),
    ),
)


DIRECT_FIRE_BOUNDARY_CONTRACT = ModelMechanismContract(
    mechanism_id="m3s2.direct_fire_boundary_event_head",
    role=MechanismRole.EXECUTABLE,
    owner=(
        "python/rl/policy_algo/policies.py::hybrid_event_head + "
        "python/rl/policy_algo/ppo_adaptive_kl.py::fire_boundary"
    ),
    activation_paths=(
        ("hyperparameters", "fire_boundary_coef"),
    ),
    fault_stages=(
        FaultStage.OBSERVATION,
        FaultStage.SUPPORT,
        FaultStage.LABEL,
        FaultStage.REPRESENTATION,
        FaultStage.LOSS_OBJECT,
        FaultStage.OPTIMIZER,
        FaultStage.ADAPTER,
        FaultStage.EVALUATION,
    ),
    input_support=(
        SupportPopulation.POLICY_VISIBLE_SUPPORT,
        SupportPopulation.COLLECTION_SUPPORT,
        SupportPopulation.EXECUTION_SUPPORT,
    ),
    normalization_population=None,
    loss_owner="M3-S2 direct fire-boundary auxiliary update on executable event logits",
    adapter_coupling=(
        "The loss is computed on the final _HybridActionDistribution hold/fire delta, "
        "but the dedicated update may write only hybrid_event_head parameters. "
        "M3 stopping and window-classifier adapters must stay disabled in this contract."
    ),
    required_probe_stages=(
        FaultStage.LABEL,
        FaultStage.OPTIMIZER,
        FaultStage.ADAPTER,
        FaultStage.EVALUATION,
    ),
    held_boundary=(
        "This contract proves only the executable fire boundary can be fitted from the current sidecar labels; "
        "short-train behavior still requires deterministic launch probes."
    ),
    config_gates=(
        ConfigGate(
            ("policy",),
            ConfigExpectation.EQUALS,
            "The direct fire boundary is defined only for the maintained HMoE policy surface.",
            expected="HierarchicalMoEExecutionPolicy",
        ),
        ConfigGate(
            ("hyperparameters", "policy_kwargs", "hybrid_action_spec"),
            ConfigExpectation.EQUALS,
            "The boundary must target the hybrid event action distribution.",
            expected="air_combat_hybrid_v1",
        ),
        ConfigGate(
            ("hyperparameters", "policy_kwargs", "hybrid_event_head_lr_scale"),
            ConfigExpectation.POSITIVE_NUMBER,
            "The executable fire boundary must have a trainable hybrid_event_head.",
        ),
        ConfigGate(
            ("hyperparameters", "policy_kwargs", "hybrid_event_use_stopping_head"),
            ConfigExpectation.REQUIRED_FALSE,
            "Direct fire boundary owns executable hold/fire logits and must not be overridden by stopping adapter.",
        ),
        ConfigGate(
            ("hyperparameters", "policy_kwargs", "hybrid_event_use_window_classifier_head"),
            ConfigExpectation.REQUIRED_FALSE,
            "Direct fire boundary owns executable hold/fire logits and must not be overridden by classifier adapter.",
        ),
        ConfigGate(
            ("hyperparameters", "fire_boundary_coef"),
            ConfigExpectation.POSITIVE_NUMBER,
            "The direct fire boundary needs an owned auxiliary objective.",
        ),
        ConfigGate(
            ("hyperparameters", "fire_boundary_separate_update_enabled"),
            ConfigExpectation.REQUIRED_TRUE,
            "The direct fire boundary update must stay isolated from PPO actor/value updates.",
        ),
        ConfigGate(
            ("hyperparameters", "fire_boundary_dedicated_optimizer_enabled"),
            ConfigExpectation.REQUIRED_TRUE,
            "The direct fire boundary must not reuse PPO Adam state.",
        ),
        ConfigGate(
            ("hyperparameters", "fire_boundary_support_preserving_collect_enabled"),
            ConfigExpectation.REQUIRED_TRUE,
            "Support-preserving collection must keep legal rows visible for boundary fitting.",
        ),
        ConfigGate(
            ("hyperparameters", "fire_boundary_support_preserving_hold_quality_enabled"),
            ConfigExpectation.REQUIRED_TRUE,
            "Quality-window rows must be preserved until the boundary is verified.",
        ),
    ),
)


MODEL_MECHANISM_CONTRACTS: tuple[ModelMechanismContract, ...] = (
    WINDOW_CLASSIFIER_CONTRACT,
    DIRECT_FIRE_BOUNDARY_CONTRACT,
)


def active_model_contracts_for_config(
    config: Mapping[str, Any],
    contracts: tuple[ModelMechanismContract, ...] = MODEL_MECHANISM_CONTRACTS,
) -> tuple[ModelMechanismContract, ...]:
    return tuple(contract for contract in contracts if contract.is_active(config))


def validate_training_config_contract(
    config: Mapping[str, Any],
    contracts: tuple[ModelMechanismContract, ...] = MODEL_MECHANISM_CONTRACTS,
) -> list[ContractViolation]:
    violations: list[ContractViolation] = []
    for contract in active_model_contracts_for_config(config, contracts):
        for gate in contract.config_gates:
            actual = _value_at(config, gate.path)
            if _gate_passes(actual, gate):
                continue
            violations.append(
                ContractViolation(
                    mechanism_id=contract.mechanism_id,
                    path=_format_path(gate.path),
                    expected=_expectation_label(gate),
                    actual="<missing>" if actual is _MISSING else actual,
                    reason=gate.reason,
                )
            )
    violations.extend(validate_launch_decision_contract(config))
    return violations
