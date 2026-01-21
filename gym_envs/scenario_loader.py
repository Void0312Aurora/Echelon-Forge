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
        return self.agent_id

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
        return self.scenario_data.get("meta", {}).get("max_steps", 1000)

    def get_rewards_config(self):
        return self.scenario_data.get("rewards", {})

    def get_objectives(self):
        return self.scenario_data.get("objectives", [])
    
    def get_entity_id(self, name):
        return self.entities.get(name)

    def update_behaviors(self, sim_time):
        pass

    def compute_full_step(self, obs, sim, steps, max_steps):
        rules = self.scenario_data.get("objectives", [])
        cfg = self.scenario_data.get("rewards", {})
        
        # Get Truth State for Scoring
        truth = sim.get_agent_observation(self.agent_id)
        
        reward = 0.0
        terminated = False
        truncated = (steps >= max_steps)
        status = [0.0]*4
        
        if truth.health <= 0:
            reward += cfg.get("crash_penalty", -1000.0)
            terminated = True
        else:
            reward += cfg.get("survival", 0.01)
            
        for obj in rules:
            if obj["type"] == "capture_zone":
                target_id = self.entities.get(obj.get("target"))
                if target_id is not None:
                     t_pos = sim.get_unit_position(target_id)
                     # Truth Position
                     dist = math.sqrt((t_pos[0]-truth.x)**2 + (t_pos[1]-truth.y)**2 + (t_pos[2]-truth.z)**2)
                     
                     dist_cfg = cfg.get("distance_to_target", {})
                     if dist_cfg:
                         reward += dist * dist_cfg.get("weight", -0.001)
                         
                     if dist < obj.get("radius", 1000.0):
                         self.captured_time += sim.get_time_step()
                         reward += 1.0
                         if self.captured_time >= obj.get("duration", 10.0):
                             reward += obj.get("reward", 1000.0)
                             terminated = True
                             
                     status[0] = dist
                     status[1] = obj.get("duration", 10.0) - self.captured_time
                     
            elif obj["type"] == "conditional":
                conds_met = True
                for i, cond in enumerate(obj.get("conditions", [])):
                    prop = cond.get("property")
                    op = cond.get("op", ">=")
                    tgt = cond.get("value", 0.0)
                    
                    # Fetch property from Truth State
                    val = 0.0
                    if prop == "altitude": val = truth.z
                    elif prop == "speed": val = truth.speed
                    elif prop == "heading": val = truth.heading
                    elif prop == "pitch": val = truth.pitch
                    elif prop == "roll": val = truth.roll
                    elif prop == "health": val = truth.health
                    elif prop == "missiles": val = float(truth.missiles_remaining)
                    # Add more mappings as needed
                    
                    # Shaping
                    if op in [">=", ">"] and tgt != 0:
                        reward += (val / tgt) * 0.0005
                        
                    # Check
                    if op == ">=" and val < tgt: conds_met = False
                    elif op == ">" and val <= tgt: conds_met = False
                    elif op == "<=" and val > tgt: conds_met = False
                    elif op == "<" and val >= tgt: conds_met = False
                    
                    # Status
                    if i < 4: status[i] = tgt - val
                    
                if conds_met:
                    reward += obj.get("reward", 1000.0)
                    terminated = True
                    
        return reward, terminated, truncated, status
