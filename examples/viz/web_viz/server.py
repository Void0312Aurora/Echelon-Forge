import os
import time
import threading
from flask import Flask, render_template
from flask_socketio import SocketIO, emit

from python.runtime_bootstrap import ensure_repo_imports

ensure_repo_imports()
import ef_py

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Maintained facade state. The visualization example intentionally consumes
# the same batch setup/step/query surface as the production caller; raw kernel
# construction is diagnostics-only after P5-C.
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
facade = ef_py.RuntimeFacade(1)
database_path = os.path.join(repo_root, "examples", "config", "database")
if not facade.load_database(database_path):
    raise RuntimeError(f"failed to load runtime database: {database_path}")

setup = ef_py.BatchWorldSetupRequest()
setup.seeds = [42]
terrain = ef_py.WorldTerrainAssignment()
terrain.world_index = 0
terrain.terrain_type = "flat"
wind = ef_py.WorldWindAssignment()
wind.world_index = 0
setup.terrain_assignments = [terrain]
setup.wind_assignments = [wind]
setup.time_steps = [0.05]

target_request = ef_py.WorldSpawnRequest()
target_request.world_index = 0
target_request.side = ef_py.Side.Red
target_request.type_name = "F-16C_Block50"
target_request.entity_name = "RedTarget"
target_request.is_agent = True
target_request.x = 100.0
target_request.y = 100.0
target_request.z = 5000.0
target_request.heading = 90.0
target_request.vx = 20.0

interceptor_request = ef_py.WorldSpawnRequest()
interceptor_request.world_index = 0
interceptor_request.side = ef_py.Side.Blue
interceptor_request.type_name = "F-16C_Block50"
interceptor_request.entity_name = "BlueInterceptor"
interceptor_request.is_agent = True
interceptor_request.x = 0.0
interceptor_request.y = 0.0
interceptor_request.z = 5000.0
interceptor_request.heading = 0.0
interceptor_request.vy = 10.0
setup.spawn_requests = [target_request, interceptor_request]
setup_result = facade.apply_world_setup(setup)
target = int(setup_result.entity_ids[0])
interceptor = int(setup_result.entity_ids[1])


def _world_ref(entity_id):
    ref = ef_py.WorldEntityRef()
    ref.world_index = 0
    ref.entity_id = int(entity_id)
    return ref


target_ref = _world_ref(target)
interceptor_ref = _world_ref(interceptor)

sim_running = True

def simulation_loop():
    """Run simulation in background and broadcast state."""
    global sim_running
    print("Simulation Loop Started")
    
    while sim_running:
        facade.step_batch()
        
        # Get data through the maintained observation packet.
        observations = facade.get_agent_observations_batch([target_ref, interceptor_ref])
        pos_t = (float(observations[0].x), float(observations[0].y), float(observations[0].z))
        pos_i = (float(observations[1].x), float(observations[1].y), float(observations[1].z))
        
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
