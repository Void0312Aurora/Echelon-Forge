from __future__ import annotations

import dataclasses

import json
from types import SimpleNamespace
import numpy as np
import pytest

from python.experiment.contracts import ContractError
from python.experiment.numeric_observation_adapter import AgentObservationPacket
from python.experiment.numeric_observation_adapter import AgentObservationSeries
from python.experiment.numeric_observation_adapter import build_numeric_exports
from python.experiment.numeric_observation_adapter import collect_agent_observation_sources
from python.experiment.numeric_observation_adapter import (
    collect_agent_observation_sources_by_branch_reader,
)
from python.experiment.numeric_observation_adapter import read_agent_observation_packet
from python.experiment.numeric_observation_adapter import read_agent_observation_series
from python.experiment.numeric_observation_adapter import write_episode_store
from python.world_model.replay import EpisodeDataset
from python.experiment.trace_projection import SeedSplit
from python.experiment.trace_projection import project_manifests
from tests.experiment.test_trace_projection import _manifest


def _projection():
    manifest = _manifest(11)
    return project_manifests(
        (manifest,),
        SeedSplit(training=(11,), evaluation=(17,)),
        consumer="ppo",
        selected_branch_digests=[trace.branch.digest for trace in manifest.branches],
    )


def _sources(projection):
    result = {}
    for branch_digest in sorted({row.branch_digest for row in projection.rows}):
        rows = [row for row in projection.rows if row.branch_digest == branch_digest]
        result[(rows[0].manifest_digest, branch_digest)] = AgentObservationSeries(
            rows[0].manifest_digest,
            branch_digest,
            "pilot",
            tuple(
                AgentObservationPacket(
                    "pilot", f"packet_{index}", "gym_envs.observation_view.v1",
                    "facade_observation_packet", values
                )
                for index, values in enumerate(
                    np.arange((len(rows) + 1) * 2, dtype=np.float32).reshape(len(rows) + 1, 2)
                )
            ),
        )
    return result


def _action(row):
    return (1.0,) if row.actions[0][1] == "full" else (0.0,)


def _reward(row):
    return float(sum(value for _, value in row.rewards))


class _PacketReader:
    def __init__(self, *, source_label="facade_observation_packet", maintained_status="maintained"):
        self.source_label = source_label
        self.maintained_status = maintained_status
        self.calls = []

    def read_observation_packet(self, refs, *, include_agent_observations, include_instrument_states):
        self.calls.append((list(refs), include_agent_observations, include_instrument_states))
        ref = refs[0]
        packet_id = f"obs:{len(self.calls)}"
        packet = SimpleNamespace(
            refs=[SimpleNamespace(world_index=ref.world_index, entity_id=ref.entity_id)],
            agent_observations=[SimpleNamespace(speed=12.5, health=0.75)],
            provenance=SimpleNamespace(
                information_state_layer="AgentObservation",
                source_label=self.source_label,
                maintained_status=self.maintained_status,
                observation_packet_ids=[packet_id],
                source_observation_versions=[f"global:{len(self.calls)}"],
            ),
        )
        return packet


def test_agent_packet_bridge_uses_facade_packet_and_preserves_identity() -> None:
    reader = _PacketReader()
    ref = SimpleNamespace(world_index=2, entity_id=17)
    packet = read_agent_observation_packet(
        reader, ref, agent_id="pilot", fields=("speed", "health")
    )
    assert packet.agent_id == "pilot"
    assert packet.packet_id == "obs:1"
    assert packet.observation_version == "global:1"
    assert packet.provenance == "facade_observation_packet"
    assert packet.values.tolist() == [12.5, 0.75]
    assert reader.calls == [([ref], True, False)]

    series = read_agent_observation_series(
        reader,
        [ref, SimpleNamespace(world_index=2, entity_id=18)],
        manifest_digest=_projection().manifest_digests[0],
        branch_digest=next(iter({row.branch_digest for row in _projection().rows})),
        agent_id="pilot",
        fields=("speed", "health"),
    )
    assert [item.packet_id for item in series.packets] == ["obs:2", "obs:3"]


