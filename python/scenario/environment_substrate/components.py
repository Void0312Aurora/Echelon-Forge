from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable


ENVIRONMENT_SUBSTRATE_CONTRACT_VERSION = "environment_substrate.g0_j.static_manifest.v1"

BRANCH_MEMBERSHIP_ROLES = (
    "primary",
    "supporting",
    "context",
    "projectable",
    "metadata_only",
    "reserved_dynamic",
)

PROJECTION_TARGETS = (
    "terrain_type",
    "world_zone_definition",
    "world_wind_assignment",
    "runtime_maritime_setup",
    "manifest_only",
)

DROPPED_ATTRIBUTE_POLICIES = (
    "reject",
    "record",
    "omit_if_profile_allows",
)

HELD_CAPABILITY_CLAIMS = (
    "movement",
    "terrain_aware_movement",
    "passability",
    "line_of_sight",
    "los",
    "cover",
    "concealment",
    "fires",
    "damage",
    "combat",
    "weather_simulation",
    "hydrodynamics",
    "hydrology_effects",
    "dynamic_environment_mutation",
)


def _normalized_text(value: Any) -> str:
    return str(value or "").strip()


def _normalized_unique_texts(values: Iterable[Any]) -> tuple[str, ...]:
    seen: set[str] = set()
    normalized: list[str] = []
    for value in values:
        text = _normalized_text(value)
        if not text or text in seen:
            continue
        seen.add(text)
        normalized.append(text)
    return tuple(sorted(normalized))


@dataclass(frozen=True)
class EnvironmentBranchDescriptor:
    branch_id: str
    schema_version: str = "1"
    owner: str = "shared_environment_substrate"
    static_dynamic_status: str = "static_manifest"
    supported_geometry_types: tuple[str, ...] = ("rect", "polygon", "line", "point", "volume")
    allowed_components: tuple[str, ...] = ()
    projection_targets: tuple[str, ...] = ("manifest_only",)
    held_capabilities: tuple[str, ...] = HELD_CAPABILITY_CLAIMS

    def __post_init__(self) -> None:
        object.__setattr__(self, "branch_id", _normalized_text(self.branch_id))
        object.__setattr__(self, "schema_version", _normalized_text(self.schema_version))
        object.__setattr__(self, "owner", _normalized_text(self.owner))
        object.__setattr__(
            self,
            "static_dynamic_status",
            _normalized_text(self.static_dynamic_status),
        )
        object.__setattr__(
            self,
            "supported_geometry_types",
            _normalized_unique_texts(self.supported_geometry_types),
        )
        object.__setattr__(
            self,
            "allowed_components",
            _normalized_unique_texts(self.allowed_components),
        )
        object.__setattr__(
            self,
            "projection_targets",
            _normalized_unique_texts(self.projection_targets),
        )
        object.__setattr__(
            self,
            "held_capabilities",
            _normalized_unique_texts(self.held_capabilities),
        )

    def to_metadata(self) -> dict[str, Any]:
        return {
            "branch_id": self.branch_id,
            "schema_version": self.schema_version,
            "owner": self.owner,
            "static_dynamic_status": self.static_dynamic_status,
            "supported_geometry_types": list(self.supported_geometry_types),
            "allowed_components": list(self.allowed_components),
            "projection_targets": list(self.projection_targets),
            "held_capabilities": list(self.held_capabilities),
        }


@dataclass(frozen=True)
class EnvironmentComponentDescriptor:
    family: str
    schema_version: str = "1"
    required_attributes: tuple[str, ...] = ()
    consumer_tags: tuple[str, ...] = ()
    minimum_realism_grade: str = "G1"

    def __post_init__(self) -> None:
        object.__setattr__(self, "family", _normalized_text(self.family))
        object.__setattr__(self, "schema_version", _normalized_text(self.schema_version))
        object.__setattr__(
            self,
            "required_attributes",
            _normalized_unique_texts(self.required_attributes),
        )
        object.__setattr__(
            self,
            "consumer_tags",
            _normalized_unique_texts(self.consumer_tags),
        )
        object.__setattr__(
            self,
            "minimum_realism_grade",
            _normalized_text(self.minimum_realism_grade),
        )

    def to_metadata(self) -> dict[str, Any]:
        return {
            "family": self.family,
            "schema_version": self.schema_version,
            "required_attributes": list(self.required_attributes),
            "consumer_tags": list(self.consumer_tags),
            "minimum_realism_grade": self.minimum_realism_grade,
        }


