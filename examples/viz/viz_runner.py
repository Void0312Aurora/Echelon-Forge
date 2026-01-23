import eventlet
eventlet.monkey_patch()

import sys
import os
import argparse
import time
import numpy as np
from flask import Flask, render_template
from flask_socketio import SocketIO
from stable_baselines3 import PPO

repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
build_dir = os.path.join(repo_root, "build")

# Prefer the locally built `ef_py` extension when present.
if os.path.isdir(build_dir) and any(fname.startswith("ef_py") and fname.endswith(".so") for fname in os.listdir(build_dir)):
    sys.path.insert(0, build_dir)
sys.path.insert(0, repo_root)

# Import ef_py before numpy/torch-heavy libs
import ef_py
# Import Universal Env
from gym_envs.universal_env import UniversalEnv
from python.models.transformer import TransformerExtractor

# Setup Web Server
base_dir = os.path.abspath(os.path.dirname(__file__))
# We will use the generic 'index.html' (2D) as default, but allow switching
template_dir = os.path.join(base_dir, "web_viz/templates")
static_dir = os.path.join(base_dir, "web_viz/static")

app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# Globals
simulation_running = False
simulation_paused = False
env = None
model = None
episode_return = 0.0
episode_return = 0.0
args = None
map_data = None

@socketio.on('connect')
def handle_connect():
    print("Client Connected")
    global map_data
    if map_data:
        print(f"Sending cached map data ({len(map_data['zones'])} zones) to new client")
        socketio.emit('map_setup', map_data)

@socketio.on('start_sim')
def handle_start_sim():
    global simulation_running, simulation_paused
    print("Start Signal Received")
    simulation_running = True
    simulation_paused = False

@socketio.on('pause_sim')
def handle_pause_sim():
    global simulation_paused
    print("Pause Signal Received")
    simulation_paused = True

@socketio.on('resume_sim')
def handle_resume_sim():
    global simulation_paused
    print("Resume Signal Received")
    simulation_paused = False

@app.route('/')
def index():
    # Universal 3D Viewer
    return render_template('index.html')

