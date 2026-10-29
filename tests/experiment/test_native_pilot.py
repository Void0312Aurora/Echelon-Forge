from __future__ import annotations

from dataclasses import FrozenInstanceError
import json
import math

import pytest

from python.experiment.contracts import FIXED_PROTOCOL_PROVENANCE
from python.experiment.native_pilot import (
    FlightAction,
    RuntimePilotActionBackend,
    SpeedChangeEvaluator,
)
from python.experiment.native_pilot_comparison import build_trace_projection_summary
from python.experiment.native_pilot_comparison import compare_seed
from python.experiment.native_pilot_comparison import summarize_runs
from python.experiment.numeric_observation_adapter import read_agent_observation_packet
from python.experiment.runtime_candidate import RuntimeCandidateError, RuntimeCandidateSession
from python.experiment.runtime_facade_observation import RuntimeFacadeAgentObservationProvider
from python.experiment.trace import manifest_from_payload
from python.world_model.replay import EpisodeDataset


@pytest.mark.parametrize("seed", [19, 83, 191])
def test_real_controls_change_motion_and_scores_with_isolated_verified_replays(seed: int) -> None:
    ef_py = pytest.importorskip("ef_py")
    candidate_py = pytest.importorskip("ef_runtime_candidate_py")
    result = compare_seed(ef_py, candidate_py, seed)
    assert result["source_isolation_verified"]
    assert result["agent_observation_refs"]
    assert result["numeric_export"]["consumer"] == "ppo"
    assert [item["observation_count"] for item in result["numeric_export"]["episodes"]] == [21, 21]
    assert [item["transition_count"] for item in result["numeric_export"]["episodes"]] == [20, 20]
    assert all(
        item["packet_provenance"] == "facade_observation_packet"
        for item in result["numeric_export"]["episodes"]
    )
    assert result["full_minus_idle_mmps"] > 0
    idle, full = result["branches"]
    assert idle["initial_speed_mmps"] == full["initial_speed_mmps"]
    assert idle["state_digest"] != full["state_digest"]
    assert full["reward_sum_mmps"] > idle["reward_sum_mmps"]
    assert [row["replay_verified_steps"] for row in result["branches"]] == [20, 20]
    assert [row["agent_observation_ref_count"] for row in result["branches"]] == [21, 21]
    manifest = manifest_from_payload(result["manifest"])
    assert manifest.to_payload() == result["manifest"]
    assert all(
        item.observation_provenance == FIXED_PROTOCOL_PROVENANCE
        for branch in manifest.branches
        for item in branch.transitions
    )
    assert "numeric_observations" not in result
    projection = build_trace_projection_summary([result])
    assert projection["split_spec"] == {"training": [19, 83], "evaluation": [191]}
    assert set(projection["consumers"]) == {"bc", "evaluation", "ppo", "world_model"}
    assert all(item["rows"] > 0 for item in projection["consumers"].values())
    (summary,) = summarize_runs([result])
    assert "manifest" not in summary
    assert summary["manifest_digest"] == manifest.digest
    assert {key: value for key, value in summary.items() if key != "manifest_digest"} == {
        key: value for key, value in result.items() if key != "manifest"
    }


def test_native_pilot_can_persist_selected_numeric_exports(tmp_path) -> None:
    ef_py = pytest.importorskip("ef_py")
    candidate_py = pytest.importorskip("ef_runtime_candidate_py")
    result = compare_seed(
        ef_py,
        candidate_py,
        19,
        numeric_export_root=tmp_path / "exports",
    )
    export = result["numeric_export"]
    assert export["persisted"] is True
    assert export["metadata_digest"]
    dataset_root = tmp_path / "exports" / "seed-19"
    dataset = EpisodeDataset(str(dataset_root))
    assert len(dataset) == 2
    metadata = json.loads((dataset_root / "trace_projection_export.json").read_text())
    assert metadata["metadata_digest"] == export["metadata_digest"]
    assert {item["branch_digest"] for item in metadata["episodes"]} == {
        item["branch_digest"] for item in export["episodes"]
    }


