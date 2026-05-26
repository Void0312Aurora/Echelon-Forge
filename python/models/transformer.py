from __future__ import annotations

from typing import Mapping

import gymnasium as gym
import torch
import torch.nn as nn
from stable_baselines3.common.torch_layers import BaseFeaturesExtractor

from python.mission_obs_taxonomy import mission_observation_dim


_TRANSFORMER_FEATURE_CLAMP = 12.0

# Execution observation layout from `gym_envs/universal_env.py`.
_INST_IDX_IAS = 0
_INST_IDX_MACH = 1
_INST_IDX_ALT_BARO = 2
_INST_IDX_ALT_RADAR = 3
_INST_IDX_VVI = 4
_INST_IDX_AOA = 5
_INST_IDX_BETA = 6
_INST_IDX_PITCH = 7
_INST_IDX_ROLL = 8
_INST_IDX_HEADING = 9
_INST_IDX_G_LOAD = 10
_INST_IDX_G_LOAD_AXIAL = 11
_INST_IDX_P = 12
_INST_IDX_Q = 13
_INST_IDX_R = 14
_INST_IDX_ENGINE_RPM = 15
_INST_IDX_FUEL_TOTAL = 16
_INST_IDX_FUEL_FLOW = 17
_INST_IDX_GEAR_POS = 18
_INST_IDX_FLAPS_POS = 19
_INST_IDX_SPEEDBRAKE_POS = 20
_INST_IDX_CMD_HEADING = 21
_INST_IDX_CMD_ALT = 22
_INST_IDX_CMD_SPEED = 23
_INST_IDX_LAT = 24
_INST_IDX_LON = 25
_INST_IDX_VN = 26
_INST_IDX_VE = 27
_INST_IDX_VD = 28
_INST_IDX_GROUND_SPEED = 29
_INST_IDX_GROUND_TRACK = 30
_INST_IDX_WIND_SPEED = 31
_INST_IDX_WIND_DIR = 32
_INST_IDX_OAT = 33
_INST_IDX_GPS_AVAILABLE = 34
_INST_IDX_POSITION_UNCERTAINTY = 35
_INST_IDX_RWR_ACTIVE = 36
_INST_IDX_MISSILES_REMAINING = 37
_INST_IDX_ILS_LOC_DEV = 38
_INST_IDX_ILS_GS_DEV = 39
_INST_IDX_ILS_VALID = 40
_INST_IDX_ILS_DME = 41

# Cooperative takeoff mission observation layout from `gym_envs/scenario_loader.py`.
_MISSION_IDX_COMMAND_CODE = 0
_MISSION_IDX_TARGET_HEADING = 1
_MISSION_IDX_TARGET_ALTITUDE = 2
_MISSION_IDX_TARGET_SPEED = 3
_MISSION_IDX_SELECTED_STEERPOINT = 4
_MISSION_IDX_STEERPOINT_MODE_CODE = 5
_MISSION_IDX_DIST_M = 6
_MISSION_IDX_BEARING_REL_DEG = 7
_MISSION_IDX_ALTITUDE_DELTA_M = 8
_MISSION_IDX_CDI_NORM = 9
_MISSION_IDX_TRACK_ANGLE_ERROR_DEG = 10
_MISSION_IDX_LEG_DISTANCE_REMAINING_M = 11
_MISSION_IDX_NEXT_TURN_DEG = 12
_MISSION_IDX_DISTANCE_TO_TURN_M = 13
_MISSION_IDX_TAKEOFF_PROCEDURE_CODE = 14
_MISSION_IDX_TAKEOFF_CLEARANCE_CODE = 15
_MISSION_IDX_TAKEOFF_INTERVAL_S = 16
_MISSION_IDX_RUNWAY_SLOT_CODE = 17
_MISSION_IDX_FORM_OFFSET_X_M = 18
_MISSION_IDX_FORM_OFFSET_Y_M = 19
_MISSION_IDX_FORM_OFFSET_Z_M = 20
_MISSION_IDX_SELF_ROLE_CODE = 21
_MISSION_IDX_SELF_FORMATION_ROLE_CODE = 22
_MISSION_IDX_RELATIVE_SLOT_CODE = 23
_MISSION_IDX_REFERENCE_RELATIVE_SLOT_CODE = 24

_MISSION_NAVAL_SCREEN_DIM = mission_observation_dim("naval_screen_station_v1")
_MISSION_NAVAL_IDX_COMMAND_CODE = 0
_MISSION_NAVAL_IDX_TARGET_HEADING = 1
_MISSION_NAVAL_IDX_TARGET_SPEED = 2
_MISSION_NAVAL_IDX_STATION_RADIUS = 3
_MISSION_NAVAL_IDX_STATION_BEARING = 4
_MISSION_NAVAL_IDX_STATION_ERROR = 5
_MISSION_NAVAL_IDX_STATION_ERROR_NORM = 6
_MISSION_NAVAL_IDX_SCREEN_SEPARATION = 7
_MISSION_NAVAL_IDX_SCREEN_SEPARATION_ERROR = 8
_MISSION_NAVAL_IDX_OWN_REL_X = 9
_MISSION_NAVAL_IDX_OWN_REL_Y = 10
_MISSION_NAVAL_IDX_DESIRED_REL_X = 11
_MISSION_NAVAL_IDX_DESIRED_REL_Y = 12
_MISSION_NAVAL_IDX_TARGET_CONTACT_PRESENT = 13
_MISSION_NAVAL_IDX_SUPPORT_TRACK_PRESENT = 14
_MISSION_NAVAL_IDX_REPORT_CHAIN_SEEN = 15
_MISSION_NAVAL_IDX_ROE_STATE = 16
_MISSION_NAVAL_IDX_AUTHORIZATION_TO_FIRE = 17
_MISSION_NAVAL_IDX_ASSIGNED_TARGET_ID = 18
_MISSION_NAVAL_IDX_ASSIGNED_TARGET_SOURCE_ID = 19
_MISSION_NAVAL_IDX_SELF_ROLE_CODE = 20
_MISSION_NAVAL_IDX_RELATIVE_SLOT_CODE = 21
_MISSION_NAVAL_IDX_REFERENCE_RELATIVE_SLOT_CODE = 22

