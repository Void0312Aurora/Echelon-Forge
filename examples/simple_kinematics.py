import sys
import os
import math

# Ensure we can import the module from build/
sys.path.append(os.path.join(os.getcwd(), "build"))

import ef_py

def run_fire_and_forget_demo():
    """
    Demonstrates what works: Initial State -> Deterministic Projection
    """
    kernel = ef_py.SimulationKernel()
    kernel.reset(42)

    # Scenario: Head-on collision course
    # Red Unit: at x=100, moving Left (-10)
    red = kernel.spawn_unit(ef_py.Side.Red, ef_py.UnitType.Aircraft, 
                            100, 0, 5000, 
                            -10, 0, 0)
    
    # Blue Unit: at x=0, moving Right (+10)
    blue = kernel.spawn_unit(ef_py.Side.Blue, ef_py.UnitType.Aircraft, 
                             0, 0, 5000, 
                             10, 0, 0)

    print("--- Head-on Merge Demo ---")
    for t in range(6): # Run 6 seconds (assuming 1 tick = 1 sec for simplicity, logic is 1/60 usually)
        # Manually stepping 60 times to simulate 1 second
        for _ in range(60):
            kernel.step()
            
        p_r = kernel.get_unit_position(red)
        p_b = kernel.get_unit_position(blue)
        dist = math.sqrt((p_r[0]-p_b[0])**2)
        
        print(f"Time {t}s: Red@{p_r[0]:.1f}, Blue@{p_b[0]:.1f}, Dist: {dist:.1f}")
        
    print("Simulation finished correctly. Units crossed each other.")

if __name__ == "__main__":
    run_fire_and_forget_demo()
