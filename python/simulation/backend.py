"""Backend selection boundary for simulation episodes.

This module deliberately has no RL, Gym, NumPy, or native-binding import at
module load time. The existing WorldBatch implementation is one provider,
loaded lazily behind this boundary. A native or other simulation provider can
register the same construction surface without changing decision-model code.
"""

from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from typing import Any, Callable, Protocol, runtime_checkable


@runtime_checkable
class SimulationBatchBackend(Protocol):
    """Small batch-provider surface consumed by direct episode entry points."""

    def seed(self, seed: int) -> Any: ...

    def reset(self) -> Any: ...

    def step(self, actions: Any) -> Any: ...

    def close(self) -> Any: ...


@runtime_checkable
class SimulationExecutionRuntime(Protocol):
    """Single-world execution wrapper surface used by trajectory diagnostics."""

    def reset(self, *, seed: int | None = None, options: dict[str, Any] | None = None) -> Any: ...

    def step(self, action: Any) -> Any: ...

    def close(self) -> Any: ...


SingleBackendFactory = Callable[..., SimulationBatchBackend]
CooperativeBackendFactory = Callable[..., SimulationBatchBackend]
ExecutionRuntimeFactory = Callable[..., SimulationExecutionRuntime]


@dataclass(frozen=True)
class SimulationBackendRegistration:
    """Factories for one simulation provider.

    ``single_factory`` and ``cooperative_factory`` are intentionally opaque;
    their keyword arguments belong to the selected simulation provider.
    """

    backend_id: str
    single_factory: SingleBackendFactory | None = None
    cooperative_factory: CooperativeBackendFactory | None = None
    execution_factory: ExecutionRuntimeFactory | None = None

    def __post_init__(self) -> None:
        backend_id = str(self.backend_id).strip().lower()
        if not backend_id:
            raise ValueError("simulation backend_id must be non-empty")
        if self.single_factory is None and self.cooperative_factory is None and self.execution_factory is None:
            raise ValueError("simulation backend must expose at least one factory")
        object.__setattr__(self, "backend_id", backend_id)


_REGISTRATIONS: dict[str, SimulationBackendRegistration] = {}
_BUILTIN_BACKEND_ID = "world_batch"


def register_backend(registration: SimulationBackendRegistration) -> None:
    """Register one explicit simulation provider, rejecting ambiguous IDs."""

    if not isinstance(registration, SimulationBackendRegistration):
        raise TypeError("simulation backend registration has an invalid type")
    if registration.backend_id in _REGISTRATIONS:
        raise ValueError(f"simulation backend already registered: {registration.backend_id}")
    _REGISTRATIONS[registration.backend_id] = registration


def _load_builtin_backend() -> SimulationBackendRegistration:
    """Load the current WorldBatch provider only when a backend is requested."""

    single_module = import_module("python.rl.runtime.world_batch.vec_env")
    cooperative_module = import_module("python.rl.runtime.cooperative_world_batch_vec_env")
    registration = SimulationBackendRegistration(
        backend_id=_BUILTIN_BACKEND_ID,
        single_factory=getattr(single_module, "WorldBatchVecEnv", None),
        cooperative_factory=getattr(cooperative_module, "CooperativeWorldBatchVecEnv", None),
        execution_factory=getattr(
            import_module("python.rl.runtime.single_world_batch_runtime"),
            "build_single_world_batch_execution_runtime",
            None,
        ),
    )
    _REGISTRATIONS.setdefault(registration.backend_id, registration)
    return _REGISTRATIONS[registration.backend_id]


def _resolve_backend(backend_id: str) -> SimulationBackendRegistration:
    key = str(backend_id).strip().lower()
    if not key:
        raise ValueError("simulation backend_id must be non-empty")
    registration = _REGISTRATIONS.get(key)
    if registration is None and key == _BUILTIN_BACKEND_ID:
        registration = _load_builtin_backend()
    if registration is None:
        known = ", ".join(sorted(_REGISTRATIONS)) or "<none>"
        raise KeyError(f"unknown simulation backend {key!r}; registered={known}")
    return registration


def create_single_backend(*, backend_id: str = _BUILTIN_BACKEND_ID, **kwargs: Any) -> SimulationBatchBackend:
    """Construct a single-world provider without exposing its implementation path."""

    factory = _resolve_backend(backend_id).single_factory
    if factory is None:
        raise ValueError(f"simulation backend {backend_id!r} has no single-world factory")
    return factory(**kwargs)


def create_cooperative_backend(
    *, backend_id: str = _BUILTIN_BACKEND_ID, **kwargs: Any
) -> SimulationBatchBackend:
    """Construct a cooperative provider without exposing its implementation path."""

    factory = _resolve_backend(backend_id).cooperative_factory
    if factory is None:
        raise ValueError(f"simulation backend {backend_id!r} has no cooperative factory")
    return factory(**kwargs)


def create_single_execution_runtime(
    *, backend_id: str = _BUILTIN_BACKEND_ID, **kwargs: Any
) -> SimulationExecutionRuntime:
    """Construct a single-world execution wrapper through the backend seam."""

    factory = _resolve_backend(backend_id).execution_factory
    if factory is None:
        raise ValueError(f"simulation backend {backend_id!r} has no execution factory")
    return factory(**kwargs)


__all__ = [
    "SimulationBackendRegistration",
    "SimulationBatchBackend",
    "SimulationExecutionRuntime",
    "create_cooperative_backend",
    "create_single_backend",
    "create_single_execution_runtime",
    "register_backend",
]
