import sys
import os
import math
import time

# Ensure we can find the built module
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../build")))

import ef_py  # The binding module

def run_demo():
    print("Initializing Simulation...")
    sim = ef_py.SimulationKernel()
    sim.reset(42)

    # Load Unit Definitions
    config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../examples/config/database"))
    print(f"Loading units from: {config_path}")
    
    if not sim.load_unit_definitions(config_path):
        print("Failed to load unit definitions!")
        return

    # Scenario Setup
    # Blue Force: 1x AWACS, 2x F-16
    print("Spawning Blue Force...")
    awacs_id = sim.spawn_unit(ef_py.Side.Blue, "E-3_Sentry_AWACS", 0, 0, 10000, 200, 0, 0)
    f16_1_id = sim.spawn_unit(ef_py.Side.Blue, "F-16C_Block50", 10000, 10000, 5000, 250, 0, 0) # East of AWACS
    
    if awacs_id == 0 or f16_1_id == 0:
        print("Failed to spawn Blue units. Check definition names.")
        return

    # Red Force: 1x Su-35 (Approaching from North)
    print("Spawning Red Force...")
    su35_id = sim.spawn_unit(ef_py.Side.Red, "Su-35S_Flanker-E", 50000, 50000, 6000, -300, -300, 0)
    
    if su35_id == 0:
        print("Failed to spawn Red unit.")
        return

    # Set Commands (Intercept Course)
    # F-16 moves to intercept Su-35
    # Calculate heading to target
    f16_obs = sim.get_agent_observation(f16_1_id)
    su35_obs = sim.get_agent_observation(su35_id) # Cheating for demo setup
    
    dx = su35_obs.x - f16_obs.x
    dy = su35_obs.y - f16_obs.y
    heading_rad = math.atan2(dy, dx)
    heading_deg = math.degrees(heading_rad)
    heading_nav = (90 - heading_deg) % 360
    
    print(f"Commanding F-16 to Heading {heading_nav:.1f}")
    sim.set_command(f16_1_id, heading_nav, 300.0, 6000.0)

    # Simulation Loop
    print("\nRunning Simulation Loop...")
    for i in range(120): # 2 seconds at 60Hz
        sim.step()
        
        if i % 20 == 0:
            f16_state = sim.get_agent_observation(f16_1_id)
            su35_state = sim.get_agent_observation(su35_id)
            
            # Check detections (did AWACS see Su-35?)
            awacs_dets = sim.get_detections(awacs_id)
            f16_dets = sim.get_detections(f16_1_id)
            
            print(f"Step {i}")
            print(f"  F-16: Pos=({f16_state.x:.0f}, {f16_state.y:.0f}), Heading={f16_state.heading:.1f}")
            print(f"  Su-35: Pos=({su35_state.x:.0f}, {su35_state.y:.0f})")
            
            if awacs_dets:
                print(f"  AWACS Radar Contacts: {len(awacs_dets)}")
                for det in awacs_dets:
                    print(f"    - ID {det.target_id} Range {det.range:.0f}m")
            
            if f16_dets:
                print(f"  F-16 Radar Contacts: {len(f16_dets)}")
                # If Data Link works, F-16 might see Su-35 via AWACS even beyond its own range?
                # For this demo, separation is small (40km), so F-16 usually sees it too.

if __name__ == "__main__":
    run_demo()
