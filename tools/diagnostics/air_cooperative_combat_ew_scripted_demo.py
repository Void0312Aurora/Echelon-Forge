#!/usr/bin/env python3
"""Run the RL-independent cooperative Air C2/ROE plus EW terminal surrogate."""

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

from python.simulation import create_cooperative_backend  # noqa: E402
from python.tasking_contracts.air.combat_ew.model import (  # noqa: E402
    AIR_COMBAT_EW_ROLE_ID,
    AIR_SCRIPTED_COMBAT_EW_MODEL_ID,
)
from python.tasking_contracts.air.engagement.model import AIR_COMBAT_C2_ROE_V2  # noqa: E402
from python.tasking_contracts.air.ew.model import (  # noqa: E402
    AIR_EW_HYBRID_V2_ACTION_DIM,
    AIR_EW_JAMMER_DOCTRINES,
)
from python.tasking_contracts.air.registry import AIR_SCRIPTED_MODEL_REGISTRY  # noqa: E402
from python.tasking_contracts.common.decision_runtime import (  # noqa: E402
    DecisionRuntimeAgent,
    DecisionRuntimeAgentSpec,
)
from tools.diagnostics.air_cooperative_ew_scripted_demo import (  # noqa: E402
    _cooperative_slot_metadata,
)


DEFAULT_SCENARIO = resolve_repo_path(
    "scenarios", "air_combat", "cooperative_air_2v2_scripted_c2_roe_ew_terminal_v1.json"
)
RESPONSE_DOCTRINES = ("observe_only", "countermeasure_ready", "chaff_only", "flare_only")
PLAYABLE_BOUNDARY = (
    "bounded_multi_aircraft_terminal_ew_surrogate: two scripted Blue aircraft "
    "close a native shared terminal objective while their EW tails are accepted "
    "by the native dispenser and jammer owners. Chaff and flare only consume "
    "inventory, jammer burn-through is an uncalibrated proxy, DRFM false tracks "
    "are not modeled, and the generic Aircraft targets are surrogates; this is "
    "not a playable EW claim."
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


def _countermeasure_state(instrument: Any) -> dict[str, Any]:
    return {
        "chaff_remaining": int(getattr(instrument, "countermeasure_chaff_remaining", -1)),
        "flare_remaining": int(getattr(instrument, "countermeasure_flare_remaining", -1)),
        "last_release_time_s": float(getattr(instrument, "countermeasure_last_release_time_s", -1.0)),
    }


def run_demo(
    *,
    scenario_path: str,
    seed: int,
    max_steps: int,
    response_doctrine: str = "countermeasure_ready",
    jammer_doctrine: str = "self_protect_on_lock",
) -> dict[str, Any]:
    response = str(response_doctrine).strip().lower()
    if response not in RESPONSE_DOCTRINES:
        raise ValueError(f"response_doctrine must be one of {RESPONSE_DOCTRINES}")
    jammer = str(jammer_doctrine).strip().lower()
    if jammer not in AIR_EW_JAMMER_DOCTRINES:
        raise ValueError(f"jammer_doctrine must be one of {AIR_EW_JAMMER_DOCTRINES}")

    slot_metadata = _cooperative_slot_metadata(scenario_path)
    if not slot_metadata:
        raise ValueError("cooperative scenario must declare at least one controllable roster member")
    slot_names = tuple(item["entity_name"] for item in slot_metadata)
    slot_roles = tuple(item["formation_role_id"] for item in slot_metadata)
    vec_env = create_cooperative_backend(
        backend_id="world_batch",
        scenario_path=os.path.abspath(str(scenario_path)),
        n_envs=1,
        include_visual=False,
        include_proprio=True,
        action_mode="air_ew_hybrid_v2",
        mission_obs_mode=AIR_COMBAT_C2_ROE_V2,
        step_info_mode="full",
        execution_step_runtime_mode="compiled",
        flight_shaping_backend="compiled",
        worker_threads=1,
    )
    agents: list[DecisionRuntimeAgent] = []
    last_infos: list[dict[str, Any]] = []
    last_runtime_steps: list[Any] = []
    terminated: list[bool] = []
    truncated: list[bool] = []
    steps_run = 0
    try:
        vec_env.seed(int(seed))
        observation_batch = vec_env.reset()
        runtime_slot_metadata = tuple(vec_env.cooperative_slot_metadata())
        if int(vec_env.slots_per_world) != len(slot_metadata) or len(runtime_slot_metadata) != len(slot_metadata):
            raise RuntimeError(
                "scenario roster/runtime slot mismatch: "
                f"metadata={len(slot_metadata)} runtime={vec_env.slots_per_world} "
                f"provider={len(runtime_slot_metadata)}"
            )
        agents = [
            DecisionRuntimeAgent(
                DecisionRuntimeAgentSpec(
                    agent_id=f"air-combat-ew-cooperative-{name.lower()}",
                    model_id=AIR_SCRIPTED_COMBAT_EW_MODEL_ID,
                    domain="air",
                    role_id=AIR_COMBAT_EW_ROLE_ID,
                    authority_scope="air_weapons_c2_ew_response",
                ),
                AIR_SCRIPTED_MODEL_REGISTRY.create_for(
                    domain="air",
                    role_id=AIR_COMBAT_EW_ROLE_ID,
                    model_id=AIR_SCRIPTED_COMBAT_EW_MODEL_ID,
                    action_dim=AIR_EW_HYBRID_V2_ACTION_DIM,
                    max_rwr=4,
                    dt=0.05,
                    mission_obs_mode=AIR_COMBAT_C2_ROE_V2,
                    weapon_station_id=1,
                ),
            )
            for name in slot_names
        ]
        last_infos = [{} for _ in agents]
        last_runtime_steps = [None for _ in agents]
        terminated = [False for _ in agents]
        truncated = [False for _ in agents]
        launch_warning_steps: list[list[int]] = [[] for _ in agents]
        countermeasure_request_steps: list[list[int]] = [[] for _ in agents]
        countermeasure_state_samples: list[list[dict[str, Any]]] = [[] for _ in agents]
        jammer_request_steps: list[list[int]] = [[] for _ in agents]
        jammer_transmit_steps: list[list[int]] = [[] for _ in agents]
        accepted_steps: list[list[int]] = [[] for _ in agents]
        release_steps: list[list[int]] = [[] for _ in agents]
        pre_request_state: list[dict[str, Any] | None] = [None for _ in agents]
        last_unrequested_state: list[dict[str, Any] | None] = [None for _ in agents]
        for slot_index, agent in enumerate(agents):
            observation = {key: np.asarray(value)[slot_index] for key, value in observation_batch.items()}
            agent.reset(
                context={
                    "observation": observation,
                    "phase_name": "stable_flight",
                    "mission_obs_mode": AIR_COMBAT_C2_ROE_V2,
                    "response_doctrine": response,
                    "jammer_doctrine": jammer,
                },
                episode_seed=int(seed),
            )

        for step in range(1, max(1, int(max_steps)) + 1):
            actions = []
            for slot_index, agent in enumerate(agents):
                observation = {key: np.asarray(value)[slot_index] for key, value in observation_batch.items()}
                rwr = np.asarray(observation.get("rwr", []), dtype=np.float32).reshape(-1, 4)
                if rwr.size and bool(np.any(rwr[:, 3] > 0.5)):
                    launch_warning_steps[slot_index].append(step)
                runtime_step = agent.step(
                    observation=observation,
                    clock_s=float(step - 1) * 0.05,
                    observation_version=f"air-combat-ew-cooperative:{slot_index}:{step - 1}",
                    context={
                        "phase_name": "stable_flight",
                        "mission_obs_mode": AIR_COMBAT_C2_ROE_V2,
                        "response_doctrine": response,
                        "jammer_doctrine": jammer,
                        "last_event_info": last_infos[slot_index],
                    },
                )
                last_runtime_steps[slot_index] = runtime_step
                action = np.asarray(runtime_step.action, dtype=np.float32).reshape(-1)
                if action.size != AIR_EW_HYBRID_V2_ACTION_DIM:
                    raise RuntimeError(
                        f"cooperative combat-EW model returned {action.size} values, "
                        f"expected {AIR_EW_HYBRID_V2_ACTION_DIM}"
                    )
                if bool(np.any(action[12:14] > 0.5)):
                    countermeasure_request_steps[slot_index].append(step)
                if bool(action[14] > 0.5):
                    jammer_request_steps[slot_index].append(step)
                actions.append(action)

            observation_batch, _rewards, dones, infos = vec_env.step(np.asarray(actions, dtype=np.float32))
            for slot_index in range(len(agents)):
                last_infos[slot_index] = dict(infos[slot_index]) if len(infos) > slot_index else {}
                if bool(last_infos[slot_index].get("fire_once_accepted", False)):
                    accepted_steps[slot_index].append(step)
                if bool(last_infos[slot_index].get("release_executed", False)):
                    release_steps[slot_index].append(step)
                terminated[slot_index] = bool(dones[slot_index]) if len(dones) > slot_index else False
                truncated[slot_index] = bool(last_infos[slot_index].get("truncated", False))
                if terminated[slot_index] or truncated[slot_index]:
                    continue
                instrument = vec_env._slots[slot_index].last_inst
                if bool(getattr(instrument, "jammer_transmitting", False)):
                    jammer_transmit_steps[slot_index].append(step)
                countermeasure_requested = (
                    countermeasure_request_steps[slot_index]
                    and countermeasure_request_steps[slot_index][-1] == step
                )
                if countermeasure_requested:
                    if pre_request_state[slot_index] is None and last_unrequested_state[slot_index] is not None:
                        pre_request_state[slot_index] = dict(last_unrequested_state[slot_index])
                    countermeasure_state_samples[slot_index].append(
                        {"step": step, **_countermeasure_state(instrument)}
                    )
                else:
                    last_unrequested_state[slot_index] = {"step": step, **_countermeasure_state(instrument)}
            steps_run = step
            if any(terminated) or any(truncated):
                break

        owner_loader = vec_env._slots[0].loader
        return _json_value(
            {
                "scenario": os.path.abspath(str(scenario_path)),
                "seed": int(seed),
                "action_mode": "air_ew_hybrid_v2",
                "mission_obs_mode": AIR_COMBAT_C2_ROE_V2,
                "response_doctrine": response,
                "jammer_doctrine": jammer,
                "max_steps": int(max_steps),
                "steps": int(steps_run),
                "terminated": terminated,
                "truncated": truncated,
                "termination_reasons": [str(info.get("termination_reason", "")) for info in last_infos],
                "roster": [
                    {
                        "entity_name": slot_names[index],
                        "formation_role_id": slot_roles[index],
                        "target_owner_name": str(runtime_slot_metadata[index].get("target_owner_name", "")),
                        "scripted_opponent_owner": index == 0,
                        "scripted_opponent_count": len(vec_env._slots[index].loader.scripted_opponents),
                    }
                    for index in range(len(agents))
                ],
                "fire_once_accepted_steps": accepted_steps,
                "release_executed_steps": release_steps,
                "launch_warning_steps": launch_warning_steps,
                "countermeasure_request_steps": countermeasure_request_steps,
                "countermeasure_state_samples": countermeasure_state_samples,
                "pre_request_countermeasure_state": pre_request_state,
                "jammer_request_steps": jammer_request_steps,
                "jammer_transmit_steps": jammer_transmit_steps,
                "scripted_opponent_reports": dict(owner_loader.scripted_opponent_reports),
                "scripted_runtime_identity": [agent.replay_identity for agent in agents],
                "scripted_runtime_decisions": [
                    int(step.report.decision_index) if step is not None else 0
                    for step in last_runtime_steps
                ],
                "native_state_sample_last_step": int(
                    steps_run - 1 if any(terminated) or any(truncated) else steps_run
                ),
                "playable_boundary": PLAYABLE_BOUNDARY,
                "last_infos": last_infos,
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
    parser.add_argument("--max_steps", type=int, default=600)
    parser.add_argument("--response_doctrine", choices=RESPONSE_DOCTRINES, default="countermeasure_ready")
    parser.add_argument("--jammer_doctrine", choices=AIR_EW_JAMMER_DOCTRINES, default="self_protect_on_lock")
    parser.add_argument("--json_out", default="")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    payload = run_demo(
        scenario_path=args.scenario,
        seed=args.seed,
        max_steps=args.max_steps,
        response_doctrine=args.response_doctrine,
        jammer_doctrine=args.jammer_doctrine,
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
