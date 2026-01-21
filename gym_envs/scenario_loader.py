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
        
    def load_scenario(self, json_path):
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
            if "time_step" in env_cfg:
                self.sim.set_time_step(env_cfg["time_step"])
            
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
        self.sim.reset(42)  # Ensure clean slate before spawning
        
        for ent_cfg in self.scenario_data.get("entities", []):
            side_map = {
                "Blue": ef_py.Side.Blue,
                "Red": ef_py.Side.Red,
                "Neutral": ef_py.Side.Neutral
            }
            side = side_map.get(ent_cfg["side"], ef_py.Side.Neutral)
            
            p = ent_cfg["pos"]
            v = ent_cfg["vel"]
            
            eid = self.sim.spawn_unit(
                side,
                ent_cfg["type"],
                float(p[0]), float(p[1]), float(p[2]),
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
        
        # Randomize Mission if ranges provided
        self._randomize_mission()
        
        # Initialize prev state if agent exists
        if self.agent_id is not None:
             truth = self.sim.get_agent_observation(self.agent_id)
             self.prev_alt = truth.z
             self.prev_speed = truth.speed
             
        return self.agent_id

    def _randomize_mission(self):
        """Randomize mission parameters if ranges are specified in config."""
        import random
        base_cmd = self.scenario_data.get("mission_command", {})
        
        # Check for randomization config
        rand_cfg = base_cmd.get("randomization", {})
        
        # 1. Heading
        if "heading_range" in rand_cfg:
            r = rand_cfg["heading_range"]
            self.mission_cmd["target_heading"] = random.uniform(r[0], r[1])
        
        # 2. Altitude
        if "altitude_range" in rand_cfg:
            r = rand_cfg["altitude_range"]
            self.mission_cmd["target_altitude"] = random.uniform(r[0], r[1])
            
        # 3. Speed
        if "speed_range" in rand_cfg:
            r = rand_cfg["speed_range"]
            self.mission_cmd["target_speed"] = random.uniform(r[0], r[1])
        
        # Ensure values are floats
        self.mission_cmd["target_heading"] = float(self.mission_cmd.get("target_heading", 0.0))
        self.mission_cmd["target_altitude"] = float(self.mission_cmd.get("target_altitude", 0.0))
        self.mission_cmd["target_speed"] = float(self.mission_cmd.get("target_speed", 0.0))
        self.mission_cmd["command_code"] = int(self.mission_cmd.get("command_code", 0))

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
            if "zones" in prefab and "environment" in self.scenario_data:
                current_zones = self.scenario_data["environment"].get("zones", [])
                current_zones.extend(prefab["zones"])
                self.scenario_data["environment"]["zones"] = current_zones
                
            # Merge Entities
            if "entities" in prefab:
                current_ents = self.scenario_data.get("entities", [])
                current_ents.extend(prefab["entities"])
                self.scenario_data["entities"] = current_ents

    def get_max_steps(self):
        return self.scenario_data.get("meta", {}).get("max_steps", 2000) # Default increased to 2000

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
            d_alt = truth.z - self.prev_alt
            if d_alt > 0: # Only reward climbing, don't penalize sinking heavily (gravity does that via crash)
                reward += d_alt * cfg.get("altitude_progress_weight", 0.0)
            elif truth.z < 10.0 and d_alt < -1.0: # Penalize rapid descent near ground
                 reward += d_alt * 0.1 
                 
            # Speed Progress (Until target speed)
            tgt_spd = self.mission_cmd.get("target_speed", 180.0)
            if truth.speed < tgt_spd:
                d_spd = truth.speed - self.prev_speed
                if d_spd > 0:
                    reward += d_spd * cfg.get("speed_progress_weight", 0.0)
            
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
        
        # Update Prev State
        self.prev_alt = truth.z
        self.prev_speed = truth.speed
            
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
                    
                    # Override with randomized mission command if property matches
                    if prop == "altitude" and "target_altitude" in self.mission_cmd:
                        # Allow some tolerance, e.g. 90% of target alt
                         tgt = self.mission_cmd["target_altitude"] * 0.95 
                    elif prop == "speed" and "target_speed" in self.mission_cmd:
                         tgt = self.mission_cmd["target_speed"] * 0.90
                    
                    val = 0.0
                    if prop == "altitude": val = truth.z
                    elif prop == "speed": val = truth.speed
                    
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
