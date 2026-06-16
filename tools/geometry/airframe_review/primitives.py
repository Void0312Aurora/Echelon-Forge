"""Primitive geometry records and serialization helpers."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Iterable


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


def _round_points(points: Iterable[Iterable[float]], digits: int = 6) -> list[list[float]]:
  return [_round_vec(point, digits) for point in points]


def _strip_internal_keys(value: Any) -> Any:
  """Return a copy of ``value`` with internal keys removed.

  Internal keys start with an underscore and carry in-process state that must
  not be serialized (for example the cached mesh vertex records attached to a
  fine-proxy dict). dicts and lists are recursed shallowly; other types pass
  through unchanged.
  """
  if isinstance(value, dict):
    return {
      key: _strip_internal_keys(item)
      for key, item in value.items()
      if not isinstance(key, str) or not key.startswith("_")
    }
  if isinstance(value, list):
    return [_strip_internal_keys(item) for item in value]
  return value
