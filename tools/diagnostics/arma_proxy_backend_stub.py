#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
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

from python.runtime_bootstrap import ensure_repo_imports


ensure_repo_imports()


ENGINE_ON_FLAG = 1 << 0
DESTROYED_FLAG = 1 << 1
LANDED_FLAG = 1 << 2


def parse_sqf_simple_array(text: str) -> Any:
    return ast.literal_eval(text)


def serialize_sqf_simple_array(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, separators=(",", ":"))


def _as_float(value: Any, field_name: str) -> float:
    try:
        out = float(value)
    except Exception as exc:
        raise ValueError(f"{field_name} must be numeric") from exc
    if not math.isfinite(out):
        raise ValueError(f"{field_name} must be finite")
    return out


def _as_vector3(value: Any, field_name: str) -> tuple[float, float, float]:
    if not isinstance(value, (list, tuple)) or len(value) < 3:
        raise ValueError(f"{field_name} must be a 3-vector")
    return (
        _as_float(value[0], f"{field_name}[0]"),
        _as_float(value[1], f"{field_name}[1]"),
        _as_float(value[2], f"{field_name}[2]"),
    )


def _normalize_horizontal(
    vector: tuple[float, float, float],
    *,
    fallback: tuple[float, float, float] = (1.0, 0.0, 0.0),
) -> tuple[float, float, float]:
    magnitude = math.hypot(vector[0], vector[1])
    if magnitude <= 1e-6:
        return fallback
    return (vector[0] / magnitude, vector[1] / magnitude, 0.0)


@dataclass(frozen=True)
class HostFrame:
    protocol_version: int
    world_name: str
    mission_time_s: float
    delta_time_s: float
    terrain_height_asl: float
    position_asl: tuple[float, float, float]
    velocity_world: tuple[float, float, float]
    direction: tuple[float, float, float]
    up: tuple[float, float, float]

    @classmethod
    def from_sqf_payload(cls, payload_text: str) -> "HostFrame":
        payload = parse_sqf_simple_array(payload_text)
        if not isinstance(payload, (list, tuple)) or len(payload) < 9:
            raise ValueError("host_frame payload must contain 9 fields")
        return cls(
            protocol_version=int(payload[0]),
            world_name=str(payload[1]),
            mission_time_s=_as_float(payload[2], "mission_time_s"),
            delta_time_s=_as_float(payload[3], "delta_time_s"),
            terrain_height_asl=_as_float(payload[4], "terrain_height_asl"),
            position_asl=_as_vector3(payload[5], "position_asl"),
            velocity_world=_as_vector3(payload[6], "velocity_world"),
            direction=_normalize_horizontal(_as_vector3(payload[7], "direction")),
            up=_as_vector3(payload[8], "up"),
        )


@dataclass(frozen=True)
class ProxyState:
    frame_id: int
    position_asl: tuple[float, float, float]
    velocity_world: tuple[float, float, float]
    direction: tuple[float, float, float]
    up: tuple[float, float, float]
    throttle_01: float
    gear_down_01: float
    afterburner_01: float
    state_flags: int

    def to_sqf_payload(self) -> str:
        return serialize_sqf_simple_array(
            [
                int(self.frame_id),
                [float(v) for v in self.position_asl],
                [float(v) for v in self.velocity_world],
                [float(v) for v in self.direction],
                [float(v) for v in self.up],
                float(self.throttle_01),
                float(self.gear_down_01),
                float(self.afterburner_01),
                int(self.state_flags),
            ]
        )


@dataclass(frozen=True)
class StubConfig:
    host: str = "127.0.0.1"
    port: int = 8765
    start_position_asl: tuple[float, float, float] = (0.0, 0.0, 1200.0)
    speed_mps: float = 220.0
    turn_rate_deg_s: float = 0.0
    climb_rate_mps: float = 0.0
    throttle_01: float = 0.82
    gear_down_01: float = 0.0
    afterburner_01: float = 0.0
    bootstrap_from_host: bool = True
    log_requests: bool = False


