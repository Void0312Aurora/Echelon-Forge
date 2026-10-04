"""Backend selection boundary for simulation episodes.

This module deliberately has no RL, Gym, NumPy, or native-binding import at
module load time. The existing WorldBatch implementation is one provider,
loaded lazily behind this boundary. A native or other simulation provider can
register the same construction surface without changing decision-model code.
"""

from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from typing import Any, Callable, Mapping, Protocol, Sequence, runtime_checkable


@runtime_checkable
class SimulationBatchBackend(Protocol):
    """Small batch-provider surface consumed by direct episode entry points."""

    def seed(self, seed: int) -> Any: ...

    def reset(self) -> Any: ...

    def step(self, actions: Any) -> Any: ...

    def close(self) -> Any: ...


@runtime_checkable
class SimulationCooperativeBatchBackend(SimulationBatchBackend, Protocol):
    """Public cooperative metadata surface shared by batch providers."""

    slots_per_world: int

    def cooperative_slot_metadata(self) -> Sequence[Mapping[str, Any]]: ...


@runtime_checkable
class SimulationExecutionRuntime(Protocol):
    """Single-world execution wrapper surface used by trajectory diagnostics."""

    def reset(self, *, seed: int | None = None, options: dict[str, Any] | None = None) -> Any: ...

    def step(self, action: Any) -> Any: ...

    def close(self) -> Any: ...


SingleBackendFactory = Callable[..., SimulationBatchBackend]
CooperativeBackendFactory = Callable[..., SimulationCooperativeBatchBackend]
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
_RESERVED_BACKEND_IDS = frozenset({_BUILTIN_BACKEND_ID, "facade_batch"})


def register_backend(registration: SimulationBackendRegistration) -> None:
    """Register one explicit simulation provider, rejecting ambiguous IDs."""

    if not isinstance(registration, SimulationBackendRegistration):
        raise TypeError("simulation backend registration has an invalid type")
    if registration.backend_id in _RESERVED_BACKEND_IDS:
        raise ValueError(f"simulation backend id is reserved by the built-in provider: {registration.backend_id}")
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


def _load_facade_batch_backend() -> SimulationBackendRegistration:
    provider = import_module("python.simulation.facade_batch")
    registration = SimulationBackendRegistration(
        backend_id="facade_batch",
        single_factory=provider.FacadeBatchBackend,
        cooperative_factory=provider.FacadeBatchBackend,
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
    if registration is None and key == "facade_batch":
        registration = _load_facade_batch_backend()
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
) -> SimulationCooperativeBatchBackend:
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


def resolve_execution_wrapper_spec(
    config: Mapping[str, Any],
) -> tuple[type | None, dict[str, Any] | None]:
    """Resolve an execution wrapper through the neutral simulation boundary.

    The maintained wrapper implementation remains a provider detail. Loading it
    here keeps environment construction independent from the RL control package
    while preserving the provider's existing lazy import behavior.
    """

    provider = import_module("python.rl.control.wrappers")
    resolver = getattr(provider, "get_action_wrapper_spec")
    wrapper_class, wrapper_kwargs = resolver(config)
    return wrapper_class, wrapper_kwargs


def create_leader_window_runtime(env: Any) -> Any:
    """Create the leader-window provider selected by the active execution runtime."""

    provider = import_module("python.rl.runtime.leader_window_runtime")
    execution_runtime = getattr(env, "_exec_runtime", None)
    if bool(getattr(env, "execution_world_batch_runtime", False)) and hasattr(
        execution_runtime, "rollout_window"
    ):
        runtime_class = getattr(provider, "WorldBatchLeaderWindowRuntime")
    else:
        runtime_class = getattr(provider, "LocalLeaderWindowRuntime")
    return runtime_class(env)


def load_execution_policy(
    model_path: str,
    algo_name: str = "auto",
    device: str = "cpu",
) -> Any:
    """Load a frozen execution policy through the provider boundary."""

    from python.artifact_paths import resolve_artifact_path

    resolved_path = resolve_artifact_path(model_path) or str(model_path)
    load_path = resolved_path[:-4] if str(resolved_path).endswith(".zip") else str(resolved_path)
    algo_norm = str(algo_name or "auto").strip()
    if algo_norm in ("auto", "AdaptiveKLPPO", "PPOAdaptiveKL", "PPO_AdaptiveKL"):
        provider = import_module("python.rl.policy_algo.ppo_adaptive_kl")
        adaptive_kl = getattr(provider, "AdaptiveKLPPO")
        try:
            return adaptive_kl.load(load_path, device=device)
        except Exception:
            if algo_norm != "auto":
                raise
    stable_baselines = import_module("stable_baselines3")
    return stable_baselines.PPO.load(load_path, device=device)


def create_scenario_runtime_adapter(world_count: int = 1, **kwargs: Any) -> Any:
    """Create the scenario runtime adapter through the selected provider."""

    provider = import_module("python.rl.runtime.world_batch.adapter")
    adapter_class = getattr(provider, "RuntimeFacadeAdapter")
    return adapter_class(int(world_count), **kwargs)


__all__ = [
    "SimulationBackendRegistration",
    "SimulationBatchBackend",
    "SimulationCooperativeBatchBackend",
    "SimulationExecutionRuntime",
    "create_cooperative_backend",
    "create_single_backend",
    "create_single_execution_runtime",
    "create_leader_window_runtime",
    "create_scenario_runtime_adapter",
    "load_execution_policy",
    "resolve_execution_wrapper_spec",
    "register_backend",
]