@pytest.fixture
def pilot_native():
    ef_py = pytest.importorskip("ef_py")
    candidate_py = pytest.importorskip("ef_runtime_candidate_py")
    native = candidate_py.RuntimeKernelCandidate(0x50494C4F542D5445, 19, True, 19)
    assert native.start()
    request = ef_py.WorldSpawnRequest()
    request.type_name = "Aircraft"
    request.entity_name = "controlled_aircraft"
    request.z = 3000.0
    request.vx = 150.0
    entity = native.spawn_unit(request)
    assert entity
    assert native.resolve_entity("controlled_aircraft") == entity
    try:
        yield ef_py, native, entity
    finally:
        assert native.shutdown()


def _assignment(ef_py, entity: int, throttle: float = 1.0):
    action = ef_py.PilotAction()
    action.active = True
    action.throttle = throttle
    assignment = ef_py.WorldPilotActionAssignment()
    assignment.entity_id = entity
    assignment.action = action
    return assignment


def test_native_invalid_batch_does_not_apply_earlier_valid_action_or_advance(pilot_native) -> None:
    ef_py, native, entity = pilot_native
    head = native.snapshot_facts()
    valid = _assignment(ef_py, entity)
    for assignments in (
        [],
        [valid, valid],
        [valid, _assignment(ef_py, 999999)],
        [_assignment(ef_py, entity, math.nan)],
        [_assignment(ef_py, entity, 1.1)],
    ):
        assert not native.step_pilot_actions(assignments)
        after = native.snapshot_facts()
        assert (after.step, after.state_digest, after.rng_digest) == (
            head.step,
            head.state_digest,
            head.rng_digest,
        )
    assert native.step_pilot_actions([valid])
    assert native.snapshot_facts().step == head.step + 1


def test_restore_resolves_logical_entity_and_applies_controls_to_imported_aircraft(
    pilot_native,
) -> None:
    ef_py, native, source_id = pilot_native
    assert native.step_pilot_actions([_assignment(ef_py, source_id, 0)])
    source_speed = native.observation(source_id).speed
    saved = native.checkpoint_native()
    target_id = saved.resolve_entity("controlled_aircraft")
    assert target_id
    assert target_id != source_id  # This fixture exposes the source-local-ID hazard.
    assert saved.observation(target_id).speed == source_speed
    assert saved.observation(source_id) is None
    assert not saved.step_pilot_actions([_assignment(ef_py, source_id)])
    before = saved.snapshot_facts()
    assert saved.step_pilot_actions([_assignment(ef_py, target_id)])
    assert saved.snapshot_facts().step == before.step + 1
    assert saved.observation(target_id).speed != source_speed
    assert native.observation(source_id).speed == source_speed


def test_named_spawn_rejects_duplicate_before_world_mutation(pilot_native) -> None:
    ef_py, native, _ = pilot_native
    before = native.snapshot_facts()
    request = ef_py.WorldSpawnRequest()
    request.type_name = "Aircraft"
    request.entity_name = "controlled_aircraft"
    assert not native.spawn_unit(request)
    assert native.snapshot_facts().state_digest == before.state_digest


def test_protocol_binds_actions_entities_evaluator_and_provenance(pilot_native) -> None:
    ef_py, native, _ = pilot_native

    def backend(catalog):
        return RuntimePilotActionBackend(
            native,
            entity_bindings=(("pilot", "controlled_aircraft"),),
            catalog=catalog,
            evaluator=SpeedChangeEvaluator(),
            action_factory=ef_py.PilotAction,
            assignment_factory=ef_py.WorldPilotActionAssignment,
        )

    controlled = backend((("full", FlightAction(1000)),))
    different = backend((("full", FlightAction(500)),))
    assert controlled.config_digest != different.config_digest
    arguments = dict(
        session_id="pilot_protocol",
        backend_id="runtime_candidate",
        scenario_ref="scenario:pilot",
        config_digest=controlled.config_digest,
        seed=19,
        agent_ids=("pilot",),
        policy_ref="policy:fixed",
        backend=controlled,
    )
    with pytest.raises(RuntimeCandidateError, match="config digest"):
        RuntimeCandidateSession(**{**arguments, "config_digest": different.config_digest})
    with pytest.raises(RuntimeCandidateError, match="agents"):
        RuntimeCandidateSession(**{**arguments, "agent_ids": ("other",)})
    session = RuntimeCandidateSession(**arguments)
    before = session.head()
    for symbol, provenance, message in (
        ("unknown", FIXED_PROTOCOL_PROVENANCE, "unknown"),
        ("full", "facade_observation_packet", "provenance"),
    ):
        with pytest.raises(RuntimeCandidateError, match=message):
            session.step({"pilot": symbol}, observation_provenance=provenance)
        assert session.head() == before
        assert native.snapshot_facts().step == 0
    evaluator = SpeedChangeEvaluator()
    entity = native.resolve_entity("controlled_aircraft")
    speed_before = evaluator.measure(native.observation(entity))
    transition = session.step({"pilot": "full"}, observation_provenance=FIXED_PROTOCOL_PROVENANCE)
    speed_after = evaluator.measure(native.observation(entity))
    assert dict(transition.rewards)["pilot"] == speed_after - speed_before


