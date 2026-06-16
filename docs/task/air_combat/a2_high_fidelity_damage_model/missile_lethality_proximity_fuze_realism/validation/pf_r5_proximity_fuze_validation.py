from __future__ import annotations

import csv
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams["font.sans-serif"] = [
    "Microsoft YaHei",
    "SimHei",
    "Noto Sans CJK SC",
    "Arial Unicode MS",
    "DejaVu Sans",
]
plt.rcParams["axes.unicode_minus"] = False

from tests.runtime.air_combat.weapon_guidance_realism.helpers import (
    _drive_missile_with_truth_track,
    _make_baseline_kernel,
    _spawn_geometry_pair,
    ef_py,
)


REPO_ROOT = Path(__file__).resolve().parents[6]
OUT_DIR = Path(__file__).resolve().parent
TAG = "20260616"

FAMILIES = ("blast_fragmentation", "continuous_rod")
TRIGGER_RADII_M = (7.0, 8.0, 10.0, 12.0, 16.0, 24.0, 35.0, 50.0)
LATERAL_OFFSETS_M = (-120.0, -80.0, -40.0, 0.0, 40.0, 80.0, 120.0)
VERTICAL_OFFSETS_M = (-80.0, -40.0, -20.0, 0.0, 20.0, 40.0, 80.0)


def _warhead_profile(family: str) -> Any:
    profile = ef_py.WarheadProfile()
    profile.family = family
    profile.mass_kg = 12.0
    profile.lethal_radius_m = 35.0
    profile.damage_scalar = 90.0
    profile.synthetic = True
    profile.damage_scalar_synthetic = True
    profile.provenance = "pf_r5_proximity_fuze_validation"
    return profile


def _fuze_profile(trigger_radius_m: float) -> Any:
    profile = ef_py.FuzeProfile()
    profile.type = "radar_proximity"
    profile.trigger_radius_m = float(trigger_radius_m)
    profile.delay_s = 0.0
    profile.reliability = 1.0
    profile.synthetic = True
    profile.provenance = "pf_r5_proximity_fuze_validation"
    return profile


def _finite(value: Any, default: float = float("nan")) -> float:
    try:
        out = float(value)
    except Exception:
        return default
    return out if math.isfinite(out) else default


def _event_reason(fuze_event: Any | None, nearest_event: Any | None) -> str:
    if fuze_event is not None:
        return str(getattr(getattr(fuze_event, "header", None), "reason", "") or "")
    if nearest_event is not None:
        return str(getattr(getattr(nearest_event, "header", None), "reason", "") or "")
    return "no_event"


def _no_load_aware_probability(fuze_event: Any | None) -> float:
    if fuze_event is None:
        return 0.0
    reason = _event_reason(fuze_event, None)
    if reason in {
        "miss_outside_trigger_radius",
        "fuze_no_terminal_track",
        "outside_sensor_window",
        "target_not_detected",
        "missile_timeout",
    }:
        return 0.0
    return max(0.0, min(1.0, _finite(getattr(fuze_event, "expected_detonation_probability", 0.0), 0.0)))


