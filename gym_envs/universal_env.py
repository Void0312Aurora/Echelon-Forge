import sys
import os
import math
import gymnasium as gym
import numpy as np
from gymnasium import spaces

# Build path setup
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../build")))
import ef_py
from gym_envs.scenario_loader import ScenarioLoader

class UniversalEnv(gym.Env):
    """
    Universal Environment for Flight Simulation.
    
    Action Space (17 dimensions total):
    - [0-3] Primary Controls: stick_pitch, stick_roll, rudder, throttle (continuous)
    - [4-6] Secondary Controls: gear, flaps, speedbrake (continuous 0-1)
    - [7-8] Brakes: brake_left, brake_right (binary 0/1)
    - [9-12] Sensors: radar_active (binary), radar_az, radar_el, tms_up (binary)
    - [13-16] Weapons: master_arm (binary), fire_weapon (binary), fire_gun (binary), weapon_select (discrete)
    
    Observation Space: Dict with instruments, contacts, rwr, mission
    """
    metadata = {"render_modes": ["human"], "render_fps": 60}

    def __init__(self, scenario_path, render_mode=None):
        super().__init__()
        self.render_mode = render_mode
        self.scenario_path = scenario_path
        
        # Initialize Core
        self.sim = ef_py.SimulationKernel()
        # Load DB
        db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../examples/config/database"))
        self.sim.load_database(db_path)
        
        self.loader = ScenarioLoader(self.sim)
        
        # Action Space: Full Digital Pilot Standard
        # 17 dimensions to cover all act.md operations
        # Layout:
        # [0] stick_pitch    [-1, 1]
        # [1] stick_roll     [-1, 1]
        # [2] rudder         [-1, 1]
        # [3] throttle       [0, 1]
        # [4] gear           [0, 1]
        # [5] flaps          [0, 1]
        # [6] speedbrake     [0, 1]
        # [7] brake_left     [0, 1] (treat as continuous, threshold at 0.5)
        # [8] brake_right    [0, 1]
        # [9] radar_active   [0, 1]
        # [10] radar_az      [-1, 1] (normalized)
        # [11] radar_el      [-1, 1] (normalized)
        # [12] tms_up        [0, 1]
        # [13] master_arm    [0, 1]
        # [14] fire_weapon   [0, 1]
        # [15] fire_gun      [0, 1]
        # [16] weapon_select [0, 1] (normalized, map to int 0-7)
        
        self.action_space = spaces.Box(
            low=np.array([-1.0, -1.0, -1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, -1.0, -1.0, 0.0, 0.0, 0.0, 0.0, 0.0], dtype=np.float32),
            high=np.array([1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0], dtype=np.float32),
            dtype=np.float32
        )
        
        # Observation Space
        self.max_contacts = 10
        self.max_rwr = 4
        
        # Instrument State Size: see _get_obs
        self.obs_size = 24 
        
        self.observation_space = spaces.Dict({
            "instruments": spaces.Box(low=-np.inf, high=np.inf, shape=(self.obs_size,), dtype=np.float32),
            "contacts": spaces.Box(low=-np.inf, high=np.inf, shape=(self.max_contacts, 5), dtype=np.float32),
            "rwr": spaces.Box(low=-np.inf, high=np.inf, shape=(self.max_rwr, 4), dtype=np.float32),
            "mission": spaces.Box(low=-np.inf, high=np.inf, shape=(4,), dtype=np.float32)
        })
        
        self.agent_id = None
        self.steps = 0
        self.max_steps = 1000
        
    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        # Note: Loader now handles sim.reset() internally when loading to ensure sync
        self.agent_id = self.loader.load_scenario(self.scenario_path)
        self.max_steps = self.loader.get_max_steps()
        
        if self.agent_id is None:
            raise ValueError("Scenario must define at least one entity with 'is_agent': true")
            
        self.steps = 0
        return self._get_obs(), {}
        
    def step(self, action):
        self.steps += 1
        
        # 1. Apply Action (Full Digital Pilot)
        pilot_act = ef_py.PilotAction()
        pilot_act.active = True
        
        # Primary Controls
        pilot_act.stick_pitch = float(action[0])
        pilot_act.stick_roll = float(action[1])
        pilot_act.rudder = float(action[2])
        pilot_act.throttle = float(action[3])
        
        # Secondary Controls
        pilot_act.gear_handle = float(action[4])
        pilot_act.flaps = float(action[5])
        pilot_act.speedbrake = float(action[6])
        pilot_act.brake_left = action[7] > 0.5
        pilot_act.brake_right = action[8] > 0.5
        
        # Sensors
        pilot_act.radar_active = action[9] > 0.5
        pilot_act.radar_scan_az = float(action[10]) * 60.0  # Map to degrees
        pilot_act.radar_scan_el = float(action[11]) * 30.0  # Map to degrees
        pilot_act.tms_up = action[12] > 0.5
        
        # Weapons
        pilot_act.master_arm = action[13] > 0.5
        pilot_act.fire_weapon = action[14] > 0.5
        pilot_act.fire_gun = action[15] > 0.5
        pilot_act.weapon_select_id = int(action[16] * 7)  # Map to 0-7
        
        # Countermeasures (not in action space yet, default off)
        pilot_act.program_chaff = False
        pilot_act.program_flare = False
        pilot_act.jettison_emergency = False
        
        self.sim.set_pilot_action(self.agent_id, pilot_act)
        
        # 2. Step Sim
        self.sim.step()
        self.loader.update_behaviors(self.steps * self.sim.get_time_step())
        
        # 3. Get Observation
        obs = self._get_obs()
        
        # 4. Compute Reward & Done (Logic delegated to Loader/Config)
        reward, terminated, truncated, mission_status = self.loader.compute_full_step(
            obs, self.sim, self.steps, self.max_steps
        )
        
        # Update observable mission status
        obs["mission"] = np.array(mission_status, dtype=np.float32)

        return obs, reward, terminated, truncated, {}
        
    def _get_obs(self):
        # 1. Instruments
        inst = self.sim.get_instrument_state(self.agent_id)
        
        inst_vec = np.array([
            inst.ias, inst.mach, inst.alt_baro, inst.alt_radar, inst.vvi,
            inst.aoa, inst.beta, inst.pitch, inst.roll, inst.heading,
            inst.g_load, inst.g_load_axial,
            inst.p, inst.q, inst.r,
            inst.engine_rpm, inst.fuel_internal + inst.fuel_external, inst.fuel_flow,
            inst.gear_pos, inst.flaps_pos, inst.speedbrake_pos,
            inst.cmd_heading, inst.cmd_alt, inst.cmd_speed
        ], dtype=np.float32)
        
        # 2. Contacts (Via Truth for now, simulating Sensor Fusion)
        raw_truth = self.sim.get_agent_observation(self.agent_id)
        
        contacts = np.zeros((self.max_contacts, 5), dtype=np.float32)
        for i, t in enumerate(raw_truth.contacts):
            if i >= self.max_contacts: break
            contacts[i] = [t.range, t.azimuth, t.elevation, t.closing_speed, t.time_since_update]
            
        rwr = np.zeros((self.max_rwr, 4), dtype=np.float32)
        for i, w in enumerate(raw_truth.rwr_warnings):
            if i >= self.max_rwr: break
            rwr[i] = [w.bearing, w.signal_strength, 1.0 if w.is_lock else 0.0, 1.0 if w.is_launch else 0.0]
            
        return {
            "instruments": inst_vec,
            "contacts": contacts,
            "rwr": rwr,
            "mission": np.zeros(4, dtype=np.float32)
        }
