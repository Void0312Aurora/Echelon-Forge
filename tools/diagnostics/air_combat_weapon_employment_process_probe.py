#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from typing import Any

import numpy as np

_REPO_ROOT_HINT = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT_HINT = os.path.dirname(_REPO_ROOT_HINT)
_REPO_ROOT_HINT = os.path.dirname(_REPO_ROOT_HINT)
if _REPO_ROOT_HINT not in sys.path:
    sys.path.insert(0, _REPO_ROOT_HINT)
from python.runtime_bootstrap import ensure_repo_imports, resolve_repo_path

ensure_repo_imports()

from python.rl.control.wrappers import MultiTimescaleActionWrapper, get_action_wrapper_spec
from python.rl.runtime.single_world_batch_runtime import (
    build_single_world_batch_execution_runtime,
)
from python.rl.runtime.world_batch.vec_env import WorldBatchVecEnv
from tools.eval.sb3_eval_base import load_json_config, load_sb3_policy
from tools.diagnostics._air_combat_weapon_employment_process_probe_impl.schema import (
    FIRE_MASK_COMPONENT_NAMES,
    ACTION_SIGNAL_NAMES,
    DEFAULT_SCENARIO,
    DEFAULT_TRAIN_CONFIG,
    FULL_ACTION_COLUMNS,
    HYBRID_ACTION_COLUMNS,
    HYBRID_BINARY_POLICY_SIGNAL_NAMES,
    LETHALITY_CHAIN_CONTRACT_SCHEMA_VERSION,
    LETHALITY_CHAIN_ROW_FIELDS,
    LETHALITY_CHAIN_SCHEMA_VERSION,
    LETHALITY_CHAIN_STAGES,
    SELF_DAMAGE_CONSEQUENCE_REWARD_PREFIX,
    TARGET_DAMAGE_CONSEQUENCE_REWARD_PREFIX,
    _event_info_columns,
    _launch_window_config_from_train_config,
    _action_columns_for_mode,
    _bool_int,
    _c2_roe_event_columns,
    _clamp_unit,
    _damage_consequence_reward_columns,
    _distance_m,
    _entity_id,
    _event_id,
    _finite_float,
    _health_current,
    _mission_command_dict,
    _positive_finite,
    _reward_terms_prefix_total,
    _stable_json,
    _target_track,
    _unit_id_set,
    _weapon_select_id,
)
from tools.diagnostics._air_combat_weapon_employment_process_probe_impl.lethality_chain import (
    _append_unique_lethality_component_response_rows,
    _append_unique_lethality_chain_rows,
    _effects_event_has_warhead_load,
    _lethality_chain_rows,
    _lethality_component_response_rows,
    _lethality_evidence_level,
    _lethality_trace_indexes,
    _parse_platform_damage_state_delta,
    _project_current_lethality_component_response_rows,
    _project_current_lethality_chain_rows,
)
from tools.diagnostics._air_combat_weapon_employment_process_probe_impl.lethality_abstraction import (
    _lethality_chain_decoupling_summary,
    _lethality_chain_stage_abstractions,
)
from tools.diagnostics._air_combat_weapon_employment_process_probe_impl.lethality_scalar_ledger import (
    _lethality_chain_scalar_ledger,
    _scalar_coupling_summary,
)
from tools.diagnostics._air_combat_weapon_employment_process_probe_impl.lethality_rows import (
    _lethality_base_row,
    _lethality_header_base_kwargs,
)
from tools.diagnostics._air_combat_weapon_employment_process_probe_impl.lethality_snapshot import (
    _lethality_chain_snapshot_columns,
)
from tools.diagnostics._air_combat_weapon_employment_process_probe_impl.output_writers import (
    plot_rows,
    write_csv,
    write_json,
)
from tools.diagnostics._air_combat_weapon_employment_process_probe_impl.policy_diagnostics import (
    _base_action,
    _distribution_policy_diagnostics,
    _forced_fire_action,
    _legal_fire_mask_open,
    _stopping_policy_diagnostics,
    _window_classifier_policy_diagnostics,
    _model_action,
    _model_policy_diagnostics,
    _policy_c2_context,
    _range_gate_fire_action,
    _switch_explore_action,
    _uniform_action,
)
from tools.diagnostics._air_combat_weapon_employment_process_probe_impl.probe_env import (
    _apply_diagnostic_dcr_bridge,
    _base_env,
    _BatchSingleWorldProbeEnv,
    _BatchSingleWorldProbeView,
    _BatchSingleWorldSimProxy,
    _diagnostic_dcr_bridge_overrides,
)
from tools.diagnostics._air_combat_weapon_employment_process_probe_impl.snapshot import (
    _controlled_consequence_bridge_record,
    _last_row_before_auto_reset,
    _snapshot_row,
)
from tools.diagnostics._air_combat_weapon_employment_process_probe_impl.summarize import (
    _summarize_episode,
)
from tools.diagnostics import mlf9_statistical_trends

