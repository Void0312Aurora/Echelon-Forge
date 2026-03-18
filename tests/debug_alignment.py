#!/usr/bin/env python3
"""Debug script to check zone and spawn data alignment."""
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from gym_envs.universal_env import UniversalEnv

def debug_alignment():
    env = UniversalEnv(scenario_path="scenarios/takeoff/takeoff.json")
    
    # Reset FIRST to trigger import/merge
    obs, _ = env.reset(seed=42)
    
    print("=" * 60)
    print("ZONE AND SPAWN ALIGNMENT DEBUG")
    print("=" * 60)
    
    # Check zones in scenario_data (after reset)
    zones = env.loader.scenario_data.get("environment", {}).get("zones", [])
    print(f"\nZones loaded: {len(zones)}")
    for z in zones:
        print(f"  - {z.get('name', 'Unnamed')}: center=({z.get('x')}, {z.get('y')}), "
              f"size=({z.get('width')}x{z.get('length')}), heading={z.get('heading')}")
    
    # Check entity spawn
    entities = env.loader.scenario_data.get("entities", [])
    print(f"\nEntities spawned: {len(entities)}")
    for e in entities:
        print(f"  - {e.get('name')}: pos={e.get('pos')}, heading={e.get('heading')}")
    
    # Get actual physics state
    obs, _ = env.reset(seed=42)
    pos = env.sim.get_unit_position(env.agent_id)
    hdg = env.sim.get_unit_heading(env.agent_id)
    
    print(f"\nActual spawn position from physics: {pos}")
    print(f"Actual spawn heading from physics: {hdg}")
    
    # Check runway zone geometry
    # Runway at (0,0) with heading=90 and length=3000 means:
    # Length axis points along heading 90 (East = +X)
    # So runway spans from x = 0 - 1500 to x = 0 + 1500 = (-1500, +1500)
    print("\n" + "=" * 60)
    print("EXPECTED RUNWAY GEOMETRY (heading=90 means length along +X):")
    print("  Runway center: (0, 0)")
    print("  Length axis: +X direction (East)")
    print("  Width axis: +Y direction (North)")
    print("  X range: -1500 to +1500")
    print("  Y range: -30 to +30")
    print("\nEXPECTED AIRCRAFT POSITION:")
    print("  pos = (10, 0, 2.1)")
    print("  This is at X=10, Y=0 which is ON the runway near center")
    print("  heading=90 means facing East (+X direction)")
    print("=" * 60)

if __name__ == "__main__":
    debug_alignment()
