from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass
from typing import Any, Callable

import numpy as np

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from tools.eval.eval_utils import (
    add_common_env_args,
    bootstrap_repo_imports,
    format_stats,
    make_single_world_batch_env_from_args,
    quantile_summary,
    wrap_deg,
)
from tools.eval.waypoint_eval_utils import (
    finalize_waypoint_episode,
    make_waypoint_distance_trackers,
    update_waypoint_distance_samples,
    update_waypoint_min_distances,
)


TaskArgBuilder = Callable[[argparse.ArgumentParser], None]


@dataclass(frozen=True)
class TaskCliConfig:
    description: str
    episodes_default: int
    max_steps_default: int
    seed_default: int
    default_action_mode: str
    include_no_randomization: bool = False
    world_model_device_default: str = "cuda"


class PolicyAdapter:
    def reset_episode(self, env, obs: dict[str, Any]) -> None:
        raise NotImplementedError

    def act(self, obs: dict[str, Any]) -> np.ndarray:
        raise NotImplementedError

    def observe(self, next_obs: dict[str, Any]) -> None:
        return None


class WorldModelPolicyAdapter(PolicyAdapter):
    def __init__(self, checkpoint: str, *, device: str, include_visual: bool, stochastic_state: bool) -> None:
        from tools.eval.world_model_eval_utils import WorldModelPolicyRunner

        self._runner = WorldModelPolicyRunner(checkpoint, device=device, include_visual=include_visual)
        self._deterministic_state = not bool(stochastic_state)

    def reset_episode(self, env, obs: dict[str, Any]) -> None:
        del env
        self._runner.reset_episode(obs, deterministic_state=self._deterministic_state)

    def act(self, obs: dict[str, Any]) -> np.ndarray:
        del obs
        return self._runner.act_env()

    def observe(self, next_obs: dict[str, Any]) -> None:
        self._runner.observe(next_obs)


class ScriptedPolicyAdapter(PolicyAdapter):
    def __init__(self, controller_builder: Callable[[Any], Any]) -> None:
        self._controller_builder = controller_builder
        self._controller = None

    def reset_episode(self, env, obs: dict[str, Any]) -> None:
        self._controller = self._controller_builder(env)
        self._controller.reset(obs)

    def act(self, obs: dict[str, Any]) -> np.ndarray:
        if self._controller is None:
            raise RuntimeError("scripted controller is not initialized")
        return self._controller.step(obs)


def _build_scripted_stable_controller(env):
    from python.rl.control.scripted_stable_flight import ScriptedStableFlightController

    return ScriptedStableFlightController(action_dim=int(env.action_space.shape[0]), dt=_env_time_step(env))


def _build_scripted_takeoff_controller(env):
    from python.rl.control.scripted_takeoff import ScriptedTakeoffController

    return ScriptedTakeoffController(action_dim=int(env.action_space.shape[0]), dt=_env_time_step(env))


SCRIPTED_CONTROLLER_BUILDERS: dict[str, Callable[[Any], Any]] = {
    "stable_flight": _build_scripted_stable_controller,
    "waypoint_nav": _build_scripted_stable_controller,
    "takeoff_roll": _build_scripted_takeoff_controller,
    "centerline": _build_scripted_takeoff_controller,
}


def add_stable_flight_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--warmup_steps", type=int, default=100, help="Ignore first N steps when computing hold fractions.")
    parser.add_argument("--alt_tol_m", type=float, default=30.0)
    parser.add_argument("--spd_tol_mps", type=float, default=10.0)
    parser.add_argument("--hdg_tol_deg", type=float, default=10.0)


def add_takeoff_roll_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--wheel_off_alt_threshold",
        type=float,
        default=None,
        help="Override wheel-off altitude threshold (AGL). Default uses scenario on_ground_alt_threshold.",
    )
    parser.add_argument(
        "--liftoff_alt_threshold",
        type=float,
        default=None,
        help="Override liftoff altitude threshold (AGL). Default uses scenario liftoff_alt_threshold.",
    )
    parser.add_argument(
        "--liftoff_ias_threshold",
        type=float,
        default=None,
        help="Override liftoff IAS threshold. Default uses scenario liftoff_speed_threshold.",
    )


