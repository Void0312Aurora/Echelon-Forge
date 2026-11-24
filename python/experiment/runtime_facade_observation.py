"""Explicit Agent observation access through the maintained RuntimeFacade surface.

This module does not create a second runtime or infer entity identity. A caller
must provide the Agent-to-``WorldEntityRef`` mapping. The provider is usable by
the experiment packet bridge and by a branch owner that supplies a facade-shaped
child handle; unsupported handles fail closed.
"""

from __future__ import annotations

from typing import Callable, Mapping

from python.experiment.runtime_candidate import RuntimeCandidateError


class RuntimeFacadeAgentObservationProvider:
    """Bind explicit Agent refs to a maintained facade packet reader."""

    supports_agent_observation_refs = True

    def __init__(
        self,
        runtime: object,
        ref_factory: Callable[[object | None, str], object],
        agent_ids: tuple[str, ...],
    ) -> None:
        if not callable(ref_factory):
            raise RuntimeCandidateError("RuntimeFacade Agent ref factory must be callable")
        if (
            type(agent_ids) is not tuple
            or not agent_ids
            or any(type(agent_id) is not str or not agent_id for agent_id in agent_ids)
            or len(set(agent_ids)) != len(agent_ids)
        ):
            raise RuntimeCandidateError("RuntimeFacade Agent ids must be unique and non-empty")
        if not self._has_packet_surface(runtime):
            raise RuntimeCandidateError(
                "RuntimeFacade Agent provider requires maintained observation packet bindings"
            )
        self._runtime = runtime
        self._ref_factory = ref_factory
        self._agent_ids = agent_ids

    @staticmethod
    def _has_packet_surface(runtime: object) -> bool:
        return callable(getattr(runtime, "read_observation_packet", None)) or callable(
            getattr(runtime, "export_observation_packet", None)
        )

    @property
    def agent_ids(self) -> tuple[str, ...]:
        return self._agent_ids

    def observation_refs(self, handle: object | None = None) -> Mapping[str, object]:
        refs = {
            agent_id: self._ref_factory(handle, agent_id)
            for agent_id in self._agent_ids
        }
        if any(value is None for value in refs.values()):
            raise RuntimeCandidateError("RuntimeFacade Agent ref factory returned None")
        return refs

    def observation_packet_reader(self, handle: object | None = None) -> object:
        source = self._runtime if handle is None else handle
        if callable(getattr(source, "read_observation_packet", None)):
            return source
        if callable(getattr(source, "export_observation_packet", None)):
            return _FacadeExportPacketReader(source)
        raise RuntimeCandidateError(
            "RuntimeFacade branch has no maintained observation packet bindings"
        )


class _FacadeExportPacketReader:
    """Adapt the direct C++ facade overload to the maintained reader protocol."""

    def __init__(self, facade: object) -> None:
        self._facade = facade

    def read_observation_packet(
        self,
        refs: list[object],
        *,
        include_agent_observations: bool = True,
        include_instrument_states: bool = True,
    ) -> object:
        # Direct RuntimeFacade bindings expose the vector overload. It always
        # returns maintained Agent observations; the adapter-level request
        # flags remain available when the caller supplies RuntimeFacadeAdapter.
        del include_agent_observations, include_instrument_states
        return self._facade.export_observation_packet(refs)


__all__ = ["RuntimeFacadeAgentObservationProvider"]
