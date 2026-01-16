import sys
import os
import math
import time

# Ensure we can import the module from build/
sys.path.append(os.path.join(os.getcwd(), "build"))

import ef_py

def normalize(v):
    mag = math.sqrt(v[0]**2 + v[1]**2 + v[2]**2)
    if mag == 0: return [0, 0, 0]
    return [v[0]/mag, v[1]/mag, v[2]/mag]

def run_intercept_demo():
    kernel = ef_py.SimulationKernel()
    kernel.reset(42)

    # 1. Spawn a Target (Red Bomber) flying straight
    # Position: (100, 100, 5000), Velocity: (10, 0, 0)
    target = kernel.spawn_unit(ef_py.Side.Red, ef_py.UnitType.Aircraft, 
                               100, 100, 5000, 
                               10, 0, 0)

    # 2. Spawn an Interceptor (Blue Fighter)
    # Position: (0, 0, 5000) - 500 ticks running
    interceptor = kernel.spawn_unit(ef_py.Side.Blue, ef_py.UnitType.Aircraft, 
                                    0, 0, 5000, 
                                    0, 0, 0) # Initially stationary

    interceptor_speed = 20.0 # Faster than target

    print("--- Intercept Demo Start ---")
    print(f"Target Start: {kernel.get_unit_position(target)}")
    print(f"Interceptor Start: {kernel.get_unit_position(interceptor)}")

    for t in range(200): # Run for 200 ticks
        # --- Python Logic (The "Brain") ---
        # Get observations
        pos_t = kernel.get_unit_position(target)
        pos_i = kernel.get_unit_position(interceptor)

        # Calculate vector to target
        diff = [pos_t[0] - pos_i[0], pos_t[1] - pos_i[1], pos_t[2] - pos_i[2]]
        distance = math.sqrt(diff[0]**2 + diff[1]**2 + diff[2]**2)
        
        # Simple "Guidance Law": Fly directly towards target
        direction = normalize(diff)
        
        # We can't set velocity directly via API yet (Need to add set_velocity capabilities generally)
        # But wait! We only exposed 'spawn_unit' and 'get_position'. 
        # We actually haven't exposed a way to UPDATE command in our MVP implementation plan yet!
        # This is a great finding. The current engine is "Fire and Forget".
        
        # CRITICAL REALIZATION: In v0.0.1, we cannot change velocity after spawn!
        # So this demo effectively shows we need to add "Command" capability.
        pass 
        
        kernel.step()
        
        if t % 20 == 0:
            print(f"Tick {t}: Distance {distance:.2f} m")

    print("--- Demo End ---")
    print("Wait... did the interceptor move? No, because we haven't implemented 'SetVelocity' binding yet!")
    print("This demonstrates exactly what needs to be done next: The 'Action Interface'.")

if __name__ == "__main__":
    run_intercept_demo()