_CANONICAL_WORLD_BATCH_VEC_ENV = WorldBatchVecEnv

__all__ = (
    "FIRE_MASK_COMPONENT_NAMES",
    "ACTION_SIGNAL_NAMES",
    "DEFAULT_SCENARIO",
    "DEFAULT_TRAIN_CONFIG",
    "FULL_ACTION_COLUMNS",
    "HYBRID_ACTION_COLUMNS",
    "HYBRID_BINARY_POLICY_SIGNAL_NAMES",
    "LETHALITY_CHAIN_CONTRACT_SCHEMA_VERSION",
    "LETHALITY_CHAIN_ROW_FIELDS",
    "LETHALITY_CHAIN_SCHEMA_VERSION",
    "LETHALITY_CHAIN_STAGES",
    "MultiTimescaleActionWrapper",
    "SELF_DAMAGE_CONSEQUENCE_REWARD_PREFIX",
    "TARGET_DAMAGE_CONSEQUENCE_REWARD_PREFIX",
    "WorldBatchVecEnv",
    "build_arg_parser",
    "get_action_wrapper_spec",
    "main",
    "plot_rows",
    "resolve_repo_path",
    "run_probe",
    "write_csv",
    "write_json",
    "_BatchSingleWorldProbeEnv",
    "_BatchSingleWorldProbeView",
    "_BatchSingleWorldSimProxy",
    "_event_info_columns",
    "_launch_window_config_from_train_config",
    "_action_columns_for_mode",
    "_append_unique_lethality_component_response_rows",
    "_append_unique_lethality_chain_rows",
    "_apply_diagnostic_dcr_bridge",
    "_base_action",
    "_base_env",
    "_bool_int",
    "_build_env",
    "_c2_roe_event_columns",
    "_clamp_unit",
    "_controlled_consequence_bridge_record",
    "_damage_consequence_reward_columns",
    "_diagnostic_dcr_bridge_overrides",
    "_distance_m",
    "_distribution_policy_diagnostics",
    "_effects_event_has_warhead_load",
    "_entity_id",
    "_event_id",
    "_finite_float",
    "_forced_fire_action",
    "_health_current",
    "_last_row_before_auto_reset",
    "_legal_fire_mask_open",
    "_legal_mask_fire_action",
    "_lethality_base_row",
    "_lethality_chain_rows",
    "_lethality_chain_decoupling_summary",
    "_lethality_chain_scalar_ledger",
    "_lethality_chain_snapshot_columns",
    "_lethality_chain_stage_abstractions",
    "_lethality_component_response_rows",
    "_lethality_evidence_level",
    "_lethality_header_base_kwargs",
    "_lethality_trace_indexes",
    "_stopping_policy_diagnostics",
    "_window_classifier_policy_diagnostics",
    "_mission_command_dict",
    "_model_action",
    "_model_policy_diagnostics",
    "_parse_platform_damage_state_delta",
    "_policy_c2_context",
    "_positive_finite",
    "_project_current_lethality_component_response_rows",
    "_project_current_lethality_chain_rows",
    "_range_gate_fire_action",
    "_reward_terms_prefix_total",
    "_scalar_coupling_summary",
    "_snapshot_row",
    "_stable_json",
    "_summarize_episode",
    "_switch_explore_action",
    "_target_track",
    "_uniform_action",
    "_unit_id_set",
    "_weapon_select_id",
)


