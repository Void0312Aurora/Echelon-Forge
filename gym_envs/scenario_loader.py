import json
import os
import math
import ef_py
import numpy as np

class ScenarioLoader:
    def __init__(self, sim_kernel):
        self.sim = sim_kernel
        self.scenario_data = {}
        self.entities = {} # map name -> entity_id
        self.agent_id = None
        self.steps = 0
        self.captured_time = 0.0
        self.max_contacts = 10
        self.max_rwr = 4

        # Waypoint mission state (command_code == 3).
        # Waypoints are part of the mission command (realistic: FMS/EGI steerpoints).
        self.waypoints: list[dict] = []
        self.waypoint_idx: int = 0
        self._waypoint_prev_dist_m: float | None = None
        
        # Property Map for generic access
        self.prop_map = {
            "altitude": 2, "z": 2,
            "speed": 9, "velocity": 9,
            "health": 10, "hp": 10,
            "missiles": 11, "ammo": 11,
            "pitch": 7, "roll": 8, "heading": 6,
            "x": 0, "y": 1,
            "vx": 3, "vy": 4, "vz": 5
        }
        self.ils_beacons = []
        self.world_yaw_deg = 0.0
        self.rotate_mission_heading_with_world = False
        self.randomization_overrides = {}

    def set_randomization_overrides(self, overrides: dict | None) -> None:
        """
        Override `environment.randomization` fields from the scenario JSON at load time.

        Intended for curriculum learning: gradually increase randomization ranges (wind/yaw)
        without editing the scenario file on disk.
        """
        if overrides is None:
            self.randomization_overrides = {}
            return
        if not isinstance(overrides, dict):
            raise TypeError(f"randomization overrides must be a dict or None, got {type(overrides)}")
        self.randomization_overrides = dict(overrides)
        
    def load_scenario(self, json_path, seed=42):
        if seed is None:
            seed = np.random.randint(0, 2**32 - 1)
        seed = int(seed) & 0xFFFFFFFF
        self.rng = np.random.RandomState(seed)
        with open(json_path, 'r') as f:
            self.scenario_data = json.load(f)
            
        # Handle Options/Imports (Generic Prefabs)
        if "imports" in self.scenario_data:
            self._process_imports(self.scenario_data["imports"])
            
        # Parse Mission Command
        self.mission_cmd = self.scenario_data.get("mission_command", {
            "command_code": 0, "target_heading": 0.0, "target_altitude": 0.0, "target_speed": 0.0
        })
            
        # 1. Setup Environment
        if "environment" in self.scenario_data:
            env_cfg = self.scenario_data["environment"]
            env_rand = env_cfg.get("randomization", {}) if isinstance(env_cfg.get("randomization", {}), dict) else {}
            if isinstance(self.randomization_overrides, dict) and self.randomization_overrides:
                env_rand = dict(env_rand)
                env_rand.update(self.randomization_overrides)
            self.rotate_mission_heading_with_world = bool(env_rand.get("rotate_mission_heading_with_world", False))

            # World yaw randomization (rotates the entire scenario geometry around an origin).
            # This prevents agents from exploiting fixed runway/terrain headings.
            self.world_yaw_deg = 0.0
            if "world_yaw_range" in env_rand:
                r = env_rand["world_yaw_range"]
                yaw_deg = float(self.rng.uniform(r[0], r[1]))
                origin = env_rand.get("world_yaw_origin", [0.0, 0.0])
                try:
                    ox = float(origin[0])
                    oy = float(origin[1])
                except Exception:
                    ox, oy = 0.0, 0.0
                self._apply_world_yaw(yaw_deg, ox, oy)
                self.world_yaw_deg = yaw_deg

            if "time_step" in env_cfg:
                self.sim.set_time_step(env_cfg["time_step"])

            # Wind / Atmosphere configuration (optional)
            # Uses NAV convention for direction "from": 0=North, CW positive.
            wind_cfg = env_cfg.get("wind", {}) if isinstance(env_cfg.get("wind", {}), dict) else {}

            wind_speed = float(wind_cfg.get("speed_mps", 10.0))
            wind_dir_from = float(wind_cfg.get("dir_from_deg", 270.0))
            wind_shear = float(wind_cfg.get("shear_mps_per_km", 4.0))

            def _primary_runway_heading_deg() -> float | None:
                zones = env_cfg.get("zones", [])
                if not isinstance(zones, list):
                    return None
                best = None
                best_pri = -1
                for z in zones:
                    if not isinstance(z, dict):
                        continue
                    name = str(z.get("name", "")).lower()
                    surface = str(z.get("surface", ""))
                    ils_cfg = z.get("ils", {})
                    if not isinstance(ils_cfg, dict):
                        ils_cfg = {}
                    ils_enabled = bool(ils_cfg.get("enabled", False))
                    is_runway = "runway" in name
                    # Priority: ILS-enabled runway > named runway > other paved zones.
                    pri = 0
                    if ils_enabled and is_runway:
                        pri = 3
                    elif ils_enabled:
                        pri = 2
                    elif is_runway and surface in ("Concrete", "Asphalt"):
                        pri = 1
                    if pri <= best_pri:
                        continue
                    try:
                        hdg = float(z.get("heading", 0.0)) % 360.0
                    except Exception:
                        continue
                    best = hdg
                    best_pri = pri
                return best

            # Optional: runway-relative wind sampling (realistic for takeoff/landing scenarios).
            # Specify headwind/crosswind components instead of global direction:
            #   wind_headwind_range:   [min, max] m/s  (positive = headwind, negative = tailwind)
            #   wind_crosswind_range:  [min, max] m/s  (positive = wind-from runway right)
            #   wind_tailwind_max_mps: float         (optional clamp for negative headwind)
            used_runway_relative_wind = False
            if "wind_headwind_range" in env_rand or "wind_crosswind_range" in env_rand:
                r_h = env_rand.get("wind_headwind_range", [0.0, 0.0])
                r_c = env_rand.get("wind_crosswind_range", [0.0, 0.0])
                try:
                    headwind = float(self.rng.uniform(float(r_h[0]), float(r_h[1])))
                except Exception:
                    headwind = 0.0
                try:
                    crosswind = float(self.rng.uniform(float(r_c[0]), float(r_c[1])))
                except Exception:
                    crosswind = 0.0

                tw_max = env_rand.get("wind_tailwind_max_mps", env_rand.get("wind_tailwind_max", None))
                if tw_max is not None:
                    try:
                        tw_max_f = abs(float(tw_max))
                        headwind = max(headwind, -tw_max_f)
                    except Exception:
                        pass

                rw_hdg = _primary_runway_heading_deg()
                if rw_hdg is not None:
                    h_rad = math.radians(float(rw_hdg))
                    fwd_x = math.sin(h_rad)
                    fwd_y = math.cos(h_rad)
                    right_x = math.cos(h_rad)
                    right_y = -math.sin(h_rad)
                    wx = headwind * fwd_x + crosswind * right_x
                    wy = headwind * fwd_y + crosswind * right_y
                    wind_speed = float(math.sqrt(wx * wx + wy * wy))
                    wind_dir_from = float((math.degrees(math.atan2(wx, wy)) + 360.0) % 360.0)
                    used_runway_relative_wind = True

            if not used_runway_relative_wind:
                if "wind_speed_range" in env_rand:
                    r = env_rand["wind_speed_range"]
                    wind_speed = float(self.rng.uniform(r[0], r[1]))
                if "wind_dir_from_range" in env_rand:
                    r = env_rand["wind_dir_from_range"]
                    wind_dir_from = float(self.rng.uniform(r[0], r[1]))
            if "wind_shear_range" in env_rand:
                r = env_rand["wind_shear_range"]
                wind_shear = float(self.rng.uniform(r[0], r[1]))

            # Interpret wind_speed_range as the wind speed at a *reference altitude* when shear is enabled.
            #
            # The environment model applies shear as: v(z) = base_speed + shear * (z_km).
            # If we directly sample base_speed from wind_speed_range and also apply positive shear,
            # the resulting wind at typical start altitudes (e.g., 1000m) can exceed the configured
            # range by a large margin (speed + shear*1km). That makes scenario randomization harder to
            # reason about and often less realistic.
            #
            # To keep scenario configs intuitive and realism-first, we treat wind_speed_range as the
            # intended wind magnitude at a reference altitude (default: agent spawn altitude) and
            # convert it to the base_speed passed into the environment model.
            if abs(float(wind_shear)) > 1.0e-9:
                wind_ref_alt_m = env_rand.get("wind_ref_alt_m", None)
                if wind_ref_alt_m is None:
                    try:
                        # Prefer agent spawn altitude as reference.
                        for ent in self.scenario_data.get("entities", []):
                            if isinstance(ent, dict) and bool(ent.get("is_agent", False)):
                                pos = ent.get("pos", None)
                                if isinstance(pos, list) and len(pos) >= 3:
                                    wind_ref_alt_m = float(pos[2])
                                    break
                    except Exception:
                        wind_ref_alt_m = None
                if wind_ref_alt_m is None:
                    try:
                        ents = self.scenario_data.get("entities", [])
                        if isinstance(ents, list) and ents:
                            pos = ents[0].get("pos", None) if isinstance(ents[0], dict) else None
                            if isinstance(pos, list) and len(pos) >= 3:
                                wind_ref_alt_m = float(pos[2])
                    except Exception:
                        wind_ref_alt_m = None
                if wind_ref_alt_m is None:
                    wind_ref_alt_m = 0.0
                alt_km_ref = max(0.0, float(wind_ref_alt_m)) / 1000.0
                try:
                    base_speed = float(wind_speed) - float(wind_shear) * alt_km_ref
                except Exception:
                    base_speed = float(wind_speed)
                wind_speed = max(0.0, base_speed)

            if hasattr(self.sim, "set_wind"):
                try:
                    self.sim.set_wind(wind_speed, wind_dir_from, wind_shear)
                except Exception:
                    pass
            
            # Zones (Runways/Terrains)
            if hasattr(self.sim, 'clear_zones'):
                self.sim.clear_zones()
                
                # Zone Type Map (String -> Int)
                surf_map = {
                    "Concrete": 0, "Asphalt": 1, 
                    "HardPacked": 2, "SoftDirt": 3, 
                    "Water": 4, "Obstacle": 5
                }
                
                for z in env_cfg.get("zones", []):
                    sx = surf_map.get(z.get("surface", "SoftDirt"), 3)
                    if os.environ.get("CMO_DEBUG_ZONES"):
                        print(f"[DEBUG] Adding zone: {z.get('name', 'Zone')} at ({z.get('x')}, {z.get('y')}) heading={z.get('heading')}")
                    self.sim.add_zone(
                        z.get("name", "Zone"),
                        float(z.get("x", 0.0)),
                        float(z.get("y", 0.0)),
                        float(z.get("width", 1000.0)),
                        float(z.get("length", 1000.0)),
                        float(z.get("heading", 0.0)),
                        int(sx)
                    )
        
        # 2. Spawn Entities
        self.entities = {}
        agents = []
        self.sim.reset(seed)  # Deterministic Physics Reset
        
        for ent_cfg in self.scenario_data.get("entities", []):
            side_map = {
                "Blue": ef_py.Side.Blue,
                "Red": ef_py.Side.Red,
                "Neutral": ef_py.Side.Neutral
            }
            side = side_map.get(ent_cfg["side"], ef_py.Side.Neutral)
            
            p = ent_cfg["pos"]
            v = ent_cfg["vel"]
            
            # Optional Orientation (Default to 0 if not provided)
            heading = float(ent_cfg.get("heading", 0.0))
            pitch = float(ent_cfg.get("pitch", 0.0))
            roll = float(ent_cfg.get("roll", 0.0))

            eid = self.sim.spawn_unit(
                side,
                ent_cfg["type"],
                float(p[0]), float(p[1]), float(p[2]),
                heading, pitch, roll,
                float(v[0]), float(v[1]), float(v[2])
            )
            
            self.entities[ent_cfg["name"]] = eid
            
            if ent_cfg.get("is_agent", False):
                agents.append(eid)
        
        self.agent_id = agents[0] if agents else None
        self.steps = 0
        self.captured_time = 0.0
        
        # Reset State Tracking for Rewards
        self.prev_alt = 0.0
        self.prev_speed = 0.0
        self.gear_bonus_awarded = False
        self.liftoff_awarded = False
        self.off_runway_steps = 0
        
        # Randomize Mission if ranges provided
        self._randomize_mission()

        # Optional: rotate mission target heading together with world-yaw randomization.
        # Default is to keep mission headings in global coordinates (more realistic for command inputs).
        if self.rotate_mission_heading_with_world and self.world_yaw_deg != 0.0:
            try:
                self.mission_cmd["target_heading"] = float(self.mission_cmd.get("target_heading", 0.0)) + float(self.world_yaw_deg)
            except Exception:
                pass
            self.mission_cmd["target_heading"] = float(self.mission_cmd.get("target_heading", 0.0)) % 360.0

        # Parse mission waypoints (if any). This must run after world-yaw has been applied.
        self._parse_waypoints()

        # Mirror mission command into the simulation kernel (so cmd_* instrument fields and
        # any mission-aware systems stay consistent with the Python-side mission randomization).
        if self.agent_id is not None and hasattr(self.sim, "set_mission_command") and hasattr(ef_py, "MissionCommand"):
            try:
                cmd = ef_py.MissionCommand()
                cmd.active = True
                cmd.command_code = int(self.mission_cmd.get("command_code", 0))
                cmd.cmd_heading_deg = float(self.mission_cmd.get("target_heading", 0.0))
                cmd.cmd_altitude_m = float(self.mission_cmd.get("target_altitude", 0.0))
                cmd.cmd_speed_mps = float(self.mission_cmd.get("target_speed", 0.0))
                self.sim.set_mission_command(self.agent_id, cmd)
            except Exception:
                pass
        
        # Initialize prev state if agent exists
        if self.agent_id is not None:
             truth = self.sim.get_agent_observation(self.agent_id)
             self.prev_alt = truth.z
             # Waypoint LNAV: leg origin for the first leg is the spawn position.
             self._waypoint_leg_origin_x = float(getattr(truth, "x", 0.0))
             self._waypoint_leg_origin_y = float(getattr(truth, "y", 0.0))
             # Use IAS for speed shaping/objectives (robust under randomized wind).
             # Ground speed is still used for stationary detection.
             try:
                 inst0 = self.sim.get_instrument_state(self.agent_id)
                 self.prev_speed = float(inst0.ias)
             except Exception:
                 self.prev_speed = truth.speed

        # If this is a waypoint mission, initialize the commanded heading/targets immediately so the
        # very first observation matches the active waypoint.
        try:
            self.update_behaviors(0.0)
        except Exception:
            pass

        # Cache ILS beacons (purely derived from scenario geometry; no direct runway heading is exposed).
        self.ils_beacons = self._extract_ils_beacons()
             
        return self.agent_id

    def _extract_ils_beacons(self):
        beacons = []
        zones = self.scenario_data.get("environment", {}).get("zones", [])
        if not isinstance(zones, list):
            return beacons

        for zone in zones:
            if not isinstance(zone, dict):
                continue
            name = str(zone.get("name", ""))
            surface = str(zone.get("surface", ""))
            ils_cfg = zone.get("ils", {})
            if not isinstance(ils_cfg, dict):
                ils_cfg = {}

            enabled = bool(ils_cfg.get("enabled", False))
            if not enabled:
                # Sensible default: paved runway/taxiway zones can provide an ILS beacon if named as runway.
                if ("runway" in name.lower()) and surface in ("Concrete", "Asphalt"):
                    enabled = True
                else:
                    continue

            try:
                cx = float(zone.get("x", 0.0))
                cy = float(zone.get("y", 0.0))
                width = float(zone.get("width", 0.0))
                length = float(zone.get("length", 0.0))
                heading = float(zone.get("heading", 0.0)) % 360.0
            except Exception:
                continue

            if length <= 1.0:
                continue
            if width <= 1.0:
                # Default runway width fallback (meters)
                width = float(ils_cfg.get("width_m", 60.0))

            glide_slope_deg = float(ils_cfg.get("glide_slope_deg", 3.0))
            loc_max_deg = float(ils_cfg.get("loc_max_deg", 2.5))
            gs_max_deg = float(ils_cfg.get("gs_max_deg", 0.7))
            range_m = float(ils_cfg.get("range_m", 25000.0))
            elev_m = float(ils_cfg.get("elev_m", 0.0))

            # NAV heading (0=N, CW): forward unit vector (x=East, y=North).
            h_rad = math.radians(heading)
            fwd_x = math.sin(h_rad)
            fwd_y = math.cos(h_rad)

            thr_x = cx - fwd_x * (length * 0.5)
            thr_y = cy - fwd_y * (length * 0.5)

            beacons.append(
                {
                    "name": name,
                    "cx": cx,
                    "cy": cy,
                    "thr_x": thr_x,
                    "thr_y": thr_y,
                    "heading": heading,
                    "length": length,
                    "width": width,
                    "elev_m": elev_m,
                    "glide_slope_deg": glide_slope_deg,
                    "loc_max_deg": max(0.1, loc_max_deg),
                    "gs_max_deg": max(0.1, gs_max_deg),
                    "range_m": max(100.0, range_m),
                }
            )

        return beacons

    def _nearest_ils_beacon(self, x_m: float, y_m: float):
        if not self.ils_beacons:
            return None
        best = None
        best_d2 = float("inf")
        for b in self.ils_beacons:
            dx = x_m - float(b.get("cx", 0.0))
            dy = y_m - float(b.get("cy", 0.0))
            d2 = dx * dx + dy * dy
            if d2 < best_d2:
                best_d2 = d2
                best = b
        return best

    def get_runway_local_frame(self, x_m: float, y_m: float):
        """
        Returns a geometry-only runway frame derived from the nearest ILS beacon.

        Output:
          valid: bool
          along_m: float  (positive along runway forward axis, relative to runway center)
          cross_m: float  (positive to the runway right)
          length_m: float
          width_m: float
        """
        b = self._nearest_ils_beacon(x_m, y_m)
        if b is None:
            return False, 0.0, 0.0, 0.0, 0.0
        h_rad = math.radians(float(b.get("heading", 0.0)))
        fwd_x = math.sin(h_rad)
        fwd_y = math.cos(h_rad)
        right_x = math.cos(h_rad)
        right_y = -math.sin(h_rad)

        dx = x_m - float(b.get("cx", 0.0))
        dy = y_m - float(b.get("cy", 0.0))
        along = dx * fwd_x + dy * fwd_y
        cross = dx * right_x + dy * right_y
        length = float(b.get("length", 0.0))
        width = float(b.get("width", 0.0))
        if not (length > 1.0 and width > 1.0):
            return False, float(along), float(cross), float(length), float(width)
        return True, float(along), float(cross), float(length), float(width)

    def get_ils_observation(self, x_m: float, y_m: float, alt_m: float):
        """
        Returns a small navigation observation vector:
        [ils_valid, loc_dev, gs_dev, dme_m]

        - loc_dev, gs_dev are normalized to [-1, 1] using the configured max deflections.
        - dme_m is slant-range distance to the threshold reference point.
        """
        if not self.ils_beacons:
            return np.zeros((4,), dtype=np.float32)

        best = None
        best_d2 = float("inf")
        for b in self.ils_beacons:
            dx = x_m - b["cx"]
            dy = y_m - b["cy"]
            d2 = dx * dx + dy * dy
            if d2 < best_d2:
                best_d2 = d2
                best = b

        if best is None:
            return np.zeros((4,), dtype=np.float32)

        h_rad = math.radians(float(best["heading"]))
        fwd_x = math.sin(h_rad)
        fwd_y = math.cos(h_rad)
        right_x = math.cos(h_rad)
        right_y = -math.sin(h_rad)

        # Localizer geometry: use a fixed reference point at the far end of the runway
        # (opposite the threshold) to avoid a singularity near the runway center.
        #
        # This yields a stable, pilot-like "centerline deviation angle" throughout the takeoff roll.
        cx = float(best["cx"])
        cy = float(best["cy"])
        length = float(best.get("length", 0.0))
        loc_x = cx + fwd_x * (0.5 * length)
        loc_y = cy + fwd_y * (0.5 * length)

        dx = x_m - loc_x
        dy = y_m - loc_y
        # Positive "along" means the aircraft is in front of the localizer antenna; clamp for safety.
        along = -(dx * fwd_x + dy * fwd_y)
        cross = dx * right_x + dy * right_y

        along_abs = max(abs(along), 1.0)
        loc_angle_deg = math.degrees(math.atan2(cross, along_abs))
        loc_dev = float(np.clip(loc_angle_deg / float(best["loc_max_deg"]), -1.0, 1.0))

        thr_dx = x_m - float(best["thr_x"])
        thr_dy = y_m - float(best["thr_y"])
        along_thr = thr_dx * fwd_x + thr_dy * fwd_y
        dme = float(math.sqrt(thr_dx * thr_dx + thr_dy * thr_dy + (alt_m - float(best["elev_m"])) ** 2))

        glide_slope_deg = float(best["glide_slope_deg"])
        gs_max_deg = float(best["gs_max_deg"])

        if along_thr <= 1.0:
            gs_dev = 0.0
        else:
            gs_angle_deg = math.degrees(math.atan2(max(0.0, alt_m - float(best["elev_m"])), along_thr))
            gs_dev = float(np.clip((gs_angle_deg - glide_slope_deg) / gs_max_deg, -1.0, 1.0))

        valid = 1.0 if dme <= float(best["range_m"]) else 0.0

        return np.array([valid, loc_dev, gs_dev, dme], dtype=np.float32)

    def _randomize_mission(self):
        """Randomize mission parameters if ranges are specified in config."""
        # Use seeded RNG (self.rng) instead of global
        base_cmd = self.scenario_data.get("mission_command", {})
        
        # Check for randomization config
        rand_cfg = base_cmd.get("randomization", {})
        
        # 1. Heading
        if "heading_range" in rand_cfg:
            r = rand_cfg["heading_range"]
            self.mission_cmd["target_heading"] = self.rng.uniform(r[0], r[1])
        
        # 2. Altitude
        if "altitude_range" in rand_cfg:
            r = rand_cfg["altitude_range"]
            self.mission_cmd["target_altitude"] = self.rng.uniform(r[0], r[1])
            
        # 3. Speed
        if "speed_range" in rand_cfg:
            r = rand_cfg["speed_range"]
            self.mission_cmd["target_speed"] = self.rng.uniform(r[0], r[1])
        
        # Ensure values are floats
        self.mission_cmd["target_heading"] = float(self.mission_cmd.get("target_heading", 0.0))
        self.mission_cmd["target_altitude"] = float(self.mission_cmd.get("target_altitude", 0.0))
        self.mission_cmd["target_speed"] = float(self.mission_cmd.get("target_speed", 0.0))
        self.mission_cmd["command_code"] = int(self.mission_cmd.get("command_code", 0))

    @staticmethod
    def _rotate_xy_clockwise(x, y, origin_x, origin_y, yaw_deg):
        """Rotate (x,y) around (origin_x, origin_y) by yaw_deg clockwise (NAV convention)."""
        rad = -math.radians(float(yaw_deg))
        c = math.cos(rad)
        s = math.sin(rad)
        dx = float(x) - float(origin_x)
        dy = float(y) - float(origin_y)
        rx = float(origin_x) + c * dx - s * dy
        ry = float(origin_y) + s * dx + c * dy
        return rx, ry

    def _apply_world_yaw(self, yaw_deg, origin_x=0.0, origin_y=0.0):
        """Apply a deterministic world-yaw rotation to zones and entities."""
        # Zones
        env = self.scenario_data.get("environment", {})
        zones = env.get("zones", [])
        if isinstance(zones, list):
            for z in zones:
                if not isinstance(z, dict):
                    continue
                if "x" in z and "y" in z:
                    zx, zy = self._rotate_xy_clockwise(z.get("x", 0.0), z.get("y", 0.0), origin_x, origin_y, yaw_deg)
                    z["x"] = zx
                    z["y"] = zy
                if "heading" in z:
                    try:
                        z["heading"] = (float(z.get("heading", 0.0)) + float(yaw_deg)) % 360.0
                    except Exception:
                        pass

        # Entities
        ents = self.scenario_data.get("entities", [])
        if isinstance(ents, list):
            for ent in ents:
                if not isinstance(ent, dict):
                    continue
                pos = ent.get("pos", None)
                vel = ent.get("vel", None)
                if isinstance(pos, list) and len(pos) >= 2:
                    px, py = self._rotate_xy_clockwise(pos[0], pos[1], origin_x, origin_y, yaw_deg)
                    pos[0] = px
                    pos[1] = py
                if isinstance(vel, list) and len(vel) >= 2:
                    vx, vy = self._rotate_xy_clockwise(vel[0], vel[1], 0.0, 0.0, yaw_deg)
                    vel[0] = vx
                    vel[1] = vy
                if "heading" in ent:
                    try:
                        ent["heading"] = (float(ent.get("heading", 0.0)) + float(yaw_deg)) % 360.0
                    except Exception:
                        pass

        # Mission waypoints (if present): rotate together with the world so the mission remains consistent
        # under world-yaw randomization.
        mc = self.scenario_data.get("mission_command", None)
        if isinstance(mc, dict):
            wps = mc.get("waypoints", None)
            if isinstance(wps, list):
                for wp in wps:
                    if isinstance(wp, dict):
                        if "pos" in wp and isinstance(wp.get("pos"), list) and len(wp["pos"]) >= 2:
                            px, py = self._rotate_xy_clockwise(wp["pos"][0], wp["pos"][1], origin_x, origin_y, yaw_deg)
                            wp["pos"][0] = px
                            wp["pos"][1] = py
                        elif "x" in wp and "y" in wp:
                            px, py = self._rotate_xy_clockwise(wp.get("x", 0.0), wp.get("y", 0.0), origin_x, origin_y, yaw_deg)
                            wp["x"] = px
                            wp["y"] = py
                    elif isinstance(wp, list) and len(wp) >= 2:
                        px, py = self._rotate_xy_clockwise(wp[0], wp[1], origin_x, origin_y, yaw_deg)
                        wp[0] = px
                        wp[1] = py

    def _parse_waypoints(self) -> None:
        """
        Parse mission waypoints from scenario_data into a normalized internal list.

        Supported waypoint formats:
          - {"x":..., "y":..., "z":...}
          - {"pos":[x,y,z]}
          - [x, y, z]
        Optional per-waypoint overrides:
          - radius_m / arrival_radius_m
          - altitude_m / altitude / target_altitude / z
          - speed_mps / speed / target_speed
        """
        self.waypoints = []
        self.waypoint_idx = 0
        self._waypoint_prev_dist_m = None

        mc = self.scenario_data.get("mission_command", None)
        if not isinstance(mc, dict):
            return
        wps = mc.get("waypoints", None)
        if not isinstance(wps, list) or not wps:
            return

        def _f(x, default: float | None = None) -> float | None:
            if x is None:
                return default
            try:
                return float(x)
            except Exception:
                return default

        default_alt = _f(mc.get("target_altitude", 0.0), 0.0) or 0.0
        default_spd = _f(mc.get("target_speed", 0.0), 0.0) or 0.0
        default_rad = _f(mc.get("waypoint_radius_m", mc.get("arrival_radius_m", 500.0)), 500.0) or 500.0

        for wp in wps:
            x = y = z = None
            rad = None
            alt = None
            spd = None
            if isinstance(wp, dict):
                if "pos" in wp and isinstance(wp.get("pos"), list) and len(wp["pos"]) >= 2:
                    x = _f(wp["pos"][0], 0.0)
                    y = _f(wp["pos"][1], 0.0)
                    if len(wp["pos"]) >= 3:
                        z = _f(wp["pos"][2], default_alt)
                else:
                    x = _f(wp.get("x", None), 0.0)
                    y = _f(wp.get("y", None), 0.0)
                    z = _f(
                        wp.get("z", wp.get("altitude_m", wp.get("altitude", wp.get("target_altitude", None)))),
                        default_alt,
                    )
                rad = _f(wp.get("radius_m", wp.get("arrival_radius_m", None)), default_rad)
                alt = _f(wp.get("altitude_m", wp.get("altitude", wp.get("target_altitude", None))), z if z is not None else default_alt)
                spd = _f(wp.get("speed_mps", wp.get("speed", wp.get("target_speed", None))), default_spd)
            elif isinstance(wp, list) and len(wp) >= 2:
                x = _f(wp[0], 0.0)
                y = _f(wp[1], 0.0)
                z = _f(wp[2], default_alt) if len(wp) >= 3 else default_alt
                rad = default_rad
                alt = z
                spd = default_spd

            if x is None or y is None:
                continue

            self.waypoints.append(
                {
                    "x": float(x),
                    "y": float(y),
                    "z": float(z if z is not None else default_alt),
                    "radius_m": float(rad if rad is not None else default_rad),
                    "altitude_m": float(alt if alt is not None else (z if z is not None else default_alt)),
                    "speed_mps": float(spd if spd is not None else default_spd),
                }
            )

    @staticmethod
    def _bearing_to_deg(dx: float, dy: float) -> float:
        # Heading convention: 0=North, +CW. Vector mapping used in viz: x=sin(hdg), y=cos(hdg).
        return float((math.degrees(math.atan2(float(dx), float(dy))) + 360.0) % 360.0)

    def _process_imports(self, imports):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(base_dir, ".."))
        
        for imp in imports:
            path = imp.get("file")
            if not path: continue
            
            full_path = os.path.join(project_root, path)
            if not os.path.exists(full_path):
                print(f"Warning: Import file not found: {full_path}")
                continue
                
            with open(full_path, 'r') as f:
                prefab = json.load(f)
                
            # Merge Zones
            if "zones" in prefab:
                # Ensure environment dict exists
                if "environment" not in self.scenario_data:
                    self.scenario_data["environment"] = {}
                current_zones = self.scenario_data["environment"].get("zones", [])
                current_zones.extend(prefab["zones"])
                self.scenario_data["environment"]["zones"] = current_zones
                if os.environ.get("CMO_DEBUG_ZONES"):
                    print(f"[DEBUG] Merged {len(prefab['zones'])} zones from prefab")
                
            # Merge Entities
            if "entities" in prefab:
                current_ents = self.scenario_data.get("entities", [])
                current_ents.extend(prefab["entities"])
                self.scenario_data["entities"] = current_ents

    def get_max_steps(self):
        meta = self.scenario_data.get("meta", {})
        if "max_steps" in meta:
            return int(meta["max_steps"])
        env = self.scenario_data.get("environment", {})
        if "max_steps" in env:
            return int(env["max_steps"])
        return 2000

    def get_rewards_config(self):
        return self.scenario_data.get("rewards", {})

    def get_objectives(self):
        return self.scenario_data.get("objectives", [])
    
    def get_entity_id(self, name):
        return self.entities.get(name)
        
    def get_mission_observation(self):
        """Returns [command_code, target_heading, target_altitude, target_speed]"""
        return np.array([
            float(self.mission_cmd["command_code"]),
            float(self.mission_cmd["target_heading"]),
            float(self.mission_cmd["target_altitude"]),
            float(self.mission_cmd["target_speed"])
        ], dtype=np.float32)

    def update_behaviors(self, sim_time):
        # Waypoint navigation: update commanded lateral steering for the active waypoint leg.
        #
        # Realism-first: in real aircraft, the EGI/FMS provides LNAV-style guidance:
        #   - a desired track (DTK) for the active leg (prev_wp -> next_wp)
        #   - an intercept/capture command when off-track (XTK)
        #
        # We model this by commanding a *ground-referenced* track bug (stored in mission_cmd["target_heading"])
        # that includes a small intercept angle based on cross-track error. This uses only mission data
        # (the flight plan waypoints) and own-ship navigation state, without exposing privileged world geometry
        # to the agent beyond what real avionics would present.
        if not self.waypoints or self.agent_id is None:
            return
        try:
            cmd_code = int(self.mission_cmd.get("command_code", 0))
        except Exception:
            cmd_code = 0
        if cmd_code != 3:
            return

        idx = int(getattr(self, "waypoint_idx", 0))
        if idx < 0:
            idx = 0
        if idx >= len(self.waypoints):
            return

        wp = self.waypoints[idx]
        try:
            truth = self.sim.get_agent_observation(self.agent_id)
        except Exception:
            return

        # Leg start: spawn position for the first leg, then previous waypoint for subsequent legs.
        if idx <= 0:
            sx = float(getattr(self, "_waypoint_leg_origin_x", getattr(truth, "x", 0.0)))
            sy = float(getattr(self, "_waypoint_leg_origin_y", getattr(truth, "y", 0.0)))
        else:
            prev = self.waypoints[idx - 1]
            sx = float(prev.get("x", 0.0))
            sy = float(prev.get("y", 0.0))

        ex = float(wp.get("x", 0.0))
        ey = float(wp.get("y", 0.0))

        lx = ex - sx
        ly = ey - sy
        leg_len = float(math.hypot(lx, ly))
        if leg_len < 1.0e-6:
            # Degenerate leg: fall back to direct-to bearing.
            dx = ex - float(getattr(truth, "x", 0.0))
            dy = ey - float(getattr(truth, "y", 0.0))
            desired_track_deg = float(self._bearing_to_deg(dx, dy))
            self.mission_cmd["target_heading"] = desired_track_deg
        else:
            # Desired track is the bearing of the active leg (DTK), not the instantaneous bearing-to-fix.
            desired_track_deg = float(self._bearing_to_deg(lx, ly))

            # Cross-track error (XTK) relative to the leg, positive = right of track.
            ux = lx / leg_len
            uy = ly / leg_len
            rx = uy
            ry = -ux
            px = float(getattr(truth, "x", 0.0)) - sx
            py = float(getattr(truth, "y", 0.0)) - sy
            xtk_m = float(px * rx + py * ry)

            # Intercept: small angle proportional to cross-track, using an L1-like lookahead distance.
            lookahead_m = float(self.mission_cmd.get("lnav_lookahead_m", 1500.0))
            try:
                inst = self.sim.get_instrument_state(self.agent_id)
                spd = float(getattr(inst, "ias", 0.0))
            except Exception:
                spd = 0.0
            if math.isfinite(spd) and spd > 1.0:
                lookahead_m = max(500.0, min(5000.0, float(spd) * 8.0))
            lookahead_m = max(200.0, float(lookahead_m))
            # Negative sign: if we're right of track (+xtk), command a left intercept (negative angle).
            intercept_rad = math.atan2(-xtk_m, lookahead_m)
            intercept_deg = float(math.degrees(intercept_rad))
            max_int = float(self.mission_cmd.get("lnav_max_intercept_deg", 25.0))
            if max_int > 0.0:
                intercept_deg = float(np.clip(intercept_deg, -max_int, max_int))
            cmd_track = float((desired_track_deg + intercept_deg + 360.0) % 360.0)
            self.mission_cmd["target_heading"] = cmd_track

        # Optional per-waypoint cruise constraints.
        try:
            self.mission_cmd["target_altitude"] = float(wp.get("altitude_m", self.mission_cmd.get("target_altitude", 0.0)))
        except Exception:
            pass
        try:
            self.mission_cmd["target_speed"] = float(wp.get("speed_mps", self.mission_cmd.get("target_speed", 0.0)))
        except Exception:
            pass

        # Keep simulation kernel mission command in sync so InstrumentState.cmd_* matches.
        if hasattr(self.sim, "set_mission_command") and hasattr(ef_py, "MissionCommand"):
            try:
                cmd = ef_py.MissionCommand()
                cmd.active = True
                cmd.command_code = int(self.mission_cmd.get("command_code", 0))
                cmd.cmd_heading_deg = float(self.mission_cmd.get("target_heading", 0.0))
                cmd.cmd_altitude_m = float(self.mission_cmd.get("target_altitude", 0.0))
                cmd.cmd_speed_mps = float(self.mission_cmd.get("target_speed", 0.0))
                self.sim.set_mission_command(self.agent_id, cmd)
            except Exception:
                pass

    def compute_full_step(self, obs, sim, steps, max_steps):
        rules = self.scenario_data.get("objectives", [])
        cfg = self.scenario_data.get("rewards", {})
        
        # Get Truth State for Scoring
        truth = sim.get_agent_observation(self.agent_id)
        
        # Extract Physical Props from Instruments for Safety Checks
        # Obs layout: [ias(0), mach, alt_baro(2), ..., aoa(5), ..., roll(8), heading(9), g_load(10), ..., gear(18)]
        inst = obs["instruments"]
        curr_aoa = inst[5]
        curr_roll = inst[8]
        curr_g = inst[10]
        curr_gear = inst[18]
        curr_ias = float(inst[0])

        def _finite(x) -> bool:
            try:
                return math.isfinite(float(x))
            except Exception:
                return False

        # Hard guard: if physics produces NaN/Inf, terminate immediately to avoid poisoning training.
        truncated = (steps >= max_steps)
        if not all(
            _finite(v)
            for v in (
                getattr(truth, "x", 0.0),
                getattr(truth, "y", 0.0),
                getattr(truth, "z", 0.0),
                getattr(truth, "vx", 0.0),
                getattr(truth, "vy", 0.0),
                getattr(truth, "vz", 0.0),
                getattr(truth, "speed", 0.0),
                getattr(truth, "pitch", 0.0),
                getattr(truth, "roll", 0.0),
                getattr(truth, "heading", 0.0),
                getattr(truth, "health", 100.0),
                curr_ias,
                float(inst[2]),  # alt_baro
                float(inst[3]),  # alt_radar
                curr_aoa,
                curr_roll,
                curr_g,
            )
        ):
            status = [0.0] * 4
            status[3] = -1.0
            return float(cfg.get("crash_penalty", -1000.0)), True, truncated, status

        # Use InstrumentState directly for gear damage / surface checks.
        # Note: stall/attitude envelope checks should not apply while the aircraft is still on the ground,
        # where AoA can be undefined/noisy at very low speeds.
        try:
            inst_obj = sim.get_instrument_state(self.agent_id)
        except Exception:
            inst_obj = None

        if inst_obj is not None:
            gear_collapsed = bool(getattr(inst_obj, "gear_collapsed", False))
            # Note: `InstrumentState.on_runway` is a surface-type flag ("on paved surface"),
            # not a geometry-accurate runway membership test. Use it for safety/termination.
            on_paved = bool(getattr(inst_obj, "on_runway", True))
            gear_stress = float(getattr(inst_obj, "gear_stress", 0.0))
        else:
            gear_collapsed = False
            on_paved = True
            gear_stress = 0.0
        alt_agl = float(inst[3])  # radar altitude (AGL)
        on_ground_alt_threshold = float(cfg.get("on_ground_alt_threshold", 2.5))
        airborne_alt_threshold = float(cfg.get("airborne_alt_threshold", cfg.get("liftoff_alt_threshold", 5.0)))
        on_ground = alt_agl <= on_ground_alt_threshold
        airborne = alt_agl >= airborne_alt_threshold
        # "Pre-liftoff" phase used for runway safety/termination: includes ground roll + rotation until the
        # aircraft clearly departs the runway environment.
        preliftoff = not airborne

        # Geometry-based runway membership (best-effort).
        # Prefer runway geometry over the surface-type flag so apron/taxiway do not count as "on runway".
        on_runway_geom = None
        runway_along_m = None
        runway_cross_m = None
        runway_len_m = None
        runway_wid_m = None
        try:
            valid_rf, along_m, cross_m, rw_len, rw_wid = self.get_runway_local_frame(float(truth.x), float(truth.y))
            if valid_rf and rw_len > 1.0 and rw_wid > 1.0:
                runway_along_m = float(along_m)
                runway_cross_m = float(cross_m)
                runway_len_m = float(rw_len)
                runway_wid_m = float(rw_wid)
                runway_width_margin_m = float(cfg.get("runway_width_margin_m", 2.0))
                runway_length_margin_m = float(cfg.get("runway_length_margin_m", 0.0))
                on_runway_geom = bool(
                    (abs(cross_m) <= 0.5 * rw_wid + runway_width_margin_m)
                    and (abs(along_m) <= 0.5 * rw_len + runway_length_margin_m)
                )
        except Exception:
            on_runway_geom = None

        # Task-level runway membership:
        # - Use geometry-based runway containment pre-liftoff when available (distinguishes runway vs apron/taxiway)
        # - Fall back to the surface-type flag (paved vs off-pavement) when geometry cannot be computed.
        # - Always report false once clearly airborne.
        on_runway_task = bool(on_paved) if preliftoff else False
        if on_runway_geom is not None:
            on_runway_task = bool(on_runway_geom) if preliftoff else False

        # Track consecutive off-runway steps pre-liftoff. This allows a short grace window for recovery
        # (e.g., brief edge crossing due to crosswind) while still preventing "apron takeoff" exploits.
        if preliftoff and (not on_runway_task):
            self.off_runway_steps = int(getattr(self, "off_runway_steps", 0)) + 1
        else:
            self.off_runway_steps = 0
        
        reward = 0.0
        terminated = False
        status = [0.0]*4
        
        # 1. Base Survival & Crash
        if truth.health <= 0:
            reward += cfg.get("crash_penalty", -1000.0)
            terminated = True
            status[3] = -1.0
        else:
            reward += cfg.get("survival", 0.01)
            
        # 2. Progress Shaping (Reward for increasing Alt/Speed towards target)
        # Only apply if not crashed
        if not terminated:
            # Altitude Progress
            tgt_alt = cfg.get("altitude_progress_target", None)
            if tgt_alt is None:
                tgt_alt = self.mission_cmd.get("target_altitude", 0.0)
            try:
                tgt_alt = float(tgt_alt)
            except Exception:
                tgt_alt = 0.0
            d_alt = truth.z - self.prev_alt
            if (tgt_alt <= 0.0 or truth.z < tgt_alt) and d_alt > 0:
                # Reward climbing only until reaching the configured target altitude.
                reward += d_alt * cfg.get("altitude_progress_weight", 0.0)
            elif truth.z < 10.0 and d_alt < -1.0: # Penalize rapid descent near ground
                 reward += d_alt * 0.1 
                 
            # Speed Progress (Until target speed)
            tgt_spd = cfg.get("speed_progress_target", None)
            if tgt_spd is None:
                tgt_spd = self.mission_cmd.get("target_speed", 180.0)
            try:
                tgt_spd = float(tgt_spd)
            except Exception:
                tgt_spd = 0.0
            # NOTE: use IAS (inst[0]) for progress shaping, not truth ground speed.
            d_spd = curr_ias - self.prev_speed
            if (tgt_spd <= 0.0 or curr_ias < tgt_spd) and d_spd > 0:
                reward += d_spd * cfg.get("speed_progress_weight", 0.0)
            elif d_spd < 0:
                reward += d_spd * cfg.get("speed_progress_weight_negative", 0.0)

            # Stationary penalty (discourage policies that never initiate takeoff roll)
            stationary_penalty = cfg.get("stationary_penalty", 0.0)
            if stationary_penalty != 0.0:
                grace_steps = int(cfg.get("stationary_grace_steps", 20))
                speed_thr = float(cfg.get("stationary_speed_threshold", 5.0))
                alt_thr = float(cfg.get("stationary_alt_threshold", 5.0))
                if steps > grace_steps and truth.speed < speed_thr and truth.z < alt_thr:
                    reward += float(stationary_penalty)

            # Takeoff shaping: reward first liftoff (wheels-off) event.
            liftoff_bonus = float(cfg.get("liftoff_bonus", 0.0))
            if liftoff_bonus != 0.0 and not self.liftoff_awarded:
                liftoff_speed_thr = float(cfg.get("liftoff_speed_threshold", 80.0))
                liftoff_alt_thr = float(cfg.get("liftoff_alt_threshold", 5.0))
                if float(inst[0]) >= liftoff_speed_thr and float(inst[3]) >= liftoff_alt_thr:
                    reward += liftoff_bonus
                    self.liftoff_awarded = True

            # Takeoff shaping: encourage rotation on the runway once above Vr.
            rotation_weight = float(cfg.get("rotation_reward_weight", 0.0))
            if rotation_weight != 0.0:
                rot_spd_thr = float(cfg.get("rotation_speed_threshold", 80.0))
                rot_alt_thr = float(cfg.get("rotation_alt_threshold", 5.0))
                rot_pitch_cap = float(cfg.get("rotation_pitch_cap", 15.0))
                if float(inst[0]) >= rot_spd_thr and float(inst[3]) <= rot_alt_thr:
                    # Encourage initiating rotation by rewarding positive pitch attitude and penalizing nose-down.
                    pitch_deg = float(inst[7])
                    pitch_term = float(np.clip(pitch_deg, -rot_pitch_cap, rot_pitch_cap))
                    reward += pitch_term * rotation_weight
                    # Discourage over-rotation on the runway (can cause loss of directional control / tail strike).
                    over_w = float(cfg.get("rotation_overpitch_penalty_weight", 0.0))
                    if over_w != 0.0 and pitch_deg > rot_pitch_cap:
                        reward += (pitch_deg - rot_pitch_cap) * over_w
            
            # Gear Bonus (One-time)
            # If above 50m and gear is up (<0.1), and haven't awarded yet
            if truth.z > 50.0 and curr_gear < 0.1 and not self.gear_bonus_awarded:
                reward += cfg.get("gear_up_bonus", 0.0)
                self.gear_bonus_awarded = True
                
            # 3. Safety Constraints (Penalties)
            # Stall
            aoa_valid = math.isfinite(float(curr_aoa)) and (abs(float(curr_aoa)) < 89.0) and (curr_ias > 10.0)
            stall_lim = cfg.get("stall_aoa_threshold", 15.0)
            if airborne and aoa_valid and abs(curr_aoa) > stall_lim:
                reward += cfg.get("stall_penalty", -1.0) * (abs(curr_aoa) - stall_lim)
                
            # Overload
            g_lim = cfg.get("overload_g_threshold", 6.0)
            if abs(curr_g) > g_lim:
                reward += cfg.get("overload_penalty", -1.0) * (abs(curr_g) - g_lim)

            # 4. Early Termination (Fail Fast)
            # Prevent "Stall Hell" where agent accumulates -2000 points over 2000 steps.
            # If flight envelope is excessively violated, kill episode.
            
            # Condition A: Deep Stall / Spin (AoA > 50 deg)
            if airborne and aoa_valid and abs(curr_aoa) > 50.0:
                 reward -= 50.0 # Fixed penalty instead of accumulation
                 terminated = True
                 status[3] = -1.0 # Fail code
            
            # Condition B: Inverted Flight at low alt (Roll > 135 deg while < 100m)
            elif airborne and truth.z < 100.0 and abs(curr_roll) > 135.0:
                 reward -= 50.0
                 terminated = True
                 status[3] = -1.0
                 
            # Condition C: Extreme Pitch (Cobra) > 85 deg
            elif airborne and abs(truth.pitch) > 85.0:
                 reward -= 50.0
                 terminated = True
                 status[3] = -1.0
            
            # Condition D: Gear Collapse (off-runway at high speed)
            # Do NOT index into obs["instruments"] for gear fields: the instrument vector is for
            # training observations and its layout changes over time (e.g. when adding EGI fields).
            # Use InstrumentState directly for gear damage/off-runway logic.
            if gear_collapsed:
                reward += cfg.get("gear_collapse_penalty", -500.0)
                terminated = True
                status[3] = -1.0
            elif preliftoff and (not on_runway_task):
                # Off-runway penalty (per step, during ground roll/rotation before liftoff).
                # Prefer geometry runway membership when available so apron/taxiway do not count as "on runway".
                reward += cfg.get("off_runway_penalty", -1.0)
                # Also penalize proportional to gear stress accumulation
                if gear_stress > 0.1:
                    reward += gear_stress * cfg.get("gear_stress_penalty", -10.0)
                # Fail-fast: leaving the runway at high speed is almost always unrecoverable for takeoff training.
                # Terminating early reduces huge negative tails (rollover) that destabilize value learning.
                off_runway_term_speed = float(cfg.get("off_runway_terminate_speed", 0.0))
                if off_runway_term_speed > 0.0 and float(truth.speed) >= off_runway_term_speed:
                    # Grace period (seconds) to avoid terminating on a single-step boundary crossing.
                    # Defaults to 0.0 for legacy behavior.
                    grace_s = float(cfg.get("off_runway_terminate_grace_s", 0.0))
                    dt = float(getattr(sim, "get_time_step", lambda: 0.05)())
                    dt = dt if dt > 1.0e-6 else 0.05
                    grace_steps = int(max(0.0, grace_s) / dt)
                    if int(getattr(self, "off_runway_steps", 0)) > grace_steps:
                        reward += float(cfg.get("off_runway_terminate_penalty", -200.0))
                        terminated = True
                        status[3] = -1.0
                
            # Roll Stability (Penalize extreme bank angles at low altitude)
            if truth.z < 100.0:
                reward += abs(curr_roll) * cfg.get("roll_stability_weight", 0.0)
                
            # 4. Command Adherence (Error Penalty)
            # Only if strictly requested (usually better to let Objectives handle final success)
            if cfg.get("heading_error_weight", 0.0) != 0.0:
                 tgt_hdg = self.mission_cmd.get("target_heading", 0.0)
                 # Angular difference
                 diff = abs(tgt_hdg - truth.heading)
                 if diff > 180: diff = 360 - diff
                 reward += diff * cfg.get("heading_error_weight")

            # Altitude/speed command tracking (airborne-only; realism-safe: targets are already in obs["mission"]).
            # These were present in scenario configs but previously not implemented, which can lead to weak
            # steady-state signals (e.g., the agent learns to "survive" but not to stabilize near the commanded
            # flight condition).
            if airborne:
                # Altitude error penalty (baro altitude vs mission target altitude)
                w_alt_err = float(cfg.get("altitude_error_weight", 0.0))
                if w_alt_err != 0.0:
                    alt_baro = float(inst[2])
                    min_alt = float(cfg.get("altitude_error_min_alt", 0.0))
                    if alt_baro >= min_alt:
                        tgt_alt = cfg.get("altitude_error_target", None)
                        if tgt_alt is None:
                            tgt_alt = self.mission_cmd.get("target_altitude", alt_baro)
                        try:
                            tgt_alt = float(tgt_alt)
                        except Exception:
                            tgt_alt = alt_baro
                        deadband = float(cfg.get("altitude_error_deadband_m", cfg.get("altitude_error_band_m", 0.0)))
                        norm = float(cfg.get("altitude_error_norm_m", 100.0))
                        if norm <= 1.0e-6:
                            norm = 100.0
                        p = float(cfg.get("altitude_error_power", 1.0))
                        if p < 1.0:
                            p = 1.0
                        if p > 8.0:
                            p = 8.0
                        err = abs(alt_baro - float(tgt_alt)) - max(0.0, deadband)
                        if err > 0.0:
                            x = err / norm
                            clip = float(cfg.get("altitude_error_clip", 0.0))
                            if clip > 0.0:
                                x = min(x, clip)
                            reward += w_alt_err * (x**p)

                # Speed error penalty (IAS vs mission target speed)
                w_spd_err = float(cfg.get("speed_error_weight", 0.0))
                if w_spd_err != 0.0:
                    min_ias = float(cfg.get("speed_error_min_ias", 0.0))
                    if float(curr_ias) >= min_ias:
                        tgt_spd = cfg.get("speed_error_target", None)
                        if tgt_spd is None:
                            tgt_spd = self.mission_cmd.get("target_speed", float(curr_ias))
                        try:
                            tgt_spd = float(tgt_spd)
                        except Exception:
                            tgt_spd = float(curr_ias)
                        deadband = float(cfg.get("speed_error_deadband", cfg.get("speed_error_band", 0.0)))
                        norm = float(cfg.get("speed_error_norm", 30.0))
                        if norm <= 1.0e-6:
                            norm = 30.0
                        p = float(cfg.get("speed_error_power", 1.0))
                        if p < 1.0:
                            p = 1.0
                        if p > 8.0:
                            p = 8.0
                        err = abs(float(curr_ias) - float(tgt_spd)) - max(0.0, deadband)
                        if err > 0.0:
                            x = err / norm
                            clip = float(cfg.get("speed_error_clip", 0.0))
                            if clip > 0.0:
                                x = min(x, clip)
                            reward += w_spd_err * (x**p)

                # Stability penalties (airborne-only). These encourage smooth, realistic flight by penalizing
                # large attitudes/rates and uncoordinated slip, without adding any privileged observations.
                w_roll = float(cfg.get("roll_abs_weight", 0.0))
                if w_roll != 0.0:
                    roll = float(inst[8])
                    dead = float(cfg.get("roll_abs_deadband_deg", 0.0))
                    norm = float(cfg.get("roll_abs_norm_deg", 30.0))
                    if norm <= 1.0e-6:
                        norm = 30.0
                    p = float(cfg.get("roll_abs_power", 1.0))
                    if p < 1.0:
                        p = 1.0
                    if p > 8.0:
                        p = 8.0
                    err = abs(roll) - max(0.0, dead)
                    if err > 0.0:
                        reward += w_roll * ((err / norm) ** p)

                w_pitch = float(cfg.get("pitch_abs_weight", 0.0))
                if w_pitch != 0.0:
                    pitch = float(inst[7])
                    dead = float(cfg.get("pitch_abs_deadband_deg", 0.0))
                    norm = float(cfg.get("pitch_abs_norm_deg", 20.0))
                    if norm <= 1.0e-6:
                        norm = 20.0
                    p = float(cfg.get("pitch_abs_power", 1.0))
                    if p < 1.0:
                        p = 1.0
                    if p > 8.0:
                        p = 8.0
                    err = abs(pitch) - max(0.0, dead)
                    if err > 0.0:
                        reward += w_pitch * ((err / norm) ** p)

                w_r = float(cfg.get("yaw_rate_abs_weight", 0.0))
                if w_r != 0.0:
                    r_deg_s = float(inst[14]) if len(inst) > 14 else 0.0
                    dead = float(cfg.get("yaw_rate_abs_deadband_deg_s", 0.0))
                    norm = float(cfg.get("yaw_rate_abs_norm_deg_s", 10.0))
                    if norm <= 1.0e-6:
                        norm = 10.0
                    p = float(cfg.get("yaw_rate_abs_power", 1.0))
                    if p < 1.0:
                        p = 1.0
                    if p > 8.0:
                        p = 8.0
                    err = abs(r_deg_s) - max(0.0, dead)
                    if err > 0.0:
                        reward += w_r * ((err / norm) ** p)

                w_beta = float(cfg.get("beta_abs_weight", 0.0))
                if w_beta != 0.0:
                    beta = float(inst[6]) if len(inst) > 6 else 0.0
                    dead = float(cfg.get("beta_abs_deadband_deg", 0.0))
                    norm = float(cfg.get("beta_abs_norm_deg", 10.0))
                    if norm <= 1.0e-6:
                        norm = 10.0
                    p = float(cfg.get("beta_abs_power", 1.0))
                    if p < 1.0:
                        p = 1.0
                    if p > 8.0:
                        p = 8.0
                    err = abs(beta) - max(0.0, dead)
                    if err > 0.0:
                        reward += w_beta * ((err / norm) ** p)

                w_g = float(cfg.get("g_deviation_weight", 0.0))
                if w_g != 0.0:
                    g_load = float(inst[10])
                    dead = float(cfg.get("g_deviation_deadband", 0.0))
                    norm = float(cfg.get("g_deviation_norm", 0.5))
                    if norm <= 1.0e-6:
                        norm = 0.5
                    p = float(cfg.get("g_deviation_power", 1.0))
                    if p < 1.0:
                        p = 1.0
                    if p > 8.0:
                        p = 8.0
                    err = abs(g_load - 1.0) - max(0.0, dead)
                    if err > 0.0:
                        reward += w_g * ((err / norm) ** p)
            
            # 6. Raw Speed Reward (Encourage Velocity)
            reward += truth.speed * cfg.get("speed_reward_weight", 0.0)

            # 7. Runway Alignment Reward (Positive reinforcement for staying aligned)
            # 1.0 if perfectly aligned, 0.0 if 90 deg off, -1.0 if opposite
            # diff is absolute error [0, 180] from lines 643-644
            #
            # Realism note:
            # - The agent does NOT observe runway geometry (heading/cross-track) directly.
            # - We allow reward shaping to reflect a real-world training objective: keep the aircraft near the runway
            #   centerline during takeoff roll. This is a continuous penalty (not a hard "on/off runway" threshold),
            #   to avoid edge-hugging policies that look unrealistic yet stay within runway bounds.
            if (
                preliftoff
                and on_runway_task
                and runway_cross_m is not None
                and runway_wid_m is not None
            ):
                half_w = 0.5 * float(runway_wid_m)
                if half_w > 1.0e-6:
                    frac = abs(float(runway_cross_m)) / half_w
                    # Allow slight overshoot; off-runway termination handles true departures.
                    if frac > 2.0:
                        frac = 2.0
                    min_ias = float(cfg.get("runway_centerline_penalty_min_ias", 0.0))
                    max_ias = float(cfg.get("runway_centerline_penalty_max_ias", 0.0))
                    scale = 1.0
                    if max_ias > min_ias + 1.0e-6:
                        scale = (float(curr_ias) - min_ias) / (max_ias - min_ias)
                        if scale < 0.0:
                            scale = 0.0
                        if scale > 1.0:
                            scale = 1.0

                    # Continuous centerline penalty (no observation leakage; geometry is teacher-only).
                    # Meter-based shaping (recommended):
                    # - direct interpretability (e.g. "5m deviation costs ~1 per step")
                    # - avoids "safe region" exploits by being strictly increasing from 0
                    w_center_m = float(cfg.get("runway_centerline_m_penalty_weight", 0.0))
                    if w_center_m != 0.0:
                        dead_m = float(cfg.get("runway_centerline_m_deadband_m", 0.0))
                        if dead_m < 0.0:
                            dead_m = 0.0
                        norm_m = float(cfg.get("runway_centerline_m_norm_m", 5.0))
                        if norm_m <= 1.0e-6:
                            norm_m = 5.0
                        p_m = float(cfg.get("runway_centerline_m_power", 2.0))
                        if p_m < 1.0:
                            p_m = 1.0
                        if p_m > 8.0:
                            p_m = 8.0
                        err_m = abs(float(runway_cross_m)) - dead_m
                        if err_m > 0.0:
                            x_m = err_m / norm_m
                            clip_m = float(cfg.get("runway_centerline_m_clip", 0.0))
                            if clip_m > 0.0:
                                x_m = min(x_m, clip_m)
                            reward += w_center_m * (x_m**p_m) * scale

                    w_center = float(cfg.get("runway_centerline_penalty_weight", 0.0))
                    if w_center != 0.0:
                        safe_frac = float(cfg.get("runway_centerline_safe_frac", 0.0))
                        if safe_frac < 0.0:
                            safe_frac = 0.0
                        if safe_frac > 0.99:
                            safe_frac = 0.99
                        x = max(0.0, frac - safe_frac) / max(1.0 - safe_frac, 1.0e-6)
                        p = float(cfg.get("runway_centerline_penalty_power", 2.0))
                        if p < 1.0:
                            p = 1.0
                        if p > 8.0:
                            p = 8.0
                        reward += w_center * (x**p) * scale

                    # Optional centerline barrier: smoothly increases without any "safe region".
                    # This makes edge-hugging strategies strictly worse, while keeping the observation
                    # space realism intact (no privileged geometry is exposed to the agent).
                    w_bar = float(cfg.get("runway_centerline_barrier_weight", 0.0))
                    if w_bar != 0.0:
                        clip_frac = float(cfg.get("runway_centerline_barrier_clip_frac", 0.995))
                        if clip_frac <= 0.0:
                            clip_frac = 0.995
                        if clip_frac >= 0.999999:
                            clip_frac = 0.999999
                        frac_c = min(max(frac, 0.0), clip_frac)
                        barrier = -math.log(max(1.0e-6, 1.0 - frac_c))
                        reward += w_bar * barrier * scale

            if cfg.get("alignment_reward_weight", 0.0) != 0.0:
                w = float(cfg.get("alignment_reward_weight"))
                # On the runway, we should NOT force alignment to the mission heading (that can conflict with runway
                # direction and encourages unrealistic pivoting/braking). Instead, use the ILS localizer deviation
                # when available to reward staying on the runway centerline.
                if on_runway_task and preliftoff:
                    try:
                        ils_valid = float(inst[-4])
                        loc_dev = float(inst[-3])
                    except Exception:
                        ils_valid = 0.0
                        loc_dev = 0.0
                    if ils_valid > 0.5:
                        # loc_dev is normalized [-1,1]; reward is [0,1] when centered.
                        reward += (1.0 - min(abs(loc_dev), 1.0)) * w
                else:
                    # Airborne: command adherence can follow mission heading, but not immediately after liftoff.
                    # Realistic departure keeps runway heading until a safe altitude.
                    min_alt_for_cmd_align = float(cfg.get("mission_alignment_min_alt", 120.0))
                    if truth.z >= min_alt_for_cmd_align:
                        tgt_hdg = self.mission_cmd.get("target_heading", 0.0)
                        diff = abs(tgt_hdg - truth.heading)
                        if diff > 180:
                            diff = 360 - diff
                        align_factor = math.cos(math.radians(diff))
                        if align_factor > 0:
                            reward += align_factor * w

        # Update Prev State
        self.prev_alt = truth.z
        self.prev_speed = curr_ias

        # 4.x Waypoint Navigation (Cruise): reach a sequence of mission waypoints.
        # Note: This is a mission-level task (reach waypoints), not "fly a straight line".
        if not terminated:
            try:
                cmd_code = int(self.mission_cmd.get("command_code", 0))
            except Exception:
                cmd_code = 0
            if cmd_code == 3 and self.waypoints:
                idx = int(getattr(self, "waypoint_idx", 0))
                if idx < 0:
                    idx = 0
                n = int(len(self.waypoints))
                if idx < n:
                    wp = self.waypoints[idx]
                    dx = float(wp.get("x", 0.0)) - float(getattr(truth, "x", 0.0))
                    dy = float(wp.get("y", 0.0)) - float(getattr(truth, "y", 0.0))
                    dist_m = float(math.sqrt(dx * dx + dy * dy))

                    # Use status slots for quick debugging in logs/viz tools.
                    status[0] = dist_m
                    status[1] = float(idx)
                    status[2] = float(n)

                    w_prog = float(cfg.get("waypoint_progress_weight", 0.0))
                    if w_prog != 0.0 and self._waypoint_prev_dist_m is not None:
                        reward += (float(self._waypoint_prev_dist_m) - dist_m) * w_prog
                    self._waypoint_prev_dist_m = dist_m

                    w_dist = float(cfg.get("waypoint_distance_weight", 0.0))
                    if w_dist != 0.0:
                        reward += dist_m * w_dist

                    # Arrival / sequencing check.
                    # Cruise uses a more realistic fly-by LNAV style by default: intermediate waypoints
                    # are sequenced with turn anticipation based on speed + bank limit.
                    try:
                        rad = float(wp.get("radius_m", cfg.get("waypoint_radius_m", 500.0)))
                    except Exception:
                        rad = float(cfg.get("waypoint_radius_m", 500.0))
                    rad = max(1.0, float(rad))

                    mode = str(self.mission_cmd.get("waypoint_mode", "flyby")).strip().lower()

                    # Compute leg-relative metrics for fly-by sequencing.
                    arrived = False
                    if mode == "flyby" and idx < (n - 1):
                        # Leg start: origin for first leg, otherwise previous waypoint.
                        if idx <= 0:
                            sx = float(getattr(self, "_waypoint_leg_origin_x", getattr(truth, "x", 0.0)))
                            sy = float(getattr(self, "_waypoint_leg_origin_y", getattr(truth, "y", 0.0)))
                        else:
                            prev = self.waypoints[idx - 1]
                            sx = float(prev.get("x", 0.0))
                            sy = float(prev.get("y", 0.0))
                        ex = float(wp.get("x", 0.0))
                        ey = float(wp.get("y", 0.0))
                        lx = ex - sx
                        ly = ey - sy
                        leg_len = float(math.hypot(lx, ly))
                        if leg_len > 1.0e-6:
                            ux = lx / leg_len
                            uy = ly / leg_len
                            px = float(getattr(truth, "x", 0.0)) - sx
                            py = float(getattr(truth, "y", 0.0)) - sy
                            along = float(px * ux + py * uy)
                            # XTK (right of track positive)
                            xtk = float(px * uy - py * ux)
                            dtg = float(leg_len - along)
                            dtg = max(0.0, dtg)

                            # Turn anticipation lead distance (simple constant-radius geometry).
                            next_wp = self.waypoints[idx + 1]
                            nx = float(next_wp.get("x", 0.0)) - ex
                            ny = float(next_wp.get("y", 0.0)) - ey
                            cur_trk = float(self._bearing_to_deg(lx, ly))
                            next_trk = float(self._bearing_to_deg(nx, ny)) if (nx * nx + ny * ny) > 1.0e-9 else cur_trk
                            delta = (next_trk - cur_trk + 180.0) % 360.0 - 180.0
                            delta = abs(float(delta))
                            bank_lim = float(self.mission_cmd.get("lnav_bank_limit_deg", 30.0))
                            bank_lim = float(np.clip(bank_lim, 5.0, 70.0))
                            bank_rad = math.radians(bank_lim)
                            tanb = math.tan(bank_rad)
                            if abs(tanb) < 1.0e-6:
                                lead = 0.0
                            else:
                                v = max(30.0, float(curr_ias))
                                r_turn = (v * v) / (9.80665 * abs(tanb))
                                lead = float(r_turn * math.tan(math.radians(delta) * 0.5))
                                lead = max(0.0, lead)

                            # Sequence when close enough to the waypoint along-track (dtg <= lead) and
                            # sufficiently near the active leg laterally (|xtk| <= rad).
                            if abs(xtk) <= rad and dtg <= max(lead, 0.0):
                                arrived = True
                    else:
                        # Fly-over: require entering a radial acceptance radius around the fix.
                        arrived = bool(dist_m <= rad)

                    if arrived:
                        reward += float(cfg.get("waypoint_reached_bonus", 0.0))
                        self.waypoint_idx = idx + 1
                        status[1] = float(self.waypoint_idx)
                        self._waypoint_prev_dist_m = None
                        if self.waypoint_idx >= n:
                            reward += float(cfg.get("waypoint_mission_success_bonus", 1000.0))
                            terminated = True
                            status[3] = 1.0
            
        # 5. Objectives (Binary Success)
        # Only evaluate success conditions if we did not already terminate due to a failure mode.
        if not terminated:
            for obj in rules:
                if obj["type"] == "conditional":
                    conds_met = True
                    for i, cond in enumerate(obj.get("conditions", [])):
                        prop = cond.get("property")
                        op = cond.get("op", ">=")

                        tgt = cond.get("value", 0.0)

                        # Optional dynamic target resolution (opt-in).
                        # If a scenario wants a condition to follow the randomized mission command, it can
                        # set `"value": "CMD_ALT"` / `"CMD_SPEED"` / `"CMD_HDG"` (optionally with `"scale": ...`).
                        if isinstance(tgt, str):
                            key = tgt.strip().upper()
                            if key in ("CMD_ALT", "CMD_ALTITUDE"):
                                scale = float(cond.get("scale", 0.95))
                                tgt = float(self.mission_cmd.get("target_altitude", 0.0)) * scale
                            elif key in ("CMD_SPEED",):
                                scale = float(cond.get("scale", 0.90))
                                tgt = float(self.mission_cmd.get("target_speed", 0.0)) * scale
                            elif key in ("CMD_HDG", "CMD_HEADING"):
                                tgt = float(self.mission_cmd.get("target_heading", 0.0))

                        val = 0.0
                        if prop == "altitude":
                            val = float(truth.z)
                        elif prop == "speed":
                            val = float(curr_ias)

                        # Status for TensorBoard (log up to first 3 values; slot 3 is reserved for terminal flag).
                        if i < 3:
                            status[i] = val

                        # Check
                        if op == ">=" and val < tgt:
                            conds_met = False
                        elif op == ">" and val <= tgt:
                            conds_met = False
                        elif op == "<=" and val > tgt:
                            conds_met = False
                        elif op == "<" and val >= tgt:
                            conds_met = False

                    if conds_met:
                        reward += obj.get("reward", 1000.0)
                        terminated = True
                        # Convention: status[3] is a terminal outcome flag.
                        # -1.0 = failure (set by fail-fast blocks above)
                        # +1.0 = success
                        status[3] = 1.0
                    
        return reward, terminated, truncated, status
