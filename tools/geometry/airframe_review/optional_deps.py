"""Optional geometry dependencies for projected-contour diagnostics."""

from __future__ import annotations


try:
  from scipy.spatial import Delaunay
  from shapely.geometry import Polygon as ShapelyPolygon
  from shapely.ops import polygonize as shapely_polygonize
  from shapely.ops import unary_union as shapely_unary_union

  GEOMETRY_DEPS_AVAILABLE = True
  GEOMETRY_IMPORT_ERROR: Exception | None = None
except ImportError as geometry_import_exc:  # pragma: no cover - exercised via guard
  GEOMETRY_DEPS_AVAILABLE = False
  GEOMETRY_IMPORT_ERROR = geometry_import_exc
  Delaunay = None  # type: ignore[assignment]
  ShapelyPolygon = None  # type: ignore[assignment]
  shapely_polygonize = None  # type: ignore[assignment]
  shapely_unary_union = None  # type: ignore[assignment]


def require_geometry_deps() -> None:
  """Raise an actionable error when scipy/shapely are missing."""
  if not GEOMETRY_DEPS_AVAILABLE:
    raise RuntimeError(
      "The whole-airframe contour diagnostic requires scipy and shapely. "
      "Install the optional geometry dependency group: "
      'pip install -e ".[geometry]" (or "pip install scipy shapely"). '
      f"Original import error: {GEOMETRY_IMPORT_ERROR}"
    ) from GEOMETRY_IMPORT_ERROR
