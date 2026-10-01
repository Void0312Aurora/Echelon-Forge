from __future__ import annotations

from tests.runtime.air_combat.ew_trace_invariants import (
    assert_continuous_warning,
    assert_interval_gated_consumption,
)
from tools.diagnostics.air_ew_scripted_demo import run_demo


_SCENARIO_PATH = "scenarios/air_combat/air_combat_1v1_headon_sensor_smoke_v1.json"

# Red's scripted fire range (9 km) exceeds the 8 km head-on separation, so the
# first missile is in flight by step 3 and Red keeps one inbound through the
# 120-step window; native MAWS warns on every one of those frames.
_FIRST_LAUNCH_WARNING_STEP = 3
_MAX_STEPS = 120


def test_scripted_ew_demo_replays_warning_and_inventory_trace() -> None:
    first = run_demo(
        scenario_path=_SCENARIO_PATH,
        seed=20260516,
        max_steps=_MAX_STEPS,
        response_doctrine="countermeasure_ready",
    )
    second = run_demo(
        scenario_path=_SCENARIO_PATH,
        seed=20260516,
        max_steps=_MAX_STEPS,
        response_doctrine="countermeasure_ready",
    )

    for key in (
        "steps",
        "terminated",
        "truncated",
        "termination_reason",
        "launch_warning_steps",
        "countermeasure_request_steps",
        "countermeasure_state_samples",
        "scripted_runtime_decisions",
    ):
        assert first[key] == second[key]
    assert first["scripted_runtime_identity"] == second["scripted_runtime_identity"]

    first_warning = assert_continuous_warning(first["launch_warning_steps"], last_step=_MAX_STEPS)
    assert first_warning == _FIRST_LAUNCH_WARNING_STEP
    assert first["countermeasure_request_steps"] == first["launch_warning_steps"]
    assert_interval_gated_consumption(
        first["countermeasure_state_samples"],
        first_warning_step=first_warning,
        chaff_requested=True,
        flare_requested=True,
    )


def test_scripted_ew_demo_can_report_flare_only_consumption() -> None:
    result = run_demo(
        scenario_path=_SCENARIO_PATH,
        seed=20260516,
        max_steps=_MAX_STEPS,
        response_doctrine="flare_only",
    )

    first_warning = assert_continuous_warning(result["launch_warning_steps"], last_step=_MAX_STEPS)
    assert first_warning == _FIRST_LAUNCH_WARNING_STEP
    assert result["countermeasure_request_steps"] == result["launch_warning_steps"]
    assert_interval_gated_consumption(
        result["countermeasure_state_samples"],
        first_warning_step=first_warning,
        chaff_requested=False,
        flare_requested=True,
    )
