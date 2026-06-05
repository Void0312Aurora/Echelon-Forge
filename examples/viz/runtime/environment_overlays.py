from __future__ import annotations

import math
from copy import deepcopy
from typing import Any, Mapping


ENVIRONMENT_OVERLAY_CONTRACT_VERSION = "examples.viz.environment_overlays.g0_viz_a.v1"

_ACCEPTED_DERIVED_PRODUCT_KINDS = {
    "surface_zone_index",
    "occlusion_candidate_index",
}


def _clone(value: Any) -> Any:
    return deepcopy(value)


def _finite_float(value: Any) -> float | None:
    try:
        coerced = float(value)
    except Exception:
        return None
    if not math.isfinite(coerced):
        return None
    return coerced


def _normalized_text(value: Any) -> str:
    return str(value or "").strip()


def _rect_geometry(source: Mapping[str, Any]) -> dict[str, float] | None:
    numbers: dict[str, float] = {}
    for key in ("x", "y", "width", "length"):
        value = _finite_float(source.get(key))
        if value is None:
            return None
        numbers[key] = value
    heading = _finite_float(source.get("heading", 0.0))
    if heading is None or numbers["width"] <= 0.0 or numbers["length"] <= 0.0:
        return None
    numbers["heading"] = heading
    return numbers


def _aabb_geometry(source: Mapping[str, Any]) -> dict[str, float] | None:
    numbers: dict[str, float] = {}
    for key in ("min_x", "min_y", "max_x", "max_y"):
        value = _finite_float(source.get(key))
        if value is None:
            return None
        numbers[key] = value
    if numbers["max_x"] <= numbers["min_x"] or numbers["max_y"] <= numbers["min_y"]:
        return None
    return numbers


def _surface_zone_from_zone(zone: Mapping[str, Any], *, index: int) -> dict[str, Any] | None:
    geometry = _rect_geometry(zone)
    if geometry is None:
        return None
    label = _normalized_text(zone.get("name")) or f"zone_{index}"
    return {
        "overlay_id": f"environment.zone.{index}",
        "overlay_kind": "surface_zone",
        "label": label,
        "geometry": {"geometry_type": "rect", **geometry},
        "attributes": {
            "surface": _normalized_text(zone.get("surface")) or "Unknown",
            "source": "environment.zones",
            "zone_index": int(index),
        },
        "evidence": {
            "runtime_consumer_release": False,
            "no_runtime_setup_application": True,
            "no_held_capability_release": True,
        },
    }


def _surface_zone_from_index_entry(
    entry: Mapping[str, Any],
    *,
    index: int,
) -> dict[str, Any] | None:
    rect = entry.get("rect")
    if not isinstance(rect, Mapping):
        return None
    geometry = _rect_geometry(rect)
    if geometry is None:
        return None
    source_object_id = _normalized_text(entry.get("source_object_id"))
    label = _normalized_text(entry.get("zone_name")) or source_object_id or f"surface_{index}"
    return {
        "overlay_id": f"environment.surface_zone_index.{index}",
        "overlay_kind": "surface_zone",
        "label": label,
        "geometry": {"geometry_type": "rect", **geometry},
        "attributes": {
            "surface": _normalized_text(entry.get("surface")) or "Unknown",
            "source": "g0_m.surface_zone_index",
            "source_object_id": source_object_id,
            "product_entry_index": int(index),
        },
        "evidence": {
            "runtime_consumer_release": False,
            "no_runtime_consumer_release": True,
            "no_held_capability_release": True,
        },
    }


def _occlusion_candidate_from_index_entry(
    entry: Mapping[str, Any],
    *,
    index: int,
) -> dict[str, Any] | None:
    bounds = entry.get("bounds")
    if not isinstance(bounds, Mapping):
        return None
    bounds_kind = _normalized_text(entry.get("bounds_kind"))
    if bounds_kind == "rect":
        geometry_values = _rect_geometry(bounds)
        geometry_type = "rect"
    else:
        geometry_values = _aabb_geometry(bounds)
        geometry_type = "aabb"
    if geometry_values is None:
        return None
    source_object_id = _normalized_text(entry.get("source_object_id"))
    component_family = _normalized_text(entry.get("component_family")) or "candidate"
    attributes: dict[str, Any] = {
        "source": "g0_m.occlusion_candidate_index",
        "source_object_id": source_object_id,
        "catalog_ref": _normalized_text(entry.get("catalog_ref")),
        "component_family": component_family,
        "component_id": _normalized_text(entry.get("component_id")),
        "layer_membership": list(entry.get("layer_membership", []))
        if isinstance(entry.get("layer_membership"), list)
        else [],
        "product_entry_index": int(index),
    }
    height_m = _finite_float(entry.get("height_m"))
    opacity = _finite_float(entry.get("opacity"))
    if height_m is not None:
        attributes["height_m"] = height_m
    if opacity is not None:
        attributes["opacity"] = opacity
    return {
        "overlay_id": f"environment.occlusion_candidate_index.{index}",
        "overlay_kind": "occlusion_candidate",
        "label": source_object_id or f"{component_family}_{index}",
        "geometry": {"geometry_type": geometry_type, **geometry_values},
        "attributes": attributes,
        "evidence": {
            "runtime_consumer_release": False,
            "no_los_runtime_release": True,
            "no_cover_runtime_release": True,
            "no_held_capability_release": True,
        },
    }


