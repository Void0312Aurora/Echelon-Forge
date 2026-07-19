import ef_py

from python.tasking_contracts.bridge_views import (
    has_mission_command_dict,
    loader_owned_runtime_view,
    mission_command_dict,
    resolve_loader_time_step,
    sync_loader_mission_command,
)
# `build_kernel_mission_command` stays python.rl-resident: it dispatches
# through `tasking_profile_for_loader`, a genuine entanglement point with the
# air/ground/naval profile modules (see I24 report).
from python.rl.tasking.bridge import build_kernel_mission_command
from .command_chain_owner import ensure_command_chain_owner
from .naval_screen import apply_naval_screen_station_hold, compute_naval_screen_station_hold


def _reset_naval_screen_station_hold_state(loader) -> None:
    ensure_command_chain_owner(loader).reset_naval_screen_state()


def _apply_dynamic_naval_screen_command_overrides(loader, cmd) -> None:
    task = getattr(loader, "task_order", None)
    if task is None:
        return
    use_direct_command = bool(getattr(loader, "_naval_screen_use_direct_command", False))
    if hasattr(cmd, "cmd_heading_deg"):
        dynamic_heading = getattr(task, "target_heading_deg", None)
        if dynamic_heading is not None:
            cmd.cmd_heading_deg = float(dynamic_heading)
    if hasattr(cmd, "cmd_speed_mps"):
        dynamic_speed = getattr(task, "target_speed_mps", None)
        if dynamic_speed is not None:
            cmd.cmd_speed_mps = float(dynamic_speed)
    if use_direct_command:
        if hasattr(cmd, "reference_entity_id"):
            cmd.reference_entity_id = 0
        if hasattr(cmd, "station_radius_m"):
            cmd.station_radius_m = 0.0


def _apply_naval_screen_runtime_state(loader, *, truth=None) -> None:
    result = compute_naval_screen_station_hold(loader, truth=truth)
    if result is None:
        return
    task = getattr(loader, "task_order", None)
    mission_cmd = mission_command_dict(loader)
    if task is None or not has_mission_command_dict(loader):
        return
    loader._naval_screen_last_reference_id = int(result["reference_entity_id"])
    loader._naval_screen_last_heading_deg = float(result["target_heading_deg"])
    loader._naval_screen_last_speed_mps = float(result["target_speed_mps"])
    loader._naval_screen_use_direct_command = bool(result.get("use_direct_command", 0.0))
    for attr, value in (
        ("anchor_x_m", float(result["desired_x"])),
        ("anchor_y_m", float(result["desired_y"])),
        ("anchor_z_m", 0.0),
        ("target_heading_deg", float(result["target_heading_deg"])),
        ("target_speed_mps", float(result["target_speed_mps"])),
        ("target_altitude_m", 0.0),
    ):
        try:
            setattr(task, attr, value)
        except Exception:
            pass
    mission_cmd["target_heading"] = float(result["target_heading_deg"])
    mission_cmd["target_speed"] = float(result["target_speed_mps"])
    mission_cmd["target_altitude"] = 0.0


def sync_kernel_mission_command(loader) -> None:
    if loader.agent_id is None:
        return
    if not loader_owned_runtime_view(loader).supports("set_mission_command") or not hasattr(ef_py, "MissionCommand"):
        return
    try:
        _apply_naval_screen_runtime_state(loader)
    except Exception:
        pass
    try:
        cmd = build_kernel_mission_command(loader)
        _apply_dynamic_naval_screen_command_overrides(loader, cmd)
        sync_loader_mission_command(loader, cmd)
    except Exception:
        pass


def hierarchical_command_chain_active(loader) -> bool:
    task_cfg = loader.scenario_data.get("task_order", None)
    if isinstance(task_cfg, dict) and bool(task_cfg):
        return True
    if getattr(loader, "task_order", None) is not None:
        return True
    if getattr(loader, "leader_intent", None) is not None:
        return True
    if getattr(loader, "pilot_report", None) is not None:
        return True
    if str(getattr(loader, "c2_task_name", "") or "").strip():
        return True
    return False


def sync_kernel_command_chain(loader) -> None:
    if loader.agent_id is None:
        return
    if not hierarchical_command_chain_active(loader):
        return
    try:
        ensure_command_chain_owner(loader)._leader_phase_manager.sync_to_kernel(loader)
    except Exception:
        pass


def reset_command_chain(loader, *, initial_truth=None, initial_inst=None, sync_to_kernel: bool = True) -> None:
    _reset_naval_screen_station_hold_state(loader)
    if loader.agent_id is None:
        return
    if not hierarchical_command_chain_active(loader):
        loader.task_order = None
        loader.leader_intent = None
        loader.pilot_report = None
        if sync_to_kernel:
            sync_kernel_mission_command(loader)
        return
    sim_time_s = float(loader.steps) * float(resolve_loader_time_step(loader, default=0.05))
    ensure_command_chain_owner(loader)._leader_phase_manager.reset(
        loader,
        sim_time_s=sim_time_s,
        truth=initial_truth,
        inst=initial_inst,
        sync_to_kernel=sync_to_kernel,
    )
    if sync_to_kernel:
        sync_kernel_mission_command(loader)
        sync_kernel_command_chain(loader)


def update_command_chain(loader, sim_time: float, *, truth=None, inst=None, sync_to_kernel: bool = True) -> None:
    if loader.agent_id is None:
        return
    if not hierarchical_command_chain_active(loader):
        return
    ensure_command_chain_owner(loader)._leader_phase_manager.update(
        loader,
        sim_time_s=float(sim_time),
        truth=truth,
        inst=inst,
        sync_to_kernel=sync_to_kernel,
    )
    _apply_naval_screen_runtime_state(loader, truth=truth)
    if sync_to_kernel:
        try:
            cmd = build_kernel_mission_command(loader)
            _apply_dynamic_naval_screen_command_overrides(loader, cmd)
            sync_loader_mission_command(loader, cmd)
        except Exception:
            pass
        sync_kernel_command_chain(loader)


def update_command_chain_only(loader, sim_time, *, truth=None, inst=None, sync_to_kernel: bool = True):
    update_command_chain(loader, sim_time, truth=truth, inst=inst, sync_to_kernel=False)
    if sync_to_kernel:
        sync_kernel_command_chain(loader)
