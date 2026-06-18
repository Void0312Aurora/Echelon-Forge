"""glTF scene parsing helpers for airframe review assets."""

from __future__ import annotations

import base64
import json
import struct
from pathlib import Path
from typing import Any, Iterable

from tools.geometry.airframe_review.constants import (
  COMPONENT_TYPE_FORMATS,
  TRIANGLE_MODE,
  TYPE_COUNTS,
)
from tools.geometry.airframe_review.primitives import Bounds, _round_vec


def load_json(path: Path) -> dict[str, Any]:
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
  gltf = load_json(gltf_path)
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