def _derived_product_bundles(env_cfg: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    substrate_cfg = env_cfg.get("environment_substrate", {})
    if not isinstance(substrate_cfg, Mapping):
        return []
    candidates = [
        substrate_cfg.get("derived_product_bundle"),
        substrate_cfg.get("derived_products_bundle"),
        substrate_cfg.get("derived_product_result"),
    ]
    bundles: list[Mapping[str, Any]] = []
    for candidate in candidates:
        if not isinstance(candidate, Mapping):
            continue
        bundle = candidate.get("bundle") if isinstance(candidate.get("bundle"), Mapping) else candidate
        if isinstance(bundle, Mapping):
            bundles.append(bundle)
    return bundles


def _derived_product_layers(
    env_cfg: Mapping[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    layers_by_id: dict[str, dict[str, Any]] = {}
    skipped_products: list[dict[str, Any]] = []
    for bundle in _derived_product_bundles(env_cfg):
        products = bundle.get("products", [])
        if not isinstance(products, list):
            continue
        for product in products:
            if not isinstance(product, Mapping):
                continue
            product_kind = _normalized_text(product.get("product_kind"))
            if product_kind not in _ACCEPTED_DERIVED_PRODUCT_KINDS:
                if product_kind:
                    skipped_products.append(
                        {
                            "product_kind": product_kind,
                            "reason": "not_released_for_g0_viz_overlay",
                        }
                    )
                continue
            entries = product.get("entries", [])
            if not isinstance(entries, list):
                continue
            if product_kind == "surface_zone_index":
                layer_id = "surface_zone_index"
                layer = layers_by_id.setdefault(
                    layer_id,
                    {
                        "layer_id": layer_id,
                        "overlay_kind": "surface_zone",
                        "source": "g0_m.surface_zone_index",
                        "entries": [],
                        "evidence": {
                            "no_runtime_consumer_release": True,
                            "no_held_capability_release": True,
                        },
                    },
                )
                for index, entry in enumerate(entries):
                    if isinstance(entry, Mapping):
                        overlay = _surface_zone_from_index_entry(entry, index=index)
                        if overlay is not None:
                            layer["entries"].append(overlay)
            elif product_kind == "occlusion_candidate_index":
                layer_id = "occlusion_candidate_index"
                layer = layers_by_id.setdefault(
                    layer_id,
                    {
                        "layer_id": layer_id,
                        "overlay_kind": "occlusion_candidate",
                        "source": "g0_m.occlusion_candidate_index",
                        "entries": [],
                        "evidence": {
                            "no_los_runtime_release": True,
                            "no_cover_runtime_release": True,
                            "no_held_capability_release": True,
                        },
                    },
                )
                for index, entry in enumerate(entries):
                    if isinstance(entry, Mapping):
                        overlay = _occlusion_candidate_from_index_entry(entry, index=index)
                        if overlay is not None:
                            layer["entries"].append(overlay)
    return (
        [layer for layer in layers_by_id.values() if layer.get("entries")],
        skipped_products,
    )


def build_environment_overlay_payload(scenario_data: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(scenario_data, Mapping):
        raise TypeError("scenario_data must be a mapping")
    env_cfg = scenario_data.get("environment", {})
    if not isinstance(env_cfg, Mapping):
        env_cfg = {}

    zones = env_cfg.get("zones", [])
    surface_entries = []
    if isinstance(zones, list):
        for index, zone in enumerate(zones):
            if isinstance(zone, Mapping):
                entry = _surface_zone_from_zone(zone, index=index)
                if entry is not None:
                    surface_entries.append(entry)

    layers: list[dict[str, Any]] = []
    if surface_entries:
        layers.append(
            {
                "layer_id": "scenario_environment_zones",
                "overlay_kind": "surface_zone",
                "source": "environment.zones",
                "entries": surface_entries,
                "evidence": {
                    "no_runtime_setup_application": True,
                    "no_runtime_consumer_release": True,
                    "no_held_capability_release": True,
                },
            }
        )

    derived_layers, skipped_products = _derived_product_layers(env_cfg)
    layers.extend(derived_layers)

    return {
        "contract_version": ENVIRONMENT_OVERLAY_CONTRACT_VERSION,
        "layers": _clone(layers),
        "skipped_products": skipped_products,
        "evidence": {
            "source": "scenario.environment",
            "no_runtime_setup_application": True,
            "no_runtime_consumer_release": True,
            "no_movement_release": True,
            "no_los_cover_release": True,
            "no_held_capability_release": True,
        },
    }


__all__ = [
    "ENVIRONMENT_OVERLAY_CONTRACT_VERSION",
    "build_environment_overlay_payload",
]
