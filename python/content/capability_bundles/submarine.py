"""Submarine-family pilot: content capability bundle -> typed platform request.

The submarine family is the T11 pilot's bounded platform family (this
iteration): it is the smallest family with a complete definition set (one
maintained definition, ``Kilo_Class_MVP``), and I74 just table-drove its
platform-field parse seam, so its content surface is freshly pinned.

Importing this module is the opt-in: it registers the ``submarine`` family
expander on the default registry (G5 registration socket). The maintained
default path never imports it.

Two responsibilities live here:

1. ``expand_submarine_family_bundle`` -- expand a validated bundle document
   into an ``ExpandedTypedPlatformRequest`` with maintained-typed-setup
   semantics (``typed_platform_request`` + ``resolved_spawn_plan_bridge``,
   ``type_name_projection_preserved`` false on request, bundle, and plan).
2. ``derive_submarine_capability_bundle_facts`` -- the bounded, pure-JSON
   re-derivation of the capability set the runtime factory
   (``DefaultUnitFactory::build_platform_capability_bundle_template``) would
   project from the reference unit definition. The parity fixture test uses
   it to prove the content document and the reference definition agree
   field-for-field at the UnitDefinition level during the compatibility
   window. It fails closed on any seam outside the bounded submarine
   surface, keeping the pilot honestly bounded to one platform family.

Standard library only; no ``ef_py`` import.
"""

from __future__ import annotations

import re
from typing import Any, List, Mapping, Tuple

from python.content.capability_bundles.registry import (
    RESOLVED_SPAWN_PLAN_BRIDGE_STRATEGY,
    FACADE_EVIDENCE_TYPED_PLATFORM_SPAWN_REQUESTS,
    TYPED_PLATFORM_REQUEST_KIND,
    ExpandedCapability,
    ExpandedCapabilityBundle,
    ExpandedResolvedSpawnPlan,
    ExpandedTypedPlatformRequest,
    SpawnPlacement,
    register_capability_bundle_family,
)

SUBMARINE_PLATFORM_FAMILY = "submarine"

# Top-level unit-definition keys the bounded submarine derivation understands.
# Keys in _CAPABILITY_SEAM_KEYS map onto factory capability seams; keys in
# _NEUTRAL_KEYS carry no capability seam of their own. Anything else is an
# out-of-family seam and the derivation fails closed (bounded pilot).
_CAPABILITY_SEAM_KEYS = frozenset(
    {
        "sensor_refs",
        "sensor_ref",
        "sensor",
        "has_sensor",
        "mounted_sensors",
        "sonar",
        "mounted_sonars",
        "ship_platform",
        "submarine_platform",
        "naval_stores",
        "naval_logistics",
        "naval_weapon_system",
        "embarked_air_ops",
        "default_loadout",
        "has_command_link",
        "command_link",
        "has_data_link",
        "data_link_network_id",
        "health",
        "damage_model",
    }
)
_NEUTRAL_KEYS = frozenset({"name", "type", "mass_kg"})


def _platform_token(value: str) -> str:
    """Mirror ``default_unit_factory_detail::make_platform_token``."""

    token = re.sub(r"[^0-9A-Za-z]+", "_", value).strip("_").lower()
    return token or "unnamed"


def make_bundle_id(type_name: str) -> str:
    return f"platform.bundle.{_platform_token(type_name)}"


def make_capability_id(type_name: str, capability_type: str) -> str:
    return (
        f"platform.capability.{_platform_token(type_name)}."
        f"{_platform_token(capability_type)}"
    )


def make_evidence_ref(type_name: str, evidence_type: str) -> str:
    return (
        f"platform.evidence.{_platform_token(type_name)}."
        f"{_platform_token(evidence_type)}"
    )


def make_definition_ref(type_name: str) -> str:
    return f"platform.definition.{_platform_token(type_name)}"


