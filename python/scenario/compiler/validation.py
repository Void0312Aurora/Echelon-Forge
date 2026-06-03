from __future__ import annotations

from typing import Any


def _format_source(source_path: str) -> str:
    return source_path or "<unknown>"


def _require_optional_dict(
    scenario_data: dict[str, Any],
    field_name: str,
    *,
    context: str,
    source_path: str,
) -> None:
    if field_name in scenario_data and not isinstance(scenario_data[field_name], dict):
        raise ValueError(
            f"{context} {field_name!r} must be an object: {_format_source(source_path)}"
        )


def _require_optional_list(
    scenario_data: dict[str, Any],
    field_name: str,
    *,
    context: str,
    source_path: str,
) -> None:
    if field_name in scenario_data and not isinstance(scenario_data[field_name], list):
        raise ValueError(
            f"{context} {field_name!r} must be a list: {_format_source(source_path)}"
        )


def _require_object_entries(
    values: list[Any],
    field_name: str,
    *,
    context: str,
    source_path: str,
) -> None:
    for index, value in enumerate(values):
        if not isinstance(value, dict):
            raise ValueError(
                f"{context} {field_name}[{index}] must be an object: "
                f"{_format_source(source_path)}"
            )


def validate_scenario_compiler_shape(
    scenario_data: dict[str, Any],
    *,
    source_path: str,
    context: str = "scenario",
) -> None:
    """Validate only the shapes the compiler consumes directly."""
    if not isinstance(scenario_data, dict):
        raise ValueError(
            f"{context} must be a JSON object: {_format_source(source_path)}"
        )

    for field_name in ("environment", "mission_command", "rewards", "task_order", "meta"):
        _require_optional_dict(
            scenario_data,
            field_name,
            context=context,
            source_path=source_path,
        )

    for field_name in ("imports", "entities", "objectives", "zones"):
        _require_optional_list(
            scenario_data,
            field_name,
            context=context,
            source_path=source_path,
        )

    entities = scenario_data.get("entities", [])
    if isinstance(entities, list):
        _require_object_entries(
            entities,
            "entities",
            context=context,
            source_path=source_path,
        )

    imports = scenario_data.get("imports", [])
    if isinstance(imports, list):
        _require_object_entries(
            imports,
            "imports",
            context=context,
            source_path=source_path,
        )

    zones = scenario_data.get("zones", [])
    if isinstance(zones, list):
        _require_object_entries(
            zones,
            "zones",
            context=context,
            source_path=source_path,
        )

    env_cfg = scenario_data.get("environment", {})
    if isinstance(env_cfg, dict):
        env_zones = env_cfg.get("zones", [])
        if "zones" in env_cfg and not isinstance(env_zones, list):
            raise ValueError(
                f"{context} 'environment.zones' must be a list: "
                f"{_format_source(source_path)}"
            )
        if isinstance(env_zones, list):
            _require_object_entries(
                env_zones,
                "environment.zones",
                context=context,
                source_path=source_path,
            )


__all__ = [
    "validate_scenario_compiler_shape",
]
