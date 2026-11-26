"""Route-aware cooperative policy dispatch.

The cooperative runtime owns slot ordering and advances a shared world once per
call to ``env.step``.  This module owns only the policy-side operation: select
the model for each declared ``policy_route``, predict actions for that route's
slots, and scatter the results back into the runtime's canonical flat slot
order.  It deliberately does not implement a second environment or a second
world-step loop.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

import numpy as np


class CooperativePolicyDispatchError(ValueError):
    """Raised when route configuration or a policy output is unsafe to use."""


def _route_name(value: Any, context: str) -> str:
    route = str(value).strip()
    if not route:
        raise CooperativePolicyDispatchError(f"{context} must be a non-empty route name")
    return route


def _model_path(value: Any, context: str) -> str:
    if isinstance(value, str):
        path = value.strip()
    elif isinstance(value, Mapping):
        path = str(value.get("model_path", value.get("path", ""))).strip()
    else:
        path = ""
    if not path:
        raise CooperativePolicyDispatchError(f"{context} must declare model_path")
    return path


def resolve_cooperative_policy_models(train_config: Mapping[str, Any]) -> dict[str, str]:
    """Resolve optional route-to-model declarations from a train config.

    The maintained single-policy config remains represented by
    ``cooperative_execution.policy_route`` and the top-level ``--model``
    argument.  A multi-policy evaluation config may additionally declare:

    ``cooperative_execution.policy_models`` as either ``{route: path}`` or a
    list of ``{"route": ..., "model_path": ...}`` objects.  Empty declarations
    are rejected rather than silently falling back to a shared model.
    """

    cooperative = train_config.get("cooperative_execution", {})
    if cooperative is None:
        return {}
    if not isinstance(cooperative, Mapping):
        raise CooperativePolicyDispatchError("cooperative_execution must be an object")
    raw = cooperative.get("policy_models")
    if raw is None:
        return {}
    result: dict[str, str] = {}
    if isinstance(raw, Mapping):
        items = raw.items()
        for raw_route, raw_model in items:
            route = _route_name(raw_route, "cooperative_execution.policy_models route")
            if route in result:
                raise CooperativePolicyDispatchError(f"duplicate policy route {route!r}")
            result[route] = _model_path(raw_model, f"policy_models[{route!r}]")
        if not result:
            raise CooperativePolicyDispatchError("policy_models must not be empty")
        return result
    if isinstance(raw, list):
        if not raw:
            raise CooperativePolicyDispatchError("policy_models must not be empty")
        for index, item in enumerate(raw):
            if not isinstance(item, Mapping):
                raise CooperativePolicyDispatchError(f"policy_models[{index}] must be an object")
            route = _route_name(item.get("route"), f"policy_models[{index}].route")
            if route in result:
                raise CooperativePolicyDispatchError(f"duplicate policy route {route!r}")
            result[route] = _model_path(item, f"policy_models[{index}]")
        return result
    raise CooperativePolicyDispatchError("cooperative_execution.policy_models must be an object or list")


def _slice_observation(observation: Any, indices: list[int]) -> Any:
    """Gather a VecEnv observation in route-slot order."""

    if isinstance(observation, Mapping):
        return {key: _slice_observation(value, indices) for key, value in observation.items()}
    array = np.asarray(observation)
    if array.ndim == 0:
        raise CooperativePolicyDispatchError("observation must have a slot dimension")
    return np.asarray(array[indices])


def _scatter_action(actions: Any, indices: list[int], total_slots: int, *, route: str) -> np.ndarray:
    array = np.asarray(actions)
    if array.ndim == 0:
        if len(indices) != 1:
            raise CooperativePolicyDispatchError(
                f"policy route {route!r} returned a scalar for {len(indices)} slots"
            )
        array = array.reshape(1)
    if array.shape[0] != len(indices):
        # SB3 may return a single action vector for a one-slot route.
        if len(indices) == 1 and array.ndim >= 1 and array.shape[0] != 1:
            array = np.expand_dims(array, axis=0)
        else:
            raise CooperativePolicyDispatchError(
                f"policy route {route!r} returned {array.shape[0]} actions for {len(indices)} slots"
            )
    if not np.issubdtype(array.dtype, np.number):
        raise CooperativePolicyDispatchError(f"policy route {route!r} returned non-numeric actions")
    if not np.all(np.isfinite(array.astype(np.float64, copy=False))):
        raise CooperativePolicyDispatchError(f"policy route {route!r} returned non-finite actions")
    return array


@dataclass(frozen=True)
class CooperativeRouteLayout:
    """Validated route-to-flat-slot mapping."""

    slots_by_route: dict[str, tuple[int, ...]]
    total_slots: int

    @classmethod
    def from_env(cls, env: Any) -> "CooperativeRouteLayout":
        raw = env.slot_indices_by_policy_route()
        if not isinstance(raw, Mapping):
            raise CooperativePolicyDispatchError("environment route layout must be a mapping")
        slots_by_route: dict[str, tuple[int, ...]] = {}
        seen: set[int] = set()
        max_slot = -1
        for raw_route, raw_indices in raw.items():
            route = _route_name(raw_route, "environment policy route")
            if route in slots_by_route:
                raise CooperativePolicyDispatchError(f"duplicate environment route {route!r}")
            try:
                indices = tuple(int(index) for index in raw_indices)
            except (TypeError, ValueError) as exc:
                raise CooperativePolicyDispatchError(
                    f"environment route {route!r} has invalid slot indices"
                ) from exc
            if not indices:
                raise CooperativePolicyDispatchError(f"environment route {route!r} has no slots")
            if any(index < 0 for index in indices):
                raise CooperativePolicyDispatchError(f"environment route {route!r} has negative slot index")
            if len(set(indices)) != len(indices):
                raise CooperativePolicyDispatchError(f"environment route {route!r} repeats a slot index")
            overlap = seen.intersection(indices)
            if overlap:
                raise CooperativePolicyDispatchError(f"slot indices belong to multiple routes: {sorted(overlap)}")
            seen.update(indices)
            max_slot = max(max_slot, max(indices))
            slots_by_route[route] = indices
        if not slots_by_route:
            raise CooperativePolicyDispatchError("environment has no policy routes")
        expected = set(range(max_slot + 1))
        if seen != expected:
            missing = sorted(expected - seen)
            raise CooperativePolicyDispatchError(f"environment route layout has missing slots: {missing}")
        return cls(slots_by_route=slots_by_route, total_slots=max_slot + 1)


class CooperativeRoutePolicyDispatcher:
    """Predict route-specific actions and scatter them into flat VecEnv order."""

    def __init__(self, models: Mapping[str, Any], layout: CooperativeRouteLayout):
        if not isinstance(models, Mapping) or not models:
            raise CooperativePolicyDispatchError("at least one route model is required")
        normalized: dict[str, Any] = {}
        for raw_route, model in models.items():
            route = _route_name(raw_route, "model route")
            if model is None or not callable(getattr(model, "predict", None)):
                raise CooperativePolicyDispatchError(f"model for route {route!r} has no predict()")
            if route in normalized:
                raise CooperativePolicyDispatchError(f"duplicate model route {route!r}")
            normalized[route] = model
        expected = set(layout.slots_by_route)
        actual = set(normalized)
        if actual != expected:
            missing = sorted(expected - actual)
            extra = sorted(actual - expected)
            raise CooperativePolicyDispatchError(
                f"route model mismatch; missing={missing!r} extra={extra!r}"
            )
        self._models = normalized
        self.layout = layout

    @property
    def routes(self) -> tuple[str, ...]:
        return tuple(self.layout.slots_by_route)

    def predict_actions(self, observation: Any, *, deterministic: bool = True) -> np.ndarray:
        if isinstance(observation, Mapping):
            first_value = next(iter(observation.values()), None)
            if first_value is None:
                raise CooperativePolicyDispatchError("observation mapping is empty")
            observed_slots = int(np.asarray(first_value).shape[0])
        else:
            observed_slots = int(np.asarray(observation).shape[0])
        if observed_slots != self.layout.total_slots:
            raise CooperativePolicyDispatchError(
                f"observation has {observed_slots} slots; expected {self.layout.total_slots}"
            )

        scattered: np.ndarray | None = None
        for route, indices_tuple in self.layout.slots_by_route.items():
            indices = list(indices_tuple)
            route_obs = _slice_observation(observation, indices)
            route_actions, _state = self._models[route].predict(route_obs, deterministic=bool(deterministic))
            route_array = _scatter_action(route_actions, indices, self.layout.total_slots, route=route)
            if scattered is None:
                scattered = np.empty((self.layout.total_slots,) + route_array.shape[1:], dtype=route_array.dtype)
            elif scattered.shape[1:] != route_array.shape[1:]:
                raise CooperativePolicyDispatchError(
                    f"policy route {route!r} action shape {route_array.shape[1:]} does not match {scattered.shape[1:]}"
                )
            scattered[indices] = route_array
        assert scattered is not None
        return scattered

    def predict(self, observation: Any, *, deterministic: bool = True):
        """SB3-compatible predict result: ``(flat_actions, recurrent_state)``."""

        return self.predict_actions(observation, deterministic=deterministic), None

    def step(self, env: Any, observation: Any, *, deterministic: bool = True):
        """Predict all route actions and invoke exactly one shared env.step."""

        actions, _state = self.predict(observation, deterministic=deterministic)
        return env.step(actions)


__all__ = [
    "CooperativePolicyDispatchError",
    "CooperativeRouteLayout",
    "CooperativeRoutePolicyDispatcher",
    "resolve_cooperative_policy_models",
]
