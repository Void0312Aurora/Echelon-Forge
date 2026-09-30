"""Simulation execution boundary shared by scripted and learned agents.

The package owns backend selection, not a physics implementation. Decision
models depend on the backend protocol and may run without importing RL; a
backend provider is loaded only when an episode is opened.
"""

from .backend import (
    SimulationBackendRegistration,
    SimulationBatchBackend,
    SimulationExecutionRuntime,
    create_cooperative_backend,
    create_single_backend,
    create_single_execution_runtime,
    register_backend,
)

__all__ = [
    "SimulationBackendRegistration",
    "SimulationBatchBackend",
    "SimulationExecutionRuntime",
    "create_cooperative_backend",
    "create_single_backend",
    "create_single_execution_runtime",
    "register_backend",
]
