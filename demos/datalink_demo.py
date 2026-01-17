import sys
import os
import math

# Add build/ to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../build'))

import ef_py
from ef_py import Side, SimulationKernel

def main():
    kernel = SimulationKernel()
    kernel.reset(42)
    
    # 1. Test Horizon Blocked (Low Altitude)
    print("\n--- TEST 1: Low Altitude (Blocked) ---")
    kernel.reset(42)
    # Observer A: Blue, Pos(0,0,10). Heading North (0).
    obs_a = kernel.spawn_unit(Side.Blue, "Aircraft", 0, 0, 10, 0, 0, 0)
    
    # Observer B: Blue, Pos(50000,0,10). Dist 50km.
    obs_b = kernel.spawn_unit(Side.Blue, "Aircraft", 50000, 0, 10, 0, 0, 0)
    
    # Target: Red, Pos(0, 5000, 100), Speed 100 m/s South (Closing).
    target = kernel.spawn_unit(Side.Red, "Aircraft", 0, 5000, 100, 0, -100, 0)
    
    for _ in range(20):
        kernel.step() 
    
    dets_a = kernel.get_detections(obs_a)
    dets_b = kernel.get_detections(obs_b)
    
    print(f"Obs A Detections: {len(dets_a)}")
    print(f"Obs B Detections: {len(dets_b)}")
    
    if len(dets_a) > 0 and len(dets_b) == 0:
        print("PASS: A sees Target, B blocked by Horizon.")
    else:
        print(f"FAIL: A={len(dets_a)}, B={len(dets_b)}")

    # 2. Test Horizon Clear (High Altitude)
    print("\n--- TEST 2: High Altitude (Connected) ---")
    kernel.reset(42)
    
    # Observer A: Blue, Pos(0,0,5000). 
    obs_a = kernel.spawn_unit(Side.Blue, "Aircraft", 0, 0, 5000, 0, 0, 0)
    
    # Observer B: Blue, Pos(50000,0,5000).
    obs_b = kernel.spawn_unit(Side.Blue, "Aircraft", 50000, 0, 5000, 0, 0, 0)
    
    # Target: Red, Pos(0, 5000, 100), Speed 100 m/s South.
    target = kernel.spawn_unit(Side.Red, "Aircraft", 0, 5000, 100, 0, -100, 0)
    
    for _ in range(20):
        kernel.step()
    
    dets_a = kernel.get_detections(obs_a)
    dets_b = kernel.get_detections(obs_b)
    
    print(f"Obs A Detections: {len(dets_a)}")
    print(f"Obs B Detections: {len(dets_b)}")
    
    if len(dets_a) > 0 and len(dets_b) > 0:
        print("PASS: Link Connected. B sees target via A.")
    else:
        print(f"FAIL: A={len(dets_a)}, B={len(dets_b)}")

if __name__ == "__main__":
    main()