_CONTACT_IDX_RANGE_M = 0
_CONTACT_IDX_AZIMUTH_DEG = 1
_CONTACT_IDX_ELEVATION_DEG = 2
_CONTACT_IDX_CLOSING_SPEED_MPS = 3
_CONTACT_IDX_TIME_SINCE_UPDATE_S = 4

_RWR_IDX_BEARING_DEG = 0
_RWR_IDX_SIGNAL_STRENGTH = 1
_RWR_IDX_IS_LOCK = 2
_RWR_IDX_IS_LAUNCH = 3


def _normalize_amp_dtype(value: str | None) -> str:
    normalized = str(value or "auto").strip().lower()
    if normalized in {"auto", "fp16", "float16", "half", "bf16", "bfloat16"}:
        return "bf16" if normalized in {"bf16", "bfloat16"} else ("fp16" if normalized in {"fp16", "float16", "half"} else "auto")
    return "auto"


def _safe_scale(scale: float) -> float:
    return max(abs(float(scale)), 1.0e-6)


def _symlog(values: torch.Tensor, *, scale: float) -> torch.Tensor:
    return torch.sign(values) * torch.log1p(torch.abs(values) / _safe_scale(scale))


def _scaled(values: torch.Tensor, *, scale: float) -> torch.Tensor:
    return values / _safe_scale(scale)


def _wrap_degrees_unit(values: torch.Tensor) -> torch.Tensor:
    wrapped = torch.remainder(values + 180.0, 360.0) - 180.0
    return wrapped / 180.0


def _sanitize_features(values: torch.Tensor) -> torch.Tensor:
    return torch.clamp(torch.nan_to_num(values.float(), nan=0.0, posinf=0.0, neginf=0.0), -_TRANSFORMER_FEATURE_CLAMP, _TRANSFORMER_FEATURE_CLAMP)


def _set_last_dim(tensor: torch.Tensor, index: int, transform) -> None:
    if tensor.ndim < 1 or int(tensor.shape[-1]) <= int(index):
        return
    tensor[..., int(index)] = transform(tensor[..., int(index)])


def preprocess_instrument_tensor(instruments: torch.Tensor) -> torch.Tensor:
    out = instruments.float().clone()
    if out.ndim != 2:
        return _sanitize_features(out)

    _set_last_dim(out, _INST_IDX_IAS, lambda x: _scaled(x, scale=200.0))
    _set_last_dim(out, _INST_IDX_MACH, lambda x: _scaled(x, scale=2.0))
    _set_last_dim(out, _INST_IDX_ALT_BARO, lambda x: _symlog(x, scale=1000.0))
    _set_last_dim(out, _INST_IDX_ALT_RADAR, lambda x: _symlog(x, scale=500.0))
    _set_last_dim(out, _INST_IDX_VVI, lambda x: _scaled(x, scale=50.0))
    _set_last_dim(out, _INST_IDX_AOA, lambda x: _scaled(x, scale=45.0))
    _set_last_dim(out, _INST_IDX_BETA, lambda x: _scaled(x, scale=30.0))
    _set_last_dim(out, _INST_IDX_PITCH, _wrap_degrees_unit)
    _set_last_dim(out, _INST_IDX_ROLL, _wrap_degrees_unit)
    _set_last_dim(out, _INST_IDX_HEADING, _wrap_degrees_unit)
    _set_last_dim(out, _INST_IDX_G_LOAD, lambda x: _scaled(x, scale=10.0))
    _set_last_dim(out, _INST_IDX_G_LOAD_AXIAL, lambda x: _scaled(x, scale=10.0))
    _set_last_dim(out, _INST_IDX_P, lambda x: _scaled(x, scale=180.0))
    _set_last_dim(out, _INST_IDX_Q, lambda x: _scaled(x, scale=180.0))
    _set_last_dim(out, _INST_IDX_R, lambda x: _scaled(x, scale=180.0))
    _set_last_dim(out, _INST_IDX_ENGINE_RPM, lambda x: _scaled(x, scale=100.0))
    _set_last_dim(out, _INST_IDX_FUEL_TOTAL, lambda x: _symlog(x, scale=1000.0))
    _set_last_dim(out, _INST_IDX_FUEL_FLOW, lambda x: _symlog(x, scale=1000.0))
    _set_last_dim(out, _INST_IDX_GEAR_POS, lambda x: torch.clamp(x, -1.0, 1.0))
    _set_last_dim(out, _INST_IDX_FLAPS_POS, lambda x: torch.clamp(x, -1.0, 1.0))
    _set_last_dim(out, _INST_IDX_SPEEDBRAKE_POS, lambda x: torch.clamp(x, -1.0, 1.0))
    _set_last_dim(out, _INST_IDX_CMD_HEADING, _wrap_degrees_unit)
    _set_last_dim(out, _INST_IDX_CMD_ALT, lambda x: _symlog(x, scale=1000.0))
    _set_last_dim(out, _INST_IDX_CMD_SPEED, lambda x: _scaled(x, scale=200.0))
    _set_last_dim(out, _INST_IDX_LAT, lambda x: _scaled(x, scale=90.0))
    _set_last_dim(out, _INST_IDX_LON, lambda x: _scaled(x, scale=180.0))
    _set_last_dim(out, _INST_IDX_VN, lambda x: _scaled(x, scale=250.0))
    _set_last_dim(out, _INST_IDX_VE, lambda x: _scaled(x, scale=250.0))
    _set_last_dim(out, _INST_IDX_VD, lambda x: _scaled(x, scale=100.0))
    _set_last_dim(out, _INST_IDX_GROUND_SPEED, lambda x: _scaled(x, scale=250.0))
    _set_last_dim(out, _INST_IDX_GROUND_TRACK, _wrap_degrees_unit)
    _set_last_dim(out, _INST_IDX_WIND_SPEED, lambda x: _scaled(x, scale=100.0))
    _set_last_dim(out, _INST_IDX_WIND_DIR, _wrap_degrees_unit)
    _set_last_dim(out, _INST_IDX_OAT, lambda x: _scaled(x, scale=50.0))
    _set_last_dim(out, _INST_IDX_GPS_AVAILABLE, lambda x: torch.clamp(x, 0.0, 1.0))
    _set_last_dim(out, _INST_IDX_POSITION_UNCERTAINTY, lambda x: _symlog(x, scale=10.0))
    _set_last_dim(out, _INST_IDX_RWR_ACTIVE, lambda x: torch.clamp(x, 0.0, 1.0))
    _set_last_dim(out, _INST_IDX_MISSILES_REMAINING, lambda x: _scaled(x, scale=8.0))
    _set_last_dim(out, _INST_IDX_ILS_LOC_DEV, lambda x: torch.clamp(x, -2.0, 2.0))
    _set_last_dim(out, _INST_IDX_ILS_GS_DEV, lambda x: torch.clamp(x, -2.0, 2.0))
    _set_last_dim(out, _INST_IDX_ILS_VALID, lambda x: torch.clamp(x, 0.0, 1.0))
    _set_last_dim(out, _INST_IDX_ILS_DME, lambda x: _symlog(x, scale=1000.0))
    return _sanitize_features(out)


