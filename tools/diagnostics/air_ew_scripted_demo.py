#!/usr/bin/env python3
"""Run the RL-independent Air EW action adapter against a scripted opponent."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

import numpy as np

from python.runtime_bootstrap import ensure_repo_imports, resolve_repo_path


ensure_repo_imports()

from python.simulation import create_single_backend  # noqa: E402
from python.tasking_contracts.air.ew.model import (  # noqa: E402
    AIR_SCRIPTED_EW_ACTION_MODEL_ID,
)
from python.tasking_contracts.air.registry import AIR_SCRIPTED_MODEL_REGISTRY  # noqa: E402
from python.tasking_contracts.common.decision_runtime import (  # noqa: E402
    DecisionRuntimeAgent,
    DecisionRuntimeAgentSpec,
)


DEFAULT_SCENARIO = resolve_repo_path(
    "scenarios", "air_combat", "air_combat_1v1_headon_sensor_smoke_v1.json"
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
    response_doctrine: str,
) -> dict[str, Any]:
    doctrine = str(response_doctrine).strip().lower()
    if doctrine not in {"observe_only", "countermeasure_ready", "chaff_only", "flare_only"}:
        raise ValueError(
            "response_doctrine must be 'observe_only', 'countermeasure_ready', 'chaff_only', or 'flare_only'"
        )

    vec_env = create_single_backend(
        scenario_path=os.path.abspath(str(scenario_path)),
        n_envs=1,
        include_visual=False,
        include_proprio=False,
        action_mode="air_ew_hybrid_v1",
        mission_obs_mode="basic",
        execution_step_runtime_mode="compiled",
        flight_shaping_backend="compiled",
        worker_threads=1,
    )
    model = AIR_SCRIPTED_MODEL_REGISTRY.create_for(
        domain="air",
        role_id="air_ew_action_controller",
        model_id=AIR_SCRIPTED_EW_ACTION_MODEL_ID,
        dt=0.05,
        max_rwr=4,
    )
    agent = DecisionRuntimeAgent(
        DecisionRuntimeAgentSpec(
            agent_id="air-ew-scripted-demo",
            model_id=AIR_SCRIPTED_EW_ACTION_MODEL_ID,
            domain="air",
            role_id="air_ew_action_controller",
            authority_scope="air_ew_response",
        ),
        model,
    )
    launch_warning_steps: list[int] = []
    countermeasure_request_steps: list[int] = []
    countermeasure_state_samples: list[dict[str, Any]] = []
    last_info: dict[str, Any] = {}
    last_runtime_step = None
    terminated = False
    truncated = False
    steps_run = 0
    try:
        vec_env.seed(int(seed))
        observation_batch = vec_env.reset()
        observation = _unbatch(observation_batch)
        initial_instrument = vec_env.envs[0].last_inst
        initial_countermeasure_state = {
            "chaff_remaining": int(getattr(initial_instrument, "countermeasure_chaff_remaining", -1)),
            "flare_remaining": int(getattr(initial_instrument, "countermeasure_flare_remaining", -1)),
        }
        agent.reset(
            context={
                "observation": observation,
                "phase_name": "stable_flight",
                "response_doctrine": doctrine,
                "mission_obs_mode": "basic",
            },
            episode_seed=int(seed),
        )
        for step in range(1, max(1, int(max_steps)) + 1):
            observation = _unbatch(observation_batch)
            rwr = np.asarray(observation.get("rwr", []), dtype=np.float32).reshape(-1, 4)
            if rwr.size and bool(np.any(rwr[:, 3] > 0.5)):
                launch_warning_steps.append(step)
            runtime_step = agent.step(
                observation=observation,
                clock_s=float(step - 1) * 0.05,
                observation_version=f"air-ew:{step - 1}",
                context={
                    "phase_name": "stable_flight",
                    "response_doctrine": doctrine,
                    "mission_obs_mode": "basic",
                },
            )
            last_runtime_step = runtime_step
            action = np.asarray(runtime_step.action, dtype=np.float32).reshape(-1)
            if action.size >= 14 and bool(np.any(action[12:14] > 0.5)):
                countermeasure_request_steps.append(step)
            observation_batch, _rewards, dones, infos = vec_env.step(action.reshape(1, -1))
            last_info = dict(infos[0]) if infos else {}
            instrument = vec_env.envs[0].last_inst
            if action.size >= 14 and bool(np.any(action[12:14] > 0.5)):
                countermeasure_state_samples.append(
                    {
                        "step": step,
                        "chaff_remaining": int(getattr(instrument, "countermeasure_chaff_remaining", -1)),
                        "flare_remaining": int(getattr(instrument, "countermeasure_flare_remaining", -1)),
                        "last_release_time_s": float(
                            getattr(instrument, "countermeasure_last_release_time_s", -1.0)
                        ),
                    }
                )
            steps_run = step
            terminated = bool(dones[0]) if len(dones) else False
            truncated = bool(last_info.get("truncated", False))
            if terminated or truncated:
                break
        return _json_value(
            {
                "scenario": os.path.abspath(str(scenario_path)),
                "seed": int(seed),
                "action_mode": "air_ew_hybrid_v1",
                "response_doctrine": doctrine,
                "max_steps": int(max_steps),
                "steps": int(steps_run),
                "terminated": bool(terminated),
                "truncated": bool(truncated),
                "termination_reason": str(last_info.get("termination_reason", "")),
                "launch_warning_steps": launch_warning_steps,
                "countermeasure_request_steps": countermeasure_request_steps,
                "countermeasure_state_samples": countermeasure_state_samples,
                "initial_countermeasure_state": initial_countermeasure_state,
                "scripted_runtime_identity": agent.replay_identity,
                "scripted_runtime_decisions": int(last_runtime_step.report.decision_index)
                if last_runtime_step is not None
                else 0,
                "native_countermeasure_state": "instrument_state_projection",
            }
        )
    finally:
        agent.close()
        vec_env.close()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", default=DEFAULT_SCENARIO)
    parser.add_argument("--seed", type=int, default=20260516)
    parser.add_argument("--max_steps", type=int, default=120)
    parser.add_argument(
        "--response_doctrine",
        choices=("observe_only", "countermeasure_ready", "chaff_only", "flare_only"),
        default="countermeasure_ready",
    )
    parser.add_argument("--json_out", default="")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    payload = run_demo(
        scenario_path=args.scenario,
        seed=args.seed,
        max_steps=args.max_steps,
        response_doctrine=args.response_doctrine,
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
