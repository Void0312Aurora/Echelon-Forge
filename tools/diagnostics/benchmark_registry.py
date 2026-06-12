from __future__ import annotations

from dataclasses import dataclass
import importlib
from typing import Callable


@dataclass(frozen=True)
class BenchmarkFamily:
    name: str
    description: str
    module_path: str


def load_benchmark_entrypoint(family_name: str) -> Callable[[], int]:
    family = BENCHMARK_FAMILIES[str(family_name)]
    module = importlib.import_module(family.module_path)
    main = getattr(module, "main", None)
    if not callable(main):
        raise TypeError(f"benchmark family {family_name!r} module {family.module_path!r} has no callable main()")
    return main


BENCHMARK_FAMILIES: dict[str, BenchmarkFamily] = {
    "air_combat_post_launch_assessment": BenchmarkFamily(
        name="air_combat_post_launch_assessment",
        description="Air-combat post-launch assessment rollout benchmark.",
        module_path="tools.diagnostics.benchmarks.air_combat_post_launch_assessment",
    ),
    "spatial_query": BenchmarkFamily(
        name="spatial_query",
        description="Compiled spatial-query vs legacy geometry benchmark.",
        module_path="tools.diagnostics.benchmarks.spatial_query",
    ),
    "scenario_compiler": BenchmarkFamily(
        name="scenario_compiler",
        description="Scenario compiler cache / instantiate / load benchmark.",
        module_path="tools.diagnostics.benchmarks.scenario_compiler",
    ),
    "mission_runtime": BenchmarkFamily(
        name="mission_runtime",
        description="Mission runtime helper microbenchmark.",
        module_path="tools.diagnostics.benchmarks.mission_runtime",
    ),
    "world_batch_vec_env": BenchmarkFamily(
        name="world_batch_vec_env",
        description="WorldBatchVecEnv training-adapter benchmark.",
        module_path="tools.diagnostics.benchmarks.world_batch_vec_env",
    ),
    "policy_observation_bridge": BenchmarkFamily(
        name="policy_observation_bridge",
        description="Policy-observation bridge benchmark.",
        module_path="tools.diagnostics.benchmarks.policy_observation_bridge",
    ),
}
