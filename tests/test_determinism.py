import sys
import os

# Ensure we can import the module from build/
sys.path.append(os.path.join(os.getcwd(), "build"))

import cmo_py
import math

def test_determinism():
    print("Test 1: Determinism Check")
    kernel1 = cmo_py.SimulationKernel()
    kernel2 = cmo_py.SimulationKernel()

    seed = 12345
    kernel1.reset(seed)
    kernel2.reset(seed)

    # Spawn identical units
    e1 = kernel1.spawn_unit(cmo_py.Side.Red, cmo_py.UnitType.Aircraft, 0, 0, 0, 10, 5, 1)
    e2 = kernel2.spawn_unit(cmo_py.Side.Red, cmo_py.UnitType.Aircraft, 0, 0, 0, 10, 5, 1)

    steps = 1000
    mismatch = False

    for i in range(steps):
        kernel1.step()
        kernel2.step()
        
        pos1 = kernel1.get_unit_position(e1)
        pos2 = kernel2.get_unit_position(e2)

        if pos1 != pos2:
            print(f"Mismatch at step {i}: {pos1} != {pos2}")
            mismatch = True
            break
    
    if not mismatch:
        print(f"SUCCESS: Both kernels matched perfectly for {steps} steps.")
    else:
        print("FAILURE: Determinism check failed.")
        sys.exit(1)

def test_physics():
    print("\nTest 2: Basic Physics Check")
    kernel = cmo_py.SimulationKernel()
    kernel.reset(42)

    # V = (10, 0, 0)
    e = kernel.spawn_unit(cmo_py.Side.Blue, cmo_py.UnitType.Ship, 0, 0, 0, 10, 0, 0)
    
    # Run 60 ticks (1 second at 60Hz)
    for _ in range(60):
        kernel.step()
        
    pos = kernel.get_unit_position(e)
    # Expected: (10, 0, 0) approximately (floating point error expected but small)
    
    print(f"Position after 1s: {pos}")
    if math.isclose(pos[0], 10.0, rel_tol=1e-5) and \
       math.isclose(pos[1], 0.0, abs_tol=1e-5) and \
       math.isclose(pos[2], 0.0, abs_tol=1e-5):
        print("SUCCESS: Physics position matches expectation.")
    else:
        print("FAILURE: Physics check failed.")
        sys.exit(1)

if __name__ == "__main__":
    try:
        test_determinism()
        test_physics()
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)
