import sys
import os
import math
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.animation import PillowWriter

# Ensure we can import the module from build/
sys.path.append(os.path.join(os.getcwd(), "build"))

import ef_py

def run_matplotlib_demo():
    print("Initializing Simulation...")
    kernel = ef_py.SimulationKernel()
    kernel.reset(42)

    # Spawn Units
    # Red: (100, 100, 5000)
    target = kernel.spawn_unit(ef_py.Side.Red, ef_py.UnitType.Aircraft, 100, 100, 5000, 10, 0, 0)
    # Blue: (0, 0, 5000)
    interceptor = kernel.spawn_unit(ef_py.Side.Blue, ef_py.UnitType.Aircraft, 0, 0, 5000, 0, 0, 0)

    # Simulation Loop to collect data
    history_target = []
    history_interceptor = []
    
    steps = 100
    print(f"Simulating {steps} steps...")
    
    for _ in range(steps):
        kernel.step()
        
        pos_t = kernel.get_unit_position(target)
        pos_i = kernel.get_unit_position(interceptor)
        
        history_target.append(pos_t)
        history_interceptor.append(pos_i)

    print("Generating Animation (output.gif)...")
    
    fig, ax = plt.subplots()
    ax.set_xlim(-50, 200)
    ax.set_ylim(-50, 200)
    ax.set_aspect('equal')
    ax.grid(True)
    ax.set_title("CMO Kinematics Demo (2D Projection)")
    ax.set_xlabel("East (km)")
    ax.set_ylabel("North (km)")

    # Plot objects
    line_t, = ax.plot([], [], 'r-', label='Red Target')
    dot_t, = ax.plot([], [], 'ro')
    
    line_i, = ax.plot([], [], 'b-', label='Blue Interceptor')
    dot_i, = ax.plot([], [], 'bo')
    
    ax.legend()

    def update(frame):
        # Target
        pt = history_target[frame]
        line_t.set_data([p[0] for p in history_target[:frame+1]], [p[1] for p in history_target[:frame+1]])
        dot_t.set_data([pt[0]], [pt[1]])
        
        # Interceptor
        pi = history_interceptor[frame]
        line_i.set_data([p[0] for p in history_interceptor[:frame+1]], [p[1] for p in history_interceptor[:frame+1]])
        dot_i.set_data([pi[0]], [pi[1]])
        
        return line_t, dot_t, line_i, dot_i

    ani = animation.FuncAnimation(fig, update, frames=steps, interval=50, blit=True)
    
    # Save as GIF
    ani.save("simulation_demo.gif", writer=PillowWriter(fps=20))
    print("Done! Open 'simulation_demo.gif' in VSCode to view.")

if __name__ == "__main__":
    run_matplotlib_demo()
