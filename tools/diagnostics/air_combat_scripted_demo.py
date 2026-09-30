#!/usr/bin/env python3
"""Run the maintained Air scripted C2/ROE model without RL training."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

import numpy as np

_REPO_ROOT_HINT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT_HINT not in sys.path:
    sys.path.insert(0, _REPO_ROOT_HINT)

from python.runtime_bootstrap import ensure_repo_imports, resolve_repo_path


ensure_repo_imports()

from python.tasking_contracts.air.engagement.model import (  # noqa: E402
    AIR_COMBAT_C2_ROE_V2,
    AIR_COMBAT_HYBRID_ACTION_DIM,
    AIR_SCRIPTED_ENGAGEMENT_MODEL_ID,
)
from python.tasking_contracts.common.decision_runtime import (  # noqa: E402
    DecisionRuntimeAgent,
    DecisionRuntimeAgentSpec,
)
from python.tasking_contracts.air.registry import AIR_SCRIPTED_MODEL_REGISTRY  # noqa: E402
from python.simulation import create_single_backend  # noqa: E402


DEFAULT_SCENARIO = resolve_repo_path(
    "scenarios",
    "air_combat",
    "1v1",
    "air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json",
)


def _unbatch(observation: dict[str, Any]) -> dict[str, Any]:
    return {key: np.asarray(value)[0] for key, value in observation.items()}


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


def run_demo(
    *,
    scenario_path: str,
    seed: int,
    max_steps: int,
    action_mode: str,
    post_launch_assessment: bool,
) -> dict[str, Any]:
    action_mode = str(action_mode).strip().lower()
    if action_mode != "air_combat_hybrid_v1":
        raise ValueError("the scripted combat demo requires action_mode='air_combat_hybrid_v1'")
    action_dim = AIR_COMBAT_HYBRID_ACTION_DIM
    vec_env = create_single_backend(
        scenario_path=os.path.abspath(str(scenario_path)),
        n_envs=1,
        include_visual=False,
        include_proprio=True,
        action_mode=action_mode,
        mission_obs_mode=AIR_COMBAT_C2_ROE_V2,
        step_info_mode="full",
        execution_step_runtime_mode="compiled",
        flight_shaping_backend="compiled",
        worker_threads=1,
        air_combat_post_launch_assessment_enabled=bool(post_launch_assessment),
        air_combat_post_launch_assessment_stages=["A1-S1"],
        air_combat_post_launch_assessment_max_steps=4,
        air_combat_post_launch_assessment_gamma=0.5,
    )
    model = AIR_SCRIPTED_MODEL_REGISTRY.create_for(
        domain="air",
        role_id="air_tactical_engagement_controller",
        model_id=AIR_SCRIPTED_ENGAGEMENT_MODEL_ID,
        action_dim=action_dim,
        dt=0.05,
        mission_obs_mode=AIR_COMBAT_C2_ROE_V2,
        # The fixture declares station 1 through the maintained loadout seam;
        # the model fails closed if a runtime omits or invalidates it.
        weapon_station_id=1,
    )
    agent = DecisionRuntimeAgent(
        DecisionRuntimeAgentSpec(
            agent_id="air-combat-scripted-demo",
            model_id=AIR_SCRIPTED_ENGAGEMENT_MODEL_ID,
            domain="air",
            role_id="air_tactical_engagement_controller",
            authority_scope="air_weapons_c2",
        ),
        model,
    )
    release_steps: list[int] = []
    fire_accept_steps: list[int] = []
    last_info: dict[str, Any] = {}
    last_runtime_step = None
    steps_run = 0
    terminated = False
    truncated = False
    try:
        vec_env.seed(int(seed))
        observation_batch = vec_env.reset()
        observation = _unbatch(observation_batch)
        agent.reset(
            context={
                "observation": observation,
                "phase_name": "stable_flight",
                "mission_obs_mode": AIR_COMBAT_C2_ROE_V2,
            },
            episode_seed=int(seed),
        )
        for step in range(1, max(1, int(max_steps)) + 1):
            observation = _unbatch(observation_batch)
            runtime_step = agent.step(
                observation=observation,
                clock_s=float(step - 1) * 0.05,
                observation_version=f"air-combat:{step - 1}",
                context={
                    "phase_name": "stable_flight",
                    "mission_obs_mode": AIR_COMBAT_C2_ROE_V2,
                },
            )
            last_runtime_step = runtime_step
            steps_run = step
            observation_batch, rewards, dones, infos = vec_env.step(
                np.asarray(runtime_step.action, dtype=np.float32).reshape(1, -1)
            )
            last_info = dict(infos[0]) if infos else {}
            if bool(last_info.get("fire_once_accepted", False)):
                fire_accept_steps.append(step)
            if bool(last_info.get("release_executed", False)):
                release_steps.append(step)
            terminated = bool(dones[0]) if len(dones) else False
            truncated = bool(last_info.get("truncated", False))
            if terminated or truncated:
                break
        report = agent.model.last_decision_info if hasattr(agent.model, "last_decision_info") else {}
        payload = {
            "scenario": os.path.abspath(str(scenario_path)),
            "seed": int(seed),
            "action_mode": action_mode,
            "mission_obs_mode": AIR_COMBAT_C2_ROE_V2,
            "max_steps": int(max_steps),
            "steps": int(steps_run),
            "terminated": bool(terminated),
            "truncated": bool(truncated),
            "termination_reason": str(last_info.get("termination_reason", "")),
            "fire_once_accepted_steps": fire_accept_steps,
            "release_executed_steps": release_steps,
            "scripted_decision_info": report,
            "scripted_runtime_identity": agent.replay_identity,
            "scripted_runtime_decisions": int(last_runtime_step.report.decision_index)
            if last_runtime_step is not None
            else 0,
            "last_info": {
                key: last_info.get(key)
                for key in (
                    "fire_once_requested",
                    "fire_once_accepted",
                    "release_executed",
                    "post_launch_assessment",
                    "post_launch_assessment_steps",
                    "post_launch_assessment_reward_mode",
                    "mission_status",
                    "reward_terms",
                    "terminated",
                    "truncated",
                    "termination_reason",
                )
                if key in last_info
            },
        }
        return _json_value(payload)
    finally:
        agent.close()
        vec_env.close()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", default=DEFAULT_SCENARIO)
    parser.add_argument("--seed", type=int, default=20260516)
    parser.add_argument("--max_steps", type=int, default=400)
    parser.add_argument("--action_mode", choices=("air_combat_hybrid_v1",), default="air_combat_hybrid_v1")
    parser.add_argument("--post_launch_assessment", action="store_true")
    parser.add_argument("--json_out", default="")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    payload = run_demo(
        scenario_path=args.scenario,
        seed=args.seed,
        max_steps=args.max_steps,
        action_mode=args.action_mode,
        post_launch_assessment=args.post_launch_assessment,
    )
    rendered = json.dumps(payload, indent=2, ensure_ascii=True)
    if args.json_out:
        output_path = Path(args.json_out).resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