def derive_submarine_capability_bundle_facts(
    definition: Mapping[str, Any],
) -> List[Tuple[str, str, Tuple[str, ...]]]:
    """Derive ``(family, capability_type, evidence_types)`` facts, in factory order.

    Pure-JSON mirror of the bounded-submarine slice of
    ``DefaultUnitFactory::build_platform_capability_bundle_template``. Raises
    ``ValueError`` (fail-closed) when the definition is not a Submarine or
    carries a seam outside the bounded submarine surface.
    """

    if definition.get("type") != "Submarine":
        raise ValueError(
            "bounded submarine derivation requires a Submarine definition, got "
            f"{definition.get('type')!r}"
        )
    unexpected = [
        key
        for key in definition
        if not key.startswith("_")
        and key not in _CAPABILITY_SEAM_KEYS
        and key not in _NEUTRAL_KEYS
    ]
    if unexpected:
        raise ValueError(
            "definition carries seams outside the bounded submarine pilot "
            f"surface: {sorted(unexpected)!r}"
        )

    facts: List[Tuple[str, str, Tuple[str, ...]]] = []

    sensor_refs = definition.get("sensor_refs")
    # Match unit_definition_loader.cpp: presence of an array selects this
    # branch, even when the array is empty. Non-array values fall through to
    # the inline-sensor branch below.
    has_sensor_refs_branch = "sensor_refs" in definition and isinstance(sensor_refs, list)
    sensor_ref_values = (
        tuple(value for value in sensor_refs if isinstance(value, str))
        if has_sensor_refs_branch
        else ()
    )
    if sensor_ref_values:
        facts.append(("sensing", "sensor_refs", ("sensor_refs", "sensor_ref")))
    if str(definition.get("sensor_ref") or ""):
        facts.append(("sensing", "sensor_ref", ("sensor_ref",)))
    # Loader chain: sensor_refs / inline sensor / has_sensor are a mutually
    # exclusive if/else-if chain, so an inline sensor only sets the flag when
    # sensor_refs is absent or non-array (t11 schema survey, family SEN).
    has_inline_sensor = not has_sensor_refs_branch and (
        isinstance(definition.get("sensor"), Mapping) or bool(definition.get("has_sensor"))
    )
    if has_inline_sensor:
        facts.append(("sensing", "inline_sensor", ("sensor_inline", "sensor")))
    if definition.get("mounted_sensors"):
        facts.append(("sensing", "mounted_sensors", ("mounted_sensors",)))
    if isinstance(definition.get("sonar"), Mapping):
        facts.append(("sensing", "sonar", ("sonar",)))
    if definition.get("mounted_sonars"):
        facts.append(("sensing", "mounted_sonars", ("mounted_sonars",)))

    has_ship_platform = isinstance(definition.get("ship_platform"), Mapping)
    has_submarine_platform = isinstance(definition.get("submarine_platform"), Mapping)
    if has_ship_platform:
        facts.append(("mobility", "ship_platform_mobility", ("ship_platform", "mobility")))
        facts.append(
            ("survivability", "ship_platform_survivability", ("ship_platform", "survivability"))
        )
    if has_submarine_platform:
        facts.append(
            ("mobility", "submarine_platform_mobility", ("submarine_platform", "mobility"))
        )
        facts.append(
            (
                "survivability",
                "submarine_platform_survivability",
                ("submarine_platform", "survivability"),
            )
        )

    if isinstance(definition.get("naval_stores"), Mapping):
        facts.append(("survivability", "naval_stores", ("naval_stores",)))
    has_naval_weapon_system = isinstance(definition.get("naval_weapon_system"), Mapping)
    if has_naval_weapon_system:
        facts.append(("launching", "naval_weapon_system", ("naval_weapon_system",)))
    if definition.get("default_loadout"):
        facts.append(("launching", "default_loadout", ("default_loadout",)))

    has_command_link = bool(definition.get("has_command_link")) or isinstance(
        definition.get("command_link"), Mapping
    )
    if has_command_link:
        facts.append(("command", "command_link", ("command_link",)))
    if definition.get("has_data_link"):
        facts.append(("communication", "data_link", ("data_link", "data_link_network_id")))
    if isinstance(definition.get("embarked_air_ops"), Mapping):
        facts.append(("doctrine", "embarked_air_ops", ("embarked_air_ops",)))

    if has_ship_platform or has_submarine_platform or has_naval_weapon_system:
        facts.append(
            (
                "doctrine",
                "naval_platform_doctrine",
                ("naval_platform_doctrine", "naval_weapon_system"),
            )
        )

    damage_model = definition.get("damage_model")
    has_hitboxes = isinstance(damage_model, Mapping) and bool(damage_model.get("hitboxes"))
    health = definition.get("health")
    has_positive_hp = isinstance(health, Mapping) and float(health.get("current_hp", 0.0)) > 0.0
    if has_hitboxes or has_positive_hp:
        facts.append(
            ("survivability", "health_and_damage_model", ("health", "damage_model"))
        )

    return facts