def test_agent_packet_bridge_rejects_unmaintained_or_ambiguous_packets() -> None:
    ref = SimpleNamespace(world_index=0, entity_id=1)
    with pytest.raises(ContractError, match="not maintained"):
        read_agent_observation_packet(
            _PacketReader(source_label="raw_world_truth"),
            ref,
            agent_id="pilot",
            fields=("speed",),
        )
    with pytest.raises(ContractError, match="not maintained"):
        read_agent_observation_packet(
            _PacketReader(maintained_status="candidate"),
            ref,
            agent_id="pilot",
            fields=("speed",),
        )


def test_branch_ref_collector_requires_explicit_selection_and_keeps_lineage() -> None:
    projection = _projection()
    keys = sorted({(row.manifest_digest, row.branch_digest) for row in projection.rows})
    reader = _PacketReader()
    refs = {
        key: [
            SimpleNamespace(world_index=0, entity_id=index + 1)
            for index in range(2)
        ]
        for key in keys
    }
    selected = collect_agent_observation_sources(
        reader,
        {keys[0]: refs[keys[0]]},
        agent_id="pilot",
        fields=("speed", "health"),
        selected_branch_digests=[keys[0][1]],
    )
    assert set(selected) == {keys[0]}
    assert selected[keys[0]].manifest_digest == keys[0][0]
    assert selected[keys[0]].branch_digest == keys[0][1]
    with pytest.raises(ContractError, match="identify ref sequences"):
        collect_agent_observation_sources(
            reader,
            {keys[0]: refs[keys[0]]},
            agent_id="pilot",
            fields=("speed",),
            selected_branch_digests=[keys[0][1], keys[1][1]],
        )


def test_branch_reader_collector_keeps_reader_bound_to_selected_branch() -> None:
    projection = _projection()
    keys = sorted({(row.manifest_digest, row.branch_digest) for row in projection.rows})
    readers = {
        key: (
            _PacketReader(),
            [SimpleNamespace(world_index=0, entity_id=index + 1) for index in range(2)],
        )
        for key in keys
    }
    selected = collect_agent_observation_sources_by_branch_reader(
        readers,
        agent_id="pilot",
        fields=("speed",),
        selected_branch_digests=[key[1] for key in keys],
    )
    assert set(selected) == set(keys)
    assert all(series.values.shape == (2, 1) for series in selected.values())
    with pytest.raises(ContractError, match="identify packet reader sources"):
        collect_agent_observation_sources_by_branch_reader(
            {keys[0]: readers[keys[0]]},
            agent_id="pilot",
            fields=("speed",),
            selected_branch_digests=[keys[0][1], keys[1][1]],
        )


def test_numeric_export_requires_explicit_sources_and_preserves_lineage() -> None:
    projection = _projection()
    sources = _sources(projection)
    exports = build_numeric_exports(
        projection, sources, agent_id="pilot",
        selected_branch_digests=[key[1] for key in sources],
        action_encoder=_action, reward_encoder=_reward
    )
    assert len(exports) == 2
    assert all(item.projection_digest == projection.digest for item in exports)
    assert {item.split for item in exports} == {"training"}
    assert all(item.observations.shape[0] == item.actions.shape[0] + 1 for item in exports)
    assert {item.branch_digest for item in exports} == {key[1] for key in sources}

    selected_key = next(iter(sources))
    selected = build_numeric_exports(
        projection,
        {selected_key: sources[selected_key]},
        agent_id="pilot",
        selected_branch_digests=[selected_key[1]],
        action_encoder=_action,
        reward_encoder=_reward,
    )
    assert len(selected) == 1
    assert selected[0].branch_digest == selected_key[1]

    missing = dict(sources)
    missing.pop(next(iter(missing)))
    with pytest.raises(ContractError, match="keys differ"):
        build_numeric_exports(
            projection, missing, agent_id="pilot",
            selected_branch_digests=[key[1] for key in sources],
            action_encoder=_action, reward_encoder=_reward
        )


