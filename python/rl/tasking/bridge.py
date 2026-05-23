from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from typing import Any

import ef_py


TASKING_TRUTH_READ_BLOCKER = (
    "Missing maintained tasking observation seam: add a bridge/facade-owned "
    "`loader.get_policy_agent_observation(agent_id)` replacement for raw "
    "simulation observation access."
)
TASKING_INSTRUMENT_READ_BLOCKER = (
    "Missing maintained tasking instrument seam: add a bridge/facade-owned "
    "`loader.get_policy_instrument_state(agent_id)` replacement for raw "
    "simulation instrument access."
)


class _ProfileModuleProxy:
    def __init__(self, module_name: str):
        self._module_name = str(module_name)

    def _module(self):
        return import_module(f"{__package__}.{self._module_name}")

    def __getattr__(self, name: str) -> Any:
        return getattr(self._module(), name)

    def __repr__(self) -> str:
        return f"<tasking-profile-proxy {self._module_name}>"


_air = _ProfileModuleProxy("air_adapter")
_ground = _ProfileModuleProxy("ground_adapter")
_naval = _ProfileModuleProxy("naval_adapter")


@dataclass(frozen=True)
class MissionCommandView:
    payload: dict[str, Any]

    def get(self, field_name: str, default: Any = None) -> Any:
        return self.payload.get(field_name, default)

    def int_field(self, field_name: str, default: int = 0) -> int:
        try:
            return int(self.payload.get(field_name, default))
        except Exception:
            return int(default)

    def float_field(self, field_name: str, default: float = 0.0) -> float:
        try:
            return float(self.payload.get(field_name, default))
        except Exception:
            return float(default)

    def bool_field(self, field_name: str, default: bool = False) -> bool:
        raw = self.payload.get(field_name, default)
        if isinstance(raw, bool):
            return raw
        if isinstance(raw, (int, float)):
            return bool(raw)
        if isinstance(raw, str):
            text = raw.strip().lower()
            if text in {"1", "true", "yes", "on"}:
                return True
            if text in {"0", "false", "no", "off", ""}:
                return False
        return bool(default)

    def text_field(self, field_name: str, default: str = "") -> str:
        raw = self.payload.get(field_name, default)
        return str(default if raw is None else raw)


class LoaderOwnedRawSimCompatibilityFacade:
    """Compatibility-only quarantine around loader-owned raw simulation access."""

    def __init__(self, loader: Any):
        self._loader = loader

    def _sim(self) -> Any:
        return getattr(self._loader, "sim", None)

    def require_sim(self, seam_name: str = "loader-owned compatibility seam") -> Any:
        sim = self._sim()
        if sim is None:
            raise RuntimeError(f"{seam_name} requires loader.sim")
        return sim

    def _method(self, method_name: str) -> Any:
        return getattr(self._sim(), method_name, None)

    def supports(self, method_name: str) -> bool:
        return callable(self._method(method_name))

    def call_optional(self, method_name: str, *args: Any, default: Any = None) -> Any:
        method = self._method(method_name)
        if not callable(method):
            return default
        try:
            return method(*args)
        except Exception:
            return default

    def read_time_step_s(self, default: float = 0.05) -> float:
        try:
            return max(float(default), float(self.call_optional("get_time_step", default=float(default))))
        except Exception:
            return float(default)

    def sync_task_order(self, agent_id: Any, task_order: Any) -> None:
        if task_order is not None:
            self.call_optional("set_task_order", agent_id, task_order)

    def sync_leader_intent(self, agent_id: Any, leader_intent: Any) -> None:
        if leader_intent is not None:
            self.call_optional("set_leader_intent", agent_id, leader_intent)

    def sync_pilot_report(self, agent_id: Any, pilot_report: Any) -> None:
        if pilot_report is not None:
            self.call_optional("set_pilot_report", agent_id, pilot_report)

    def sync_mission_command(self, agent_id: Any, cmd: Any) -> None:
        if cmd is not None:
            self.call_optional("set_mission_command", agent_id, cmd)

    def get_unit_position(self, entity_id: int) -> Any:
        return self.call_optional("get_unit_position", int(entity_id))

    def get_unit_velocity(self, entity_id: int) -> Any:
        return self.call_optional("get_unit_velocity", int(entity_id))

    def is_unit_active(self, entity_id: int) -> bool:
        return bool(self.call_optional("is_unit_active", int(entity_id), default=False))

    def get_agent_observation(self, entity_id: int) -> Any:
        return self.call_optional("get_agent_observation", int(entity_id))

    def get_instrument_state(self, entity_id: int) -> Any:
        return self.call_optional("get_instrument_state", int(entity_id))

    def set_command(
        self,
        entity_id: int,
        target_heading_deg: float,
        target_speed_mps: float,
        target_altitude_m: float,
    ) -> None:
        self.call_optional(
            "set_command",
            int(entity_id),
            float(target_heading_deg),
            float(target_speed_mps),
            float(target_altitude_m),
        )

    def fire_missile(self, entity_id: int, target_id: int) -> int:
        try:
            return int(self.call_optional("fire_missile", int(entity_id), int(target_id), default=0) or 0)
        except Exception:
            return 0


