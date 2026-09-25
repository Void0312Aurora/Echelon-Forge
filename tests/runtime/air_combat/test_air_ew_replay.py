from __future__ import annotations

from tools.diagnostics.air_ew_scripted_demo import run_demo


_SCENARIO_PATH = "scenarios/air_combat/air_combat_1v1_headon_sensor_smoke_v1.json"


def test_scripted_ew_demo_replays_warning_and_inventory_trace() -> None:
    first = run_demo(
        scenario_path=_SCENARIO_PATH,
        seed=20260516,
        max_steps=120,
        response_doctrine="countermeasure_ready",
    )
    second = run_demo(
        scenario_path=_SCENARIO_PATH,
        seed=20260516,
        max_steps=120,
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
    assert first["launch_warning_steps"] == [42, 82]
    assert first["countermeasure_request_steps"] == [42, 82]
    assert [sample["chaff_remaining"] for sample in first["countermeasure_state_samples"]] == [60, 59]
    assert [sample["flare_remaining"] for sample in first["countermeasure_state_samples"]] == [30, 30]