def build_task_eval_parser(*, backend: str, config: TaskCliConfig) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=config.description)
    add_common_env_args(
        parser,
        episodes_default=config.episodes_default,
        max_steps_default=config.max_steps_default,
        seed_default=config.seed_default,
        default_action_mode=config.default_action_mode,
        include_no_randomization=config.include_no_randomization,
    )
    if str(backend) == "world_model":
        parser.add_argument("--checkpoint", required=True)
        parser.add_argument("--device", type=str, default=str(config.world_model_device_default))
        parser.add_argument("--stochastic_state", action="store_true")
    return parser


def run_task_eval_cli(
    *,
    task: str,
    backend: str,
    config: TaskCliConfig,
    add_task_args: TaskArgBuilder | None = None,
) -> int:
    parser = build_task_eval_parser(backend=backend, config=config)
    if add_task_args is not None:
        add_task_args(parser)
    args = parser.parse_args()
    return run_task_eval(task=task, backend=backend, args=args)


def run_task_eval(*, task: str, backend: str, args: argparse.Namespace) -> int:
    bootstrap_repo_imports()
    task_name = str(task).strip().lower()
    backend_name = str(backend).strip().lower()
    if task_name == "stable_flight":
        return _run_stable_flight_eval(backend=backend_name, args=args)
    if task_name == "takeoff_roll":
        return _run_takeoff_roll_eval(backend=backend_name, args=args)
    if task_name == "centerline":
        return _run_centerline_eval(backend=backend_name, args=args)
    if task_name == "waypoint_nav":
        return _run_waypoint_nav_eval(backend=backend_name, args=args)
    raise ValueError(f"unknown task {task!r}")


def _policy_adapter_for(*, task: str, backend: str, args: argparse.Namespace) -> PolicyAdapter:
    if backend == "world_model":
        return WorldModelPolicyAdapter(
            checkpoint=str(args.checkpoint),
            device=str(args.device),
            include_visual=bool(args.include_visual),
            stochastic_state=bool(args.stochastic_state),
        )
    if backend == "scripted":
        try:
            builder = SCRIPTED_CONTROLLER_BUILDERS[str(task)]
        except KeyError as exc:
            raise ValueError(f"no scripted controller registered for task {task!r}") from exc
        return ScriptedPolicyAdapter(builder)
    raise ValueError(f"unknown backend {backend!r}")


def _backend_summary_label(backend: str) -> str:
    if backend == "world_model":
        return "world-model"
    if backend == "scripted":
        return "scripted controller"
    return backend


def _print_common_source(args: argparse.Namespace, *, backend: str) -> None:
    print(f"scenario:   {args.scenario}")
    if backend == "world_model":
        print(f"checkpoint: {args.checkpoint}")


def _mission_status_failed(info: dict[str, Any] | Any) -> bool:
    if not isinstance(info, dict):
        return False
    mission_status = info.get("mission_status", None)
    if mission_status is None:
        return False
    try:
        arr = np.asarray(mission_status, dtype=np.float32).reshape(-1)
    except Exception:
        return False
    return bool(arr.size >= 4 and float(arr[3]) < -0.5)


def _env_base(env):
    return getattr(env, "unwrapped", env)


def _env_loader(env):
    return getattr(_env_base(env), "loader", None)


def _env_sim(env):
    return getattr(_env_base(env), "sim", None)


def _env_agent_id(env) -> int | None:
    agent_id = getattr(_env_base(env), "agent_id", None)
    if agent_id is None:
        return None
    return int(agent_id)


def _env_time_step(env) -> float:
    sim = _env_sim(env)
    if sim is not None:
        return float(sim.get_time_step())
    world_vec = getattr(env, "world_vec", None)
    if world_vec is not None:
        return float(world_vec._world_time_step(0))
    return 0.05


def _env_max_steps(env) -> int:
    world_vec = getattr(env, "world_vec", None)
    if world_vec is not None and getattr(world_vec, "envs", None):
        return int(getattr(world_vec.envs[0], "max_steps", 0))
    return int(getattr(_env_base(env), "max_steps", 0))


