from __future__ import annotations

import json
import math
from typing import Any

from python.testing.runtime import resolve_repo_path

from ..common import ContractSkipped


def run_misc_contract(check_kind: str, spec: dict[str, Any]) -> tuple[bool, str] | None:
    if check_kind == "takeoff_safe_action_bias":
        try:
            import gymnasium as gym
            from stable_baselines3 import PPO
            from train import apply_safe_action_bias
        except ModuleNotFoundError as exc:
            raise ContractSkipped(f"optional dependency missing: {exc.name}") from exc
        import numpy as np

        class _DummyTakeoff4Env(gym.Env):
            metadata = {}

            def __init__(self):
                super().__init__()
                self.observation_space = gym.spaces.Box(low=-1.0, high=1.0, shape=(4,), dtype=np.float32)
                self.action_space = gym.spaces.Box(
                    low=np.array([-1.0, -1.0, -1.0, 0.0], dtype=np.float32),
                    high=np.array([1.0, 1.0, 1.0, 1.0], dtype=np.float32),
                    dtype=np.float32,
                )

            def reset(self, *, seed=None, options=None):
                super().reset(seed=seed)
                return np.zeros((4,), dtype=np.float32), {}

            def step(self, action):
                _ = action
                return np.zeros((4,), dtype=np.float32), 0.0, False, False, {}

        env = _DummyTakeoff4Env()
        model = PPO(
            "MlpPolicy",
            env,
            n_steps=int(spec.get("n_steps", 8)),
            batch_size=int(spec.get("batch_size", 8)),
            n_epochs=int(spec.get("n_epochs", 1)),
            learning_rate=float(spec.get("learning_rate", 3.0e-4)),
            gamma=float(spec.get("gamma", 0.99)),
            verbose=0,
        )
        scenario_path = resolve_repo_path(str(spec.get("scenario", "scenarios/takeoff/takeoff_stage1_runway45.json")))
        apply_safe_action_bias(model, str(spec.get("action_mode", "takeoff4")), scenario_path)
        bias = model.policy.action_net.bias.detach().cpu().numpy()
        if bias.shape[0] < int(spec.get("min_action_dim", 4)):
            return False, f"unexpected action bias shape {bias.shape}"
        if abs(float(bias[3]) - float(spec.get("expected_throttle_bias", 1.0))) > 1.0e-6:
            return False, f"takeoff4 throttle bias was not initialized high: {bias}"
        for idx in list(spec.get("neutral_indices", [0, 1, 2])) or []:
            if abs(float(bias[int(idx)])) > 1.0e-6:
                return False, f"takeoff4 lateral controls should start neutral: {bias}"
        return True, "takeoff safe action bias contract passed"

    if check_kind == "scripted_stable_flight_rudder_sign":
        import numpy as np
        from python.rl.control.scripted_stable_flight import ScriptedStableFlightController

        ctrl = ScriptedStableFlightController(
            action_dim=int(spec.get("action_dim", 17)),
            dt=float(spec.get("dt", 0.05)),
        )
        obs = {
            "mission": np.asarray(spec.get("mission", [3.0, 90.0, 1200.0, 210.0]), dtype=np.float32),
            "instruments": np.zeros((int(spec.get("instrument_dim", 42)),), dtype=np.float32),
        }
        obs["instruments"][int(spec.get("beta_index", 6))] = float(spec.get("beta_deg", 5.0))
        obs["instruments"][int(spec.get("yaw_rate_index", 14))] = float(spec.get("yaw_rate_dps", 10.0))
        ctrl.reset(obs)
        act = ctrl.step(obs)
        if float(act[int(spec.get("rudder_index", 2))]) <= float(spec.get("rudder_min", 0.0)):
            return False, f"expected positive rudder command for positive beta/yaw-rate, got {act}"
        return True, "scripted stable-flight rudder sign contract passed"

    if check_kind == "replay_expert_actions":
        import tempfile
        import numpy as np
        from python.world_model.replay import DatasetSpec, Episode, EpisodeDataset, EpisodeStore

        def _make_episode(*, T: int, obs_dim: int, act_dim: int, include_expert: bool) -> Any:
            rng = np.random.default_rng(0)
            obs_vec = rng.standard_normal((T + 1, obs_dim), dtype=np.float32)
            actions = rng.standard_normal((T, act_dim), dtype=np.float32)
            rewards = rng.standard_normal((T,), dtype=np.float32)
            dones = np.zeros((T,), dtype=np.bool_)
            dones[-1] = True
            expert_actions = actions + float(spec.get("expert_offset", 0.123)) if include_expert else None
            return Episode(obs_vec=obs_vec, actions=actions, rewards=rewards, dones=dones, expert_actions=expert_actions)

        with tempfile.TemporaryDirectory() as td:
            roundtrip_spec = dict(spec.get("roundtrip", {}) or {})
            ds_spec = DatasetSpec(
                action_dim=int(roundtrip_spec.get("action_dim", 3)),
                obs_vec_dim=int(roundtrip_spec.get("obs_dim", 4)),
                action_low=-np.ones((int(roundtrip_spec.get("action_dim", 3)),), dtype=np.float32),
                action_high=np.ones((int(roundtrip_spec.get("action_dim", 3)),), dtype=np.float32),
            )
            store = EpisodeStore(td, ds_spec)
            ep = _make_episode(
                T=int(roundtrip_spec.get("T", 8)),
                obs_dim=int(roundtrip_spec.get("obs_dim", 4)),
                act_dim=int(roundtrip_spec.get("action_dim", 3)),
                include_expert=True,
            )
            store.add(ep, seed=int(roundtrip_spec.get("seed", 123)))
            ds = EpisodeDataset(td)
            loaded = ds.get_episode(0)
            if loaded.expert_actions is None:
                return False, "expert_actions missing after roundtrip save/load"
            np.testing.assert_allclose(loaded.expert_actions, ep.expert_actions)
            batch = ds.sample_batch(
                batch_size=int(roundtrip_spec.get("batch_size", 2)),
                seq_len=int(roundtrip_spec.get("seq_len", 5)),
                rng=np.random.default_rng(int(roundtrip_spec.get("batch_rng_seed", 1))),
            )
            if "expert_actions" not in batch:
                return False, "expert_actions missing from sampled batch"
            if tuple(batch["expert_actions"].shape) != tuple(batch["actions"].shape):
                return False, (
                    f"expert_actions batch shape mismatch: {batch['expert_actions'].shape} "
                    f"!= {batch['actions'].shape}"
                )

        with tempfile.TemporaryDirectory() as td2:
            fallback_spec = dict(spec.get("fallback", {}) or {})
            ds_spec2 = DatasetSpec(
                action_dim=int(fallback_spec.get("action_dim", 2)),
                obs_vec_dim=int(fallback_spec.get("obs_dim", 3)),
                action_low=-np.ones((int(fallback_spec.get("action_dim", 2)),), dtype=np.float32),
                action_high=np.ones((int(fallback_spec.get("action_dim", 2)),), dtype=np.float32),
            )
            store2 = EpisodeStore(td2, ds_spec2)
            ep2 = _make_episode(
                T=int(fallback_spec.get("T", 6)),
                obs_dim=int(fallback_spec.get("obs_dim", 3)),
                act_dim=int(fallback_spec.get("action_dim", 2)),
                include_expert=False,
            )
            store2.add(ep2)
            ds2 = EpisodeDataset(td2)
            batch2 = ds2.sample_batch(
                batch_size=int(fallback_spec.get("batch_size", 1)),
                seq_len=int(fallback_spec.get("seq_len", 6)),
                rng=np.random.default_rng(int(fallback_spec.get("batch_rng_seed", 2))),
            )
            np.testing.assert_allclose(batch2["expert_actions"], batch2["actions"])
        return True, "replay expert-actions contract passed"

    if check_kind == "continuous_waypoint_template_geometry":
        def _wrap_deg_local(angle_deg: float) -> float:
            return float((float(angle_deg) + 180.0) % 360.0 - 180.0)

        def _bearing_deg(dx: float, dy: float) -> float:
            return float((math.degrees(math.atan2(float(dx), float(dy))) + 360.0) % 360.0)

        def _turn_radius_m(speed_mps: float, bank_limit_deg: float) -> float:
            bank_rad = math.radians(max(1.0, min(80.0, float(bank_limit_deg))))
            tanb = math.tan(bank_rad)
            if abs(tanb) <= 1.0e-6:
                return float("inf")
            v = max(30.0, float(speed_mps))
            return (v * v) / (9.80665 * abs(tanb))

        scenario_paths = [resolve_repo_path(str(path)) for path in list(spec.get("scenarios", []) or [])]
        if not scenario_paths:
            return False, "continuous_waypoint_template_geometry requires non-empty scenarios list"
        for path in scenario_paths:
            with open(path, "r", encoding="utf-8") as f:
                scenario = json.load(f)
            spawn = next(ent for ent in scenario["entities"] if bool(ent.get("is_agent", False)))
            spawn_x = float(spawn["pos"][0])
            spawn_y = float(spawn["pos"][1])
            bank_limit_deg = float(scenario["mission_command"]["lnav_bank_limit_deg"])
            runway_heading_deg = float(scenario["mission_command"]["post_waypoint_transition"]["target_heading"])
            templates = list(scenario["mission_command"]["randomization"]["waypoint_templates"] or [])
            for ti, route in enumerate(templates):
                points = [(spawn_x, spawn_y)] + [(float(wp["x"]), float(wp["y"])) for wp in route]
                modes = [str(wp.get("waypoint_mode", "")).strip().lower() for wp in route]
                if not modes or modes[-1] != "flyover":
                    return False, f"{os.path.basename(path)} template {ti}: final waypoint must remain flyover"
                if any(mode == "flyover" for mode in modes[-3:-1]):
                    return False, f"{os.path.basename(path)} template {ti}: late arrival bridge should not require stacked flyover fixes"
                legs = []
                for i in range(1, len(points)):
                    dx = points[i][0] - points[i - 1][0]
                    dy = points[i][1] - points[i - 1][1]
                    legs.append((math.hypot(dx, dy), _bearing_deg(dx, dy)))
                final_track = float(legs[-1][1])
                if abs(_wrap_deg_local(final_track - runway_heading_deg)) > float(spec.get("final_leg_alignment_max_deg", 15.0)):
                    return False, f"{os.path.basename(path)} template {ti}: final leg track {final_track:.1f} not aligned with runway"
                for wi in range(1, len(route)):
                    prev_leg_m, prev_track_deg = legs[wi - 1]
                    next_leg_m, next_track_deg = legs[wi]
                    turn_abs_deg = abs(_wrap_deg_local(next_track_deg - prev_track_deg))
                    if turn_abs_deg > float(spec.get("turn_abs_max_deg", 85.0)):
                        return False, f"{os.path.basename(path)} template {ti}: turn {wi} too sharp ({turn_abs_deg:.1f} deg)"
                    speed_mps = float(route[wi - 1].get("speed_mps", scenario["mission_command"]["target_speed"]))
                    radius_m = float(route[wi - 1].get("radius_m", scenario["mission_command"].get("waypoint_radius_m", 1000.0)))
                    lead_m = _turn_radius_m(speed_mps, bank_limit_deg) * math.tan(0.5 * math.radians(turn_abs_deg))
                    lead_budget_m = float(spec.get("lead_budget_leg_fraction", 0.45)) * min(prev_leg_m, next_leg_m) - max(
                        radius_m,
                        float(spec.get("lead_budget_clearance_m", 800.0)),
                    )
                    if lead_m > lead_budget_m + float(spec.get("lead_budget_tolerance_m", 1.0)):
                        return False, (
                            f"{os.path.basename(path)} template {ti}: turn {wi} lead {lead_m:.1f} exceeds budget {lead_budget_m:.1f}"
                        )
        return True, "continuous waypoint-template geometry contract passed"

    if check_kind == "landing_entity_spawn_randomization":
        import numpy as np
        from gym_envs.scenario_loader import ScenarioLoader

        loader = ScenarioLoader(None)
        loader.rng = np.random.RandomState(int(spec.get("seed", 7)))
        ent = copy.deepcopy(dict(spec.get("entity", {}) or {}))
        pos, vel, heading, pitch, roll = loader._sample_entity_spawn(ent)
        _ = pitch, roll
        if pos == ent["pos"] and vel == ent["vel"] and abs(float(heading) - float(ent.get("heading", 0.0))) < 1.0e-9:
            return False, "entity randomization did not change the spawn"
        alt_bounds = list(spec.get("altitude_offset_bounds", [-20.0, 20.0]))
        hdg_bounds = list(spec.get("heading_offset_bounds", [-5.0, 5.0]))
        sink_bounds = list(spec.get("sink_rate_bounds", [-2.0, -1.0]))
        base_alt = float(ent["pos"][2])
        base_hdg = float(ent.get("heading", 0.0))
        if not (float(alt_bounds[0]) <= float(pos[2]) - base_alt <= float(alt_bounds[1])):
            return False, "altitude offset out of configured range"
        if not (float(hdg_bounds[0]) <= float(heading) - base_hdg <= float(hdg_bounds[1])):
            return False, "heading offset out of configured range"
        if not (float(sink_bounds[0]) <= float(vel[2]) <= float(sink_bounds[1])):
            return False, "sink rate out of configured range"
        return True, "landing entity spawn randomization contract passed"

    if check_kind == "scripted_takeoff_takeoff2_throttle":
        import numpy as np
        from python.rl.control.scripted_takeoff import ScriptedTakeoffController

        ctrl = ScriptedTakeoffController(action_dim=2, dt=0.05)
        obs = {
            "instruments": np.asarray(spec["obs"]["instruments"], dtype=np.float32),
            "mission": np.asarray(spec["obs"]["mission"], dtype=np.float32),
        }
        ctrl.reset(obs)
        action = ctrl.step(obs)
        if tuple(action.shape) != (2,):
            return False, f"unexpected action shape {action.shape}"
        if abs(float(action[1]) - 1.0) > 1.0e-6:
            return False, f"takeoff2 throttle axis was modified during departure hold: {action}"
        return True, "scripted takeoff takeoff2 throttle contract passed"

    if check_kind == "scripted_takeoff_clearance_hold":
        import numpy as np
        from python.rl.control.scripted_takeoff import ScriptedTakeoffController

        ctrl = ScriptedTakeoffController(action_dim=4, dt=0.05)
        obs = {
            "instruments": np.asarray(spec["obs"]["instruments"], dtype=np.float32),
            "mission": np.asarray(spec["obs"]["mission"], dtype=np.float32),
        }
        ctrl.reset(obs)
        action = ctrl.step(obs)
        if tuple(action.shape) != (4,):
            return False, f"unexpected action shape {action.shape}"
        if abs(float(action[3])) > 1.0e-6:
            return False, f"throttle should remain idle before clearance: {action}"
        return True, "scripted takeoff clearance hold contract passed"

    if check_kind == "scripted_landing_controller":
        import numpy as np
        from python.rl.control.scripted_landing import ScriptedLandingController

        for idx, case in enumerate(list(spec.get("cases", []) or []), start=1):
            obs = {
                "mission": np.asarray(case["mission"], dtype=np.float32),
                "instruments": np.asarray(case["instruments"], dtype=np.float32),
            }
            ctrl = ScriptedLandingController(action_dim=int(spec.get("action_dim", 17)), dt=float(spec.get("dt", 0.05)))
            ctrl.reset(obs)
            action = ctrl.step(obs)
            checks = dict(case.get("checks", {}) or {})
            for action_idx_str, rule in checks.items():
                action_idx = int(action_idx_str)
                value = float(action[action_idx])
                if "gt" in rule and not (value > float(rule["gt"])):
                    return False, f"case {idx}: action[{action_idx}] expected > {rule['gt']}, got {value}"
                if "lt" in rule and not (value < float(rule["lt"])):
                    return False, f"case {idx}: action[{action_idx}] expected < {rule['lt']}, got {value}"
                if "eq" in rule and not math.isclose(value, float(rule["eq"]), rel_tol=1e-6, abs_tol=1e-6):
                    return False, f"case {idx}: action[{action_idx}] expected == {rule['eq']}, got {value}"
                if "min" in rule and not (value >= float(rule["min"])):
                    return False, f"case {idx}: action[{action_idx}] expected >= {rule['min']}, got {value}"
                if "max" in rule and not (value <= float(rule["max"])):
                    return False, f"case {idx}: action[{action_idx}] expected <= {rule['max']}, got {value}"
        return True, "scripted landing controller contract passed"

    if check_kind == "env_config_resolution":
        import argparse
        from python.env_config import resolve_env_settings

        def _make_args(**overrides):
            base = {
                "include_visual": None,
                "include_proprio": None,
                "mission_obs_mode": None,
                "visual_downsample": None,
                "visual_update_interval": None,
                "action_mode": None,
            }
            base.update(overrides)
            return argparse.Namespace(**base)

        train_config = dict(spec.get("train_config", {}) or {})
        resolved = resolve_env_settings(train_config, _make_args())
        for key, value in dict(spec.get("expected_defaults", {}) or {}).items():
            if resolved.get(key) != value:
                return False, f"expected default {key}={value!r}, got {resolved}"
        overridden = resolve_env_settings(train_config, _make_args(**dict(spec.get("overrides", {}) or {})))
        for key, value in dict(spec.get("expected_overrides", {}) or {}).items():
            if overridden.get(key) != value:
                return False, f"expected override {key}={value!r}, got {overridden}"
        return True, "env config resolution contract passed"

    if check_kind == "takeoff_curriculum_auto_gear_agl":
        try:
            import gymnasium as gym
        except ModuleNotFoundError as exc:
            raise ContractSkipped("gymnasium not installed") from exc
        import numpy as np
        from types import SimpleNamespace
        from gym_envs.universal_env import UniversalEnv

        class _StubSim:
            def __init__(self) -> None:
                self._inst = SimpleNamespace(
                    alt_baro=float(spec.get("alt_baro", 500.0)),
                    alt_radar=float(spec.get("alt_radar", 0.0)),
                    on_runway=True,
                    gear_collapsed=False,
                    gear_stress=0.0,
                )
                self.captured_action = None

            def get_instrument_state(self, _agent_id):
                return self._inst

            def set_pilot_action(self, _agent_id, pilot_action):
                self.captured_action = pilot_action

            def step(self):
                return None

            def get_time_step(self):
                return 0.05

        class _StubLoader:
            def update_behaviors(self, _t):
                return None

            def compute_full_step(self, _obs, _sim, _steps, _max_steps):
                return 0.0, False, False, [0.0, 0.0, 0.0, 0.0]

            def get_rewards_config(self):
                return {}

        env = object.__new__(UniversalEnv)
        env.action_mode = "takeoff4"
        env.action_space = gym.spaces.Box(
            low=np.array([-1.0, -1.0, -1.0, 0.0], dtype=np.float32),
            high=np.array([1.0, 1.0, 1.0, 1.0], dtype=np.float32),
            dtype=np.float32,
        )
        env.sim = _StubSim()
        env.loader = _StubLoader()
        env.agent_id = 1
        env.steps = 0
        env.max_steps = 10
        env._last_action = None
        env._last_inst = None
        env._last_truth = None
        env._get_obs = lambda: {
            "instruments": np.zeros((42,), dtype=np.float32),
            "contacts": np.zeros((10, 5), dtype=np.float32),
            "rwr": np.zeros((4, 4), dtype=np.float32),
            "mission": np.zeros((4,), dtype=np.float32),
        }
        env.step(np.array([0.0, 0.0, 0.0, 1.0], dtype=np.float32))
        pilot_action = env.sim.captured_action
        if pilot_action is None:
            return False, "pilot action was not sent to the sim"
        if abs(float(pilot_action.gear_handle) - 1.0) > 1.0e-6:
            return False, f"gear retracted on-ground when baro alt was high: gear_handle={pilot_action.gear_handle}"
        return True, "takeoff curriculum auto-gear contract passed"

    return None
