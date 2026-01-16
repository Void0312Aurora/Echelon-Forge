import eventlet
eventlet.monkey_patch()

import sys
import os
import time
import math
from flask import Flask, render_template
from flask_socketio import SocketIO

# Import CMO Engine
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), "build")))
import cmo_py

# Setup Web Server (Use absolute paths)
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
target = kernel.spawn_unit(cmo_py.Side.Red, cmo_py.UnitType.Aircraft, 200, 200, 5000, 150, 0, 0) # Moving East
interceptor = kernel.spawn_unit(cmo_py.Side.Blue, cmo_py.UnitType.Aircraft, 0, 0, 5000, 0, 100, 0) # Start Moving North

print(f"Entities Spawned: Target={target}, Interceptor={interceptor}")

def to_degrees(rad):
    return rad * 180.0 / math.pi

def normalize_angle(angle):
    return angle % 360.0

def simulation_loop():
    print("Starting Simulation Loop with Agent Control...")
    
    while True:
        # 1. Observation
        pos_t = kernel.get_unit_position(target) # [x, y, z]
        pos_i = kernel.get_unit_position(interceptor)
        
        # 2. Agent Logic (Pure Pursuit)
        dx = pos_t[0] - pos_i[0]
        dy = pos_t[1] - pos_i[1]
        dist = math.sqrt(dx*dx + dy*dy)
        
        # Calculate Math Angle (0=East, CCW)
        math_angle = math.atan2(dy, dx)
        
        # Convert to Nav Heading (0=North, CW)
        # Nav = 90 - Math_Deg
        nav_heading = 90.0 - to_degrees(math_angle)
        nav_heading = normalize_angle(nav_heading)
        
        # Command Interceptor
        # Speed: 300 m/s (approx 600 knots)
        # Heading: Calculated intercept course
        kernel.set_command(interceptor, nav_heading, 300.0)
        
        # Command Target to circle (Primitive evasion)
        # Just keep turning right 1 degree per tick
        # We don't have get_heading yet visible easily, so just fixed pattern?
        # Let's just set a fixed command for target too to keep it moving fast
        kernel.set_command(target, 90.0, 200.0) # Fly East at 200 m/s
        
        # 3. Step Physics
        kernel.step()
        
        # 4. Visualization Update
        state = {
            "tick": time.time(),
            "units": [
                {"id": "RedTarget", "side": "Red", "x": pos_t[0], "y": pos_t[1], "z": pos_t[2]},
                {"id": "BlueInterceptor", "side": "Blue", "x": pos_i[0], "y": pos_i[1], "z": pos_i[2]}
            ]
        }
        socketio.emit('state_update', state)
        
        socketio.sleep(0.1) # 10Hz (Slowed down for better viewing)

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    socketio.start_background_task(simulation_loop)
    print("Running Chase Demo on http://localhost:5000")
    socketio.run(app, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)