def preprocess_contact_tensor(contacts: torch.Tensor) -> torch.Tensor:
    out = contacts.float().clone()
    if out.ndim != 3:
        return _sanitize_features(out)

    _set_last_dim(out, _CONTACT_IDX_RANGE_M, lambda x: _symlog(x, scale=1000.0))
    _set_last_dim(out, _CONTACT_IDX_AZIMUTH_DEG, _wrap_degrees_unit)
    _set_last_dim(out, _CONTACT_IDX_ELEVATION_DEG, lambda x: _scaled(x, scale=90.0))
    _set_last_dim(out, _CONTACT_IDX_CLOSING_SPEED_MPS, lambda x: _symlog(x, scale=50.0))
    _set_last_dim(out, _CONTACT_IDX_TIME_SINCE_UPDATE_S, lambda x: _scaled(x, scale=10.0))
    return _sanitize_features(out)


def preprocess_rwr_tensor(rwr: torch.Tensor) -> torch.Tensor:
    out = rwr.float().clone()
    if out.ndim != 3:
        return _sanitize_features(out)

    _set_last_dim(out, _RWR_IDX_BEARING_DEG, _wrap_degrees_unit)
    _set_last_dim(out, _RWR_IDX_SIGNAL_STRENGTH, lambda x: torch.clamp(x, -4.0, 4.0))
    _set_last_dim(out, _RWR_IDX_IS_LOCK, lambda x: torch.clamp(x, 0.0, 1.0))
    _set_last_dim(out, _RWR_IDX_IS_LAUNCH, lambda x: torch.clamp(x, 0.0, 1.0))
    return _sanitize_features(out)


def preprocess_mission_tensor(mission: torch.Tensor) -> torch.Tensor:
    out = mission.float().clone()
    if out.ndim != 2:
        return _sanitize_features(out)
    if int(out.shape[-1]) == _MISSION_NAVAL_SCREEN_DIM:
        return preprocess_naval_screen_station_mission_tensor(out)

    _set_last_dim(out, _MISSION_IDX_COMMAND_CODE, lambda x: _scaled(x, scale=4.0))
    _set_last_dim(out, _MISSION_IDX_TARGET_HEADING, _wrap_degrees_unit)
    _set_last_dim(out, _MISSION_IDX_TARGET_ALTITUDE, lambda x: _symlog(x, scale=1000.0))
    _set_last_dim(out, _MISSION_IDX_TARGET_SPEED, lambda x: _scaled(x, scale=200.0))
    _set_last_dim(out, _MISSION_IDX_SELECTED_STEERPOINT, lambda x: _scaled(x, scale=8.0))
    _set_last_dim(out, _MISSION_IDX_STEERPOINT_MODE_CODE, lambda x: torch.clamp(x, 0.0, 1.0))
    _set_last_dim(out, _MISSION_IDX_DIST_M, lambda x: _symlog(x, scale=1000.0))
    _set_last_dim(out, _MISSION_IDX_BEARING_REL_DEG, _wrap_degrees_unit)
    _set_last_dim(out, _MISSION_IDX_ALTITUDE_DELTA_M, lambda x: _symlog(x, scale=500.0))
    _set_last_dim(out, _MISSION_IDX_CDI_NORM, lambda x: torch.clamp(x, -2.0, 2.0))
    _set_last_dim(out, _MISSION_IDX_TRACK_ANGLE_ERROR_DEG, _wrap_degrees_unit)
    _set_last_dim(out, _MISSION_IDX_LEG_DISTANCE_REMAINING_M, lambda x: _symlog(x, scale=1000.0))
    _set_last_dim(out, _MISSION_IDX_NEXT_TURN_DEG, _wrap_degrees_unit)
    _set_last_dim(out, _MISSION_IDX_DISTANCE_TO_TURN_M, lambda x: _symlog(x, scale=1000.0))
    _set_last_dim(out, _MISSION_IDX_TAKEOFF_PROCEDURE_CODE, lambda x: _scaled(x, scale=4.0))
    _set_last_dim(out, _MISSION_IDX_TAKEOFF_CLEARANCE_CODE, lambda x: _scaled(x, scale=2.0))
    _set_last_dim(out, _MISSION_IDX_TAKEOFF_INTERVAL_S, lambda x: _symlog(x, scale=10.0))
    _set_last_dim(out, _MISSION_IDX_RUNWAY_SLOT_CODE, lambda x: _scaled(x, scale=4.0))
    _set_last_dim(out, _MISSION_IDX_FORM_OFFSET_X_M, lambda x: _symlog(x, scale=100.0))
    _set_last_dim(out, _MISSION_IDX_FORM_OFFSET_Y_M, lambda x: _symlog(x, scale=100.0))
    _set_last_dim(out, _MISSION_IDX_FORM_OFFSET_Z_M, lambda x: _symlog(x, scale=50.0))
    _set_last_dim(out, _MISSION_IDX_SELF_ROLE_CODE, lambda x: _scaled(x, scale=32.0))
    _set_last_dim(out, _MISSION_IDX_SELF_FORMATION_ROLE_CODE, lambda x: _scaled(x, scale=4.0))
    _set_last_dim(out, _MISSION_IDX_RELATIVE_SLOT_CODE, lambda x: _scaled(x, scale=16.0))
    _set_last_dim(out, _MISSION_IDX_REFERENCE_RELATIVE_SLOT_CODE, lambda x: _scaled(x, scale=16.0))
    return _sanitize_features(out)


