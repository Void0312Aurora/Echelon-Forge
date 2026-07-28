"""Deterministic config composition for the Experiment face.

Standard-library only. This module owns the base+delta merge semantics and
the canonical trailing-key normalization that config matrices use when they
serialize composed run configurations. It performs no IO and imports no
runtime packages.

Merge order rules (load-bearing for byte-stable generation):

1. Keys present in the base keep the base's key order, even when the delta
   overrides their values.
2. Keys introduced by the delta are appended after the base keys, in the
   delta's own key order.
3. Mapping values merge recursively with the same rules; any non-mapping
   value (including lists) is replaced wholesale by the delta.
4. ``normalize_trailing_keys`` then moves a declared set of keys to the end
   of their mapping, in declared order, so composed output matches the
   checked-in canonical key layout.
"""

from __future__ import annotations

import math
from types import MappingProxyType
from typing import Any, Mapping


def describe_path(path: tuple[str, ...]) -> str:
    return ".".join(path) if path else "<root>"


def ensure_json_value(value: Any, path: tuple[str, ...] = ()) -> None:
    """Fail fast on values that cannot round-trip through strict JSON."""
    if isinstance(value, bool) or value is None or isinstance(value, (str, int)):
        return
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError(f"non-finite float at {describe_path(path)}: {value!r}")
        return
    if isinstance(value, Mapping):
        for key, child in value.items():
            if not isinstance(key, str) or not key:
                raise TypeError(
                    f"mapping keys must be non-empty strings at {describe_path(path)}: {key!r}"
                )
            ensure_json_value(child, path + (key,))
        return
    if isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            ensure_json_value(child, path + (f"[{index}]",))
        return
    raise TypeError(
        f"unsupported JSON value type at {describe_path(path)}: {type(value).__name__}"
    )


def freeze_json_value(value: Any) -> Any:
    """Deep-freeze a JSON-safe value into read-only mappings and tuples."""
    if isinstance(value, Mapping):
        return MappingProxyType(
            {key: freeze_json_value(child) for key, child in value.items()}
        )
    if isinstance(value, (list, tuple)):
        return tuple(freeze_json_value(child) for child in value)
    return value


def freeze_json_mapping(mapping: Mapping[str, Any]) -> Mapping[str, Any]:
    """Validate and deep-freeze one JSON object; key order is preserved."""
    if not isinstance(mapping, Mapping):
        raise TypeError(f"expected a mapping, got {type(mapping).__name__}")
    ensure_json_value(mapping)
    return freeze_json_value(mapping)


def thaw_json_value(value: Any) -> Any:
    """Deep-copy a (possibly frozen) JSON-safe value into plain dicts/lists."""
    if isinstance(value, Mapping):
        return {key: thaw_json_value(child) for key, child in value.items()}
    if isinstance(value, (list, tuple)):
        return [thaw_json_value(child) for child in value]
    return value


def compose_config(base: Mapping[str, Any], delta: Mapping[str, Any]) -> dict[str, Any]:
    """Merge ``delta`` onto ``base`` with deterministic key ordering.

    Returns a fresh plain-dict tree; neither input is mutated.
    """
    if not isinstance(base, Mapping):
        raise TypeError(f"base must be a mapping, got {type(base).__name__}")
    if not isinstance(delta, Mapping):
        raise TypeError(f"delta must be a mapping, got {type(delta).__name__}")
    result: dict[str, Any] = {key: thaw_json_value(value) for key, value in base.items()}
    for key, value in delta.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, Mapping):
            result[key] = compose_config(result[key], value)
        else:
            result[key] = thaw_json_value(value)
    return result


def normalize_trailing_keys(
    config: Mapping[str, Any],
    trailing_keys: Mapping[tuple[str, ...], tuple[str, ...]],
    path: tuple[str, ...] = (),
) -> dict[str, Any]:
    """Move declared keys to the end of their mapping, in declared order.

    ``trailing_keys`` maps a mapping path (``()`` is the document root) to the
    keys that must serialize last at that path. Missing keys are skipped, so
    the operation is idempotent and delta-agnostic.
    """
    if not isinstance(config, Mapping):
        raise TypeError(f"config must be a mapping, got {type(config).__name__}")
    result: dict[str, Any] = {}
    for key, value in config.items():
        if isinstance(value, Mapping):
            result[key] = normalize_trailing_keys(value, trailing_keys, path + (key,))
        else:
            result[key] = thaw_json_value(value)
    for key in trailing_keys.get(path, ()):
        if key in result:
            result[key] = result.pop(key)
    return result
