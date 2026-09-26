#!/usr/bin/env python3
"""Run the RL-independent cooperative Air EW response demonstration."""

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
from python.tasking_contracts.air.ew.model import AIR_SCRIPTED_EW_ACTION_MODEL_ID  # noqa: E402
from python.tasking_contracts.air.registry import AIR_SCRIPTED_MODEL_REGISTRY  # noqa: E402
from python.tasking_contracts.common.scripted_runtime import (  # noqa: E402
    ScriptedRuntimeAgent,
    ScriptedRuntimeAgentSpec,
)


DEFAULT_SCENARIO = resolve_repo_path(
    "scenarios", "air_combat", "cooperative_air_2v2_scripted_ew_response_v1.json"
)


def _cooperative_slot_metadata(scenario_path: str) -> tuple[dict[str, str], ...]:
    """Resolve runner slots from the scenario-owned cooperative roster."""

    with open(os.path.abspath(str(scenario_path)), "r", encoding="utf-8") as handle:
        scenario = json.load(handle)
    roster = scenario.get("cooperative_roster", scenario.get("active_controllable_roster", {}))
    raw_members = roster.get("members", []) if isinstance(roster, dict) else []
    slots: list[dict[str, str]] = []
    if isinstance(raw_members, list):
        for member in raw_members:
            if not isinstance(member, dict) or not bool(member.get("is_agent", True)):
                continue
            name = str(member.get("entity", member.get("entity_name", ""))).strip()
            if not name:
                continue
            slots.append(
                {
                    "entity_name": name,
                    "formation_role_id": str(member.get("formation_role_id", "")).strip()
                    or "Unspecified",
                }
            )
    if slots:
        return tuple(slots)

    entities = scenario.get("entities", [])
    if isinstance(entities, list):
        for entity in entities:
            if not isinstance(entity, dict) or not bool(entity.get("is_agent", False)):
                continue
            name = str(entity.get("name", "")).strip()
            if name:
                slots.append({"entity_name": name, "formation_role_id": "Unspecified"})
    return tuple(slots)


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

    slot_metadata = _cooperative_slot_metadata(scenario_path)
    if not slot_metadata:
        raise ValueError("cooperative scenario must declare at least one controllable roster member")
    slot_names = tuple(item["entity_name"] for item in slot_metadata)
    slot_roles = tuple(item["formation_role_id"] for item in slot_metadata)

    vec_env = CooperativeWorldBatchVecEnv(
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
    if int(vec_env.slots_per_world) != len(slot_metadata):
        vec_env.close()
        raise RuntimeError(
            "scenario roster/runtime slot mismatch: "
            f"metadata={len(slot_metadata)} runtime={vec_env.slots_per_world}"
        )
    slot_count = len(slot_metadata)
    scenario_time_step = 0.05
    with open(os.path.abspath(str(scenario_path)), "r", encoding="utf-8") as handle:
        scenario_environment = json.load(handle).get("environment", {})
    if isinstance(scenario_environment, dict):
        try:
            scenario_time_step = float(scenario_environment.get("time_step", scenario_time_step))
        except (TypeError, ValueError):
            scenario_time_step = 0.05
    scenario_time_step = max(1.0e-6, scenario_time_step)
    agents = [
        ScriptedRuntimeAgent(
            ScriptedRuntimeAgentSpec(
                agent_id=f"air-ew-cooperative-{name.lower()}",
                model_id=AIR_SCRIPTED_EW_ACTION_MODEL_ID,
                domain="air",
                role_id="air_ew_action_controller",
                authority_scope="air_ew_response",
            ),
            AIR_SCRIPTED_MODEL_REGISTRY.create_for(
                domain="air",
                role_id="air_ew_action_controller",
                model_id=AIR_SCRIPTED_EW_ACTION_MODEL_ID,
                dt=scenario_time_step,
                max_rwr=4,
            ),
        )
        for name in slot_names
    ]
    launch_warning_steps: list[list[int]] = [[] for _ in range(slot_count)]
    countermeasure_request_steps: list[list[int]] = [[] for _ in range(slot_count)]
    countermeasure_state_samples: list[list[dict[str, Any]]] = [[] for _ in range(slot_count)]
    last_infos: list[dict[str, Any]] = [{} for _ in range(slot_count)]
    terminated = [False for _ in range(slot_count)]
    truncated = [False for _ in range(slot_count)]
    last_runtime_steps: list[Any] = [None for _ in range(slot_count)]
    scripted_opponent_reports_at_last_request: dict[str, dict[str, Any]] = {}
    steps_run = 0
    try:
        vec_env.seed(int(seed))
        observation_batch = vec_env.reset()
        for slot_index, agent in enumerate(agents):
            observation = {
                key: np.asarray(value)[slot_index] for key, value in observation_batch.items()
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
            actions = []
            for slot_index, agent in enumerate(agents):
                observation = {
                    key: np.asarray(value)[slot_index] for key, value in observation_batch.items()
                }
                rwr = np.asarray(observation.get("rwr", []), dtype=np.float32).reshape(-1, 4)
                if rwr.size and bool(np.any(rwr[:, 3] > 0.5)):
                    launch_warning_steps[slot_index].append(step)
                runtime_step = agent.step(
                    observation=observation,
                    clock_s=float(step - 1) * scenario_time_step,
                    observation_version=f"air-ew-cooperative:{slot_index}:{step - 1}",
                    context={
                        "phase_name": "stable_flight",
                        "response_doctrine": doctrine,
                        "mission_obs_mode": "basic",
                    },
                )
                last_runtime_steps[slot_index] = runtime_step
                action = np.asarray(runtime_step.action, dtype=np.float32).reshape(-1)
                if action.size >= 14 and bool(np.any(action[12:14] > 0.5)):
                    countermeasure_request_steps[slot_index].append(step)
                actions.append(action)

            observation_batch, _rewards, dones, infos = vec_env.step(
                np.asarray(actions, dtype=np.float32)
            )
            for slot_index in range(slot_count):
                last_infos[slot_index] = dict(infos[slot_index]) if len(infos) > slot_index else {}
                instrument = vec_env._slots[slot_index].last_inst
                if countermeasure_request_steps[slot_index] and countermeasure_request_steps[slot_index][-1] == step:
                    scripted_opponent_reports_at_last_request = {
                        str(entity_id): dict(report)
                        for entity_id, report in vec_env._slots[0].loader.scripted_opponent_reports.items()
                    }
                    countermeasure_state_samples[slot_index].append(
                        {
                            "step": step,
                            "chaff_remaining": int(
                                getattr(instrument, "countermeasure_chaff_remaining", -1)
                            ),
                            "flare_remaining": int(
                                getattr(instrument, "countermeasure_flare_remaining", -1)
                            ),
                            "last_release_time_s": float(
                                getattr(instrument, "countermeasure_last_release_time_s", -1.0)
                            ),
                        }
                    )
                terminated[slot_index] = bool(dones[slot_index]) if len(dones) > slot_index else False
                truncated[slot_index] = bool(last_infos[slot_index].get("truncated", False))
            steps_run = step
            if any(terminated) or any(truncated):
                break

        owner_loader = vec_env._slots[0].loader
        return _json_value(
            {
                "scenario": os.path.abspath(str(scenario_path)),
                "seed": int(seed),
                "action_mode": "air_ew_hybrid_v1",
                "response_doctrine": doctrine,
                "max_steps": int(max_steps),
                "steps": int(steps_run),
                "terminated": terminated,
                "truncated": truncated,
                "termination_reasons": [
                    str(info.get("termination_reason", "")) for info in last_infos
                ],
                "roster": [
                    {
                        "entity_name": slot_names[index],
                        "formation_role_id": slot_roles[index],
                        "scripted_opponent_owner": index == 0,
                        "scripted_opponent_count": len(vec_env._slots[index].loader.scripted_opponents),
                    }
                    for index in range(slot_count)
                ],
                "scripted_opponent_reports": scripted_opponent_reports_at_last_request,
                "launch_warning_steps": launch_warning_steps,
                "countermeasure_request_steps": countermeasure_request_steps,
                "countermeasure_state_samples": countermeasure_state_samples,
                "scripted_runtime_identity": [agent.replay_identity for agent in agents],
                "scripted_runtime_decisions": [
                    int(step.report.decision_index) if step is not None else 0
                    for step in last_runtime_steps
                ],
                "native_countermeasure_state": "instrument_state_projection",
                "playable_boundary": "ew_response_demo_without_terminal_objective",
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
    parser.add_argument("--max_steps", type=int, default=204)
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
