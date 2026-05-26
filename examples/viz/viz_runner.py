import eventlet

eventlet.monkey_patch()

import argparse
import os
import sys

from flask import Flask, render_template
from flask_socketio import SocketIO

repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

from examples.viz.runtime.viz_session import VizSession
from examples.viz.runtime.action_utils import normalize_fixed_action


base_dir = os.path.abspath(os.path.dirname(__file__))
template_dir = os.path.join(base_dir, "web_viz/templates")
static_dir = os.path.join(base_dir, "web_viz/static")

app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")

args = None
session = None


@socketio.on("connect")
def handle_connect():
    print("Client Connected")
    if session is not None:
        session.emit_cached_setup()


@socketio.on("start_sim")
def handle_start_sim():
    if session is not None:
        session.start()


@socketio.on("pause_sim")
def handle_pause_sim():
    if session is not None:
        session.pause()


@socketio.on("resume_sim")
def handle_resume_sim():
    if session is not None:
        session.resume()


@socketio.on("set_speed")
def handle_set_speed(data):
    if session is not None:
        session.set_speed(data)


@app.route("/")
def index():
    return render_template("index.html")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Universal Visualization Runner")
    parser.add_argument("--scenario", type=str, required=True, help="Path to scenario JSON")
    parser.add_argument("--model", type=str, help="Path to trained model (.zip SB3 PPO or .pt world-model checkpoint)")
    parser.add_argument(
        "--scripted",
        type=str,
        default=None,
        choices=["takeoff", "stable_flight", "landing_ils", "takeoff_cruise_landing"],
        help="Run a built-in scripted controller instead of a learned model.",
    )
    parser.add_argument(
        "--pause_on_done",
        action="store_true",
        help="Pause the simulation on terminal state instead of auto-resetting immediately.",
    )
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--seed", type=int, default=None, help="Deterministic env.reset seed for reproducible wind/yaw.")
    parser.add_argument(
        "--algo",
        type=str,
        default="auto",
        choices=["auto", "PPO", "AdaptiveKLPPO", "PPOAdaptiveKL", "PPO_AdaptiveKL"],
        help="Algorithm class used during training. 'auto' tries AdaptiveKLPPO first, then PPO.",
    )
    parser.add_argument(
        "--train_config",
        type=str,
        default=None,
        help="Optional training config JSON; if omitted, the runner will try train_config_backup.json next to the checkpoint.",
    )
    parser.add_argument(
        "--include_proprio",
        action="store_true",
        help="Include previous-action proprioception in observations. If omitted, the runner will infer it from the model when possible.",
    )
    parser.add_argument(
        "--mission_obs_mode",
        type=str,
        default=None,
        choices=[
            "basic",
            "nav_v1",
            "nav_v2",
            "nav_v2_formation_v1",
            "nav_v2_formation_role_v1",
            "nav_v2_cooperative_takeoff_v1",
            "naval_screen_station_v1",
        ],
        help="Mission observation format. If omitted, infer it from the model observation space when possible.",
    )
    parser.add_argument(
        "--visual_downsample",
        type=int,
        default=None,
        help="Visual downsample factor. If omitted, infer it from the model observation space when possible.",
    )
    parser.add_argument(
        "--visual_update_interval",
        type=int,
        default=None,
        help="Visual refresh interval used by the env. If omitted, use the training config when available.",
    )
    parser.add_argument(
        "--action_mode",
        type=str,
        default="auto",
        choices=["auto", "full", "takeoff2", "takeoff4"],
        help="Action space mode; use 'auto' to infer from the model action dimension.",
    )
    parser.add_argument(
        "--fixed_action",
        type=str,
        default=None,
        help="Comma-separated action vector to apply every step (overrides model), e.g. '0,0,0,1' for takeoff4.",
    )
    parser.add_argument(
        "--zero_randomization",
        action="store_true",
        help="Override world yaw and wind randomization to zero for deterministic debugging.",
    )
    return parser


def main():
    global args, session
    parser = build_arg_parser()
    args = parser.parse_args()

    if args.fixed_action is not None:
        args.fixed_action = normalize_fixed_action(args.fixed_action, name="--fixed_action")

    app.config["SECRET_KEY"] = "universal_viz_secret"
    session = VizSession(args, socketio)

    socketio.start_background_task(session.run_loop)
    print(f"Running Universal Viz on http://localhost:{args.port}")
    socketio.run(app, host="0.0.0.0", port=args.port, allow_unsafe_werkzeug=True)


if __name__ == "__main__":
    main()