def preprocess_naval_screen_station_mission_tensor(mission: torch.Tensor) -> torch.Tensor:
    out = mission.float().clone()
    if out.ndim != 2:
        return _sanitize_features(out)

    _set_last_dim(out, _MISSION_NAVAL_IDX_COMMAND_CODE, lambda x: _scaled(x, scale=4.0))
    _set_last_dim(out, _MISSION_NAVAL_IDX_TARGET_HEADING, _wrap_degrees_unit)
    _set_last_dim(out, _MISSION_NAVAL_IDX_TARGET_SPEED, lambda x: _scaled(x, scale=25.0))
    _set_last_dim(out, _MISSION_NAVAL_IDX_STATION_RADIUS, lambda x: _symlog(x, scale=1000.0))
    _set_last_dim(out, _MISSION_NAVAL_IDX_STATION_BEARING, _wrap_degrees_unit)
    _set_last_dim(out, _MISSION_NAVAL_IDX_STATION_ERROR, lambda x: _symlog(x, scale=1000.0))
    _set_last_dim(out, _MISSION_NAVAL_IDX_STATION_ERROR_NORM, lambda x: torch.clamp(x, -4.0, 4.0))
    _set_last_dim(out, _MISSION_NAVAL_IDX_SCREEN_SEPARATION, lambda x: _symlog(x, scale=1000.0))
    _set_last_dim(out, _MISSION_NAVAL_IDX_SCREEN_SEPARATION_ERROR, lambda x: _symlog(x, scale=1000.0))
    _set_last_dim(out, _MISSION_NAVAL_IDX_OWN_REL_X, lambda x: _symlog(x, scale=1000.0))
    _set_last_dim(out, _MISSION_NAVAL_IDX_OWN_REL_Y, lambda x: _symlog(x, scale=1000.0))
    _set_last_dim(out, _MISSION_NAVAL_IDX_DESIRED_REL_X, lambda x: _symlog(x, scale=1000.0))
    _set_last_dim(out, _MISSION_NAVAL_IDX_DESIRED_REL_Y, lambda x: _symlog(x, scale=1000.0))
    _set_last_dim(out, _MISSION_NAVAL_IDX_TARGET_CONTACT_PRESENT, lambda x: torch.clamp(x, 0.0, 1.0))
    _set_last_dim(out, _MISSION_NAVAL_IDX_SUPPORT_TRACK_PRESENT, lambda x: torch.clamp(x, 0.0, 1.0))
    _set_last_dim(out, _MISSION_NAVAL_IDX_REPORT_CHAIN_SEEN, lambda x: torch.clamp(x, 0.0, 1.0))
    _set_last_dim(out, _MISSION_NAVAL_IDX_ROE_STATE, lambda x: _scaled(x, scale=4.0))
    _set_last_dim(out, _MISSION_NAVAL_IDX_AUTHORIZATION_TO_FIRE, lambda x: torch.clamp(x, 0.0, 1.0))
    _set_last_dim(out, _MISSION_NAVAL_IDX_ASSIGNED_TARGET_ID, lambda x: _symlog(x, scale=100.0))
    _set_last_dim(out, _MISSION_NAVAL_IDX_ASSIGNED_TARGET_SOURCE_ID, lambda x: _symlog(x, scale=100.0))
    _set_last_dim(out, _MISSION_NAVAL_IDX_SELF_ROLE_CODE, lambda x: _scaled(x, scale=32.0))
    _set_last_dim(out, _MISSION_NAVAL_IDX_RELATIVE_SLOT_CODE, lambda x: _scaled(x, scale=32.0))
    _set_last_dim(out, _MISSION_NAVAL_IDX_REFERENCE_RELATIVE_SLOT_CODE, lambda x: _scaled(x, scale=32.0))
    return _sanitize_features(out)


def preprocess_proprio_tensor(proprio: torch.Tensor) -> torch.Tensor:
    return _sanitize_features(proprio.float().clone())


def preprocess_visual_tensor(visual: torch.Tensor) -> torch.Tensor:
    return _sanitize_features(torch.clamp(visual.float().clone(), -10.0, 10.0))


def _preprocess_instrument_sequence(instruments: torch.Tensor) -> torch.Tensor:
    if instruments.ndim != 3:
        return _sanitize_features(instruments.float())
    b, t, d = instruments.shape
    return preprocess_instrument_tensor(instruments.reshape(b * t, d)).reshape(b, t, d)


def _preprocess_contact_sequence(contacts: torch.Tensor) -> torch.Tensor:
    if contacts.ndim != 4:
        return _sanitize_features(contacts.float())
    b, t, n, d = contacts.shape
    return preprocess_contact_tensor(contacts.reshape(b * t, n, d)).reshape(b, t, n, d)


