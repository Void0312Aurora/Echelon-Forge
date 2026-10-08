"""Group-composition scenario schema (Carrier Strike Group Engagement, S0-D).

A scenario may declare a top-level ``groups`` list. Each group is expanded at
compile time into plain ``entities`` (ships and submarines) plus an embarked
aircraft inventory in ``meta.csg``. The runtime spawn paths never see
``groups``: they consume the expanded entities unchanged, so the single-world
and batch loaders stay identical.

Why aircraft are inventory, not entities, at CSG-S0: there is no deck contact
surface (ground contact reads terrain elevation only), so an aircraft cannot
rest on a flight deck. (The gear-contact step-size limit that also blocked this
was closed by the semi-implicit ground contact, 2026-09-30.) The one stowed
helicopter each ship's ``embarked_air_ops`` record spawns (pinned by
EmbarkedAirOpsSystem) is counted against that host's inventory row. CSG-S2
consumes the inventory as the deck cycle's initial condition.

Placement (CSG-S0-B, through the shared geodetic frame):

* A guide declares either ``geo`` (``latitude_deg``, ``longitude_deg``) or a
  local ``pos``. ``geo`` is projected into the scenario's local frame through
  ``environment.geodetic_anchor`` with the runtime's own azimuthal-equidistant
  projection (``ef_py.geodesy_geodetic_to_local``), so the compiler and the
  runtime share one frame. A geodetic guide requires a declared anchor.
* ``axis_deg`` is the threat axis as a TRUE bearing at the guide (NAV
  convention: 0 = north, clockwise). A station is range and bearing relative to
  that axis; for a geodetic guide the station point is found along the great
  circle from the guide (direct geodesic problem on the model sphere) and then
  projected, so screen geometry is exact on the sphere at any distance from the
  anchor.
* ``meta.csg.geometry`` records the anchor and the great-circle separation and
  bearing between geodetic guides.
* A local ``pos`` guide keeps the flat ``station_local_offset_m`` layout.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import ef_py

from .common import resolve_environment_geodetic_anchor

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
_GROUP_KEYS = {"group_id", "side", "oob_ref", "guide", "default_heading_deg", "branches", "members", "transit"}
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


# Mean earth radius of the runtime's model sphere (geodesy::kMeanEarthRadiusM).
# Only the direct geodesic below needs it; projection itself goes through ef_py.
_MEAN_EARTH_RADIUS_M = 6371009.0


def geodesic_destination_deg(
    latitude_deg: float, longitude_deg: float, bearing_deg: float, distance_m: float
) -> tuple[float, float]:
    """Point reached along a great circle from a start point (direct problem, sphere)."""
    if distance_m == 0.0:
        return latitude_deg, longitude_deg
    phi1 = math.radians(latitude_deg)
    lam1 = math.radians(longitude_deg)
    theta = math.radians(bearing_deg)
    delta = distance_m / _MEAN_EARTH_RADIUS_M
    sin_phi2 = math.sin(phi1) * math.cos(delta) + math.cos(phi1) * math.sin(delta) * math.cos(theta)
    phi2 = math.asin(max(-1.0, min(1.0, sin_phi2)))
    lam2 = lam1 + math.atan2(
        math.sin(theta) * math.sin(delta) * math.cos(phi1),
        math.cos(delta) - math.sin(phi1) * sin_phi2,
    )
    return math.degrees(phi2), (math.degrees(lam2) + 180.0) % 360.0 - 180.0


class _GuideFrame:
    """Places one group's stations in the local frame, geodetically or flat."""

    def __init__(self, guide: dict[str, Any], anchor: tuple[float, float, float]):
        self.axis_deg = float(guide.get("axis_deg", 0.0))
        self.anchor = anchor
        geo = guide.get("geo")
        if geo is not None:
            self.geo: tuple[float, float] | None = (float(geo["latitude_deg"]), float(geo["longitude_deg"]))
            east, north, _up = ef_py.geodesy_geodetic_to_local(*anchor, self.geo[0], self.geo[1], anchor[2])
            self.origin: tuple[float, float, float] = (float(east), float(north), 0.0)
        else:
            self.geo = None
            gx, gy, gz = (float(v) for v in guide["pos"])
            self.origin = (gx, gy, gz)

    def place(self, true_bearing_deg: float, range_m: float) -> tuple[float, float]:
        """Local (east, north) of the point ``range_m`` from the guide on a true bearing."""
        if self.geo is None:
            b = math.radians(true_bearing_deg)
            return self.origin[0] + range_m * math.sin(b), self.origin[1] + range_m * math.cos(b)
        lat, lon = geodesic_destination_deg(self.geo[0], self.geo[1], true_bearing_deg, range_m)
        east, north, _up = ef_py.geodesy_geodetic_to_local(*self.anchor, lat, lon, self.anchor[2])
        return float(east), float(north)


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
        _unknown_keys(guide, {"pos", "geo", "axis_deg"}, f"{ctx}.guide")
        if ("pos" in guide) == ("geo" in guide):
            _fail(f"{ctx}.guide", "must declare exactly one of 'pos' (local) or 'geo' (geodetic)")
        if "pos" in guide:
            pos = guide.get("pos")
            if not isinstance(pos, list) or len(pos) != 3:
                _fail(f"{ctx}.guide.pos", "must be [x, y, z]")
            for k, v in enumerate(pos):
                _number(v, f"{ctx}.guide.pos[{k}]")
        else:
            geo = guide.get("geo")
            if not isinstance(geo, dict):
                _fail(f"{ctx}.guide.geo", "must be an object")
            _unknown_keys(geo, {"latitude_deg", "longitude_deg"}, f"{ctx}.guide.geo")
            lat = _number(geo.get("latitude_deg"), f"{ctx}.guide.geo.latitude_deg")
            _number(geo.get("longitude_deg"), f"{ctx}.guide.geo.longitude_deg")
            if not -90.0 < lat < 90.0:
                _fail(f"{ctx}.guide.geo.latitude_deg", "must lie inside (-90, 90)")
            env = scenario.get("environment")
            if not isinstance(env, dict) or "geodetic_anchor" not in env:
                # A geodetic guide needs a declared frame, not the inherited default anchor.
                _fail(f"{ctx}.guide.geo", "requires environment.geodetic_anchor")
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
        if "transit" in group:
            transit = group["transit"]
            tctx = f"{ctx}.transit"
            if not isinstance(transit, dict):
                _fail(tctx, "must be an object")
            _unknown_keys(transit, {"guide_member_id", "speed_mps", "arrival_radius_m", "waypoint_offsets_m"}, tctx)
            leader = next((m for m in members if m["member_id"] == transit.get("guide_member_id")), None)
            if (leader is None or leader.get("embarked_on") is not None or
                    leader.get("role") != "carrier" or _active_count(leader, branches) != 1 or
                    float(leader["station"].get("range_m", 0.0)) != 0.0):
                _fail(f"{tctx}.guide_member_id", "must name one active carrier at the guide origin")
            if _number(transit.get("speed_mps"), f"{tctx}.speed_mps", minimum=0.0) <= 0.0:
                _fail(f"{tctx}.speed_mps", "must be positive")
            if _number(transit.get("arrival_radius_m"), f"{tctx}.arrival_radius_m", minimum=0.0) <= 0.0:
                _fail(f"{tctx}.arrival_radius_m", "must be positive")
            offsets = transit.get("waypoint_offsets_m")
            if not isinstance(offsets, list) or not offsets:
                _fail(f"{tctx}.waypoint_offsets_m", "must be a non-empty list of local east/north offsets")
            for wi, offset in enumerate(offsets):
                if not isinstance(offset, list) or len(offset) != 2:
                    _fail(f"{tctx}.waypoint_offsets_m[{wi}]", "must be [east_m, north_m]")
                for k, value in enumerate(offset):
                    _number(value, f"{tctx}.waypoint_offsets_m[{wi}][{k}]")


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
    anchor, anchor_source = resolve_environment_geodetic_anchor(scenario.get("environment"))
    entities: list[dict[str, Any]] = []
    groups_meta: list[dict[str, Any]] = []
    frames: dict[str, _GuideFrame] = {}
    for group in scenario.get("groups") or []:
        gid = group["group_id"]
        side = group["side"]
        branches = dict(group.get("branches", {}))
        frame = _GuideFrame(group["guide"], anchor)
        frames[gid] = frame
        gx, gy, gz = frame.origin
        axis = frame.axis_deg
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
                dx = east + lateral * math.cos(math.radians(axis))
                dy = north - lateral * math.sin(math.radians(axis))
                px, py = frame.place(math.degrees(math.atan2(dx, dy)), math.hypot(dx, dy))
                entities.append(
                    {
                        "name": name,
                        "type": member["type"],
                        "side": side,
                        "pos": [px, py, gz - depth],
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
        guide_meta: dict[str, Any] = {"pos": [gx, gy, gz], "axis_deg": axis}
        if frame.geo is not None:
            guide_meta["geo"] = {"latitude_deg": frame.geo[0], "longitude_deg": frame.geo[1]}
        groups_meta.append(
            {
                "group_id": gid,
                "side": side,
                "oob_ref": group["oob_ref"],
                "guide": guide_meta,
                "branches": branches,
                "ships": rows,
                "embarked_inventory": inventory,
            }
        )
        if "transit" in group:
            groups_meta[-1]["transit"] = {
                **group["transit"],
                "waypoints_m": [[gx + float(dx), gy + float(dy)]
                                for dx, dy in group["transit"]["waypoint_offsets_m"]],
            }
    geo_ids = sorted(gid for gid, f in frames.items() if f.geo is not None)
    separations = []
    for i, a in enumerate(geo_ids):
        for b in geo_ids[i + 1:]:
            la, oa = frames[a].geo  # type: ignore[misc]
            lb, ob = frames[b].geo  # type: ignore[misc]
            separations.append(
                {
                    "from": a,
                    "to": b,
                    "great_circle_m": float(ef_py.geodesy_great_circle_distance_m(la, oa, lb, ob)),
                    "initial_bearing_deg": float(ef_py.geodesy_initial_bearing_deg(la, oa, lb, ob)),
                }
            )
    geometry = {
        "anchor": {"latitude_deg": anchor[0], "longitude_deg": anchor[1], "height_m": anchor[2]},
        "anchor_source": anchor_source,
        "placement": "geodetic" if geo_ids else "local",
        "guide_separations": separations,
    }
    return entities, {"schema": "csg.group_composition.v2", "groups": groups_meta, "geometry": geometry}


__all__ = [
    "COUNT_BASES",
    "GROUP_SIDES",
    "MEMBER_ROLES",
    "expand_group_composition",
    "geodesic_destination_deg",
    "station_local_offset_m",
    "validate_group_composition",
]
