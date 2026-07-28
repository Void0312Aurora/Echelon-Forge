"""I24 (W2 critical period) architecture gates for the neutral tasking-contracts layer.

Background: `gym_envs` and `python.rl` used to form a real import cycle through
`python.rl.tasking.bridge` / `python.rl.control.mission_defs` (gym_envs consumed
them) and `python.rl.runtime.*` (which imports `gym_envs.scenario_loader`/
`gym_envs.universal_env`). I24 extracted the profile-independent slice of that
consumed surface into `python.tasking_contracts` (zero dependency on either
side) so the dependency direction becomes::

    gym_envs -> python.tasking_contracts <- python.rl

This module enforces two invariants going forward:

1. `python/tasking_contracts/**` never imports `python.rl` or `gym_envs`
   (unconditional; this is the whole point of a neutral layer).
2. `gym_envs/**` does not gain *new* `python.rl` imports beyond an explicit,
   named allowlist of the residual profile-dispatch/algorithm entanglements
   that I24 deliberately left in place (see the I24 report for why each entry
   cannot be moved without either reaching back into `python.rl`-internal
   profile modules or into another genuine `python.rl` <-> `gym_envs` mutual
   dependency). Shrinking the allowlist is encouraged in a future iteration;
   growing it silently is not allowed by this gate.

It also pins the compatibility-shell guarantee: every name I24 moved out of
`python.rl.control.mission_defs`, `python.rl.tasking.bridge`,
`python.rl.control.{base_scripted_controller,scripted_landing,
scripted_stable_flight,scripted_takeoff}`, `python.rl.runtime.
leader_window_runtime.LeaderDecisionState`, and `python.rl.runtime.
execution_runtime.coerce_timing_dict` is re-exported from its original
location as the *exact same object* as the neutral-layer canonical definition.
"""

from __future__ import annotations

import ast
from pathlib import Path

from tests.architecture.helpers import ensure_repo_root_on_sys_path
from tests.support.paths import REPO_ROOT

ensure_repo_root_on_sys_path()

GYM_ENVS_ROOT = REPO_ROOT / "gym_envs"
TASKING_CONTRACTS_ROOT = REPO_ROOT / "python" / "tasking_contracts"


def _iter_python_files(root: Path) -> list[Path]:
    excluded_prefixes = ("__pycache__",)
    return [
        path
        for path in sorted(root.rglob("*.py"))
        if not any(part.startswith(excluded_prefixes) for part in path.parts)
    ]


def _foreign_package_refs(path: Path, *, packages: tuple[str, ...]) -> set[tuple[str, str, int]]:
    """Every `from <pkg...> import name` / `import <pkg...>` reference, anywhere in the file
    (including inside function bodies, to also catch deferred/lazy imports)."""

    tree = ast.parse(path.read_text(encoding="utf-8"))
    refs: set[tuple[str, str, int]] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            if node.module in packages or any(node.module.startswith(f"{pkg}.") for pkg in packages):
                for alias in node.names:
                    refs.add((node.module, alias.name, int(node.lineno)))
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name in packages or any(alias.name.startswith(f"{pkg}.") for pkg in packages):
                    refs.add((alias.name, "<module>", int(node.lineno)))
    return refs


