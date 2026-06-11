#!/usr/bin/env python3
"""Generate review-only airframe geometry manifests from glTF audit assets.

The manifest produced here is evidence for human geometry review. It is not a
runtime collision mesh, not a vulnerability calibration, and not an authority
source for real internal aircraft structure.
"""

from __future__ import annotations

import argparse
import base64
import csv
import hashlib
import html
import json
import math
import struct
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_VERSION = "a2.target_geometry_manifest.v1"
MAPPING_SCHEMA_VERSION = "a2.target_geometry_mapping_candidate.v1"
COMPONENT_BINDING_SCHEMA_VERSION = "a2.target_geometry_component_binding_report.v1"
REVIEW_POINT_DIAGNOSTICS_SCHEMA_VERSION = (
  "a2.target_geometry_review_point_diagnostics.v1"
)
DEFAULT_GENERATED_ON = "2026-06-11"
REVIEW_POINT_COMPONENT_RADIUS_M = 2.0

DEFAULT_AIRCRAFT = (
  REPO_ROOT / "examples" / "config" / "database" / "aircraft" / "units" / "f16c_block50.json"
)
DEFAULT_AUDIT_SCENE = (
  REPO_ROOT
  / "examples"
  / "viz"
  / "web_viz"
  / "static"
  / "assets"
  / "air"
  / "audit"
  / "f16_c_falcon_carlos_maciel"
  / "gltf"
  / "scene.gltf"
)
DEFAULT_VISUAL_GLB = (
  REPO_ROOT
  / "examples"
  / "viz"
  / "web_viz"
  / "static"
  / "assets"
  / "air"
  / "f16_c_falcon_carlos_maciel"
  / "f16_c_falcon_carlos_maciel.glb"
)
DEFAULT_INTAKE_METADATA = (
  REPO_ROOT
  / "examples"
  / "viz"
  / "web_viz"
  / "static"
  / "assets"
  / "air"
  / "f16_c_falcon_carlos_maciel"
  / "intake_metadata.json"
)
DEFAULT_REGISTRY = REPO_ROOT / "examples" / "viz" / "assets" / "registry" / "default.json"
DEFAULT_OUTPUT_DIR = (
  REPO_ROOT
  / "docs"
  / "task"
  / "air_combat"
  / "a2_high_fidelity_damage_model"
  / "missile_lethality_target_geometry"
  / "review_packets"
  / "f16c_20260611"
)

COMPONENT_TYPE_FORMATS = {
  5120: "b",
  5121: "B",
  5122: "h",
  5123: "H",
  5125: "I",
  5126: "f",
}
TYPE_COUNTS = {
  "SCALAR": 1,
  "VEC2": 2,
  "VEC3": 3,
  "VEC4": 4,
  "MAT2": 4,
  "MAT3": 9,
  "MAT4": 16,
}
TRIANGLE_MODE = 4


@dataclass
class Bounds:
  minimum: list[float]
  maximum: list[float]

  @classmethod
  def empty(cls) -> "Bounds":
    inf = float("inf")
    return cls([inf, inf, inf], [-inf, -inf, -inf])

  def include(self, point: Iterable[float]) -> None:
    for index, value in enumerate(point):
      self.minimum[index] = min(self.minimum[index], float(value))
      self.maximum[index] = max(self.maximum[index], float(value))

  def span(self) -> list[float]:
    return [self.maximum[index] - self.minimum[index] for index in range(3)]

  def center(self) -> list[float]:
    return [
      (self.minimum[index] + self.maximum[index]) / 2.0 for index in range(3)
    ]

  def to_record(self) -> dict[str, list[float]]:
    return {
      "min": _round_vec(self.minimum),
      "max": _round_vec(self.maximum),
      "span": _round_vec(self.span()),
      "center": _round_vec(self.center()),
    }


def _round(value: float, digits: int = 6) -> float:
  if math.isfinite(value):
    return round(float(value), digits)
  return value


def _round_vec(values: Iterable[float], digits: int = 6) -> list[float]:
  return [_round(value, digits) for value in values]


def _display_path(path: Path, repo_root: Path) -> str:
  try:
    return path.resolve().relative_to(repo_root.resolve()).as_posix()
  except ValueError:
    return str(path)


def _sha256_file(path: Path) -> str:
  digest = hashlib.sha256()
  with path.open("rb") as handle:
    for chunk in iter(lambda: handle.read(1024 * 1024), b""):
      digest.update(chunk)
  return digest.hexdigest()


def _load_json(path: Path) -> dict[str, Any]:
  return json.loads(path.read_text(encoding="utf-8"))


def _identity() -> list[list[float]]:
  return [
    [1.0, 0.0, 0.0, 0.0],
    [0.0, 1.0, 0.0, 0.0],
    [0.0, 0.0, 1.0, 0.0],
    [0.0, 0.0, 0.0, 1.0],
  ]


def _mat_mul(left: list[list[float]], right: list[list[float]]) -> list[list[float]]:
  return [
    [
      sum(left[row][k] * right[k][col] for k in range(4))
      for col in range(4)
    ]
    for row in range(4)
  ]


def _transform_point(matrix: list[list[float]], point: tuple[float, float, float]) -> tuple[float, float, float]:
  x, y, z = point
  return (
    matrix[0][0] * x + matrix[0][1] * y + matrix[0][2] * z + matrix[0][3],
    matrix[1][0] * x + matrix[1][1] * y + matrix[1][2] * z + matrix[1][3],
    matrix[2][0] * x + matrix[2][1] * y + matrix[2][2] * z + matrix[2][3],
  )


def _matrix_from_gltf(values: list[float]) -> list[list[float]]:
  if len(values) != 16:
    raise ValueError("glTF node matrix must contain 16 values")
  return [
    [values[0], values[4], values[8], values[12]],
    [values[1], values[5], values[9], values[13]],
    [values[2], values[6], values[10], values[14]],
    [values[3], values[7], values[11], values[15]],
  ]


def _translation_matrix(values: list[float]) -> list[list[float]]:
  matrix = _identity()
  matrix[0][3], matrix[1][3], matrix[2][3] = values
  return matrix


def _scale_matrix(values: list[float]) -> list[list[float]]:
  matrix = _identity()
  matrix[0][0], matrix[1][1], matrix[2][2] = values
  return matrix


def _rotation_matrix(quaternion: list[float]) -> list[list[float]]:
  x, y, z, w = quaternion
  xx, yy, zz = x * x, y * y, z * z
  xy, xz, yz = x * y, x * z, y * z
  wx, wy, wz = w * x, w * y, w * z
  return [
    [1.0 - 2.0 * (yy + zz), 2.0 * (xy - wz), 2.0 * (xz + wy), 0.0],
    [2.0 * (xy + wz), 1.0 - 2.0 * (xx + zz), 2.0 * (yz - wx), 0.0],
    [2.0 * (xz - wy), 2.0 * (yz + wx), 1.0 - 2.0 * (xx + yy), 0.0],
    [0.0, 0.0, 0.0, 1.0],
  ]


def _node_local_matrix(node: dict[str, Any]) -> list[list[float]]:
  if "matrix" in node:
    return _matrix_from_gltf([float(value) for value in node["matrix"]])

  translation = [float(value) for value in node.get("translation", [0.0, 0.0, 0.0])]
  rotation = [float(value) for value in node.get("rotation", [0.0, 0.0, 0.0, 1.0])]
  scale = [float(value) for value in node.get("scale", [1.0, 1.0, 1.0])]
  return _mat_mul(_mat_mul(_translation_matrix(translation), _rotation_matrix(rotation)), _scale_matrix(scale))


def _load_buffer(gltf_path: Path, buffer_def: dict[str, Any]) -> bytes:
  uri = buffer_def.get("uri", "")
  if uri.startswith("data:"):
    _, encoded = uri.split(",", 1)
    return base64.b64decode(encoded)
  buffer_path = gltf_path.parent / uri
  return buffer_path.read_bytes()


