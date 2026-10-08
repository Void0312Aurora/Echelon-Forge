from __future__ import annotations

import ef_py
import pytest

from python.scenario.compiler import ScenarioCompiler
from python.scenario.runtime import load_compiled_scenario_for_setup_target
from python.scenario.runtime.world_setup import normalize_world_setup_seeds


@pytest.mark.parametrize("values,expected", [([], [42, 43, 44, 45]), ([11], [11, 12, 13, 14]),
                                           ([11, 22, 33, 44], [11, 22, 33, 44]),
                                           ([0xFFFFFFFF], [0xFFFFFFFF, 0, 1, 2])])
def test_compiled_loader_records_the_effective_seed_modes(values, expected):
    class Target:
        request = None
        def world_count(self): return 4
        def apply_world_setup(self, request):
            self.request = request
            return ef_py.BatchWorldSetupResult()
    target = Target()
    worlds = load_compiled_scenario_for_setup_target(target, ScenarioCompiler.compile_data({}), seeds=values)
    assert list(target.request.seeds) == expected
    assert [world.layout.seed for world in worlds] == expected
    assert normalize_world_setup_seeds(values, 4) == expected


@pytest.mark.parametrize("count,values", [(4, [11, 22, 33]), (1, [11, 22]), (0, [11, 22])])
def test_bad_counts_reject_compiled_loader_before_setup(count, values):
    class Target:
        def world_count(self): return count
        def apply_world_setup(self, request): pytest.fail("setup mutated before seed validation")
    with pytest.raises(ValueError, match="seeds must have size"):
        load_compiled_scenario_for_setup_target(Target(), ScenarioCompiler.compile_data({}), seeds=values)


def test_native_facade_binding_rejects_bad_reset_and_setup_counts():
    facade = ef_py.RuntimeFacade(4)
    reset = ef_py.BatchResetRequest()
    reset.seeds = [11, 22, 33]
    with pytest.raises(ValueError, match="seeds must have size"):
        facade.reset_batch(reset)
    setup = ef_py.BatchWorldSetupRequest()
    setup.seeds = [11, 22, 33]
    with pytest.raises(ValueError, match="seeds must have size"):
        facade.apply_world_setup(setup)