def _build_env(scenario_path: str, train_config: dict[str, Any] | None):
    env_cfg = train_config.get("env", {}) if isinstance(train_config, dict) else {}
    env_cfg = env_cfg if isinstance(env_cfg, dict) else {}
    wrapper_class, wrapper_kwargs = get_action_wrapper_spec(train_config)
    if wrapper_class is not None and wrapper_class is not MultiTimescaleActionWrapper:
        raise ValueError(
            "air-combat process diagnostics only supports maintained WorldBatchVecEnv "
            f"or MultiTimescaleActionWrapper controller configs; got {wrapper_class!r}"
        )
    env_settings = {
        "include_visual": bool(env_cfg.get("include_visual", False)),
        "include_proprio": bool(env_cfg.get("include_proprio", True)),
        "action_mode": str(env_cfg.get("action_mode", "full")),
        "mission_obs_mode": str(env_cfg.get("mission_obs_mode", "basic")),
        "visual_downsample": int(env_cfg.get("visual_downsample", 1)),
        "visual_update_interval": int(env_cfg.get("visual_update_interval", 1)),
        "temporal_history_len": int(env_cfg.get("temporal_history_len", 1)),
        "execution_step_runtime_mode": str(
            env_cfg.get("execution_step_runtime_mode", "compiled")
        ),
        "flight_shaping_backend": str(
            env_cfg.get("flight_shaping_backend", "compiled")
        ),
        "step_info_mode": "full",
        "action_wrapper_kwargs": (
            dict(wrapper_kwargs or {})
            if wrapper_class is MultiTimescaleActionWrapper
            else None
        ),
    }
    if WorldBatchVecEnv is not _CANONICAL_WORLD_BATCH_VEC_ENV:
        # Preserve the diagnostics module's constructor override seam.
        vec_env = WorldBatchVecEnv(
            scenario_path=os.path.abspath(scenario_path),
            n_envs=1,
            worker_threads=1,
            **env_settings,
        )
    else:
        runtime = build_single_world_batch_execution_runtime(
            scenario_path=os.path.abspath(scenario_path),
            env_settings=env_settings,
            worker_threads=1,
        )
        vec_env = runtime.world_vec
    return _BatchSingleWorldProbeEnv(vec_env)


def _legal_mask_fire_action(
    *,
    env,
    action_mode: str,
    already_fired: bool,
    legal_open_age_steps: int,
    fire_delay_steps: int,
    legal_fire_range_m: float = 0.0,
) -> tuple[np.ndarray, bool, int]:
    legal_open = _legal_fire_mask_open(
        env,
        action_mode=action_mode,
        fire_range_m=float(legal_fire_range_m),
    )
    next_age = int(legal_open_age_steps) + 1 if legal_open else 0
    fire = not bool(already_fired) and bool(legal_open) and next_age > max(0, int(fire_delay_steps))
    return (
        _range_gate_fire_action(fire=fire, action_mode=action_mode),
        bool(fire),
        int(next_age),
    )


