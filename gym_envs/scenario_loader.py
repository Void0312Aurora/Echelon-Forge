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

            if "wind_speed_range" in env_rand:
                r = env_rand["wind_speed_range"]
                wind_speed = float(self.rng.uniform(r[0], r[1]))
            if "wind_dir_from_range" in env_rand:
                r = env_rand["wind_dir_from_range"]
                wind_dir_from = float(self.rng.uniform(r[0], r[1]))
            if "wind_shear_range" in env_rand:
                r = env_rand["wind_shear_range"]
                wind_shear = float(self.rng.uniform(r[0], r[1]))

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
             # Use IAS for speed shaping/objectives (robust under randomized wind).
             # Ground speed is still used for stationary detection.
             try:
                 inst0 = self.sim.get_instrument_state(self.agent_id)
                 self.prev_speed = float(inst0.ias)
             except Exception:
                 self.prev_speed = truth.speed

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
                length = float(zone.get("length", 0.0))
                heading = float(zone.get("heading", 0.0)) % 360.0
            except Exception:
                continue

            if length <= 1.0:
                continue

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
                    "elev_m": elev_m,
                    "glide_slope_deg": glide_slope_deg,
                    "loc_max_deg": max(0.1, loc_max_deg),
                    "gs_max_deg": max(0.1, gs_max_deg),
                    "range_m": max(100.0, range_m),
                }
            )

        return beacons

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

        dx = x_m - float(best["cx"])
        dy = y_m - float(best["cy"])
        along = dx * fwd_x + dy * fwd_y
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
        
        reward = 0.0
        terminated = False
        truncated = (steps >= max_steps)
        status = [0.0]*4
        
        # 1. Base Survival & Crash
        if truth.health <= 0:
            reward += cfg.get("crash_penalty", -1000.0)
            terminated = True
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
                    reward += max(0.0, min(float(inst[7]), rot_pitch_cap)) * rotation_weight
            
            # Gear Bonus (One-time)
            # If above 50m and gear is up (<0.1), and haven't awarded yet
            if truth.z > 50.0 and curr_gear < 0.1 and not self.gear_bonus_awarded:
                reward += cfg.get("gear_up_bonus", 0.0)
                self.gear_bonus_awarded = True
                
            # 3. Safety Constraints (Penalties)
            # Stall
            stall_lim = cfg.get("stall_aoa_threshold", 15.0)
            if abs(curr_aoa) > stall_lim:
                reward += cfg.get("stall_penalty", -1.0) * (abs(curr_aoa) - stall_lim)
                
            # Overload
            g_lim = cfg.get("overload_g_threshold", 6.0)
            if abs(curr_g) > g_lim:
                reward += cfg.get("overload_penalty", -1.0) * (abs(curr_g) - g_lim)

            # 4. Early Termination (Fail Fast)
            # Prevent "Stall Hell" where agent accumulates -2000 points over 2000 steps.
            # If flight envelope is excessively violated, kill episode.
            
            # Condition A: Deep Stall / Spin (AoA > 50 deg)
            if abs(curr_aoa) > 50.0:
                 reward -= 50.0 # Fixed penalty instead of accumulation
                 terminated = True
                 status[3] = -1.0 # Fail code
            
            # Condition B: Inverted Flight at low alt (Roll > 135 deg while < 100m)
            elif truth.z < 100.0 and abs(curr_roll) > 135.0:
                 reward -= 50.0
                 terminated = True
                 status[3] = -1.0
                 
            # Condition C: Extreme Pitch (Cobra) > 85 deg
            elif abs(truth.pitch) > 85.0:
                 reward -= 50.0
                 terminated = True
                 status[3] = -1.0
            
            # Condition D: Gear Collapse (off-runway at high speed)
            # Do NOT index into obs["instruments"] for gear fields: the instrument vector is for
            # training observations and its layout changes over time (e.g. when adding EGI fields).
            # Use InstrumentState directly for gear damage/off-runway logic.
            try:
                inst_obj = sim.get_instrument_state(self.agent_id)
            except Exception:
                inst_obj = None

            if inst_obj is not None:
                gear_collapsed = bool(getattr(inst_obj, "gear_collapsed", False))
                on_runway = bool(getattr(inst_obj, "on_runway", True))
                gear_stress = float(getattr(inst_obj, "gear_stress", 0.0))
            else:
                gear_collapsed = False
                on_runway = True
                gear_stress = 0.0
            
            if gear_collapsed:
                reward += cfg.get("gear_collapse_penalty", -500.0)
                terminated = True
                status[3] = -1.0
            elif not on_runway and truth.z < 10.0:
                # Off-runway penalty (per step, only when on ground)
                reward += cfg.get("off_runway_penalty", -1.0)
                # Also penalize proportional to gear stress accumulation
                if gear_stress > 0.1:
                    reward += gear_stress * cfg.get("gear_stress_penalty", -10.0)
                
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
            
            # 6. Raw Speed Reward (Encourage Velocity)
            reward += truth.speed * cfg.get("speed_reward_weight", 0.0)

            # 7. Runway Alignment Reward (Positive reinforcement for staying aligned)
            # 1.0 if perfectly aligned, 0.0 if 90 deg off, -1.0 if opposite
            # diff is absolute error [0, 180] from lines 643-644
            if cfg.get("alignment_reward_weight", 0.0) != 0.0:
                 tgt_hdg = self.mission_cmd.get("target_heading", 0.0)
                 diff = abs(tgt_hdg - truth.heading)
                 if diff > 180: diff = 360 - diff
                 # Cosine similarity-ish
                 align_factor = math.cos(math.radians(diff))
                 # Only reward if strictly positive alignment (within +/- 90)
                 if align_factor > 0:
                      reward += align_factor * cfg.get("alignment_reward_weight")

        # Update Prev State
        self.prev_alt = truth.z
        self.prev_speed = curr_ias
            
        # 5. Objectives (Binary Success)
        for obj in rules:
            if obj["type"] == "conditional":
                conds_met = True
                for i, cond in enumerate(obj.get("conditions", [])):
                    prop = cond.get("property")
                    op = cond.get("op", ">=")
                    
                    # DYNAMIC TARGET RESOLUTION
                    # Instead of using static 'value' from JSON, check if we should use mission_cmd
                    # If value is string 'CMD_ALT', 'CMD_SPEED', etc., resolve it
                    # OR, for this specific scenario, just override for known properties
                    
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
                    if prop == "altitude": val = truth.z
                    elif prop == "speed": val = curr_ias
                    
                    # Check
                    if op == ">=" and val < tgt: conds_met = False
                    elif op == ">" and val <= tgt: conds_met = False
                    elif op == "<=" and val > tgt: conds_met = False
                    elif op == "<" and val >= tgt: conds_met = False
                    
                    # Status for TensorBoard
                    if i < 4: status[i] = val # Log current value
                    
                if conds_met:
                    reward += obj.get("reward", 1000.0)
                    terminated = True
                    
        return reward, terminated, truncated, status
