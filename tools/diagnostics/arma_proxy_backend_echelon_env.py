#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import os
import socketserver
import sys
import threading
from dataclasses import dataclass
from typing import Any

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from python.testing.runtime import ensure_repo_imports


ensure_repo_imports()

from gym_envs.universal_env import UniversalEnv  # noqa: E402
from python.rl.control.scripted_stable_flight import ScriptedStableFlightController  # noqa: E402
from tools.diagnostics.arma_proxy_backend_stub import (  # noqa: E402
    DESTROYED_FLAG,
    ENGINE_ON_FLAG,
    LANDED_FLAG,
    HostFrame,
    ProxyState,
)


def _normalize_degrees(value: float) -> float:
    out = float(value) % 360.0
    return out + 360.0 if out < 0.0 else out


def _heading_from_horizontal(direction: tuple[float, float, float]) -> float:
    return _normalize_degrees(math.degrees(math.atan2(float(direction[0]), float(direction[1]))))


def _vector_add(
    lhs: tuple[float, float, float],
    rhs: tuple[float, float, float],
) -> tuple[float, float, float]:
    return (
        float(lhs[0] + rhs[0]),
        float(lhs[1] + rhs[1]),
        float(lhs[2] + rhs[2]),
    )


def _rotate_horizontal(
    vector: tuple[float, float, float],
    heading_offset_deg: float,
) -> tuple[float, float, float]:
    theta = math.radians(float(heading_offset_deg))
    cos_t = math.cos(theta)
    sin_t = math.sin(theta)
    return (
        float(vector[0] * cos_t + vector[1] * sin_t),
        float(-vector[0] * sin_t + vector[1] * cos_t),
        float(vector[2]),
    )


def _normalize_vector(vector: tuple[float, float, float]) -> tuple[float, float, float]:
    norm = math.sqrt(sum(float(v) * float(v) for v in vector))
    if norm <= 1e-9:
        return (1.0, 0.0, 0.0)
    return tuple(float(v) / norm for v in vector)


def _cross(
    lhs: tuple[float, float, float],
    rhs: tuple[float, float, float],
) -> tuple[float, float, float]:
    return (
        float(lhs[1] * rhs[2] - lhs[2] * rhs[1]),
        float(lhs[2] * rhs[0] - lhs[0] * rhs[2]),
        float(lhs[0] * rhs[1] - lhs[1] * rhs[0]),
    )


def _dot(
    lhs: tuple[float, float, float],
    rhs: tuple[float, float, float],
) -> float:
    return float(lhs[0] * rhs[0] + lhs[1] * rhs[1] + lhs[2] * rhs[2])


def heading_pitch_roll_to_dir_up(
    *,
    heading_deg: float,
    pitch_deg: float,
    roll_deg: float,
) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    heading = math.radians(float(heading_deg))
    pitch = math.radians(float(pitch_deg))
    roll = math.radians(float(roll_deg))

    direction = _normalize_vector(
        (
            math.sin(heading) * math.cos(pitch),
            math.cos(heading) * math.cos(pitch),
            math.sin(pitch),
        )
    )
    world_up = (0.0, 0.0, 1.0)
    forward_cross_up = _cross(direction, world_up)
    up = (
        world_up[0] * math.cos(roll)
        + forward_cross_up[0] * math.sin(roll)
        + direction[0] * _dot(direction, world_up) * (1.0 - math.cos(roll)),
        world_up[1] * math.cos(roll)
        + forward_cross_up[1] * math.sin(roll)
        + direction[1] * _dot(direction, world_up) * (1.0 - math.cos(roll)),
        world_up[2] * math.cos(roll)
        + forward_cross_up[2] * math.sin(roll)
        + direction[2] * _dot(direction, world_up) * (1.0 - math.cos(roll)),
    )
    return direction, _normalize_vector(up)


@dataclass(frozen=True)
class EchelonEnvConfig:
    host: str = "127.0.0.1"
    port: int = 8765
    scenario: str = os.path.join("scenarios", "stable_flight", "stable_flight.json")
    action_mode: str = "full"
    include_visual: bool = False
    include_proprio: bool = False
    mission_obs_mode: str = "basic"
    seed: int = 20260530
    log_requests: bool = False


class ScriptedStablePolicyAdapter:
    def __init__(self, env: UniversalEnv) -> None:
        self._controller = ScriptedStableFlightController(
            action_dim=int(env.action_space.shape[0]),
            dt=float(env.sim.get_time_step()),
        )

    def reset(self, obs: dict[str, Any]) -> None:
        self._controller.reset(obs)

    def act(self, obs: dict[str, Any]):
        return self._controller.step(obs)


@dataclass
class EchelonEnvSession:
    session_id: str
    world_name: str
    proxy_class: str
    env: UniversalEnv
    policy: ScriptedStablePolicyAdapter
    obs: dict[str, Any]
    reset_count: int
    accumulated_host_time_s: float = 0.0
    frame_id: int = 0
    anchor_offset_asl: tuple[float, float, float] | None = None
    heading_offset_deg: float | None = None
    last_context: str = ""
    last_host_frame: HostFrame | None = None