def _accessor_values(
  *,
  gltf: dict[str, Any],
  buffers: list[bytes],
  accessor_index: int,
) -> list[tuple[float, ...]]:
  accessor = gltf["accessors"][accessor_index]
  if "sparse" in accessor:
    raise ValueError("Sparse glTF accessors are not supported by this review tool")

  component_type = accessor["componentType"]
  type_name = accessor["type"]
  fmt = COMPONENT_TYPE_FORMATS[component_type]
  component_count = TYPE_COUNTS[type_name]
  component_size = struct.calcsize("<" + fmt)
  element_size = component_size * component_count

  buffer_view = gltf["bufferViews"][accessor["bufferView"]]
  buffer_data = buffers[buffer_view["buffer"]]
  base_offset = int(buffer_view.get("byteOffset", 0)) + int(accessor.get("byteOffset", 0))
  stride = int(buffer_view.get("byteStride", element_size))
  count = int(accessor["count"])
  unpack = struct.Struct("<" + fmt * component_count).unpack_from

  values: list[tuple[float, ...]] = []
  for index in range(count):
    offset = base_offset + index * stride
    values.append(tuple(float(value) for value in unpack(buffer_data, offset)))
  return values


def _scene_root_nodes(gltf: dict[str, Any]) -> list[int]:
  scene_index = int(gltf.get("scene", 0))
  scenes = gltf.get("scenes", [])
  if scenes:
    return [int(index) for index in scenes[scene_index].get("nodes", [])]
  return list(range(len(gltf.get("nodes", []))))


def _walk_nodes(
  gltf: dict[str, Any],
  node_indices: Iterable[int],
  parent_matrix: list[list[float]],
) -> Iterable[tuple[int, dict[str, Any], list[list[float]]]]:
  nodes = gltf.get("nodes", [])
  for node_index in node_indices:
    node = nodes[node_index]
    world_matrix = _mat_mul(parent_matrix, _node_local_matrix(node))
    yield node_index, node, world_matrix
    yield from _walk_nodes(gltf, node.get("children", []), world_matrix)


def summarize_gltf_scene(gltf_path: Path) -> dict[str, Any]:
  gltf = _load_json(gltf_path)
  buffers = [_load_buffer(gltf_path, buffer_def) for buffer_def in gltf.get("buffers", [])]
  raw_bounds = Bounds.empty()
  transformed_bounds = Bounds.empty()
  node_bounds: list[dict[str, Any]] = []
  position_accessor_vertex_count = 0
  triangle_count = 0
  primitive_count = 0

  for node_index, node, world_matrix in _walk_nodes(gltf, _scene_root_nodes(gltf), _identity()):
    mesh_index = node.get("mesh")
    if mesh_index is None:
      continue
    mesh = gltf["meshes"][mesh_index]
    current_node_bounds = Bounds.empty()
    current_node_vertices = 0
    current_node_triangles = 0
    for primitive in mesh.get("primitives", []):
      attributes = primitive.get("attributes", {})
      if "POSITION" not in attributes:
        continue
      primitive_count += 1
      positions = _accessor_values(
        gltf=gltf,
        buffers=buffers,
        accessor_index=int(attributes["POSITION"]),
      )
      position_accessor_vertex_count += len(positions)
      current_node_vertices += len(positions)
      for position in positions:
        point = (position[0], position[1], position[2])
        raw_bounds.include(point)
        transformed = _transform_point(world_matrix, point)
        transformed_bounds.include(transformed)
        current_node_bounds.include(transformed)
      if int(primitive.get("mode", TRIANGLE_MODE)) == TRIANGLE_MODE:
        indices = primitive.get("indices")
        if indices is not None:
          triangle_count += int(gltf["accessors"][indices]["count"]) // 3
          current_node_triangles += int(gltf["accessors"][indices]["count"]) // 3
        else:
          triangle_count += len(positions) // 3
          current_node_triangles += len(positions) // 3
    if current_node_vertices:
      node_bounds.append(
        {
          "node_index": node_index,
          "node_name": node.get("name", f"node_{node_index}"),
          "mesh_index": mesh_index,
          "mesh_name": mesh.get("name", f"mesh_{mesh_index}"),
          "position_accessor_vertex_count": current_node_vertices,
          "triangle_count": current_node_triangles,
          "bounds": current_node_bounds.to_record(),
        }
      )

  notable_names = [
    record["node_name"]
    for record in node_bounds
    if any(
      token.lower() in record["node_name"].lower()
      for token in ("canopy", "pilot", "elevator", "aileron", "volet", "engine", "rudder")
    )
  ][:16]

  return {
    "asset": {
      "version": gltf.get("asset", {}).get("version", ""),
      "generator": gltf.get("asset", {}).get("generator", ""),
      "copyright": gltf.get("asset", {}).get("copyright", ""),
    },
    "node_count": len(gltf.get("nodes", [])),
    "mesh_count": len(gltf.get("meshes", [])),
    "material_count": len(gltf.get("materials", [])),
    "primitive_count": primitive_count,
    "triangle_count": triangle_count,
    "position_accessor_vertex_count": position_accessor_vertex_count,
    "raw_accessor_bounds": raw_bounds.to_record(),
    "transformed_bounds": transformed_bounds.to_record(),
    "notable_node_names": notable_names,
    "mesh_node_bounds": node_bounds,
  }


def _find_registry_entry(registry: dict[str, Any], visual_glb: Path, repo_root: Path) -> dict[str, Any]:
  expected_suffix = "/" + _display_path(visual_glb, repo_root).split("examples/viz/web_viz/", 1)[-1]
  expected_suffix = expected_suffix.replace("/static/", "/static/")
  for entry in registry.get("entries", []):
    asset_path = entry.get("visual", {}).get("asset_path", "")
    if asset_path and asset_path.endswith(visual_glb.name):
      return entry
    if asset_path == expected_suffix:
      return entry
  return {}


def _hitbox_envelope(hitboxes: list[dict[str, Any]]) -> dict[str, Any]:
  bounds = Bounds.empty()
  component_count = 0
  systems: set[str] = set()
  for hitbox in hitboxes:
    offset = [float(value) for value in hitbox["offset"]]
    size = [float(value) for value in hitbox["size"]]
    for axis in range(3):
      bounds.minimum[axis] = min(bounds.minimum[axis], offset[axis] - size[axis] / 2.0)
      bounds.maximum[axis] = max(bounds.maximum[axis], offset[axis] + size[axis] / 2.0)
    systems.update(str(system) for system in hitbox.get("systems", []))
    components = hitbox.get("components", [])
    component_count += len(components)
    for component in components:
      if "system" in component:
        systems.add(str(component["system"]))
  return {
    "hitbox_count": len(hitboxes),
    "component_count": component_count,
    "systems": sorted(systems),
    "combined_envelope": bounds.to_record(),
  }


def _percent_error(actual: float, expected: float) -> float:
  if expected == 0.0:
    return 0.0
  return ((actual - expected) / expected) * 100.0


def _bounds_from_min_max(minimum: list[float], maximum: list[float]) -> dict[str, list[float]]:
  bounds = Bounds(minimum[:], maximum[:])
  return bounds.to_record()


def _box_from_center_size(center: list[float], size: list[float]) -> dict[str, list[float]]:
  minimum = [center[index] - size[index] / 2.0 for index in range(3)]
  maximum = [center[index] + size[index] / 2.0 for index in range(3)]
  return _bounds_from_min_max(minimum, maximum)


def _sim_point_from_asset(
  point: list[float], *, asset_center: list[float], scale: float
) -> list[float]:
  # Project local aircraft review coordinates use x forward, y right, z up.
  return [
    -(point[2] - asset_center[2]) * scale,
    (point[0] - asset_center[0]) * scale,
    (point[1] - asset_center[1]) * scale,
  ]


def _sim_bounds_from_asset_bounds(
  asset_bounds: dict[str, list[float]], *, asset_center: list[float], scale: float
) -> dict[str, list[float]]:
  bounds = Bounds.empty()
  min_values = asset_bounds["min"]
  max_values = asset_bounds["max"]
  for x in (min_values[0], max_values[0]):
    for y in (min_values[1], max_values[1]):
      for z in (min_values[2], max_values[2]):
        bounds.include(_sim_point_from_asset([x, y, z], asset_center=asset_center, scale=scale))
  return bounds.to_record()


def _volume(bounds: dict[str, list[float]]) -> float:
  span = bounds["span"]
  return max(span[0], 0.0) * max(span[1], 0.0) * max(span[2], 0.0)


def _bounds_center_distance(
  first: dict[str, list[float]], second: dict[str, list[float]]
) -> float:
  return math.sqrt(
    sum(
      (first["center"][index] - second["center"][index]) ** 2 for index in range(3)
    )
  )


def _contains_point(bounds: dict[str, list[float]], point: list[float]) -> bool:
  return all(bounds["min"][index] <= point[index] <= bounds["max"][index] for index in range(3))


def _bounds_containment_fraction(
  inner: dict[str, list[float]], outer: dict[str, list[float]]
) -> float:
  intersection = _intersection_bounds(inner, outer)
  if intersection is None:
    return 0.0
  return _volume(intersection) / max(_volume(inner), 1e-9)


