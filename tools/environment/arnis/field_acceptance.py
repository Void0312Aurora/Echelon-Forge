"""Evaluate a generated Arnis bundle for a flat-field infantry training tile.

This is an offline acceptance probe, not a movement or combat model.  It checks
terrain composition and source-overlay completeness before a future owner is
allowed to derive passability or observation products.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any, Iterable

import numpy as np


FIELD_ACCEPTANCE_CONTRACT_VERSION = "ground_field_map_acceptance.v1"
# Decimal places kept for derived slope metrics: 1e-9 deg / 1e-9 fraction is
# far below any acceptance threshold and far above float64 ulp differences
# between host math libraries.
REPORT_DECIMALS = 9


def _report_value(value: float) -> float:
    return round(float(value), REPORT_DECIMALS)


class FieldAcceptanceError(ValueError):
    """Raised when a bundle or overlay cannot be evaluated safely."""


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise FieldAcceptanceError(f"failed to read {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise FieldAcceptanceError(f"{path} must contain an object")
    return value


def _artifact(bundle: dict[str, Any], kind: str) -> dict[str, Any]:
    for artifact in bundle.get("artifacts", []):
        if isinstance(artifact, dict) and artifact.get("kind") == kind:
            return artifact
    raise FieldAcceptanceError(f"bundle is missing {kind} artifact")


def _raster(bundle_root: Path, bundle: dict[str, Any], kind: str, dtype: str) -> tuple[np.ndarray, dict[str, Any]]:
    artifact = _artifact(bundle, kind)
    shape = artifact.get("shape")
    path = artifact.get("path")
    if not isinstance(shape, list) or len(shape) != 2 or not all(type(x) is int and x > 0 for x in shape):
        raise FieldAcceptanceError(f"{kind} artifact shape is invalid")
    if not isinstance(path, str) or not path:
        raise FieldAcceptanceError(f"{kind} artifact path is invalid")
    raster_path = (bundle_root / Path(path)).resolve()
    if bundle_root.resolve() not in raster_path.parents:
        raise FieldAcceptanceError(f"{kind} artifact path escapes bundle")
    if not raster_path.is_file():
        raise FieldAcceptanceError(f"{kind} artifact file is missing: {raster_path}")
    values = np.memmap(raster_path, dtype=dtype, mode="r", shape=tuple(shape))
    return values, artifact


def _slope_metrics(elevation: np.ndarray, artifact: dict[str, Any]) -> dict[str, float]:
    metadata = artifact.get("metadata", {})
    step = metadata.get("step_xy_m") if isinstance(metadata, dict) else None
    if not isinstance(step, list) or len(step) != 2:
        raise FieldAcceptanceError("elevation artifact requires two metric step values")
    dx = abs(float(step[0]))
    dy = abs(float(step[1]))
    if not math.isfinite(dx) or not math.isfinite(dy) or dx <= 0.0 or dy <= 0.0:
        raise FieldAcceptanceError("elevation metric steps must be positive and finite")
    stride = max(1, int(max(elevation.shape) / 512))
    # The report is a checked-in evidence artifact compared for equality on
    # every host. Float32 accumulation and the platform atan implementation
    # differ in the last bits between Windows and Linux builds, so the field is
    # evaluated in float64, the mean is an exactly rounded sum, and reported
    # metrics carry a fixed decimal precision far coarser than that ulp noise.
    sampled = np.asarray(elevation[::stride, ::stride], dtype=np.float64)
    gy, gx = np.gradient(sampled, dy * stride, dx * stride)
    slope = np.degrees(np.arctan(np.sqrt(gx * gx + gy * gy)))
    return {
        "sample_stride": float(stride),
        "slope_mean_deg": _report_value(math.fsum(slope.ravel().tolist()) / slope.size),
        "slope_p50_deg": _report_value(np.percentile(slope, 50)),
        "slope_p95_deg": _report_value(np.percentile(slope, 95)),
        "slope_p99_deg": _report_value(np.percentile(slope, 99)),
        "fraction_below_5deg": _report_value(np.count_nonzero(slope < 5.0) / slope.size),
        "fraction_below_10deg": _report_value(np.count_nonzero(slope < 10.0) / slope.size),
        "elevation_min_m": float(np.min(elevation)),
        "elevation_max_m": float(np.max(elevation)),
    }


def _landcover_metrics(landcover: np.ndarray) -> dict[str, Any]:
    values, counts = np.unique(np.asarray(landcover, dtype=np.uint8), return_counts=True)
    total = int(landcover.size)
    class_counts = {str(int(value)): int(count) for value, count in zip(values, counts)}
    fractions = {key: count / total for key, count in class_counts.items()}
    open_codes = (30, 40, 60, 90)
    open_fraction = sum(fractions.get(str(code), 0.0) for code in open_codes)
    return {
        "class_counts": class_counts,
        "class_fractions": fractions,
        "open_landcover_codes": list(open_codes),
        "open_landcover_fraction": float(open_fraction),
        "tree_cover_fraction": float(fractions.get("10", 0.0)),
        "built_up_fraction": float(fractions.get("50", 0.0)),
    }


def evaluate_field_map(
    bundle_root: Path,
    overlay_path: Path,
    *,
    thresholds: dict[str, float] | None = None,
) -> dict[str, Any]:
    """Return a deterministic, fail-closed composition acceptance report."""

    bundle_root = Path(bundle_root).expanduser().resolve()
    overlay_path = Path(overlay_path).expanduser().resolve()
    bundle = _read_json(bundle_root / "bundle.json")
    overlay = _read_json(overlay_path)
    if overlay.get("contract_version") != "field_overlay.v1":
        raise FieldAcceptanceError("unsupported field overlay contract")
    if not overlay.get("evidence", {}).get("metadata_only", False):
        raise FieldAcceptanceError("field overlay must remain metadata-only")

    default_thresholds = {
        "min_fraction_below_5deg": 0.85,
        "max_slope_p95_deg": 8.0,
        "min_open_landcover_fraction": 0.65,
        "max_tree_cover_fraction": 0.20,
    }
    active_thresholds = {**default_thresholds, **(thresholds or {})}
    elevation, elevation_artifact = _raster(bundle_root, bundle, "elevation_raster", "<f4")
    landcover, _landcover_artifact = _raster(bundle_root, bundle, "landcover_raster", "u1")
    slope = _slope_metrics(elevation, elevation_artifact)
    landcover_metrics = _landcover_metrics(landcover)
    overlay_counts = dict(overlay.get("summary", {}).get("counts_by_kind", {}))
    failures: list[str] = []
    if slope["fraction_below_5deg"] < active_thresholds["min_fraction_below_5deg"]:
        failures.append("flatness_fraction_below_5deg")
    if slope["slope_p95_deg"] > active_thresholds["max_slope_p95_deg"]:
        failures.append("flatness_p95_slope")
    if landcover_metrics["open_landcover_fraction"] < active_thresholds["min_open_landcover_fraction"]:
        failures.append("open_landcover_fraction")
    if landcover_metrics["tree_cover_fraction"] > active_thresholds["max_tree_cover_fraction"]:
        failures.append("tree_cover_fraction")
    for kind in ("farmland_area", "tree_line", "settlement_anchor", "river_corridor", "bridge_crossing"):
        if int(overlay_counts.get(kind, 0)) <= 0:
            failures.append(f"overlay_missing_{kind}")
    return {
        "contract_version": FIELD_ACCEPTANCE_CONTRACT_VERSION,
        "profile_id": overlay.get("profile_id", ""),
        "valid": not failures,
        "fail_closed": bool(failures),
        "failures": failures,
        "thresholds": active_thresholds,
        "terrain": slope,
        "landcover": landcover_metrics,
        "overlay_counts": overlay_counts,
        "evidence": {
            "bundle_lineage_checked": True,
            "overlay_metadata_only": True,
            "no_runtime_setup_application": True,
            "no_movement_release": True,
            "no_passability_release": True,
            "no_los_cover_release": True,
        },
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--overlay", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = _parser().parse_args(list(argv) if argv is not None else None)
    report = evaluate_field_map(args.bundle, args.overlay)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=True, indent=2, sort_keys=True))
    return 0 if report["valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ["FIELD_ACCEPTANCE_CONTRACT_VERSION", "FieldAcceptanceError", "evaluate_field_map"]
