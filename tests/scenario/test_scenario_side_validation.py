from __future__ import annotations

import json

import ef_py
import pytest

from python.runtime_bootstrap import resolve_repo_path
from python.scenario.compiler import ScenarioCompiler
from python.scenario.runtime import BatchWorldApplyBuffer, build_compiled_world_layout, load_compiled_scenario_for_setup_target
from python.scenario.runtime.models import resolve_scenario_side
from python.simulation import create_scenario_runtime_adapter


def scene(side="Blue"):
    return {"entities": [{"name": "Test", "type": "F-16C_Block50", "side": side,
                          "is_agent": True, "pos": [0, 0, 1200], "vel": [0, 180, 0]}]}


@pytest.mark.parametrize("side", ["Blu", "Reed", "RED", "blue", "", None, 0, [], {}])
def test_explicit_invalid_side_rejected_at_compile_and_runtime(side):
    with pytest.raises(ValueError, match=r"entities\[0\]\.side"):
        ScenarioCompiler.compile_data(scene(side), source_path="authored.json")
    with pytest.raises(ValueError, match="side must be one of"):
        resolve_scenario_side(side)


def test_imported_invalid_side_names_source_and_field(tmp_path):
    imported = tmp_path / "prefab.json"
    imported.write_text(json.dumps(scene("Reed")), encoding="utf-8")
    with pytest.raises(ValueError, match=r"imported scenario prefab entities\[0\]\.side.*prefab.json"):
        ScenarioCompiler.compile_data({"imports": [{"file": str(imported)}]})


@pytest.mark.parametrize("side", ["Blue", "Red", "Neutral"])
def test_allowed_sides_preserved_in_single_and_compiled_batch_paths(side):
    compiled = ScenarioCompiler.compile_data(scene(side))
    expected = getattr(ef_py.Side, side)
    for use_template in (False, True):
        layout = build_compiled_world_layout(compiled, seed=42, use_compiled_template=use_template)
        assert layout.spawns[0].side == expected
    adapter = create_scenario_runtime_adapter(2)
    assert adapter.load_database(resolve_repo_path("examples", "config", "database"))
    buffer = BatchWorldApplyBuffer(2)
    worlds = load_compiled_scenario_for_setup_target(adapter, compiled, seeds=[11, 17], apply_buffer=buffer)
    assert len(worlds) == 2
    assert [req.side for req in buffer.spawn_requests] == [expected, expected]


def test_absent_side_intentionally_defaults_to_neutral():
    data = scene()
    del data["entities"][0]["side"]
    compiled = ScenarioCompiler.compile_data(data)
    assert compiled.runtime_metadata.layout_template.spawns[0].side_name == "Neutral"
