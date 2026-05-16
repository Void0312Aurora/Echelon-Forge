from __future__ import annotations

from typing import Any


def coerce_positive_int(raw_value: Any) -> int:
    try:
        value = int(raw_value)
    except Exception:
        return 0
    return value if value > 0 else 0


def enum_or_default(namespace: Any, raw_value: Any, default_value: Any) -> Any:
    if raw_value is None:
        return default_value
    if isinstance(raw_value, str):
        text = str(raw_value).strip()
        if not text:
            return default_value
        direct = getattr(namespace, text, None)
        if direct is not None:
            return direct
        normalized = text.replace("_", "").replace(" ", "").lower()
        for name in dir(namespace):
            if name.startswith("_"):
                continue
            if name.replace("_", "").lower() == normalized:
                return getattr(namespace, name)
        return default_value
    try:
        return namespace(int(raw_value))
    except Exception:
        pass
    try:
        return int(raw_value)
    except Exception:
        return default_value


def enum_value(raw_value: Any, default_value: int = 0) -> int:
    try:
        return int(raw_value)
    except Exception:
        return int(default_value)


def is_default_enum(raw_value: Any, default_value: Any) -> bool:
    return enum_value(raw_value) == enum_value(default_value)
