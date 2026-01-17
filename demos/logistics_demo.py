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
    
    # Load Database
    db_path = os.path.join(os.path.dirname(__file__), '../examples/config/database')
    print(f"Loading DB from: {db_path}")
    if not kernel.load_database(db_path):
        print("Failed to load database")
        return

    print("Spawning Base...")
    base_id = kernel.spawn_unit(Side.Blue, "Generic_Airbase", 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    print(f"Base ID: {base_id}")

    print("Spawning Fighter (Stopped)...")
    unit_id = kernel.spawn_unit(Side.Blue, "Su-35S_Flanker-E", 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    print(f"Unit ID: {unit_id}")
    
    # Run Simulation
    for i in range(100):
        kernel.step()
        
        fuel = kernel.get_unit_fuel(unit_id)
        # Fuel: [internal, max_int, external, max_ext]
        if i % 10 == 0:
            print(f"Step {i}: Fuel={fuel[0]:.1f}/{fuel[1]:.1f}")

    print("Demo Complete")

if __name__ == "__main__":
    main()
