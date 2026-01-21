
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

def test_takeoff_physics():
    sim = ef_py.SimulationKernel()
    sim.load_database("examples/config/database")
    
    loader = ScenarioLoader(sim)
    scenario_path = os.path.join(base_dir, "scenarios/takeoff.json")
    
    print(f"Loading Scenario: {scenario_path}")
    loader.load_scenario(scenario_path)
    
    agent_id = loader.agent_id
    if agent_id is None:
        print("Error: No Agent Found!")
        return

    print(f"Agent ID: {agent_id}")
    
    # Init state
    pos0 = sim.get_unit_position(agent_id)
    print(f"Initial Pos: {pos0}")
    
    # ACTIVATE PHYSICS by setting a command
    # Mimic UniversalEnv reset
    sim.set_command(
        agent_id,
        0.0, # heading
        0.0, # speed
        0.0, # altitude
    )
    
    dt = 0.05
    sim.set_time_step(dt)
    
    print("Time(s) | X(m)    | Y(m)    | Z(m)    | Speed | Heading")
    print("-" * 65)
    
    for i in range(100): # 5 seconds
        sim.step()
        pos = sim.get_unit_position(agent_id)
        hdg = sim.get_unit_heading(agent_id)
        # Assuming speed is 0 initially?
        
        # Check delta
        if abs(pos[0] - pos0[0]) > 0.1 or abs(pos[1] - pos0[1]) > 0.1 or abs(pos[2] - pos0[2]) > 0.1:
            drift_mark = "DRIFT!"
        else:
            drift_mark = ""
            
        print(f"{i*dt:7.2f} | {pos[0]:7.2f} | {pos[1]:7.2f} | {pos[2]:7.2f} | ----- | {hdg:6.2f} {drift_mark}")

if __name__ == "__main__":
    test_takeoff_physics()