def _intersection_bounds(
  first: dict[str, list[float]], second: dict[str, list[float]]
) -> dict[str, list[float]] | None:
  minimum = [max(first["min"][index], second["min"][index]) for index in range(3)]
  maximum = [min(first["max"][index], second["max"][index]) for index in range(3)]
  if any(maximum[index] <= minimum[index] for index in range(3)):
    return None
  return _bounds_from_min_max(minimum, maximum)


def _mesh_node_candidates(
  manifest: dict[str, Any],
  region_bounds: dict[str, list[float]],
  *,
  limit: int = 6,
) -> list[dict[str, Any]]:
  asset_center = manifest["gltf_summary"]["transformed_bounds"]["center"]
  scale = float(manifest["public_dimension_check"]["registry_scale"])
  scored: list[dict[str, Any]] = []
  region_volume = max(_volume(region_bounds), 1e-9)
  for mesh_node in manifest["gltf_summary"]["mesh_node_bounds"]:
    sim_bounds = _sim_bounds_from_asset_bounds(
      mesh_node["bounds"], asset_center=asset_center, scale=scale
    )
    intersection = _intersection_bounds(region_bounds, sim_bounds)
    if intersection is None:
      continue
    intersection_volume = _volume(intersection)
    scored.append(
      {
        "node_name": mesh_node["node_name"],
        "mesh_name": mesh_node["mesh_name"],
        "triangle_count": mesh_node["triangle_count"],
        "coverage_fraction_of_region_box": _round(intersection_volume / region_volume, 5),
        "sim_bounds": sim_bounds,
      }
    )
  scored.sort(
    key=lambda row: (
      row["coverage_fraction_of_region_box"],
      row["triangle_count"],
    ),
    reverse=True,
  )
  return scored[:limit]


def _region_record(
  *,
  region_id: str,
  label: str,
  role: str,
  minimum: list[float],
  maximum: list[float],
  rationale: str,
  manifest: dict[str, Any],
) -> dict[str, Any]:
  bounds = _bounds_from_min_max(minimum, maximum)
  return {
    "id": region_id,
    "label": label,
    "role": role,
    "bounds_kind": "review_aabb_sim_m",
    "bounds": bounds,
    "source_basis": "scaled_outer_envelope_fraction_plus_manual_review_seed",
    "source_mesh_node_candidates": _mesh_node_candidates(manifest, bounds),
    "confidence": "low_initial_review_candidate",
    "manual_review_required": True,
    "rationale": rationale,
  }


def _outer_region_records(manifest: dict[str, Any]) -> list[dict[str, Any]]:
  dims = manifest["public_dimension_check"]["scaled_review_dimensions"]
  half_length = float(dims["length_m"]) / 2.0
  half_width = float(dims["wingspan_m"]) / 2.0
  half_height = float(dims["height_m"]) / 2.0
  fuselage_half_width = min(0.85, half_width * 0.18)
  nose_half_width = min(0.48, half_width * 0.10)

  return [
    _region_record(
      region_id="nose_radome",
      label="nose_radome",
      role="outer_skin",
      minimum=[0.68 * half_length, -nose_half_width, -0.18 * half_height],
      maximum=[half_length, nose_half_width, 0.24 * half_height],
      rationale="Forward-most narrow body area; seeded from public length scale and nose direction.",
      manifest=manifest,
    ),
    _region_record(
      region_id="forward_fuselage",
      label="forward_fuselage",
      role="outer_skin",
      minimum=[0.30 * half_length, -fuselage_half_width, -0.34 * half_height],
      maximum=[0.72 * half_length, fuselage_half_width, 0.36 * half_height],
      rationale="Forward fuselage and avionics/cockpit support area; covers the old 4 m/6 m nose test zone.",
      manifest=manifest,
    ),
    _region_record(
      region_id="canopy",
      label="canopy",
      role="raised_outer_skin",
      minimum=[0.28 * half_length, -0.55, 0.20 * half_height],
      maximum=[0.58 * half_length, 0.55, 0.72 * half_height],
      rationale="Raised cockpit canopy candidate; kept separate because old hitboxes understate height.",
      manifest=manifest,
    ),
    _region_record(
      region_id="center_fuselage",
      label="center_fuselage",
      role="outer_skin",
      minimum=[-0.25 * half_length, -fuselage_half_width, -0.34 * half_height],
      maximum=[0.32 * half_length, fuselage_half_width, 0.34 * half_height],
      rationale="Main body core around fuel, avionics, and flight-control components.",
      manifest=manifest,
    ),
    _region_record(
      region_id="intake",
      label="intake",
      role="outer_skin",
      minimum=[0.05 * half_length, -0.62, -0.72 * half_height],
      maximum=[0.42 * half_length, 0.62, -0.10 * half_height],
      rationale="Lower intake candidate; separated from center fuselage for underside proximity review.",
      manifest=manifest,
    ),
    _region_record(
      region_id="aft_fuselage_engine",
      label="aft_fuselage_engine",
      role="outer_skin",
      minimum=[-0.78 * half_length, -fuselage_half_width, -0.32 * half_height],
      maximum=[-0.20 * half_length, fuselage_half_width, 0.34 * half_height],
      rationale="Aft fuselage and engine bay candidate for tail-aspect blast/fragment review.",
      manifest=manifest,
    ),
    _region_record(
      region_id="engine_nozzle",
      label="engine_nozzle",
      role="outer_skin",
      minimum=[-half_length, -0.58, -0.22 * half_height],
      maximum=[-0.76 * half_length, 0.58, 0.24 * half_height],
      rationale="Rear nozzle candidate; kept distinct for tail-on shot diagnostics.",
      manifest=manifest,
    ),
    _region_record(
      region_id="left_wing",
      label="left_wing",
      role="lifting_surface",
      minimum=[-0.30 * half_length, 0.68, -0.10 * half_height],
      maximum=[0.18 * half_length, half_width, 0.12 * half_height],
      rationale="Left wing lifting surface, thin but broad; review uses project-positive y as right/left convention only by sign.",
      manifest=manifest,
    ),
    _region_record(
      region_id="right_wing",
      label="right_wing",
      role="lifting_surface",
      minimum=[-0.30 * half_length, -half_width, -0.10 * half_height],
      maximum=[0.18 * half_length, -0.68, 0.12 * half_height],
      rationale="Right wing lifting surface, mirrored from left wing candidate.",
      manifest=manifest,
    ),
    _region_record(
      region_id="left_wing_root",
      label="left_wing_root",
      role="structural_transition",
      minimum=[-0.35 * half_length, 0.30, -0.20 * half_height],
      maximum=[0.25 * half_length, 1.35, 0.20 * half_height],
      rationale="Left wing root transition; useful for component binding and grazing-warhead review.",
      manifest=manifest,
    ),
    _region_record(
      region_id="right_wing_root",
      label="right_wing_root",
      role="structural_transition",
      minimum=[-0.35 * half_length, -1.35, -0.20 * half_height],
      maximum=[0.25 * half_length, -0.30, 0.20 * half_height],
      rationale="Right wing root transition; mirrored from left wing root candidate.",
      manifest=manifest,
    ),
    _region_record(
      region_id="left_horizontal_tail",
      label="left_horizontal_tail",
      role="tail_surface",
      minimum=[-0.90 * half_length, 0.55, -0.02 * half_height],
      maximum=[-0.55 * half_length, min(2.80, half_width), 0.28 * half_height],
      rationale="Left horizontal tail candidate for aft control-surface exposure.",
      manifest=manifest,
    ),
    _region_record(
      region_id="right_horizontal_tail",
      label="right_horizontal_tail",
      role="tail_surface",
      minimum=[-0.90 * half_length, -min(2.80, half_width), -0.02 * half_height],
      maximum=[-0.55 * half_length, -0.55, 0.28 * half_height],
      rationale="Right horizontal tail candidate for aft control-surface exposure.",
      manifest=manifest,
    ),
    _region_record(
      region_id="vertical_tail",
      label="vertical_tail",
      role="tail_surface",
      minimum=[-0.88 * half_length, -0.38, 0.22 * half_height],
      maximum=[-0.45 * half_length, 0.38, half_height],
      rationale="Vertical tail candidate; separated because old damage boxes omit most aircraft height.",
      manifest=manifest,
    ),
  ]


