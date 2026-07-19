#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import os
import sys
from collections import defaultdict
from collections.abc import Iterable, Sequence
from statistics import NormalDist
from typing import Any

_REPO_ROOT_HINT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _REPO_ROOT_HINT not in sys.path:
    sys.path.insert(0, _REPO_ROOT_HINT)

from tools.diagnostics.common import finite_float
from tools.diagnostics import lethality_chain_contract as chain_contract

SCHEMA_VERSION = "mlf9.statistical_trends.v1"
INTERVAL_METHOD = "wilson"
DEFAULT_GROUP_BY = ("all",)

OUTCOME_FIELDS = (
    "fuze_negative",
    "effective_component_damage",
    "structural_breakup",
    "airframe_breakup",
    "functional_kill",
    "terminal_lifecycle",
)
DENOMINATOR_FIELDS = (
    "chain_count",
    "released_chain_count",
    "detonated_chain_count",
    "component_damage_chain_count",
    "structural_breakup_chain_count",
    "platform_consequence_chain_count",
)

def _truthy(value: Any) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "on"}
    return bool(value)

def _chain_id(row: dict[str, Any]) -> int:
    try:
        return int(row.get("chain_id", 0) or 0)
    except Exception:
        return 0

def _episode(row: dict[str, Any]) -> int:
    try:
        return int(row.get("episode", 0) or 0)
    except Exception:
        return 0

def normalize_group_by(group_by: str | Sequence[str] | None) -> tuple[str, ...]:
    if group_by is None:
        return DEFAULT_GROUP_BY
    if isinstance(group_by, str):
        fields = tuple(item.strip() for item in group_by.split(",") if item.strip())
    else:
        fields = tuple(str(item).strip() for item in group_by if str(item).strip())
    if not fields or fields == DEFAULT_GROUP_BY:
        return DEFAULT_GROUP_BY
    return fields

def validate_confidence_level(confidence_level: Any) -> float:
    level = finite_float(confidence_level)
    if not math.isfinite(level) or not (0.0 < level < 1.0):
        raise ValueError("confidence_level must be finite and satisfy 0 < level < 1")
    return level

