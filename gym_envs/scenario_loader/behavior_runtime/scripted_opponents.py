from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from examples.agents import RedScriptedAgent
from python.rl.tasking.bridge import loader_owned_scripted_opponent_kernel_view


_RED_SCRIPTED_AGENT_ALIASES = frozenset({"red_scripted_agent", "red_scripted_baseline", "red_agent"})


def _resolve_scripted_target_id(loader: Any, scripted_cfg: dict[str, Any], blue_id: int) -> int:
    try:
        target_id = int(scripted_cfg.get("target_id", 0))
    except Exception:
        target_id = 0
    if target_id > 0:
        return target_id

    target_name = str(scripted_cfg.get("target_name", "")).strip()
    if target_name:
        resolved = getattr(loader, "entities", {}).get(target_name)
        if resolved is not None:
            return int(resolved)
    return int(blue_id) if blue_id > 0 else 0


def _build_red_scripted_agent(
    loader: Any,
    *,
    entity_id: int,
    scripted_cfg: dict[str, Any],
    target_id: int,
) -> RedScriptedAgent:
    altitude_hold_m = scripted_cfg.get("altitude_hold_m", None)
    return RedScriptedAgent(
        loader_owned_scripted_opponent_kernel_view(loader),
        int(entity_id),
        target_id=int(target_id) if int(target_id) > 0 else None,
        cruise_speed_mps=float(scripted_cfg.get("cruise_speed_mps", 220.0)),
        attack_speed_mps=float(scripted_cfg.get("attack_speed_mps", 260.0)),
        defensive_speed_mps=float(scripted_cfg.get("defensive_speed_mps", 290.0)),
        threat_range_m=float(scripted_cfg.get("threat_range_m", 9000.0)),
        merge_range_m=float(scripted_cfg.get("merge_range_m", 3500.0)),
        fire_range_m=float(scripted_cfg.get("fire_range_m", 6500.0)),
        altitude_hold_m=None if altitude_hold_m is None else float(altitude_hold_m),
        beam_offset_deg=float(scripted_cfg.get("beam_offset_deg", 85.0)),
    )


@dataclass(slots=True)
class ScriptedOpponentRuntime:
    controllers: dict[int, Any] = field(default_factory=dict)
    reports: dict[int, dict[str, Any]] = field(default_factory=dict)

    def reset(self) -> None:
        self.controllers = {}
        self.reports = {}

    def build_from_loader(self, loader: Any) -> None:
        self.reset()
        scenario_data = loader.scenario_data if isinstance(loader.scenario_data, dict) else {}
        entities_cfg = scenario_data.get("entities", [])
        if not isinstance(entities_cfg, list):
            return

        blue_id = int(getattr(loader, "agent_id", 0) or 0)
        for ent_cfg in entities_cfg:
            if not isinstance(ent_cfg, dict):
                continue
            scripted_cfg = ent_cfg.get("scripted_agent", None)
            if not isinstance(scripted_cfg, dict):
                continue
            script_name = str(scripted_cfg.get("name", "") or scripted_cfg.get("type", "")).strip().lower()
            if script_name not in _RED_SCRIPTED_AGENT_ALIASES:
                continue

            entity_name = str(ent_cfg.get("name", "")).strip()
            entity_id = getattr(loader, "entities", {}).get(entity_name)
            if entity_id is None:
                continue

            target_id = _resolve_scripted_target_id(loader, scripted_cfg, blue_id)
            controller = _build_red_scripted_agent(
                loader,
                entity_id=int(entity_id),
                scripted_cfg=scripted_cfg,
                target_id=target_id,
            )
            self.controllers[int(entity_id)] = controller
            self.reports[int(entity_id)] = {
                "active": False,
                "mode": "idle",
                "target_id": int(target_id or 0),
            }

    def step_all(self, sim_time: float) -> None:
        if not self.controllers:
            return
        for entity_id, controller in list(self.controllers.items()):
            if controller is None:
                continue
            try:
                report = controller.step(current_time=float(sim_time))
            except Exception as exc:
                report = {
                    "active": False,
                    "mode": "error",
                    "entity_id": int(entity_id),
                    "error": str(exc),
                }
            self.reports[int(entity_id)] = dict(report)


def make_scripted_opponent_runtime() -> ScriptedOpponentRuntime:
    return ScriptedOpponentRuntime()


def reset_scripted_opponents(loader: Any) -> None:
    runtime = getattr(loader, "_scripted_opponent_runtime", None)
    if runtime is None:
        runtime = make_scripted_opponent_runtime()
        loader._scripted_opponent_runtime = runtime
    runtime.reset()
    loader.scripted_opponents = runtime.controllers
    loader.scripted_opponent_reports = runtime.reports


def build_scripted_opponents(loader: Any) -> None:
    runtime = getattr(loader, "_scripted_opponent_runtime", None)
    if runtime is None:
        runtime = make_scripted_opponent_runtime()
        loader._scripted_opponent_runtime = runtime
    runtime.build_from_loader(loader)
    loader.scripted_opponents = runtime.controllers
    loader.scripted_opponent_reports = runtime.reports


def update_scripted_opponents(loader: Any, sim_time: float) -> None:
    runtime = getattr(loader, "_scripted_opponent_runtime", None)
    if runtime is None:
        return
    runtime.step_all(float(sim_time))
    loader.scripted_opponents = runtime.controllers
    loader.scripted_opponent_reports = runtime.reports
