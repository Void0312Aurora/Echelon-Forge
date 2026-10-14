"""Shared JSON-safe value freezing helpers."""

from __future__ import annotations

import math
from types import MappingProxyType
from typing import Any, Mapping


def describe_path(path: tuple[str, ...]) -> str:
    return ".".join(path) if path else "<root>"


def ensure_json_value(value: Any, path: tuple[str, ...] = ()) -> None:
    if isinstance(value, bool) or value is None or isinstance(value, (str, int)):
        return
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError(f"non-finite float at {describe_path(path)}: {value!r}")
        return
    if isinstance(value, Mapping):
        for key, child in value.items():
            if not isinstance(key, str) or not key:
                raise TypeError(f"mapping keys must be non-empty strings at {describe_path(path)}: {key!r}")
            ensure_json_value(child, path + (key,))
        return
    if isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            ensure_json_value(child, path + (f"[{index}]",))
        return
    raise TypeError(f"unsupported JSON value type at {describe_path(path)}: {type(value).__name__}")


def freeze_json_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({key: freeze_json_value(child) for key, child in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(freeze_json_value(child) for child in value)
    return value


def freeze_json_mapping(mapping: Mapping[str, Any]) -> Mapping[str, Any]:
    if not isinstance(mapping, Mapping):
        raise TypeError(f"expected a mapping, got {type(mapping).__name__}")
    ensure_json_value(mapping)
    return freeze_json_value(mapping)


def thaw_json_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: thaw_json_value(child) for key, child in value.items()}
    if isinstance(value, (list, tuple)):
        return [thaw_json_value(child) for child in value]
    return value
