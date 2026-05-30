from __future__ import annotations

import argparse
import asyncio
import copy
import json
import math
import os
import tempfile
import sys
import time
from dataclasses import dataclass, field
from typing import Any

import numpy as np
from websockets.asyncio.server import ServerConnection, serve


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from gym_envs.universal_env import UniversalEnv
from python.scenario_compiler import invalidate_runtime_waypoint_cache, materialize_runtime_waypoint_cache
from python.rl.tasking.leader_tasking import (
    infer_recovery_approach_type,
    infer_recovery_base_id,
    infer_recovery_runway_id,
)
from python.rl.control.mission_defs import (
    COMMAND_NAME_TO_CODE,
    CRUISE_PHASE_NAMES,
    LANDING_PHASE_NAMES,
    TAKEOFF_PHASE_NAMES,
    normalize_phase_name,
)


DEFAULT_SCENARIO = "scenarios/takeoff/takeoff.json"
DEFAULT_MODE = "prototype_takeoff_patrol_rtb"
DEFAULT_ROUTE = "/game"
DEFAULT_C2_TASK_SEQUENCE = [
    "TASK_SCRAMBLE",
    "TASK_CAP",
    "TASK_RTB",
    "TASK_RECOVER_LAND",
]
COMMAND_CODE_TO_NAME = {int(v): str(k).upper() for k, v in COMMAND_NAME_TO_CODE.items()}
PLAYER_ROLE_ALIASES = {
    "lead": "Lead",
    "wing": "Wing",
    "wingman": "Wing",
}
LEAD_COMMAND_CAP = "lead_cap"
LEAD_COMMAND_RTB = "lead_rtb"
LEAD_COMMAND_RECOVER = "lead_recover"
LEAD_COMMAND_LABELS = {
    LEAD_COMMAND_CAP: "Resume CAP",
    LEAD_COMMAND_RTB: "Return To Base",
    LEAD_COMMAND_RECOVER: "Recover And Land",
}


def _json_default(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.floating,)):
        return float(value)
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.bool_,)):
        return bool(value)
    return str(value)


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        out = float(value)
    except Exception:
        return float(default)
    if not math.isfinite(out):
        return float(default)
    return out


def _safe_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return bool(default)
    try:
        return bool(value)
    except Exception:
        return bool(default)


def _normalize_scenario_path(scenario_path: str) -> str:
    path = str(scenario_path or "").strip()
    if not path:
        path = DEFAULT_SCENARIO
    if os.path.isabs(path):
        return path
    return os.path.abspath(os.path.join(REPO_ROOT, path))


def _normalize_player_role(value: Any) -> str:
    raw = str(value or "").strip().lower()
    return PLAYER_ROLE_ALIASES.get(raw, "Lead")


def _role_label_from_member(member: Any, *, fallback_name: str = "") -> str:
    formation_role = str(getattr(member, "formation_role_id", "") or "").strip()
    role_code = int(getattr(member, "role_code", 0) or 0) if member is not None else 0
    if formation_role == "ElementLead" or role_code == 21:
        return "Lead"
    if formation_role == "Wingman" or role_code == 22:
        return "Wing"
    name = str(getattr(member, "entity_name", "") or fallback_name).strip()
    if name:
        return name
    return "Unknown"


def _session_temp_dir() -> str:
    path = os.path.join(REPO_ROOT, "game", ".session_cache")
    os.makedirs(path, exist_ok=True)
    return path


def _build_session_scenario_variant(
    scenario_path: str,
    *,
    player_entity_name: str | None,
    session_id: str,
) -> tuple[str, dict[str, Any], bool]:
    with open(scenario_path, "r", encoding="utf-8") as f:
        scenario_data = json.load(f)
    if not isinstance(scenario_data, dict):
        raise ValueError(f"Scenario at {scenario_path} is not a JSON object.")

    entities_raw = scenario_data.get("entities", [])
    if not isinstance(entities_raw, list):
        return scenario_path, scenario_data, False

    entities = [copy.deepcopy(entity) for entity in entities_raw]
    agent_entities = [
        entity for entity in entities
        if isinstance(entity, dict) and bool(entity.get("is_agent", False))
    ]
    if len(agent_entities) <= 1:
        return scenario_path, scenario_data, False

    target_name = str(player_entity_name or "").strip()
    target_entity: dict[str, Any] | None = None
    if target_name:
        for entity in agent_entities:
            if str(entity.get("name", "") or "").strip() == target_name:
                target_entity = entity
                break
    if target_entity is None:
        return scenario_path, scenario_data, False
    if agent_entities and agent_entities[0] is target_entity:
        return scenario_path, scenario_data, False

    reordered_agents = [target_entity] + [entity for entity in agent_entities if entity is not target_entity]
    reordered_entities: list[Any] = []
    agent_index = 0
    for entity in entities:
        if isinstance(entity, dict) and bool(entity.get("is_agent", False)):
            reordered_entities.append(reordered_agents[agent_index])
            agent_index += 1
        else:
            reordered_entities.append(entity)

    scenario_variant = copy.deepcopy(scenario_data)
    scenario_variant["entities"] = reordered_entities
    variant_dir = tempfile.mkdtemp(prefix=f"{session_id}-", dir=_session_temp_dir())
    variant_path = os.path.join(variant_dir, os.path.basename(scenario_path))
    with open(variant_path, "w", encoding="utf-8") as f:
        json.dump(scenario_variant, f, ensure_ascii=True, indent=2)
        f.write("\n")
    return variant_path, scenario_variant, True


def _message(message_type: str, **payload: Any) -> str:
    body = {"type": message_type, **payload}
    return json.dumps(body, ensure_ascii=True, default=_json_default)


def _pretty_label(name: str | None) -> str:
    text = str(name or "").strip()
    if not text:
        return "--"
    if text.startswith("TASK_"):
        text = text[5:]
    return text.replace("_", " ").title()


