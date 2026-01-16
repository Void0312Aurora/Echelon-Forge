import sys
import os
import math
import time
import rerun as rr

# Ensure we can import the module from build/
sys.path.append(os.path.join(os.getcwd(), "build"))

import cmo_py

def run_visualized_demo():
    # 1. Initialize Rerun
    # We use save() to write a static recording file, which is more robust for remote viewing
    # than trying to proxy live gRPC/WebSocket connections over SSH.
    
    rr.init("cmo_intercept_demo", spawn=False)
    rr.save("demo.rrd")
    
    kernel = cmo_py.SimulationKernel()
    kernel.reset(42)

    target = kernel.spawn_unit(cmo_py.Side.Red, cmo_py.UnitType.Aircraft, 100, 100, 5000, 10, 0, 0)
    interceptor = kernel.spawn_unit(cmo_py.Side.Blue, cmo_py.UnitType.Aircraft, 0, 0, 5000, 0, 0, 0)

    print("--- Rerun Visualization Started (File Mode) ---")
    print("Generating demo.rrd...")
    
    # Log static environment
    rr.log("world", rr.ViewCoordinates.RIGHT_HAND_Z_UP) # ENU assumption (Z Up)

    for t in range(500):
        kernel.step()
        
        # Get positions
        pos_t = kernel.get_unit_position(target)
        pos_i = kernel.get_unit_position(interceptor)
        
        # Log to Rerun
        rr.set_time("tick", sequence=t)
        
        rr.log(
            "world/target", 
            rr.Points3D([pos_t], colors=[[255, 0, 0]]) # Red
        )
        
        rr.log(
            "world/interceptor", 
            rr.Points3D([pos_i], colors=[[0, 0, 255]]) # Blue
        )
        
    print("Demo execution finished. Saved to demo.rrd")

if __name__ == "__main__":
    run_visualized_demo()
