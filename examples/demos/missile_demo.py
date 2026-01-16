import eventlet
eventlet.monkey_patch()

import sys
import os
import time
import math
from flask import Flask, render_template
from flask_socketio import SocketIO

repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.append(os.path.join(repo_root, "build"))
sys.path.append(repo_root)

import ef_py
from examples.agents.red_agent import RedScriptedAgent

# Setup Web Server
web_viz_dir = os.path.join(repo_root, "examples", "viz", "web_viz")
template_dir = os.path.join(web_viz_dir, "templates")
static_dir = os.path.join(web_viz_dir, "static")

app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# Simulation Setup
kernel = ef_py.SimulationKernel()
kernel.reset(42)

# Entities
# Red starts at 10km distance
active_units = set()

target_id = kernel.spawn_unit(ef_py.Side.Red, ef_py.UnitType.Aircraft, 10000, 5000, 5000, 200, 0, 0)
active_units.add(target_id)

interceptor_id = kernel.spawn_unit(ef_py.Side.Blue, ef_py.UnitType.Aircraft, 0, 0, 5000, 0, 100, 0)
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
                
                kernel.set_command(interceptor_id, nav_heading, 300.0, pos_i[2])
                
                # FIRE LOGIC: Range < 8km
                if not missile_fired and dist < 8000.0:
                    print(f"Target in range ({dist:.0f}m)! FOX 2!")
                    m_id = kernel.fire_missile(interceptor_id, target_id)
                    active_units.add(m_id) # Track the missile!
                    missile_fired = True
            
            # 3. Step Physics
            kernel.step()
            sim_time += kernel.get_time_step()
            
            # 4. Visualization packet (Optimized Bulk API)
            units_data = []
            
            # Use C++ helper for bulk state
            all_units = kernel.get_all_units()
            
            for u in all_units:
                # Update our active tracking set (useful for logic)
                active_units.add(u.id)
                
                side_str = "Neutral"
                if u.side == 1: side_str = "Blue"
                elif u.side == 2: side_str = "Red"
                
                type_str = "Unknown"
                if u.type == 1: type_str = "Aircraft"
                elif u.type == 3: type_str = "Missile"
                
                units_data.append({
                    "id": u.id,
                    "side": side_str,
                    "type": type_str,
                    "x": u.x,
                    "y": u.y,
                    "z": u.z,
                    "heading": u.heading
                })
                
            # Check if target died (it won't be in the list returned by get_all_units if destroyed)
            # Logic: If target_id was in active_units but not in current snapshot -> Destroyed
            
            # Sync active_units with current reality (remove dead ones)
            current_ids = {u.id for u in all_units}
            dead_units = active_units - current_ids
            
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