class LoaderOwnedScriptedOpponentKernelCompat:
    """Compatibility-only kernel adapter for scripted opponents."""

    def __init__(self, loader: Any):
        self._compat = loader_owned_raw_sim_compat(loader)

    def is_unit_active(self, entity_id: int) -> bool:
        return self._compat.is_unit_active(entity_id)

    def get_unit_position(self, entity_id: int) -> Any:
        return self._compat.get_unit_position(entity_id)

    def get_agent_observation(self, entity_id: int) -> Any:
        return self._compat.get_agent_observation(entity_id)

    def set_command(
        self,
        entity_id: int,
        target_heading_deg: float,
        target_speed_mps: float,
        target_altitude_m: float,
    ) -> None:
        self._compat.set_command(
            int(entity_id),
            float(target_heading_deg),
            float(target_speed_mps),
            float(target_altitude_m),
        )

    def fire_missile(self, entity_id: int, target_id: int) -> int:
        return self._compat.fire_missile(int(entity_id), int(target_id))


def loader_owned_raw_sim_compat(loader: Any) -> LoaderOwnedRawSimCompatibilityFacade:
    return LoaderOwnedRawSimCompatibilityFacade(loader)


def loader_owned_scripted_opponent_kernel_compat(loader: Any) -> LoaderOwnedScriptedOpponentKernelCompat:
    return LoaderOwnedScriptedOpponentKernelCompat(loader)


def apply_loader_owned_world_layout_to_kernel(loader: Any, layout: Any) -> Any:
    """Compatibility-only quarantine around loader-owned world-layout kernel apply."""

    sim = loader_owned_raw_sim_compat(loader).require_sim("loader-owned world-layout kernel-apply seam")
    apply_world_layout = getattr(import_module("python.scenario_runtime"), "apply_world_layout_to_kernel", None)
    if not callable(apply_world_layout):
        raise RuntimeError("python.scenario_runtime.apply_world_layout_to_kernel is not available")
    return apply_world_layout(sim, layout)


def mission_command_dict(loader: Any) -> dict[str, Any]:
    mission_cmd = getattr(loader, "mission_cmd", None)
    return mission_cmd if isinstance(mission_cmd, dict) else {}


def has_mission_command_dict(loader: Any) -> bool:
    return isinstance(getattr(loader, "mission_cmd", None), dict)


def mission_command_view(loader: Any) -> MissionCommandView:
    return MissionCommandView(mission_command_dict(loader))