def _run_stable_flight_eval(*, backend: str, args: argparse.Namespace) -> int:
    env = make_single_world_batch_env_from_args(args)
    policy = _policy_adapter_for(task="stable_flight", backend=backend, args=args)

    ep_rewards: list[float] = []
    ep_steps: list[int] = []
    ep_alt_err_mean: list[float] = []
    ep_spd_err_mean: list[float] = []
    ep_hdg_err_mean: list[float] = []
    ep_hold_frac: list[float] = []
    alt_err_abs: list[float] = []
    spd_err_abs: list[float] = []
    hdg_err_abs: list[float] = []
    roll_abs: list[float] = []
    pitch_abs: list[float] = []
    crashes = 0

    try:
        for ep in range(int(args.episodes)):
            obs, _ = env.reset(seed=int(args.seed) + ep)
            policy.reset_episode(env, obs)

            done = False
            steps = 0
            total_rew = 0.0
            ep_alt: list[float] = []
            ep_spd: list[float] = []
            ep_hdg: list[float] = []
            ep_hold = 0
            hold_total = 0

            while not done and steps < int(args.max_steps):
                action = policy.act(obs)
                next_obs, reward, terminated, truncated, info = env.step(action)
                policy.observe(next_obs)
                total_rew += float(reward)

                try:
                    inst = np.asarray(next_obs["instruments"], dtype=np.float32).reshape(-1)
                    mission = np.asarray(next_obs.get("mission", []), dtype=np.float32).reshape(-1)
                except Exception:
                    inst = None
                    mission = None

                if inst is not None and mission is not None and inst.size >= 10 and mission.size >= 4:
                    ias = float(inst[0])
                    alt = float(inst[2])
                    hdg = float(inst[9])
                    roll = float(inst[8])
                    pitch = float(inst[7])
                    tgt_hdg = float(mission[1])
                    tgt_alt = float(mission[2])
                    tgt_spd = float(mission[3])

                    alt_e = abs(alt - tgt_alt)
                    spd_e = abs(ias - tgt_spd)
                    hdg_e = abs(wrap_deg(hdg - tgt_hdg))

                    alt_err_abs.append(alt_e)
                    spd_err_abs.append(spd_e)
                    hdg_err_abs.append(hdg_e)
                    roll_abs.append(abs(roll))
                    pitch_abs.append(abs(pitch))
                    ep_alt.append(alt_e)
                    ep_spd.append(spd_e)
                    ep_hdg.append(hdg_e)

                    if steps >= int(args.warmup_steps):
                        hold_total += 1
                        if (
                            alt_e <= float(args.alt_tol_m)
                            and spd_e <= float(args.spd_tol_mps)
                            and hdg_e <= float(args.hdg_tol_deg)
                        ):
                            ep_hold += 1

                if _mission_status_failed(info):
                    crashes += 1

                obs = next_obs
                steps += 1
                done = bool(terminated or truncated or steps >= int(args.max_steps))

            ep_rewards.append(float(total_rew))
            ep_steps.append(int(steps))
            ep_alt_err_mean.append(float(np.mean(ep_alt)) if ep_alt else float("nan"))
            ep_spd_err_mean.append(float(np.mean(ep_spd)) if ep_spd else float("nan"))
            ep_hdg_err_mean.append(float(np.mean(ep_hdg)) if ep_hdg else float("nan"))
            ep_hold_frac.append(float(ep_hold) / float(hold_total) if hold_total > 0 else 0.0)

        print("=" * 60)
        print(f"STABLE FLIGHT EVAL ({_backend_summary_label(backend)})")
        _print_common_source(args, backend=backend)
        print(f"episodes:   {int(args.episodes)} seed: {int(args.seed)}..{int(args.seed) + int(args.episodes) - 1}")
        print(f"action_mode:{args.action_mode} include_visual={bool(args.include_visual)} include_proprio={bool(args.include_proprio)}")
        print(
            f"tolerances: alt<= {float(args.alt_tol_m):.1f}m, spd<= {float(args.spd_tol_mps):.1f}m/s, "
            f"hdg<= {float(args.hdg_tol_deg):.1f}deg (warmup={int(args.warmup_steps)} steps)"
        )
        print("-" * 60)
        print(format_stats("episode_reward", ep_rewards))
        print(format_stats("episode_steps", [float(x) for x in ep_steps]))
        print(format_stats("episode_alt_err_mean", ep_alt_err_mean, unit="m"))
        print(format_stats("episode_spd_err_mean", ep_spd_err_mean, unit="m/s"))
        print(format_stats("episode_hdg_err_mean", ep_hdg_err_mean, unit="deg"))
        print(format_stats("episode_hold_frac", ep_hold_frac))
        print("-" * 60)
        print(format_stats("all_alt_err_abs", alt_err_abs, unit="m"))
        print(format_stats("all_spd_err_abs", spd_err_abs, unit="m/s"))
        print(format_stats("all_hdg_err_abs", hdg_err_abs, unit="deg"))
        print(format_stats("all_roll_abs", roll_abs, unit="deg"))
        print(format_stats("all_pitch_abs", pitch_abs, unit="deg"))
        print("-" * 60)
        print(f"crashes={int(crashes)}")
        print("=" * 60)
        return 0
    finally:
        env.close()


