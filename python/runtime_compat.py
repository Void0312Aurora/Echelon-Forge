from __future__ import annotations

from typing import Any


RUNTIME_COMPAT_TRUE = {"1", "true", "on", "yes", "compat", "compatibility", "diagnostics", "debug"}
RUNTIME_COMPAT_FALSE = {"", "0", "false", "off", "no", "none", "mainline", "compiled"}


def normalize_runtime_compatibility_enabled(
    value: Any,
    *,
    option_name: str = "runtime_compatibility_enabled",
) -> bool:
    if isinstance(value, bool):
        return bool(value)
    if value is None:
        return False
    normalized = str(value).strip().lower()
    if normalized in RUNTIME_COMPAT_TRUE:
        return True
    if normalized in RUNTIME_COMPAT_FALSE:
        return False
    raise ValueError(
        f"Unknown {option_name}: {value!r}; expected an explicit true or false compatibility value."
    )


__all__ = [
    "RUNTIME_COMPAT_FALSE",
    "RUNTIME_COMPAT_TRUE",
    "normalize_runtime_compatibility_enabled",
]
