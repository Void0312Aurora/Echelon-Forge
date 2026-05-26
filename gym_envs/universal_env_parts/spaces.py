from __future__ import annotations

import numpy as np

from python.mission_obs_taxonomy import mission_observation_dim as shared_mission_observation_dim

from .common import spaces

NAVAL_STATION3_ACTION_MODE = "naval_station3"
_ACTION_DIMS = {"full": 17, "takeoff2": 2, "takeoff4": 4, NAVAL_STATION3_ACTION_MODE: 3}
_FULL_ACTION_LOW = np.array(
    [-1.0, -1.0, -1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, -1.0, -1.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    dtype=np.float32,
)
_FULL_ACTION_HIGH = np.array(
    [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0],
    dtype=np.float32,
)


def expected_action_dim(action_mode: str) -> int:
    mode = str(action_mode)
    if mode not in _ACTION_DIMS:
        raise ValueError(f"Unknown action_mode: {action_mode}")
    return int(_ACTION_DIMS[mode])


def mission_observation_dim(mission_obs_mode: str) -> int:
    return int(shared_mission_observation_dim(mission_obs_mode))


def make_action_space(action_mode: str):
    if spaces is None:
        raise ModuleNotFoundError("gymnasium is required to build action spaces.")
    if action_mode == "full":
        return spaces.Box(low=_FULL_ACTION_LOW, high=_FULL_ACTION_HIGH, dtype=np.float32)
    if action_mode == "takeoff2":
        return spaces.Box(
            low=np.array([-1.0, 0.0], dtype=np.float32),
            high=np.array([1.0, 1.0], dtype=np.float32),
            dtype=np.float32,
        )
    if action_mode == "takeoff4":
        return spaces.Box(
            low=np.array([-1.0, -1.0, -1.0, 0.0], dtype=np.float32),
            high=np.array([1.0, 1.0, 1.0, 1.0], dtype=np.float32),
            dtype=np.float32,
        )
    if action_mode == NAVAL_STATION3_ACTION_MODE:
        return spaces.Box(
            low=np.array([-1.0, -1.0, -1.0], dtype=np.float32),
            high=np.array([1.0, 1.0, 1.0], dtype=np.float32),
            dtype=np.float32,
        )
    raise ValueError(f"Unknown action_mode: {action_mode}")


def make_observation_space(
    *,
    action_space,
    mission_obs_mode: str,
    include_visual: bool,
    include_proprio: bool,
    arb_height: int,
    arb_width: int,
    arb_channels: int,
    temporal_history_len: int = 1,
    obs_size: int = 42,
    max_contacts: int = 10,
    max_rwr: int = 4,
):
    if spaces is None:
        raise ModuleNotFoundError("gymnasium is required to build observation spaces.")
    mission_dim = mission_observation_dim(mission_obs_mode)
    obs_spaces = {
        "instruments": spaces.Box(low=-np.inf, high=np.inf, shape=(int(obs_size),), dtype=np.float32),
        "contacts": spaces.Box(low=-np.inf, high=np.inf, shape=(int(max_contacts), 5), dtype=np.float32),
        "rwr": spaces.Box(low=-np.inf, high=np.inf, shape=(int(max_rwr), 4), dtype=np.float32),
        "mission": spaces.Box(low=-np.inf, high=np.inf, shape=(int(mission_dim),), dtype=np.float32),
    }
    if include_proprio:
        obs_spaces["proprio"] = spaces.Box(
            low=action_space.low.astype(np.float32, copy=False),
            high=action_space.high.astype(np.float32, copy=False),
            shape=action_space.shape,
            dtype=np.float32,
        )
    history_len = max(1, int(temporal_history_len))
    if history_len > 1:
        obs_spaces["instruments_history"] = spaces.Box(
            low=-np.inf,
            high=np.inf,
            shape=(history_len, int(obs_size)),
            dtype=np.float32,
        )
        obs_spaces["contacts_history"] = spaces.Box(
            low=-np.inf,
            high=np.inf,
            shape=(history_len, int(max_contacts), 5),
            dtype=np.float32,
        )
        obs_spaces["rwr_history"] = spaces.Box(
            low=-np.inf,
            high=np.inf,
            shape=(history_len, int(max_rwr), 4),
            dtype=np.float32,
        )
        obs_spaces["mission_history"] = spaces.Box(
            low=-np.inf,
            high=np.inf,
            shape=(history_len, int(mission_dim)),
            dtype=np.float32,
        )
        obs_spaces["proprio_history"] = spaces.Box(
            low=-np.inf,
            high=np.inf,
            shape=(history_len, int(action_space.shape[0])),
            dtype=np.float32,
        )
    if include_visual:
        obs_spaces["visual"] = spaces.Box(
            low=-np.inf,
            high=np.inf,
            shape=(int(arb_height), int(arb_width), int(arb_channels)),
            dtype=np.float32,
        )
    return spaces.Dict(obs_spaces)


__all__ = [
    "expected_action_dim",
    "make_action_space",
    "make_observation_space",
    "mission_observation_dim",
]
