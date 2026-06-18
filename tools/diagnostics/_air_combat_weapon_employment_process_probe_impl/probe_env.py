"""Environment adapters for running the process probe against WorldBatchVecEnv."""

from __future__ import annotations

import argparse
from typing import Any

import numpy as np

import ef_py
from python.rl.runtime.world_batch_vec_env import WorldBatchVecEnv


def _base_env(env):
    return getattr(env, "unwrapped", env)


def _single_obs(batch_obs: dict[str, Any]) -> dict[str, Any]:
    return {
        str(key): np.asarray(value[0], dtype=np.float32, copy=True)
        for key, value in dict(batch_obs or {}).items()
    }


class _BatchSingleWorldProbeView:
    def __init__(self, vec_env: WorldBatchVecEnv):
        self._vec_env = vec_env
        self._sim_proxy = _BatchSingleWorldSimProxy(vec_env)

    @property
    def _handle(self):
        return self._vec_env.envs[0]

    @property
    def loader(self):
        return self._handle.loader

    @property
    def sim(self):
        return self._sim_proxy

    @property
    def agent_id(self):
        return self._handle.agent_id

    @property
    def steps(self):
        return self._handle.steps

    @property
    def max_steps(self):
        return self._handle.max_steps

    @property
    def action_mode(self):
        return self._vec_env.action_mode

    @property
    def mission_obs_mode(self):
        return self._vec_env.mission_obs_mode

    @property
    def _last_action(self):
        return self._handle.last_action


class _BatchSingleWorldSimProxy:
    def __init__(self, vec_env: WorldBatchVecEnv):
        self._vec_env = vec_env

    @property
    def _shim(self):
        return self._vec_env.envs[0].loader.sim

    def export_recent_engagement_events(self):
        export_packet = getattr(
            getattr(self._vec_env, "runtime_facade", None),
            "export_engagement_event_packet",
            None,
        )
        if not callable(export_packet):
            raise RuntimeError(
                "air-combat process diagnostics require RuntimeFacade.export_engagement_event_packet"
            )
        request = ef_py.EngagementBatchRequest()
        ref = ef_py.EngagementEntityRef()
        ref.world_index = 0
        ref.entity_id = int(self._vec_env.envs[0].agent_id or 0)
        request.refs = [ref]
        request.include_track_packets = True
        request.include_launch_requests = True
        request.include_launch_events = True
        request.include_munition_lifecycle_packets = True
        request.include_effects_events = True
        request.include_damage_reports = True
        request.include_diagnostics_traces = True
        return export_packet(request)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._shim, name)


class _BatchSingleWorldProbeEnv:
    def __init__(self, vec_env: WorldBatchVecEnv):
        self._vec_env = vec_env
        self._view = _BatchSingleWorldProbeView(vec_env)

    @property
    def action_space(self):
        return self._vec_env.action_space

    @property
    def observation_space(self):
        return self._vec_env.observation_space

    @property
    def unwrapped(self):
        return self._view

    def reset(self, *, seed: int | None = None):
        if seed is not None:
            self._vec_env.seed(int(seed))
        obs = self._vec_env.reset()
        info = {}
        if self._vec_env.reset_infos:
            info = dict(self._vec_env.reset_infos[0] or {})
        return _single_obs(obs), info

    def step(self, action):
        obs, rewards, dones, infos = self._vec_env.step(
            np.asarray(action, dtype=np.float32).reshape(1, -1)
        )
        info = dict(infos[0] or {})
        truncated = bool(info.get("truncated", info.get("TimeLimit.truncated", False)))
        terminated = bool(info.get("terminated", bool(dones[0]) and not truncated))
        if bool(dones[0]) and not (terminated or truncated):
            terminated = True
        return _single_obs(obs), float(rewards[0]), bool(terminated), bool(truncated), info

    def close(self) -> None:
        self._vec_env.close()


def _diagnostic_dcr_bridge_overrides(args: argparse.Namespace) -> dict[str, Any]:
    if not bool(getattr(args, "diagnostic_dcr_bridge", False)):
        return {}
    return {
        "air_combat_damage_consequence_shaping_enabled": True,
        "air_combat_target_damage_consequence_scale": float(
            getattr(args, "diagnostic_dcr_target_scale", 1.0)
        ),
        "air_combat_self_damage_consequence_scale": float(
            getattr(args, "diagnostic_dcr_self_scale", 1.0)
        ),
        "air_combat_damage_consequence_delta_clip": float(
            getattr(args, "diagnostic_dcr_delta_clip", 1.0)
        ),
    }


def _apply_diagnostic_dcr_bridge(env, overrides: dict[str, Any]) -> None:
    if not overrides:
        return
    base = _base_env(env)
    loader = getattr(base, "loader", None)
    if loader is None:
        return
    scenario_data = getattr(loader, "scenario_data", None)
    if not isinstance(scenario_data, dict):
        scenario_data = {}
        setattr(loader, "scenario_data", scenario_data)
    rewards = scenario_data.get("rewards", {})
    if not isinstance(rewards, dict):
        rewards = {}
    rewards = dict(rewards)
    rewards.update(dict(overrides))
    scenario_data["rewards"] = rewards

    compiled_rewards = getattr(loader, "_compiled_rewards_cfg", None)
    if isinstance(compiled_rewards, dict):
        next_compiled = dict(compiled_rewards)
        next_compiled.update(dict(overrides))
        setattr(loader, "_compiled_rewards_cfg", next_compiled)
