from __future__ import annotations

import argparse
import csv
import json
import os
from collections import defaultdict
from collections.abc import Iterable
from typing import Any


SCHEMA_VERSION = "mlf6.structural_breakup_export.v1"

ROW_FIELDS = (
    "schema_version",
    "chain_id",
    "event_id",
    "parent_event_id",
    "stage",
    "status",
    "reason",
    "source_time_s",
    "source_frame",
    "producer_node_id",
    "fidelity_mode",
    "evidence_level",
    "observation_mode",
    "consumer_visibility",
    "confidence",
    "munition_world_index",
    "munition_id",
    "shooter_world_index",
    "shooter_id",
    "target_world_index",
    "target_id",
    "breakup_state",
    "break_mode",
    "detached_part_ref",
    "detached_part_count",
    "airframe_breakup",
    "cause_event_id",
)


def _as_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _as_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _as_str(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


def _entity_id(ref: Any) -> int:
    return _as_int(getattr(ref, "entity_id", 0))


def _world_index(ref: Any) -> int:
    return _as_int(getattr(ref, "world_index", 0))


def _event_iter(source: Any) -> list[Any]:
    if source is None:
        return []
    if hasattr(source, "structural_breakup_events"):
        return list(getattr(source, "structural_breakup_events") or [])
    if hasattr(source, "breakup_state") and hasattr(source, "header"):
        return [source]
    if isinstance(source, (str, bytes, dict)):
        raise TypeError("source must be an event, event sequence, or object with structural_breakup_events")
    if isinstance(source, Iterable):
        return list(source)
    raise TypeError("source must be an event, event sequence, or object with structural_breakup_events")


def structural_breakup_event_row(event: Any) -> dict[str, Any]:
    header = getattr(event, "header", None)
    munition = getattr(header, "munition", None)
    shooter = getattr(header, "shooter", None)
    target = getattr(header, "target", None)
    return {
        "schema_version": SCHEMA_VERSION,
        "chain_id": _as_int(getattr(header, "chain_id", 0)),
        "event_id": _as_int(getattr(header, "event_id", 0)),
        "parent_event_id": _as_int(getattr(header, "parent_event_id", 0)),
        "stage": _as_str(getattr(header, "stage", "")),
        "status": _as_str(getattr(header, "status", "")),
        "reason": _as_str(getattr(header, "reason", "")),
        "source_time_s": _as_float(getattr(header, "source_time_s", 0.0)),
        "source_frame": _as_int(getattr(header, "source_frame", 0)),
        "producer_node_id": _as_str(getattr(header, "producer_node_id", "")),
        "fidelity_mode": _as_str(getattr(header, "fidelity_mode", "")),
        "evidence_level": _as_str(getattr(header, "evidence_level", "")),
        "observation_mode": _as_str(getattr(header, "observation_mode", "")),
        "consumer_visibility": _as_str(getattr(header, "consumer_visibility", "")),
        "confidence": _as_float(getattr(header, "confidence", 0.0)),
        "munition_world_index": _world_index(munition),
        "munition_id": _entity_id(munition),
        "shooter_world_index": _world_index(shooter),
        "shooter_id": _entity_id(shooter),
        "target_world_index": _world_index(target),
        "target_id": _entity_id(target),
        "breakup_state": _as_str(getattr(event, "breakup_state", "")),
        "break_mode": _as_str(getattr(event, "break_mode", "")),
        "detached_part_ref": _as_str(getattr(event, "detached_part_ref", "")),
        "detached_part_count": _as_int(getattr(event, "detached_part_count", 0)),
        "airframe_breakup": bool(getattr(event, "airframe_breakup", False)),
        "cause_event_id": _as_int(getattr(event, "cause_event_id", 0)),
    }


def structural_breakup_rows(source: Any, *, chain_id: int | None = None) -> list[dict[str, Any]]:
    rows = [structural_breakup_event_row(event) for event in _event_iter(source)]
    if chain_id is not None:
        rows = [row for row in rows if int(row["chain_id"]) == int(chain_id)]
    return sorted(rows, key=lambda row: (int(row["chain_id"]), int(row["event_id"])))


def summarize_by_chain(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[int(row["chain_id"])].append(row)

    summaries: list[dict[str, Any]] = []
    for chain_id in sorted(grouped):
        chain_rows = sorted(grouped[chain_id], key=lambda row: int(row["event_id"]))
        summaries.append(
            {
                "chain_id": chain_id,
                "event_count": len(chain_rows),
                "first_event_id": int(chain_rows[0]["event_id"]) if chain_rows else 0,
                "last_event_id": int(chain_rows[-1]["event_id"]) if chain_rows else 0,
                "airframe_breakup": any(bool(row["airframe_breakup"]) for row in chain_rows),
                "breakup_states": sorted({_as_str(row["breakup_state"]) for row in chain_rows}),
                "break_modes": sorted({_as_str(row["break_mode"]) for row in chain_rows}),
                "detached_part_refs": sorted({_as_str(row["detached_part_ref"]) for row in chain_rows}),
                "cause_event_ids": sorted(
                    {
                        int(row["cause_event_id"])
                        for row in chain_rows
                        if int(row["cause_event_id"]) != 0
                    }
                ),
            }
        )
    return summaries


def export_structural_breakup_events(
    source: Any,
    *,
    chain_id: int | None = None,
) -> dict[str, Any]:
    rows = structural_breakup_rows(source, chain_id=chain_id)
    chain_ids = sorted({int(row["chain_id"]) for row in rows})
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "structural_breakup_events_exported",
        "event_count": len(rows),
        "chain_count": len(chain_ids),
        "chain_ids": chain_ids,
        "rows": rows,
        "summary_by_chain": summarize_by_chain(rows),
        "authority_boundary": {
            "consumes_existing_bindings_only": True,
            "new_binding_surface": False,
            "aerodynamics_modified": False,
            "structural_integrity_modified": False,
            "loss_state_modified": False,
            "wreck_debris_lifecycle": False,
            "real_weapon_structural_kill_authority": False,
            "pk_authority": False,
        },
    }


def write_csv(path: str, rows: list[dict[str, Any]]) -> None:
    out_path = os.path.abspath(path)
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(ROW_FIELDS))
        writer.writeheader()
        writer.writerows({field: row.get(field, "") for field in ROW_FIELDS} for row in rows)


def write_json(path: str, payload: dict[str, Any]) -> None:
    out_path = os.path.abspath(path)
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=True)
        f.write("\n")


def run_export(
    source: Any,
    *,
    chain_id: int | None = None,
    csv_out: str = "",
    json_out: str = "",
) -> dict[str, Any]:
    payload = export_structural_breakup_events(source, chain_id=chain_id)
    if csv_out:
        write_csv(csv_out, list(payload["rows"]))
        payload["csv_out"] = os.path.abspath(csv_out)
    if json_out:
        write_json(json_out, payload)
        payload["json_out"] = os.path.abspath(json_out)
    return payload


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Normalize StructuralBreakupEvent binding objects into diagnostic rows. "
            "The CLI emits an empty payload; production callers should pass an "
            "EngagementEventPacket or RecentEngagementEvents object to run_export()."
        )
    )
    parser.add_argument("--chain_id", type=int, default=None)
    parser.add_argument("--csv_out", default="")
    parser.add_argument("--json_out", default="")
    return parser


def main() -> int:
    args = build_arg_parser().parse_args()
    payload = run_export([], chain_id=args.chain_id, csv_out=args.csv_out, json_out=args.json_out)
    print(json.dumps(payload, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
