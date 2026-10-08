from __future__ import annotations

import json

import pytest

from python.scenario.compiler import ScenarioCompiler
from python.scenario.compiler.common import _SURFACE_TYPE_MAP
from python.scenario.runtime import BatchWorldApplyBuffer, build_compiled_world_layout, load_compiled_scenario_for_setup_target
from python.simulation import create_scenario_runtime_adapter


def scene(surface="SoftDirt"):
    return {"environment": {"zones": [{"name": "Test", "surface": surface}]}, "entities": []}


@pytest.mark.parametrize("surface", ["Conrete", "concrete", "CONCRETE", "", None, 3, [], {}])
def test_invalid_surface_rejected_before_materialization(surface):
    with pytest.raises(ValueError, match=r"environment.zones\[0\]\.surface"):
        ScenarioCompiler.compile_data(scene(surface), source_path="terrain.json")


def test_imported_zone_is_validated_in_its_source(tmp_path):
    prefab = tmp_path / "prefab.json"
    prefab.write_text(json.dumps({"zones": [{"name": "Test", "surface": "Conrete"}]}))
    with pytest.raises(ValueError, match=r"imported scenario prefab zones\[0\]\.surface.*prefab.json"):
        ScenarioCompiler.compile_data({"imports": [{"file": str(prefab)}]})


@pytest.mark.parametrize("surface,expected", list(_SURFACE_TYPE_MAP.items()))
def test_valid_surface_matches_legacy_template_and_batch(surface, expected):
    compiled = ScenarioCompiler.compile_data(scene(surface))
    for use_template in (False, True):
        assert build_compiled_world_layout(compiled, seed=42, use_compiled_template=use_template).zones[0].surface_type == expected
    buffer = BatchWorldApplyBuffer(2)
    load_compiled_scenario_for_setup_target(create_scenario_runtime_adapter(2), compiled, seeds=[11, 17], apply_buffer=buffer)
    assert [zone.surface_type for zone in buffer.zone_defs] == [expected, expected]


def test_omitted_surface_intentionally_defaults_to_soft_dirt():
    data = scene()
    del data["environment"]["zones"][0]["surface"]
    compiled = ScenarioCompiler.compile_data(data)
    assert compiled.runtime_metadata.layout_template.zones[0].surface_type == 3
