from __future__ import annotations

import argparse
import os

from flask import Flask, render_template, request
from flask_socketio import SocketIO

from examples.viz.app.session_manager import SessionManager


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Unified Visualization App")
    parser.add_argument("--scenario", type=str, default=None, help="Optional scenario to load on startup.")
    parser.add_argument("--profile", type=str, default=None, help="Optional viz profile to load on startup.")
    parser.add_argument("--model", type=str, help="Path to trained model (.zip SB3 PPO or .pt world-model checkpoint)")
    parser.add_argument(
        "--scripted",
        type=str,
        default=None,
        choices=["takeoff", "stable_flight", "landing_ils", "takeoff_cruise_landing"],
        help="Run a built-in scripted controller instead of a learned model.",
    )
    parser.add_argument("--pause_on_done", action="store_true")
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument(
        "--algo",
        type=str,
        default="auto",
        choices=["auto", "PPO", "AdaptiveKLPPO", "PPOAdaptiveKL", "PPO_AdaptiveKL"],
    )
    parser.add_argument("--train_config", type=str, default=None)
    parser.add_argument("--include_proprio", action="store_true")
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
    )
    parser.add_argument("--visual_downsample", type=int, default=None)
    parser.add_argument("--visual_update_interval", type=int, default=None)
    parser.add_argument(
        "--action_mode",
        type=str,
        default="auto",
        choices=["auto", "full", "takeoff2", "takeoff4"],
    )
    parser.add_argument("--fixed_action", type=str, default=None)
    parser.add_argument("--zero_randomization", action="store_true")
    return parser


def create_app(args: argparse.Namespace):
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    template_dir = os.path.join(base_dir, "web_viz/templates")
    static_dir = os.path.join(base_dir, "web_viz/static")
    async_mode = "threading" if os.name == "nt" else "eventlet"

    app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
    socketio = SocketIO(app, cors_allowed_origins="*", async_mode=async_mode)
    manager = SessionManager(socketio, default_args=args)

    def report_load_error(action: str, exc: Exception) -> None:
        message = f"{action}: {type(exc).__name__}: {exc}"
        print(f"[viz] {message}")
        socketio.emit("viz_error", {"message": message})
        manager.emit_status()

    @app.route("/")
    def index():
        return render_template("index.html")

    @socketio.on("connect")
    def handle_connect():
        print("Client Connected")
        manager.emit_status()
        current = manager.current()
        if current is not None:
            current.emit_cached_setup()

    @socketio.on("start_sim")
    def handle_start_sim():
        manager.start_current()

    @socketio.on("pause_sim")
    def handle_pause_sim():
        manager.pause_current()

    @socketio.on("resume_sim")
    def handle_resume_sim():
        manager.resume_current()

    @socketio.on("set_speed")
    def handle_set_speed(data):
        manager.set_speed(data)

    @socketio.on("viz_load_session")
    def handle_viz_load_session(data):
        scenario = ""
        profile = ""
        if isinstance(data, dict):
            scenario = str(data.get("scenario", "")).strip()
            profile = str(data.get("profile", "")).strip()
        try:
            if profile:
                manager.load_profile(profile)
                return
            if not scenario:
                return
            manager.clear_profile_selection()
            manager.load_session(scenario)
        except Exception as exc:
            report_load_error(f"load {profile or scenario}", exc)

    @socketio.on("viz_load_profile")
    def handle_viz_load_profile(data):
        profile = ""
        if isinstance(data, dict):
            profile = str(data.get("profile", "")).strip()
        if not profile:
            return
        try:
            manager.load_profile(profile)
        except Exception as exc:
            report_load_error(f"load profile {profile}", exc)

    @socketio.on("viz_load_asset_registry")
    def handle_viz_load_asset_registry(data):
        registry = ""
        if isinstance(data, dict):
            registry = str(data.get("asset_registry", "")).strip()
        if not registry:
            return
        try:
            manager.load_asset_registry_only(registry)
        except Exception as exc:
            report_load_error(f"load asset registry {registry}", exc)

    @socketio.on("viz_stop_session")
    def handle_viz_stop_session():
        manager.stop_current()

    @socketio.on("viz_reload_session")
    def handle_viz_reload_session(data=None):
        current = manager.current()
        scenario = ""
        profile = ""
        if isinstance(data, dict):
            scenario = str(data.get("scenario", "")).strip()
            profile = str(data.get("profile", "")).strip()
        try:
            if profile:
                manager.load_profile(profile)
                return
            current_profile = manager.current_profile
            if not scenario and isinstance(current_profile, dict):
                profile_path = str(current_profile.get("path", "")).strip()
                if profile_path:
                    manager.load_profile(profile_path)
                    return
            if not scenario and current is not None:
                scenario = current.scenario
            if not scenario:
                return
            manager.clear_profile_selection()
            manager.load_session(scenario)
        except Exception as exc:
            report_load_error(f"reload {profile or scenario}", exc)

    @app.get("/api/viz/scenarios")
    def list_scenarios():
        return {"scenarios": manager.list_scenarios()}

    @app.get("/api/viz/profiles")
    def list_profiles():
        return {"profiles": manager.list_profiles()}

    @app.get("/api/viz/asset_registries")
    def list_asset_registries():
        return {"asset_registries": manager.list_asset_registries()}

    @app.get("/api/viz/assets")
    def get_asset_registry():
        return {"asset_registry": manager.asset_registry}

    @app.get("/api/viz/scene_geometry")
    def get_scene_geometry():
        payload = manager.scene_geometry
        if not isinstance(payload, dict):
            return {"ok": False, "error": "no environment bundle loaded"}, 404
        return payload

    @app.get("/api/viz/status")
    def get_status():
        return manager.status_payload()

    @app.post("/api/viz/load")
    def load_via_http():
        payload = request.get_json(silent=True) or {}
        scenario = str(payload.get("scenario", "")).strip()
        if not scenario:
            return {"ok": False, "error": "missing scenario"}, 400
        manager.clear_profile_selection()
        manager.load_session(scenario)
        return {"ok": True, "status": manager.status_payload()}

    @app.post("/api/viz/load_profile")
    def load_profile_via_http():
        payload = request.get_json(silent=True) or {}
        profile = str(payload.get("profile", "")).strip()
        if not profile:
            return {"ok": False, "error": "missing profile"}, 400
        manager.load_profile(profile)
        return {"ok": True, "status": manager.status_payload()}

    return app, socketio, manager
