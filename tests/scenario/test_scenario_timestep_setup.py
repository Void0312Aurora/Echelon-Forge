from __future__ import annotations

import ef_py
import numpy as np
import pytest

from python.scenario.compiler import ScenarioCompiler
from python.scenario.runtime import (
    load_compiled_scenario_for_setup_target,
    prepare_scenario_world_layout,
    apply_world_layout_to_kernel,
)


@pytest.mark.parametrize("count", [1, 2])
def test_compiled_reused_world_default_matches_fresh_world(count):
    reused = ef_py.RuntimeFacade(count)
    a = ScenarioCompiler.compile_data({"environment": {"time_step": 0.2}})
    b = ScenarioCompiler.compile_data({})
    for compiled, expected in ((a, 0.2), (b, ef_py.DEFAULT_TIME_STEP_S), (a, 0.2)):
        fresh = ef_py.RuntimeFacade(count)
        for target in (reused, fresh):
            load_compiled_scenario_for_setup_target(target, compiled, seeds=list(range(count)))
        assert [reused.world_time_step(i) for i in range(count)] == pytest.approx([expected] * count)
        assert [reused.world_time_step(i) for i in range(count)] == [fresh.world_time_step(i) for i in range(count)]


def test_legacy_kernel_setup_also_restores_absent_default():
    kernel = ef_py.SimulationKernel()
    for data, expected in (({"environment": {"time_step": 0.2}}, 0.2), ({}, ef_py.DEFAULT_TIME_STEP_S)):
        layout = prepare_scenario_world_layout(data, seed=17, rng=np.random.RandomState(17))
        apply_world_layout_to_kernel(kernel, layout)
        assert kernel.get_time_step() == expected


@pytest.mark.parametrize("value", [0, -0.1, float("nan"), float("inf"), None, True, "0.2"])
def test_authored_invalid_timestep_fails_at_compiler_and_legacy_layout(value):
    data = {"environment": {"time_step": value}}
    with pytest.raises(ValueError, match="environment.time_step"):
        ScenarioCompiler.compile_data(data, source_path="invalid-dt.json")
    with pytest.raises(ValueError, match="environment.time_step"):
        prepare_scenario_world_layout(data, seed=17, rng=np.random.RandomState(17))


@pytest.mark.parametrize("value", [-0.1, float("nan"), float("inf")])
def test_native_facade_rejects_invalid_dt_without_partial_reset(value):
    facade = ef_py.RuntimeFacade(2)
    request = ef_py.BatchWorldSetupRequest()
    request.time_steps = [0.2, 0.3]
    facade.apply_world_setup(request)
    facade.step_batch()
    before = [facade.world_time_step(i) for i in range(2)]
    request.time_steps = [0.1, value]
    with pytest.raises(ValueError, match="time_steps"):
        facade.apply_world_setup(request)
    assert [facade.world_time_step(i) for i in range(2)] == before
