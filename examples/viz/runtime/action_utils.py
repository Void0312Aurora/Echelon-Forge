from __future__ import annotations

from collections.abc import Iterable

import numpy as np


def normalize_fixed_action(value, *, name: str = "fixed_action") -> np.ndarray | None:
    if value is None:
        return None
    if isinstance(value, str):
        tokens = [token.strip() for token in value.split(",") if token.strip()]
        if not tokens:
            raise ValueError(f"{name} provided but empty")
        return np.asarray([float(token) for token in tokens], dtype=np.float32).reshape(-1)
    if isinstance(value, np.ndarray):
        return np.asarray(value, dtype=np.float32).reshape(-1)
    if isinstance(value, Iterable):
        return np.asarray(list(value), dtype=np.float32).reshape(-1)
    return np.asarray(value, dtype=np.float32).reshape(-1)
