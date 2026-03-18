#!/usr/bin/env python3
"""
Diagnose terrain classification at spawn point.
"""
import sys
import os

from python.testing.runtime import ensure_repo_imports

REPO_ROOT = ensure_repo_imports()
os.chdir(REPO_ROOT)

import ef_py

def main():
    print("=" * 70)
    print("TERRAIN CLASSIFICATION DIAGNOSTIC")
    print("=" * 70)
    
    sim = ef_py.SimulationKernel()
    sim.load_database("examples/config/database")
    
    # Add zones BEFORE reset to ensure they're registered
    print("\n1. ADDING ZONES")
    print("-" * 50)
    
    # Runway 09: center (0,0), width 60, length 3000, heading 90
    sim.clear_zones()
    sim.add_zone("Runway 09", 0.0, 0.0, 60.0, 3000.0, 90.0, 0)  # 0 = Concrete
    sim.add_zone("Apron", 0.0, 0.0, 1000.0, 4000.0, 90.0, 1)    # 1 = Asphalt
    
    print("  Added: Runway 09 (x=0, y=0, w=60, l=3000, hdg=90, Concrete)")
    print("  Added: Apron (x=0, y=0, w=1000, l=4000, hdg=90, Asphalt)")
    
    sim.reset(42)
    
    # Test terrain at various points
    print("\n2. TERRAIN CLASSIFICATION TESTS")
    print("-" * 50)
    
    test_points = [
        (-1400.0, 0.0, "Spawn Point"),
        (0.0, 0.0, "Runway Center"),
        (1400.0, 0.0, "Runway End"),
        (-1600.0, 0.0, "Off Runway"),
        (0.0, 100.0, "100m North of Centerline"),
    ]
    
    for x, y, label in test_points:
        terrain = sim.get_terrain_at(x, y)
        print(f"  {label} ({x}, {y}):")
        print(f"    Surface: {terrain.type}, Elevation: {terrain.elevation:.1f}m")
    
    # Spawn aircraft and check what terrain it's on
    print("\n3. SPAWN AND CHECK")
    print("-" * 50)
    
    eid = sim.spawn_unit(
        ef_py.Side.Blue,
        "Aircraft",
        -1400.0, 0.0, 2.1,
        90.0, 0.0, 0.0,
        0.0, 0.0, 0.0
    )
    
    pos = sim.get_unit_position(eid)
    terrain = sim.get_terrain_at(pos[0], pos[1])
    
    print(f"  Aircraft spawned at: ({pos[0]:.1f}, {pos[1]:.1f}, {pos[2]:.1f})")
    print(f"  Terrain under aircraft: {terrain.type}")
    
    # Check if zones_ list has any entries by checking terrain at runway center
    print("\n4. DIAGNOSIS")
    print("=" * 70)
    
    center_terrain = sim.get_terrain_at(0.0, 0.0)
    spawn_terrain = sim.get_terrain_at(-1400.0, 0.0)
    
    # TerrainType: 0=Concrete, 1=Asphalt, 2=HardPacked, 3=SoftDirt, 4=Water, 5=Obstacle
    if hasattr(center_terrain, 'type'):
        if center_terrain.type == 0:  # Concrete
            print("  ✓ Runway center correctly classified as Concrete.")
        else:
            print(f"  ✗ Runway center is NOT Concrete (type={center_terrain.type}).")
            print("    Zones may not be registered correctly.")
    
    if hasattr(spawn_terrain, 'type'):
        if spawn_terrain.type == 0:  # Concrete
            print("  ✓ Spawn point correctly classified as Concrete.")
        elif spawn_terrain.type == 1:  # Asphalt
            print("  △ Spawn point is Asphalt (Apron), mu=0.025 (acceptable).")
        elif spawn_terrain.type == 3:  # SoftDirt
            print("  ✗ Spawn point is SoftDirt! mu=0.15 (HIGH FRICTION - explains slow accel).")
            print("    The zone geometry or registration is broken.")
        else:
            print(f"  ? Spawn point type: {spawn_terrain.type}")

if __name__ == "__main__":
    main()
