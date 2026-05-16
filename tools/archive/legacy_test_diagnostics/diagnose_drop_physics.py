
import sys
import os
import json
import time

# Add repo root and build to path
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(base_dir)
sys.path.append(os.path.join(base_dir, "build"))

import ef_py
from gym_envs.scenario_loader import ScenarioLoader

# Mock simulation kernel
# We need to load definitions first usually?
# Actually ScenarioLoader takes a pre-inited kernel.

def test_drop():
    sim = ef_py.SimulationKernel()
    sim.load_database("examples/config/database")
    
    loader = ScenarioLoader(sim)
    
    # We will manually spawn a unit to ensure exact conditions
    # Position: 0,0,100. Vel: 0,0,0. Heading: 0.
    sim.reset(42)
    
    eid = sim.spawn_unit(
        ef_py.Side.Blue,
        "F-16C_Block50", # Must match database name
        0.0, 0.0, 100.0, # Pos
        heading=0.0,
        pitch=0.0,
        roll=0.0,
        vx=0.0,
        vy=0.0,
        vz=0.0,
    )
    
    print(f"Spawned Unit {eid} at [0, 0, 100]")
    
    dt = 0.05
    sim.set_time_step(dt)
    
    print("Time(s) | X(m) | Y(m) | Z(m) | Speed(m/s) | Heading")
    print("-" * 60)
    
    for i in range(20): # 1 second
        sim.step()
        pos = sim.get_unit_position(eid)
        hdg = sim.get_unit_heading(eid)
        raw = sim.get_unit_velocity(eid) if hasattr(sim, 'get_unit_velocity') else [0,0,0] # C++ binding might vary
        
        # Calculate speed manually if needed
        # But let's just trace Pos
        
        print(f"{i*dt:7.2f} | {pos[0]:6.2f} | {pos[1]:6.2f} | {pos[2]:6.2f} | ----- | {hdg:.2f}")

if __name__ == "__main__":
    test_drop()