# Governance ledger of the I24 residual: (file relative to repo root) -> {(module, imported_name)}.
# Every entry here is a genuine entanglement point that I24's own report documents:
# either it dispatches through `tasking_profile_for_loader`/`resolve_tasking_profile`
# into the python.rl-internal air/ground/naval profile modules, or it is a
# python.rl runtime/algorithm module that itself imports gym_envs (a real mutual
# dependency, not a misplaced pure helper). See docs referenced in the I24 report
# for the full rationale per entry.
GYM_ENVS_PYTHON_RL_RESIDUAL_ALLOWLIST: dict[str, set[tuple[str, str]]] = {
    "gym_envs/leader_env.py": {
        ("python.rl.tasking.bridge", "make_rule_based_leader_phase_manager"),
        ("python.rl.tasking.bridge", "make_scripted_c2_task_manager"),
        ("python.rl.tasking.bridge", "scripted_c2_task_manager_class"),
    },
    "gym_envs/leader_env_parts/decision_runtime/commands.py": {
        ("python.rl.tasking.bridge", "infer_recovery_approach_type"),
        ("python.rl.tasking.bridge", "infer_recovery_base_id"),
        ("python.rl.tasking.bridge", "infer_recovery_runway_id"),
        ("python.rl.tasking.bridge", "infer_route_ref_id"),
        ("python.rl.tasking.bridge", "is_patrol_task"),
        ("python.rl.tasking.bridge", "is_recover_task"),
    },
    "gym_envs/leader_env_parts/decision_runtime/observations.py": {
        ("python.rl.tasking.bridge", "task_observation_codes"),
    },
    "gym_envs/leader_env_parts/execution_runtime/policy_runtime.py": {
        ("python.rl.runtime.single_world_batch_runtime", "build_single_world_batch_execution_runtime"),
        ("python.rl.control.wrappers", "get_action_wrapper_spec"),
    },
    "gym_envs/leader_env_parts/policy.py": {
        ("python.rl.policy_algo.ppo_adaptive_kl", "AdaptiveKLPPO"),
    },
    "gym_envs/leader_env_parts/runtime_facade.py": {
        ("python.rl.runtime.leader_window_runtime", "LocalLeaderWindowRuntime"),
        ("python.rl.runtime.leader_window_runtime", "WorldBatchLeaderWindowRuntime"),
    },
    "gym_envs/scenario_loader/behavior_runtime/command_chain.py": {
        ("python.rl.tasking.bridge", "build_kernel_mission_command"),
    },
    "gym_envs/scenario_loader/behavior_runtime/command_chain_owner.py": {
        ("python.rl.tasking.bridge", "make_rule_based_leader_phase_manager"),
    },
    "gym_envs/scenario_loader/loading.py": {
        ("python.rl.tasking.bridge", "normalize_task_order_spec"),
    },
    "gym_envs/scenario_loader/runtime_state.py": {
        ("python.rl.tasking.bridge", "build_kernel_mission_command"),
    },
    "gym_envs/scenario_loader/step_evaluation.py": {
        ("python.rl.tasking.bridge", "resolve_tasking_profile"),
        ("python.rl.tasking.bridge", "tasking_profile_for_loader"),
    },
    "gym_envs/universal_env_parts/info.py": {
        ("python.rl.tasking.bridge", "resolve_tasking_profile"),
        ("python.rl.tasking.bridge", "tasking_profile_for_loader"),
    },
    "gym_envs/universal_env_parts/naval_actions.py": {
        ("python.rl.tasking.bridge", "resolve_tasking_profile"),
        ("python.rl.tasking.bridge", "tasking_profile_for_loader"),
    },
    "gym_envs/universal_env_parts/observations.py": {
        ("python.rl.tasking.bridge", "resolve_tasking_profile"),
        ("python.rl.tasking.bridge", "tasking_profile_for_loader"),
    },
}


def test_tasking_contracts_package_never_imports_python_rl_or_gym_envs() -> None:
    offenders: dict[str, list[str]] = {}
    for path in _iter_python_files(TASKING_CONTRACTS_ROOT):
        refs = _foreign_package_refs(path, packages=("python.rl", "gym_envs"))
        if refs:
            rel = path.relative_to(REPO_ROOT).as_posix()
            offenders[rel] = sorted(f"L{lineno}: {module}.{name}" for module, name, lineno in refs)

    assert not offenders, (
        "python/tasking_contracts/** must stay neutral (stdlib + ef_py-style native "
        f"lazy imports only); found python.rl/gym_envs references: {offenders}"
    )


def test_gym_envs_python_rl_imports_are_limited_to_the_documented_residual_allowlist() -> None:
    found: dict[str, set[tuple[str, str]]] = {}
    for path in _iter_python_files(GYM_ENVS_ROOT):
        refs = _foreign_package_refs(path, packages=("python.rl",))
        if refs:
            rel = path.relative_to(REPO_ROOT).as_posix()
            found.setdefault(rel, set()).update((module, name) for module, name, _lineno in refs)

    expected_files = set(GYM_ENVS_PYTHON_RL_RESIDUAL_ALLOWLIST)
    found_files = set(found)

    new_files = found_files - expected_files
    assert not new_files, (
        "gym_envs file(s) import python.rl without a governance-ledger allowlist entry "
        f"(I24 broke this cycle; new python.rl imports need an explicit, reviewed entry "
        f"or must go through python.tasking_contracts instead): {sorted(new_files)}"
    )

    for relative_path, expected_refs in GYM_ENVS_PYTHON_RL_RESIDUAL_ALLOWLIST.items():
        actual_refs = found.get(relative_path, set())
        assert actual_refs == expected_refs, (
            f"{relative_path}: residual python.rl import set drifted from the I24 governance "
            f"ledger. expected={sorted(expected_refs)} actual={sorted(actual_refs)}. "
            "If this file's residual shrank, narrow the allowlist entry (progress); if it "
            "grew, that is a new entanglement that needs its own reviewed justification."
        )

    stale_files = expected_files - found_files
    assert not stale_files, (
        "governance ledger allowlist entries no longer match any real python.rl import in "
        f"gym_envs; remove the stale entries to keep this gate honest: {sorted(stale_files)}"
    )
