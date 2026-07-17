from __future__ import annotations

import atexit
import json
import os
from dataclasses import dataclass
from typing import Any

from .clone import (
    _clone_runtime_context_scenario_data,
    _clone_runtime_scenario_data,
    _clone_scenario_value,
)
from .common import _mtime_ns, REPO_ROOT
from .layout_template import _compile_world_layout_template, _extract_ils_beacons
from .merge import _compile_merged_scenario_data
from .reward_metadata import (
    _build_approach_reward_config,
    _build_lnav_runtime_config,
    _build_objective_shaping_config,
    _build_safety_reward_config,
    _build_waypoint_mode_reward_config,
    _compile_conditional_objectives,
    ApproachRewardConfig,
    CompiledScenarioRuntimeMetadata,
    CompiledWorldLayoutTemplate,
    LNavRuntimeConfig,
    SafetyRewardConfig,
    WaypointModeRewardConfig,
)
from .validation import validate_scenario_compiler_shape
from .waypoint_cache import (
    _compile_normalized_waypoint_templates,
    _compile_waypoint_template_route_ref_ids,
    _normalize_runtime_mission_command,
    materialize_runtime_waypoint_cache,
)
from ..environment_substrate.scenario_ingestion import (
    ingest_projection_setup_payloads_into_scenario,
)


@dataclass(frozen=True)
class CompiledScenario:
    source_path: str
    scenario_name: str
    merged_scenario_data: dict[str, Any]
    runtime_metadata: CompiledScenarioRuntimeMetadata
    imported_files: tuple[str, ...]
    dependency_mtimes_ns: tuple[tuple[str, int], ...]
    warnings: tuple[str, ...]
    zone_count: int
    entity_count: int

    def instantiate(self) -> dict[str, Any]:
        return _clone_scenario_value(self.merged_scenario_data)

    def instantiate_runtime(self) -> dict[str, Any]:
        return _clone_runtime_scenario_data(self.merged_scenario_data)

    def instantiate_runtime_context(self) -> dict[str, Any]:
        return _clone_runtime_context_scenario_data(self.merged_scenario_data)

    def is_fresh(self) -> bool:
        for path, expected_mtime_ns in self.dependency_mtimes_ns:
            try:
                if _mtime_ns(path) != int(expected_mtime_ns):
                    return False
            except OSError:
                return False
        return True


