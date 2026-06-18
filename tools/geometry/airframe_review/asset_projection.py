"""Projection helpers from review glTF assets into simulation coordinates."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from tools.geometry.airframe_review import gltf_io
from tools.geometry.airframe_review.constants import TRIANGLE_MODE
from tools.geometry.airframe_review.primitives import Bounds, _round_vec


def sim_point_from_asset(
  point: list[float], *, asset_center: list[float], scale: float
) -> list[float]:
  # Project-local aircraft review coordinates use x forward, y right, z up.
  return [
    -(point[2] - asset_center[2]) * scale,
    (point[0] - asset_center[0]) * scale,
    (point[1] - asset_center[1]) * scale,
  ]


def sim_bounds_from_asset_bounds(
  asset_bounds: dict[str, list[float]], *, asset_center: list[float], scale: float
) -> dict[str, list[float]]:
  bounds = Bounds.empty()
  min_values = asset_bounds["min"]
  max_values = asset_bounds["max"]
  for x in (min_values[0], max_values[0]):
    for y in (min_values[1], max_values[1]):
      for z in (min_values[2], max_values[2]):
        bounds.include(
          sim_point_from_asset([x, y, z], asset_center=asset_center, scale=scale)
        )
  return bounds.to_record()


def extract_gltf_sim_vertex_records(
  gltf_path: Path,
  manifest: dict[str, Any],
) -> list[dict[str, Any]]:
  gltf = gltf_io.load_json(gltf_path)
  buffers = [
    gltf_io._load_buffer(gltf_path, buffer_def) for buffer_def in gltf.get("buffers", [])
  ]
  asset_center = manifest["gltf_summary"]["transformed_bounds"]["center"]
  scale = float(manifest["public_dimension_check"]["registry_scale"])
  records: list[dict[str, Any]] = []

  for node_index, node, world_matrix in gltf_io._walk_nodes(
    gltf, gltf_io._scene_root_nodes(gltf), gltf_io._identity()
  ):
    mesh_index = node.get("mesh")
    if mesh_index is None:
      continue
    mesh = gltf["meshes"][mesh_index]
    for primitive in mesh.get("primitives", []):
      attributes = primitive.get("attributes", {})
      if "POSITION" not in attributes:
        continue
      positions = gltf_io._accessor_values(
        gltf=gltf,
        buffers=buffers,
        accessor_index=int(attributes["POSITION"]),
      )
      for position in positions:
        transformed = gltf_io._transform_point(
          world_matrix,
          (position[0], position[1], position[2]),
        )
        records.append(
          {
            "point_m": _round_vec(
              sim_point_from_asset(
                [transformed[0], transformed[1], transformed[2]],
                asset_center=asset_center,
                scale=scale,
              )
            ),
            "node_index": node_index,
            "node_name": node.get("name", f"node_{node_index}"),
            "mesh_index": mesh_index,
            "mesh_name": mesh.get("name", f"mesh_{mesh_index}"),
          }
        )
  return records


def extract_gltf_sim_triangle_records(
  gltf_path: Path,
  manifest: dict[str, Any],
) -> list[dict[str, Any]]:
  gltf = gltf_io.load_json(gltf_path)
  buffers = [
    gltf_io._load_buffer(gltf_path, buffer_def) for buffer_def in gltf.get("buffers", [])
  ]
  asset_center = manifest["gltf_summary"]["transformed_bounds"]["center"]
  scale = float(manifest["public_dimension_check"]["registry_scale"])
  records: list[dict[str, Any]] = []

  for node_index, node, world_matrix in gltf_io._walk_nodes(
    gltf, gltf_io._scene_root_nodes(gltf), gltf_io._identity()
  ):
    mesh_index = node.get("mesh")
    if mesh_index is None:
      continue
    mesh = gltf["meshes"][mesh_index]
    for primitive in mesh.get("primitives", []):
      if int(primitive.get("mode", TRIANGLE_MODE)) != TRIANGLE_MODE:
        continue
      attributes = primitive.get("attributes", {})
      if "POSITION" not in attributes:
        continue
      positions = gltf_io._accessor_values(
        gltf=gltf,
        buffers=buffers,
        accessor_index=int(attributes["POSITION"]),
      )
      sim_positions = []
      for position in positions:
        transformed = gltf_io._transform_point(
          world_matrix,
          (position[0], position[1], position[2]),
        )
        sim_positions.append(
          _round_vec(
            sim_point_from_asset(
              [transformed[0], transformed[1], transformed[2]],
              asset_center=asset_center,
              scale=scale,
            )
          )
        )

      if "indices" in primitive:
        index_values = gltf_io._accessor_values(
          gltf=gltf,
          buffers=buffers,
          accessor_index=int(primitive["indices"]),
        )
        indices = [int(value[0]) for value in index_values]
      else:
        indices = list(range(len(sim_positions)))

      for triangle_offset in range(0, len(indices) - 2, 3):
        try:
          points = [
            sim_positions[indices[triangle_offset]],
            sim_positions[indices[triangle_offset + 1]],
            sim_positions[indices[triangle_offset + 2]],
          ]
        except IndexError:
          continue
        records.append(
          {
            "points_m": points,
            "node_index": node_index,
            "node_name": node.get("name", f"node_{node_index}"),
            "mesh_index": mesh_index,
            "mesh_name": mesh.get("name", f"mesh_{mesh_index}"),
          }
        )
  return records


def extract_gltf_sim_vertices(gltf_path: Path, manifest: dict[str, Any]) -> list[list[float]]:
  return [
    record["point_m"]
    for record in extract_gltf_sim_vertex_records(gltf_path, manifest)
  ]
