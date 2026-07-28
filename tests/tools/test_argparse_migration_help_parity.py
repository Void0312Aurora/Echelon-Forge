"""Byte-parity regression test for the T5 second argparse batch.

Pins ``--help`` output for every tool touched by the argparse-group
migration (I20's ``add_probe_run_args``/``add_model_load_args``/
``add_json_out_arg`` reach extended to nine partial-match call sites, plus
the two new groups: KCES before-report args and the independent-review
retained-gate output args). The fixtures under
``tests/tools/fixtures/argparse_migration_help/`` were captured from this
tree right after the migration landed and were diffed byte-for-byte against
a pre-migration capture of the same invocations during development (see the
iteration register); this test keeps that parity pinned going forward.

``naval_station_policy_eval.py`` additionally carries the new opt-in
``--report-envelope`` flag from the T5 report-envelope slice, so its
fixture reflects the post-envelope shape rather than the pre-migration one;
``tests/tools/test_report_envelope_integration.py`` covers that flag on its
own terms.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures" / "argparse_migration_help"

# (fixture stem, argv relative to REPO_ROOT)
INVOCATIONS: list[tuple[str, list[str]]] = [
    ("evaluate", ["evaluate.py", "--help"]),
    ("naval_station_policy_eval", ["tools/eval/naval_station_policy_eval.py", "--help"]),
    ("ablate_visual_training_effect", ["tools/diagnostics/ablate_visual_training_effect.py", "--help"]),
    ("diagnose_cooperative_trajectory", ["tools/diagnostics/diagnose_cooperative_trajectory.py", "--help"]),
    ("leader_perf_probe", ["tools/diagnostics/leader_perf_probe.py", "--help"]),
    ("takeoff_to_landing", ["tools/diagnostics/flight_trajectory/takeoff_to_landing.py", "--help"]),
    ("trace_training_nonfinite_source", ["tools/diagnostics/trace_training_nonfinite_source.py", "--help"]),
    ("policy_execution_eval_single", ["tools/eval/policy_execution_eval.py", "--mode", "single", "--help"]),
    ("policy_execution_eval_cooperative", ["tools/eval/policy_execution_eval.py", "--mode", "cooperative", "--help"]),
    (
        "eval_task_stable_flight_scripted",
        ["tools/eval/eval_task.py", "--task", "stable_flight", "--backend", "scripted", "--help"],
    ),
    (
        "eval_task_stable_flight_world_model",
        ["tools/eval/eval_task.py", "--task", "stable_flight", "--backend", "world_model", "--help"],
    ),
    (
        "eval_task_takeoff_roll_scripted",
        ["tools/eval/eval_task.py", "--task", "takeoff_roll", "--backend", "scripted", "--help"],
    ),
    (
        "eval_task_takeoff_roll_world_model",
        ["tools/eval/eval_task.py", "--task", "takeoff_roll", "--backend", "world_model", "--help"],
    ),
    ("eval_task_centerline_scripted", ["tools/eval/eval_task.py", "--task", "centerline", "--backend", "scripted", "--help"]),
    (
        "eval_task_waypoint_nav_world_model",
        ["tools/eval/eval_task.py", "--task", "waypoint_nav", "--backend", "world_model", "--help"],
    ),
    ("kces_response_diagnosis", ["tools/diagnostics/kill_chain_expectation_response_diagnosis.py", "--help"]),
    ("kces_stage_attribution", ["tools/diagnostics/kill_chain_expectation_stage_attribution.py", "--help"]),
    ("kces_visualize", ["tools/diagnostics/kill_chain_expectation_visualize.py", "--help"]),
    ("kces_envelope_audit", ["tools/diagnostics/kces/envelope_audit.py", "--help"]),
    ("review_closeout", ["tools/maintenance/independent_review/review_closeout.py", "--help"]),
    ("scope_bucket_review", ["tools/maintenance/independent_review/scope_bucket_review.py", "--help"]),
    ("uncertainty_review", ["tools/maintenance/independent_review/uncertainty_review.py", "--help"]),
]


def _run_help(argv: list[str]) -> str:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO_ROOT) + os.pathsep + env.get("PYTHONPATH", "")
    proc = subprocess.run(
        [sys.executable, *argv],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    return proc.stdout


@pytest.mark.parametrize("fixture_stem,argv", INVOCATIONS, ids=[name for name, _ in INVOCATIONS])
def test_help_output_matches_pinned_fixture(fixture_stem: str, argv: list[str]) -> None:
    expected = (FIXTURES_DIR / f"{fixture_stem}.txt").read_text(encoding="utf-8")
    actual = _run_help(argv)
    assert actual == expected


def test_all_fixture_files_are_referenced_by_some_invocation() -> None:
    referenced = {name for name, _ in INVOCATIONS}
    on_disk = {path.stem for path in FIXTURES_DIR.glob("*.txt")}
    assert on_disk == referenced
