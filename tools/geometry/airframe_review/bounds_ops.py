"""Bounds and volume helpers for airframe review report builders."""

from __future__ import annotations

import math
from typing import Iterable

from tools.geometry.airframe_review.primitives import Bounds


def bounds_from_min_max(minimum: list[float], maximum: list[float]) -> dict[str, list[float]]:
  bounds = Bounds(minimum[:], maximum[:])
  return bounds.to_record()


def box_from_center_size(center: list[float], size: list[float]) -> dict[str, list[float]]:
  minimum = [center[index] - size[index] / 2.0 for index in range(3)]
  maximum = [center[index] + size[index] / 2.0 for index in range(3)]
  return bounds_from_min_max(minimum, maximum)


def merge_bounds(bounds_records: Iterable[dict[str, list[float]]]) -> dict[str, list[float]]:
  merged = Bounds.empty()
  count = 0
  for bounds in bounds_records:
    count += 1
    merged.include(bounds["min"])
    merged.include(bounds["max"])
  if count == 0:
    raise ValueError("Cannot merge an empty bounds collection")
  return merged.to_record()


def pad_bounds(
  bounds: dict[str, list[float]],
  margins_m: list[float],
) -> dict[str, list[float]]:
  minimum = [bounds["min"][index] - margins_m[index] for index in range(3)]
  maximum = [bounds["max"][index] + margins_m[index] for index in range(3)]
  return bounds_from_min_max(minimum, maximum)


def volume(bounds: dict[str, list[float]]) -> float:
  span = bounds["span"]
  return max(span[0], 0.0) * max(span[1], 0.0) * max(span[2], 0.0)


def bounds_center_distance(
  first: dict[str, list[float]], second: dict[str, list[float]]
) -> float:
  return math.sqrt(
    sum(
      (first["center"][index] - second["center"][index]) ** 2 for index in range(3)
    )
  )


def contains_point(bounds: dict[str, list[float]], point: list[float]) -> bool:
  return all(bounds["min"][index] <= point[index] <= bounds["max"][index] for index in range(3))


def point_box_distance(point: list[float], bounds: dict[str, list[float]]) -> float:
  squared = 0.0
  for axis in range(3):
    value = point[axis]
    if value < bounds["min"][axis]:
      squared += (bounds["min"][axis] - value) ** 2
    elif value > bounds["max"][axis]:
      squared += (value - bounds["max"][axis]) ** 2
  return math.sqrt(squared)


def bounds_containment_fraction(
  inner: dict[str, list[float]], outer: dict[str, list[float]]
) -> float:
  intersection = intersection_bounds(inner, outer)
  if intersection is None:
    return 0.0
  return volume(intersection) / max(volume(inner), 1e-9)


def outside_fraction(
  inner: dict[str, list[float]], outer: dict[str, list[float]]
) -> float:
  return min(max(1.0 - bounds_containment_fraction(inner, outer), 0.0), 1.0)


def intersection_bounds(
  first: dict[str, list[float]], second: dict[str, list[float]]
) -> dict[str, list[float]] | None:
  minimum = [max(first["min"][index], second["min"][index]) for index in range(3)]
  maximum = [min(first["max"][index], second["max"][index]) for index in range(3)]
  if any(maximum[index] <= minimum[index] for index in range(3)):
    return None
  return bounds_from_min_max(minimum, maximum)
