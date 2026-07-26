from __future__ import annotations

from typing import Any

import ef_py
import numpy as np

from gym_envs.scenario_loader import ScenarioLoader


# G4 information-state declaration (architecture design doc §3/§15; facility in
# python/architecture/information_layer.py). This module holds the world-batch
# vec-env observation support helpers: ``_execution_instrument_vector`` consumes
# own-ship authoritative truth (``truth.x/y`` for the ILS query; the truth object
# then feeds ``ef_py.compute_execution_observation_runtime_numpy``) and produces
# the per-agent execution instrument observation vector. Per the I32 batch-step
# stage contracts (python/rl/runtime/world_batch/core.py), execution observation
# assembly closes at P10 ObservationExport. Declared this iteration, settling its
# I76 G4_DECLARATION_PENDING_CONSUMERS pin
# (python/architecture/consumer_classification.py); reads kept, not
# view-converged: the batch path consumes cached per-state truth under the I32
# stage contracts rather than a per-loader observation view, so this module is
# declared-but-open (t8_g4_truth_leak_inventory.md) and NOT ban-gated. Pure
# metadata; no runtime cost.
INFORMATION_LAYER_CONSUMED = ("World Truth",)
INFORMATION_LAYER_PRODUCED = ("Agent Observation",)
SEMANTIC_STAGE = ("P10 ObservationExport",)


_POST_LAUNCH_ASSESSMENT_REWARD_KEYS = {
    "combat_win_bonus",
    "combat_loss_penalty",
    "combat_draw_reward",
}
_POST_LAUNCH_ASSESSMENT_REWARD_PREFIXES = (
    "air_combat_target_",
    "air_combat_self_",
)
_POST_LAUNCH_ASSESSMENT_DEFAULT_STAGES = {"A1-S1", "A1-S2"}


def _float32_view(value: Any) -> np.ndarray:
    return np.asarray(value, dtype=np.float32)


def _execution_instrument_vector(loader: ScenarioLoader, truth: Any, inst: Any, *, max_contacts: int, max_rwr: int) -> np.ndarray:
    ils_vec = loader.get_ils_observation(float(truth.x), float(truth.y), float(inst.alt_baro))
    inst_vec, _contacts, _rwr = ef_py.compute_execution_observation_runtime_numpy(
        inst,
        truth,
        float(ils_vec[0]) if len(ils_vec) > 0 else 0.0,
        float(ils_vec[1]) if len(ils_vec) > 1 else 0.0,
        float(ils_vec[2]) if len(ils_vec) > 2 else 0.0,
        float(ils_vec[3]) if len(ils_vec) > 3 else 0.0,
        int(max_contacts),
        int(max_rwr),
    )
    return np.asarray(inst_vec, dtype=np.float32)


def _as_stage_set(value: Any) -> set[str]:
    if value is None:
        return set(_POST_LAUNCH_ASSESSMENT_DEFAULT_STAGES)
    if isinstance(value, str):
        parts = [part.strip() for part in value.replace(";", ",").split(",")]
        return {part for part in parts if part}
    try:
        return {str(part).strip() for part in value if str(part).strip()}
    except TypeError:
        return {str(value).strip()} if str(value).strip() else set()


def _scenario_stage(loader: ScenarioLoader) -> str:
    scenario = getattr(loader, "scenario_data", {})
    scenario = scenario if isinstance(scenario, dict) else {}
    realism = scenario.get("realism_gradient", {})
    realism = realism if isinstance(realism, dict) else {}
    stage = str(realism.get("stage", "") or "").strip()
    if stage:
        return stage
    source_path = str(getattr(loader, "_scenario_source_path", "") or "").lower()
    if "stage1" in source_path or "a1-s1" in source_path:
        return "A1-S1"
    if "stage2" in source_path or "a1-s2" in source_path:
        return "A1-S2"
    return ""


def _post_launch_reward_from_breakdown(breakdown: Any) -> float:
    if not isinstance(breakdown, dict):
        return 0.0
    total = 0.0
    for key, value in breakdown.items():
        key_s = str(key)
        if key_s in _POST_LAUNCH_ASSESSMENT_REWARD_KEYS or key_s.startswith(
            _POST_LAUNCH_ASSESSMENT_REWARD_PREFIXES
        ):
            try:
                total += float(value)
            except Exception:
                continue
    return float(total)


__all__ = [
    "_as_stage_set",
    "_execution_instrument_vector",
    "_float32_view",
    "_post_launch_reward_from_breakdown",
    "_scenario_stage",
]
