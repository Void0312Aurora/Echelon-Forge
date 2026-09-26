#!/usr/bin/env python3
"""Run a RL-independent multi-aircraft scripted Air C2/ROE engagement."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

import numpy as np

from python.runtime_bootstrap import ensure_repo_imports, resolve_repo_path


ensure_repo_imports()

from python.rl.runtime.cooperative_world_batch_vec_env import CooperativeWorldBatchVecEnv  # noqa: E402
from python.tasking_contracts.air_scripted_engagement import (  # noqa: E402
    AIR_COMBAT_C2_ROE_V2,
    AIR_COMBAT_HYBRID_ACTION_DIM,
    AIR_SCRIPTED_ENGAGEMENT_MODEL_ID,
)
from python.tasking_contracts.air_scripted_registry import AIR_SCRIPTED_MODEL_REGISTRY  # noqa: E402
from python.tasking_contracts.scripted_runtime import (  # noqa: E402
    ScriptedRuntimeAgent,
    ScriptedRuntimeAgentSpec,
)
from tools.diagnostics.air_cooperative_ew_scripted_demo import _cooperative_slot_metadata  # noqa: E402


DEFAULT_SCENARIO = resolve_repo_path(
    "scenarios", "air_combat", "cooperative_air_2v1_scripted_c2_roe_engagement_v1.json"
)


def _json_value(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.floating, np.integer, np.bool_)):
        return value.item()
    if isinstance(value, dict):
        return {str(key): _json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_value(item) for item in value]
    return value


def run_demo(*, scenario_path: str, seed: int, max_steps: int) -> dict[str, Any]:
    slot_metadata = _cooperative_slot_metadata(scenario_path)
    if not slot_metadata:
        raise ValueError("cooperative scenario must declare at least one controllable roster member")
    slot_names = tuple(item["entity_name"] for item in slot_metadata)
    slot_roles = tuple(item["formation_role_id"] for item in slot_metadata)
    vec_env = CooperativeWorldBatchVecEnv(
        scenario_path=os.path.abspath(str(scenario_path)),
        n_envs=1,
        include_visual=False,
        include_proprio=True,
        action_mode="air_combat_hybrid_v1",
        mission_obs_mode=AIR_COMBAT_C2_ROE_V2,
        step_info_mode="full",
        execution_step_runtime_mode="compiled",
        flight_shaping_backend="compiled",
        worker_threads=1,
    )
    if int(vec_env.slots_per_world) != len(slot_metadata):
        vec_env.close()
        raise RuntimeError(
            f"scenario roster/runtime slot mismatch: metadata={len(slot_metadata)} runtime={vec_env.slots_per_world}"
        )
    agents = [
        ScriptedRuntimeAgent(
            ScriptedRuntimeAgentSpec(
                agent_id=f"air-combat-cooperative-{name.lower()}",
                model_id=AIR_SCRIPTED_ENGAGEMENT_MODEL_ID,
                domain="air",
                role_id="air_tactical_engagement_controller",
                authority_scope="air_weapons_c2",
            ),
            AIR_SCRIPTED_MODEL_REGISTRY.create_for(
                domain="air",
                role_id="air_tactical_engagement_controller",
                model_id=AIR_SCRIPTED_ENGAGEMENT_MODEL_ID,
                action_dim=AIR_COMBAT_HYBRID_ACTION_DIM,
                dt=0.05,
                mission_obs_mode=AIR_COMBAT_C2_ROE_V2,
            ),
        )
        for name in slot_names
    ]
    accepted_steps: list[list[int]] = [[] for _ in agents]
    release_steps: list[list[int]] = [[] for _ in agents]
    decision_reports: list[dict[str, Any]] = [{} for _ in agents]
    last_infos: list[dict[str, Any]] = [{} for _ in agents]
    steps_run = 0
    try:
        vec_env.seed(int(seed))
        observation_batch = vec_env.reset()
        for slot_index, agent in enumerate(agents):
            observation = {key: np.asarray(value)[slot_index] for key, value in observation_batch.items()}
            agent.reset(
                context={
                    "observation": observation,
                    "phase_name": "stable_flight",
                    "mission_obs_mode": AIR_COMBAT_C2_ROE_V2,
                },
                episode_seed=int(seed),
            )

        terminated = [False for _ in agents]
        truncated = [False for _ in agents]
        for step in range(1, max(1, int(max_steps)) + 1):
            actions = []
            for slot_index, agent in enumerate(agents):
                observation = {key: np.asarray(value)[slot_index] for key, value in observation_batch.items()}
                runtime_step = agent.step(
                    observation=observation,
                    clock_s=float(step - 1) * 0.05,
                    observation_version=f"air-combat-cooperative:{slot_index}:{step - 1}",
                    context={
                        "phase_name": "stable_flight",
                        "mission_obs_mode": AIR_COMBAT_C2_ROE_V2,
                    },
                )
                decision_reports[slot_index] = dict(getattr(agent.model, "last_decision_info", {}))
                actions.append(np.asarray(runtime_step.action, dtype=np.float32).reshape(-1))
            observation_batch, _rewards, dones, infos = vec_env.step(np.asarray(actions, dtype=np.float32))
            for slot_index in range(len(agents)):
                last_infos[slot_index] = dict(infos[slot_index]) if len(infos) > slot_index else {}
                if bool(last_infos[slot_index].get("fire_once_accepted", False)):
                    accepted_steps[slot_index].append(step)
                if bool(last_infos[slot_index].get("release_executed", False)):
                    release_steps[slot_index].append(step)
                terminated[slot_index] = bool(dones[slot_index]) if len(dones) > slot_index else False
                truncated[slot_index] = bool(last_infos[slot_index].get("truncated", False))
            steps_run = step
            if any(terminated) or any(truncated):
                break

        return _json_value(
            {
                "scenario": os.path.abspath(str(scenario_path)),
                "seed": int(seed),
                "action_mode": "air_combat_hybrid_v1",
                "mission_obs_mode": AIR_COMBAT_C2_ROE_V2,
                "max_steps": int(max_steps),
                "steps": int(steps_run),
                "terminated": terminated,
                "truncated": truncated,
                "termination_reasons": [str(info.get("termination_reason", "")) for info in last_infos],
                "roster": [
                    {
                        "entity_name": slot_names[index],
                        "formation_role_id": slot_roles[index],
                    }
                    for index in range(len(agents))
                ],
                "fire_once_accepted_steps": accepted_steps,
                "release_executed_steps": release_steps,
                "scripted_decision_reports": decision_reports,
                "last_infos": last_infos,
                "scripted_runtime_identity": [agent.replay_identity for agent in agents],
                "scripted_runtime_decisions": [
                    int(agent._decision_index) for agent in agents
                ],
                "playable_boundary": "multi_aircraft_scripted_c2_roe_terminal_demo",
            }
        )
    finally:
        for agent in agents:
            agent.close()
        vec_env.close()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", default=DEFAULT_SCENARIO)
    parser.add_argument("--seed", type=int, default=20260516)
    parser.add_argument("--max_steps", type=int, default=2400)
    parser.add_argument("--json_out", default="")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    payload = run_demo(scenario_path=args.scenario, seed=args.seed, max_steps=args.max_steps)
    rendered = json.dumps(payload, indent=2, ensure_ascii=True)
    if args.json_out:
        output_path = Path(args.json_out).resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
