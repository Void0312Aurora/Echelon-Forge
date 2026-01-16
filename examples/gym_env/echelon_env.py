import gymnasium as gym
from gymnasium import spaces
import numpy as np
import ef_py
import sys
import os

class EchelonForgeEnv(gym.Env):
    """
    Custom Environment that follows gym interface
    Represents a 1v1 Air-to-Air engagement.
    """
    metadata = {'render.modes': ['human']}

    def __init__(self):
        super(EchelonForgeEnv, self).__init__()
        
        # Initialize Simulation Kernel
        self.kernel = ef_py.SimulationKernel()
        self.kernel.reset(42)
        
        # Action Space: Continuous
        # 0: Desired Heading (0-360) -> Simplified: -1 to 1 mapped to turn rate? 
        # For simplicity, let's make it Absolute High Level Command first, as per Phase 3.
        # [Target Heading (0-360), Target Speed (Min-Max), Target Altitude (0-15k), Fire (Boolean)]
        # However, RL agents learn better with normalized inputs/outputs (-1 to 1).
        
        # Let's try "Rate Control" or "Delta Control"
        # 0: Turn Rate (-1=Left Max, +1=Right Max)
        # 1: Speed Change (-1=Decel Max, +1=Accel Max)
        # 2: Climb Rate (-1=Dive Max, +1=Climb Max)
        # 3: Fire Trigger (>0.5 = Fire)
        self.action_space = spaces.Box(low=np.array([-1, -1, -1, 0]), 
                                       high=np.array([1, 1, 1, 1]), dtype=np.float32)

        # Observation Space: Relative State
        # [Rx, Ry, Rz, Rvx, Rvy, Rvz, MyHdg, MySpd, MyAlt]
        # 9 Dimensions
        self.observation_space = spaces.Box(low=-np.inf, high=np.inf, shape=(9,), dtype=np.float32)

        # IDs
        self.agent_id = -1
        self.target_id = -1
        self.sim_time = 0.0
        self.max_steps = 6000 # 6000 ticks @ 60Hz = 100s
        
        # State tracking
        self.current_cmd = {'heading': 0.0, 'speed': 300.0, 'alt': 5000.0}

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.kernel.reset(42 if seed is None else seed)
        self.sim_time = 0.0
        
        # Spawn Agent (Blue)
        self.agent_id = self.kernel.spawn_unit(ef_py.Side.Blue, ef_py.UnitType.Aircraft,
                                              0, 0, 5000, 300, 0, 0)
        
        # Spawn Target (Red) - Simple setup: 20km ahead, flying cross
        self.target_id = self.kernel.spawn_unit(ef_py.Side.Red, ef_py.UnitType.Aircraft,
                                               20000, 5000, 5000, 0, 200, 0) # Northbound
        
        # Initial Cmd state
        self.current_cmd = {'heading': 0.0, 'speed': 300.0, 'alt': 5000.0}

        observation = self._get_obs()
        info = {}
        return observation, info

    def step(self, action):
        # Get dt from kernel for proper scaling
        dt = self.kernel.get_time_step()
        
        # 1. Parse Action
        turn_cmd = float(action[0]) # -1 to 1
        speed_cmd = float(action[1]) # -1 to 1  
        climb_cmd = float(action[2]) # -1 to 1
        fire_cmd = float(action[3])
        
        # Action rates (scaled by dt for tick-frequency independence)
        MAX_TURN_RATE = 20.0   # deg/s
        MAX_ACCEL = 10.0       # m/s²
        MAX_CLIMB_CMD = 50.0   # m/s command change rate
        
        # Update Commands (Integration with dt scaling)
        self.current_cmd['heading'] += turn_cmd * MAX_TURN_RATE * dt
        self.current_cmd['heading'] = (self.current_cmd['heading'] + 360) % 360
        
        self.current_cmd['speed'] = np.clip(
            self.current_cmd['speed'] + speed_cmd * MAX_ACCEL * dt, 
            100.0, 600.0)
        
        self.current_cmd['alt'] = np.clip(
            self.current_cmd['alt'] + climb_cmd * MAX_CLIMB_CMD * dt, 
            100.0, 15000.0)
        
        # Apply Command
        self.kernel.set_command(self.agent_id, 
                               self.current_cmd['heading'], 
                               self.current_cmd['speed'], 
                               self.current_cmd['alt'])
        
        # Fire Logic  
        if fire_cmd > 0.5:
            self.kernel.fire_missile(self.agent_id, self.target_id)

        # 2. Step Simulation
        self.kernel.step()
        self.sim_time += dt
        
        # 3. Compute Reward & Done
        obs = self._get_obs()
        reward = 0.0
        terminated = False
        truncated = False
        
        # Distance Reward
        dist_sq = obs[0]**2 + obs[1]**2 + obs[2]**2
        dist = np.sqrt(dist_sq)
        
        reward += (20000.0 - dist) * 0.0001 # Small shaping reward for getting closer
        
        # Termination conditions
        if self.sim_time > 100.0: # Timeout
            truncated = True
        
        # Check if Target destroyed (HP check)
        t_hp = self.kernel.get_unit_health(self.target_id) # [curr, max]
        if t_hp[0] <= 0:
            reward += 1000.0
            terminated = True
            print("Target Destroyed!")
            
        return obs, reward, terminated, truncated, {}

    def _get_obs(self):
        # Get States
        self_pos = self.kernel.get_unit_position(self.agent_id)
        # self_vel = kernel... (Need to add get_velocity to bindings? Or computed)
        # For now let's just use Position diff
        
        target_pos = self.kernel.get_unit_position(self.target_id)
        
        # Relative Position (Target - Self)
        rx = target_pos[0] - self_pos[0]
        ry = target_pos[1] - self_pos[1]
        rz = target_pos[2] - self_pos[2]
        
        # We need self heading/speed/pitch to orient the vector? 
        # For MVP: Global Frame relative vector is fine for MLPs
        
        return np.array([rx, ry, rz, 0, 0, 0, 
                         self.current_cmd['heading'], 
                         self.current_cmd['speed'], 
                         self.current_cmd['alt']], dtype=np.float32)

    def render(self, mode='human'):
        pass # Visualization is handled by separate web server usually