def test_native_pilot_observation_refs_require_explicit_facade_provider(pilot_native) -> None:
    ef_py, native, _ = pilot_native
    kwargs = dict(
        native_candidate=native,
        entity_bindings=(("pilot", "controlled_aircraft"),),
        catalog=(("full", FlightAction(1000)),),
        evaluator=SpeedChangeEvaluator(),
        action_factory=ef_py.PilotAction,
        assignment_factory=ef_py.WorldPilotActionAssignment,
    )
    backend = RuntimePilotActionBackend(**kwargs)
    assert not backend.supports_agent_observation_refs
    with pytest.raises(RuntimeCandidateError, match="no RuntimeFacade Agent observation ref"):
        backend.observation_refs()
    provider_backend = RuntimePilotActionBackend(
        **kwargs,
        observation_ref_factory=lambda handle, agent_id: (handle, agent_id),
    )
    assert provider_backend.supports_agent_observation_refs
    assert provider_backend.observation_refs()["pilot"] == (None, "pilot")
    provider = RuntimeFacadeAgentObservationProvider(
        native, lambda handle, agent_id: (handle, agent_id), ("pilot",)
    )
    maintained_backend = RuntimePilotActionBackend(
        **kwargs, observation_provider=provider
    )
    assert maintained_backend.supports_agent_observation_refs
    assert maintained_backend.observation_refs()["pilot"] == (None, "pilot")
    assert maintained_backend.observation_packet_reader() is native


def test_native_candidate_and_sibling_export_agent_observation_packets(pilot_native) -> None:
    ef_py, native, entity = pilot_native
    assert native.step_pilot_actions([_assignment(ef_py, entity, 0.0)])
    ref = ef_py.WorldEntityRef()
    ref.world_index = 0
    ref.entity_id = entity
    root_packet = native.read_observation_packet([ref])
    assert root_packet.barrier_id == "export"
    assert root_packet.provenance.information_state_layer == "AgentObservation"
    assert root_packet.provenance.source_label == "facade_observation_packet"
    assert root_packet.provenance.maintained_status == "maintained"
    assert list(root_packet.provenance.observation_packet_ids)[0].startswith("obs:branch:root:")
    assert len(root_packet.agent_observations) == 1
    agent_packet = read_agent_observation_packet(
        native, ref, agent_id="pilot", fields=("speed", "health")
    )
    assert agent_packet.packet_id == list(root_packet.provenance.observation_packet_ids)[0]
    assert agent_packet.provenance == "facade_observation_packet"
    assert agent_packet.values.shape == (2,)

    checkpoint = native.checkpoint_native()
    assert checkpoint is not None
    branch = checkpoint.fork_native("a" * 64, 1)
    assert branch is not None
    branch_entity = branch.resolve_entity("controlled_aircraft")
    branch_ref = ef_py.WorldEntityRef()
    branch_ref.world_index = 0
    branch_ref.entity_id = branch_entity
    branch_packet = branch.read_observation_packet([branch_ref])
    assert list(branch_packet.provenance.observation_packet_ids)[0].startswith("obs:branch:")
    assert list(branch_packet.provenance.observation_packet_ids) != list(
        root_packet.provenance.observation_packet_ids
    )


@pytest.mark.parametrize(
    "values",
    [{"throttle": True}, {"throttle": 1001}, {"throttle": 0, "pitch": -1001}, {"throttle": 0.5}],
)
def test_flight_catalog_rejects_noncanonical_or_out_of_range_controls(values) -> None:
    with pytest.raises(RuntimeCandidateError):
        FlightAction(**values)


def test_flight_catalog_is_immutable_and_evaluator_is_explicit() -> None:
    action = FlightAction(1000)
    with pytest.raises(FrozenInstanceError):
        action.throttle = 0
    with pytest.raises(RuntimeCandidateError, match="evaluator"):
        SpeedChangeEvaluator("combat_reward")
