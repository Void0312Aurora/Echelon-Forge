from __future__ import annotations

import hashlib
import json

import pytest

from python.experiment.definition import (
    ConfigComposition,
    EvaluationProtocol,
    Experiment,
    ExperimentRegistry,
    ScenarioRef,
    SeedSpec,
)
from python.experiment.input_lock_artifacts import (
    load_resolved_input_lock_artifacts,
    write_resolved_input_lock_artifacts,
)
from python.experiment.resolved_input_lock import (
    InputLockError,
    ResolvedInputLock,
    build_resolved_input_lock,
    canonical_json_bytes,
)
from python.rl.runtime.resolved_input_lock_binding import (
    InputLockBindingError,
    load_resolved_input_lock_path,
)


def _candidate(*, seed=239, **kwargs):
    registry = ExperimentRegistry()
    registry.register_config_base("artifact_test", {"n_envs": 1})
    registry.register_evaluation_protocol(EvaluationProtocol("smoke", "bounded smoke"))
    experiment = Experiment(
        "artifact_test",
        ScenarioRef("scenarios/test/test_free_fall.json"),
        ConfigComposition("artifact_test"),
        SeedSpec((seed,)),
        "smoke",
    )
    return build_resolved_input_lock(experiment, registry, **kwargs)


def test_exported_pair_reuses_projection_and_native_payload_identity(tmp_path):
    candidate = _candidate(provenance={"note": "输入锁"})
    original = candidate.as_dict()
    projection = tmp_path / "resolved-experiment.json"
    payload = tmp_path / "native-input-lock.json"
    write_resolved_input_lock_artifacts(
        candidate, projection_path=projection, native_input_lock_path=payload
    )
    assert projection.read_bytes() == canonical_json_bytes(original)
    assert payload.read_bytes() == canonical_json_bytes(original["input_lock"])
    assert hashlib.sha256(payload.read_bytes()).hexdigest() == candidate.digest
    assert hashlib.sha256(projection.read_bytes()).hexdigest() != candidate.digest
    assert load_resolved_input_lock_path(projection).digest == candidate.digest
    reloaded = load_resolved_input_lock_artifacts(
        projection_path=projection, native_input_lock_path=payload
    )
    assert reloaded.as_dict() == original == candidate.as_dict()
    assert reloaded.digest == candidate.digest
    # The native file intentionally is not a full resolved-experiment document.
    with pytest.raises(InputLockBindingError, match="document_schema_invalid"):
        load_resolved_input_lock_path(payload)


def test_projection_metadata_changes_preserve_native_input_bytes(tmp_path):
    original = _candidate()
    changed = _candidate(
        status="unknown", provenance={"report_label": "another report"},
        native_runtime={"host_mode": "dark"},
    )
    projections = []
    payloads = []
    for name, candidate in (("original", original), ("changed", changed)):
        projection = tmp_path / f"{name}-projection.json"
        payload = tmp_path / f"{name}-input-lock.json"
        write_resolved_input_lock_artifacts(
            candidate, projection_path=projection, native_input_lock_path=payload
        )
        loaded = load_resolved_input_lock_artifacts(
            projection_path=projection, native_input_lock_path=payload
        )
        assert loaded.digest == original.digest
        projections.append(projection.read_bytes())
        payloads.append(payload.read_bytes())
    assert projections[0] != projections[1]
    assert payloads[0] == payloads[1]


@pytest.mark.parametrize("damage", ["wrong_lock", "projection_bytes", "noncanonical", "corrupt"])
def test_pair_rejects_native_artifact_identity_changes(tmp_path, damage):
    candidate = _candidate()
    projection = tmp_path / "projection.json"
    payload = tmp_path / "input-lock.json"
    write_resolved_input_lock_artifacts(
        candidate, projection_path=projection, native_input_lock_path=payload
    )
    damaged = {
        "wrong_lock": canonical_json_bytes(_candidate(seed=240).as_dict()["input_lock"]),
        "projection_bytes": projection.read_bytes(),
        "noncanonical": json.dumps(candidate.as_dict()["input_lock"], indent=2).encode(),
        "corrupt": b"not-json",
    }
    payload.write_bytes(damaged[damage])
    with pytest.raises(InputLockError, match="native_artifact_digest_mismatch"):
        load_resolved_input_lock_artifacts(
            projection_path=projection, native_input_lock_path=payload
        )


@pytest.mark.parametrize("missing", ["projection", "payload"])
def test_pair_rejects_missing_artifact(tmp_path, missing):
    projection = tmp_path / "projection.json"
    payload = tmp_path / "input-lock.json"
    write_resolved_input_lock_artifacts(
        _candidate(), projection_path=projection, native_input_lock_path=payload
    )
    (projection if missing == "projection" else payload).unlink()
    with pytest.raises(InputLockError, match="unreadable"):
        load_resolved_input_lock_artifacts(
            projection_path=projection, native_input_lock_path=payload
        )


def test_export_rejects_aliased_paths_before_writing(tmp_path):
    artifact = tmp_path / "input-lock.json"
    artifact.write_bytes(b"existing file")
    with pytest.raises(InputLockError, match="artifact_paths_must_differ"):
        write_resolved_input_lock_artifacts(
            _candidate(), projection_path=artifact,
            native_input_lock_path=artifact.parent / "." / artifact.name,
        )
    assert artifact.read_bytes() == b"existing file"


def test_export_does_not_turn_joined_evidence_into_a_pre_run_projection(tmp_path):
    candidate = _candidate()
    document = candidate.as_dict()
    document["completion_evidence"] = {}
    joined_shape = ResolvedInputLock(document, candidate.digest)
    projection = tmp_path / "projection.json"
    payload = tmp_path / "input-lock.json"
    with pytest.raises(InputLockError, match="unjoined_projection_required"):
        write_resolved_input_lock_artifacts(
            joined_shape, projection_path=projection, native_input_lock_path=payload
        )
    assert not projection.exists() and not payload.exists()