@dataclass(frozen=True)
class EnvironmentLayerDescriptor:
    layer_id: str
    order_hint: int
    branch_ids: tuple[str, ...] = ()
    compatible_layers: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "layer_id", _normalized_text(self.layer_id))
        object.__setattr__(self, "order_hint", int(self.order_hint))
        object.__setattr__(self, "branch_ids", _normalized_unique_texts(self.branch_ids))
        object.__setattr__(
            self,
            "compatible_layers",
            _normalized_unique_texts(self.compatible_layers),
        )

    def to_metadata(self) -> dict[str, Any]:
        return {
            "layer_id": self.layer_id,
            "order_hint": int(self.order_hint),
            "branch_ids": list(self.branch_ids),
            "compatible_layers": list(self.compatible_layers),
        }


def default_component_registry() -> tuple[EnvironmentComponentDescriptor, ...]:
    return (
        EnvironmentComponentDescriptor(
            "surface_material",
            required_attributes=("surface",),
            consumer_tags=("terrain_projection",),
            minimum_realism_grade="G1",
        ),
        EnvironmentComponentDescriptor(
            "terrain_morphology",
            required_attributes=("confidence",),
            consumer_tags=("terrain_manifest",),
            minimum_realism_grade="G1",
        ),
        EnvironmentComponentDescriptor(
            "mobility_modifier",
            required_attributes=("actor_classes", "speed_multiplier"),
            consumer_tags=("movement_held",),
            minimum_realism_grade="G2",
        ),
        EnvironmentComponentDescriptor(
            "vegetation",
            required_attributes=("density", "species_group"),
            consumer_tags=("los_cover_held",),
            minimum_realism_grade="G3",
        ),
        EnvironmentComponentDescriptor(
            "structure",
            required_attributes=("footprint", "height_m", "material"),
            consumer_tags=("los_cover_damage_held",),
            minimum_realism_grade="G3",
        ),
        EnvironmentComponentDescriptor(
            "occlusion",
            required_attributes=("height_m", "opacity"),
            consumer_tags=("los_held",),
            minimum_realism_grade="G4",
        ),
        EnvironmentComponentDescriptor(
            "cover_concealment",
            required_attributes=("cover_class", "concealment_factor"),
            consumer_tags=("cover_fires_held",),
            minimum_realism_grade="G5",
        ),
        EnvironmentComponentDescriptor(
            "network",
            required_attributes=("width_m", "connectivity", "surface_class"),
            consumer_tags=("route_graph_held",),
            minimum_realism_grade="G2",
        ),
        EnvironmentComponentDescriptor(
            "hydrology",
            required_attributes=("state",),
            consumer_tags=("hydrology_held",),
            minimum_realism_grade="G2",
        ),
        EnvironmentComponentDescriptor(
            "atmospheric_profile",
            required_attributes=("temperature_c", "pressure_pa"),
            consumer_tags=("weather_manifest",),
            minimum_realism_grade="G1",
        ),
        EnvironmentComponentDescriptor(
            "weather_effect",
            required_attributes=("phenomenon", "visibility_m"),
            consumer_tags=("weather_held",),
            minimum_realism_grade="G4",
        ),
        EnvironmentComponentDescriptor(
            "wind_field",
            required_attributes=("direction_from_deg", "speed_mps"),
            consumer_tags=("wind_projection",),
            minimum_realism_grade="G1",
        ),
        EnvironmentComponentDescriptor(
            "illumination",
            required_attributes=("sun_vector",),
            consumer_tags=("illumination_manifest",),
            minimum_realism_grade="G1",
        ),
        EnvironmentComponentDescriptor(
            "maritime_state",
            required_attributes=("sea_state",),
            consumer_tags=("maritime_projection",),
            minimum_realism_grade="G1",
        ),
        EnvironmentComponentDescriptor(
            "hazard",
            required_attributes=("hazard_kind",),
            consumer_tags=("effects_held",),
            minimum_realism_grade="G5",
        ),
        EnvironmentComponentDescriptor(
            "tactical_semantic",
            required_attributes=("semantic_type",),
            consumer_tags=("tasking_reference",),
            minimum_realism_grade="G1",
        ),
        EnvironmentComponentDescriptor(
            "ownership_control",
            required_attributes=("side",),
            consumer_tags=("tasking_reference",),
            minimum_realism_grade="G1",
        ),
        EnvironmentComponentDescriptor(
            "damageable",
            required_attributes=("health_class",),
            consumer_tags=("damage_held",),
            minimum_realism_grade="G6",
        ),
    )


