from __future__ import annotations

from copy import deepcopy
import math
from pathlib import Path
import re
from types import SimpleNamespace

import pytest

from observation_replay_fixtures import make_observation_packet
from python.experiment.contracts import ContractError
from python.experiment import observation_replay as replay


ROOT = Path(__file__).resolve().parents[2]
REF = SimpleNamespace(world_index=0, entity_id=587)


def _digest(packet, ref=REF):
    return replay.observation_replay_digest(packet, ref, agent_id="pilot")


def _nested(kind):
    groups = {
        "TrackData": (
            replay.TRACK_FLOAT_FIELDS,
            replay.TRACK_UINT64_FIELDS,
            replay.TRACK_INT_FIELDS,
            replay.TRACK_BOOL_FIELDS,
        ),
        "RWREvent": (replay.RWR_FLOAT_FIELDS, replay.RWR_UINT64_FIELDS, (), replay.RWR_BOOL_FIELDS),
        "ESMEvent": (replay.ESM_FLOAT_FIELDS, replay.ESM_UINT64_FIELDS, (), replay.ESM_BOOL_FIELDS),
    }
    floats, uints, ints, bools = groups[kind]
    fields = {name: 0.25 for name in floats}
    fields.update({name: (1 << 64) - 1 for name in uints})
    fields.update({name: 1 for name in ints})
    fields.update({name: False for name in bools})
    return SimpleNamespace(**fields)


def _populated_packet():
    packet = make_observation_packet(REF, 3)
    observation = packet.agent_observations[0]
    observation.contacts = [_nested("TrackData")]
    observation.rwr_warnings = [_nested("RWREvent")]
    observation.esm_detections = [_nested("ESMEvent")]
    return packet


def test_native_binding_field_catalogue_cannot_silently_grow():
    bindings = ROOT / "src/interfaces/python"
    source = "\n".join(path.read_text(encoding="utf-8") for path in bindings.glob("*.cpp"))
    for kind, declared in replay.OBSERVATION_REPLAY_FIELD_CATALOGUE.items():
        bound = re.findall(rf'\.def_(?:ro|rw)\(\s*"([^"]+)",\s*&{kind}::([A-Za-z0-9_]+)\)', source)
        assert bound, f"missing native binding inventory for {kind}"
        assert all(public == member for public, member in bound)
        assert {public for public, _ in bound} == set(declared), kind
        assert len(declared) == len(set(declared)), kind
        class_start = source.index(f"nb::class_<{kind}>")
        class_body = source[class_start:].split(";", 1)[0]
        public_fields = re.findall(r'\.def_(?:ro|rw|prop_ro|prop_rw)\(\s*"([^"]+)"', class_body)
        assert set(public_fields) == set(declared), f"{kind} has an unreviewed property binding"
    provenance = re.findall(
        r'\.def_(?:ro|rw)\(\s*"([^"]+)",\s*&InformationStateSource::[A-Za-z0-9_]+\)', source
    )
    assert set(provenance) == set(replay.OBSERVATION_PROVENANCE_FIELDS)
    packet_inc = (ROOT / "src/runtime/facade/detail/batch/observation_batch_packet.inc").read_text(
        encoding="utf-8"
    )
    fields = re.findall(
        r"^EF_OBSERVATION_BATCH_PACKET_FIELD\([^,]+,\s*([A-Za-z0-9_]+),", packet_inc, re.M
    )
    assert set(fields) == set(replay.OBSERVATION_PACKET_FIELDS)


def test_declared_catalogue_is_immutable():
    with pytest.raises(TypeError):
        replay.OBSERVATION_REPLAY_FIELD_CATALOGUE["NewField"] = ()


@pytest.mark.parametrize("step", [0, 1, 19])
def test_owner_local_envelopes_and_own_handles_do_not_change_semantics(step):
    baseline = make_observation_packet(REF, step)
    child_ref = SimpleNamespace(world_index=2, entity_id=(1 << 64) - 1)
    child = make_observation_packet(child_ref, step, scope="root")
    assert baseline.snapshot_version == 1
    assert child.snapshot_version == step + 1
    assert _digest(baseline) == _digest(child, child_ref)
    baseline.provenance.observation_packet_ids = ["obs:1"]
    assert _digest(baseline) == _digest(child, child_ref)
    child.provenance.observation_packet_ids = [f"obs:facade-native-branch:{step + 1}"]
    child.provenance.source_observation_versions = [f"branch:{step + 1}"]
    assert _digest(baseline) == _digest(child, child_ref)