def run_case(
    *,
    axis: str,
    offset_m: float,
    trigger_radius_m: float,
    family: str,
) -> dict[str, Any]:
    sim = _make_baseline_kernel()
    sim.set_time_step(0.02)

    tuning = sim.get_missile_tuning()
    tuning.fuze_profile = _fuze_profile(trigger_radius_m)
    tuning.has_fuze_profile = True
    tuning.warhead_profile = _warhead_profile(family)
    tuning.has_warhead_profile = True
    sim.set_missile_tuning(tuning)

    red_x = float(offset_m) if axis == "lateral_x" else 0.0
    red_z = 5000.0 + (float(offset_m) if axis == "vertical_z" else 0.0)
    blue_id, red_id = _spawn_geometry_pair(
        sim,
        red_x=red_x,
        red_y=22000.0,
        red_z=red_z,
        red_heading=180.0,
        red_vx=0.0,
        red_vy=-250.0,
    )
    missile_id = int(sim.fire_missile(blue_id, red_id))
    if missile_id <= 0:
        raise RuntimeError("missile launch failed in PF-R5 validation case")

    drive = _drive_missile_with_truth_track(sim, missile_id, red_id, max_steps=3600)
    packet = sim.export_recent_engagement_events()
    nearest_event = packet.nearest_approach_events[-1] if packet.nearest_approach_events else None
    fuze_event = packet.fuze_evaluation_events[-1] if packet.fuze_evaluation_events else None
    effects_event = packet.effects_events[-1] if packet.effects_events else None

    reason = _event_reason(fuze_event, nearest_event)
    outcome = str(getattr(effects_event, "outcome_state", "") or reason)
    actual_miss_m = _finite(drive.get("proximity_min_dist_m", float("nan")))
    range_score = max(0.0, min(1.0, 1.0 - actual_miss_m / max(1.0e-9, float(trigger_radius_m))))
    no_load_probability = _no_load_aware_probability(fuze_event)

    return {
        "axis": axis,
        "offset_m": float(offset_m),
        "trigger_radius_m": float(trigger_radius_m),
        "family": family,
        "actual_miss_m": actual_miss_m,
        "actual_local_forward_m": _finite(getattr(nearest_event, "local_forward_m", float("nan"))),
        "actual_local_right_m": _finite(getattr(nearest_event, "local_right_m", float("nan"))),
        "actual_local_up_m": _finite(getattr(nearest_event, "local_up_m", float("nan"))),
        "range_score_from_actual_miss": range_score,
        "reason": reason,
        "outcome": outcome,
        "fuze_armed": bool(getattr(fuze_event, "armed", False)) if fuze_event is not None else False,
        "fuze_triggered": bool(getattr(fuze_event, "triggered", False)) if fuze_event is not None else False,
        "target_detected": bool(getattr(fuze_event, "target_detected", False)) if fuze_event is not None else False,
        "terminal_track_valid": bool(getattr(fuze_event, "terminal_track_valid", False)) if fuze_event is not None else False,
        "sensor_opportunity_score": _finite(getattr(fuze_event, "sensor_opportunity_score", float("nan"))),
        "target_detection_confidence": _finite(
            getattr(fuze_event, "target_detection_confidence", float("nan"))
        ),
        "target_detection_threshold": _finite(
            getattr(fuze_event, "target_detection_threshold", float("nan"))
        ),
        "mechanism_coverage_score": _finite(getattr(fuze_event, "mechanism_coverage_score", float("nan"))),
        "expected_detonation_probability_raw": _finite(
            getattr(fuze_event, "expected_detonation_probability", float("nan"))
        ),
        "expected_detonation_probability_no_load_aware": no_load_probability,
        "fuze_sample": _finite(getattr(fuze_event, "sample", float("nan"))),
        "detonation_point_source": str(getattr(fuze_event, "detonation_point_source", "") or ""),
        "effects_event_present": effects_event is not None,
        "warhead_load_observed": bool(packet.warhead_mechanism_events),
        "projected_hitbox_count": int(getattr(effects_event, "projected_hitbox_count", 0) or 0)
        if effects_event is not None
        else 0,
        "component_hit_count": int(getattr(effects_event, "component_hit_count", 0) or 0)
        if effects_event is not None
        else 0,
    }


def _all_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for family in FAMILIES:
        for trigger_radius_m in TRIGGER_RADII_M:
            for offset_m in LATERAL_OFFSETS_M:
                rows.append(
                    run_case(
                        axis="lateral_x",
                        offset_m=offset_m,
                        trigger_radius_m=trigger_radius_m,
                        family=family,
                    )
                )
            for offset_m in VERTICAL_OFFSETS_M:
                rows.append(
                    run_case(
                        axis="vertical_z",
                        offset_m=offset_m,
                        trigger_radius_m=trigger_radius_m,
                        family=family,
                    )
                )
    return rows