def resolve_loader_time_step(loader: Any, default: float = 0.05) -> float:
    if loader is None:
        return float(default)

    for candidate in (
        getattr(loader, "_compiled_runtime_metadata", None),
        getattr(loader, "_compiled_scenario", None),
    ):
        if candidate is None:
            continue
        time_step_s = getattr(candidate, "time_step_s", None)
        if time_step_s is None:
            time_step_s = getattr(
                getattr(candidate, "layout_template", None),
                "time_step_s",
                None,
            )
        try:
            if time_step_s is not None:
                return max(float(default), float(time_step_s))
        except Exception:
            pass

    scenario_data = getattr(loader, "scenario_data", None)
    if isinstance(scenario_data, dict):
        env_cfg = scenario_data.get("environment", None)
        if isinstance(env_cfg, dict) and "time_step" in env_cfg:
            try:
                return max(float(default), float(env_cfg["time_step"]))
            except Exception:
                pass

    compat = loader_owned_raw_sim_compat(loader)
    if compat.supports("get_time_step"):
        return compat.read_time_step_s(default=float(default))

    return float(default)


def _normalized_profile_name(profile_name: Any | None) -> str | None:
    if profile_name is None:
        return None

    service_profile = getattr(ef_py, "ServiceProfile", None)
    if service_profile is not None:
        if profile_name == getattr(service_profile, "Navy", object()):
            return "naval"
        if profile_name == getattr(service_profile, "Army", object()):
            return "ground"
        if profile_name == getattr(service_profile, "AirForce", object()):
            return "air"

    text = str(getattr(profile_name, "name", profile_name)).strip().lower()
    if text.startswith("serviceprofile."):
        text = text.rsplit(".", 1)[-1]

    if text in {"", "unspecified"}:
        return None
    if text in {"air", "airforce", "joint"}:
        return "air"
    if text in {"army", "ground", "land"}:
        return "ground"
    if text in {"naval", "navy"}:
        return "naval"
    return None


def _resolve_profile_from_candidates(*candidates: Any) -> Any:
    for candidate in candidates:
        normalized = _normalized_profile_name(candidate)
        if normalized is not None:
            return resolve_tasking_profile(candidate)
    return resolve_tasking_profile(None)


def resolve_tasking_profile(profile_name: str | None = None):
    normalized = _normalized_profile_name(profile_name)
    if normalized is None:
        if profile_name is None or not str(getattr(profile_name, "name", profile_name)).strip():
            return _air
        raise ValueError(f"Unknown tasking profile: {profile_name!r}")
    if normalized == "air":
        return _air
    if normalized == "ground":
        return _ground
    if normalized == "naval":
        return _naval
    raise ValueError(f"Unknown tasking profile: {profile_name!r}")


def tasking_profile_for_loader(loader: Any):
    scenario_data = getattr(loader, "scenario_data", {}) or {}
    mission_cfg = None
    if isinstance(scenario_data, dict):
        mission_cfg = scenario_data.get("mission_command", None)

    task_order = getattr(loader, "task_order", None)
    mission_cmd = mission_command_dict(loader)
    explicit_profile_candidates = [
        scenario_data.get("tasking_profile", None) if isinstance(scenario_data, dict) else None,
        mission_cfg.get("tasking_profile", None) if isinstance(mission_cfg, dict) else None,
        getattr(task_order, "tasking_profile", None),
        mission_cmd.get("tasking_profile", None),
    ]
    profile = _resolve_profile_from_candidates(*explicit_profile_candidates)
    if profile is not _air or any(_normalized_profile_name(candidate) == "air" for candidate in explicit_profile_candidates):
        return profile

    inferred_profile_candidates = [
        getattr(task_order, "service_profile", None),
        mission_cmd.get("service_profile", None),
        mission_cfg.get("service_profile", None) if isinstance(mission_cfg, dict) else None,
        scenario_data.get("service_profile", None) if isinstance(scenario_data, dict) else None,
    ]
    return _resolve_profile_from_candidates(*inferred_profile_candidates)


def normalize_task_order_spec(order_spec: dict[str, Any] | None, *, loader: Any | None = None) -> dict[str, Any]:
    if loader is not None:
        profile = tasking_profile_for_loader(loader)
    else:
        if isinstance(order_spec, dict):
            profile = _resolve_profile_from_candidates(
                order_spec.get("tasking_profile", None),
                order_spec.get("service_profile", None),
            )
        else:
            profile = resolve_tasking_profile(None)
    return profile.normalize_task_order_spec(order_spec)