def _preprocess_rwr_sequence(rwr: torch.Tensor) -> torch.Tensor:
    if rwr.ndim != 4:
        return _sanitize_features(rwr.float())
    b, t, n, d = rwr.shape
    return preprocess_rwr_tensor(rwr.reshape(b * t, n, d)).reshape(b, t, n, d)


def _preprocess_mission_sequence(mission: torch.Tensor) -> torch.Tensor:
    if mission.ndim != 3:
        return _sanitize_features(mission.float())
    b, t, d = mission.shape
    return preprocess_mission_tensor(mission.reshape(b * t, d)).reshape(b, t, d)


def _preprocess_proprio_sequence(proprio: torch.Tensor) -> torch.Tensor:
    return _sanitize_features(proprio.float().clone())


def preprocess_transformer_observations(observations: Mapping[str, torch.Tensor]) -> dict[str, torch.Tensor]:
    processed = {
        "instruments": preprocess_instrument_tensor(observations["instruments"]),
        "contacts": preprocess_contact_tensor(observations["contacts"]),
        "rwr": preprocess_rwr_tensor(observations["rwr"]),
        "mission": preprocess_mission_tensor(observations["mission"]),
    }
    if "proprio" in observations:
        processed["proprio"] = preprocess_proprio_tensor(observations["proprio"])
    if "visual" in observations:
        processed["visual"] = preprocess_visual_tensor(observations["visual"])
    return processed


class TransformerExtractor(BaseFeaturesExtractor):
    """
    A Transformer-based Feature Extractor for Dict Observation Spaces.
    
    It treats the observation as a sequence of tokens:
    [Instruments, Contact_1, ..., Contact_N, RWR_1, ..., RWR_M, Mission_Token]
    
    The 'Instruments' token attends to all other tokens to gather situational awareness.
    The final feature vector is the output embedding of the 'Instruments' token.
    """
    
    def __init__(
        self,
        observation_space: gym.spaces.Dict,
        features_dim: int = 128,
        n_heads: int = 4,
        n_layers: int = 2,
        use_amp: bool = False,
        amp_dtype: str = "auto",
        use_checkpointing: bool = True,
    ):
        # We don't know the exact flattened size in advance easily without calc, 
        # but supers constructor needs it.
        super().__init__(observation_space, features_dim)
        
        self.d_model = features_dim
        self.use_amp = bool(use_amp)
        self.amp_dtype = _normalize_amp_dtype(amp_dtype)
        self._use_checkpointing = bool(use_checkpointing)
        
        # 1. Input Projections
        # Read actual dimensions from observation_space
        instruments_dim = observation_space["instruments"].shape[0]
        contacts_shape = observation_space["contacts"].shape  # (N, 5)
        rwr_shape = observation_space["rwr"].shape  # (M, 4)
        mission_dim = observation_space["mission"].shape[0]
        self.has_proprio = "proprio" in observation_space.spaces
        
        self.embed_instruments = nn.Linear(instruments_dim, self.d_model)
        self.embed_contact = nn.Linear(contacts_shape[1], self.d_model)
        self.embed_rwr = nn.Linear(rwr_shape[1], self.d_model)
        self.embed_mission = nn.Linear(mission_dim, self.d_model)
        if self.has_proprio:
            proprio_dim = observation_space["proprio"].shape[0]
            self.embed_proprio = nn.Linear(proprio_dim, self.d_model)
        else:
            self.embed_proprio = None
        
        # Learnable "Type Embeddings" to distinguish token sources
        # 0=Instruments, 1=Contact, 2=RWR, 3=Mission, 4=Proprio(optional)
        self.type_embed = nn.Embedding(5 if self.has_proprio else 4, self.d_model)
        
        # Register type indices as buffers (not parameters, but move with model)
        self.register_buffer('idx_inst', torch.tensor(0))
        self.register_buffer('idx_contact', torch.tensor(1))
        self.register_buffer('idx_rwr', torch.tensor(2))
        self.register_buffer('idx_mission', torch.tensor(3))
        if self.has_proprio:
            self.register_buffer('idx_proprio', torch.tensor(4))
        
        # 2. Transformer
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=self.d_model,
            nhead=n_heads,
            dim_feedforward=self.d_model * 4,
            dropout=0.0,
            batch_first=True
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=n_layers, enable_nested_tensor=False)
        
        # 3. Output Head
        # We just use the first token (Instruments) as the summary representation
        # So no extra pooling layer needed effectively, just identity or layernorm
        self.ln_final = nn.LayerNorm(self.d_model)
        
        # Verification
        # Total tokens = 1 (Self) + 10 (Contacts) + 4 (RWR) + 1 (Mission) = 16

    def _autocast_enabled_for_forward(self) -> bool:
        return bool(torch.cuda.is_available() and self.use_amp)

    def _autocast_dtype(self) -> torch.dtype:
        if self.amp_dtype == "bf16":
            return torch.bfloat16
        if self.amp_dtype == "fp16":
            return torch.float16
        if torch.cuda.is_available() and torch.cuda.is_bf16_supported():
            return torch.bfloat16
        return torch.float16

    def forward(self, observations: dict) -> torch.Tensor:
        with torch.autocast(
            "cuda",
            enabled=self._autocast_enabled_for_forward(),
            dtype=self._autocast_dtype(),
        ):
            processed = preprocess_transformer_observations(observations)

            # 1. Get Components
            # shapes: (Batch, 24), (Batch, 10, 5), (Batch, 4, 4), (Batch, 4)
            s_inst = processed["instruments"]
            s_contacts = processed["contacts"]
            s_rwr = processed["rwr"]
            s_mission = processed["mission"]
            
            batch_size = s_inst.shape[0]
            
            # 2. Embed (using pre-registered buffer indices)
            # (B, 24) -> (B, 1, d_model)
            emb_inst = self.embed_instruments(s_inst).unsqueeze(1) + self.type_embed(self.idx_inst)
            
            # (B, 10, 5) -> (B, 10, d_model)
            emb_contacts = self.embed_contact(s_contacts) + self.type_embed(self.idx_contact)
            
            # (B, 4, 4) -> (B, 4, d_model)
            emb_rwr = self.embed_rwr(s_rwr) + self.type_embed(self.idx_rwr)
            
            # (B, 4) -> (B, 1, d_model)
            emb_mission = self.embed_mission(s_mission).unsqueeze(1) + self.type_embed(self.idx_mission)
            emb_parts = [emb_inst, emb_mission]
            if self.has_proprio:
                s_proprio = processed["proprio"]
                emb_proprio = self.embed_proprio(s_proprio).unsqueeze(1) + self.type_embed(self.idx_proprio)
                emb_parts.append(emb_proprio)
            
            # 3. Concat Sequence
            # Order: [Instruments, Mission, Proprio?, Contacts..., RWR...]
            sequence = torch.cat([*emb_parts, emb_contacts, emb_rwr], dim=1)
            
            # 4. Transform with optional gradient checkpointing
            # Masking: We could mask empty contacts/rwr if we had a valid mask. 
            # UniversalEnv pads with 0. 0-padding is a valid input for NN, though attention might check it.
            # For now, we assume all slots are potentially relevant (even 0s imply "empty/no info").
            if self._use_checkpointing and self.training:
                from torch.utils.checkpoint import checkpoint
                # Apply checkpointing to each layer individually
                x = sequence
                for layer in self.transformer.layers:
                    x = checkpoint(layer, x, use_reentrant=False)
                transformed = x
            else:
                transformed = self.transformer(sequence)
            
            # 5. Extract "Instruments" token (Index 0)
            # This token has attended to all other context
            cls_token = transformed[:, 0, :]
            
            out = self.ln_final(cls_token)
        return out.float()


