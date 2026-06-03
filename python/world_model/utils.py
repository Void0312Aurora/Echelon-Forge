from __future__ import annotations

import os
import random
from dataclasses import dataclass
from typing import Any

import numpy as np

_TORCH: Any | None = None
_TORCH_IMPORT_ERROR: Exception | None = None


def _load_torch() -> Any | None:
    global _TORCH, _TORCH_IMPORT_ERROR
    if _TORCH is not None:
        return _TORCH
    if _TORCH_IMPORT_ERROR is not None:
        return None
    try:
        import torch as torch_module
    except Exception as exc:  # pragma: no cover - optional dependency boundary
        _TORCH_IMPORT_ERROR = exc
        return None
    _TORCH = torch_module
    return _TORCH


def _require_torch() -> Any:
    torch_module = _load_torch()
    if torch_module is None:
        raise ModuleNotFoundError(
            "python.world_model tensor utilities require the optional dependency 'torch'. "
            "Install the world-model or train extra to use these helpers."
        ) from _TORCH_IMPORT_ERROR
    return torch_module


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch_module = _load_torch()
    if torch_module is None:
        return
    torch_module.manual_seed(seed)
    if torch_module.cuda.is_available():
        torch_module.cuda.manual_seed_all(seed)


def symlog(x: torch.Tensor) -> torch.Tensor:
    torch_module = _require_torch()
    return torch_module.sign(x) * torch_module.log1p(torch_module.abs(x))


def symexp(x: torch.Tensor) -> torch.Tensor:
    torch_module = _require_torch()
    return torch_module.sign(x) * (torch_module.expm1(torch_module.abs(x)))


@dataclass(frozen=True)
class DeviceConfig:
    device: str = "cuda"

    def torch_device(self) -> torch.device:
        torch_module = _require_torch()
        if self.device == "cuda" and not torch_module.cuda.is_available():
            return torch_module.device("cpu")
        return torch_module.device(self.device)


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)

