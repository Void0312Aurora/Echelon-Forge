"""Policy/algorithm package with lazy public exports.

Contract and configuration modules import this package during lightweight
preflight.  Public training classes are loaded only when requested, so
``import python.rl.policy_algo.model_contracts`` does not pull in torch, SB3,
or the policy implementation.
"""

from __future__ import annotations

from importlib import import_module


_LAZY_EXPORTS = {
    "AdaptiveKLPPO": ("python.rl.policy_algo.ppo_adaptive_kl", "AdaptiveKLPPO"),
    "FirstEventDeviceDictRolloutBuffer": (
        "python.rl.policy_algo.first_event_rollout_buffer",
        "FirstEventDeviceDictRolloutBuffer",
    ),
    "FirstEventDictRolloutBuffer": (
        "python.rl.policy_algo.first_event_rollout_buffer",
        "FirstEventDictRolloutBuffer",
    ),
    "DEFAULT_FAMILY_SUBEXPERT_COUNTS": (
        "python.rl.policy_algo.hmoe_routing",
        "DEFAULT_FAMILY_SUBEXPERT_COUNTS",
    ),
    "DEFAULT_SUBEXPERT_NAMES": ("python.rl.policy_algo.hmoe_routing", "DEFAULT_SUBEXPERT_NAMES"),
    "DeviceDictRolloutBuffer": (
        "python.rl.policy_algo.device_dict_rollout_buffer",
        "DeviceDictRolloutBuffer",
    ),
    "FAMILY_DEPARTURE_NAV": ("python.rl.policy_algo.hmoe_routing", "FAMILY_DEPARTURE_NAV"),
    "FAMILY_FORMATION_COOPERATIVE": (
        "python.rl.policy_algo.hmoe_routing",
        "FAMILY_FORMATION_COOPERATIVE",
    ),
    "FAMILY_NAMES": ("python.rl.policy_algo.hmoe_routing", "FAMILY_NAMES"),
    "FAMILY_RECOVERY_LANDING": (
        "python.rl.policy_algo.hmoe_routing",
        "FAMILY_RECOVERY_LANDING",
    ),
    "FAMILY_TAKEOFF_GROUND": ("python.rl.policy_algo.hmoe_routing", "FAMILY_TAKEOFF_GROUND"),
    "HMoERouteBatch": ("python.rl.policy_algo.hmoe_routing", "HMoERouteBatch"),
    "HierarchicalMoEExecutionPolicy": (
        "python.rl.policy_algo.policies",
        "HierarchicalMoEExecutionPolicy",
    ),
    "FirstEventHazardLabels": ("python.rl.policy_algo.first_event_hazard", "FirstEventHazardLabels"),
    "FirstEventHazardLoss": ("python.rl.policy_algo.first_event_hazard", "FirstEventHazardLoss"),
    "SquashedMultiInputPolicy": (
        "python.rl.policy_algo.policies",
        "SquashedMultiInputPolicy",
    ),
    "build_first_event_hazard_labels": (
        "python.rl.policy_algo.first_event_hazard",
        "build_first_event_hazard_labels",
    ),
    "compute_first_event_hazard_loss": (
        "python.rl.policy_algo.first_event_hazard",
        "compute_first_event_hazard_loss",
    ),
    "current_first_event_curriculum_coef": (
        "python.rl.policy_algo.first_event_hazard",
        "current_first_event_curriculum_coef",
    ),
    "family_name": ("python.rl.policy_algo.hmoe_routing", "family_name"),
    "first_event_hazard_batch_from_rollout_data": (
        "python.rl.policy_algo.first_event_hazard",
        "first_event_hazard_batch_from_rollout_data",
    ),
    "route_from_mission_observation": (
        "python.rl.policy_algo.hmoe_routing",
        "route_from_mission_observation",
    ),
    "subexpert_name": ("python.rl.policy_algo.hmoe_routing", "subexpert_name"),
}

__all__ = sorted(_LAZY_EXPORTS)


def __getattr__(name: str):
    try:
        module_name, attribute = _LAZY_EXPORTS[name]
    except KeyError as exc:  # pragma: no cover - standard module attribute behavior
        raise AttributeError(name) from exc
    value = getattr(import_module(module_name), attribute)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))
