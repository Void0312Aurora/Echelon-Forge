"""Simulation execution boundary shared by scripted and learned agents.

The package owns backend selection, not a physics implementation. Decision
models depend on the backend protocol and may run without importing RL; a
backend provider is loaded only when an episode is opened.
"""

from .backend import (
    SimulationBackendRegistration,
    SimulationBatchBackend,
    SimulationCooperativeBatchBackend,
    SimulationExecutionRuntime,
    create_cooperative_backend,
    create_single_backend,
    create_single_execution_runtime,
    register_backend,
    resolve_execution_wrapper_spec,
)

__all__ = [
    "SimulationBackendRegistration",
    "SimulationBatchBackend",
    "SimulationCooperativeBatchBackend",
    "SimulationExecutionRuntime",
    "create_cooperative_backend",
    "create_single_backend",
    "create_single_execution_runtime",
    "resolve_execution_wrapper_spec",
    "register_backend",
]