def test_numeric_export_rejects_bad_lengths_nonfinite_values_and_action_vectors() -> None:
    projection = _projection()
    sources = _sources(projection)
    key = next(iter(sources))
    rows = [row for row in projection.rows if row.branch_digest == key[1]]
    sources[key] = AgentObservationSeries(
        key[0], key[1], "pilot", tuple(
            AgentObservationPacket(
                "pilot", f"bad_{index}", "gym_envs.observation_view.v1",
                "facade_observation_packet", values
            ) for index, values in enumerate(np.zeros((len(rows), 2), dtype=np.float32))
        )
    )
    with pytest.raises(ContractError, match="needs"):
        build_numeric_exports(
            projection, sources, agent_id="pilot",
            selected_branch_digests=[key[1] for key in sources],
            action_encoder=_action, reward_encoder=_reward
        )

    with pytest.raises(ContractError, match="finite"):
        AgentObservationPacket(
            "pilot", "bad", "gym_envs.observation_view.v1",
            "facade_observation_packet", np.asarray([np.inf, 0.0])
        )

    sources = _sources(projection)
    with pytest.raises(ContractError, match="one-dimensional"):
        build_numeric_exports(
            projection,
            sources, agent_id="pilot",
            selected_branch_digests=[key[1] for key in sources],
            action_encoder=lambda _row: [[1.0]],
            reward_encoder=_reward,
        )


def test_numeric_export_writes_episode_store_and_auditable_sidecar(tmp_path) -> None:
    projection = _projection()
    exports = build_numeric_exports(
        projection, _sources(projection), agent_id="pilot",
        selected_branch_digests=[key[1] for key in _sources(projection)],
        action_encoder=_action, reward_encoder=_reward
    )
    receipt = write_episode_store(exports, str(tmp_path / "dataset"))
    assert receipt.metadata_digest
    assert len(receipt.episode_paths) == 2
    dataset = EpisodeDataset(str(tmp_path / "dataset"))
    assert len(dataset) == 2
    assert dataset.spec.obs_vec_dim == 2
    assert dataset.spec.action_dim == 1
    assert all(dataset.get_episode(index).dones.shape[0] > 0 for index in range(len(dataset)))
    metadata = json.loads((tmp_path / "dataset" / "trace_projection_export.json").read_text())
    assert {item["agent_id"] for item in metadata["episodes"]} == {"pilot"}
    assert {item["observation_provenance"] for item in metadata["episodes"]} == {
        "facade_observation_packet"
    }
    with pytest.raises(ContractError, match="existing export"):
        write_episode_store(exports, str(tmp_path / "dataset"))
    assert all("\\" not in item["path"] for item in metadata["episodes"])


def _exports():
    projection = _projection()
    return build_numeric_exports(
        projection, _sources(projection), agent_id="pilot",
        selected_branch_digests=[key[1] for key in _sources(projection)],
        action_encoder=_action, reward_encoder=_reward
    )


def test_episode_store_refuses_a_root_that_already_has_episodes(tmp_path) -> None:
    # A crashed earlier run can leave episodes without a sidecar; never append.
    (tmp_path / "dataset" / "episodes").mkdir(parents=True)
    (tmp_path / "dataset" / "episodes" / "episode_000000.npz").write_bytes(b"orphan")
    with pytest.raises(ContractError, match="existing export"):
        write_episode_store(_exports(), str(tmp_path / "dataset"))


def test_episode_store_refuses_mixed_splits(tmp_path) -> None:
    exports = _exports()
    mixed = (exports[0], dataclasses.replace(exports[1], split="evaluation"))
    with pytest.raises(ContractError, match="single split"):
        write_episode_store(mixed, str(tmp_path / "dataset"))
    assert not (tmp_path / "dataset").exists()


def test_episode_store_leaves_nothing_behind_when_a_write_fails(tmp_path, monkeypatch) -> None:
    from python.world_model import replay

    def fail(*_args, **_kwargs):
        raise OSError("disk full")

    monkeypatch.setattr(replay.EpisodeStore, "add", fail)
    with pytest.raises(OSError, match="disk full"):
        write_episode_store(_exports(), str(tmp_path / "dataset"))
    assert list(tmp_path.iterdir()) == []
