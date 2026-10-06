"""ESM observation DTOs travel through the maintained compiled facade."""
from __future__ import annotations

import json
from pathlib import Path

import ef_py
import pytest

from python.simulation.air.observation import build_air_esm_matrix
from python.simulation.facade_batch import FacadeBatchBackend


def _setup(seeds: tuple[int, ...]) -> ef_py.BatchWorldSetupRequest:
    request = ef_py.BatchWorldSetupRequest()
    request.seeds = list(seeds)
    request.time_steps = [0.05]
    spawns = []
    for name, side, north in (("Passive", ef_py.Side.Blue, 0.0), ("Emitter", ef_py.Side.Red, 10000.0)):
        spawn = ef_py.WorldSpawnRequest()
        spawn.world_index = 0
        spawn.type_name = name
        spawn.entity_name = name
        spawn.side = side
        spawn.y = north
        spawn.z = 5000.0
        spawns.append(spawn)
    request.spawn_requests = spawns
    return request


@pytest.mark.parametrize("classify", [True, False])
def test_rf_strobe_native_dto_reaches_facade_with_no_range_solution(tmp_path: Path, classify: bool) -> None:
    sensor = {"max_range": 1000000.0, "fov_deg": 360.0, "scan_period": 0.01,
              "reference_range_m": 1000000.0, "reference_snr_db": 100.0,
              "range_power": 8.0, "bearing_noise_std": 0.0, "velocity_noise_std": 0.0}
    definitions = [
        {"name": "Passive", "type": "C2Node", "sensor": {**sensor, "type": "ESM"},
         "esm": {"require_rf_contract": True, "classify_emitters": classify,
                 "memory_s": 1.0, "confirmation_scans": 2,
                 "frequency_min_mhz": 900.0, "frequency_max_mhz": 1100.0}},
        {"name": "Emitter", "type": "C2Node", "sensor": {**sensor, "type": "Radar",
         "rf_eirp_watts": 100.0, "rf_frequency_mhz": 1000.0, "rf_bandwidth_mhz": 20.0}},
    ]
    (tmp_path / "synthetic_rf.json").write_text(json.dumps({"units": definitions}), encoding="utf-8")
    backend = FacadeBatchBackend(database_path=str(tmp_path), setup_factory=_setup,
                                 controlled_spawn_indices=(0, 1))
    try:
        backend.seed(161)
        first = backend.reset()
        assert not first.observations[0].esm_detections
        hold = ef_py.PilotAction()
        hold.active = True
        actions = {key: hold for key in first.entity_keys}
        observed = backend.step(actions)
        row = observed.observations[0].esm_detections[0]
        assert isinstance(row, ef_py.ESMEvent)
        assert row.has_rf_power
        assert row.confidence == pytest.approx(0.5)
        assert not row.classification_known
        observed = backend.step(actions)
        row = observed.observations[0].esm_detections[0]
        assert row.received_power_dbm == pytest.approx(-62.4477832219)
        assert row.sensitivity_margin_db == pytest.approx(22.5522167781)
        assert row.confidence == 1.0
        assert row.classification_known is classify
        assert row.age_s == 0.0
        assert not row.is_lock and not row.is_guidance
        assert not hasattr(row, "range") and not hasattr(row, "position")
        assert build_air_esm_matrix(observed.observations[0]).shape == (8, 10)
        with pytest.raises(AttributeError):
            row.confidence = 0.0
        backend.reset()
        assert not backend.snapshot().observations[0].esm_detections
    finally:
        backend.close()