class TemporalTransformerExtractor(BaseFeaturesExtractor):
    """
    Observation-window temporal extractor for Dict observation spaces.

    This is the low-intrusion Path-A extractor: the environment provides fixed
    history tensors such as `instruments_history` and `contacts_history`, this
    module encodes each frame with the same token layout as `TransformerExtractor`,
    then applies causal frame-level attention and returns the latest contextual
    frame embedding.
    """

    def __init__(
        self,
        observation_space: gym.spaces.Dict,
        features_dim: int = 128,
        n_heads: int = 4,
        n_layers: int = 2,
        temporal_n_heads: int | None = None,
        temporal_n_layers: int = 2,
        use_amp: bool = False,
        amp_dtype: str = "auto",
        use_checkpointing: bool = True,
    ):
        super().__init__(observation_space, features_dim)

        required = ("instruments_history", "contacts_history", "rwr_history", "mission_history", "proprio_history")
        missing = [key for key in required if key not in observation_space.spaces]
        if missing:
            raise ValueError(
                "TemporalTransformerExtractor requires temporal_history_len>1 observation keys; "
                f"missing={missing}"
            )

        self.d_model = int(features_dim)
        self.use_amp = bool(use_amp)
        self.amp_dtype = _normalize_amp_dtype(amp_dtype)
        self._use_checkpointing = bool(use_checkpointing)

        instruments_shape = observation_space["instruments_history"].shape
        contacts_shape = observation_space["contacts_history"].shape
        rwr_shape = observation_space["rwr_history"].shape
        mission_shape = observation_space["mission_history"].shape
        proprio_shape = observation_space["proprio_history"].shape
        self.history_len = int(instruments_shape[0])
        self.has_proprio = True

        self.embed_instruments = nn.Linear(int(instruments_shape[-1]), self.d_model)
        self.embed_contact = nn.Linear(int(contacts_shape[-1]), self.d_model)
        self.embed_rwr = nn.Linear(int(rwr_shape[-1]), self.d_model)
        self.embed_mission = nn.Linear(int(mission_shape[-1]), self.d_model)
        self.embed_proprio = nn.Linear(int(proprio_shape[-1]), self.d_model)

        # 0=Instruments, 1=Mission, 2=Proprio, 3=Contact, 4=RWR
        self.type_embed = nn.Embedding(5, self.d_model)
        self.register_buffer("idx_inst", torch.tensor(0))
        self.register_buffer("idx_mission", torch.tensor(1))
        self.register_buffer("idx_proprio", torch.tensor(2))
        self.register_buffer("idx_contact", torch.tensor(3))
        self.register_buffer("idx_rwr", torch.tensor(4))

        frame_layer = nn.TransformerEncoderLayer(
            d_model=self.d_model,
            nhead=int(n_heads),
            dim_feedforward=self.d_model * 4,
            dropout=0.0,
            batch_first=True,
        )
        self.frame_transformer = nn.TransformerEncoder(frame_layer, num_layers=int(n_layers), enable_nested_tensor=False)

        temporal_layer = nn.TransformerEncoderLayer(
            d_model=self.d_model,
            nhead=int(temporal_n_heads if temporal_n_heads is not None else n_heads),
            dim_feedforward=self.d_model * 4,
            dropout=0.0,
            batch_first=True,
        )
        self.temporal_transformer = nn.TransformerEncoder(
            temporal_layer,
            num_layers=int(temporal_n_layers),
            enable_nested_tensor=False,
        )
        self.temporal_pos_embed = nn.Parameter(torch.zeros(1, self.history_len, self.d_model))
        self.ln_final = nn.LayerNorm(self.d_model)

    def _autocast_enabled_for_forward(self) -> bool:
        return bool(torch.cuda.is_available() and self.use_amp)

    def _autocast_dtype(self) -> torch.dtype:
        if self.amp_dtype == "bf16":
            return torch.bfloat16
        if self.amp_dtype == "fp16":
            return torch.float16
        if torch.cuda.is_available() and torch.cuda.is_bf16_supported():
            return torch.bfloat16
        return torch.float16

    def _encode_frames(
        self,
        instruments: torch.Tensor,
        contacts: torch.Tensor,
        rwr: torch.Tensor,
        mission: torch.Tensor,
        proprio: torch.Tensor,
    ) -> torch.Tensor:
        b, t, _ = instruments.shape
        inst_flat = instruments.reshape(b * t, instruments.shape[-1])
        mission_flat = mission.reshape(b * t, mission.shape[-1])
        proprio_flat = proprio.reshape(b * t, proprio.shape[-1])
        contacts_flat = contacts.reshape(b * t, contacts.shape[-2], contacts.shape[-1])
        rwr_flat = rwr.reshape(b * t, rwr.shape[-2], rwr.shape[-1])

        emb_inst = self.embed_instruments(inst_flat).unsqueeze(1) + self.type_embed(self.idx_inst)
        emb_mission = self.embed_mission(mission_flat).unsqueeze(1) + self.type_embed(self.idx_mission)
        emb_proprio = self.embed_proprio(proprio_flat).unsqueeze(1) + self.type_embed(self.idx_proprio)
        emb_contacts = self.embed_contact(contacts_flat) + self.type_embed(self.idx_contact)
        emb_rwr = self.embed_rwr(rwr_flat) + self.type_embed(self.idx_rwr)

        frame_tokens = torch.cat([emb_inst, emb_mission, emb_proprio, emb_contacts, emb_rwr], dim=1)
        if self._use_checkpointing and self.training:
            from torch.utils.checkpoint import checkpoint

            x = frame_tokens
            for layer in self.frame_transformer.layers:
                x = checkpoint(layer, x, use_reentrant=False)
            frame_out = x
        else:
            frame_out = self.frame_transformer(frame_tokens)
        return frame_out[:, 0, :].reshape(b, t, self.d_model)

    def forward(self, observations: dict) -> torch.Tensor:
        with torch.autocast(
            "cuda",
            enabled=self._autocast_enabled_for_forward(),
            dtype=self._autocast_dtype(),
        ):
            instruments = _preprocess_instrument_sequence(observations["instruments_history"])
            contacts = _preprocess_contact_sequence(observations["contacts_history"])
            rwr = _preprocess_rwr_sequence(observations["rwr_history"])
            mission = _preprocess_mission_sequence(observations["mission_history"])
            proprio = _preprocess_proprio_sequence(observations["proprio_history"])

            frame_embeddings = self._encode_frames(instruments, contacts, rwr, mission, proprio)
            frame_embeddings = frame_embeddings + self.temporal_pos_embed[:, : frame_embeddings.shape[1], :]
            seq_len = int(frame_embeddings.shape[1])
            causal_mask = torch.triu(
                torch.ones((seq_len, seq_len), dtype=torch.bool, device=frame_embeddings.device),
                diagonal=1,
            )
            if self._use_checkpointing and self.training:
                from torch.utils.checkpoint import checkpoint

                x = frame_embeddings
                for layer in self.temporal_transformer.layers:
                    x = checkpoint(lambda hidden, layer=layer: layer(hidden, src_mask=causal_mask), x, use_reentrant=False)
                temporal_out = x
            else:
                temporal_out = self.temporal_transformer(frame_embeddings, mask=causal_mask)
            latest = temporal_out[:, -1, :]
            out = self.ln_final(latest)
        return out.float()


