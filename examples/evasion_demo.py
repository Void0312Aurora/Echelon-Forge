import eventlet
eventlet.monkey_patch()

import sys
import os
import time
import math
from flask import Flask, render_template
from flask_socketio import SocketIO

# Import CMO Engine & Agents
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), "build")))
sys.path.append(os.path.abspath(os.getcwd())) # To find examples.agents

import cmo_py
from examples.agents.red_agent import RedScriptedAgent

# Setup Web Server (Use absolute paths for robustness)
base_dir = os.path.abspath(os.path.dirname(__file__))
# Note: visualization templates are shared in web_viz
template_dir = os.path.join(base_dir, "web_viz/templates")
static_dir = os.path.join(base_dir, "web_viz/static")

app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# Simulation Setup
kernel = cmo_py.SimulationKernel()
kernel.reset(42)

# Entities
# Red starts further away to allow engagement geometry to develop
target_id = kernel.spawn_unit(cmo_py.Side.Red, cmo_py.UnitType.Aircraft, 5000, 5000, 5000, 200, 0, 0) 
interceptor_id = kernel.spawn_unit(cmo_py.Side.Blue, cmo_py.UnitType.Aircraft, 0, 0, 5000, 0, 100, 0) 

red_agent = RedScriptedAgent(kernel, target_id)

print(f"Entities Spawned: Target={target_id}, Interceptor={interceptor_id}")

def to_degrees(rad): return rad * 180.0 / math.pi
def normalize_angle(angle): return angle % 360.0

def simulation_loop():
    print("Starting Dogfight Simulation...")
    
    sim_time = 0.0
    dt_wall = 0.1 # 10Hz viewing freq
    
    while True:
        # 0. Get State
        pos_t = kernel.get_unit_position(target_id)
        pos_i = kernel.get_unit_position(interceptor_id)
        
        # 1. Update Red Agent (Adversary)
        red_status = red_agent.step(pos_i, sim_time)
        
        # 2. Update Blue Agent (Pure Pursuit Logic)
        dx = pos_t[0] - pos_i[0]
        dy = pos_t[1] - pos_i[1]
        
        # Intercept Logic
        math_angle = math.atan2(dy, dx)
        nav_heading = 90.0 - to_degrees(math_angle)
        nav_heading = normalize_angle(nav_heading)
        
        # Blue tries to close distance at max speed (Afterburner ON!)
        # Speed advantage (450 vs 300) is crucial for Pure Pursuit against a maneuvering target.
        kernel.set_command(interceptor_id, nav_heading, 450.0)
        
        # 3. Step Physics
        kernel.step()
        sim_time += kernel.get_time_step()
        
        # 4. Visualization
        state = {
            "tick": sim_time,
            "units": [
                {"id": "RedTarget", "side": "Red", "x": pos_t[0], "y": pos_t[1], "z": pos_t[2]},
                {"id": "BlueInterceptor", "side": "Blue", "x": pos_i[0], "y": pos_i[1], "z": pos_i[2]}
            ]
        }
        socketio.emit('state_update', state)
        
        # Log event if evasive
        if red_status["evading"] and int(sim_time*10) % 10 == 0:
            print(f"Defending! Range: {red_status['dist']:.0f}m")
            
        socketio.sleep(dt_wall)

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    socketio.start_background_task(simulation_loop)
    print("Running Evasion Demo on http://localhost:5000")
    socketio.run(app, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)