def simulation_loop():
    global simulation_running, simulation_paused, env, model, episode_return, args
    
    # Load Model if provided
    if args.model and os.path.exists(args.model):
        print(f"Loading PPO model from {args.model}...")
        try:
            model_path = args.model
            if model_path.endswith(".zip"):
                model_path = model_path[:-4]
            model = PPO.load(model_path, device="cpu")
        except Exception as e:
            print(f"Error loading model: {e}")
            model = None
    else:
        print("No model loaded. Running with random/noop actions.")
        model = None

    action_mode = args.action_mode
    if action_mode == "auto":
        if model is not None:
            act_space = getattr(model, "action_space", None)
            act_shape = getattr(act_space, "shape", None)
            act_dim = int(act_shape[0]) if act_shape and len(act_shape) == 1 else None
            if act_dim == 2:
                action_mode = "takeoff2"
            elif act_dim == 4:
                action_mode = "takeoff4"
            else:
                action_mode = "full"
        else:
            action_mode = "full"

    print(f"Initializing Universal Environment with scenario: {args.scenario} (action_mode={action_mode})")
    env = UniversalEnv(args.scenario, action_mode=action_mode, include_visual=True)

    print("Server ready. Waiting for start...")
    obs, _ = env.reset()
    episode_return = 0.0
    
    hz = 30
    dt_wall = 1.0 / float(hz)
    dt_wall = 1.0 / float(hz)
    dt_wall = 1.0 / float(hz)
    sim_time = 0.0
    
    # --- Map Setup ---
    global map_data
    zones = env.loader.scenario_data.get("environment", {}).get("zones", [])
    map_data = {"zones": zones}
    print(f"=" * 60)
    print(f"MAP DATA SENT TO VIZ:")
    for z in zones:
        print(f"  Zone '{z.get('name')}': x={z.get('x')}, y={z.get('y')}, "
              f"width={z.get('width')}, length={z.get('length')}, heading={z.get('heading')}")
    print(f"=" * 60)
    socketio.emit('map_setup', map_data)
    
    while True:
        try:
            eventlet.sleep(dt_wall)
            
            if not simulation_running:
                continue

            if simulation_paused:
                continue
                
            # Predict
            if model:
                # We need to map the env observation to what the model expects
                # UniversalEnv returns a Dict observation. SB3 PPO handles Dict if trained on it.
                action, _ = model.predict(obs, deterministic=True)
                if action.shape != env.action_space.shape:
                    raise ValueError(
                        f"Action shape mismatch: model produced {action.shape} but env expects {env.action_space.shape} "
                        f"(hint: set --action_mode to match the training action space)."
                    )
                if sim_time < 2.0:
                    print(f"Action: {action}")
            else:
                # No model: Do nothing (zeros)
                action = np.zeros(env.action_space.shape, dtype=np.float32)

            obs, reward, terminated, truncated, info = env.step(action)
            episode_return += float(reward)
            sim_time += env.sim.get_time_step() # Use internal sim step
            
            # --- Universal State Extraction ---
            # Instead of specific hardcoded fields, we extract all entities in the loader
            
            units_data = []
            
            # Helper to get safe unit data
            def get_unit_data(eid, name):
                if not env.sim.is_unit_active(eid):
                    return None
                    
                pos = env.sim.get_unit_position(eid) # list [x, y, z]
                hdg = env.sim.get_unit_heading(eid)
                # UniversalEnv helper or direct sim access for more details?
                # SimulationKernel doesn't expose generic "get_all_properties" easily in python 
                # without the specialized struct binding.
                # But 'get_agent_observation' returns a rich struct. 
                # Let's try to use basic info we have.
                
                # We need velocity/speed for viz
                # Currently C++ side: get_unit_velocity is not bound? 
                # We can check universal_env usage. It calls get_unit_position.
                # It calls get_agent_observation for THE agent.
                
                # Implementation Detail: 
                # Getting rich state for NON-agents might be limited in current bindings 
                # unless we use `get_detections` or similar.
                # However, for Visualization, we often want "Ground Truth".
                # Let's assume we can get basic Pos/Hdg.
                
                return {
                    "id": eid,
                    "name": name,
                    "side": "Blue", 
                    "type": "Aircraft" if "F16" in name or "Aircraft" in name else "Facility", 
                    "x": pos[0],
                    "y": pos[1],
                    # Physics Z is CG. Visual Model Origin is approx at wheels. 
                    # Subtract gear height (~2.0m) to align visuals.
                    "z": pos[2] - 2.0 if "Aircraft" in name or "F16" in name else pos[2],
                    "heading": hdg,
                    "pitch": 0.0, # TODO: Get Pitch/Roll if possible
                    "roll": 0.0,
                    "speed": 0.0, 
                    "hp": 100.0,
                    "max_hp": 100.0,
                }

            # Iterate ALL entities known to loader
            for name, eid in env.loader.entities.items():
                u = get_unit_data(eid, name)
                if u:
                    # Enrich with Agent data if it's the agent (has more info)
                    if eid == env.agent_id:
                        # DEBUG: Print position of agent to debug drift - FORCE FLUSH
                        # DEBUG: Print position of agent to debug drift - FORCE FLUSH
                        if sim_time < 5.0: 
                            raw = env.sim.get_agent_observation(eid)
                            print(f"Viz Frame T={sim_time:.2f} | {name} Pos: ({u['x']:.2f}, {u['y']:.2f}, {u['z']:.2f}) Hdg: {raw.heading:.1f} Thr: {raw.throttle:.2f}")
                            sys.stdout.flush()
                        u.update({
                            "speed": float(raw.speed),
                            "roll": float(raw.roll),
                            "throttle": float(raw.throttle),
                            "pitch": float(raw.pitch),
                            "hp": float(raw.health),
                            "side": "Blue" # Agent is usually Blue
                        })
                    
                    units_data.append(u)
            
            state = {
                "tick": sim_time,
                "units": units_data
            }
            
            socketio.emit('state_update', state)
            
            if terminated or truncated:
                print(f"Episode Done. Return: {episode_return:.2f}")
                obs, _ = env.reset()
                episode_return = 0.0
                
        except Exception as e:
            print(f"Viz Loop Error: {e}")
            import traceback
            traceback.print_exc()
            break

def main():
    global args, app
    parser = argparse.ArgumentParser(description="Universal Visualization Runner")
    parser.add_argument("--scenario", type=str, required=True, help="Path to scenario JSON")
    parser.add_argument("--model", type=str, help="Path to trained model zip")
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument(
        "--action_mode",
        type=str,
        default="auto",
        choices=["auto", "full", "takeoff2", "takeoff4"],
        help="Action space mode; use 'auto' to infer from the model action dimension.",
    )
    args = parser.parse_args()
    
    app.config['SECRET_KEY'] = 'universal_viz_secret'
    
    socketio.start_background_task(simulation_loop)
    print(f"Running Universal Viz on http://localhost:{args.port}")
    socketio.run(app, host='0.0.0.0', port=args.port, allow_unsafe_werkzeug=True)

if __name__ == '__main__':
    main()
