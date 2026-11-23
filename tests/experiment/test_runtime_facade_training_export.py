from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path

import pytest

from python.experiment.contracts import ContractError, canonical_bytes
from python.experiment.numeric_observation_adapter import AgentObservationSeries
from python.experiment.runtime_facade_training_export import (
    ADMITTED_AIR_MISSION_SURFACES,
    AIR_RUNTIME_FACADE_SURFACE,
    AIR_TAKEOFF_RUNTIME_FACADE_SURFACE,
    export_runtime_facade_training_sidecar,
    load_runtime_facade_training_sidecar,
)
from tests.experiment.test_numeric_observation_adapter import _action, _projection, _reward, _sources


def _selected():
    projection = _projection()
    sources = _sources(projection)
    key = next(iter(sources))
    return projection, key, {key: sources[key]}


def test_sidecar_write_failure_leaves_no_export_and_allows_retry(tmp_path, monkeypatch) -> None:
    from python.experiment import runtime_facade_training_export as exporter

    projection, key, sources = _selected()
    root = tmp_path / "atomic-export"
    write_bytes = Path.write_bytes

    def fail_sidecar(path, data):
        if path.name == exporter._RUNTIME_EXPORT_SIDECAR:
            raise OSError("injected sidecar write failure")
        return write_bytes(path, data)

    kwargs = dict(
        agent_id="pilot", selected_branch_digests=[key[1]], seed=11,
        split="training", action_encoder=_action, reward_encoder=_reward,
        root_dir=str(root),
    )
    with monkeypatch.context() as patch:
        patch.setattr(Path, "write_bytes", fail_sidecar)
        with pytest.raises(OSError, match="sidecar write failure"):
            export_runtime_facade_training_sidecar(projection, sources, **kwargs)
    assert not root.exists()
    assert list(tmp_path.iterdir()) == []
    receipt = export_runtime_facade_training_sidecar(projection, sources, **kwargs)
    payload = load_runtime_facade_training_sidecar(
        str(root), projection_digest=projection.digest, agent_id="pilot",
        seed=11, split="training", branch_digests=[key[1]],
    )
    assert payload["metadata_digest"] == receipt.metadata_digest
    assert all(Path(path).is_file() for path in receipt.episode_paths)


def test_runtime_facade_export_round_trips_one_admitted_air_branch(tmp_path) -> None:
    projection, key, sources = _selected()
    receipt = export_runtime_facade_training_sidecar(
        projection,
        sources,
        agent_id="pilot",
        selected_branch_digests=[key[1]],
        seed=11,
        split="training",
        action_encoder=_action,
        reward_encoder=_reward,
        root_dir=str(tmp_path / "air-training"),
    )

    assert receipt.surface_id == AIR_RUNTIME_FACADE_SURFACE
    assert receipt.seed == 11
    assert receipt.split == "training"
    assert receipt.branch_digests == (key[1],)
    payload = load_runtime_facade_training_sidecar(
        receipt.root_dir,
        projection_digest=projection.digest,
        agent_id="pilot",
        seed=11,
        split="training",
        branch_digests=[key[1]],
    )
    assert payload["metadata_digest"] == receipt.metadata_digest
    assert payload["packet_provenance"] == "facade_observation_packet"
    assert payload["surface_id"] == AIR_RUNTIME_FACADE_SURFACE
    assert payload["episodes"][0]["projection_digest"] == projection.digest
    assert payload["branch_ancestry"][0]["branch_digest"] == key[1]


def test_takeoff_surface_round_trips_through_the_same_sidecar_contract(tmp_path) -> None:
    projection, key, sources = _selected()
    receipt = export_runtime_facade_training_sidecar(
        projection,
        sources,
        agent_id="pilot",
        selected_branch_digests=[key[1]],
        seed=11,
        split="training",
        action_encoder=_action,
        reward_encoder=_reward,
        root_dir=str(tmp_path / "takeoff-training"),
        surface_id=AIR_TAKEOFF_RUNTIME_FACADE_SURFACE,
    )
    payload = load_runtime_facade_training_sidecar(
        receipt.root_dir,
        projection_digest=projection.digest,
        agent_id="pilot",
        seed=11,
        split="training",
        branch_digests=[key[1]],
        surface_id=AIR_TAKEOFF_RUNTIME_FACADE_SURFACE,
    )
    assert payload["surface_id"] == AIR_TAKEOFF_RUNTIME_FACADE_SURFACE
    assert receipt.surface_id in ADMITTED_AIR_MISSION_SURFACES