def build_kernel_mission_command(loader: Any):
    return tasking_profile_for_loader(loader).build_kernel_mission_command(loader)


def make_rule_based_leader_phase_manager(loader: Any | None = None, **kwargs: Any):
    profile = tasking_profile_for_loader(loader) if loader is not None else resolve_tasking_profile(None)
    return profile.RuleBasedLeaderPhaseManager(**kwargs)


def make_scripted_c2_task_manager(loader: Any | None = None, **kwargs: Any):
    profile = tasking_profile_for_loader(loader) if loader is not None else resolve_tasking_profile(None)
    return profile.ScriptedC2TaskManager(**kwargs)


def scripted_c2_task_manager_class(loader: Any | None = None):
    profile = tasking_profile_for_loader(loader) if loader is not None else resolve_tasking_profile(None)
    return profile.ScriptedC2TaskManager


def is_patrol_task(
    task: Any | None = None,
    *,
    task_name: str | None = None,
    phase_name: str | None = None,
    loader: Any | None = None,
) -> bool:
    profile = tasking_profile_for_loader(loader) if loader is not None else resolve_tasking_profile(None)
    return profile.is_patrol_task(task, task_name=task_name, phase_name=phase_name)


def is_recover_task(
    task: Any | None = None,
    *,
    task_name: str | None = None,
    phase_name: str | None = None,
    loader: Any | None = None,
) -> bool:
    profile = tasking_profile_for_loader(loader) if loader is not None else resolve_tasking_profile(None)
    return profile.is_recover_task(task, task_name=task_name, phase_name=phase_name)


def task_observation_codes(
    task: Any | None,
    *,
    fallback_phase_id: int = 0,
    loader: Any | None = None,
) -> tuple[float, float, float]:
    profile = tasking_profile_for_loader(loader) if loader is not None else resolve_tasking_profile(None)
    return profile.task_observation_codes(task, fallback_phase_id=fallback_phase_id)


def infer_route_ref_id(loader: Any) -> int:
    return tasking_profile_for_loader(loader).infer_route_ref_id(loader)


def infer_recovery_base_id(loader: Any, task: Any | None = None) -> int:
    return tasking_profile_for_loader(loader).infer_recovery_base_id(loader, task=task)


def infer_recovery_runway_id(loader: Any, task: Any | None = None) -> int:
    return tasking_profile_for_loader(loader).infer_recovery_runway_id(loader, task=task)


def infer_recovery_approach_type(loader: Any, task: Any | None = None):
    return tasking_profile_for_loader(loader).infer_recovery_approach_type(loader, task=task)


def has_active_waypoint_leg(loader: Any) -> bool:
    profile = tasking_profile_for_loader(loader)
    probe = getattr(profile, "has_active_waypoint_leg", None)
    if callable(probe):
        return bool(probe(loader))
    return False


def landing_reference_heading_deg(loader: Any, default_heading_deg: float) -> float:
    profile = tasking_profile_for_loader(loader)
    probe = getattr(profile, "_landing_reference_heading_deg", None)
    if callable(probe):
        return float(probe(loader, default_heading_deg))
    return float(default_heading_deg)


def _raw_sync_loader_command_chain(loader: Any) -> None:
    # compatibility_only direct simulation seam: maintained bridge fallback until a
    # facade-owned command-chain sync surface replaces this loader-owned quarantine.
    if getattr(loader, "agent_id", None) is None:
        return
    compat = loader_owned_raw_sim_compat(loader)
    compat.sync_task_order(loader.agent_id, getattr(loader, "task_order", None))
    compat.sync_leader_intent(loader.agent_id, getattr(loader, "leader_intent", None))
    compat.sync_pilot_report(loader.agent_id, getattr(loader, "pilot_report", None))


