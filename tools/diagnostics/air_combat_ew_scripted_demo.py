#!/usr/bin/env python3
"""Run the scripted Air combat model with its EW self-protection tail, no RL.

One aircraft runs the registered ``air.combat_ew.c2_roe_ew_scripted`` model:
the C2/ROE engagement action is emitted unchanged in the shared 12-element
prefix and the RWR-derived countermeasure (and optional jammer) intent rides in
the versioned ``air_ew_hybrid_v1``/``v2`` tail. The environment fire gate owns
release acceptance and the native EW owners own dispense and jammer state; the
report only reads them back.
"""

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

from python.simulation import create_single_backend  # noqa: E402
from python.tasking_contracts.air.combat_ew.model import (  # noqa: E402
    AIR_COMBAT_EW_ROLE_ID,
    AIR_SCRIPTED_COMBAT_EW_MODEL_ID,
)
from python.tasking_contracts.air.engagement.model import AIR_COMBAT_C2_ROE_V2  # noqa: E402
from python.tasking_contracts.air.ew.model import (  # noqa: E402
    AIR_EW_HYBRID_ACTION_DIM,
    AIR_EW_HYBRID_V2_ACTION_DIM,
    AIR_EW_JAMMER_DOCTRINES,
)
from python.tasking_contracts.air.registry import AIR_SCRIPTED_MODEL_REGISTRY  # noqa: E402
from python.tasking_contracts.common.decision_runtime import (  # noqa: E402
    DecisionRuntimeAgent,
    DecisionRuntimeAgentSpec,
)


