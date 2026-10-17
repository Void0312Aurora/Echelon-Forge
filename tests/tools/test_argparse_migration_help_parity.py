"""Contract-focused CLI checks for the argparse migration.

The commands retain a working ``--help`` entrypoint and their supported option
surface.  Argparse prose, wrapping and whitespace are presentation details and
are intentionally not treated as a compatibility ABI.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]

INVOCATIONS: list[tuple[str, list[str]]] = [
    ("evaluate", ["evaluate.py", "--help"]),
    ("naval_station_policy_eval", ["tools/eval/naval_station_policy_eval.py", "--help"]),
    (
        "ablate_visual_training_effect",
        ["tools/diagnostics/ablate_visual_training_effect.py", "--help"],
    ),
    (
        "diagnose_cooperative_trajectory",
        ["tools/diagnostics/diagnose_cooperative_trajectory.py", "--help"],
    ),
    ("leader_perf_probe", ["tools/diagnostics/leader_perf_probe.py", "--help"]),
    ("takeoff_to_landing", ["tools/diagnostics/flight_trajectory/takeoff_to_landing.py", "--help"]),
    (
        "trace_training_nonfinite_source",
        ["tools/diagnostics/trace_training_nonfinite_source.py", "--help"],
    ),
    (
        "policy_execution_eval_single",
        ["tools/eval/policy_execution_eval.py", "--mode", "single", "--help"],
    ),
    (
        "policy_execution_eval_cooperative",
        ["tools/eval/policy_execution_eval.py", "--mode", "cooperative", "--help"],
    ),
    (
        "eval_task_stable_flight_scripted",
        ["tools/eval/eval_task.py", "--task", "stable_flight", "--backend", "scripted", "--help"],
    ),
    (
        "eval_task_stable_flight_world_model",
        [
            "tools/eval/eval_task.py",
            "--task",
            "stable_flight",
            "--backend",
            "world_model",
            "--help",
        ],
    ),
    (
        "eval_task_takeoff_roll_scripted",
        ["tools/eval/eval_task.py", "--task", "takeoff_roll", "--backend", "scripted", "--help"],
    ),
    (
        "eval_task_takeoff_roll_world_model",
        ["tools/eval/eval_task.py", "--task", "takeoff_roll", "--backend", "world_model", "--help"],
    ),
    (
        "eval_task_centerline_scripted",
        ["tools/eval/eval_task.py", "--task", "centerline", "--backend", "scripted", "--help"],
    ),
    (
        "eval_task_waypoint_nav_world_model",
        ["tools/eval/eval_task.py", "--task", "waypoint_nav", "--backend", "world_model", "--help"],
    ),
    (
        "kces_response_diagnosis",
        ["tools/diagnostics/kill_chain_expectation_response_diagnosis.py", "--help"],
    ),
    (
        "kces_stage_attribution",
        ["tools/diagnostics/kill_chain_expectation_stage_attribution.py", "--help"],
    ),
    ("kces_visualize", ["tools/diagnostics/kill_chain_expectation_visualize.py", "--help"]),
    ("kces_envelope_audit", ["tools/diagnostics/kces/envelope_audit.py", "--help"]),
]

HELP_OPTION_CONTRACTS: dict[str, tuple[str, ...]] = {
    "evaluate": ("--scenario", "--model", "--algo", "--episodes"),
    "naval_station_policy_eval": ("--scenario", "--train_config", "--mode", "--report-envelope"),
    "ablate_visual_training_effect": ("--scenario", "--train_config", "--factors", "--json_out"),
    "diagnose_cooperative_trajectory": ("--task", "--scenario", "--train_config", "--scripted"),
    "leader_perf_probe": ("--scenario", "--train_config", "--n_envs", "--vec_backend"),
    "takeoff_to_landing": ("--scenario", "--train_config", "--scripted", "--max_steps"),
    "trace_training_nonfinite_source": ("--scenario", "--train_config", "--timesteps"),
    "policy_execution_eval_single": (
        "--mode",
        "--scenario",
        "--train_config",
        "--model",
        "--max_steps",
    ),
    "policy_execution_eval_cooperative": (
        "--mode",
        "--scenario",
        "--train_config",
        "--model",
        "--max_world_steps",
    ),
    "eval_task_stable_flight_scripted": ("--task", "--backend", "--scenario", "--warmup_steps"),
    "eval_task_stable_flight_world_model": (
        "--task",
        "--backend",
        "--scenario",
        "--checkpoint",
        "--warmup_steps",
    ),
    "eval_task_takeoff_roll_scripted": (
        "--task",
        "--backend",
        "--scenario",
        "--wheel_off_alt_threshold",
    ),
    "eval_task_takeoff_roll_world_model": (
        "--task",
        "--backend",
        "--scenario",
        "--checkpoint",
        "--liftoff_ias_threshold",
    ),
    "eval_task_centerline_scripted": ("--task", "--backend", "--scenario", "--action_mode"),
    "eval_task_waypoint_nav_world_model": ("--task", "--backend", "--scenario", "--checkpoint"),
    "kces_response_diagnosis": ("--input", "--output-dir", "--variant"),
    "kces_stage_attribution": ("--input", "--output-dir", "--target-motion-layer"),
    "kces_visualize": ("--input", "--output-dir", "--date-stamp"),
    "kces_envelope_audit": ("--input", "--output-dir", "--prefix"),
}


def _run_help(argv: list[str]) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO_ROOT) + os.pathsep + env.get("PYTHONPATH", "")
    return subprocess.run(
        [sys.executable, *argv],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )


def _help_contains_option(help_text: str, option: str) -> bool:
    return re.search(
        rf"(?<![A-Za-z0-9_-]){re.escape(option)}(?![A-Za-z0-9_-])",
        help_text,
    ) is not None


def test_help_option_contracts_cover_all_invocations() -> None:
    assert {name for name, _ in INVOCATIONS} == set(HELP_OPTION_CONTRACTS)


@pytest.mark.parametrize("name,argv", INVOCATIONS)
def test_help_invocation_preserves_option_contract(name: str, argv: list[str]) -> None:
    proc = _run_help(argv)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert proc.stderr == ""
    assert "usage:" in proc.stdout
    assert "-h, --help" in proc.stdout
    for option in HELP_OPTION_CONTRACTS[name]:
        assert _help_contains_option(proc.stdout, option), (
            f"{name} no longer advertises option token {option}"
        )