def test_export_rejects_decision_belief_source_that_old_api_accepts(tmp_path) -> None:
    projection, key, sources = _selected()
    bad_packets = tuple(replace(packet, provenance="decision_belief_packet") for packet in sources[key].packets)
    bad_sources = {key: AgentObservationSeries(key[0], key[1], "pilot", bad_packets)}
    with pytest.raises(ContractError, match="facade observation provenance"):
        export_runtime_facade_training_sidecar(
            projection,
            bad_sources,
            agent_id="pilot",
            selected_branch_digests=[key[1]],
            seed=11,
            split="training",
            action_encoder=_action,
            reward_encoder=_reward,
            root_dir=str(tmp_path / "bad-source"),
        )


def test_export_rejects_toy_projection_and_seed_or_branch_confusion(tmp_path) -> None:
    projection, key, sources = _selected()
    toy_rows = tuple(replace(row, evidence_label="toy") for row in projection.rows)
    toy_projection = replace(projection, rows=toy_rows)
    with pytest.raises(ContractError, match="admitted Air"):
        export_runtime_facade_training_sidecar(
            toy_projection,
            sources,
            agent_id="pilot",
            selected_branch_digests=[key[1]],
            seed=11,
            split="training",
            action_encoder=_action,
            reward_encoder=_reward,
            root_dir=str(tmp_path / "toy"),
        )

    with pytest.raises(ContractError, match="seed"):
        export_runtime_facade_training_sidecar(
            projection,
            sources,
            agent_id="pilot",
            selected_branch_digests=[key[1]],
            seed=17,
            split="training",
            action_encoder=_action,
            reward_encoder=_reward,
            root_dir=str(tmp_path / "wrong-seed"),
        )
    with pytest.raises(ContractError, match="branch"):
        export_runtime_facade_training_sidecar(
            projection,
            sources,
            agent_id="pilot",
            selected_branch_digests=["f" * 64],
            seed=11,
            split="training",
            action_encoder=_action,
            reward_encoder=_reward,
            root_dir=str(tmp_path / "wrong-branch"),
        )


def test_loader_rejects_digest_and_metadata_tampering(tmp_path) -> None:
    projection, key, sources = _selected()
    receipt = export_runtime_facade_training_sidecar(
        projection,
        sources,
        agent_id="pilot",
        selected_branch_digests=[key[1]],
        seed=11,
        split="training",
        action_encoder=_action,
        reward_encoder=_reward,
        root_dir=str(tmp_path / "tamper"),
    )
    path = tmp_path / "tamper" / "runtime_facade_training_export.json"
    payload = json.loads(path.read_text())
    payload["projection_digest"] = "0" * 64
    path.write_bytes(canonical_bytes(payload) + b"\n")
    with pytest.raises(ContractError, match="metadata digest"):
        load_runtime_facade_training_sidecar(
            receipt.root_dir,
            projection_digest=projection.digest,
            agent_id="pilot",
            seed=11,
            split="training",
            branch_digests=[key[1]],
        )


def test_export_rejects_evaluation_split_for_training_sidecar(tmp_path) -> None:
    projection, key, sources = _selected()
    with pytest.raises(ContractError, match="split"):
        export_runtime_facade_training_sidecar(
            projection,
            sources,
            agent_id="pilot",
            selected_branch_digests=[key[1]],
            seed=11,
            split="evaluation",
            action_encoder=_action,
            reward_encoder=_reward,
            root_dir=str(tmp_path / "evaluation"),
        )


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))

def test_reserved_api_does_not_claim_production_admission() -> None:
    assert AIR_RUNTIME_FACADE_SURFACE == "air.execution.runtime_facade.v1"
    assert "receipt" not in AIR_RUNTIME_FACADE_SURFACE
    assert "input_lock" not in AIR_RUNTIME_FACADE_SURFACE