def build_geometry_mapping_candidate(manifest: dict[str, Any]) -> dict[str, Any]:
  regions = _outer_region_records(manifest)
  return {
    "schema_version": MAPPING_SCHEMA_VERSION,
    "status": "outer_region_candidate_generated_review_only",
    "generated_on": manifest["generated_on"],
    "asset_ref": {
      "source_uid": manifest["source"]["uid"],
      "runtime_visual_glb": manifest["paths"]["runtime_visual_glb"],
      "audit_scene_gltf": manifest["paths"]["audit_scene_gltf"],
      "manifest_schema_version": manifest["schema_version"],
    },
    "coordinate_frame": {
      "frame": "sim_local_m_review",
      "x_positive": "nose_forward",
      "y_positive": "right_or_left_by_project_sign_review_only",
      "z_positive": "up",
      "source_axis_map": manifest["axis_alignment"],
      "origin": "center_of_audit_asset_transformed_bounds_after_registry_scale",
    },
    "outer_envelope": {
      "bounds_kind": "review_aabb_sim_m",
      "bounds": _sim_bounds_from_asset_bounds(
        manifest["gltf_summary"]["transformed_bounds"],
        asset_center=manifest["gltf_summary"]["transformed_bounds"]["center"],
        scale=float(manifest["public_dimension_check"]["registry_scale"]),
      ),
      "scaled_review_dimensions": manifest["public_dimension_check"][
        "scaled_review_dimensions"
      ],
    },
    "mesh_node_name_quality": {
      "actual_scene_node_pattern": "generic_Object_nodes",
      "semantic_hints_from_intake_metadata": manifest["source_geometry_hints"][
        "metadata_notable_node_names"
      ],
      "decision": "do_not_auto_classify_regions_from_node_names_only",
    },
    "outer_regions": regions,
    "legacy_damage_geometry_overlay": manifest["current_damage_geometry"]["summary"],
    "manual_review_queue": [
      {
        "question": "Do the generated nose and forward-fuselage regions cover the 4 m and 6 m nose test points without creating a hard edge?",
        "priority": "high",
      },
      {
        "question": "Do canopy, intake, and vertical-tail regions correct the legacy hitbox height gap without overstating true internal component boundaries?",
        "priority": "high",
      },
      {
        "question": "Are left/right wing signs aligned with the runtime local-coordinate convention before component binding?",
        "priority": "medium",
      },
    ],
    "authority_boundary": manifest["authority_boundary"],
  }


def _iter_damage_components(aircraft: dict[str, Any]) -> Iterable[dict[str, Any]]:
  for hitbox_index, hitbox in enumerate(aircraft.get("damage_model", {}).get("hitboxes", [])):
    hitbox_bounds = _box_from_center_size(
      [float(value) for value in hitbox["offset"]],
      [float(value) for value in hitbox["size"]],
    )
    for component in hitbox.get("components", []):
      component_bounds = _box_from_center_size(
        [float(value) for value in component["offset"]],
        [float(value) for value in component["size"]],
      )
      yield {
        "hitbox_index": hitbox_index,
        "hitbox_systems": hitbox.get("systems", []),
        "hitbox_bounds": hitbox_bounds,
        "component": component,
        "component_bounds": component_bounds,
      }


