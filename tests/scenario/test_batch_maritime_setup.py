from __future__ import annotations

from unittest.mock import Mock

import ef_py
import pytest

from python.scenario.compiler import ScenarioCompiler
from python.scenario.runtime.batch_apply import _load_compiled_scenario_for_setup_target
from python.scenario.runtime import load_compiled_scenario_for_setup_target


class RecordingTarget:
    def __init__(self, count):
        self.count = count
        self.requests = []

    def world_count(self):
        return self.count

    def apply_world_setup(self, request):
        self.requests.append(request)
        return ef_py.BatchWorldSetupResult()


@pytest.mark.parametrize("count", [1, 2])
def test_compiled_scenario_transports_configured_and_absent_maritime(count):
    target = RecordingTarget(count)
    configured = ScenarioCompiler.compile_data({"environment": {"maritime": {
        "sea_state": 6, "wave_heading_deg": 90, "wave_period_s": 9}}, "entities": []})
    load_compiled_scenario_for_setup_target(target, configured, seeds=list(range(count)))
    items = target.requests[-1].maritime_assignments
    assert [item.world_index for item in items] == list(range(count))
    assert all(item.configured and (item.sea_state, item.wave_heading_deg, item.wave_period_s) == (6, 90, 9) for item in items)
    absent = ScenarioCompiler.compile_data({"entities": []})
    load_compiled_scenario_for_setup_target(target, absent, seeds=list(range(count)))
    assert all(not item.configured for item in target.requests[-1].maritime_assignments)


def test_injected_legacy_applier_cannot_silently_drop_authored_maritime():
    applier = Mock()
    compiled = ScenarioCompiler.compile_data({"environment": {"maritime": {"sea_state": 6}}})
    with pytest.raises(ValueError, match="cannot carry environment.maritime"):
        _load_compiled_scenario_for_setup_target(RecordingTarget(1), compiled, seeds=[42], setup_payload_apply=applier)
    applier.assert_not_called()