class ScenarioCompiler:
    _path_cache: dict[str, CompiledScenario] = {}

    @classmethod
    def clear_cache(cls) -> None:
        cls._path_cache.clear()

    @classmethod
    def compile_path(cls, source_path: str) -> CompiledScenario:
        abs_path = os.path.abspath(source_path)
        cached = cls._path_cache.get(abs_path)
        if cached is not None and cached.is_fresh():
            return cached

        compiled = cls._compile_from_path(abs_path)
        cls._path_cache[abs_path] = compiled
        return compiled

    @classmethod
    def compile_data(cls, scenario_data: dict[str, Any], *, source_path: str | None = None) -> CompiledScenario:
        if not isinstance(scenario_data, dict):
            raise TypeError("scenario_data must be a dict")
        return cls._compile_from_data(
            scenario_data,
            source_path=os.path.abspath(source_path) if source_path else "<inline>",
        )

    @classmethod
    def _compile_from_path(cls, abs_path: str) -> CompiledScenario:
        with open(abs_path, "r", encoding="utf-8") as handle:
            raw = json.load(handle)
        if not isinstance(raw, dict):
            raise ValueError(f"Scenario file must contain a JSON object: {abs_path}")
        return cls._compile_from_data(raw, source_path=abs_path)

    @classmethod
    def _compile_from_data(cls, raw_scenario_data: dict[str, Any], *, source_path: str) -> CompiledScenario:
        validate_scenario_compiler_shape(
            raw_scenario_data,
            source_path=source_path,
        )
        merged, imported_files, warnings = _compile_merged_scenario_data(
            raw_scenario_data,
            project_root=REPO_ROOT,
        )
        ingestion = ingest_projection_setup_payloads_into_scenario(merged)
        if not ingestion.valid:
            message = ingestion.errors[0] if ingestion.errors else ingestion.rejection_reason
            raise ValueError(
                f"environment substrate projection ingestion failed "
                f"({ingestion.rejection_reason}): {message}"
            )
        if ingestion.scenario_data is not None:
            merged = ingestion.scenario_data
        validate_scenario_compiler_shape(
            merged,
            source_path=source_path,
            context="merged scenario",
        )
        for line in warnings:
            print(line)

        env_cfg = merged.get("environment", {})
        zones = env_cfg.get("zones", [])
        entities = merged.get("entities", [])
        rewards_cfg = merged.get("rewards", {})
        task_cfg = merged.get("task_order", {})
        mission_cmd_template = _normalize_runtime_mission_command(merged.get("mission_command", {}), task_cfg)
        normalized_route_waypoints = materialize_runtime_waypoint_cache(mission_cmd_template)
        normalized_waypoint_templates = _compile_normalized_waypoint_templates(mission_cmd_template)
        compiled_conditional_objectives = _compile_conditional_objectives(merged.get("objectives", []))
        runtime_metadata = CompiledScenarioRuntimeMetadata(
            mission_command_template=mission_cmd_template,
            rewards_config=_clone_scenario_value(rewards_cfg),
            meta_config=_clone_scenario_value(merged.get("meta", {})) if isinstance(merged.get("meta", {}), dict) else {},
            normalized_route_waypoints=tuple(_clone_scenario_value(normalized_route_waypoints)),
            normalized_waypoint_templates=normalized_waypoint_templates,
            waypoint_template_route_ref_ids=_compile_waypoint_template_route_ref_ids(normalized_waypoint_templates),
            compiled_conditional_objectives=compiled_conditional_objectives,
            objective_shaping_cfg=_build_objective_shaping_config(
                rewards_cfg,
                required=bool(compiled_conditional_objectives),
            ),
            ils_beacon_templates=tuple(_clone_scenario_value(_extract_ils_beacons(env_cfg))),
            waypoint_mode_configs={
                "flyby": _build_waypoint_mode_reward_config(rewards_cfg, mode="flyby"),
                "flyover": _build_waypoint_mode_reward_config(rewards_cfg, mode="flyover"),
            },
            approach_reward_config=_build_approach_reward_config(rewards_cfg),
            safety_reward_config=_build_safety_reward_config(rewards_cfg),
            lnav_config=_build_lnav_runtime_config(mission_cmd_template),
            layout_template=_compile_world_layout_template(merged),
        )

        dependency_mtimes_ns: list[tuple[str, int]] = []
        if source_path != "<inline>":
            dependency_mtimes_ns.append((source_path, _mtime_ns(source_path)))
        for imported_path in imported_files:
            dependency_mtimes_ns.append((imported_path, _mtime_ns(imported_path)))

        scenario_name = str(merged.get("scenario_name", os.path.basename(source_path))).strip() or os.path.basename(source_path)
        return CompiledScenario(
            source_path=source_path,
            scenario_name=scenario_name,
            merged_scenario_data=merged,
            runtime_metadata=runtime_metadata,
            imported_files=imported_files,
            dependency_mtimes_ns=tuple(dependency_mtimes_ns),
            warnings=warnings,
            zone_count=len(zones),
            entity_count=len(entities),
        )


# Cached compiled metadata may own nanobind-backed runtime DTOs.  Release the
# cache while extension types are still alive instead of relying on arbitrary
# interpreter module-destruction order.
atexit.register(ScenarioCompiler.clear_cache)


__all__ = [
    "WaypointModeRewardConfig",
    "ApproachRewardConfig",
    "SafetyRewardConfig",
    "LNavRuntimeConfig",
    "CompiledWorldLayoutTemplate",
    "CompiledScenarioRuntimeMetadata",
    "CompiledScenario",
    "ScenarioCompiler",
]