def _run_centerline_eval(*, backend: str, args: argparse.Namespace) -> int:
    env = make_single_world_batch_env_from_args(args)
    policy = _policy_adapter_for(task="centerline", backend=backend, args=args)

    ep_max_abs_cross: list[float] = []
    ep_mean_abs_cross: list[float] = []
    ep_on_runway_geom_frac: list[float] = []
    all_abs_cross: list[float] = []

    try:
        for ep in range(int(args.episodes)):
            obs, _ = env.reset(seed=int(args.seed) + ep)
            policy.reset_episode(env, obs)

            done = False
            steps = 0
            ep_cross: list[float] = []
            ground_steps = 0
            on_runway_geom_steps = 0

            while not done and steps < int(args.max_steps):
                action = policy.act(obs)
                next_obs, _reward, terminated, truncated, info = env.step(action)
                policy.observe(next_obs)

                try:
                    if float(info.get("on_ground", 0.0)) > 0.5 and "runway_cross_m" in info:
                        cross = abs(float(info["runway_cross_m"]))
                        ep_cross.append(cross)
                        all_abs_cross.append(cross)
                        ground_steps += 1
                        if float(info.get("on_runway_geom", 0.0)) > 0.5:
                            on_runway_geom_steps += 1
                except Exception:
                    pass

                obs = next_obs
                steps += 1
                done = bool(terminated or truncated or steps >= int(args.max_steps))

            if ep_cross:
                ep_max_abs_cross.append(float(np.max(ep_cross)))
                ep_mean_abs_cross.append(float(np.mean(ep_cross)))
            else:
                ep_max_abs_cross.append(0.0)
                ep_mean_abs_cross.append(0.0)
            ep_on_runway_geom_frac.append(float(on_runway_geom_steps) / float(ground_steps) if ground_steps > 0 else 0.0)

        print("=" * 60)
        print(f"CENTERLINE EVAL ({_backend_summary_label(backend)})")
        _print_common_source(args, backend=backend)
        print(
            f"episodes:   {int(args.episodes)} seed: {int(args.seed)}..{int(args.seed) + int(args.episodes) - 1}"
        )
        print(
            f"action_mode:{args.action_mode} include_visual={bool(args.include_visual)} "
            f"include_proprio={bool(args.include_proprio)} no_randomization={bool(getattr(args, 'no_randomization', False))}"
        )
        print("-" * 60)
        print(f"episode_max_abs_cross_m: {quantile_summary(ep_max_abs_cross, [0.50, 0.90, 0.95, 0.99])}")
        print(f"episode_mean_abs_cross_m: {quantile_summary(ep_mean_abs_cross, [0.50, 0.90, 0.95, 0.99])}")
        print(f"all_steps_abs_cross_m: {quantile_summary(all_abs_cross, [0.50, 0.90, 0.95, 0.99])}")
        print(f"episode_on_runway_geom_frac: {quantile_summary(ep_on_runway_geom_frac, [0.50, 0.90, 0.95, 0.99])}")
        print("=" * 60)
        return 0
    finally:
        env.close()


def _resolve_runway_along(env, info: dict[str, Any] | Any) -> float | None:
    try:
        if isinstance(info, dict) and "runway_along_m" in info:
            return float(info["runway_along_m"])
    except Exception:
        return None
    try:
        sim = _env_sim(env)
        loader = _env_loader(env)
        agent_id = _env_agent_id(env)
        if sim is None or loader is None or agent_id is None:
            return None
        truth = sim.get_agent_observation(agent_id)
        valid_rf, along_m, _cross_m, rw_len, rw_wid = loader.get_runway_local_frame(float(truth.x), float(truth.y))
        if bool(valid_rf) and float(rw_len) > 1.0 and float(rw_wid) > 1.0:
            return float(along_m)
    except Exception:
        return None
    return None


def _wheel_off_condition(
    *,
    backend: str,
    alt_agl: float,
    ias_mps: float,
    wheel_off_alt_threshold: float,
    liftoff_speed_threshold: float,
) -> bool:
    if backend == "scripted":
        return bool(alt_agl > wheel_off_alt_threshold and ias_mps >= liftoff_speed_threshold)
    return bool(alt_agl >= wheel_off_alt_threshold)