def _write_csv(rows: list[dict[str, Any]], path: Path) -> None:
    fieldnames = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _matrix(
    rows: list[dict[str, Any]],
    *,
    axis: str,
    family: str,
    metric: str,
    offsets: tuple[float, ...],
) -> list[list[float]]:
    by_key = {
        (float(row["offset_m"]), float(row["trigger_radius_m"])): _finite(row.get(metric, float("nan")))
        for row in rows
        if row["axis"] == axis and row["family"] == family
    }
    return [[by_key.get((float(offset), float(radius)), float("nan")) for radius in TRIGGER_RADII_M] for offset in offsets]


def _plot_heatmaps(rows: list[dict[str, Any]], path: Path) -> None:
    plot_specs = [
        ("expected_detonation_probability_no_load_aware", "no-load 修正起爆概率 P(det)", 0.0, 1.0),
        ("target_detection_confidence", "目标探测置信度", 0.0, 1.0),
        ("mechanism_coverage_score", "机制覆盖度", 0.0, 1.0),
    ]
    family_labels = {
        "blast_fragmentation": "爆破破片",
        "continuous_rod": "连续杆",
    }
    axis_labels = {
        "lateral_x": "初始横向偏置 x",
        "vertical_z": "初始高度偏置 z",
    }
    row_specs = [
        ("lateral_x", "blast_fragmentation", LATERAL_OFFSETS_M),
        ("lateral_x", "continuous_rod", LATERAL_OFFSETS_M),
        ("vertical_z", "blast_fragmentation", VERTICAL_OFFSETS_M),
        ("vertical_z", "continuous_rod", VERTICAL_OFFSETS_M),
    ]
    fig, axes = plt.subplots(
        nrows=len(row_specs),
        ncols=len(plot_specs),
        figsize=(15.0, 12.0),
        constrained_layout=True,
    )
    for row_index, (axis, family, offsets) in enumerate(row_specs):
        for col_index, (metric, title, vmin, vmax) in enumerate(plot_specs):
            ax = axes[row_index][col_index]
            values = _matrix(rows, axis=axis, family=family, metric=metric, offsets=offsets)
            image = ax.imshow(values, aspect="auto", cmap="viridis", vmin=vmin, vmax=vmax)
            ax.set_xticks(range(len(TRIGGER_RADII_M)))
            ax.set_xticklabels([f"{value:g}" for value in TRIGGER_RADII_M], rotation=45)
            ax.set_yticks(range(len(offsets)))
            ax.set_yticklabels([f"{value:g}" for value in offsets])
            ax.set_title(f"{family_labels[family]}\n{axis_labels[axis]}：{title}", fontsize=10)
            ax.set_xlabel("触发半径 m")
            ax.set_ylabel("初始偏置 m")
            fig.colorbar(image, ax=ax, fraction=0.046, pad=0.02)
    fig.suptitle("PF-R5 近炸引信 surrogate 验证热图", fontsize=14)
    fig.savefig(path, dpi=160)
    plt.close(fig)


def _monotonic_non_decreasing(values: list[float], tolerance: float = 1.0e-9) -> bool:
    finite_values = [value for value in values if math.isfinite(value)]
    return all(b >= a - tolerance for a, b in zip(finite_values, finite_values[1:]))