def _rank_region_bindings(
  component_bounds: dict[str, list[float]],
  regions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
  component_volume = max(_volume(component_bounds), 1e-9)
  ranked: list[dict[str, Any]] = []
  for region in regions:
    region_bounds = region["bounds"]
    intersection = _intersection_bounds(component_bounds, region_bounds)
    overlap_volume = 0.0 if intersection is None else _volume(intersection)
    ranked.append(
      {
        "region_id": region["id"],
        "region_role": region["role"],
        "component_overlap_fraction": _round(overlap_volume / component_volume, 5),
        "region_overlap_fraction": _round(overlap_volume / max(_volume(region_bounds), 1e-9), 5),
        "center_inside_region": _contains_point(region_bounds, component_bounds["center"]),
        "center_distance_m": _round(_bounds_center_distance(component_bounds, region_bounds)),
      }
    )
  ranked.sort(
    key=lambda row: (
      row["component_overlap_fraction"],
      row["center_inside_region"],
      -row["center_distance_m"],
    ),
    reverse=True,
  )
  return ranked


def _component_anomalies(
  *,
  component_name: str,
  component_bounds: dict[str, list[float]],
  outer_envelope: dict[str, list[float]],
  best: dict[str, Any],
) -> list[str]:
  anomalies: list[str] = []
  envelope_fraction = _bounds_containment_fraction(component_bounds, outer_envelope)
  if envelope_fraction < 0.99:
    anomalies.append("component_extends_outside_outer_envelope")
  if best["component_overlap_fraction"] <= 0.0:
    anomalies.append("no_outer_region_overlap")
  elif best["component_overlap_fraction"] < 0.50:
    anomalies.append("low_outer_region_overlap")
  if not best["center_inside_region"]:
    anomalies.append("component_center_outside_bound_region")
  if component_name.startswith("left_") and best["region_id"].startswith("right_"):
    anomalies.append("left_name_bound_to_negative_y_region_sign_review")
  if component_name.startswith("right_") and best["region_id"].startswith("left_"):
    anomalies.append("right_name_bound_to_positive_y_region_sign_review")
  return anomalies


def build_component_binding_report(
  aircraft: dict[str, Any],
  mapping: dict[str, Any],
) -> dict[str, Any]:
  regions = mapping["outer_regions"]
  outer_envelope = mapping["outer_envelope"]["bounds"]
  rows: list[dict[str, Any]] = []
  for item in _iter_damage_components(aircraft):
    component = item["component"]
    component_bounds = item["component_bounds"]
    rankings = _rank_region_bindings(component_bounds, regions)
    best = rankings[0]
    anomalies = _component_anomalies(
      component_name=component["name"],
      component_bounds=component_bounds,
      outer_envelope=outer_envelope,
      best=best,
    )
    rows.append(
      {
        "component_name": component["name"],
        "system": component.get("system", ""),
        "critical": bool(component.get("critical", False)),
        "hitbox_index": item["hitbox_index"],
        "component_bounds": component_bounds,
        "parent_hitbox_bounds": item["hitbox_bounds"],
        "bound_region_id": best["region_id"],
        "bound_region_role": best["region_role"],
        "component_overlap_fraction": best["component_overlap_fraction"],
        "region_overlap_fraction": best["region_overlap_fraction"],
        "center_inside_bound_region": best["center_inside_region"],
        "center_distance_m": best["center_distance_m"],
        "outer_envelope_containment_fraction": _round(
          _bounds_containment_fraction(component_bounds, outer_envelope), 5
        ),
        "candidate_regions": rankings[:5],
        "review_status": "needs_review" if anomalies else "candidate_binding",
        "anomalies": anomalies,
        "authority_boundary": "review_only_not_true_internal_component_geometry",
      }
    )

  needs_review = [row for row in rows if row["review_status"] == "needs_review"]
  return {
    "schema_version": COMPONENT_BINDING_SCHEMA_VERSION,
    "status": "component_binding_report_generated_review_only",
    "generated_on": mapping["generated_on"],
    "asset_ref": mapping["asset_ref"],
    "coordinate_frame": mapping["coordinate_frame"],
    "summary": {
      "component_count": len(rows),
      "bound_component_count": len(rows) - sum(
        1 for row in rows if "no_outer_region_overlap" in row["anomalies"]
      ),
      "needs_review_count": len(needs_review),
      "side_sign_review_count": sum(
        1
        for row in rows
        if any("sign_review" in anomaly for anomaly in row["anomalies"])
      ),
      "review_status": "manual_review_required",
    },
    "rows": rows,
    "manual_review_queue": [
      {
        "priority": "high",
        "question": "Check every needs_review component before using outer regions in runtime projection.",
      },
      {
        "priority": "high",
        "question": "Resolve left/right sign convention before treating wing bindings as authoritative.",
      },
      {
        "priority": "medium",
        "question": "Review large components such as wing_spar_center for intentional multi-region coverage.",
      },
    ],
    "authority_boundary": mapping["authority_boundary"],
  }


def _point_box_distance(point: list[float], bounds: dict[str, list[float]]) -> float:
  squared = 0.0
  for axis in range(3):
    value = point[axis]
    if value < bounds["min"][axis]:
      squared += (bounds["min"][axis] - value) ** 2
    elif value > bounds["max"][axis]:
      squared += (value - bounds["max"][axis]) ** 2
  return math.sqrt(squared)


def _default_review_points() -> list[dict[str, Any]]:
  return [
    {
      "id": "nose_axis_4m",
      "label": "nose x=4m",
      "point": [4.0, 0.0, 0.0],
      "aspect": "nose",
      "rationale": "Known close-to-shape nose review point that previously lacked component explanation.",
    },
    {
      "id": "nose_axis_6m",
      "label": "nose x=6m",
      "point": [6.0, 0.0, 0.0],
      "aspect": "nose",
      "rationale": "Forward nose review point used to compare the old 4 m / 6 m discontinuity.",
    },
    {
      "id": "tail_axis_4m",
      "label": "tail x=-4m",
      "point": [-4.0, 0.0, 0.0],
      "aspect": "tail",
      "rationale": "Aft approach point for engine and tail-control exposure review.",
    },
    {
      "id": "tail_axis_6m",
      "label": "tail x=-6m",
      "point": [-6.0, 0.0, 0.0],
      "aspect": "tail",
      "rationale": "Rear nozzle and engine-bay review point.",
    },
    {
      "id": "right_beam_4m",
      "label": "beam y=4m",
      "point": [0.0, 4.0, 0.0],
      "aspect": "beam",
      "rationale": "Lateral wing exposure review point on positive-y side.",
    },
    {
      "id": "right_beam_6m",
      "label": "beam y=6m",
      "point": [0.0, 6.0, 0.0],
      "aspect": "beam",
      "rationale": "Outer lateral miss point on positive-y side.",
    },
    {
      "id": "left_beam_4m",
      "label": "beam y=-4m",
      "point": [0.0, -4.0, 0.0],
      "aspect": "beam",
      "rationale": "Lateral wing exposure review point on negative-y side.",
    },
    {
      "id": "left_beam_6m",
      "label": "beam y=-6m",
      "point": [0.0, -6.0, 0.0],
      "aspect": "beam",
      "rationale": "Outer lateral miss point on negative-y side.",
    },
    {
      "id": "above_4m",
      "label": "above z=4m",
      "point": [0.0, 0.0, 4.0],
      "aspect": "above",
      "rationale": "Top-side review point for height and vertical-tail coverage.",
    },
    {
      "id": "below_4m",
      "label": "below z=-4m",
      "point": [0.0, 0.0, -4.0],
      "aspect": "below",
      "rationale": "Underside review point for intake and low-fuselage coverage.",
    },
  ]


def _rank_point_to_regions(
  point: list[float],
  regions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
  ranked: list[dict[str, Any]] = []
  for region in regions:
    distance = _point_box_distance(point, region["bounds"])
    ranked.append(
      {
        "region_id": region["id"],
        "region_role": region["role"],
        "distance_m": _round(distance),
        "contains_point": _contains_point(region["bounds"], point),
        "center_distance_m": _round(
          math.sqrt(
            sum(
              (point[axis] - region["bounds"]["center"][axis]) ** 2
              for axis in range(3)
            )
          )
        ),
      }
    )
  ranked.sort(key=lambda row: (row["distance_m"], row["center_distance_m"]))
  return ranked


def _rank_point_to_components(
  point: list[float],
  rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
  ranked: list[dict[str, Any]] = []
  for row in rows:
    distance = _point_box_distance(point, row["component_bounds"])
    ranked.append(
      {
        "component_name": row["component_name"],
        "system": row["system"],
        "critical": row["critical"],
        "bound_region_id": row["bound_region_id"],
        "distance_m": _round(distance),
        "contains_point": _contains_point(row["component_bounds"], point),
        "review_status": row["review_status"],
      }
    )
  ranked.sort(key=lambda row: (row["distance_m"], row["component_name"]))
  return ranked


def _diagnostic_interpretation(
  *,
  inside_outer_count: int,
  inside_component_count: int,
  candidate_component_count: int,
) -> str:
  if inside_component_count:
    return "point_inside_component_box_review_only"
  if inside_outer_count and candidate_component_count:
    return "inside_outer_shape_with_nearby_component_candidates_review_only"
  if inside_outer_count:
    return "inside_outer_shape_but_no_component_candidate_within_review_radius"
  if candidate_component_count:
    return "outside_outer_shape_but_near_component_candidate_review_only"
  return "outside_outer_shape_no_near_component_candidate_review_only"


def build_review_point_diagnostics(
  mapping: dict[str, Any],
  component_report: dict[str, Any],
  *,
  review_points: list[dict[str, Any]] | None = None,
  candidate_radius_m: float = REVIEW_POINT_COMPONENT_RADIUS_M,
) -> dict[str, Any]:
  points = review_points if review_points is not None else _default_review_points()
  rows: list[dict[str, Any]] = []
  for index, point_record in enumerate(points, start=1):
    point = [float(value) for value in point_record["point"]]
    outer_rankings = _rank_point_to_regions(point, mapping["outer_regions"])
    component_rankings = _rank_point_to_components(point, component_report["rows"])
    inside_outer_count = sum(1 for row in outer_rankings if row["contains_point"])
    inside_component_count = sum(1 for row in component_rankings if row["contains_point"])
    nearby_components = [
      row for row in component_rankings if row["distance_m"] <= candidate_radius_m
    ]
    rows.append(
      {
        "point_index": index,
        "point_id": point_record["id"],
        "label": point_record["label"],
        "aspect": point_record["aspect"],
        "point_m": _round_vec(point),
        "nearest_outer_region_id": outer_rankings[0]["region_id"],
        "nearest_outer_region_role": outer_rankings[0]["region_role"],
        "nearest_outer_distance_m": outer_rankings[0]["distance_m"],
        "inside_outer_region_count": inside_outer_count,
        "nearest_component_name": component_rankings[0]["component_name"],
        "nearest_component_system": component_rankings[0]["system"],
        "nearest_component_distance_m": component_rankings[0]["distance_m"],
        "inside_component_count": inside_component_count,
        "candidate_component_radius_m": candidate_radius_m,
        "candidate_component_count": len(nearby_components),
        "candidate_components": nearby_components[:8],
        "outer_region_rankings": outer_rankings[:5],
        "component_rankings": component_rankings[:8],
        "interpretation": _diagnostic_interpretation(
          inside_outer_count=inside_outer_count,
          inside_component_count=inside_component_count,
          candidate_component_count=len(nearby_components),
        ),
        "rationale": point_record["rationale"],
        "authority_boundary": "review_only_not_runtime_lethality_decision",
      }
    )

  return {
    "schema_version": REVIEW_POINT_DIAGNOSTICS_SCHEMA_VERSION,
    "status": "review_point_distance_diagnostics_generated_review_only",
    "generated_on": mapping["generated_on"],
    "asset_ref": mapping["asset_ref"],
    "coordinate_frame": mapping["coordinate_frame"],
    "candidate_component_radius_m": candidate_radius_m,
    "summary": {
      "review_point_count": len(rows),
      "inside_outer_region_point_count": sum(
        1 for row in rows if row["inside_outer_region_count"] > 0
      ),
      "inside_component_point_count": sum(
        1 for row in rows if row["inside_component_count"] > 0
      ),
      "zero_outer_distance_without_component_candidate_count": sum(
        1
        for row in rows
        if row["nearest_outer_distance_m"] == 0.0
        and row["candidate_component_count"] == 0
      ),
      "review_status": "manual_review_required",
    },
    "rows": rows,
    "manual_review_queue": [
      {
        "priority": "high",
        "question": "Review nose_axis_4m and nose_axis_6m before using these boxes for runtime near-fuze projection.",
      },
      {
        "priority": "high",
        "question": "Confirm beam left/right sign before treating wing candidates as authoritative.",
      },
      {
        "priority": "medium",
        "question": "Use TG-P6 finer geometry before any path or swept intersection decision.",
      },
    ],
    "authority_boundary": mapping["authority_boundary"],
  }


def _source_metadata(intake_metadata: dict[str, Any]) -> dict[str, Any]:
  user = intake_metadata.get("user", {})
  license_record = intake_metadata.get("license", {})
  return {
    "title": intake_metadata.get("name", ""),
    "uid": intake_metadata.get("uid", ""),
    "viewer_url": intake_metadata.get("viewerUrl", ""),
    "author": user.get("displayName", ""),
    "author_profile": user.get("profileUrl", ""),
    "license": {
      "label": license_record.get("label", ""),
      "full_name": license_record.get("fullName", ""),
      "url": license_record.get("url", ""),
      "requirements": license_record.get("requirements", ""),
    },
    "created_at": intake_metadata.get("createdAt", ""),
    "published_at": intake_metadata.get("publishedAt", ""),
    "downloaded_at": intake_metadata.get("downloadedAt", ""),
  }


def build_airframe_geometry_manifest(
  *,
  aircraft_path: Path = DEFAULT_AIRCRAFT,
  audit_scene_path: Path = DEFAULT_AUDIT_SCENE,
  visual_glb_path: Path = DEFAULT_VISUAL_GLB,
  intake_metadata_path: Path = DEFAULT_INTAKE_METADATA,
  registry_path: Path = DEFAULT_REGISTRY,
  repo_root: Path = REPO_ROOT,
  generated_on: str = DEFAULT_GENERATED_ON,
) -> dict[str, Any]:
  aircraft = _load_json(aircraft_path)
  intake_metadata = _load_json(intake_metadata_path)
  registry = _load_json(registry_path)
  gltf_summary = summarize_gltf_scene(audit_scene_path)
  registry_entry = _find_registry_entry(registry, visual_glb_path, repo_root)

  public_dimensions = {
    "length_m": float(aircraft["airframe"]["length_m"]),
    "wingspan_m": float(aircraft["airframe"]["wingspan_m"]),
    "height_m": float(aircraft["airframe"]["height_m"]),
    "reference_area_m2": float(aircraft["airframe"]["reference_area"]),
  }
  transformed_span = gltf_summary["transformed_bounds"]["span"]
  registry_scale = float(registry_entry.get("visual", {}).get("scale", 1.0))
  length_fit_scale = public_dimensions["length_m"] / transformed_span[2]
  scaled_review_dimensions = {
    "length_m": transformed_span[2] * registry_scale,
    "wingspan_m": transformed_span[0] * registry_scale,
    "height_m": transformed_span[1] * registry_scale,
  }
  dimension_errors = {
    key: _round(_percent_error(scaled_review_dimensions[key], public_dimensions[key]))
    for key in ("length_m", "wingspan_m", "height_m")
  }

  hitbox_summary = _hitbox_envelope(aircraft.get("damage_model", {}).get("hitboxes", []))
  hitbox_span = hitbox_summary["combined_envelope"]["span"]

  manifest = {
    "schema_version": SCHEMA_VERSION,
    "status": "target_geometry_manifest_generated_review_only",
    "generated_on": generated_on,
    "asset_source_status": "verified_redistributable_visual_reference",
    "review_scope": "f16c_outer_shape_scale_axis_manifest_only",
    "source": _source_metadata(intake_metadata),
    "source_geometry_hints": {
      "face_count": intake_metadata.get("faceCount"),
      "vertex_count": intake_metadata.get("vertexCount"),
      "metadata_notable_node_names": intake_metadata.get("localGeometrySummary", {}).get(
        "notableNodeNames", []
      ),
      "metadata_scene": intake_metadata.get("localGeometrySummary", {}).get("scene", ""),
      "note": (
        "The retained glTF scene may use generic Object_* node names; source "
        "metadata hints are review aids and must not be treated as true "
        "component boundaries."
      ),
    },
    "paths": {
      "aircraft_database": _display_path(aircraft_path, repo_root),
      "runtime_visual_glb": _display_path(visual_glb_path, repo_root),
      "audit_scene_gltf": _display_path(audit_scene_path, repo_root),
      "intake_metadata": _display_path(intake_metadata_path, repo_root),
      "registry": _display_path(registry_path, repo_root),
    },
    "file_hashes": {
      "runtime_visual_glb_sha256": _sha256_file(visual_glb_path),
      "audit_scene_gltf_sha256": _sha256_file(audit_scene_path),
      "intake_metadata_sha256": _sha256_file(intake_metadata_path),
      "aircraft_database_sha256": _sha256_file(aircraft_path),
    },
    "registry_entry": {
      "id": registry_entry.get("id", ""),
      "label": registry_entry.get("label", ""),
      "asset_path": registry_entry.get("visual", {}).get("asset_path", ""),
      "scale": registry_scale,
      "yaw_correction_deg": registry_entry.get("visual", {}).get("yaw_correction_deg", 0.0),
      "realism_note": registry_entry.get("realism_note", ""),
    },
    "gltf_summary": gltf_summary,
    "axis_alignment": {
      "convention": "project_review_axis_map_v1",
      "asset_x": "sim_right",
      "asset_y": "sim_up",
      "asset_z_negative": "sim_forward",
      "nose_direction": "negative_asset_z",
      "tail_engine_direction": "positive_asset_z",
      "yaw_correction_deg": registry_entry.get("visual", {}).get("yaw_correction_deg", 0.0),
      "runtime_registry_scale": registry_scale,
    },
    "public_dimension_check": {
      "public_dimensions": public_dimensions,
      "asset_transformed_span": {
        "asset_x_right_span": _round(transformed_span[0]),
        "asset_y_up_span": _round(transformed_span[1]),
        "asset_z_forward_length_span": _round(transformed_span[2]),
      },
      "length_fit_scale": _round(length_fit_scale),
      "registry_scale": registry_scale,
      "scale_delta_percent": _round(_percent_error(registry_scale, length_fit_scale)),
      "scaled_review_dimensions": {
        key: _round(value) for key, value in scaled_review_dimensions.items()
      },
      "scaled_dimension_error_percent": dimension_errors,
      "scale_basis": "registry_scale_matches_public_length_order_and_preserves_frontend_visual_size",
    },
    "current_damage_geometry": {
      "source": "damage_model.hitboxes",
      "summary": hitbox_summary,
      "public_dimension_error_percent": {
        "length_m": _round(_percent_error(hitbox_span[0], public_dimensions["length_m"])),
        "wingspan_m": _round(_percent_error(hitbox_span[1], public_dimensions["wingspan_m"])),
        "height_m": _round(_percent_error(hitbox_span[2], public_dimensions["height_m"])),
      },
      "known_gap": "current_axis_aligned_hitboxes_cover_core_damage_scaffold_but_understate_full_aircraft_height",
    },
    "authority_boundary": {
      "runtime_collision_mesh": False,
      "true_f16_engineering_geometry": False,
      "true_internal_component_boundaries": False,
      "real_weapon_pk_authority": False,
      "structural_breakup_or_debris_claim": False,
      "allowed_use": [
        "outer_shape_review",
        "scale_and_axis_audit",
        "component_binding_review_input",
        "test_point_distance_diagnostic_input",
      ],
    },
  }
  return manifest


def write_manifest(manifest: dict[str, Any], output_dir: Path) -> Path:
  output_dir.mkdir(parents=True, exist_ok=True)
  output_path = output_dir / "manifest.json"
  output_path.write_text(
    json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
    encoding="utf-8",
  )
  return output_path


def write_mapping_candidate(mapping: dict[str, Any], output_dir: Path) -> Path:
  output_dir.mkdir(parents=True, exist_ok=True)
  output_path = output_dir / "f16c_geometry_mapping_candidate_20260611.json"
  output_path.write_text(
    json.dumps(mapping, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
    encoding="utf-8",
  )
  return output_path


def write_component_binding_report(report: dict[str, Any], output_dir: Path) -> tuple[Path, Path]:
  output_dir.mkdir(parents=True, exist_ok=True)
  json_path = output_dir / "component_binding_report_20260611.json"
  csv_path = output_dir / "component_binding_report_20260611.csv"
  json_path.write_text(
    json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
    encoding="utf-8",
  )

  fieldnames = [
    "component_name",
    "system",
    "critical",
    "hitbox_index",
    "bound_region_id",
    "bound_region_role",
    "component_overlap_fraction",
    "region_overlap_fraction",
    "center_inside_bound_region",
    "center_distance_m",
    "outer_envelope_containment_fraction",
    "review_status",
    "anomalies",
  ]
  with csv_path.open("w", encoding="utf-8", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    for row in report["rows"]:
      writer.writerow(
        {
          key: (
            ";".join(row[key])
            if key == "anomalies"
            else row[key]
          )
          for key in fieldnames
        }
      )
  return json_path, csv_path


def write_review_point_diagnostics(
  diagnostics: dict[str, Any],
  output_dir: Path,
) -> tuple[Path, Path]:
  output_dir.mkdir(parents=True, exist_ok=True)
  json_path = output_dir / "review_point_diagnostics_20260611.json"
  csv_path = output_dir / "review_point_diagnostics_20260611.csv"
  json_path.write_text(
    json.dumps(diagnostics, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
    encoding="utf-8",
  )

  fieldnames = [
    "point_index",
    "point_id",
    "aspect",
    "point_m",
    "nearest_outer_region_id",
    "nearest_outer_distance_m",
    "inside_outer_region_count",
    "nearest_component_name",
    "nearest_component_distance_m",
    "inside_component_count",
    "candidate_component_count",
    "interpretation",
  ]
  with csv_path.open("w", encoding="utf-8", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    for row in diagnostics["rows"]:
      writer.writerow(
        {
          key: (
            ";".join(str(value) for value in row[key])
            if key == "point_m"
            else row[key]
          )
          for key in fieldnames
        }
      )
  return json_path, csv_path


def _project_bounds(bounds: dict[str, list[float]], axes: tuple[int, int]) -> tuple[float, float, float, float]:
  x_axis, y_axis = axes
  return (
    bounds["min"][x_axis],
    bounds["min"][y_axis],
    bounds["max"][x_axis],
    bounds["max"][y_axis],
  )


def _svg_color(index: int) -> str:
  palette = [
    "#2f6f9f",
    "#b24d3e",
    "#4f8a4b",
    "#8a5a9f",
    "#b27a2f",
    "#2f827d",
    "#6f6f6f",
  ]
  return palette[index % len(palette)]


def _svg_project_point(
  *,
  point: tuple[float, float],
  view_bounds: tuple[float, float, float, float],
  width: int,
  height: int,
) -> tuple[float, float]:
  value_x, value_y = point
  view_min_x, view_min_y, view_max_x, view_max_y = view_bounds
  span_x = view_max_x - view_min_x
  span_y = view_max_y - view_min_y
  x = ((value_x - view_min_x) / span_x) * width
  y = height - ((value_y - view_min_y) / span_y) * height
  return x, y


def _svg_rect(
  *,
  bounds: tuple[float, float, float, float],
  view_bounds: tuple[float, float, float, float],
  width: int,
  height: int,
  color: str,
  label: str,
  fill_opacity: float = 0.18,
  stroke_width: float = 1.2,
  stroke_dasharray: str = "",
  label_visible: bool = True,
) -> str:
  min_x, min_y, max_x, max_y = bounds
  x, y = _svg_project_point(
    point=(min_x, max_y),
    view_bounds=view_bounds,
    width=width,
    height=height,
  )
  max_screen_x, min_screen_y = _svg_project_point(
    point=(max_x, min_y),
    view_bounds=view_bounds,
    width=width,
    height=height,
  )
  rect_width = max(max_screen_x - x, 1.0)
  rect_height = max(min_screen_y - y, 1.0)
  text_x = x + 4.0
  text_y = y + 13.0
  dash_attr = f' stroke-dasharray="{stroke_dasharray}"' if stroke_dasharray else ""
  escaped_label = html.escape(label)
  text = ""
  if label_visible:
    text = (
      f'\n<text x="{text_x:.2f}" y="{text_y:.2f}" font-size="10" '
      f'font-family="monospace" fill="{color}">{escaped_label}</text>'
    )
  return (
    f'<rect x="{x:.2f}" y="{y:.2f}" width="{rect_width:.2f}" '
    f'height="{rect_height:.2f}" fill="{color}" fill-opacity="{fill_opacity:.2f}" '
    f'stroke="{color}" stroke-width="{stroke_width:.2f}"{dash_attr}>'
    f'<title>{escaped_label}</title></rect>'
    f'{text}'
  )


def _svg_point(
  *,
  point: list[float],
  axes: tuple[int, int],
  view_bounds: tuple[float, float, float, float],
  width: int,
  height: int,
  color: str,
  label: str,
  index: int,
) -> str:
  screen_x, screen_y = _svg_project_point(
    point=(point[axes[0]], point[axes[1]]),
    view_bounds=view_bounds,
    width=width,
    height=height,
  )
  escaped_label = html.escape(label)
  return (
    f'<circle cx="{screen_x:.2f}" cy="{screen_y:.2f}" r="4.5" fill="{color}" '
    f'stroke="#ffffff" stroke-width="1.2"><title>{escaped_label}</title></circle>\n'
    f'<text x="{screen_x + 6.0:.2f}" y="{screen_y - 6.0:.2f}" font-size="10" '
    f'font-family="monospace" fill="{color}">{index}</text>'
  )


def _legacy_hitbox_rows(component_report: dict[str, Any] | None) -> list[dict[str, Any]]:
  if component_report is None:
    return []
  rows: dict[int, dict[str, Any]] = {}
  for row in component_report["rows"]:
    rows.setdefault(
      int(row["hitbox_index"]),
      {
        "hitbox_index": int(row["hitbox_index"]),
        "bounds": row["parent_hitbox_bounds"],
      },
    )
  return [rows[index] for index in sorted(rows)]


def _svg_for_view(
  mapping: dict[str, Any],
  view: str,
  *,
  component_report: dict[str, Any] | None = None,
  diagnostics: dict[str, Any] | None = None,
) -> str:
  axes_by_view = {
    "top": (0, 1, "x forward (m)", "y lateral (m)"),
    "side": (0, 2, "x forward (m)", "z up (m)"),
    "front": (1, 2, "y lateral (m)", "z up (m)"),
  }
  axis_x, axis_y, label_x, label_y = axes_by_view[view]
  width, height = 1200, 760
  envelope = mapping["outer_envelope"]["bounds"]
  view_bounds_raw = _project_bounds(envelope, (axis_x, axis_y))
  margin_x = max((view_bounds_raw[2] - view_bounds_raw[0]) * 0.08, 0.5)
  margin_y = max((view_bounds_raw[3] - view_bounds_raw[1]) * 0.08, 0.5)
  view_bounds = (
    view_bounds_raw[0] - margin_x,
    view_bounds_raw[1] - margin_y,
    view_bounds_raw[2] + margin_x,
    view_bounds_raw[3] + margin_y,
  )
  elements = [
    '<rect x="0" y="0" width="1200" height="760" fill="#ffffff"/>',
    f'<text x="24" y="34" font-size="18" font-family="monospace" fill="#202020">'
    f'F-16 outer-region candidate {view} view</text>',
    f'<text x="24" y="58" font-size="12" font-family="monospace" fill="#555555">'
    f'{label_x}; {label_y}; review-only boxes, component overlays, and review points</text>',
    _svg_rect(
      bounds=view_bounds_raw,
      view_bounds=view_bounds,
      width=width,
      height=height,
      color="#111111",
      label="outer_envelope",
      fill_opacity=0.03,
      stroke_width=1.5,
    ),
  ]
  for legacy in _legacy_hitbox_rows(component_report):
    elements.append(
      _svg_rect(
        bounds=_project_bounds(legacy["bounds"], (axis_x, axis_y)),
        view_bounds=view_bounds,
        width=width,
        height=height,
        color="#c47a00",
        label=f'legacy_hitbox_{legacy["hitbox_index"]}',
        fill_opacity=0.02,
        stroke_width=1.2,
        stroke_dasharray="5 4",
        label_visible=False,
      )
    )
  for index, region in enumerate(mapping["outer_regions"]):
    elements.append(
      _svg_rect(
        bounds=_project_bounds(region["bounds"], (axis_x, axis_y)),
        view_bounds=view_bounds,
        width=width,
        height=height,
        color=_svg_color(index),
        label=region["id"],
      )
    )
  if component_report is not None:
    for row in component_report["rows"]:
      color = "#9b1c31" if row["review_status"] == "needs_review" else "#5b3f93"
      elements.append(
        _svg_rect(
          bounds=_project_bounds(row["component_bounds"], (axis_x, axis_y)),
          view_bounds=view_bounds,
          width=width,
          height=height,
          color=color,
          label=f'{row["component_name"]} -> {row["bound_region_id"]}',
          fill_opacity=0.05,
          stroke_width=0.9,
          label_visible=False,
        )
      )
  if diagnostics is not None:
    for row in diagnostics["rows"]:
      elements.append(
        _svg_point(
          point=row["point_m"],
          axes=(axis_x, axis_y),
          view_bounds=view_bounds,
          width=width,
          height=height,
          color="#0f172a",
          label=f'{row["point_index"]}: {row["point_id"]}',
          index=int(row["point_index"]),
        )
      )
  elements.extend(
    [
      '<text x="24" y="716" font-size="11" font-family="monospace" fill="#555555">'
      'Legend: black envelope, colored outer regions, orange dashed legacy boxes, '
      'purple/red component boxes, numbered review points</text>',
      '<text x="24" y="736" font-size="11" font-family="monospace" fill="#555555">'
      'Review-only geometry; not a runtime collision mesh or real F-16 engineering model</text>',
    ]
  )
  return (
    '<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="760" '
    'viewBox="0 0 1200 760">\n'
    + "\n".join(elements)
    + "\n</svg>\n"
  )


def write_svg_views(
  mapping: dict[str, Any],
  output_dir: Path,
  *,
  component_report: dict[str, Any] | None = None,
  diagnostics: dict[str, Any] | None = None,
) -> list[Path]:
  output_dir.mkdir(parents=True, exist_ok=True)
  paths: list[Path] = []
  for view in ("top", "side", "front"):
    path = output_dir / f"{view}.svg"
    path.write_text(
      _svg_for_view(
        mapping,
        view,
        component_report=component_report,
        diagnostics=diagnostics,
      ),
      encoding="utf-8",
    )
    paths.append(path)
  return paths


def _html_table(headers: list[str], rows: list[list[Any]]) -> str:
  header_html = "".join(f"<th>{html.escape(header)}</th>" for header in headers)
  row_html = []
  for row in rows:
    row_html.append(
      "<tr>"
      + "".join(f"<td>{html.escape(str(value))}</td>" for value in row)
      + "</tr>"
    )
  return (
    '<table>\n<thead><tr>'
    + header_html
    + "</tr></thead>\n<tbody>\n"
    + "\n".join(row_html)
    + "\n</tbody>\n</table>"
  )


def write_review_packet(
  *,
  manifest: dict[str, Any],
  mapping: dict[str, Any],
  component_report: dict[str, Any],
  diagnostics: dict[str, Any],
  output_dir: Path,
) -> Path:
  output_dir.mkdir(parents=True, exist_ok=True)
  html_path = output_dir / "scene.html"
  component_rows = [
    [
      row["component_name"],
      row["system"],
      row["bound_region_id"],
      row["review_status"],
      ";".join(row["anomalies"]),
    ]
    for row in component_report["rows"]
  ]
  diagnostic_rows = [
    [
      row["point_index"],
      row["point_id"],
      row["point_m"],
      row["nearest_outer_region_id"],
      row["nearest_outer_distance_m"],
      row["nearest_component_name"],
      row["nearest_component_distance_m"],
      row["candidate_component_count"],
      row["interpretation"],
    ]
    for row in diagnostics["rows"]
  ]
  body = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>F-16 Target Geometry Review Packet</title>
  <style>
    body {{
      margin: 0;
      background: #f6f7f9;
      color: #202124;
      font-family: Arial, sans-serif;
    }}
    main {{
      max-width: 1280px;
      margin: 0 auto;
      padding: 24px;
    }}
    h1, h2 {{
      margin: 0 0 12px;
      font-weight: 700;
    }}
    section {{
      margin: 0 0 24px;
      padding: 18px;
      background: #ffffff;
      border: 1px solid #d8dde6;
      border-radius: 6px;
    }}
    .meta {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 8px 16px;
      font-family: monospace;
      font-size: 13px;
    }}
    .views {{
      display: grid;
      grid-template-columns: 1fr;
      gap: 16px;
    }}
    img {{
      width: 100%;
      height: auto;
      border: 1px solid #cdd3dd;
      background: #ffffff;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 13px;
    }}
    th, td {{
      border: 1px solid #d8dde6;
      padding: 6px 8px;
      text-align: left;
      vertical-align: top;
    }}
    th {{
      background: #eef2f7;
    }}
    .note {{
      color: #4b5563;
      font-size: 13px;
    }}
  </style>
</head>
<body>
<main>
  <section>
    <h1>F-16 Target Geometry Review Packet</h1>
    <p class="note">Review-only geometry. This packet is not a runtime collision mesh, not a real F-16 engineering model, and not a real-weapon lethality claim.</p>
    <div class="meta">
      <div>generated_on: {html.escape(mapping["generated_on"])}</div>
      <div>source_uid: {html.escape(manifest["source"]["uid"])}</div>
      <div>outer_regions: {len(mapping["outer_regions"])}</div>
      <div>components: {component_report["summary"]["component_count"]}</div>
      <div>review_points: {diagnostics["summary"]["review_point_count"]}</div>
      <div>needs_review_components: {component_report["summary"]["needs_review_count"]}</div>
    </div>
  </section>
  <section>
    <h2>Three-View Overlay</h2>
    <div class="views">
      <img src="top.svg" alt="Top view geometry overlay">
      <img src="side.svg" alt="Side view geometry overlay">
      <img src="front.svg" alt="Front view geometry overlay">
    </div>
  </section>
  <section>
    <h2>Review Point Diagnostics</h2>
    {_html_table(
      [
        "index",
        "point",
        "local_m",
        "outer_region",
        "outer_dist_m",
        "nearest_component",
        "component_dist_m",
        "candidate_count",
        "interpretation",
      ],
      diagnostic_rows,
    )}
  </section>
  <section>
    <h2>Component Binding Summary</h2>
    {_html_table(
      ["component", "system", "bound_region", "status", "anomalies"],
      component_rows,
    )}
  </section>
</main>
</body>
</html>
"""
  html_path.write_text(body, encoding="utf-8")
  return html_path


def _parse_args(argv: list[str]) -> argparse.Namespace:
  parser = argparse.ArgumentParser(
    description="Generate a review-only airframe geometry manifest from a glTF audit asset."
  )
  parser.add_argument("--aircraft", type=Path, default=DEFAULT_AIRCRAFT)
  parser.add_argument("--asset", type=Path, default=DEFAULT_AUDIT_SCENE)
  parser.add_argument("--visual-glb", type=Path, default=DEFAULT_VISUAL_GLB)
  parser.add_argument("--intake-metadata", type=Path, default=DEFAULT_INTAKE_METADATA)
  parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
  parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT_DIR)
  parser.add_argument("--generated-on", default=DEFAULT_GENERATED_ON)
  parser.add_argument(
    "--stdout-only",
    action="store_true",
    help="Print manifest JSON to stdout instead of writing manifest.json.",
  )
  return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
  args = _parse_args(sys.argv[1:] if argv is None else argv)
  manifest = build_airframe_geometry_manifest(
    aircraft_path=args.aircraft,
    audit_scene_path=args.asset,
    visual_glb_path=args.visual_glb,
    intake_metadata_path=args.intake_metadata,
    registry_path=args.registry,
    generated_on=args.generated_on,
  )
  if args.stdout_only:
    print(json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False))
    return 0

  output_path = write_manifest(manifest, args.out)
  mapping = build_geometry_mapping_candidate(manifest)
  mapping_path = write_mapping_candidate(mapping, args.out)
  aircraft = _load_json(args.aircraft)
  component_report = build_component_binding_report(aircraft, mapping)
  component_json_path, component_csv_path = write_component_binding_report(
    component_report, args.out
  )
  diagnostics = build_review_point_diagnostics(mapping, component_report)
  diagnostics_json_path, diagnostics_csv_path = write_review_point_diagnostics(
    diagnostics, args.out
  )
  svg_paths = write_svg_views(
    mapping,
    args.out,
    component_report=component_report,
    diagnostics=diagnostics,
  )
  scene_path = write_review_packet(
    manifest=manifest,
    mapping=mapping,
    component_report=component_report,
    diagnostics=diagnostics,
    output_dir=args.out,
  )
  print(
    json.dumps(
      {
        "status": manifest["status"],
        "schema_version": manifest["schema_version"],
        "output": _display_path(output_path, REPO_ROOT),
        "mapping_output": _display_path(mapping_path, REPO_ROOT),
        "component_binding_json": _display_path(component_json_path, REPO_ROOT),
        "component_binding_csv": _display_path(component_csv_path, REPO_ROOT),
        "review_point_diagnostics_json": _display_path(
          diagnostics_json_path, REPO_ROOT
        ),
        "review_point_diagnostics_csv": _display_path(
          diagnostics_csv_path, REPO_ROOT
        ),
        "scene_html": _display_path(scene_path, REPO_ROOT),
        "svg_outputs": [_display_path(path, REPO_ROOT) for path in svg_paths],
        "component_count": component_report["summary"]["component_count"],
        "component_needs_review_count": component_report["summary"][
          "needs_review_count"
        ],
        "review_point_count": diagnostics["summary"]["review_point_count"],
        "inside_outer_region_point_count": diagnostics["summary"][
          "inside_outer_region_point_count"
        ],
        "triangle_count": manifest["gltf_summary"]["triangle_count"],
        "position_accessor_vertex_count": manifest["gltf_summary"][
          "position_accessor_vertex_count"
        ],
      },
      indent=2,
      sort_keys=True,
    )
  )
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
