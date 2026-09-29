"""Group-composition scenario schema (Carrier Strike Group Engagement, S0-D).

A scenario may declare a top-level ``groups`` list. Each group is expanded at
compile time into plain ``entities`` (ships and submarines) plus an embarked
aircraft inventory in ``meta.csg``. The runtime spawn paths never see
``groups``: they consume the expanded entities unchanged, so the single-world
and batch loaders stay identical.

Why aircraft are inventory, not entities, at CSG-S0: the flight models have no
deck-parked state, so an aircraft spawned at zero speed on a deck climbs away
within a few steps. The one stowed helicopter each ship's
``embarked_air_ops`` record spawns (pinned by EmbarkedAirOpsSystem) is counted
against that host's inventory row. CSG-S2 consumes the inventory as the deck
cycle's initial condition.

Placement: ``station`` is range and relative bearing from the group guide,
measured from the guide's threat axis (NAV convention: 0 = north, clockwise),
converted to local east/north metres. CSG-S0-B replaces only
``station_local_offset_m`` to place the guide through the geodetic frame.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

GROUP_SIDES = ("Blue", "Red")
MEMBER_ROLES = (
    "carrier",
    "escort_aaw",
    "escort_asw",
    "escort_multi",
    "ssn",
    "logistics",
    "air_wing",
)
COUNT_BASES = ("sourced", "engineering_estimate", "doctrinal_fill")
_GROUP_KEYS = {"group_id", "side", "oob_ref", "guide", "default_heading_deg", "branches", "members"}
_MEMBER_KEYS = {
    "member_id",
    "oob_row",
    "type",
    "count",
    "branch",
    "role",
    "station",
    "embarked_on",
    "hull",
    "provenance",
}
_STATION_KEYS = {"range_m", "bearing_rel_deg", "spacing_m", "depth_m"}


def _fail(context: str, message: str) -> None:
    raise ValueError(f"{context}: {message}")


def _number(value: Any, context: str, *, minimum: float | None = None) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        _fail(context, "must be a finite number")
    if minimum is not None and value < minimum:
        _fail(context, f"must be >= {minimum}")
    return float(value)


def _unknown_keys(obj: dict[str, Any], allowed: set[str], context: str) -> None:
    extra = sorted(set(obj) - allowed)
    if extra:
        _fail(context, f"unknown keys {extra}")


def station_local_offset_m(station: dict[str, Any], axis_deg: float) -> tuple[float, float]:
    """East/north offset of a station from the guide (NAV bearings, clockwise from north)."""
    bearing = math.radians(axis_deg + float(station.get("bearing_rel_deg", 0.0)))
    range_m = float(station.get("range_m", 0.0))
    return range_m * math.sin(bearing), range_m * math.cos(bearing)


def _validate_member(member: Any, context: str, branches: dict[str, bool]) -> None:
    if not isinstance(member, dict):
        _fail(context, "must be an object")
    _unknown_keys(member, _MEMBER_KEYS, context)
    for key in ("member_id", "oob_row", "type"):
        if not isinstance(member.get(key), str) or not member[key].strip():
            _fail(f"{context}.{key}", "is required and must be a non-empty string")
    count = member.get("count", 1)
    if isinstance(count, bool) or not isinstance(count, int) or count < 0:
        _fail(f"{context}.count", "must be an integer >= 0")
    if "role" in member and member["role"] not in MEMBER_ROLES:
        _fail(f"{context}.role", f"must be one of {list(MEMBER_ROLES)}")
    if "branch" in member and member["branch"] not in branches:
        _fail(f"{context}.branch", f"'{member['branch']}' is not declared in the group's branches")
    embarked = member.get("embarked_on")
    station = member.get("station")
    if embarked is not None:
        if station is not None:
            _fail(context, "an embarked row must not have a station")
        if not isinstance(embarked, str) or not embarked.strip():
            _fail(f"{context}.embarked_on", "must be a member_id")
    else:
        if not isinstance(station, dict):
            _fail(f"{context}.station", "is required for a ship or submarine row")
        _unknown_keys(station, _STATION_KEYS, f"{context}.station")
        _number(station.get("range_m", 0.0), f"{context}.station.range_m", minimum=0.0)
        _number(station.get("bearing_rel_deg", 0.0), f"{context}.station.bearing_rel_deg")
        if "spacing_m" in station:
            _number(station["spacing_m"], f"{context}.station.spacing_m", minimum=0.0)
        if "depth_m" in station:
            _number(station["depth_m"], f"{context}.station.depth_m", minimum=0.0)
    prov = member.get("provenance")
    if not isinstance(prov, dict):
        _fail(f"{context}.provenance", "is required")
    if prov.get("count_basis") not in COUNT_BASES:
        _fail(f"{context}.provenance.count_basis", f"must be one of {list(COUNT_BASES)}")


def validate_group_composition(scenario: dict[str, Any], *, project_root: str | Path) -> None:
    """Fail closed on any malformed ``groups`` block."""
    groups = scenario.get("groups")
    if groups is None:
        return
    if not isinstance(groups, list) or not groups:
        _fail("groups", "must be a non-empty list")
    group_ids: set[str] = set()
    for gi, group in enumerate(groups):
        ctx = f"groups[{gi}]"
        if not isinstance(group, dict):
            _fail(ctx, "must be an object")
        _unknown_keys(group, _GROUP_KEYS, ctx)
        gid = group.get("group_id")
        if not isinstance(gid, str) or not gid.strip() or "__" in gid:
            _fail(f"{ctx}.group_id", "must be a non-empty string without '__'")
        if gid in group_ids:
            _fail(f"{ctx}.group_id", f"duplicate '{gid}'")
        group_ids.add(gid)
        ctx = f"groups[{gid}]"
        if group.get("side") not in GROUP_SIDES:
            # resolve_scenario_side would silently map anything else to Neutral.
            _fail(f"{ctx}.side", f"must be one of {list(GROUP_SIDES)}")
        oob_ref = group.get("oob_ref")
        if not isinstance(oob_ref, str) or not (Path(project_root) / oob_ref.split("#")[0]).is_file():
            _fail(f"{ctx}.oob_ref", f"must name an existing repository file, got {oob_ref!r}")
        guide = group.get("guide")
        if not isinstance(guide, dict):
            _fail(f"{ctx}.guide", "is required")
        _unknown_keys(guide, {"pos", "axis_deg"}, f"{ctx}.guide")
        pos = guide.get("pos")
        if not isinstance(pos, list) or len(pos) != 3:
            _fail(f"{ctx}.guide.pos", "must be [x, y, z]")
        for k, v in enumerate(pos):
            _number(v, f"{ctx}.guide.pos[{k}]")
        _number(guide.get("axis_deg", 0.0), f"{ctx}.guide.axis_deg")
        if "default_heading_deg" in group:
            _number(group["default_heading_deg"], f"{ctx}.default_heading_deg")
        branches = group.get("branches", {})
        if not isinstance(branches, dict) or not all(isinstance(v, bool) for v in branches.values()):
            _fail(f"{ctx}.branches", "must map branch ids to booleans")
        members = group.get("members")
        if not isinstance(members, list) or not members:
            _fail(f"{ctx}.members", "must be a non-empty list")
        member_ids: set[str] = set()
        for mi, member in enumerate(members):
            mctx = f"{ctx}.members[{mi}]"
            _validate_member(member, mctx, branches)
            if member["member_id"] in member_ids:
                _fail(f"{mctx}.member_id", f"duplicate '{member['member_id']}'")
            member_ids.add(member["member_id"])
        hosts = {m["member_id"] for m in members if m.get("embarked_on") is None}
        for member in members:
            host = member.get("embarked_on")
            if host is not None and host not in hosts:
                _fail(f"{ctx}.members[{member['member_id']}].embarked_on", f"'{host}' is not a ship row")


def _active_count(member: dict[str, Any], branches: dict[str, bool]) -> int:
    count = int(member.get("count", 1))
    branch = member.get("branch")
    if branch is not None and not branches.get(branch, False):
        return 0
    return count


def expand_group_composition(
    scenario: dict[str, Any], *, project_root: str | Path
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Return ``(entities, csg_meta)`` for the scenario's ``groups`` block."""
    validate_group_composition(scenario, project_root=project_root)
    entities: list[dict[str, Any]] = []
    groups_meta: list[dict[str, Any]] = []
    for group in scenario.get("groups") or []:
        gid = group["group_id"]
        side = group["side"]
        branches = dict(group.get("branches", {}))
        gx, gy, gz = (float(v) for v in group["guide"]["pos"])
        axis = float(group["guide"].get("axis_deg", 0.0))
        heading = float(group.get("default_heading_deg", axis))
        rows: list[dict[str, Any]] = []
        inventory: list[dict[str, Any]] = []
        for member in group["members"]:
            count = _active_count(member, branches)
            row = {
                "member_id": member["member_id"],
                "oob_row": member["oob_row"],
                "type": member["type"],
                "role": member.get("role"),
                "count": count,
                "declared_count": int(member.get("count", 1)),
                "branch": member.get("branch"),
                "hull": member.get("hull"),
                "provenance": dict(member["provenance"]),
            }
            if member.get("embarked_on") is not None:
                row["embarked_on"] = member["embarked_on"]
                inventory.append(row)
                continue
            station = member["station"]
            spacing = float(station.get("spacing_m", 0.0))
            east, north = station_local_offset_m(station, axis)
            depth = float(station.get("depth_m", 0.0))
            names = []
            for n in range(count):
                name = f"{gid}__{member['member_id']}" + (f"_{n + 1:02d}" if count > 1 else "")
                # Multiple hulls on one station line up across the axis.
                lateral = (n - (count - 1) / 2.0) * spacing
                lx = east + lateral * math.cos(math.radians(axis))
                ly = north - lateral * math.sin(math.radians(axis))
                entities.append(
                    {
                        "name": name,
                        "type": member["type"],
                        "side": side,
                        "pos": [gx + lx, gy + ly, gz - depth],
                        "vel": [0.0, 0.0, 0.0],
                        "heading": heading,
                        "csg_member": {
                            "group_id": gid,
                            "member_id": member["member_id"],
                            "oob_row": member["oob_row"],
                            "role": member.get("role"),
                            "hull": member.get("hull"),
                        },
                    }
                )
                names.append(name)
            row["entity_names"] = names
            rows.append(row)
        groups_meta.append(
            {
                "group_id": gid,
                "side": side,
                "oob_ref": group["oob_ref"],
                "guide": {"pos": [gx, gy, gz], "axis_deg": axis},
                "branches": branches,
                "ships": rows,
                "embarked_inventory": inventory,
            }
        )
    return entities, {"schema": "csg.group_composition.v1", "groups": groups_meta}


__all__ = [
    "COUNT_BASES",
    "GROUP_SIDES",
    "MEMBER_ROLES",
    "expand_group_composition",
    "station_local_offset_m",
    "validate_group_composition",
]
