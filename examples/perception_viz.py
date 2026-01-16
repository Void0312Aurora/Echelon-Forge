# examples/perception_viz.py
# Visualization demo for Sensor and Detection rendering

import eventlet
eventlet.monkey_patch()

import sys
import os
import time
import math
from flask import Flask, render_template
from flask_socketio import SocketIO

sys.path.append(os.path.abspath(os.path.join(os.getcwd(), "build")))
import ef_py

# Setup Web Server
base_dir = os.path.abspath(os.path.dirname(__file__))
template_dir = os.path.join(base_dir, "web_viz/templates")
static_dir = os.path.join(base_dir, "web_viz/static")

app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# Simulation Setup
kernel = ef_py.SimulationKernel()
kernel.reset(42)

# Spawn units
# Observer (Blue) at origin, flying East (Faster: 300 m/s ~ Mach 0.9)
obs_id = kernel.spawn_unit(ef_py.Side.Blue, ef_py.UnitType.Aircraft, 0, 0, 5000, 300, 0, 0)
# Target (Red) 60km away, flying West (Faster: 300 m/s)
tgt_id = kernel.spawn_unit(ef_py.Side.Red, ef_py.UnitType.Aircraft, 60000, 2000, 5000, -300, 0, 0)

print(f"Entities Spawned: Observer={obs_id}, Target={tgt_id}")

# Control Flags
simulation_running = False
active_missiles = []

@socketio.on('start_sim')
def handle_start_sim():
    global simulation_running
    print("Received Start Signal")
    simulation_running = True

def simulation_loop():
    global simulation_running
    global active_missiles
    print("Server ready. Waiting for start signal...")
    
    # Wait for start
    while not simulation_running:
        socketio.sleep(0.1)
        
    print("Starting Perception Visualization Simulation...")
    
    sim_time = 0.0
    dt_wall = 0.05 # Faster updates (20Hz)
    fired = False
    
    while True:
        try:
            if not simulation_running:
                socketio.sleep(0.1)
                continue

            # FIRE LOGIC TEST: Fire at T=3.0s (Sooner, since faster)
            if not fired and sim_time > 3.0:
                    if kernel.is_unit_active(obs_id) and kernel.is_unit_active(tgt_id):
                        m_id = kernel.fire_missile(obs_id, tgt_id)
                        if m_id > 0:
                            active_missiles.append(m_id)
                            print(f"DEBUG: Fired Missile {m_id} at Time {sim_time:.2f}")
                            fired = True
            
            # CLIMB TEST: At T=1.0s, commanded climb to 8000m
            if abs(sim_time - 1.0) < 0.1:
                 # Turn Right 90 deg, Speed 400, Alt 8000
                 kernel.set_command(obs_id, 90.0, 400.0, 8000.0)
                 print("DEBUG: Commanded Climb to 8000m, Hdg 90")

            # Step Physics
            kernel.step()
            sim_time += kernel.get_time_step()
        
            # Gather Data - WORKAROUND: Build manually since get_all_units is broken
            units_data = []
            
            # Check Observer
            if kernel.is_unit_active(obs_id):
                obs_pos = kernel.get_unit_position(obs_id)
                obs_hdg = kernel.get_unit_heading(obs_id)
                obs_hp = kernel.get_unit_health(obs_id)
                
                units_data.append({
                    "id": obs_id,
                    "side": "Blue",
                    "type": "Aircraft",
                    "x": obs_pos[0],
                    "y": obs_pos[1],
                    "z": obs_pos[2],
                    "heading": obs_hdg,
                    "hp": obs_hp[0] if obs_hp else 0.0,
                    "max_hp": obs_hp[1] if obs_hp else 1.0,
                    "sensors": [{"radius": 30000.0, "fov": 120.0}],
                })
                # Add detections
                dets = kernel.get_detections(obs_id)
                if dets:
                    d_list = [{"target_id": d.target_id, "range": d.range, "bearing": d.bearing} for d in dets]
                    units_data[-1]["detections"] = d_list
            
            # Check Target
            if kernel.is_unit_active(tgt_id):
                tgt_pos = kernel.get_unit_position(tgt_id)
                tgt_hdg = kernel.get_unit_heading(tgt_id)
                tgt_hp = kernel.get_unit_health(tgt_id)
                
                units_data.append({
                    "id": tgt_id,
                    "side": "Red",
                    "type": "Aircraft",
                    "x": tgt_pos[0],
                    "y": tgt_pos[1],
                    "z": tgt_pos[2],
                    "heading": tgt_hdg,
                    "hp": tgt_hp[0] if tgt_hp else 0.0,
                    "max_hp": tgt_hp[1] if tgt_hp else 1.0,
                    "sensors": [{"radius": 30000.0, "fov": 120.0}],
                })

            # Check Missiles
            still_active = []
            for m_id in active_missiles:
                if kernel.is_unit_active(m_id):
                    m_pos = kernel.get_unit_position(m_id)
                    m_hdg = kernel.get_unit_heading(m_id)
                    units_data.append({
                        "id": m_id,
                        "side": "Blue", # Assume ownership for color
                        "type": "Missile",
                        "x": m_pos[0],
                        "y": m_pos[1],
                        "z": m_pos[2],
                        "heading": m_hdg,
                        "hp": 1.0, "max_hp": 1.0, # Dummy HP
                        "sensors": [{"radius": 15000.0, "fov": 45.0}]
                    })
                    still_active.append(m_id)
            active_missiles = still_active
            
            state = {
                "tick": sim_time,
                "units": units_data
            }
            socketio.emit('state_update', state)
            
            socketio.sleep(dt_wall)
            
        except Exception as e:
            print(f"Sim Error loop: {e}")
            import traceback
            traceback.print_exc()
            break

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    # Auto-start REMOVED per user request
    socketio.start_background_task(simulation_loop)
    print("Running Perception Viz on http://localhost:5000")
    socketio.run(app, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)