def _run_takeoff_roll_eval(*, backend: str, args: argparse.Namespace) -> int:
    env = make_single_world_batch_env_from_args(args)
    policy = _policy_adapter_for(task="takeoff_roll", backend=backend, args=args)

    wheel_off_dist_m: list[float] = []
    wheel_off_time_s: list[float] = []
    wheel_off_ias_mps: list[float] = []
    liftoff_dist_m: list[float] = []
    liftoff_time_s: list[float] = []
    liftoff_ias_mps: list[float] = []
    failures = 0

    try:
        for ep in range(int(args.episodes)):
            obs, _ = env.reset(seed=int(args.seed) + ep)
            policy.reset_episode(env, obs)
            dt = _env_time_step(env)
            max_steps = min(int(args.max_steps), _env_max_steps(env))

            try:
                loader = _env_loader(env)
                rewards_cfg = dict(loader.get_rewards_config()) if loader is not None else {}
            except Exception:
                rewards_cfg = {}

            wheel_off_alt_threshold = float(
                rewards_cfg.get("on_ground_alt_threshold", 2.5)
                if args.wheel_off_alt_threshold is None
                else args.wheel_off_alt_threshold
            )
            liftoff_alt_threshold = float(
                rewards_cfg.get("liftoff_alt_threshold", 5.0)
                if args.liftoff_alt_threshold is None
                else args.liftoff_alt_threshold
            )
            liftoff_speed_threshold = float(
                rewards_cfg.get("liftoff_speed_threshold", 80.0)
                if args.liftoff_ias_threshold is None
                else args.liftoff_ias_threshold
            )

            start_along = _resolve_runway_along(env, {})
            got_wheel_off = False
            wheel_off_time = None
            wheel_off_along = None
            wheel_off_ias = None
            got_liftoff = False
            liftoff_time = None
            liftoff_along = None
            liftoff_ias = None

            steps = 0
            done = False
            while not done and steps < max_steps:
                action = policy.act(obs)
                next_obs, _reward, terminated, truncated, info = env.step(action)
                policy.observe(next_obs)

                inst = np.asarray(next_obs.get("instruments", []), dtype=np.float32).reshape(-1)
                ias_mps = float(inst[0]) if inst.size >= 1 else float("nan")
                alt_agl = float(inst[3]) if inst.size >= 4 else float("nan")

                if np.isfinite(ias_mps) and np.isfinite(alt_agl):
                    if not got_wheel_off and _wheel_off_condition(
                        backend=backend,
                        alt_agl=alt_agl,
                        ias_mps=ias_mps,
                        wheel_off_alt_threshold=wheel_off_alt_threshold,
                        liftoff_speed_threshold=liftoff_speed_threshold,
                    ):
                        got_wheel_off = True
                        wheel_off_time = (steps + 1) * dt
                        wheel_off_ias = ias_mps
                        wheel_off_along = _resolve_runway_along(env, info)

                    if not got_liftoff and alt_agl >= liftoff_alt_threshold and ias_mps >= liftoff_speed_threshold:
                        got_liftoff = True
                        liftoff_time = (steps + 1) * dt
                        liftoff_ias = ias_mps
                        liftoff_along = _resolve_runway_along(env, info)

                obs = next_obs
                steps += 1
                done = bool(terminated or truncated or steps >= max_steps)

            if (
                start_along is None
                or not got_wheel_off
                or wheel_off_along is None
                or wheel_off_time is None
                or wheel_off_ias is None
                or not got_liftoff
                or liftoff_along is None
                or liftoff_time is None
                or liftoff_ias is None
            ):
                failures += 1
                continue

            wheel_off_dist_m.append(float(wheel_off_along - start_along))
            wheel_off_time_s.append(float(wheel_off_time))
            wheel_off_ias_mps.append(float(wheel_off_ias))
            liftoff_dist_m.append(float(liftoff_along - start_along))
            liftoff_time_s.append(float(liftoff_time))
            liftoff_ias_mps.append(float(liftoff_ias))

        total_eps = int(args.episodes)
        succ = total_eps - failures
        print("=" * 60)
        print(f"TAKEOFF ROLL EVAL ({_backend_summary_label(backend)})")
        _print_common_source(args, backend=backend)
        print(f"episodes:   {total_eps} (success={succ}, fail={failures})")
        print(f"seed:       {args.seed}..{args.seed + total_eps - 1}")
        print(f"action_mode:{args.action_mode}")
        print("-" * 60)
        print(format_stats("wheel_off_distance", wheel_off_dist_m, unit="m"))
        print(format_stats("wheel_off_time", wheel_off_time_s, unit="s"))
        print(format_stats("wheel_off_ias", wheel_off_ias_mps, unit="m/s"))
        print("-" * 60)
        print(format_stats("liftoff_distance", liftoff_dist_m, unit="m"))
        print(format_stats("liftoff_time", liftoff_time_s, unit="s"))
        print(format_stats("liftoff_ias", liftoff_ias_mps, unit="m/s"))
        print("=" * 60)
        return 0
    finally:
        env.close()


