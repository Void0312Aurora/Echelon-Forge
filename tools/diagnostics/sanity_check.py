import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BUILD_ROOT = os.path.join(REPO_ROOT, "build")
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)
if BUILD_ROOT not in sys.path:
    sys.path.insert(0, BUILD_ROOT)

import ef_py
from ef_py import Side, SimulationKernel, CommMsgType

def check_type(name, value, expected_type):
    if not isinstance(value, expected_type):
        print(f"FAIL: {name} type mismatch. Expected {expected_type}, got {type(value)}")
        return False
    return True

def main():
    print("Running Sanity Check...")
    kernel = SimulationKernel()
    kernel.reset(42)
    
    # Spawn Unit
    u1 = kernel.spawn_unit(
        Side.Blue,
        "Aircraft",
        0,
        0,
        1000,
        heading=0.0,
        pitch=0.0,
        roll=0.0,
        vx=100.0,
        vy=0.0,
        vz=0.0,
    )
    
    # 1. Check get_unit_health
    health = kernel.get_unit_health(u1)
    if not check_type("get_unit_health", health, list): return
    if len(health) != 2:
        print(f"FAIL: get_unit_health length {len(health)} != 2")
        return
    print(f"PASS: get_unit_health -> {health}")
    
    # 2. Check Observation
    obs = kernel.get_agent_observation(u1)
    
    # Check fields
    if not hasattr(obs, "health"):
        print("FAIL: obs missing health field")
    else:
        print(f"PASS: obs.health={obs.health}")

    if not hasattr(obs, "can_fire"):
        print("FAIL: obs missing can_fire field")
    else:
        print(f"PASS: obs.can_fire={obs.can_fire}")
        
    print(f"PASS: Sanity Check 1 Complete.")

if __name__ == "__main__":
    main()