def run_probe(args: argparse.Namespace) -> dict[str, Any]:
    scenario_path = os.path.abspath(args.scenario)
    train_config = load_json_config(os.path.abspath(args.train_config)) if args.train_config else {}
    launch_window_config = _launch_window_config_from_train_config(train_config)
    diagnostic_dcr_bridge_overrides = _diagnostic_dcr_bridge_overrides(args)
    model = None
    if args.mode == "model":
        if not args.model:
            raise ValueError("--mode model requires --model")
        model = load_sb3_policy(
            os.path.abspath(args.model), algo=str(args.algo), device=str(args.device)
        )

    env = _build_env(scenario_path, train_config)
    base_env = _base_env(env)
    action_mode = str(getattr(base_env, "action_mode", "full"))
    rows: list[dict[str, Any]] = []
    lethality_chain_rows: list[dict[str, Any]] = []
    lethality_chain_seen: set[tuple[int, int, int, str, str, int]] = set()
    lethality_component_response_rows: list[dict[str, Any]] = []
    lethality_component_response_seen: set[tuple[int, int, int, int, int]] = set()
    episode_summaries: list[dict[str, Any]] = []
    try:
        for ep in range(int(args.episodes)):
            rng = np.random.default_rng(int(args.seed) + ep)
            obs, _info = env.reset(seed=int(args.seed) + ep)
            _apply_diagnostic_dcr_bridge(env, diagnostic_dcr_bridge_overrides)
            base_env = _base_env(env)
            max_steps = (
                int(args.max_steps)
                if int(args.max_steps) > 0
                else int(getattr(base_env, "max_steps", 0) or 1200)
            )
            initial_units = _unit_id_set(base_env.sim)
            prev_missiles = int(
                getattr(
                    base_env.sim.get_agent_observation(base_env.agent_id), "missiles_remaining", -1
                )
            )
            release_count_so_far = 0
            range_gate_fired = False
            legal_mask_fired = False
            legal_open_age_steps = 0
            ep_rows: list[dict[str, Any]] = []
            ep_chain_rows: list[dict[str, Any]] = []
            initial_row = _snapshot_row(
                episode=ep,
                step=0,
                env=env,
                action=None,
                reward=0.0,
                terminated=False,
                truncated=False,
                info={},
                initial_units=initial_units,
                prev_missiles=None,
                prev_release_count=release_count_so_far,
                policy_diagnostics=None,
            )
            rows.append(initial_row)
            ep_rows.append(initial_row)
            initial_chain_rows = _project_current_lethality_chain_rows(
                episode=ep,
                step=0,
                sim_time_s=float(initial_row.get("sim_time_s", 0.0)),
                sim=base_env.sim,
            )
            _append_unique_lethality_chain_rows(
                lethality_chain_rows, lethality_chain_seen, initial_chain_rows
            )
            _append_unique_lethality_chain_rows(ep_chain_rows, set(), initial_chain_rows)
            initial_component_response_rows = (
                _project_current_lethality_component_response_rows(
                    episode=ep,
                    step=0,
                    sim_time_s=float(initial_row.get("sim_time_s", 0.0)),
                    sim=base_env.sim,
                )
            )
            _append_unique_lethality_component_response_rows(
                lethality_component_response_rows,
                lethality_component_response_seen,
                initial_component_response_rows,
            )
            for step in range(1, max_steps + 1):
                policy_diagnostics: dict[str, Any] = {}
                if args.mode == "forced_fire":
                    action = _forced_fire_action(obs, rng, step, action_mode=action_mode)
                elif args.mode == "hold_fire":
                    action = _range_gate_fire_action(fire=False, action_mode=action_mode)
                elif args.mode == "range_gate_fire":
                    base_env = _base_env(env)
                    target_id = int(base_env.loader.primary_target_id or 0)
                    own_obs = base_env.sim.get_agent_observation(base_env.agent_id)
                    fire = (
                        not bool(range_gate_fired)
                        and target_id > 0
                        and bool(getattr(own_obs, "can_fire", False))
                        and _distance_m(base_env.sim, base_env.agent_id, target_id)
                        <= float(args.fire_range_m)
                    )
                    action = _range_gate_fire_action(fire=fire, action_mode=action_mode)
                    if fire:
                        range_gate_fired = True
                elif args.mode == "legal_mask_fire":
                    action, fire, legal_open_age_steps = _legal_mask_fire_action(
                        env=env,
                        action_mode=action_mode,
                        already_fired=legal_mask_fired,
                        legal_open_age_steps=legal_open_age_steps,
                        fire_delay_steps=int(getattr(args, "fire_delay_steps", 0)),
                        legal_fire_range_m=float(getattr(args, "legal_fire_range_m", 0.0)),
                    )
                    if fire:
                        legal_mask_fired = True
                elif args.mode == "switch_explore":
                    action = _switch_explore_action(obs, rng, step, action_mode=action_mode)
                elif args.mode == "uniform":
                    action = _uniform_action(env, obs, rng, step)
                elif args.mode == "model":
                    policy_diagnostics = _model_policy_diagnostics(model, obs)
                    policy_diagnostics.update(_policy_c2_context(env))
                    action = _model_action(model, obs, deterministic=not bool(args.stochastic))
                else:
                    raise ValueError(f"unknown mode: {args.mode}")

                obs, reward, terminated, truncated, info = env.step(action)
                row = _snapshot_row(
                    episode=ep,
                    step=step,
                    env=env,
                    action=action,
                    reward=float(reward),
                    terminated=bool(terminated),
                    truncated=bool(truncated),
                    info=info if isinstance(info, dict) else {},
                    initial_units=initial_units,
                    prev_missiles=prev_missiles,
                    prev_release_count=release_count_so_far,
                    policy_diagnostics=policy_diagnostics,
                )
                rows.append(row)
                ep_rows.append(row)
                current_chain_rows = _project_current_lethality_chain_rows(
                    episode=ep,
                    step=step,
                    sim_time_s=float(row.get("sim_time_s", 0.0)),
                    sim=base_env.sim,
                )
                _append_unique_lethality_chain_rows(
                    lethality_chain_rows, lethality_chain_seen, current_chain_rows
                )
                ep_seen = {
                    (
                        int(existing.get("episode", 0) or 0),
                        int(existing.get("chain_id", 0) or 0),
                        int(existing.get("event_id", 0) or 0),
                        str(existing.get("stage", "") or ""),
                        str(existing.get("source_event_kind", "") or ""),
                        int(existing.get("source_event_id", 0) or 0),
                    )
                    for existing in ep_chain_rows
                }
                _append_unique_lethality_chain_rows(ep_chain_rows, ep_seen, current_chain_rows)
                current_component_response_rows = (
                    _project_current_lethality_component_response_rows(
                        episode=ep,
                        step=step,
                        sim_time_s=float(row.get("sim_time_s", 0.0)),
                        sim=base_env.sim,
                    )
                )
                _append_unique_lethality_component_response_rows(
                    lethality_component_response_rows,
                    lethality_component_response_seen,
                    current_component_response_rows,
                )
                prev_missiles = int(row.get("missiles_remaining", prev_missiles))
                release_count_so_far += int(row.get("missile_release_delta", 0) or 0)
                if bool(terminated or truncated):
                    break
            episode_summaries.append(
                _summarize_episode(
                    ep_rows,
                    launch_window_config=launch_window_config,
                    lethality_chain_rows=ep_chain_rows,
                )
            )
    finally:
        try:
            env.close()
        except Exception:
            pass

    reasons = Counter(str(row.get("termination_reason", "")) for row in episode_summaries)
    lethality_chain_stage_abstractions = _lethality_chain_stage_abstractions(
        lethality_chain_rows,
        component_response_rows=lethality_component_response_rows,
    )
    lethality_chain_scalar_ledger = _lethality_chain_scalar_ledger(
        lethality_chain_rows,
        component_response_rows=lethality_component_response_rows,
    )
    payload = {
        "scenario": scenario_path,
        "train_config": os.path.abspath(args.train_config) if args.train_config else None,
        "action_mode": action_mode,
        "mode": str(args.mode),
        "fire_delay_steps": int(getattr(args, "fire_delay_steps", 0)),
        "legal_fire_range_m": float(getattr(args, "legal_fire_range_m", 0.0)),
        "diagnostic_dcr_bridge": bool(getattr(args, "diagnostic_dcr_bridge", False)),
        "diagnostic_dcr_bridge_reward_overrides": dict(diagnostic_dcr_bridge_overrides),
        "model": os.path.abspath(args.model) if args.model else None,
        "seed": int(args.seed),
        "episodes": int(args.episodes),
        "rows": len(rows),
        "lethality_chain_rows": lethality_chain_rows,
        "lethality_component_response_rows": lethality_component_response_rows,
        "lethality_chain_stage_abstractions": lethality_chain_stage_abstractions,
        "lethality_chain_decoupling_summary": _lethality_chain_decoupling_summary(
            lethality_chain_stage_abstractions
        ),
        "lethality_chain_scalar_ledger": lethality_chain_scalar_ledger,
        "lethality_chain_scalar_coupling_summary": _scalar_coupling_summary(
            lethality_chain_scalar_ledger
        ),
        "termination_reasons": dict(sorted(reasons.items())),
        "episode_summaries": episode_summaries,
        "controlled_consequence_bridge_records": [
            _controlled_consequence_bridge_record(summary) for summary in episode_summaries
        ],
    }
    mlf9_report = mlf9_statistical_trends.summarize_trends(
        lethality_chain_rows,
        group_by=mlf9_statistical_trends.normalize_group_by(
            getattr(args, "mlf9_group_by", "all")
        ),
        confidence_level=float(getattr(args, "mlf9_confidence_level", 0.95)),
        sample_source="process_probe_lethality_chain_rows",
        report_surface="process_probe_retained_diagnostics_artifact",
    )
    payload["mlf9_statistical_trends"] = mlf9_report
    if args.csv_out:
        write_csv(args.csv_out, rows)
        payload["csv_out"] = os.path.abspath(args.csv_out)
    if args.chain_csv_out:
        write_csv(args.chain_csv_out, lethality_chain_rows)
        payload["chain_csv_out"] = os.path.abspath(args.chain_csv_out)
    if getattr(args, "mlf9_report_json_out", ""):
        write_json(str(args.mlf9_report_json_out), mlf9_report)
        payload["mlf9_report_json_out"] = os.path.abspath(str(args.mlf9_report_json_out))
    if args.json_out:
        write_json(args.json_out, payload)
    if args.plot_out:
        plot_rows(rows, args.plot_out)
        payload["plot_out"] = os.path.abspath(args.plot_out)
    return payload


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Trace air-combat weapon-employment and lethality process signals."
    )
    parser.add_argument("--scenario", default=DEFAULT_SCENARIO)
    parser.add_argument("--train_config", default=DEFAULT_TRAIN_CONFIG)
    parser.add_argument(
        "--mode",
        choices=[
            "forced_fire",
            "hold_fire",
            "range_gate_fire",
            "legal_mask_fire",
            "switch_explore",
            "uniform",
            "model",
        ],
        default="forced_fire",
    )
    parser.add_argument("--fire_range_m", type=float, default=12000.0)
    parser.add_argument(
        "--fire_delay_steps",
        type=int,
        default=0,
        help="For --mode legal_mask_fire, wait this many consecutive legal-open steps before pulsing fire.",
    )
    parser.add_argument(
        "--legal_fire_range_m",
        type=float,
        default=0.0,
        help="For --mode legal_mask_fire, optional range gate in meters; <=0 disables the range gate.",
    )
    parser.add_argument("--model", default="", help="SB3 model path for --mode model.")
    parser.add_argument("--algo", default="auto")
    parser.add_argument("--device", default="auto")
    parser.add_argument("--episodes", type=int, default=1)
    parser.add_argument("--seed", type=int, default=20260525)
    parser.add_argument("--max_steps", type=int, default=0)
    parser.add_argument(
        "--stochastic",
        action="store_true",
        help="Use stochastic policy prediction in --mode model.",
    )
    parser.add_argument(
        "--diagnostic_dcr_bridge",
        action="store_true",
        help="Enable DCR consequence rewards inside this diagnostics probe only.",
    )
    parser.add_argument(
        "--diagnostic_dcr_target_scale",
        type=float,
        default=1.0,
        help="Probe-only target DCR consequence scale used with --diagnostic_dcr_bridge.",
    )
    parser.add_argument(
        "--diagnostic_dcr_self_scale",
        type=float,
        default=1.0,
        help="Probe-only self DCR consequence scale used with --diagnostic_dcr_bridge.",
    )
    parser.add_argument(
        "--diagnostic_dcr_delta_clip",
        type=float,
        default=1.0,
        help="Probe-only DCR consequence delta clip used with --diagnostic_dcr_bridge.",
    )
    parser.add_argument("--csv_out", default="")
    parser.add_argument("--chain_csv_out", default="")
    parser.add_argument(
        "--mlf9_report_json_out",
        default="",
        help="Optional retained diagnostics-only MLF-9 trend report JSON path.",
    )
    parser.add_argument(
        "--mlf9_group_by",
        default="all",
        help="Comma-separated MLF-9 trend grouping fields.",
    )
    parser.add_argument(
        "--mlf9_confidence_level",
        type=mlf9_statistical_trends.parse_confidence_level,
        default=0.95,
    )
    parser.add_argument("--json_out", default="")
    parser.add_argument("--plot_out", default="")
    return parser


def main() -> int:
    args = build_arg_parser().parse_args()
    payload = run_probe(args)
    print(json.dumps(payload, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