class TransformerVisualExtractor(BaseFeaturesExtractor):
    """
    Transformer features for instruments/contacts/RWR/mission + a small CNN for ARB visual.

    The visual stream is embedded as an extra token so the 'instruments' token can attend to it.
    """

    def __init__(
        self,
        observation_space: gym.spaces.Dict,
        features_dim: int = 256,
        n_heads: int = 4,
        n_layers: int = 2,
        visual_cnn_channels: int = 64,
        use_amp: bool = False,
        amp_dtype: str = "auto",
        use_checkpointing: bool = True,
    ):
        super().__init__(observation_space, features_dim)

        self.d_model = int(features_dim)
        self.use_amp = bool(use_amp)
        self.amp_dtype = _normalize_amp_dtype(amp_dtype)
        self._use_checkpointing = bool(use_checkpointing)

        instruments_dim = observation_space["instruments"].shape[0]
        contacts_shape = observation_space["contacts"].shape
        rwr_shape = observation_space["rwr"].shape
        mission_dim = observation_space["mission"].shape[0]
        self.has_proprio = "proprio" in observation_space.spaces

        self.embed_instruments = nn.Linear(instruments_dim, self.d_model)
        self.embed_contact = nn.Linear(contacts_shape[1], self.d_model)
        self.embed_rwr = nn.Linear(rwr_shape[1], self.d_model)
        self.embed_mission = nn.Linear(mission_dim, self.d_model)
        if self.has_proprio:
            proprio_dim = observation_space["proprio"].shape[0]
            self.embed_proprio = nn.Linear(proprio_dim, self.d_model)
        else:
            self.embed_proprio = None

        if "visual" not in observation_space.spaces:
            raise ValueError(
                "TransformerVisualExtractor requires an observation_space with a 'visual' key. "
                "Run env with include_visual=True."
            )

        visual_shape = observation_space["visual"].shape  # (H, W, C) from env
        if len(visual_shape) != 3:
            raise ValueError(f"Expected visual shape (H,W,C), got {visual_shape}")
        self.visual_h, self.visual_w, self.visual_c = int(visual_shape[0]), int(visual_shape[1]), int(visual_shape[2])

        c1 = int(visual_cnn_channels)
        c2 = max(32, c1)
        c3 = max(32, c1)
        if (self.visual_h, self.visual_w) == (48, 96):
            # Preserve the original native-resolution architecture so existing checkpoints remain loadable.
            self.visual_cnn = nn.Sequential(
                nn.Conv2d(self.visual_c, c1, kernel_size=8, stride=4),
                nn.ReLU(),
                nn.Conv2d(c1, c2, kernel_size=4, stride=2),
                nn.ReLU(),
                nn.Conv2d(c2, c3, kernel_size=3, stride=1),
                nn.ReLU(),
                nn.Flatten(),
            )
        else:
            layers: list[nn.Module] = []
            in_ch = self.visual_c
            cur_h = self.visual_h
            cur_w = self.visual_w
            conv_specs = ((c1, 5, 2), (c2, 3, 2), (c3, 3, 1))

            applied = 0
            for out_ch, kernel, stride in conv_specs:
                if cur_h < kernel or cur_w < kernel:
                    continue
                layers.append(nn.Conv2d(in_ch, out_ch, kernel_size=kernel, stride=stride))
                layers.append(nn.ReLU())
                cur_h = (cur_h - kernel) // stride + 1
                cur_w = (cur_w - kernel) // stride + 1
                in_ch = out_ch
                applied += 1

            if applied == 0:
                kernel = 3 if min(cur_h, cur_w) >= 3 else 1
                layers.append(nn.Conv2d(in_ch, c1, kernel_size=kernel, stride=1))
                layers.append(nn.ReLU())
                cur_h = max(1, cur_h - kernel + 1)
                cur_w = max(1, cur_w - kernel + 1)

            layers.append(nn.AdaptiveAvgPool2d((max(1, min(2, cur_h)), max(1, min(4, cur_w)))))
            layers.append(nn.Flatten())
            self.visual_cnn = nn.Sequential(*layers)

        with torch.no_grad():
            sample = torch.zeros((1, self.visual_c, self.visual_h, self.visual_w), dtype=torch.float32)
            n_flatten = int(self.visual_cnn(sample).shape[1])

        self.embed_visual = nn.Linear(n_flatten, self.d_model)

        # Type embeddings: 0=Instruments, 1=Contact, 2=RWR, 3=Mission, 4=Visual, 5=Proprio(optional)
        self.type_embed = nn.Embedding(6 if self.has_proprio else 5, self.d_model)
        self.register_buffer("idx_inst", torch.tensor(0))
        self.register_buffer("idx_contact", torch.tensor(1))
        self.register_buffer("idx_rwr", torch.tensor(2))
        self.register_buffer("idx_mission", torch.tensor(3))
        self.register_buffer("idx_visual", torch.tensor(4))
        if self.has_proprio:
            self.register_buffer("idx_proprio", torch.tensor(5))

        encoder_layer = nn.TransformerEncoderLayer(
            d_model=self.d_model,
            nhead=int(n_heads),
            dim_feedforward=self.d_model * 4,
            dropout=0.0,
            batch_first=True,
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=int(n_layers), enable_nested_tensor=False)
        self.ln_final = nn.LayerNorm(self.d_model)

    def _autocast_enabled_for_forward(self) -> bool:
        return bool(torch.cuda.is_available() and self.use_amp)

    def _autocast_dtype(self) -> torch.dtype:
        if self.amp_dtype == "bf16":
            return torch.bfloat16
        if self.amp_dtype == "fp16":
            return torch.float16
        if torch.cuda.is_available() and torch.cuda.is_bf16_supported():
            return torch.bfloat16
        return torch.float16

    def forward(self, observations: dict) -> torch.Tensor:
        with torch.autocast(
            "cuda",
            enabled=self._autocast_enabled_for_forward(),
            dtype=self._autocast_dtype(),
        ):
            processed = preprocess_transformer_observations(observations)
            s_inst = processed["instruments"]
            s_contacts = processed["contacts"]
            s_rwr = processed["rwr"]
            s_mission = processed["mission"]

            visual = processed["visual"]
            # Env provides (H,W,C); PyTorch conv expects (C,H,W).
            if visual.ndim != 4:
                raise ValueError(f"Expected visual tensor with 4 dims, got shape={tuple(visual.shape)}")
            if visual.shape[1:] == (self.visual_h, self.visual_w, self.visual_c):
                visual = visual.permute(0, 3, 1, 2)
            elif visual.shape[1:] == (self.visual_c, self.visual_h, self.visual_w):
                pass  # already channel-first
            else:
                raise ValueError(
                    f"Unexpected visual tensor shape={tuple(visual.shape)}; expected "
                    f"(B,{self.visual_h},{self.visual_w},{self.visual_c}) or (B,{self.visual_c},{self.visual_h},{self.visual_w})."
                )

            emb_inst = self.embed_instruments(s_inst).unsqueeze(1) + self.type_embed(self.idx_inst)
            emb_mission = self.embed_mission(s_mission).unsqueeze(1) + self.type_embed(self.idx_mission)

            visual_feat = self.visual_cnn(visual)
            emb_visual = self.embed_visual(visual_feat).unsqueeze(1) + self.type_embed(self.idx_visual)

            emb_contacts = self.embed_contact(s_contacts) + self.type_embed(self.idx_contact)
            emb_rwr = self.embed_rwr(s_rwr) + self.type_embed(self.idx_rwr)
            emb_parts = [emb_inst, emb_mission]
            if self.has_proprio:
                s_proprio = processed["proprio"]
                emb_proprio = self.embed_proprio(s_proprio).unsqueeze(1) + self.type_embed(self.idx_proprio)
                emb_parts.append(emb_proprio)
            sequence = torch.cat([*emb_parts, emb_visual, emb_contacts, emb_rwr], dim=1)

            if self._use_checkpointing and self.training:
                from torch.utils.checkpoint import checkpoint

                x = sequence
                for layer in self.transformer.layers:
                    x = checkpoint(layer, x, use_reentrant=False)
                transformed = x
            else:
                transformed = self.transformer(sequence)

            cls_token = transformed[:, 0, :]
            out = self.ln_final(cls_token)
        return out.float()