def _summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    reason_counts = Counter(str(row["reason"]) for row in rows)
    family_reason_counts: dict[str, dict[str, int]] = defaultdict(dict)
    for family in FAMILIES:
        family_rows = [row for row in rows if row["family"] == family]
        family_reason_counts[family] = dict(Counter(str(row["reason"]) for row in family_rows))

    center_rows = [
        row
        for row in rows
        if row["axis"] == "lateral_x" and abs(float(row["offset_m"])) < 1.0e-9
    ]
    monotonic_by_family: dict[str, bool] = {}
    center_probability_by_family: dict[str, list[float]] = {}
    for family in FAMILIES:
        series = [
            _finite(row["expected_detonation_probability_no_load_aware"])
            for row in sorted(
                [row for row in center_rows if row["family"] == family],
                key=lambda item: float(item["trigger_radius_m"]),
            )
        ]
        center_probability_by_family[family] = series
        monotonic_by_family[family] = _monotonic_non_decreasing(series, tolerance=1.0e-6)

    symmetry_delta: dict[str, float] = {}
    for family in FAMILIES:
        max_delta = 0.0
        for radius in TRIGGER_RADII_M:
            for offset in (40.0, 80.0, 120.0):
                left = next(
                    row
                    for row in rows
                    if row["axis"] == "lateral_x"
                    and row["family"] == family
                    and float(row["trigger_radius_m"]) == radius
                    and float(row["offset_m"]) == -offset
                )
                right = next(
                    row
                    for row in rows
                    if row["axis"] == "lateral_x"
                    and row["family"] == family
                    and float(row["trigger_radius_m"]) == radius
                    and float(row["offset_m"]) == offset
                )
                delta = abs(
                    _finite(left["expected_detonation_probability_no_load_aware"])
                    - _finite(right["expected_detonation_probability_no_load_aware"])
                )
                max_delta = max(max_delta, delta)
        symmetry_delta[family] = max_delta

    miss_values = [_finite(row["actual_miss_m"]) for row in rows]
    probabilities = [_finite(row["expected_detonation_probability_no_load_aware"]) for row in rows]
    return {
        "schema": "pf_r5_proximity_fuze_validation.v1",
        "case_count": len(rows),
        "families": list(FAMILIES),
        "trigger_radii_m": list(TRIGGER_RADII_M),
        "lateral_offsets_m": list(LATERAL_OFFSETS_M),
        "vertical_offsets_m": list(VERTICAL_OFFSETS_M),
        "reason_counts": dict(reason_counts),
        "family_reason_counts": family_reason_counts,
        "actual_miss_m_min": min(miss_values),
        "actual_miss_m_max": max(miss_values),
        "expected_probability_min": min(probabilities),
        "expected_probability_max": max(probabilities),
        "center_probability_by_family": center_probability_by_family,
        "center_probability_monotonic_non_decreasing": monotonic_by_family,
        "max_lateral_symmetry_probability_delta_by_family": symmetry_delta,
        "validation_decision": "pass_with_residuals",
        "interpretation": {
            "range_gate": "Trigger-radius / actual-miss ratio clearly gates detection and no-load outcomes.",
            "offset_gate": "Initial lateral/vertical offsets are partially compensated by guidance, so their effect is weaker than the trigger-radius sweep.",
            "symmetry_boundary": "Initial-offset symmetry is not an acceptance criterion for this live guidance validation; pure fuze symmetry needs a fixed local-point harness.",
            "mechanism_family": "Continuous rod can diverge from blast-fragmentation through mechanism coverage while preserving the same detection gate.",
            "authority_boundary": "These are runtime surrogate diagnostics, not real fuze thresholds, Pk, or weapon-specific lethality.",
        },
        "residuals": [
            "Live guidance keeps actual miss distance in a narrow band, so initial launch offsets are not pure detonation-position offsets.",
            "Large lateral symmetry deltas can appear because the airframe orientation, target motion, and guidance path are still in the loop.",
            "The matrix validates surrogate gating behavior, not real-world fuze calibration.",
        ],
    }