def _infer_c2_task(phase_name: str | None, *, command_code: int | None = None) -> str:
    phase = normalize_phase_name(phase_name)
    if phase == "rtb":
        return "TASK_RTB"
    if phase in TAKEOFF_PHASE_NAMES:
        return "TASK_SCRAMBLE"
    if phase in LANDING_PHASE_NAMES:
        return "TASK_RECOVER_LAND"
    if phase in CRUISE_PHASE_NAMES:
        return "TASK_CAP"
    try:
        if int(command_code) == 4:
            return "TASK_RECOVER_LAND"
        if int(command_code) == 3:
            return "TASK_CAP"
        if int(command_code) == 1:
            return "TASK_SCRAMBLE"
    except Exception:
        pass
    return "TASK_IDLE"


def _format_reward_terms(reward_terms: dict[str, Any] | None, *, limit: int = 6) -> list[dict[str, Any]]:
    if not isinstance(reward_terms, dict) or not reward_terms:
        return []
    items: list[tuple[str, float]] = []
    for key, value in reward_terms.items():
        try:
            items.append((str(key), float(value)))
        except Exception:
            continue
    items.sort(key=lambda kv: abs(kv[1]), reverse=True)
    return [{"name": key, "value": float(value)} for key, value in items[: max(1, int(limit))]]


def _mission_command_name(command_code: int) -> str:
    return COMMAND_CODE_TO_NAME.get(int(command_code), f"CODE_{int(command_code)}")