def default_branch_registry() -> tuple[EnvironmentBranchDescriptor, ...]:
    terrain_components = (
        "surface_material",
        "terrain_morphology",
        "mobility_modifier",
        "vegetation",
        "structure",
        "occlusion",
        "cover_concealment",
        "network",
        "hydrology",
        "hazard",
        "tactical_semantic",
        "ownership_control",
        "damageable",
    )
    return (
        EnvironmentBranchDescriptor(
            "terrain",
            allowed_components=terrain_components,
            projection_targets=("terrain_type", "world_zone_definition", "manifest_only"),
        ),
        EnvironmentBranchDescriptor(
            "atmosphere_weather",
            allowed_components=("atmospheric_profile", "weather_effect"),
            projection_targets=("manifest_only",),
            held_capabilities=("weather_simulation", "line_of_sight"),
        ),
        EnvironmentBranchDescriptor(
            "wind_field",
            allowed_components=("wind_field", "atmospheric_profile"),
            projection_targets=("world_wind_assignment", "manifest_only"),
            held_capabilities=("weather_simulation", "dynamic_environment_mutation"),
        ),
        EnvironmentBranchDescriptor(
            "illumination",
            allowed_components=("illumination",),
            projection_targets=("manifest_only",),
            held_capabilities=("line_of_sight",),
        ),
        EnvironmentBranchDescriptor(
            "maritime_ocean",
            allowed_components=("maritime_state", "weather_effect"),
            projection_targets=("runtime_maritime_setup", "manifest_only"),
            held_capabilities=("hydrodynamics",),
        ),
        EnvironmentBranchDescriptor(
            "hydrology",
            allowed_components=("hydrology", "surface_material", "mobility_modifier"),
            projection_targets=("world_zone_definition", "manifest_only"),
            held_capabilities=("hydrology_effects", "movement"),
        ),
        EnvironmentBranchDescriptor(
            "dynamic_environment",
            static_dynamic_status="reserved_dynamic",
            allowed_components=("hazard", "damageable", "ownership_control"),
            projection_targets=("manifest_only",),
            held_capabilities=("dynamic_environment_mutation", "damage", "combat"),
        ),
    )


def default_layer_registry() -> tuple[EnvironmentLayerDescriptor, ...]:
    return (
        EnvironmentLayerDescriptor("physical_base", 10, branch_ids=("terrain",)),
        EnvironmentLayerDescriptor("terrain_surface", 20, branch_ids=("terrain",)),
        EnvironmentLayerDescriptor("hydrology", 30, branch_ids=("terrain", "hydrology")),
        EnvironmentLayerDescriptor("atmosphere_weather", 35, branch_ids=("atmosphere_weather",)),
        EnvironmentLayerDescriptor("wind_field", 36, branch_ids=("wind_field",)),
        EnvironmentLayerDescriptor("illumination", 37, branch_ids=("illumination",)),
        EnvironmentLayerDescriptor("maritime_ocean", 38, branch_ids=("maritime_ocean",)),
        EnvironmentLayerDescriptor("vegetation", 40, branch_ids=("terrain",)),
        EnvironmentLayerDescriptor("built_structure", 50, branch_ids=("terrain",)),
        EnvironmentLayerDescriptor("infrastructure_network", 60, branch_ids=("terrain",)),
        EnvironmentLayerDescriptor("tactical_semantic", 70, branch_ids=("terrain",)),
        EnvironmentLayerDescriptor("hazard_control_overlay", 80, branch_ids=("terrain", "dynamic_environment")),
        EnvironmentLayerDescriptor("dynamic_state_overlay", 90, branch_ids=("dynamic_environment",)),
    )


DEFAULT_BRANCH_IDS = tuple(branch.branch_id for branch in default_branch_registry())
DEFAULT_COMPONENT_FAMILIES = tuple(component.family for component in default_component_registry())
DEFAULT_LAYER_IDS = tuple(layer.layer_id for layer in default_layer_registry())


__all__ = [
    "BRANCH_MEMBERSHIP_ROLES",
    "DEFAULT_BRANCH_IDS",
    "DEFAULT_COMPONENT_FAMILIES",
    "DEFAULT_LAYER_IDS",
    "DROPPED_ATTRIBUTE_POLICIES",
    "ENVIRONMENT_SUBSTRATE_CONTRACT_VERSION",
    "HELD_CAPABILITY_CLAIMS",
    "PROJECTION_TARGETS",
    "EnvironmentBranchDescriptor",
    "EnvironmentComponentDescriptor",
    "EnvironmentLayerDescriptor",
    "default_branch_registry",
    "default_component_registry",
    "default_layer_registry",
]
