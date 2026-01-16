import eventlet
eventlet.monkey_patch()

import sys
import os
import time
import math
from flask import Flask, render_template
from flask_socketio import SocketIO

sys.path.append(os.path.abspath(os.path.join(os.getcwd(), "build")))
sys.path.append(os.path.abspath(os.getcwd()))

import cmo_py
from examples.agents.red_agent import RedScriptedAgent

# Setup Web Server
base_dir = os.path.abspath(os.path.dirname(__file__))
template_dir = os.path.join(base_dir, "web_viz/templates")
static_dir = os.path.join(base_dir, "web_viz/static")

app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# Simulation Setup
kernel = cmo_py.SimulationKernel()
kernel.reset(42)

# Entities
# Red starts at 10km distance
active_units = set()

target_id = kernel.spawn_unit(cmo_py.Side.Red, cmo_py.UnitType.Aircraft, 10000, 5000, 5000, 200, 0, 0)
active_units.add(target_id)

interceptor_id = kernel.spawn_unit(cmo_py.Side.Blue, cmo_py.UnitType.Aircraft, 0, 0, 5000, 0, 100, 0)
active_units.add(interceptor_id)

red_agent = RedScriptedAgent(kernel, target_id)
missile_fired = False

print(f"Entities Spawned: Target={target_id}, Interceptor={interceptor_id}")

def to_degrees(rad): return rad * 180.0 / math.pi
def normalize_angle(angle): return angle % 360.0


# Control Flags
simulation_running = False
simulation_reset = False

@socketio.on('start_sim')
def handle_start_sim():
    global simulation_running, simulation_reset
    print("Received Start Signal")
    simulation_running = True
    if simulation_reset:
        # Optional: Implement reset logic if we want replay ability
        pass

def simulation_loop():
    global missile_fired, simulation_running
    print("Server ready. Waiting for start signal...")
    
    # Wait for start
    while not simulation_running:
        socketio.sleep(0.1)
        
    print("Starting Simulation...")
    
    sim_time = 0.0
    dt_wall = 0.1 # 10Hz viewing freq
    
    while True:
        try:
            if not simulation_running:
                socketio.sleep(0.1)
                continue

            # 1. Update Agents
            # Check liveness first to prevent errors
            target_alive = kernel.is_unit_active(target_id)
            
            # 1. Update Red Agent (Adversary)
            try:
                if target_alive:
                    # We need interceptor pos for red agent
                    pos_i = kernel.get_unit_position(interceptor_id)
                    red_agent.step(pos_i, sim_time)
            except Exception as e:
                # If interceptor died (unlikely here), this might fail
                pass
            
            # 2. Update Blue Agent (Shooter)
            if target_alive:
                pos_t = kernel.get_unit_position(target_id)
                pos_i = kernel.get_unit_position(interceptor_id)
                
                dx = pos_t[0] - pos_i[0]
                dy = pos_t[1] - pos_i[1]
                dist = math.sqrt(dx*dx + dy*dy)
                
                # Turn towards target
                math_angle = math.atan2(dy, dx)
                nav_heading = 90.0 - to_degrees(math_angle)
                
                kernel.set_command(interceptor_id, nav_heading, 300.0)
                
                # FIRE LOGIC: Range < 8km
                if not missile_fired and dist < 8000.0:
                    print(f"Target in range ({dist:.0f}m)! FOX 2!")
                    m_id = kernel.fire_missile(interceptor_id, target_id)
                    active_units.add(m_id) # Track the missile!
                    missile_fired = True
            
            # 3. Step Physics
            kernel.step()
            sim_time += kernel.get_time_step()
            
            # 4. Visualization packet
            units_data = []
            
            # Filter dead units
            dead_units = set()
            for uid in active_units:
                if not kernel.is_unit_active(uid):
                    dead_units.add(uid)
                    continue
                    
                pos = kernel.get_unit_position(uid)
                heading = kernel.get_unit_heading(uid)
                utype = kernel.get_unit_type(uid)
                
                # Determine Side (We don't have get_unit_side helper yet, but logic is implicit)
                # Hack: 1=Blue, 2=Red. 
                # Blue entities: interceptor, missile. Red: target.
                side_str = "Neutral"
                if uid == interceptor_id: side_str = "Blue"
                elif uid == target_id: side_str = "Red"
                elif uid > interceptor_id: side_str = "Blue" # Newtons assumption: Missile ID > Interceptor ID
                
                # Unit Type Mapping: 1=Air, 3=Missile
                type_str = "Unknown"
                if utype == 1: type_str = "Aircraft"
                elif utype == 3: type_str = "Missile"
                
                units_data.append({
                    "id": uid, 
                    "side": side_str, 
                    "type": type_str,
                    "x": pos[0], 
                    "y": pos[1], 
                    "z": pos[2],
                    "heading": heading
                })
                
            # Remove dead units from registry
            for dead in dead_units:
                active_units.remove(dead)
                if dead == target_id:
                    print("Visualizer confirmed Target Destroyed!")
            
            state = {
                "tick": sim_time,
                "units": units_data
            }
            socketio.emit('state_update', state)
            
            if not target_alive and missile_fired:
                 # Ensure we send the "splash" frame before quitting/pausing
                 socketio.sleep(0.1)
                 # print("Mission Complete.")
                 # Don't break, allow seeing the aftermath
                 # simulation_running = False 
                
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
    socketio.start_background_task(simulation_loop)
    print("Running Missile Demo on http://localhost:5000")
    socketio.run(app, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)
