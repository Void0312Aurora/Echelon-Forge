import math


def rotate_xy_clockwise(x, y, origin_x, origin_y, yaw_deg):
    """Rotate (x,y) around (origin_x, origin_y) by yaw_deg clockwise (NAV convention)."""
    rad = -math.radians(float(yaw_deg))
    c = math.cos(rad)
    s = math.sin(rad)
    dx = float(x) - float(origin_x)
    dy = float(y) - float(origin_y)
    rx = float(origin_x) + c * dx - s * dy
    ry = float(origin_y) + s * dx + c * dy
    return rx, ry


def apply_world_yaw(loader, yaw_deg, origin_x=0.0, origin_y=0.0):
    env = loader.scenario_data.get("environment", {})
    zones = env.get("zones", [])
    if isinstance(zones, list):
        for zone in zones:
            if not isinstance(zone, dict):
                continue
            if "x" in zone and "y" in zone:
                zx, zy = rotate_xy_clockwise(zone.get("x", 0.0), zone.get("y", 0.0), origin_x, origin_y, yaw_deg)
                zone["x"] = zx
                zone["y"] = zy
            if "heading" in zone:
                try:
                    zone["heading"] = (float(zone.get("heading", 0.0)) + float(yaw_deg)) % 360.0
                except Exception:
                    pass

    entities = loader.scenario_data.get("entities", [])
    if isinstance(entities, list):
        for ent in entities:
            if not isinstance(ent, dict):
                continue
            pos = ent.get("pos", None)
            vel = ent.get("vel", None)
            if isinstance(pos, list) and len(pos) >= 2:
                px, py = rotate_xy_clockwise(pos[0], pos[1], origin_x, origin_y, yaw_deg)
                pos[0] = px
                pos[1] = py
            if isinstance(vel, list) and len(vel) >= 2:
                vx, vy = rotate_xy_clockwise(vel[0], vel[1], 0.0, 0.0, yaw_deg)
                vel[0] = vx
                vel[1] = vy
            if "heading" in ent:
                try:
                    ent["heading"] = (float(ent.get("heading", 0.0)) + float(yaw_deg)) % 360.0
                except Exception:
                    pass

    mission_cmd = loader.scenario_data.get("mission_command", None)
    if isinstance(mission_cmd, dict):
        waypoints = mission_cmd.get("waypoints", None)
        if isinstance(waypoints, list):
            for wp in waypoints:
                if isinstance(wp, dict):
                    if "pos" in wp and isinstance(wp.get("pos"), list) and len(wp["pos"]) >= 2:
                        px, py = rotate_xy_clockwise(wp["pos"][0], wp["pos"][1], origin_x, origin_y, yaw_deg)
                        wp["pos"][0] = px
                        wp["pos"][1] = py
                    elif "x" in wp and "y" in wp:
                        px, py = rotate_xy_clockwise(wp.get("x", 0.0), wp.get("y", 0.0), origin_x, origin_y, yaw_deg)
                        wp["x"] = px
                        wp["y"] = py
                elif isinstance(wp, list) and len(wp) >= 2:
                    px, py = rotate_xy_clockwise(wp[0], wp[1], origin_x, origin_y, yaw_deg)
                    wp[0] = px
                    wp[1] = py

    task = loader.scenario_data.get("task_order", None)
    if isinstance(task, dict):
        if "anchor_x_m" in task and "anchor_y_m" in task:
            try:
                px, py = rotate_xy_clockwise(
                    float(task.get("anchor_x_m", 0.0)),
                    float(task.get("anchor_y_m", 0.0)),
                    origin_x,
                    origin_y,
                    yaw_deg,
                )
                task["anchor_x_m"] = px
                task["anchor_y_m"] = py
            except Exception:
                pass
        if "station_heading_deg" in task:
            try:
                task["station_heading_deg"] = (float(task.get("station_heading_deg", 0.0)) + float(yaw_deg)) % 360.0
            except Exception:
                pass