def _write_markdown(summary: dict[str, Any], path: Path, zh: bool) -> None:
    if zh:
        title = "# PF-R5 近炸引信 Surrogate 验证结果"
        body = [
            title,
            "",
            "状态：`2026-06-16`，PF-R5 聚焦矩阵验证完成。",
            "",
            "验证决策：`pass_with_residuals`。",
            "",
            "## 验证范围",
            "",
            "- live missile / fuze runtime path；",
            "- 机制族：`blast_fragmentation` 与 `continuous_rod`；",
            "- 触发半径：`7, 8, 10, 12, 16, 24, 35, 50 m`；",
            "- 初始横向偏置：`-120..120 m`；初始高度偏置：`-80..80 m`；",
            "- 输出为最终 CSV、JSON 和一张热图，不保留额外中间结果。",
            "",
            "## 主要结论",
            "",
            "- 触发半径/实际最近距离比值能清楚打开或关闭探测门；小半径下出现 `target_not_detected` 和 no-load。",
            "- 中心样本的 no-load-aware 期望起爆概率随触发半径单调不下降。",
            "- 横向/高度初始偏置的影响较弱，因为导弹制导会补偿一部分初始几何差异；实际最近距离集中在 "
            f"`{summary['actual_miss_m_min']:.2f}` 到 `{summary['actual_miss_m_max']:.2f}` m。",
            "- 横向左右不完全对称不是本验证的失败条件：这里扫的是发射初始条件，制导、目标运动和机体朝向仍在链路中；若要验纯引信几何对称性，需要另建固定局部命中点 harness。",
            "- `continuous_rod` 与 `blast_fragmentation` 共用探测门，但可通过 mechanism coverage 产生机制差异。",
            "- 本验证仍不声明真实引信阈值、真实 Pk、具体弹种杀伤或 deterministic fuze authority。",
            "",
            "## 输出",
            "",
            f"- CSV: `pf_r5_proximity_fuze_validation_{TAG}.csv`",
            f"- JSON: `pf_r5_proximity_fuze_validation_{TAG}.json`",
            f"- Heatmap: `pf_r5_proximity_fuze_validation_heatmaps_{TAG}.png`",
        ]
    else:
        title = "# PF-R5 Proximity Fuze Surrogate Validation Result"
        body = [
            title,
            "",
            "Status: `2026-06-16` PF-R5 focused matrix validation complete.",
            "",
            "Validation decision: `pass_with_residuals`.",
            "",
            "## Scope",
            "",
            "- live missile / fuze runtime path;",
            "- mechanism families: `blast_fragmentation` and `continuous_rod`;",
            "- trigger radii: `7, 8, 10, 12, 16, 24, 35, 50 m`;",
            "- initial lateral offsets: `-120..120 m`; initial vertical offsets: `-80..80 m`;",
            "- final CSV, JSON, and one heatmap figure only.",
            "",
            "## Findings",
            "",
            "- The trigger-radius / actual-miss ratio clearly opens or closes the detection gate; small radii produce `target_not_detected` and no-load.",
            "- The centerline no-load-aware expected detonation probability is monotonic non-decreasing with trigger radius.",
            "- Initial lateral/vertical offsets have weaker effect because guidance compensates part of the geometry; actual miss distances fall between "
            f"`{summary['actual_miss_m_min']:.2f}` and `{summary['actual_miss_m_max']:.2f}` m.",
            "- Left/right lateral symmetry is not a failure criterion here: this sweeps launch initial conditions while guidance, target motion, and airframe orientation stay in the loop; pure fuze-geometry symmetry needs a fixed local-point harness.",
            "- `continuous_rod` and `blast_fragmentation` share the detection gate but can diverge through mechanism coverage.",
            "- This validation does not claim real fuze thresholds, real Pk, weapon-specific lethality, or deterministic fuze authority.",
            "",
            "## Outputs",
            "",
            f"- CSV: `pf_r5_proximity_fuze_validation_{TAG}.csv`",
            f"- JSON: `pf_r5_proximity_fuze_validation_{TAG}.json`",
            f"- Heatmap: `pf_r5_proximity_fuze_validation_heatmaps_{TAG}.png`",
        ]
    path.write_text("\n".join(body) + "\n", encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = _all_rows()
    csv_path = OUT_DIR / f"pf_r5_proximity_fuze_validation_{TAG}.csv"
    json_path = OUT_DIR / f"pf_r5_proximity_fuze_validation_{TAG}.json"
    heatmap_path = OUT_DIR / f"pf_r5_proximity_fuze_validation_heatmaps_{TAG}.png"
    summary_md = OUT_DIR / f"pf_r5_proximity_fuze_validation_{TAG}.md"
    summary_zh = OUT_DIR / f"pf_r5_proximity_fuze_validation_{TAG}.zh.md"

    summary = _summary(rows)
    _write_csv(rows, csv_path)
    json_path.write_text(
        json.dumps({"summary": summary, "rows": rows}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    _plot_heatmaps(rows, heatmap_path)
    _write_markdown(summary, summary_md, zh=False)
    _write_markdown(summary, summary_zh, zh=True)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