@dataclass
class LocalGameSession:
    scenario_path: str
    mission_label: str = DEFAULT_MODE
    session_id: str = "local-0001"
    player_slot: str = "player_1"
    requested_player_role: str = "Lead"
    requested_player_entity_name: str | None = None
    action_mode: str = "full"
    mission_obs_mode: str = "nav_v2"
    step_info_mode: str = "terminal"
    env: UniversalEnv | None = None
    loaded_scenario_path: str | None = None
    loaded_scenario_is_variant: bool = False
    loaded_scenario_data: dict[str, Any] | None = None
    last_obs: dict[str, Any] | None = None
    last_info: dict[str, Any] = field(default_factory=dict)
    last_reward: float = 0.0
    total_reward: float = 0.0
    terminated: bool = False
    truncated: bool = False
    seed: int = 1
    created_at_s: float = field(default_factory=time.time)
    frame_counter: int = 0
    current_action: np.ndarray | None = None
    control_state: dict[str, Any] = field(default_factory=dict)
    control_source: str = "neutral"
    mission_transition_log: list[dict[str, Any]] = field(default_factory=list)
    last_phase_name: str = ""
    last_c2_task: str = ""
    player_entity_name: str = ""
    player_role_label: str = "Lead"
    lead_authority: bool = True
    last_lead_command: dict[str, Any] = field(default_factory=dict)

    def start(self) -> None:
        if self.env is not None:
            self.close()
        effective_role = _normalize_player_role(self.requested_player_role)
        if not self.requested_player_entity_name:
            self.requested_player_entity_name = effective_role
        self.loaded_scenario_path, self.loaded_scenario_data, self.loaded_scenario_is_variant = _build_session_scenario_variant(
            self.scenario_path,
            player_entity_name=self.requested_player_entity_name,
            session_id=self.session_id,
        )
        self.env = UniversalEnv(
            self.loaded_scenario_path or self.scenario_path,
            include_visual=False,
            include_proprio=False,
            action_mode=self.action_mode,
            mission_obs_mode=self.mission_obs_mode,
            step_info_mode=self.step_info_mode,
        )
        self.last_obs, _info = self.env.reset(seed=self.seed)
        self.last_info = {}
        self.last_reward = 0.0
        self.total_reward = 0.0
        self.terminated = False
        self.truncated = False
        self.frame_counter = 0
        self.current_action = self.neutral_action()
        self.control_state = self._action_to_control_state(self.current_action)
        self.control_source = "neutral"
        self.mission_transition_log = []
        self.last_phase_name = ""
        self.last_c2_task = ""
        self.player_entity_name = ""
        self.player_role_label = effective_role
        self.lead_authority = effective_role == "Lead"
        self.last_lead_command = {}
        self._update_player_binding()
        self._capture_mission_status(0.0)

    def close(self) -> None:
        if self.env is not None:
            try:
                self.env.close()
            except Exception:
                pass
        self.env = None
        self.last_obs = None
        self.last_info = {}
        loaded_variant = self.loaded_scenario_path
        self.loaded_scenario_path = None
        self.loaded_scenario_data = None
        if self.loaded_scenario_is_variant and loaded_variant:
            try:
                variant_dir = os.path.dirname(loaded_variant)
                if os.path.isfile(loaded_variant):
                    os.remove(loaded_variant)
                if os.path.isdir(variant_dir):
                    os.rmdir(variant_dir)
            except Exception:
                pass
        self.loaded_scenario_is_variant = False

    def step(self, action: np.ndarray) -> dict[str, Any]:
        if self.env is None:
            raise RuntimeError("Local game session is not started.")
        obs, reward, terminated, truncated, info = self.env.step(action)
        self.last_obs = obs
        self.last_info = dict(info or {})
        self.last_reward = float(reward)
        self.total_reward += float(reward)
        self.terminated = bool(terminated)
        self.truncated = bool(truncated)
        self.frame_counter += 1
        return self.snapshot()

    def step_current_action(self) -> dict[str, Any]:
        action = self.current_action if self.current_action is not None else self.neutral_action()
        return self.step(np.asarray(action, dtype=np.float32))

    def neutral_action(self) -> np.ndarray:
        if self.env is None:
            return np.zeros((17,), dtype=np.float32)
        low = np.asarray(self.env.action_space.low, dtype=np.float32)
        high = np.asarray(self.env.action_space.high, dtype=np.float32)
        action = np.zeros(self.env.action_space.shape, dtype=np.float32)
        if action.size >= 4:
            action[3] = np.clip(0.82, low[3], high[3])
        if action.size >= 5:
            action[4] = np.clip(1.0, low[4], high[4])
        return action

    def action_from_client_payload(self, payload: dict[str, Any]) -> np.ndarray:
        if self.env is None:
            raise RuntimeError("Local game session is not started.")
        action = self.neutral_action()
        axes = payload.get("axes", {}) if isinstance(payload.get("axes", {}), dict) else {}
        toggles = payload.get("toggles", {}) if isinstance(payload.get("toggles", {}), dict) else {}
        if action.size >= 1:
            action[0] = float(np.clip(_safe_float(axes.get("pitch", 0.0)), -1.0, 1.0))
        if action.size >= 2:
            action[1] = float(np.clip(_safe_float(axes.get("roll", 0.0)), -1.0, 1.0))
        if action.size >= 3:
            action[2] = float(np.clip(_safe_float(axes.get("yaw", 0.0)), -1.0, 1.0))
        if action.size >= 4:
            action[3] = float(np.clip(_safe_float(axes.get("throttle", action[3])), 0.0, 1.0))
        if action.size >= 5:
            action[4] = 1.0 if _safe_bool(toggles.get("gear", True), True) else 0.0
        if action.size >= 8:
            brake = 1.0 if _safe_bool(toggles.get("brake", False), False) else 0.0
            action[7] = brake
        if action.size >= 9:
            action[8] = action[7]
        if action.size >= 14:
            action[13] = 1.0 if _safe_bool(toggles.get("master_arm", False), False) else 0.0
        if action.size >= 15:
            action[14] = 1.0 if _safe_bool(toggles.get("fire_weapon", False), False) else 0.0
        if action.size >= 16:
            action[15] = 1.0 if _safe_bool(toggles.get("fire_gun", False), False) else 0.0
        return action.astype(np.float32, copy=False)

    def set_player_input(self, payload: dict[str, Any]) -> None:
        action = self.action_from_client_payload(payload)
        self.current_action = action
        self.control_state = self._action_to_control_state(action)
        self.control_source = "player"

    def _current_inst(self) -> Any:
        if self.env is None:
            return None
        inst = getattr(self.env, "_last_inst", None)
        if inst is not None:
            return inst
        loader = getattr(self.env, "loader", None)
        sim = getattr(self.env, "sim", None)
        agent_id = getattr(loader, "agent_id", None) if loader is not None else None
        if sim is None or agent_id is None:
            return None
        try:
            return sim.get_instrument_state(int(agent_id))
        except Exception:
            return None

    def _lead_command_options(self) -> list[dict[str, Any]]:
        route_available = False
        on_ground = False
        if self.env is not None:
            loader = getattr(self.env, "loader", None)
            route_available = bool(list(getattr(loader, "waypoints", []) or [])) if loader is not None else False
            inst = self._current_inst()
            if inst is not None:
                alt_agl_m = _safe_float(getattr(inst, "alt_radar", 0.0), 0.0)
                ground_speed_mps = _safe_float(getattr(inst, "ground_speed", 0.0), 0.0)
                on_ground = alt_agl_m <= 5.0 and ground_speed_mps <= 45.0

        options = [
            {
                "id": LEAD_COMMAND_CAP,
                "label": LEAD_COMMAND_LABELS[LEAD_COMMAND_CAP],
                "enabled": bool(route_available),
                "reason": "" if route_available else "No active route/waypoints are available for CAP routing.",
            },
            {
                "id": LEAD_COMMAND_RTB,
                "label": LEAD_COMMAND_LABELS[LEAD_COMMAND_RTB],
                "enabled": bool(route_available),
                "reason": "" if route_available else "No active route/waypoints are available for RTB routing.",
            },
            {
                "id": LEAD_COMMAND_RECOVER,
                "label": LEAD_COMMAND_LABELS[LEAD_COMMAND_RECOVER],
                "enabled": bool(not on_ground),
                "reason": "" if not on_ground else "Recover is only available after departure / airborne transition.",
            },
        ]
        return options

    def _update_player_binding(self) -> None:
        if self.env is None:
            return
        loader = getattr(self.env, "loader", None)
        if loader is None:
            return
        agent_id = getattr(loader, "agent_id", None)
        member = None
        if agent_id is not None:
            try:
                member = loader.get_active_roster_member(entity_id=int(agent_id))
            except Exception:
                member = None
        if member is None:
            try:
                entities = getattr(loader, "entities", {}) or {}
                for entity_name, entity_id in dict(entities).items():
                    if int(entity_id) == int(agent_id):
                        self.player_entity_name = str(entity_name)
                        break
            except Exception:
                pass
        else:
            self.player_entity_name = str(getattr(member, "entity_name", "") or self.player_entity_name or "")
            self.player_role_label = _role_label_from_member(member, fallback_name=self.player_entity_name)
            self.lead_authority = self.player_role_label == "Lead"
        if not self.player_entity_name:
            self.player_entity_name = str(self.requested_player_entity_name or self.requested_player_role or "Ownship")
        if not self.player_role_label:
            self.player_role_label = _normalize_player_role(self.requested_player_role)
        self.lead_authority = bool(self.player_role_label == "Lead")

    def issue_lead_command(self, command_name: str) -> dict[str, Any]:
        if self.env is None:
            raise RuntimeError("Local game session is not started.")
        if not bool(self.lead_authority):
            raise PermissionError("Lead commands are only available when the player occupies the lead aircraft slot.")

        loader = getattr(self.env, "loader", None)
        sim = getattr(self.env, "sim", None)
        if loader is None or sim is None:
            raise RuntimeError("Command runtime is unavailable.")

        command_key = str(command_name or "").strip().lower()
        available_options = {str(item.get("id", "")): item for item in self._lead_command_options()}
        option_meta = available_options.get(command_key, {})
        if option_meta and not bool(option_meta.get("enabled", True)):
            raise ValueError(str(option_meta.get("reason", "This lead command is not currently available.")))
        mission_cmd = getattr(loader, "mission_cmd", None)
        if not isinstance(mission_cmd, dict):
            raise RuntimeError("Mission command state is unavailable.")

        changed: dict[str, Any] = {}
        previous = {
            "c2_task": str(getattr(loader, "c2_task_name", "") or ""),
            "phase_name": str(getattr(loader, "mission_phase_name", "") or ""),
            "command_code": int(mission_cmd.get("command_code", 0) or 0),
            "command_name": _mission_command_name(int(mission_cmd.get("command_code", 0) or 0)),
        }
        next_task_name = previous["c2_task"] or _infer_c2_task(previous["phase_name"], command_code=previous["command_code"])

        if command_key == LEAD_COMMAND_CAP:
            mission_cmd["command_code"] = int(COMMAND_NAME_TO_CODE["route"])
            next_task_name = "TASK_CAP"
            if list(getattr(loader, "waypoints", []) or []):
                route_ref_id = int(mission_cmd.get("route_ref_id", 0) or 0)
                if route_ref_id <= 0:
                    materialize_runtime_waypoint_cache(mission_cmd)
                changed["waypoint_preserved"] = bool(list(getattr(loader, "waypoints", []) or []))
            loader.mission_phase_name = "transit_to_station"
        elif command_key == LEAD_COMMAND_RTB:
            mission_cmd["command_code"] = int(COMMAND_NAME_TO_CODE["route"])
            next_task_name = "TASK_RTB"
            loader.mission_phase_name = "rtb"
            changed["rtb_mode"] = True
        elif command_key == LEAD_COMMAND_RECOVER:
            mission_cmd["command_code"] = int(COMMAND_NAME_TO_CODE["landing"])
            mission_cmd["recovery_base_id"] = int(infer_recovery_base_id(loader, task=getattr(loader, "task_order", None)))
            mission_cmd["recovery_runway_id"] = int(infer_recovery_runway_id(loader, task=getattr(loader, "task_order", None)))
            recovery_approach = infer_recovery_approach_type(loader, task=getattr(loader, "task_order", None))
            try:
                mission_cmd["recovery_approach_type"] = int(recovery_approach)
            except Exception:
                mission_cmd["recovery_approach_type"] = recovery_approach
            mission_cmd["target_heading"] = float(mission_cmd.get("target_heading", 0.0))
            next_task_name = "TASK_RECOVER_LAND"
            loader.mission_phase_name = "rtb"
            changed["recovery_base_id"] = int(mission_cmd.get("recovery_base_id", 0) or 0)
            changed["recovery_runway_id"] = int(mission_cmd.get("recovery_runway_id", 0) or 0)
        else:
            raise ValueError(f"Unknown lead command: {command_name!r}")

        loader.scenario_data["mission_command"] = mission_cmd
        loader.c2_task_name = str(next_task_name)
        try:
            loader.c2_task_id = int(DEFAULT_C2_TASK_SEQUENCE.index(next_task_name) + 1)
        except ValueError:
            loader.c2_task_id = 0
        loader.c2_transitioned = True
        loader.c2_transition_reason = f"manual_{command_key}"
        loader.c2_last_update_s = float(self.env.steps) * float(sim.get_time_step())
        loader.c2_report_valid = True
        loader.c2_report_reason = "manual_command"

        if command_key != LEAD_COMMAND_CAP:
            invalidate_runtime_waypoint_cache(mission_cmd)
            materialize_runtime_waypoint_cache(mission_cmd)
        if command_key == LEAD_COMMAND_RECOVER:
            loader.waypoints = []
            loader.waypoint_idx = 0
            loader._waypoint_prev_dist_m = None
            loader.waypoint_total_route_length_m = 0.0
            loader._cached_route_ref_id = None
            loader.post_waypoint_transition = None
            loader._rebuild_spatial_geometry()

        try:
            loader._sync_kernel_mission_command()
        except Exception:
            pass
        try:
            loader._update_command_chain(loader.c2_last_update_s, sync_to_kernel=True)
        except Exception:
            try:
                loader._sync_kernel_command_chain()
            except Exception:
                pass

        applied = {
            "command": command_key,
            "label": LEAD_COMMAND_LABELS.get(command_key, command_key),
            "issued_at_s": float(loader.c2_last_update_s),
            "previous": previous,
            "current": {
                "c2_task": str(getattr(loader, "c2_task_name", "") or next_task_name),
                "phase_name": str(getattr(loader, "mission_phase_name", "") or ""),
                "command_code": int(mission_cmd.get("command_code", 0) or 0),
                "command_name": _mission_command_name(int(mission_cmd.get("command_code", 0) or 0)),
            },
            "changed": changed,
        }
        self.last_lead_command = dict(applied)
        return applied

    def _action_to_control_state(self, action: np.ndarray) -> dict[str, Any]:
        arr = np.asarray(action, dtype=np.float32).reshape(-1)
        out = {
            "pitch": _safe_float(arr[0] if arr.size >= 1 else 0.0),
            "roll": _safe_float(arr[1] if arr.size >= 2 else 0.0),
            "yaw": _safe_float(arr[2] if arr.size >= 3 else 0.0),
            "throttle": _safe_float(arr[3] if arr.size >= 4 else 0.0),
            "gear": bool((arr[4] if arr.size >= 5 else 1.0) > 0.5),
            "brake": bool(max(arr[7] if arr.size >= 8 else 0.0, arr[8] if arr.size >= 9 else 0.0) > 0.5),
            "master_arm": bool((arr[13] if arr.size >= 14 else 0.0) > 0.5),
            "fire_weapon": bool((arr[14] if arr.size >= 15 else 0.0) > 0.5),
            "fire_gun": bool((arr[15] if arr.size >= 16 else 0.0) > 0.5),
        }
        return out

    def snapshot(self) -> dict[str, Any]:
        if self.env is None:
            return {
                "session_id": self.session_id,
                "mission_label": self.mission_label,
                "player_slot": self.player_slot,
                "requested_player_role": self.requested_player_role,
                "player_entity_name": self.player_entity_name or self.requested_player_entity_name or "",
                "player_role_label": self.player_role_label,
                "lead_authority": bool(self.lead_authority),
                "sim_time_s": 0.0,
                "paused": False,
                "session_state": "inactive",
            }

        inst = getattr(self.env, "_last_inst", None)
        truth = getattr(self.env, "_last_truth", None)
        loader = getattr(self.env, "loader", None)
        sim = getattr(self.env, "sim", None)
        dt = float(sim.get_time_step()) if sim is not None else 0.05
        sim_time = float(self.env.steps) * dt
        mission_status = self.last_info.get("mission_status", None)
        mission_status_list = (
            np.asarray(mission_status, dtype=np.float32).reshape(-1).tolist()
            if mission_status is not None
            else []
        )
        phase_name = str(getattr(loader, "mission_phase_name", "") or "") if loader is not None else ""
        self._update_player_binding()
        ownship_name = self.player_entity_name or ""
        scenario_entities_by_name: dict[str, dict[str, Any]] = {}
        if loader is not None:
            try:
                scenario_entities = loader.scenario_data.get("entities", [])
                for entity in scenario_entities:
                    if not isinstance(entity, dict):
                        continue
                    entity_name = str(entity.get("name", "") or "")
                    if entity_name:
                        scenario_entities_by_name[entity_name] = entity
                    if not ownship_name and bool(entity.get("is_agent", False)):
                        ownship_name = entity_name
            except Exception:
                ownship_name = ""
                scenario_entities_by_name = {}

        objective = {
            "phase": phase_name or "unknown",
            "task": phase_name or "unknown",
            "success": bool(self.last_info.get("termination_reason") in ("success", "success_waypoint", "success_objective")),
            "mission_status": mission_status_list,
        }
        mission_status_payload = self._capture_mission_status(sim_time)
        reward_terms_raw = dict(self.last_info.get("reward_terms", {}) or {})

        ownship = {
            "name": ownship_name or "Ownship",
            "alt_m": _safe_float(getattr(inst, "alt_baro", 0.0) if inst is not None else 0.0),
            "alt_agl_m": _safe_float(getattr(inst, "alt_radar", 0.0) if inst is not None else 0.0),
            "ias_mps": _safe_float(getattr(inst, "ias", 0.0) if inst is not None else 0.0),
            "heading_deg": _safe_float(getattr(inst, "heading", 0.0) if inst is not None else 0.0),
            "pitch_deg": _safe_float(getattr(inst, "pitch", 0.0) if inst is not None else 0.0),
            "roll_deg": _safe_float(getattr(inst, "roll", 0.0) if inst is not None else 0.0),
            "x_m": _safe_float(getattr(truth, "x", 0.0) if truth is not None else 0.0),
            "y_m": _safe_float(getattr(truth, "y", 0.0) if truth is not None else 0.0),
            "z_m": _safe_float(getattr(truth, "z", 0.0) if truth is not None else 0.0),
        }
        units = self._collect_units_for_snapshot(
            loader=loader,
            sim=sim,
            scenario_entities_by_name=scenario_entities_by_name,
            ownship=ownship,
            truth=truth,
        )

        return {
            "session_id": self.session_id,
            "mission_label": self.mission_label,
            "player_slot": self.player_slot,
            "requested_player_role": self.requested_player_role,
            "player_entity_name": ownship_name or self.player_entity_name or "Ownship",
            "player_role_label": self.player_role_label,
            "lead_authority": bool(self.lead_authority),
            "sim_time_s": sim_time,
            "paused": False,
            "session_state": "terminated" if (self.terminated or self.truncated) else "running",
            "ownship": ownship,
            "units": units,
            "objective": objective,
            "mission_status": mission_status_payload,
            "reward": {
                "last": float(self.last_reward),
                "total": float(self.total_reward),
                "terms": reward_terms_raw,
                "summary": _format_reward_terms(reward_terms_raw),
            },
            "control_state": dict(self.control_state or {}),
            "control_source": str(self.control_source or "neutral"),
            "termination": {
                "terminated": bool(self.terminated),
                "truncated": bool(self.truncated),
                "reason": str(self.last_info.get("termination_reason", "running")),
                "success": bool(self.last_info.get("termination_reason") in ("success", "success_waypoint", "success_objective")),
            },
            "frame_counter": int(self.frame_counter),
        }

    def _capture_mission_status(self, sim_time_now: float) -> dict[str, Any] | None:
        if self.env is None:
            return None
        loader = getattr(self.env, "loader", None)
        if loader is None:
            return None

        mission_cmd = getattr(loader, "mission_cmd", {}) or {}
        phase_name = normalize_phase_name(getattr(loader, "mission_phase_name", "idle"))
        try:
            command_code = int(mission_cmd.get("command_code", 0))
        except Exception:
            command_code = 0

        c2_task = str(getattr(loader, "c2_task_name", "") or "").strip().upper()
        if not c2_task:
            c2_task = _infer_c2_task(phase_name, command_code=command_code)

        seq = list(DEFAULT_C2_TASK_SEQUENCE)
        try:
            meta = getattr(loader, "scenario_data", {}).get("meta", {})
            custom_seq = meta.get("demo_task_sequence", None) if isinstance(meta, dict) else None
            if isinstance(custom_seq, list) and custom_seq:
                seq = [str(x).strip() for x in custom_seq if str(x).strip()]
        except Exception:
            pass

        try:
            sequence_index = seq.index(c2_task)
        except ValueError:
            sequence_index = -1

        waypoints = list(getattr(loader, "waypoints", []) or [])
        waypoint_total = int(len(waypoints))
        waypoint_idx = int(getattr(loader, "waypoint_idx", 0) or 0)
        active_waypoint = 0
        if waypoint_total > 0:
            active_waypoint = max(1, min(waypoint_total, waypoint_idx + 1))

        command_options = self._lead_command_options() if bool(self.lead_authority) else []
        status = {
            "sim_time_s": float(sim_time_now),
            "c2_task": str(c2_task),
            "c2_task_label": _pretty_label(c2_task),
            "phase_name": phase_name or "idle",
            "phase_label": _pretty_label(phase_name),
            "player_entity_name": str(self.player_entity_name or self.requested_player_entity_name or ""),
            "player_role_label": str(self.player_role_label or _normalize_player_role(self.requested_player_role)),
            "lead_authority": bool(self.lead_authority),
            "command_code": int(command_code),
            "command_name": COMMAND_CODE_TO_NAME.get(int(command_code), f"CODE_{int(command_code)}"),
            "waypoint_index": int(waypoint_idx),
            "waypoint_total": int(waypoint_total),
            "active_waypoint": int(active_waypoint),
            "task_sequence": seq,
            "task_sequence_index": int(sequence_index),
            "lead_commands_available": bool(self.lead_authority),
            "lead_command_options": command_options,
            "last_lead_command": dict(self.last_lead_command or {}),
            "history": list(self.mission_transition_log),
        }

        if phase_name != self.last_phase_name or c2_task != self.last_c2_task:
            self.mission_transition_log.append(
                {
                    "time_s": float(sim_time_now),
                    "phase_name": phase_name or "idle",
                    "phase_label": str(status.get("phase_label", "--")),
                    "c2_task": c2_task or "TASK_IDLE",
                    "c2_task_label": str(status.get("c2_task_label", "--")),
                    "command_code": int(status.get("command_code", 0)),
                    "waypoint_text": (
                        f"{int(status.get('active_waypoint', 0))}/{int(status.get('waypoint_total', 0))}"
                        if int(status.get("waypoint_total", 0)) > 0
                        else "--"
                    ),
                }
            )
            self.mission_transition_log = self.mission_transition_log[-8:]
            self.last_phase_name = phase_name
            self.last_c2_task = c2_task
            status["history"] = list(self.mission_transition_log)
        return status

    def _collect_units_for_snapshot(
        self,
        *,
        loader: Any,
        sim: Any,
        scenario_entities_by_name: dict[str, dict[str, Any]],
        ownship: dict[str, Any],
        truth: Any,
    ) -> list[dict[str, Any]]:
        ownship_unit = {
            "id": self.player_slot,
            "name": ownship["name"],
            "type": "Aircraft",
            "side": "Blue",
            "player": True,
            "role_label": self.player_role_label,
            "lead_authority": bool(self.lead_authority),
            "x": ownship["x_m"],
            "y": ownship["y_m"],
            "z": ownship["z_m"],
            "speed": _safe_float(getattr(truth, "speed", 0.0) if truth is not None else 0.0),
            "ias": ownship["ias_mps"],
            "heading": ownship["heading_deg"],
            "pitch": ownship["pitch_deg"],
            "roll": ownship["roll_deg"],
            "throttle": _safe_float((self.control_state or {}).get("throttle", 0.0)),
        }
        if loader is None or sim is None:
            return [ownship_unit]

        scenario_name_by_id: dict[int, str] = {}
        loader_entities = getattr(loader, "entities", {}) or {}
        if isinstance(loader_entities, dict):
            for entity_name, entity_id in loader_entities.items():
                try:
                    scenario_name_by_id[int(entity_id)] = str(entity_name)
                except Exception:
                    continue

        units: list[dict[str, Any]] = []
        appended_player = False
        try:
            sim_units = list(sim.get_all_units() or [])
        except Exception:
            sim_units = []

        for sim_unit in sim_units:
            try:
                unit_id = int(getattr(sim_unit, "id", -1))
            except Exception:
                continue
            if unit_id < 0:
                continue
            try:
                if not bool(sim.is_unit_active(unit_id)):
                    continue
            except Exception:
                continue

            unit_name = scenario_name_by_id.get(unit_id, f"unit_{unit_id}")
            cfg = scenario_entities_by_name.get(unit_name, {})
            cfg_type = str(cfg.get("type", "") or "")
            sim_type = getattr(sim_unit, "type", "")
            raw_type = str(sim_type if sim_type is not None else cfg_type).strip()
            display_type = cfg_type or (raw_type if not raw_type.isdigit() else "Unit")
            sim_side = getattr(sim_unit, "side", "")
            side = str(cfg.get("side", sim_side if sim_side is not None else "Neutral") or "Neutral")
            is_player = unit_name == ownship["name"]
            is_aircraft = self._looks_like_aircraft(display_type or raw_type, unit_name)

            try:
                unit_truth = sim.get_agent_observation(unit_id) if is_aircraft else None
            except Exception:
                unit_truth = None
            try:
                unit_inst = sim.get_instrument_state(unit_id) if is_aircraft else None
            except Exception:
                unit_inst = None

            unit_payload = {
                "id": self.player_slot if is_player else str(unit_id),
                "name": unit_name,
                "type": "Aircraft" if is_aircraft else display_type,
                "side": side,
                "player": is_player,
                "role_label": self.player_role_label if is_player else "",
                "lead_authority": bool(self.lead_authority) if is_player else False,
                "x": _safe_float(getattr(sim_unit, "x", 0.0)),
                "y": _safe_float(getattr(sim_unit, "y", 0.0)),
                "z": _safe_float(getattr(sim_unit, "z", 0.0)),
                "speed": _safe_float(getattr(unit_truth, "speed", 0.0) if unit_truth is not None else 0.0),
                "ias": _safe_float(
                    getattr(unit_inst, "ias", getattr(unit_truth, "speed", 0.0))
                    if unit_inst is not None or unit_truth is not None
                    else 0.0
                ),
                "heading": _safe_float(getattr(sim_unit, "heading", 0.0)),
                "pitch": _safe_float(getattr(unit_truth, "pitch", 0.0) if unit_truth is not None else 0.0),
                "roll": _safe_float(getattr(unit_truth, "roll", 0.0) if unit_truth is not None else 0.0),
                "throttle": _safe_float(
                    (self.control_state or {}).get("throttle", 0.0)
                    if is_player
                    else getattr(unit_truth, "throttle", 0.0) if unit_truth is not None else 0.0
                ),
                "hp": _safe_float(getattr(unit_truth, "health", sim.get_unit_health(unit_id)) if unit_truth is not None else sim.get_unit_health(unit_id)),
            }
            units.append(unit_payload)
            if is_player:
                appended_player = True

        if not appended_player:
            units.insert(0, ownship_unit)
        return units

    def _looks_like_aircraft(self, raw_type: str, unit_name: str) -> bool:
        type_upper = str(raw_type or "").upper()
        name_upper = str(unit_name or "").upper()
        return (
            "F-16" in type_upper
            or "F16" in type_upper
            or "AIRCRAFT" in type_upper
            or "F-16" in name_upper
            or "F16" in name_upper
            or "AIRCRAFT" in name_upper
        )

    def map_setup_payload(self) -> dict[str, Any]:
        if self.env is None:
            return {"type": "map_setup", "zones": [], "terrain_type": "unknown"}
        scenario_data = getattr(self.env.loader, "scenario_data", {}) or {}
        environment = scenario_data.get("environment", {}) if isinstance(scenario_data, dict) else {}
        environment = environment if isinstance(environment, dict) else {}
        zones_raw = list(environment.get("zones", []) or [])
        zones: list[dict[str, Any]] = []
        for zone in zones_raw:
            if not isinstance(zone, dict):
                continue
            zones.append(
                {
                    "name": str(zone.get("name", "") or ""),
                    "x": _safe_float(zone.get("x", 0.0)),
                    "y": _safe_float(zone.get("y", 0.0)),
                    "width": max(1.0, _safe_float(zone.get("width", 1.0), 1.0)),
                    "length": max(1.0, _safe_float(zone.get("length", 1.0), 1.0)),
                    "heading": _safe_float(zone.get("heading", 0.0)),
                    "surface": str(zone.get("surface", "") or ""),
                }
            )
        return {
            "type": "map_setup",
            "terrain_type": str(environment.get("terrain_type", "flat") or "flat"),
            "zones": zones,
        }

    def nav_setup_payload(self) -> dict[str, Any]:
        if self.env is None:
            return {"type": "nav_setup", "markers": []}
        loader = self.env.loader
        markers: list[dict[str, Any]] = []
        for idx, waypoint in enumerate(list(getattr(loader, "waypoints", []) or [])):
            if not isinstance(waypoint, dict):
                continue
            markers.append(
                {
                    "index": int(idx),
                    "x": _safe_float(waypoint.get("x", 0.0)),
                    "y": _safe_float(waypoint.get("y", 0.0)),
                    "z": _safe_float(waypoint.get("z", waypoint.get("altitude_m", 0.0))),
                    "radius_m": max(1.0, _safe_float(waypoint.get("radius_m", 1000.0), 1000.0)),
                    "altitude_m": _safe_float(waypoint.get("altitude_m", waypoint.get("z", 0.0))),
                    "speed_mps": _safe_float(waypoint.get("speed_mps", 0.0)),
                    "waypoint_mode": str(waypoint.get("waypoint_mode", "flyby") or "flyby"),
                }
            )
        return {
            "type": "nav_setup",
            "markers": markers,
        }