class ArmaProxyEchelonEnvBackend:
    def __init__(self, config: EchelonEnvConfig | None = None) -> None:
        self.config = config or EchelonEnvConfig()
        self._lock = threading.Lock()
        self._sessions: dict[str, EchelonEnvSession] = {}
        self._next_seed = int(self.config.seed)

    def handle_line(self, line: str, *, remote: str = "") -> str:
        request = str(line or "").strip()
        if not request:
            response = "err\tprotocol\tempty_request"
        else:
            with self._lock:
                response = self._dispatch_locked(request)
        if self.config.log_requests:
            prefix = f"{remote} " if remote else ""
            print(f"[arma_proxy_backend_echelon_env] {prefix}{request} -> {response}")
        return response

    def _dispatch_locked(self, request: str) -> str:
        parts = request.split("\t")
        command = parts[0]
        fields = parts[1:]

        if command == "ping":
            return "ack\tping"
        if command == "version":
            return "ack\tversion\tarma_proxy_backend_echelon_env 0.1.0"
        if command == "status":
            payload = {
                "session_count": len(self._sessions),
                "scenario": os.path.abspath(self.config.scenario),
                "sessions": sorted(self._sessions.keys()),
            }
            return f"status\t{json.dumps(payload, ensure_ascii=True, separators=(',', ':'))}"
        if command == "begin_session":
            return self._handle_begin_session(fields)
        if command == "host_frame":
            return self._handle_host_frame(fields)
        if command == "shutdown":
            return self._handle_shutdown(fields)
        return f"err\tprotocol\tunknown_command:{command}"

    def _handle_begin_session(self, fields: list[str]) -> str:
        if len(fields) != 3:
            return "err\tbegin_session\tinvalid_arity"
        session_id, world_name, proxy_class = fields

        if session_id in self._sessions:
            self._close_session(self._sessions.pop(session_id))

        env = UniversalEnv(
            self.config.scenario,
            include_visual=bool(self.config.include_visual),
            include_proprio=bool(self.config.include_proprio),
            action_mode=str(self.config.action_mode),
            mission_obs_mode=str(self.config.mission_obs_mode),
            runtime_compatibility_enabled=True,
            step_info_mode="full",
        )
        seed = self._next_seed
        self._next_seed += 1
        obs, _info = env.reset(seed=seed)
        policy = ScriptedStablePolicyAdapter(env)
        policy.reset(obs)
        self._sessions[session_id] = EchelonEnvSession(
            session_id=session_id,
            world_name=world_name,
            proxy_class=proxy_class,
            env=env,
            policy=policy,
            obs=obs,
            reset_count=1,
        )
        return "ack\tbegin_session"

    def _handle_host_frame(self, fields: list[str]) -> str:
        if len(fields) != 3:
            return "err\thost_frame\tinvalid_arity"
        session_id, context, payload = fields
        session = self._sessions.get(session_id)
        if session is None:
            return "err\thost_frame\tunknown_session"

        try:
            host_frame = HostFrame.from_sqf_payload(payload)
        except ValueError:
            return "err\thost_frame\tinvalid_payload"

        session.last_context = context
        session.last_host_frame = host_frame

        env = session.env
        sim_dt = float(env.sim.get_time_step())
        session.accumulated_host_time_s += max(float(host_frame.delta_time_s), 0.0)

        steps = 0
        while session.accumulated_host_time_s + 1.0e-9 >= sim_dt:
            self._step_session(session)
            session.accumulated_host_time_s -= sim_dt
            steps += 1
            if steps >= 8:
                break

        if session.anchor_offset_asl is None or session.heading_offset_deg is None:
            env_state = self._read_env_state(session)
            host_heading_deg = _heading_from_horizontal(host_frame.direction)
            session.anchor_offset_asl = (
                float(host_frame.position_asl[0] - env_state["position_asl"][0]),
                float(host_frame.position_asl[1] - env_state["position_asl"][1]),
                float(host_frame.position_asl[2] - env_state["position_asl"][2]),
            )
            session.heading_offset_deg = _normalize_degrees(host_heading_deg - float(env_state["heading_deg"]))

        proxy_state = self._build_proxy_state(session)
        return f"proxy_state\t{proxy_state.to_sqf_payload()}"

    def _handle_shutdown(self, fields: list[str]) -> str:
        if len(fields) != 1:
            return "err\tshutdown\tinvalid_arity"
        session_id = fields[0]
        session = self._sessions.pop(session_id, None)
        if session is not None:
            self._close_session(session)
        return "ack\tshutdown"

    def _step_session(self, session: EchelonEnvSession) -> None:
        action = session.policy.act(session.obs)
        obs, _reward, terminated, truncated, _info = session.env.step(action)
        session.obs = obs
        session.frame_id += 1
        if bool(terminated or truncated):
            obs, _ = session.env.reset(seed=self._next_seed)
            self._next_seed += 1
            session.policy.reset(obs)
            session.obs = obs
            session.reset_count += 1

    def _read_env_state(self, session: EchelonEnvSession) -> dict[str, Any]:
        sim = session.env.sim
        agent_id = int(session.env.agent_id)
        truth = sim.get_agent_observation(agent_id)
        inst = sim.get_instrument_state(agent_id)
        return {
            "position_asl": (float(truth.x), float(truth.y), float(truth.z)),
            "velocity_world": (float(truth.vx), float(truth.vy), float(truth.vz)),
            "heading_deg": float(getattr(inst, "heading", truth.heading)),
            "pitch_deg": float(getattr(inst, "pitch", truth.pitch)),
            "roll_deg": float(getattr(inst, "roll", truth.roll)),
            "throttle_01": float(getattr(inst, "throttle_pos", truth.throttle)),
            "gear_down_01": float(getattr(inst, "gear_pos", truth.gear_state)),
            "on_runway": bool(getattr(inst, "on_runway", False)),
            "health": float(truth.health),
        }

    def _build_proxy_state(self, session: EchelonEnvSession) -> ProxyState:
        env_state = self._read_env_state(session)
        anchor_offset = session.anchor_offset_asl or (0.0, 0.0, 0.0)
        heading_offset_deg = float(session.heading_offset_deg or 0.0)

        world_position = _vector_add(env_state["position_asl"], anchor_offset)
        world_velocity = _rotate_horizontal(env_state["velocity_world"], heading_offset_deg)
        world_heading = _normalize_degrees(float(env_state["heading_deg"]) + heading_offset_deg)
        direction, up = heading_pitch_roll_to_dir_up(
            heading_deg=world_heading,
            pitch_deg=float(env_state["pitch_deg"]),
            roll_deg=float(env_state["roll_deg"]),
        )

        state_flags = ENGINE_ON_FLAG
        if bool(env_state["on_runway"]):
            state_flags |= LANDED_FLAG
        if float(env_state["health"]) <= 0.0:
            state_flags |= DESTROYED_FLAG

        return ProxyState(
            frame_id=int(session.frame_id),
            position_asl=world_position,
            velocity_world=world_velocity,
            direction=direction,
            up=up,
            throttle_01=float(env_state["throttle_01"]),
            gear_down_01=float(env_state["gear_down_01"]),
            afterburner_01=0.0,
            state_flags=state_flags,
        )

    def _close_session(self, session: EchelonEnvSession) -> None:
        try:
            session.env.close()
        except Exception:
            pass


