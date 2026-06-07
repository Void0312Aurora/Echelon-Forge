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


M3S2_WINDOW_CLASSIFIER_CONTRACT = ModelMechanismContract(
    mechanism_id="m3s2.window_classifier_event_adapter",
    role=MechanismRole.ADAPTER_COUPLED,
    owner=(
        "python/rl/policy_algo/policies.py::m3_window_classifier_head + "
        "python/rl/policy_algo/ppo_adaptive_kl.py::m3s2_window_classifier"
    ),
    activation_paths=(
        ("hyperparameters", "policy_kwargs", "hybrid_event_use_m3_window_classifier_head"),
        ("hyperparameters", "policy_kwargs", "m3_window_classifier_head_lr_scale"),
        ("hyperparameters", "m3s2_window_classifier_coef"),
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
        "hybrid_event_use_m3_window_classifier_head rewrites hold/fire logits "
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
            ("hyperparameters", "policy_kwargs", "hybrid_event_use_m3_window_classifier_head"),
            ConfigExpectation.REQUIRED_TRUE,
            "An adapter-coupled classifier must explicitly enter the executable event path.",
        ),
        ConfigGate(
            ("hyperparameters", "policy_kwargs", "m3_window_classifier_head_lr_scale"),
            ConfigExpectation.POSITIVE_NUMBER,
            "The executable classifier branch must have a trainable head.",
        ),
        ConfigGate(
            ("hyperparameters", "policy_kwargs", "m3_window_classifier_head_norm_enabled"),
            ConfigExpectation.REQUIRED_TRUE,
            "The current executable classifier contract uses per-sample LayerNorm.",
        ),
        ConfigGate(
            ("hyperparameters", "policy_kwargs", "m3_window_classifier_event_adapter_detach"),
            ConfigExpectation.REQUIRED_TRUE,
            "PPO action gradients must not self-imitation-train the supervised classifier adapter.",
        ),
        ConfigGate(
            ("hyperparameters", "policy_kwargs", "m3_window_classifier_input_standardization_enabled"),
            ConfigExpectation.REQUIRED_FALSE,
            "Mutable population standardization is held after the execution-support mismatch diagnosis.",
        ),
        ConfigGate(
            ("hyperparameters", "m3s2_window_classifier_coef"),
            ConfigExpectation.POSITIVE_NUMBER,
            "The classifier adapter needs an owned auxiliary objective.",
        ),
        ConfigGate(
            ("hyperparameters", "m3s2_window_classifier_detach_latent"),
            ConfigExpectation.REQUIRED_TRUE,
            "The current classifier repair isolates classifier fitting from actor-latent drift.",
        ),
        ConfigGate(
            ("hyperparameters", "m3s2_window_classifier_dedicated_optimizer_enabled"),
            ConfigExpectation.REQUIRED_TRUE,
            "The classifier update must not reuse PPO Adam state.",
        ),
        ConfigGate(
            ("hyperparameters", "m3s2_window_classifier_replay_enabled"),
            ConfigExpectation.REQUIRED_TRUE,
            "Replay is part of the current classifier support contract and must be explicit.",
        ),
        ConfigGate(
            ("hyperparameters", "m3s2_window_classifier_replay_storage"),
            ConfigExpectation.EQUALS,
            "Observation replay is required so samples pass through the current actor latent.",
            expected="observation",
        ),
        ConfigGate(
            ("hyperparameters", "m3s2_event_window_support_preserving_collect_enabled"),
            ConfigExpectation.REQUIRED_TRUE,
            "Support-preserving collection remains a diagnostic guard for one-shot support collapse.",
        ),
        ConfigGate(
            ("hyperparameters", "m3s2_event_window_support_preserving_hold_quality_enabled"),
            ConfigExpectation.REQUIRED_TRUE,
            "Quality-window rows must be preserved for classifier fault localization.",
        ),
    ),
)


M3S2_DIRECT_FIRE_BOUNDARY_CONTRACT = ModelMechanismContract(
    mechanism_id="m3s2.direct_fire_boundary_event_head",
    role=MechanismRole.EXECUTABLE,
    owner=(
        "python/rl/policy_algo/policies.py::hybrid_event_head + "
        "python/rl/policy_algo/ppo_adaptive_kl.py::m3s2_fire_boundary"
    ),
    activation_paths=(
        ("hyperparameters", "m3s2_fire_boundary_coef"),
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
            ("hyperparameters", "policy_kwargs", "hybrid_event_use_m3_stopping_head"),
            ConfigExpectation.REQUIRED_FALSE,
            "Direct fire boundary owns executable hold/fire logits and must not be overridden by stopping adapter.",
        ),
        ConfigGate(
            ("hyperparameters", "policy_kwargs", "hybrid_event_use_m3_window_classifier_head"),
            ConfigExpectation.REQUIRED_FALSE,
            "Direct fire boundary owns executable hold/fire logits and must not be overridden by classifier adapter.",
        ),
        ConfigGate(
            ("hyperparameters", "m3s2_fire_boundary_coef"),
            ConfigExpectation.POSITIVE_NUMBER,
            "The direct fire boundary needs an owned auxiliary objective.",
        ),
        ConfigGate(
            ("hyperparameters", "m3s2_fire_boundary_separate_update_enabled"),
            ConfigExpectation.REQUIRED_TRUE,
            "The direct fire boundary update must stay isolated from PPO actor/value updates.",
        ),
        ConfigGate(
            ("hyperparameters", "m3s2_fire_boundary_dedicated_optimizer_enabled"),
            ConfigExpectation.REQUIRED_TRUE,
            "The direct fire boundary must not reuse PPO Adam state.",
        ),
        ConfigGate(
            ("hyperparameters", "m3s2_fire_boundary_support_preserving_collect_enabled"),
            ConfigExpectation.REQUIRED_TRUE,
            "Support-preserving collection must keep legal rows visible for boundary fitting.",
        ),
        ConfigGate(
            ("hyperparameters", "m3s2_fire_boundary_support_preserving_hold_quality_enabled"),
            ConfigExpectation.REQUIRED_TRUE,
            "Quality-window rows must be preserved until the boundary is verified.",
        ),
    ),
)


MODEL_MECHANISM_CONTRACTS: tuple[ModelMechanismContract, ...] = (
    M3S2_WINDOW_CLASSIFIER_CONTRACT,
    M3S2_DIRECT_FIRE_BOUNDARY_CONTRACT,
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
    return violations