def _expanded_capabilities(
    document: Mapping[str, Any],
) -> Tuple[ExpandedCapability, ...]:
    capabilities = []
    for entry in document["capabilities"]:
        capabilities.append(
            ExpandedCapability(
                capability_id=str(entry["capability_id"]),
                family=str(entry["family"]),
                capability_type=str(entry["capability_type"]),
                implementation_ref=str(entry.get("implementation_ref", "")),
                evidence_refs=tuple(entry["evidence_refs"]),
                required=entry.get("required", True),
                supported=entry.get("supported", True),
                unsupported_reason=entry.get("unsupported_reason", ""),
            )
        )
    return tuple(capabilities)


def expand_submarine_family_bundle(
    document: Mapping[str, Any],
    request_id: str,
    placement: SpawnPlacement,
) -> ExpandedTypedPlatformRequest:
    """Expand a validated submarine bundle document (maintained typed setup).

    The output carries ``typed_platform_request`` +
    ``resolved_spawn_plan_bridge`` with ``type_name_projection_preserved``
    false on request, bundle, and plan: the runtime classifies that as the
    ``maintained_typed_setup`` surface, the genuine opt-in
    ``typed_platform_request`` entry (not the projection bridge).
    """

    source_type_name = str(document["source_type_name"])
    capabilities = _expanded_capabilities(document)
    bundle = ExpandedCapabilityBundle(
        bundle_id=str(document["bundle_id"]),
        source_type_name=source_type_name,
        capabilities=capabilities,
        template_evidence_ref=str(document["template_evidence_ref"]),
        evidence_refs=tuple(document["evidence_refs"]),
        type_name_projection_preserved=False,
        diagnostics_reason="content_capability_bundle_truth_source",
    )
    resolution_evidence_ref = f"content.resolution.{_platform_token(request_id)}"
    materialization_evidence_ref = f"content.materialization.{_platform_token(request_id)}"
    plan_evidence_refs = list(bundle.evidence_refs)
    for evidence_ref in (resolution_evidence_ref, materialization_evidence_ref):
        if evidence_ref not in plan_evidence_refs:
            plan_evidence_refs.append(evidence_ref)
    plan = ExpandedResolvedSpawnPlan(
        plan_id=f"content.plan.{_platform_token(source_type_name)}."
        f"{_platform_token(request_id)}",
        source_request_kind=TYPED_PLATFORM_REQUEST_KIND,
        source_type_name=source_type_name,
        capability_bundle_id=bundle.bundle_id,
        resolved_platform_definition_ref=str(document["definition_ref"]),
        materialization_strategy=RESOLVED_SPAWN_PLAN_BRIDGE_STRATEGY,
        template_evidence_ref=bundle.template_evidence_ref,
        resolution_evidence_ref=resolution_evidence_ref,
        materialization_evidence_ref=materialization_evidence_ref,
        evidence_refs=tuple(plan_evidence_refs),
        resolved_capabilities=capabilities,
        type_name_projection_preserved=False,
        admitted=True,
        diagnostics_reason="content_capability_bundle_to_resolved_spawn_plan",
    )
    return ExpandedTypedPlatformRequest(
        request_id=request_id,
        source_type_name=source_type_name,
        placement=placement,
        capability_bundle=bundle,
        resolved_spawn_plan=plan,
        facade_evidence_refs=(
            FACADE_EVIDENCE_TYPED_PLATFORM_SPAWN_REQUESTS,
            f"content.capability_bundle.{_platform_token(source_type_name)}",
        ),
        type_name_projection_preserved=False,
    )


register_capability_bundle_family(
    SUBMARINE_PLATFORM_FAMILY, expand_submarine_family_bundle
)