DEFAULT_SCENARIO = resolve_repo_path(
    "scenarios", "air_combat", "air_combat_1v1_c2_roe_ew_terminal_v1.json"
)
RESPONSE_DOCTRINES = ("observe_only", "countermeasure_ready", "chaff_only", "flare_only")
PLAYABLE_BOUNDARY = (
    "bounded_terminal_adapter: one scripted aircraft closes a native terminal "
    "objective while its EW tail is accepted by the native dispenser and jammer "
    "owners. This fixture measures chaff/flare inventory changes rather than "
    "seeker seduction, and jammer transmission rather than calibrated suppression. "
    "The opponent is a generic Aircraft surrogate; this is not a playable EW claim."
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
    response_doctrine: str,
    jammer_doctrine: str | None = None,
    dispense_burst_s: float | None = None,
    dispense_bearing_gate_deg: float | None = None,
    post_launch_assessment: bool = False,
) -> dict[str, Any]:
    doctrine = str(response_doctrine).strip().lower()
    if doctrine not in RESPONSE_DOCTRINES:
        raise ValueError(f"response_doctrine must be one of {RESPONSE_DOCTRINES}")
    # Without a jammer doctrine the demo stays on the countermeasure-only v1 tail.
    jammer = None if jammer_doctrine is None else str(jammer_doctrine).strip().lower()
    if jammer is not None and jammer not in AIR_EW_JAMMER_DOCTRINES:
        raise ValueError(f"jammer_doctrine must be one of {AIR_EW_JAMMER_DOCTRINES}")
    if (dispense_burst_s is None) != (dispense_bearing_gate_deg is None):
        raise ValueError("burst dispense needs both dispense_burst_s and dispense_bearing_gate_deg")
    action_mode = "air_ew_hybrid_v1" if jammer is None else "air_ew_hybrid_v2"
    action_dim = AIR_EW_HYBRID_ACTION_DIM if jammer is None else AIR_EW_HYBRID_V2_ACTION_DIM
    model_context: dict[str, Any] = {
        "phase_name": "stable_flight",
        "mission_obs_mode": AIR_COMBAT_C2_ROE_V2,
        "response_doctrine": doctrine,
    }
    if jammer is not None:
        model_context["jammer_doctrine"] = jammer
    if dispense_burst_s is not None:
        model_context["dispense_program"] = "burst"
        model_context["dispense_burst_s"] = float(dispense_burst_s)
        model_context["dispense_bearing_gate_deg"] = float(dispense_bearing_gate_deg)

    vec_env = create_single_backend(
        backend_id="world_batch",
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
        role_id=AIR_COMBAT_EW_ROLE_ID,
        model_id=AIR_SCRIPTED_COMBAT_EW_MODEL_ID,
        action_dim=action_dim,
        max_rwr=4,
        dt=0.05,
        mission_obs_mode=AIR_COMBAT_C2_ROE_V2,
        # The fixture declares station 1 through the maintained loadout seam;
        # the engagement model fails closed if a runtime omits or invalidates it.
        weapon_station_id=1,
    )
    agent = DecisionRuntimeAgent(
        DecisionRuntimeAgentSpec(
            agent_id="air-combat-ew-scripted-demo",
            model_id=AIR_SCRIPTED_COMBAT_EW_MODEL_ID,
            domain="air",
            role_id=AIR_COMBAT_EW_ROLE_ID,
            authority_scope="air_weapons_c2_ew_response",
        ),
        model,
    )
    release_steps: list[int] = []
    fire_accept_steps: list[int] = []
    launch_warning_steps: list[int] = []
    countermeasure_request_steps: list[int] = []
    countermeasure_state_samples: list[dict[str, Any]] = []
    jammer_request_steps: list[int] = []
    jammer_transmit_steps: list[int] = []
    # Native inventory observed at the end of the step before the first
    # request, so the report shows the decrement happening on request steps.
    pre_request_countermeasure_state: dict[str, Any] | None = None
    last_unrequested_state: dict[str, Any] | None = None
    last_info: dict[str, Any] = {}
    last_runtime_step = None
    steps_run = 0
    terminated = False
    truncated = False
    try:
        vec_env.seed(int(seed))
        observation_batch = vec_env.reset()
        agent.reset(
            context={"observation": _unbatch(observation_batch), **model_context},
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
                observation_version=f"air-combat-ew:{step - 1}",
                context=dict(model_context),
            )
            last_runtime_step = runtime_step
            steps_run = step
            action = np.asarray(runtime_step.action, dtype=np.float32).reshape(-1)
            countermeasure_requested = bool(np.any(action[12:14] > 0.5))
            if countermeasure_requested:
                countermeasure_request_steps.append(step)
            if action.size >= AIR_EW_HYBRID_V2_ACTION_DIM and bool(action[14] > 0.5):
                jammer_request_steps.append(step)
            observation_batch, _rewards, dones, infos = vec_env.step(action.reshape(1, -1))
            last_info = dict(infos[0]) if infos else {}
            if bool(last_info.get("fire_once_accepted", False)):
                fire_accept_steps.append(step)
            if bool(last_info.get("release_executed", False)):
                release_steps.append(step)
            terminated = bool(dones[0]) if len(dones) else False
            truncated = bool(last_info.get("truncated", False))
            if terminated or truncated:
                # The vec env auto-resets inside a done step, so its cached
                # instrument state already belongs to the next episode and is
                # not sampled; the terminal step is reported separately.
                break
            instrument = vec_env.envs[0].last_inst
            if bool(getattr(instrument, "jammer_transmitting", False)):
                jammer_transmit_steps.append(step)
            if countermeasure_requested:
                if pre_request_countermeasure_state is None and last_unrequested_state is not None:
                    pre_request_countermeasure_state = dict(last_unrequested_state)
                countermeasure_state_samples.append({"step": step, **_countermeasure_state(instrument)})
            else:
                last_unrequested_state = {"step": step, **_countermeasure_state(instrument)}
        payload = {
            "scenario": os.path.abspath(str(scenario_path)),
            "seed": int(seed),
            "action_mode": action_mode,
            "mission_obs_mode": AIR_COMBAT_C2_ROE_V2,
            "response_doctrine": doctrine,
            "jammer_doctrine": jammer,
            "dispense_program": model_context.get("dispense_program", "continuous"),
            "max_steps": int(max_steps),
            "steps": int(steps_run),
            "terminated": bool(terminated),
            "truncated": bool(truncated),
            "termination_reason": str(last_info.get("termination_reason", "")),
            "fire_once_accepted_steps": fire_accept_steps,
            "release_executed_steps": release_steps,
            "launch_warning_steps": launch_warning_steps,
            "countermeasure_request_steps": countermeasure_request_steps,
            "pre_request_countermeasure_state": pre_request_countermeasure_state,
            "countermeasure_state_samples": countermeasure_state_samples,
            "jammer_request_steps": jammer_request_steps,
            "jammer_transmit_steps": jammer_transmit_steps,
            "scripted_decision_info": agent.model.last_decision_info,
            "scripted_runtime_identity": agent.replay_identity,
            "scripted_runtime_decisions": int(last_runtime_step.report.decision_index)
            if last_runtime_step is not None
            else 0,
            "native_countermeasure_state": "instrument_state_projection",
            # Native EW state samples stop one step before a terminal step
            # because the auto-reset replaces the cached instrument state.
            "native_state_sample_last_step": int(steps_run - 1 if (terminated or truncated) else steps_run),
            "playable_boundary": PLAYABLE_BOUNDARY,
            "last_info": {
                key: last_info.get(key)
                for key in (
                    "fire_once_requested",
                    "fire_once_accepted",
                    "release_executed",
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
    parser.add_argument("--max_steps", type=int, default=600)
    parser.add_argument("--response_doctrine", choices=RESPONSE_DOCTRINES, default="countermeasure_ready")
    parser.add_argument(
        "--jammer_doctrine",
        choices=AIR_EW_JAMMER_DOCTRINES,
        default=None,
        help="enable the air_ew_hybrid_v2 jammer tail with this doctrine",
    )
    parser.add_argument("--dispense_burst_s", type=float, default=None)
    parser.add_argument("--dispense_bearing_gate_deg", type=float, default=None)
    parser.add_argument("--post_launch_assessment", action="store_true")
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
        dispense_burst_s=args.dispense_burst_s,
        dispense_bearing_gate_deg=args.dispense_bearing_gate_deg,
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
