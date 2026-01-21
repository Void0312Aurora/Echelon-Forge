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
        
        # Action Space: Digital Pilot Standard (Pitch, Roll, Rudder, Throttle)
        # Using continuous space for main controls. Switches can be added later or mapped.
        self.action_space = spaces.Box(
            low=np.array([-1.0, -1.0, -1.0, 0.0], dtype=np.float32),
            high=np.array([1.0, 1.0, 1.0, 1.0], dtype=np.float32),
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
        
        # 1. Apply Action (Digital Pilot)
        pilot_act = ef_py.PilotAction()
        pilot_act.active = True
        pilot_act.stick_pitch = float(action[0])
        pilot_act.stick_roll = float(action[1])
        pilot_act.rudder = float(action[2])
        pilot_act.throttle = float(action[3])
        
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