def _run_waypoint_nav_eval(*, backend: str, args: argparse.Namespace) -> int:
    env = make_single_world_batch_env_from_args(args)
    policy = _policy_adapter_for(task="waypoint_nav", backend=backend, args=args)

    ep_success: list[float] = []
    ep_steps: list[int] = []
    ep_rewards: list[float] = []
    ep_final_wp_idx: list[int] = []
    ep_min_dist: list[float] = []
    ep_final_dist: list[float] = []
    ep_wp_min_last: list[float] = []
    ep_wp_min_max: list[float] = []
    crashes = 0
    failures = 0

    try:
        for ep in range(int(args.episodes)):
            obs, _ = env.reset(seed=int(args.seed) + ep)
            policy.reset_episode(env, obs)

            done = False
            steps = 0
            total_rew = 0.0
            dists: list[float] = []
            last_ms = None
            waypoints, wp_min_d = make_waypoint_distance_trackers(env)

            while not done and steps < int(args.max_steps):
                action = policy.act(obs)
                next_obs, reward, terminated, truncated, info = env.step(action)
                policy.observe(next_obs)
                total_rew += float(reward)

                update_waypoint_min_distances(env, waypoints, wp_min_d)
                last_ms = update_waypoint_distance_samples(info, dists, last_ms)

                obs = next_obs
                steps += 1
                done = bool(terminated or truncated or steps >= int(args.max_steps))

            episode = finalize_waypoint_episode(last_ms=last_ms, dists=dists, wp_min_d=wp_min_d)
            success = bool(episode["success"])
            failed = bool(episode["failed"])
            wp_idx = int(episode["wp_idx"])
            dist_final = float(episode["final_dist"])

            if failed:
                failures += 1
                crashes += 1

            ep_success.append(1.0 if success else 0.0)
            ep_steps.append(int(steps))
            ep_rewards.append(float(total_rew))
            ep_final_wp_idx.append(int(wp_idx))
            ep_min_dist.append(float(episode["min_dist"]))
            ep_final_dist.append(float(episode["final_dist"]))
            ep_wp_min_last.append(float(episode["wp_min_last"]))
            ep_wp_min_max.append(float(episode["wp_min_max"]))

            print(
                f"[ep {ep + 1}/{int(args.episodes)}] success={success} failed={failed} steps={steps} "
                f"final_wp_idx={wp_idx} min_dist={ep_min_dist[-1]:.1f}m final_dist={dist_final:.1f}m "
                f"wp_min_last={ep_wp_min_last[-1]:.1f}m wp_min_max={ep_wp_min_max[-1]:.1f}m return={total_rew:.1f}"
            )

        print("=" * 60)
        print(f"WAYPOINT NAV EVAL ({_backend_summary_label(backend)})")
        _print_common_source(args, backend=backend)
        print(f"episodes:   {int(args.episodes)} seed: {int(args.seed)}..{int(args.seed) + int(args.episodes) - 1}")
        print(
            f"action_mode:{args.action_mode} include_visual={bool(args.include_visual)} "
            f"include_proprio={bool(args.include_proprio)}"
        )
        print("-" * 60)
        print(f"success_rate: {float(np.mean(ep_success)):.3f}")
        print(f"failures={failures}/{int(args.episodes)} crashes={crashes}/{int(args.episodes)}")
        print(format_stats("steps", [float(x) for x in ep_steps]))
        print(format_stats("return", ep_rewards))
        print(format_stats("final_wp_idx", [float(x) for x in ep_final_wp_idx]))
        print(format_stats("min_dist", ep_min_dist, unit="m"))
        print(format_stats("final_dist", ep_final_dist, unit="m"))
        print(format_stats("wp_min_last", ep_wp_min_last, unit="m"))
        print(format_stats("wp_min_max", ep_wp_min_max, unit="m"))
        print("=" * 60)
        return 0
    finally:
        env.close()