class GameBridgeServer:
    def __init__(self, *, host: str, port: int, route: str, tick_hz: float, default_scenario: str) -> None:
        self.host = str(host)
        self.port = int(port)
        self.route = str(route)
        self.tick_hz = max(1.0, float(tick_hz))
        self.default_scenario = _normalize_scenario_path(default_scenario)
        self._session: LocalGameSession | None = None
        self._active_connection: ServerConnection | None = None
        self._session_lock = asyncio.Lock()

    async def run(self) -> None:
        async with serve(self._handler, self.host, self.port):
            print(f"[game-backend] listening on ws://{self.host}:{self.port}{self.route}")
            await asyncio.Future()

    async def _handler(self, websocket: ServerConnection) -> None:
        path = getattr(getattr(websocket, "request", None), "path", "")
        if path != self.route:
            await websocket.send(
                _message(
                    "state_event",
                    event="invalid_route",
                    payload={"expected": self.route, "received": path},
                )
            )
            await websocket.close(code=1008, reason="invalid route")
            return

        async with self._session_lock:
            if self._active_connection is not None:
                await websocket.send(
                    _message(
                        "state_event",
                        event="session_busy",
                        payload={"message": "Only one active local game client is supported right now."},
                    )
                )
                await websocket.close(code=1013, reason="session busy")
                return
            self._active_connection = websocket

        tick_task = asyncio.create_task(self._tick_loop(websocket))
        try:
            await websocket.send(
                _message(
                    "hello",
                    backend="cmo_game_bridge",
                    protocol_version=1,
                    features=["local_session", "state_snapshot", "state_event", "client_input", "map_setup", "nav_setup"],
                )
            )
            async for raw_message in websocket:
                await self._handle_message(websocket, raw_message)
        finally:
            tick_task.cancel()
            try:
                await tick_task
            except asyncio.CancelledError:
                pass
            async with self._session_lock:
                if self._active_connection is websocket:
                    self._active_connection = None

    async def _handle_message(self, websocket: ServerConnection, raw_message: str) -> None:
        try:
            message = json.loads(raw_message)
        except json.JSONDecodeError as exc:
            await websocket.send(
                _message(
                    "state_event",
                    event="bad_json",
                    payload={"error": str(exc)},
                )
            )
            return

        if not isinstance(message, dict):
            await websocket.send(
                _message(
                    "state_event",
                    event="bad_message_type",
                    payload={"message": "Expected a JSON object."},
                )
            )
            return

        msg_type = str(message.get("type", "")).strip()
        if msg_type == "game_command":
            await self._handle_game_command(websocket, message)
            return
        if msg_type == "client_input":
            await self._handle_client_input(websocket, message)
            return

        await websocket.send(
            _message(
                "state_event",
                event="unknown_message_type",
                payload={"type": msg_type},
            )
        )

    async def _handle_game_command(self, websocket: ServerConnection, message: dict[str, Any]) -> None:
        command = str(message.get("command", "")).strip()
        payload = message.get("payload", {})
        payload = payload if isinstance(payload, dict) else {}

        if command == "start_local_session":
            scenario = _normalize_scenario_path(str(payload.get("scenario", self.default_scenario)))
            mode = str(payload.get("mode", DEFAULT_MODE) or DEFAULT_MODE)
            player_role = _normalize_player_role(payload.get("player_role", "Lead"))
            await self._start_local_session(
                websocket,
                scenario_path=scenario,
                mission_label=mode,
                player_role=player_role,
            )
            return

        if command == "restart_local_session":
            player_role = str(payload.get("player_role", "") or "").strip()
            await self._restart_local_session(websocket, requested_player_role=player_role)
            return

        if command == "load_mission_profile":
            profile = str(payload.get("profile", DEFAULT_MODE) or DEFAULT_MODE)
            await websocket.send(
                _message(
                    "state_event",
                    event="mission_profile_selected",
                    payload={"profile": profile},
                )
            )
            return

        if command == "issue_lead_command":
            await self._issue_lead_command(websocket, command_name=str(payload.get("lead_command", "") or ""))
            return

        await websocket.send(
            _message(
                "state_event",
                event="unknown_game_command",
                payload={"command": command},
            )
        )

    async def _start_local_session(
        self,
        websocket: ServerConnection,
        *,
        scenario_path: str,
        mission_label: str,
        player_role: str,
    ) -> None:
        async with self._session_lock:
            if self._session is not None:
                self._session.close()
            self._session = LocalGameSession(
                scenario_path=scenario_path,
                mission_label=mission_label,
                session_id=f"local-{int(time.time())}",
                requested_player_role=player_role,
                requested_player_entity_name=player_role,
            )
            self._session.start()
            map_setup = self._session.map_setup_payload()
            nav_setup = self._session.nav_setup_payload()
            snapshot = self._session.snapshot()

        await websocket.send(
            _message(
                "state_event",
                event="local_session_started",
                payload={
                    "session_id": snapshot["session_id"],
                    "scenario": scenario_path,
                    "mission_label": mission_label,
                    "requested_player_role": player_role,
                    "player_entity_name": snapshot.get("player_entity_name", ""),
                    "player_role_label": snapshot.get("player_role_label", player_role),
                    "lead_authority": bool(snapshot.get("lead_authority", False)),
                },
            )
        )
        await websocket.send(_message("map_setup", **{k: v for k, v in map_setup.items() if k != "type"}))
        await websocket.send(_message("nav_setup", **{k: v for k, v in nav_setup.items() if k != "type"}))
        await websocket.send(_message("state_snapshot", **snapshot))

    async def _restart_local_session(
        self,
        websocket: ServerConnection,
        *,
        requested_player_role: str = "",
    ) -> None:
        async with self._session_lock:
            if self._session is None:
                await websocket.send(
                    _message(
                        "state_event",
                        event="no_active_session",
                        payload={"message": "Start a local session before restarting."},
                    )
                )
                return
            scenario_path = str(self._session.scenario_path)
            mission_label = str(self._session.mission_label)
            player_role = _normalize_player_role(requested_player_role or self._session.requested_player_role)
        await self._start_local_session(
            websocket,
            scenario_path=scenario_path,
            mission_label=mission_label,
            player_role=player_role,
        )

    async def _handle_client_input(self, websocket: ServerConnection, message: dict[str, Any]) -> None:
        payload = message.get("payload", message)
        payload = payload if isinstance(payload, dict) else {}
        async with self._session_lock:
            if self._session is None:
                await websocket.send(
                    _message(
                        "state_event",
                        event="no_active_session",
                        payload={"message": "Start a local session before sending player input."},
                    )
                )
                return
            self._session.set_player_input(payload)
            snapshot = self._session.snapshot()

        await websocket.send(
            _message(
                "state_event",
                event="player_input_applied",
                payload={
                    "session_id": snapshot.get("session_id"),
                    "control_state": snapshot.get("control_state", {}),
                },
            )
        )
        await websocket.send(_message("state_snapshot", **snapshot))

    async def _issue_lead_command(self, websocket: ServerConnection, *, command_name: str) -> None:
        async with self._session_lock:
            if self._session is None:
                await websocket.send(
                    _message(
                        "state_event",
                        event="no_active_session",
                        payload={"message": "Start a local session before issuing lead commands."},
                    )
                )
                return
            try:
                applied = self._session.issue_lead_command(command_name)
            except PermissionError as exc:
                await websocket.send(
                    _message(
                        "state_event",
                        event="lead_command_rejected",
                        payload={"command": command_name, "reason": str(exc)},
                    )
                )
                return
            except Exception as exc:
                await websocket.send(
                    _message(
                        "state_event",
                        event="lead_command_failed",
                        payload={"command": command_name, "reason": str(exc)},
                    )
                )
                return
            snapshot = self._session.snapshot()
            nav_setup = self._session.nav_setup_payload()

        await websocket.send(
            _message(
                "state_event",
                event="lead_command_applied",
                payload=applied,
            )
        )
        await websocket.send(_message("nav_setup", **{k: v for k, v in nav_setup.items() if k != "type"}))
        await websocket.send(_message("state_snapshot", **snapshot))

    async def _tick_loop(self, websocket: ServerConnection) -> None:
        period = 1.0 / self.tick_hz
        while True:
            await asyncio.sleep(period)
            async with self._session_lock:
                session = self._session
                if session is None or session.env is None:
                    continue
                if session.terminated or session.truncated:
                    continue
                snapshot = session.step_current_action()
                terminated = bool(snapshot.get("termination", {}).get("terminated", False))
                truncated = bool(snapshot.get("termination", {}).get("truncated", False))
                term_reason = str(snapshot.get("termination", {}).get("reason", "running"))

            await websocket.send(_message("state_snapshot", **snapshot))
            if terminated or truncated:
                await websocket.send(
                    _message(
                        "state_event",
                        event="session_terminal",
                        payload={
                            "reason": term_reason,
                            "success": bool(snapshot.get("termination", {}).get("success", False)),
                            "reward_total": float(snapshot.get("reward", {}).get("total", 0.0)),
                            "reward_summary": list(snapshot.get("reward", {}).get("summary", [])),
                            "mission_status": snapshot.get("mission_status", {}),
                            "player_entity_name": snapshot.get("player_entity_name", ""),
                            "player_role_label": snapshot.get("player_role_label", ""),
                            "lead_authority": bool(snapshot.get("lead_authority", False)),
                            "restart_available": True,
                        },
                    )
                )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Local authoritative backend bridge for the isolated Godot game branch."
    )
    parser.add_argument("--host", default="127.0.0.1", help="Bind host for the local backend server.")
    parser.add_argument("--port", type=int, default=8765, help="Bind port for the local backend server.")
    parser.add_argument("--route", default=DEFAULT_ROUTE, help="WebSocket route expected by the Godot client.")
    parser.add_argument(
        "--tick_hz",
        type=float,
        default=20.0,
        help="Authoritative backend snapshot/step frequency while a local session is running.",
    )
    parser.add_argument(
        "--scenario",
        default=DEFAULT_SCENARIO,
        help="Default scenario path used when the client starts a local session without overriding it.",
    )
    return parser


async def _async_main(args: argparse.Namespace) -> int:
    server = GameBridgeServer(
        host=str(args.host),
        port=int(args.port),
        route=str(args.route),
        tick_hz=float(args.tick_hz),
        default_scenario=str(args.scenario),
    )
    await server.run()
    return 0


def main() -> int:
    args = build_arg_parser().parse_args()
    try:
        return asyncio.run(_async_main(args))
    except KeyboardInterrupt:
        print("\n[game-backend] shutdown requested")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
