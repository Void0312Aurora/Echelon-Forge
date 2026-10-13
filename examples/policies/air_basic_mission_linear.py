"""Explicitly loaded, untrained Policy checkpoint example for RFC238.

This module owns only its JSON coefficients and DecisionModel implementation.
Mission field order, policy admission, action projection and native execution
remain in their existing owners. Importing it registers nothing and imports no
ML framework or native runtime.
"""

from __future__ import annotations

import json
import math
from typing import Any

from python.mission_obs_taxonomy import mission_observation_field_names


SCHEMA_VERSION = "echelon_forge.example.air_basic_mission_linear.v1"


def _finite_values(values: Any, count: int) -> tuple[float, ...]:
    if not isinstance(values, (list, tuple)) or len(values) != count:
        raise ValueError("example.policy_parameter_shape_mismatch")
    if any(type(value) not in (int, float) or not math.isfinite(value) for value in values):
        raise ValueError("example.policy_parameter_nonfinite")
    return tuple(float(value) for value in values)


class BasicMissionLinearPolicy:
    """A deterministic stand-in; coefficients are untrained example parameters."""

    # Keep the legacy discriminator independent of open Policy categories.
    model_kind = "scripted"

    def __init__(self, *, weights: tuple[tuple[float, ...], ...], bias: tuple[float, ...]):
        self.weights = weights
        self.bias = bias
        self.closed = False
        self.last_context: dict[str, Any] = {}

    @classmethod
    def from_checkpoint_bytes(cls, payload: bytes, *, action_dimension: int):
        """Load JSON only after the caller's Policy checkpoint/admission gate.

        The caller obtains action_dimension from the existing action owner.
        No arbitrary classes, module imports or executable code are loaded.
        """
        document = json.loads(payload)
        if not isinstance(document, dict) or set(document) != {
            "schema_version", "observation_fields", "action_mode", "weights", "bias"
        }:
            raise ValueError("example.policy_checkpoint_fields_invalid")
        fields = mission_observation_field_names("basic")
        if document["schema_version"] != SCHEMA_VERSION:
            raise ValueError("example.policy_checkpoint_schema_invalid")
        if document["observation_fields"] != fields:
            raise ValueError("example.policy_observation_order_mismatch")
        if document["action_mode"] != "takeoff4":
            raise ValueError("example.policy_action_mode_mismatch")
        if type(action_dimension) is not int or action_dimension <= 0:
            raise ValueError("example.policy_action_dimension_invalid")
        rows = document["weights"]
        if not isinstance(rows, list) or len(rows) != action_dimension:
            raise ValueError("example.policy_parameter_shape_mismatch")
        weights = tuple(_finite_values(row, len(fields)) for row in rows)
        bias = _finite_values(document["bias"], action_dimension)
        return cls(weights=weights, bias=bias)

    def reset(self, *, context: Any) -> None:
        self.closed = False
        self.last_context = dict(context) if isinstance(context, dict) else {}

    def decide(self, *, observation: Any, context: Any, dt: float) -> tuple[float, ...]:
        if self.closed:
            raise RuntimeError("example.policy_closed")
        values = _finite_values(observation, len(mission_observation_field_names("basic")))
        self.last_context = dict(context) if isinstance(context, dict) else {}
        # Bounds, timing, mask/authority/expiry and native mutation remain in
        # PolicyRuntimeBinding and the explicitly supplied domain owners.
        return tuple(
            math.fsum(weight * value for weight, value in zip(row, values)) + offset
            for row, offset in zip(self.weights, self.bias)
        )

    def close(self) -> None:
        self.closed = True