def test_transport_version_is_validated_locally_and_not_hashed():
    packet = _populated_packet()
    before = _digest(packet)
    packet.snapshot_version = 901
    packet.provenance.observation_packet_ids = ["obs:branch:123:901"]
    packet.provenance.source_observation_versions = ["branch:123:901"]
    assert _digest(packet) == before


@pytest.mark.parametrize("name", replay.AGENT_OBSERVATION_FLOAT_FIELDS)
def test_every_agent_float_changes_digest_without_float32_rounding(name):
    packet = _populated_packet()
    before = _digest(packet)
    observation = packet.agent_observations[0]
    value = math.nextafter(getattr(observation, name), math.inf)
    setattr(observation, name, value)
    if name == "sim_time":
        packet.source_time_s = value
    assert _digest(packet) != before


@pytest.mark.parametrize(
    "name", (*replay.AGENT_OBSERVATION_INT_FIELDS, *replay.AGENT_OBSERVATION_BOOL_FIELDS)
)
def test_every_agent_int_or_bool_changes_digest(name):
    packet = _populated_packet()
    before = _digest(packet)
    observation = packet.agent_observations[0]
    value = getattr(observation, name)
    setattr(observation, name, not value if type(value) is bool else value + 1)
    assert _digest(packet) != before


NESTED_FIELDS = tuple(
    (sequence, kind, field)
    for sequence, kind in (
        ("contacts", "TrackData"),
        ("rwr_warnings", "RWREvent"),
        ("esm_detections", "ESMEvent"),
    )
    for field in replay.OBSERVATION_REPLAY_FIELD_CATALOGUE[kind]
)


@pytest.mark.parametrize("sequence,kind,field", NESTED_FIELDS)
def test_every_nested_field_participates_in_replay(sequence, kind, field):
    packet = _populated_packet()
    before = _digest(packet)
    item = getattr(packet.agent_observations[0], sequence)[0]
    value = getattr(item, field)
    changed = not value if type(value) is bool else value - 1 if type(value) is int else value + 0.5
    setattr(item, field, changed)
    assert _digest(packet) != before, f"{kind}.{field} omitted"


@pytest.mark.parametrize(
    "sequence,kind",
    [
        ("contacts", "TrackData"),
        ("rwr_warnings", "RWREvent"),
        ("esm_detections", "ESMEvent"),
    ],
)
def test_sensor_sequence_order_is_significant(sequence, kind):
    packet = _populated_packet()
    first = _nested(kind)
    second = _nested(kind)
    id_field = "id" if kind == "TrackData" else "source_id"
    setattr(second, id_field, 10)
    setattr(packet.agent_observations[0], sequence, [first, second])
    before = _digest(packet)
    setattr(packet.agent_observations[0], sequence, [second, first])
    assert _digest(packet) != before


def test_signed_zero_remains_distinguishable():
    packet = _populated_packet()
    before = _digest(packet)
    packet.agent_observations[0].x = -0.0
    assert _digest(packet) != before


def test_snapshot_digest_is_detached_from_mutable_packet_and_repr():
    packet = _populated_packet()
    before = _digest(packet)
    copied = deepcopy(packet)
    copied.unrelated_repr_or_address = object()
    assert _digest(copied) == before
    packet.agent_observations[0].health -= 1.0
    assert _digest(copied) == before
    assert _digest(packet) != before
    assert type(before) is str and re.fullmatch(r"[0-9a-f]{64}", before)


def test_semantic_provenance_and_agent_binding_participate():
    packet = _populated_packet()
    before = _digest(packet)
    packet.provenance.diagnostics_reason = "maintained replay diagnostic"
    assert _digest(packet) != before
    assert replay.observation_replay_digest(packet, REF, agent_id="other") != _digest(packet)


