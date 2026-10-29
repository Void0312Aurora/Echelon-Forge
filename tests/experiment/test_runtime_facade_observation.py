from __future__ import annotations

from types import SimpleNamespace

import pytest

from python.experiment.numeric_observation_adapter import read_agent_observation_packet
from python.experiment.runtime_candidate import RuntimeCandidateError
from python.experiment.runtime_facade_observation import (
    RuntimeFacadeAgentObservationProvider,
)


def _packet(ref):
    return SimpleNamespace(
        refs=[SimpleNamespace(world_index=ref.world_index, entity_id=ref.entity_id)],
        agent_observations=[SimpleNamespace(speed=123.0, health=99.0)],
        provenance=SimpleNamespace(
            information_state_layer="AgentObservation",
            source_label="facade_observation_packet",
            maintained_status="maintained",
            observation_packet_ids=["obs:facade:1"],
            source_observation_versions=["facade:1"],
        ),
    )


class _MaintainedReader:
    def read_observation_packet(self, refs, **_kwargs):
        return _packet(refs[0])


class _DirectFacade:
    def export_observation_packet(self, refs):
        return _packet(refs[0])


def _ref_factory(_handle, _agent_id):
    return SimpleNamespace(world_index=0, entity_id=17)


def test_runtime_facade_provider_uses_explicit_refs_and_reader() -> None:
    provider = RuntimeFacadeAgentObservationProvider(
        _MaintainedReader(), _ref_factory, ("pilot",)
    )
    ref = provider.observation_refs()["pilot"]
    packet = read_agent_observation_packet(
        provider.observation_packet_reader(), ref, agent_id="pilot", fields=("speed",)
    )
    assert packet.values.tolist() == [123.0]
    assert packet.packet_id == "obs:facade:1"


def test_runtime_facade_provider_adapts_direct_export_binding() -> None:
    provider = RuntimeFacadeAgentObservationProvider(
        _DirectFacade(), _ref_factory, ("pilot",)
    )
    ref = provider.observation_refs()["pilot"]
    packet = read_agent_observation_packet(
        provider.observation_packet_reader(), ref, agent_id="pilot", fields=("health",)
    )
    assert packet.values.tolist() == [99.0]


def test_runtime_facade_provider_rejects_missing_surface_or_ref() -> None:
    with pytest.raises(RuntimeCandidateError, match="packet bindings"):
        RuntimeFacadeAgentObservationProvider(object(), _ref_factory, ("pilot",))
    with pytest.raises(RuntimeCandidateError, match="returned None"):
        RuntimeFacadeAgentObservationProvider(
            _MaintainedReader(), lambda _handle, _agent: None, ("pilot",)
        ).observation_refs()