@dataclass
class SessionState:
    session_id: str
    world_name: str
    proxy_class: str
    proxy_state: ProxyState
    heading_rad: float = 0.0
    bootstrapped: bool = False
    last_context: str = ""
    last_host_frame: HostFrame | None = None


class ArmaProxyBackendStub:
    def __init__(self, config: StubConfig | None = None) -> None:
        self.config = config or StubConfig()
        self._lock = threading.Lock()
        self._sessions: dict[str, SessionState] = {}

    def handle_line(self, line: str, *, remote: str = "") -> str:
        request = str(line or "").strip()
        if not request:
            response = "err\tprotocol\tempty_request"
        else:
            with self._lock:
                response = self._dispatch_locked(request)
        if self.config.log_requests:
            prefix = f"{remote} " if remote else ""
            print(f"[arma_proxy_backend_stub] {prefix}{request} -> {response}")
        return response

    def _dispatch_locked(self, request: str) -> str:
        parts = request.split("\t")
        command = parts[0]
        fields = parts[1:]

        if command == "ping":
            return "ack\tping"
        if command == "version":
            return "ack\tversion\tarma_proxy_backend_stub 0.1.0"
        if command == "status":
            payload = {
                "session_count": len(self._sessions),
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
        self._sessions[session_id] = SessionState(
            session_id=session_id,
            world_name=world_name,
            proxy_class=proxy_class,
            proxy_state=self._build_proxy_state(
                frame_id=0,
                position_asl=self.config.start_position_asl,
                heading_rad=0.0,
                terrain_height_asl=0.0,
            ),
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
        self._bootstrap_session_from_host(session, host_frame)
        dt = min(max(host_frame.delta_time_s, 0.01), 0.5)
        session.heading_rad += math.radians(self.config.turn_rate_deg_s) * dt
        session.proxy_state = self._build_proxy_state(
            frame_id=session.proxy_state.frame_id + 1,
            position_asl=self._advance_position(session.proxy_state.position_asl, session.heading_rad, dt),
            heading_rad=session.heading_rad,
            terrain_height_asl=host_frame.terrain_height_asl,
        )
        return f"proxy_state\t{session.proxy_state.to_sqf_payload()}"

    def _handle_shutdown(self, fields: list[str]) -> str:
        if len(fields) != 1:
            return "err\tshutdown\tinvalid_arity"
        session_id = fields[0]
        self._sessions.pop(session_id, None)
        return "ack\tshutdown"

    def _bootstrap_session_from_host(self, session: SessionState, host_frame: HostFrame) -> None:
        if session.bootstrapped:
            return

        start_position = self.config.start_position_asl
        heading_source = host_frame.velocity_world
        if math.hypot(heading_source[0], heading_source[1]) <= 1e-6:
            heading_source = host_frame.direction

        if self.config.bootstrap_from_host:
            host_x, host_y, host_z = host_frame.position_asl
            if abs(host_x) > 1.0 or abs(host_y) > 1.0 or abs(host_z) > 1.0:
                start_position = (
                    host_x,
                    host_y,
                    max(float(start_position[2]), float(host_z)),
                )
            session.heading_rad = math.atan2(heading_source[1], heading_source[0])

        session.proxy_state = self._build_proxy_state(
            frame_id=session.proxy_state.frame_id,
            position_asl=start_position,
            heading_rad=session.heading_rad,
            terrain_height_asl=host_frame.terrain_height_asl,
        )
        session.bootstrapped = True

    def _advance_position(
        self,
        position_asl: tuple[float, float, float],
        heading_rad: float,
        dt_s: float,
    ) -> tuple[float, float, float]:
        vx = self.config.speed_mps * math.cos(heading_rad)
        vy = self.config.speed_mps * math.sin(heading_rad)
        vz = self.config.climb_rate_mps
        return (
            float(position_asl[0] + vx * dt_s),
            float(position_asl[1] + vy * dt_s),
            float(max(0.0, position_asl[2] + vz * dt_s)),
        )

    def _build_proxy_state(
        self,
        *,
        frame_id: int,
        position_asl: tuple[float, float, float],
        heading_rad: float,
        terrain_height_asl: float,
    ) -> ProxyState:
        vx = self.config.speed_mps * math.cos(heading_rad)
        vy = self.config.speed_mps * math.sin(heading_rad)
        vz = self.config.climb_rate_mps
        direction = _normalize_horizontal((vx, vy, 0.0))
        state_flags = ENGINE_ON_FLAG
        if position_asl[2] <= terrain_height_asl + 1.0:
            state_flags |= LANDED_FLAG
        return ProxyState(
            frame_id=int(frame_id),
            position_asl=position_asl,
            velocity_world=(float(vx), float(vy), float(vz)),
            direction=direction,
            up=(0.0, 0.0, 1.0),
            throttle_01=float(self.config.throttle_01),
            gear_down_01=float(self.config.gear_down_01),
            afterburner_01=float(self.config.afterburner_01),
            state_flags=state_flags,
        )


class ArmaProxyRequestHandler(socketserver.StreamRequestHandler):
    def handle(self) -> None:
        remote = f"{self.client_address[0]}:{self.client_address[1]}"
        while True:
            raw = self.rfile.readline()
            if not raw:
                return
            request = raw.decode("utf-8", errors="replace").rstrip("\r\n")
            response = self.server.stub.handle_line(request, remote=remote)  # type: ignore[attr-defined]
            self.wfile.write((response + "\n").encode("utf-8"))
            self.wfile.flush()


class ArmaProxyBackendTcpServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True

    def __init__(self, server_address: tuple[str, int], stub: ArmaProxyBackendStub) -> None:
        self.stub = stub
        super().__init__(server_address, ArmaProxyRequestHandler)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a first-pass local TCP backend stub for the @EchelonProxy Arma bridge."
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument(
        "--start-position",
        nargs=3,
        type=float,
        metavar=("X", "Y", "Z"),
        default=(0.0, 0.0, 1200.0),
        help="Fallback proxy spawn position in ASL meters.",
    )
    parser.add_argument("--speed-mps", type=float, default=220.0)
    parser.add_argument("--turn-rate-deg-s", type=float, default=0.0)
    parser.add_argument("--climb-rate-mps", type=float, default=0.0)
    parser.add_argument("--throttle-01", type=float, default=0.82)
    parser.add_argument("--gear-down-01", type=float, default=0.0)
    parser.add_argument("--afterburner-01", type=float, default=0.0)
    parser.add_argument(
        "--no-bootstrap-from-host",
        action="store_true",
        help="Keep the configured start position instead of snapping to the first host frame.",
    )
    parser.add_argument(
        "--log-requests",
        action="store_true",
        help="Print each request/response pair to stdout.",
    )
    return parser


def main() -> int:
    args = build_arg_parser().parse_args()
    config = StubConfig(
        host=str(args.host),
        port=int(args.port),
        start_position_asl=tuple(float(v) for v in args.start_position),
        speed_mps=float(args.speed_mps),
        turn_rate_deg_s=float(args.turn_rate_deg_s),
        climb_rate_mps=float(args.climb_rate_mps),
        throttle_01=float(args.throttle_01),
        gear_down_01=float(args.gear_down_01),
        afterburner_01=float(args.afterburner_01),
        bootstrap_from_host=not bool(args.no_bootstrap_from_host),
        log_requests=bool(args.log_requests),
    )
    stub = ArmaProxyBackendStub(config)

    with ArmaProxyBackendTcpServer((config.host, config.port), stub) as server:
        bound_host, bound_port = server.server_address[:2]
        print(
            "[arma_proxy_backend_stub] listening on "
            f"{bound_host}:{bound_port} "
            f"start_position_asl={config.start_position_asl} "
            f"speed_mps={config.speed_mps:.1f} "
            f"turn_rate_deg_s={config.turn_rate_deg_s:.2f}"
        )
        try:
            server.serve_forever(poll_interval=0.25)
        except KeyboardInterrupt:
            print("[arma_proxy_backend_stub] interrupted, shutting down")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
