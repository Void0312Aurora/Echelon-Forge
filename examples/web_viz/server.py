import eventlet
eventlet.monkey_patch()

import sys
import os
import time
import threading
from flask import Flask, render_template
from flask_socketio import SocketIO, emit

# Ensure we can import cmo_py
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), "../../build")))
import cmo_py

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# Simulation State
kernel = cmo_py.SimulationKernel()
kernel.reset(42)

# Entities to track
target = kernel.spawn_unit(cmo_py.Side.Red, cmo_py.UnitType.Aircraft, 100, 100, 5000, 20, 0, 0) # Faster for demo
interceptor = kernel.spawn_unit(cmo_py.Side.Blue, cmo_py.UnitType.Aircraft, 0, 0, 5000, 0, 10, 0) # Moving North for demo

sim_running = True

def simulation_loop():
    """Run simulation in background and broadcast state."""
    global sim_running
    print("Simulation Loop Started")
    
    while sim_running:
        kernel.step()
        
        # Get data
        pos_t = kernel.get_unit_position(target)
        pos_i = kernel.get_unit_position(interceptor)
        
        state = {
            "tick": time.time(), # Just a timestamp
            "units": [
                {"id": "RedTarget", "side": "Red", "x": pos_t[0], "y": pos_t[1], "z": pos_t[2]},
                {"id": "BlueInterceptor", "side": "Blue", "x": pos_i[0], "y": pos_i[1], "z": pos_i[2]}
            ]
        }
        
        # Broadcast to all connected clients
        socketio.emit('state_update', state)
        
        socketio.sleep(0.1) # Yield to event loop

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    # Start simulation as a SocketIO background task (compatible with Eventlet)
    socketio.start_background_task(simulation_loop)
    
    print("Starting Web Server on port 5000...")
    socketio.run(app, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)