class ArmaProxyEchelonEnvRequestHandler(socketserver.StreamRequestHandler):
    def handle(self) -> None:
        remote = f"{self.client_address[0]}:{self.client_address[1]}"
        while True:
            raw = self.rfile.readline()
            if not raw:
                return
            request = raw.decode("utf-8", errors="replace").rstrip("\r\n")
            response = self.server.backend.handle_line(request, remote=remote)  # type: ignore[attr-defined]
            self.wfile.write((response + "\n").encode("utf-8"))
            self.wfile.flush()


class ArmaProxyEchelonEnvTcpServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True

    def __init__(
        self,
        server_address: tuple[str, int],
        backend: ArmaProxyEchelonEnvBackend,
    ) -> None:
        self.backend = backend
        super().__init__(server_address, ArmaProxyEchelonEnvRequestHandler)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run an Echelon env-backed TCP backend for the @EchelonProxy Arma bridge."
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument(
        "--scenario",
        default=os.path.join("scenarios", "stable_flight", "stable_flight.json"),
        help="Scenario path for the authoritative Echelon environment.",
    )
    parser.add_argument("--action-mode", default="full")
    parser.add_argument("--mission-obs-mode", default="basic")
    parser.add_argument("--include-visual", action="store_true")
    parser.add_argument("--include-proprio", action="store_true")
    parser.add_argument("--seed", type=int, default=20260530)
    parser.add_argument("--log-requests", action="store_true")
    return parser


def main() -> int:
    args = build_arg_parser().parse_args()
    config = EchelonEnvConfig(
        host=str(args.host),
        port=int(args.port),
        scenario=os.path.abspath(str(args.scenario)),
        action_mode=str(args.action_mode),
        include_visual=bool(args.include_visual),
        include_proprio=bool(args.include_proprio),
        mission_obs_mode=str(args.mission_obs_mode),
        seed=int(args.seed),
        log_requests=bool(args.log_requests),
    )
    backend = ArmaProxyEchelonEnvBackend(config)

    with ArmaProxyEchelonEnvTcpServer((config.host, config.port), backend) as server:
        bound_host, bound_port = server.server_address[:2]
        print(
            "[arma_proxy_backend_echelon_env] listening on "
            f"{bound_host}:{bound_port} "
            f"scenario={config.scenario} "
            f"action_mode={config.action_mode} "
            f"mission_obs_mode={config.mission_obs_mode}"
        )
        try:
            server.serve_forever(poll_interval=0.25)
        except KeyboardInterrupt:
            print("[arma_proxy_backend_echelon_env] interrupted, shutting down")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
