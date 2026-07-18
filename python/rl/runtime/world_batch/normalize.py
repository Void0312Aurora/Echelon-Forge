from __future__ import annotations

from gym_envs.scenario_loader import normalize_flight_shaping_backend as normalize_flight_shaping_backend_input
from python.env_config import VALID_FLIGHT_SHAPING_BACKENDS


def normalize_batch_observation_backend(value: str | None) -> str:
    backend = "auto" if value is None else str(value).strip().lower()
    if backend in ("", "auto"):
        return "auto"
    if backend in ("compiled", "gpu_host"):
        return backend
    if backend == "legacy":
        raise ValueError("batch_observation_backend='legacy' has been removed from maintained VecEnv paths")
    raise ValueError(f"Unknown batch_observation_backend: {value!r}")


def normalize_batch_visual_backend(value: str | None) -> str:
    backend = "auto" if value is None else str(value).strip().lower()
    if backend in ("", "auto"):
        return "auto"
    if backend in ("compiled", "gpu_host"):
        return backend
    if backend == "legacy":
        raise ValueError("batch_visual_backend='legacy' has been removed from maintained VecEnv paths")
    raise ValueError(f"Unknown batch_visual_backend: {value!r}")


def normalize_flight_shaping_backend(value: str | None) -> str:
    backend = "auto" if value is None else normalize_flight_shaping_backend_input(value)
    if backend in VALID_FLIGHT_SHAPING_BACKENDS:
        return backend
    if backend == "legacy":
        raise ValueError("flight_shaping_backend='legacy' has been removed from maintained VecEnv paths")
    raise ValueError(f"Unknown flight_shaping_backend: {value!r}")


def normalize_observation_return_mode(value: str | None) -> str:
    mode = "copy" if value is None else str(value).strip().lower()
    if mode in ("", "copy"):
        return "copy"
    if mode == "view":
        return "view"
    raise ValueError(f"Unknown observation_return_mode: {value!r}")


__all__ = [
    "normalize_batch_observation_backend",
    "normalize_batch_visual_backend",
    "normalize_flight_shaping_backend",
    "normalize_observation_return_mode",
]
