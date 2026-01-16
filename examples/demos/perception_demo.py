import sys
import os
import math

repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.append(os.path.join(repo_root, "build"))
sys.path.append(repo_root)

import ef_py
import time

def demo():
    kernel = ef_py.SimulationKernel()
    kernel.reset(123)
    
    # Spawn Observer (Blue Aircraft)
    # Flying East at 200m/s
    obs_id = kernel.spawn_unit(ef_py.Side.Blue, ef_py.UnitType.Aircraft, 0, 0, 5000, 200, 0, 0)
    
    # Spawn Target (Red Aircraft)
    # 30km ahead, Flying West (Head-on)
    tgt_id = kernel.spawn_unit(ef_py.Side.Red, ef_py.UnitType.Aircraft, 30000, 1000, 5000, -200, 0, 0)
    
    print(f"Observer: {obs_id}, Target: {tgt_id}")
    
    # Run simulation
    # We expect detection to trigger when range < max_range (let's assume 20km default if we didn't set it? 
    # Wait, we didn't set sensor params in spawn_unit!
    # We need to manually add Sensor component? 
    # Ah, spawn_unit doesn't add Sensor component by default in C++ yet?
    # Let's check simulation_kernel.cpp spawn_unit.
    
    for i in range(100):
        kernel.step()
        
        # Get Ground Truth Range
        pos_o = kernel.get_unit_position(obs_id)
        pos_t = kernel.get_unit_position(tgt_id)
        dx = pos_t[0] - pos_o[0]
        dy = pos_t[1] - pos_o[1]
        dist = math.sqrt(dx*dx + dy*dy)
        
        # Get Sensor Detections
        dets = kernel.get_detections(obs_id)
        
        print(f"T={i*kernel.get_time_step():.2f} Range={dist:.0f}m Detections={len(dets)}")
        
        for d in dets:
            print(f"  -> Contact ID: {d.target_id} R: {d.range:.0f}m Brg: {d.bearing:.1f}")

if __name__ == "__main__":
    demo()