def sync_loader_mission_command(loader: Any, cmd: Any) -> None:
    # compatibility_only direct simulation seam: quarantine mission-command writes
    # behind the shared tasking bridge until a facade-owned sync surface exists.
    if getattr(loader, "agent_id", None) is None:
        return
    loader_owned_raw_sim_compat(loader).sync_mission_command(loader.agent_id, cmd)


def sync_loader_command_chain(loader: Any) -> None:
    if getattr(loader, "agent_id", None) is None:
        return
    if bool(getattr(loader, "_loader_owned_command_chain_sync_in_progress", False)):
        _raw_sync_loader_command_chain(loader)
        return
    sync_fn = getattr(loader, "_sync_kernel_command_chain", None)
    if callable(sync_fn):
        setattr(loader, "_loader_owned_command_chain_sync_in_progress", True)
        try:
            sync_fn()
            return
        finally:
            setattr(loader, "_loader_owned_command_chain_sync_in_progress", False)
    _raw_sync_loader_command_chain(loader)


def sync_loader_command_chain_compat(loader: Any) -> None:
    # compatibility_only direct simulation seam: use this only from bridge objects that
    # temporarily occupy the loader-owned phase-manager slot and would recurse
    # through loader._sync_kernel_command_chain().
    if getattr(loader, "agent_id", None) is None:
        return
    _raw_sync_loader_command_chain(loader)


def _loader_requires_maintained_policy_read_seam(loader: Any) -> bool:
    return callable(getattr(loader, "_get_cached_step_evaluation", None)) or callable(
        getattr(loader, "_sync_kernel_command_chain", None)
    )


def _read_loader_policy_state(
    loader: Any,
    *,
    agent_id: Any | None,
    maintained_method_name: str,
    raw_method_name: str,
    blocker: str,
    caller: str,
) -> Any:
    resolved_agent_id = getattr(loader, "agent_id", None) if agent_id is None else agent_id
    if resolved_agent_id is None:
        return None

    maintained_reader = getattr(loader, maintained_method_name, None)
    if callable(maintained_reader):
        try:
            return maintained_reader(resolved_agent_id)
        except Exception:
            return None

    if caller == "maintained" and _loader_requires_maintained_policy_read_seam(loader):
        raise RuntimeError(blocker)

    return loader_owned_raw_sim_compat(loader).call_optional(raw_method_name, resolved_agent_id)


def get_policy_agent_observation(loader: Any, agent_id: Any | None = None) -> Any:
    return _read_loader_policy_state(
        loader,
        agent_id=agent_id,
        maintained_method_name="get_policy_agent_observation",
        raw_method_name="get_agent_observation",
        blocker=TASKING_TRUTH_READ_BLOCKER,
        caller="maintained",
    )


def get_policy_instrument_state(loader: Any, agent_id: Any | None = None) -> Any:
    return _read_loader_policy_state(
        loader,
        agent_id=agent_id,
        maintained_method_name="get_policy_instrument_state",
        raw_method_name="get_instrument_state",
        blocker=TASKING_INSTRUMENT_READ_BLOCKER,
        caller="maintained",
    )


def read_loader_truth_compat(loader: Any) -> Any:
    # compatibility_only direct simulation seam: keep this blocker-localized until a
    # maintained loader observation seam replaces raw fallback reads.
    agent_id = getattr(loader, "agent_id", None)
    return _read_loader_policy_state(
        loader,
        agent_id=agent_id,
        maintained_method_name="get_policy_agent_observation",
        raw_method_name="get_agent_observation",
        blocker=TASKING_TRUTH_READ_BLOCKER,
        caller="compat",
    )


def read_loader_instrument_compat(loader: Any) -> Any:
    # compatibility_only direct simulation seam: keep this blocker-localized until a
    # maintained loader instrument seam replaces raw fallback reads.
    agent_id = getattr(loader, "agent_id", None)
    return _read_loader_policy_state(
        loader,
        agent_id=agent_id,
        maintained_method_name="get_policy_instrument_state",
        raw_method_name="get_instrument_state",
        blocker=TASKING_INSTRUMENT_READ_BLOCKER,
        caller="compat",
    )
