from __future__ import annotations

from python.runtime_bootstrap import ensure_repo_imports, resolve_repo_path

from .common import _load_spec

def run_loader_command_chain_contract(spec_path: str) -> tuple[bool, str]:
    repo_root = ensure_repo_imports()

    import ef_py
    from gym_envs.scenario_loader import ScenarioLoader

    spec = _load_spec(spec_path)
    scenario_path = resolve_repo_path(str(spec["scenario"]))
    seed = int(spec.get("seed", 7))
    expected_phase_names = {str(x).strip().lower() for x in spec.get("expected_phase_names", [])}
    expected_intent_command_code = int(spec.get("expected_intent_command_code", 1))
    expected_kernel_command_code = int(spec.get("expected_kernel_command_code", expected_intent_command_code))

    sim = ef_py.SimulationKernel()
    sim.load_database("examples/config/database")

    loader = ScenarioLoader(sim)
    agent_id = loader.load_scenario(scenario_path, seed=seed)
    if agent_id is None:
        return False, "expected agent in scenario"

    if loader.task_order is None or not bool(loader.task_order.active):
        return False, "task order was not initialized"
    if loader.leader_intent is None or not bool(loader.leader_intent.active):
        return False, "leader intent was not initialized"
    if loader.pilot_report is None or not bool(loader.pilot_report.active):
        return False, "pilot report was not initialized"

    phase_name = str(loader.mission_phase_name).strip().lower()
    if expected_phase_names and phase_name not in expected_phase_names:
        return False, f"unexpected initial mission phase {loader.mission_phase_name!r}"

    kernel_order = sim.get_task_order(agent_id)
    kernel_intent = sim.get_leader_intent(agent_id)
    kernel_report = sim.get_pilot_report(agent_id)
    kernel_mission = sim.get_mission_command(agent_id)

    if not bool(kernel_order.active):
        return False, "task order did not reach kernel"
    if not bool(kernel_intent.active):
        return False, "leader intent did not reach kernel"
    if not bool(kernel_report.active):
        return False, "pilot report did not reach kernel"
    if int(kernel_intent.command_code) != expected_intent_command_code:
        return False, (
            "unexpected leader intent command_code "
            f"{kernel_intent.command_code} != {expected_intent_command_code}"
        )
    if not bool(kernel_mission.active):
        return False, "kernel mission command was not initialized"
    if int(kernel_mission.command_code) != expected_kernel_command_code:
        return False, (
            "unexpected kernel mission command "
            f"{kernel_mission.command_code} != {expected_kernel_command_code}"
        )
    if int(kernel_mission.command_code) != int(kernel_intent.command_code):
        return False, (
            "kernel mission command is not aligned with leader intent "
            f"({kernel_mission.command_code} vs {kernel_intent.command_code})"
    )
    return True, "loader command chain contract passed"
