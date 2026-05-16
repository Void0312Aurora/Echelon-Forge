import ef_py

from python.rl.tasking.bridge import build_kernel_mission_command


def sync_kernel_mission_command(loader) -> None:
    if loader.agent_id is None:
        return
    if not hasattr(loader.sim, "set_mission_command") or not hasattr(ef_py, "MissionCommand"):
        return
    try:
        cmd = build_kernel_mission_command(loader)
        loader.sim.set_mission_command(loader.agent_id, cmd)
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
        loader._leader_phase_manager.sync_to_kernel(loader)
    except Exception:
        pass


def reset_command_chain(loader, *, initial_truth=None, initial_inst=None, sync_to_kernel: bool = True) -> None:
    if loader.agent_id is None:
        return
    if not hierarchical_command_chain_active(loader):
        loader.task_order = None
        loader.leader_intent = None
        loader.pilot_report = None
        if sync_to_kernel:
            sync_kernel_mission_command(loader)
        return
    try:
        sim_time_s = float(loader.steps) * float(loader.sim.get_time_step())
    except Exception:
        sim_time_s = 0.0
    loader._leader_phase_manager.reset(
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
    loader._leader_phase_manager.update(
        loader,
        sim_time_s=float(sim_time),
        truth=truth,
        inst=inst,
        sync_to_kernel=sync_to_kernel,
    )
    if sync_to_kernel:
        sync_kernel_command_chain(loader)


def update_command_chain_only(loader, sim_time, *, truth=None, inst=None, sync_to_kernel: bool = True):
    update_command_chain(loader, sim_time, truth=truth, inst=inst, sync_to_kernel=False)
    if sync_to_kernel:
        sync_kernel_command_chain(loader)
