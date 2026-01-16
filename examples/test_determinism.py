import ef_py
import numpy as np
import sys

def run_simulation(seed, steps=100):
    kernel = ef_py.SimulationKernel()
    kernel.reset(seed)
    
    # Spawn scenario
    obs_id = kernel.spawn_unit(ef_py.Side.Blue, ef_py.UnitType.Aircraft, 0,0,5000, 300,0,0)
    tgt_id = kernel.spawn_unit(ef_py.Side.Red, ef_py.UnitType.Aircraft, 20000,5000,5000, 0,200,0) # Cross path
    
    trace = []
    
    for i in range(steps):
        # Apply some random-ish control based on time (deterministic if time is deterministic)
        if i == 10:
             kernel.set_command(obs_id, 90.0, 300.0, 5000.0)
        
        kernel.step()
        
        obs = kernel.get_agent_observation(obs_id)
        trace.append({
            'time': obs.sim_time,
            'x': obs.x, 'y': obs.y, 'z': obs.z,
            'vx': obs.vx, 'score': obs.total_reward
        })
        
    return trace

def compare_traces(t1, t2):
    if len(t1) != len(t2):
        print("Length mismatch!")
        return False
        
    mismatches = 0
    for i in range(len(t1)):
        row1 = t1[i]
        row2 = t2[i]
        
        # Check Pos
        diff = abs(row1['x'] - row2['x']) + abs(row1['y'] - row2['y'])
        if diff > 1e-9:
            print(f"Step {i} Mismatch! diff={diff}")
            mismatches += 1
            
    return mismatches == 0

def main():
    print("Running Run 1...")
    trace1 = run_simulation(42)
    
    print("Running Run 2...")
    trace2 = run_simulation(42)
    
    print("Comparing...")
    if compare_traces(trace1, trace2):
        print("SUCCESS: Simulation is Deterministic.")
        sys.exit(0)
    else:
        print("FAILURE: Simulation is NON-Deterministic.")
        sys.exit(1)

if __name__ == "__main__":
    main()