def parse_confidence_level(value: str) -> float:
    try:
        return validate_confidence_level(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc

def _confidence_z(confidence_level: float) -> float:
    level = validate_confidence_level(confidence_level)
    return NormalDist().inv_cdf((1.0 + level) / 2.0)

def _wilson_interval(success_count: int, sample_count: int, z_score: float) -> tuple[float, float]:
    if sample_count <= 0:
        return (float("nan"), float("nan"))
    n = float(sample_count)
    phat = float(success_count) / n
    z2 = z_score * z_score
    denominator = 1.0 + z2 / n
    center = (phat + z2 / (2.0 * n)) / denominator
    margin = z_score * math.sqrt((phat * (1.0 - phat) + z2 / (4.0 * n)) / n) / denominator
    return (max(0.0, center - margin), min(1.0, center + margin))

def _miss_distance_bucket(value: Any) -> str:
    distance = finite_float(value)
    if not math.isfinite(distance):
        return "unknown"
    if distance <= 0.0:
        return "direct_or_contact"
    if distance <= 5.0:
        return "near_0_5m"
    if distance <= 15.0:
        return "near_5_15m"
    if distance <= 35.0:
        return "mid_15_35m"
    return "far_gt_35m"

def _first_nonempty(values: Iterable[Any]) -> str:
    for value in values:
        text = str(value or "")
        if text:
            return text
    return ""

def _chain_record(chain_key: tuple[int, int], rows: Sequence[dict[str, Any]]) -> dict[str, Any]:
    episode, chain_id = chain_key
    stages = {str(row.get("stage", "") or "") for row in rows}
    reasons = {str(row.get("reason", "") or "") for row in rows}
    fuze_rows = [row for row in rows if str(row.get("stage", "")) == chain_contract.STAGE_FUZE]
    platform_rows = [
        row for row in rows if str(row.get("stage", "")) == chain_contract.STAGE_PLATFORM_CONSEQUENCE
    ]
    lifecycle_rows = [
        row for row in rows if str(row.get("stage", "")) == chain_contract.STAGE_LIFECYCLE
    ]
    structural_rows = [
        row for row in rows if str(row.get("stage", "")) == chain_contract.STAGE_STRUCTURAL_BREAKUP
    ]
    miss_distances = [
        finite_float(row.get("miss_distance_m", float("nan")))
        for row in rows
        if math.isfinite(finite_float(row.get("miss_distance_m", float("nan"))))
    ]
    miss_distance_m = min(miss_distances) if miss_distances else float("nan")
    fuze_negative = any(
        reason in chain_contract.TERMINAL_NEGATIVE_REASONS for reason in reasons
    ) or any(not _truthy(row.get("fuze_triggered", 0)) for row in fuze_rows)
    effective_detonation = bool(
        stages
        & {
            chain_contract.STAGE_WARHEAD_MECHANISM,
            chain_contract.STAGE_SPATIAL_COVERAGE,
            chain_contract.STAGE_COMPONENT_LOAD,
            chain_contract.STAGE_COMPONENT_DAMAGE,
        }
    ) and not bool(fuze_negative)
    effective_component_damage = chain_contract.STAGE_COMPONENT_DAMAGE in stages
    structural_breakup = bool(structural_rows)
    airframe_breakup = any(_truthy(row.get("airframe_breakup", 0)) for row in structural_rows)
    platform_consequence = bool(platform_rows)
    functional_kill = any(
        _truthy(row.get(key, 0))
        for row in platform_rows
        for key in ("mission_kill", "mobility_kill", "sensor_kill", "destroyed")
    )
    terminal_lifecycle = any(
        _truthy(row.get("lifecycle_terminal", 0))
        or str(row.get("ground_lifecycle", "") or "") in {"crashed_wreck", "debris_fragment_residue"}
        or str(row.get("lifecycle_to", "") or "") == "ground_crashed_wreck"
        for row in lifecycle_rows
    )
    return {
        "episode": int(episode),
        "chain_id": int(chain_id),
        "row_count": int(len(rows)),
        "miss_distance_m": miss_distance_m,
        "miss_distance_bucket": _miss_distance_bucket(miss_distance_m),
        "mechanism_family": _first_nonempty(row.get("mechanism_family", "") for row in rows),
        "component_system": _first_nonempty(row.get("component_system", "") for row in rows),
        "component_failure_mode": _first_nonempty(
            row.get("component_failure_mode", "") for row in rows
        ),
        "break_mode": _first_nonempty(row.get("break_mode", "") for row in structural_rows),
        "terminal_lifecycle_class": _first_nonempty(
            row.get("ground_lifecycle", "") or row.get("lifecycle_to", "")
            for row in lifecycle_rows
        ),
        "released": bool(rows),
        "effective_detonation": bool(effective_detonation),
        "fuze_negative": bool(fuze_negative),
        "effective_component_damage": bool(effective_component_damage),
        "structural_breakup": bool(structural_breakup),
        "airframe_breakup": bool(airframe_breakup),
        "platform_consequence": bool(platform_consequence),
        "functional_kill": bool(functional_kill),
        "terminal_lifecycle": bool(terminal_lifecycle),
    }

def chain_records(rows: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[int, int], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        chain_id = _chain_id(row)
        if chain_id <= 0:
            continue
        grouped[(_episode(row), chain_id)].append(dict(row))
    return [_chain_record(chain_key, grouped[chain_key]) for chain_key in sorted(grouped)]

def _group_key(record: dict[str, Any], group_by: Sequence[str]) -> tuple[tuple[str, str], ...]:
    if not group_by or tuple(group_by) == DEFAULT_GROUP_BY:
        return (("all", "all"),)
    return tuple((field, str(record.get(field, "") or "unknown")) for field in group_by)

def _denominator_filter(name: str, record: dict[str, Any]) -> bool:
    if name == "chain_count":
        return True
    if name == "released_chain_count":
        return bool(record.get("released", False))
    if name == "detonated_chain_count":
        return bool(record.get("effective_detonation", False))
    if name == "component_damage_chain_count":
        return bool(record.get("effective_component_damage", False))
    if name == "structural_breakup_chain_count":
        return bool(record.get("structural_breakup", False))
    if name == "platform_consequence_chain_count":
        return bool(record.get("platform_consequence", False))
    raise ValueError(f"unknown denominator: {name}")

def _rate_record(
    *,
    outcome: str,
    denominator: str,
    success_count: int,
    sample_count: int,
    z_score: float,
) -> dict[str, Any]:
    rate = float(success_count / sample_count) if sample_count > 0 else float("nan")
    low, high = _wilson_interval(success_count, sample_count, z_score)
    return {
        "outcome": outcome,
        "denominator": denominator,
        "success_count": int(success_count),
        "sample_count": int(sample_count),
        "rate": rate,
        "ci_low": low,
        "ci_high": high,
    }

def summarize_trends(
    rows: Sequence[dict[str, Any]],
    *,
    group_by: Sequence[str] = DEFAULT_GROUP_BY,
    confidence_level: float = 0.95,
    sample_source: str = "explicit_rows",
    report_surface: str = "standalone_diagnostics_artifact",
) -> dict[str, Any]:
    group_by = normalize_group_by(group_by)
    records = chain_records(rows)
    grouped: dict[tuple[tuple[str, str], ...], list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        grouped[_group_key(record, tuple(group_by))].append(record)

    confidence_level = validate_confidence_level(confidence_level)
    z_score = _confidence_z(confidence_level)
    groups: list[dict[str, Any]] = []
    for key in sorted(grouped):
        group_records = grouped[key]
        denominator_counts = {
            name: sum(1 for record in group_records if _denominator_filter(name, record))
            for name in DENOMINATOR_FIELDS
        }
        outcome_counts = {
            name: sum(1 for record in group_records if bool(record.get(name, False)))
            for name in OUTCOME_FIELDS
        }
        rates: list[dict[str, Any]] = []
        for denominator in DENOMINATOR_FIELDS:
            denominator_records = [
                record for record in group_records if _denominator_filter(denominator, record)
            ]
            sample_count = len(denominator_records)
            for outcome in OUTCOME_FIELDS:
                success_count = sum(
                    1 for record in denominator_records if bool(record.get(outcome, False))
                )
                rates.append(
                    _rate_record(
                        outcome=outcome,
                        denominator=denominator,
                        success_count=success_count,
                        sample_count=sample_count,
                        z_score=z_score,
                    )
                )
        groups.append(
            {
                "group": dict(key),
                "chain_ids": [int(record["chain_id"]) for record in group_records],
                "chain_identities": [
                    {
                        "episode": int(record["episode"]),
                        "chain_id": int(record["chain_id"]),
                    }
                    for record in group_records
                ],
                "denominator_counts": denominator_counts,
                "outcome_counts": outcome_counts,
                "rates": rates,
            }
        )

    return {
        "schema_version": SCHEMA_VERSION,
        "status": "simulation_trend_summary",
        "confidence_level": confidence_level,
        "confidence_z": float(z_score),
        "interval_method": INTERVAL_METHOD,
        "sample_source": str(sample_source),
        "report_surface": str(report_surface),
        "source_row_count": int(len(rows)),
        "group_by": list(group_by),
        "chain_count": int(len(records)),
        "groups": groups,
        "authority_boundary": {
            "synthetic_simulation_trend": True,
            "real_world_pk": False,
            "weapon_specific_lethality": False,
            "target_specific_lethality": False,
            "calibration_authority": False,
            "reward_authority": False,
            "entity_deletion_authority": False,
        },
    }

def _load_rows(path: str) -> list[dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        payload = json.load(f)
    if isinstance(payload, dict):
        payload = payload.get("lethality_chain_rows", payload.get("rows", []))
    if not isinstance(payload, list):
        raise ValueError("input JSON must be a row list or object with lethality_chain_rows")
    return [dict(row) for row in payload if isinstance(row, dict)]

def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Summarize MLF-9 simulation trend rows.")
    parser.add_argument("--rows_json", required=True)
    parser.add_argument("--json_out", default="")
    parser.add_argument(
        "--group_by",
        default="all",
        help="Comma-separated group fields, e.g. miss_distance_bucket,break_mode.",
    )
    parser.add_argument("--confidence_level", type=parse_confidence_level, default=0.95)
    parser.add_argument("--sample_source", default="explicit_rows")
    parser.add_argument("--report_surface", default="standalone_diagnostics_artifact")
    return parser

def main() -> int:
    args = build_arg_parser().parse_args()
    payload = summarize_trends(
        _load_rows(args.rows_json),
        group_by=normalize_group_by(str(args.group_by)),
        confidence_level=float(args.confidence_level),
        sample_source=str(args.sample_source),
        report_surface=str(args.report_surface),
    )
    text = json.dumps(payload, indent=2, ensure_ascii=True)
    if args.json_out:
        out_path = os.path.abspath(args.json_out)
        os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(text)
            f.write("\n")
    else:
        print(text)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
