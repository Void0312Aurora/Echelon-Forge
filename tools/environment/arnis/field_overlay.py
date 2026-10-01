"""Build a provenance-preserving, metadata-only field training overlay.

Arnis phase 1 exports roads, buildings, hydrology, DEM, and landcover.  This
small companion tool keeps the source tags that are useful to a future ground
passability/observation owner (farmland, tree belts, settlement anchors, and
bridge crossings) without pretending that they are already runtime semantics.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Iterable


FIELD_OVERLAY_CONTRACT_VERSION = "field_overlay.v1"
_EARTH_RADIUS_M = 6_378_137.0
_KNOWN_TAGS = (
    "bridge",
    "building",
    "building:levels",
    "crop",
    "highway",
    "landuse",
    "layer",
    "name",
    "natural",
    "place",
    "surface",
    "tree_line",
    "water",
    "waterway",
    "width",
)


class FieldOverlayError(ValueError):
    """Raised when a source cannot produce a safe deterministic overlay."""


def _finite(value: Any, label: str) -> float:
    if isinstance(value, bool):
        raise FieldOverlayError(f"{label} must be numeric")
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise FieldOverlayError(f"{label} must be numeric") from exc
    if not math.isfinite(result):
        raise FieldOverlayError(f"{label} must be finite")
    return result


def _load_source(path: Path) -> tuple[dict[str, Any], str, int]:
    try:
        raw = path.read_bytes()
        payload = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise FieldOverlayError(f"failed to read synthetic OSM source {path}: {exc}") from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("elements"), list):
        raise FieldOverlayError("source must be an object with an elements list")
    return payload, hashlib.sha256(raw).hexdigest(), len(raw)


def _bbox_values(bbox: dict[str, Any]) -> tuple[float, float, float, float]:
    if not isinstance(bbox, dict):
        raise FieldOverlayError("bbox must be an object")
    min_lat = _finite(bbox.get("min_lat"), "bbox.min_lat")
    min_lon = _finite(bbox.get("min_lon"), "bbox.min_lon")
    max_lat = _finite(bbox.get("max_lat"), "bbox.max_lat")
    max_lon = _finite(bbox.get("max_lon"), "bbox.max_lon")
    if not (-90.0 <= min_lat < max_lat <= 90.0):
        raise FieldOverlayError("bbox latitude range is invalid")
    if not (-180.0 <= min_lon < max_lon <= 180.0):
        raise FieldOverlayError("bbox longitude range is invalid")
    return min_lat, min_lon, max_lat, max_lon


def _project(lat: Any, lon: Any, bbox: tuple[float, float, float, float]) -> list[float]:
    min_lat, min_lon, _max_lat, _max_lon = bbox
    latitude = _finite(lat, "node.lat")
    longitude = _finite(lon, "node.lon")
    mid_lat = (bbox[0] + bbox[2]) * 0.5
    cos_lat = max(math.cos(math.radians(mid_lat)), 1e-6)
    x = math.radians(longitude - min_lon) * _EARTH_RADIUS_M * cos_lat
    y = math.radians(latitude - min_lat) * _EARTH_RADIUS_M
    return [round(x, 6), round(y, 6)]


def _tags(element: dict[str, Any]) -> dict[str, str]:
    raw = element.get("tags", {})
    if not isinstance(raw, dict):
        return {}
    return {
        key: str(raw[key])
        for key in _KNOWN_TAGS
        if key in raw and raw[key] is not None and str(raw[key]).strip()
    }


def _geometry(
    element: dict[str, Any],
    nodes: dict[int, dict[str, Any]],
    bbox: tuple[float, float, float, float],
) -> dict[str, Any] | None:
    element_type = element.get("type")
    if element_type == "node":
        return {
            "geometry_type": "point",
            "point": _project(element.get("lat"), element.get("lon"), bbox),
        }
    if element_type != "way":
        return None
    refs = element.get("nodes")
    if not isinstance(refs, list) or len(refs) < 2:
        return None
    points: list[list[float]] = []
    for ref in refs:
        if type(ref) is not int or ref not in nodes:
            raise FieldOverlayError(f"way {element.get('id')!r} references missing node {ref!r}")
        node = nodes[ref]
        points.append(_project(node.get("lat"), node.get("lon"), bbox))
    closed = len(points) >= 4 and points[0] == points[-1]
    return {
        "geometry_type": "polygon" if closed else "line",
        "points": points,
    }


def _entry(
    *,
    element: dict[str, Any],
    kind: str,
    geometry: dict[str, Any],
    tags: dict[str, str],
) -> dict[str, Any]:
    element_type = str(element.get("type") or "unknown")
    element_id = element.get("id")
    if type(element_id) is not int:
        raise FieldOverlayError(f"{element_type} overlay element id must be an integer")
    return {
        "overlay_id": f"field:{element_type}:{element_id}:{kind}",
        "overlay_kind": kind,
        "geometry": geometry,
        "attributes": {
            "source_element_type": element_type,
            "source_element_id": element_id,
            "source_tags": tags,
        },
        "evidence": {
            "metadata_only": True,
            "no_runtime_setup_application": True,
            "no_movement_release": True,
            "no_passability_release": True,
            "no_los_cover_release": True,
            "no_fire_control_release": True,
        },
    }


def _classify(element: dict[str, Any]) -> tuple[str, ...]:
    tags = _tags(element)
    kinds: list[str] = []
    if element.get("type") == "node" and tags.get("place") in {"village", "hamlet", "isolated_dwelling"}:
        kinds.append("settlement_anchor")
    if element.get("type") != "way":
        return tuple(kinds)
    if tags.get("landuse") == "farmland":
        kinds.append("farmland_area")
    if tags.get("natural") == "wood" and tags.get("tree_line"):
        kinds.append("tree_line")
    if tags.get("building") or "building:levels" in tags:
        kinds.append("settlement_structure")
    if tags.get("waterway") or tags.get("natural") == "water":
        kinds.append("river_corridor")
    if tags.get("highway") and tags.get("bridge") in {"yes", "true", "1"}:
        kinds.append("bridge_crossing")
    return tuple(kinds)


def build_field_overlay(
    source_path: Path,
    bbox: dict[str, Any],
    *,
    profile_id: str = "eastern_plain_infantry_phase1",
    source_label: str | None = None,
) -> dict[str, Any]:
    """Build a deterministic metadata-only overlay from a frozen OSM-style source."""

    source_path = Path(source_path).expanduser().resolve()
    payload, source_sha256, source_byte_length = _load_source(source_path)
    bbox_values = _bbox_values(bbox)
    logical_source_label = str(source_label or source_path.name).replace("\\", "/").strip()
    if not logical_source_label or logical_source_label.startswith("/") or ".." in logical_source_label.split("/"):
        raise FieldOverlayError("source_label must be a safe relative path")
    elements = payload["elements"]
    nodes: dict[int, dict[str, Any]] = {
        element["id"]: element
        for element in elements
        if isinstance(element, dict)
        and element.get("type") == "node"
        and type(element.get("id")) is int
    }
    entries: list[dict[str, Any]] = []
    for element in elements:
        if not isinstance(element, dict):
            raise FieldOverlayError("every source element must be an object")
        kinds = _classify(element)
        if not kinds:
            continue
        geometry = _geometry(element, nodes, bbox_values)
        if geometry is None:
            raise FieldOverlayError(f"cannot derive geometry for element {element.get('id')!r}")
        tags = _tags(element)
        entries.extend(
            _entry(element=element, kind=kind, geometry=geometry, tags=tags)
            for kind in kinds
        )
    entries.sort(key=lambda entry: (entry["overlay_kind"], entry["overlay_id"]))
    counts: dict[str, int] = {}
    for entry in entries:
        kind = str(entry["overlay_kind"])
        counts[kind] = counts.get(kind, 0) + 1
    return {
        "contract_version": FIELD_OVERLAY_CONTRACT_VERSION,
        "profile_id": str(profile_id),
        "source": {
            "path": logical_source_label,
            "sha256": source_sha256,
            "byte_length": source_byte_length,
            "synthetic": True,
        },
        "projection": {
            "kind": "local_enu_equirectangular",
            "origin": {"lat": bbox_values[0], "lon": bbox_values[1]},
            "meters_per_radian": _EARTH_RADIUS_M,
            "x_cosine_reference_lat": (bbox_values[0] + bbox_values[2]) * 0.5,
        },
        "entries": entries,
        "summary": {
            "entry_count": len(entries),
            "counts_by_kind": counts,
        },
        "evidence": {
            "metadata_only": True,
            "no_runtime_setup_application": True,
            "no_movement_release": True,
            "no_passability_release": True,
            "no_los_cover_release": True,
            "no_fire_control_release": True,
        },
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--bbox", nargs=4, type=float, metavar=("MIN_LAT", "MIN_LON", "MAX_LAT", "MAX_LON"), required=True)
    parser.add_argument("--profile-id", default="eastern_plain_infantry_phase1")
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = _parser().parse_args(list(argv) if argv is not None else None)
    bbox = {
        "min_lat": args.bbox[0],
        "min_lon": args.bbox[1],
        "max_lat": args.bbox[2],
        "max_lon": args.bbox[3],
    }
    overlay = build_field_overlay(args.source, bbox, profile_id=args.profile_id)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(overlay, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ["FIELD_OVERLAY_CONTRACT_VERSION", "FieldOverlayError", "build_field_overlay"]
