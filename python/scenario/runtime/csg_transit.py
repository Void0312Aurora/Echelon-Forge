"""Bounded surface-group transit through maintained scenario command writes.

The route is scenario-owned. Each guide follows local-frame waypoints; surface
escorts keep their initial local station offset through the native ship law.
Station bearings stay fixed through a guide turn. Submarines remain at S0 until
U1, and air-wing inventory remains stowed until S2. No combat authority is issued.
"""

from __future__ import annotations

import math
from typing import Any

import ef_py


class CsgTransitController:
    def __init__(self, loader: Any) -> None:
        self.sim = loader.sim
        self.groups: list[dict[str, Any]] = []
        groups = loader._compiled_runtime_metadata.meta_config.get("csg", {}).get("groups", [])
        for group in groups:
            transit = group.get("transit")
            if transit is None:
                continue
            guide_name = f"{group['group_id']}__{transit['guide_member_id']}"
            guide_id = int(loader.entities[guide_name])
            gx, gy, _ = self.sim.get_unit_position(guide_id)
            stations = []
            for row in group["ships"]:
                if row.get("role") == "ssn":
                    continue
                for name in row["entity_names"]:
                    entity_id = int(loader.entities[name])
                    if entity_id == guide_id:
                        continue
                    x, y, _ = self.sim.get_unit_position(entity_id)
                    dx, dy = float(x) - float(gx), float(y) - float(gy)
                    stations.append((entity_id, math.degrees(math.atan2(dx, dy)) % 360.0,
                                     math.hypot(dx, dy)))
            self.groups.append({"group_id": group["group_id"], "guide_id": guide_id,
                                "route": transit, "waypoint_index": 0, "stations": stations})

    def step(self) -> None:
        """Publish one set of orders before the next native fixed step."""
        for group in self.groups:
            guide_id = group["guide_id"]
            if not self.sim.is_unit_active(guide_id):
                raise RuntimeError(f"CSG transit guide lost: {group['group_id']}")
            observation = self.sim.get_agent_observation(guide_id)
            route = group["route"]
            waypoints = route["waypoints_m"]
            index = group["waypoint_index"]
            while index < len(waypoints):
                dx = float(waypoints[index][0]) - float(observation.x)
                dy = float(waypoints[index][1]) - float(observation.y)
                if math.hypot(dx, dy) > float(route["arrival_radius_m"]):
                    break
                index += 1
            group["waypoint_index"] = index
            command = ef_py.MissionCommand()
            command.active = True
            command.command_code = 3
            command.cmd_heading_deg = float(observation.heading)
            command.cmd_speed_mps = 0.0
            if index < len(waypoints):
                command.cmd_heading_deg = math.degrees(math.atan2(dx, dy)) % 360.0
                command.cmd_speed_mps = float(route["speed_mps"])
            self.sim.set_mission_command(guide_id, command)
            for entity_id, bearing, radius in group["stations"]:
                if not self.sim.is_unit_active(entity_id):
                    raise RuntimeError(f"CSG transit member lost: {entity_id}")
                station = ef_py.MissionCommand()
                station.active = True
                station.command_code = 3
                station.cmd_heading_deg = command.cmd_heading_deg
                station.cmd_speed_mps = command.cmd_speed_mps
                station.reference_entity_id = guide_id
                station.station_bearing_deg = bearing
                station.station_radius_m = radius
                self.sim.set_mission_command(entity_id, station)

    def report(self) -> list[dict[str, Any]]:
        return [{"group_id": g["group_id"], "waypoint_index": g["waypoint_index"],
                 "waypoint_count": len(g["route"]["waypoints_m"]),
                 "complete": g["waypoint_index"] == len(g["route"]["waypoints_m"])}
                for g in self.groups]