@pytest.mark.parametrize(
    "target,name,value",
    [
        ("observation", "x", 1),
        ("observation", "x", True),
        ("observation", "x", float("nan")),
        ("observation", "x", float("inf")),
        ("observation", "x", "1.0"),
        ("observation", "missiles_remaining", True),
        ("observation", "missiles_remaining", 1.0),
        ("observation", "missiles_remaining", 1 << 31),
        ("observation", "missiles_remaining", -(1 << 31) - 1),
        ("observation", "can_fire", 1),
        ("observation", "contacts", iter(())),
        ("observation", "rwr_warnings", ""),
        ("observation", "esm_detections", None),
        ("packet", "source_time_s", 3),
        ("packet", "snapshot_version", True),
        ("packet", "snapshot_version", 0),
        ("packet", "snapshot_version", 1 << 64),
        ("packet", "barrier_id", "other"),
        ("packet", "agent_observations", []),
        ("packet", "refs", [REF, REF]),
        ("provenance", "information_state_layer", "WorldTruth"),
        ("provenance", "source_label", "diagnostics_oracle"),
        ("provenance", "maintained_status", "adapter_projection"),
        ("provenance", "diagnostics_reason", None),
    ],
)
def test_invalid_types_or_packet_semantics_fail_closed(target, name, value):
    packet = _populated_packet()
    destination = {
        "packet": packet,
        "observation": packet.agent_observations[0],
        "provenance": packet.provenance,
    }[target]
    setattr(destination, name, value)
    with pytest.raises(ContractError):
        _digest(packet)


@pytest.mark.parametrize(
    "packet_id,version",
    [
        ("obs:facade:2", "global:1"),
        ("obs:facade:1", "global:2"),
        ("obs:facade:01", "global:01"),
        ("obs:branch:4:1", "branch:5:1"),
        ("obs:branch:4:1", "branch:4:2"),
        ("obs:facade-native-branch:1", "global:1"),
        ("obs:1", "branch:1"),
        ("anything:1", "global:1"),
        ("obs:branch:a b:1", "branch:a b:1"),
        ("obs:branch:a:b:1", "branch:a:b:1"),
        ("obs:facade:1", "1"),
    ],
)
def test_malformed_or_inconsistent_transport_tokens_fail_closed(packet_id, version):
    packet = _populated_packet()
    packet.provenance.observation_packet_ids = [packet_id]
    packet.provenance.source_observation_versions = [version]
    with pytest.raises(ContractError, match="transport"):
        _digest(packet)


@pytest.mark.parametrize(
    "field,value",
    [
        ("observation_packet_ids", []),
        ("source_observation_versions", ["global:1", "global:1"]),
        ("observation_packet_ids", "obs:facade:1"),
        ("source_observation_versions", [1]),
    ],
)
def test_transport_token_container_requires_one_text(field, value):
    packet = _populated_packet()
    setattr(packet.provenance, field, value)
    with pytest.raises(ContractError):
        _digest(packet)


@pytest.mark.parametrize(
    "change", ["requested_world", "packet_world", "packet_id", "own_id", "bool_id", "overflow_id"]
)
def test_ref_and_own_id_are_checked_before_normalizing_agent(change):
    packet = _populated_packet()
    ref = deepcopy(REF)
    if change == "requested_world":
        ref.world_index += 1
    elif change == "packet_world":
        packet.refs[0].world_index += 1
    elif change == "packet_id":
        packet.refs[0].entity_id += 1
    elif change == "own_id":
        packet.agent_observations[0].id += 1
    elif change == "bool_id":
        packet.agent_observations[0].id = True
    else:
        ref.entity_id = 1 << 64
    with pytest.raises(ContractError):
        _digest(packet, ref)


@pytest.mark.parametrize(
    "sequence,field,value",
    [
        ("contacts", "id", True),
        ("contacts", "id", -1),
        ("rwr_warnings", "source_id", 1 << 64),
        ("esm_detections", "source_id", 1.0),
        ("contacts", "source", True),
        ("rwr_warnings", "is_lock", 1),
        ("esm_detections", "has_rf_power", 0),
        ("esm_detections", "bearing_deg", float("nan")),
    ],
)
def test_nested_types_are_strict(sequence, field, value):
    packet = _populated_packet()
    setattr(getattr(packet.agent_observations[0], sequence)[0], field, value)
    with pytest.raises(ContractError):
        _digest(packet)


def test_missing_field_or_time_mismatch_rejected():
    packet = _populated_packet()
    del packet.agent_observations[0].health
    with pytest.raises(ContractError, match="health"):
        _digest(packet)
    packet = _populated_packet()
    packet.source_time_s += 0.5
    with pytest.raises(ContractError, match="source_time_s"):
        _digest(packet)


@pytest.mark.parametrize("agent_id", ["", "Pilot", True, "pilot:one", None])
def test_invalid_agent_identifier(agent_id):
    with pytest.raises(ContractError, match="agent_id"):
        replay.observation_replay_digest(_populated_packet(), REF, agent_id=agent_id)
