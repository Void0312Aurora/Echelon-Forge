from __future__ import annotations

import math

from tests.runtime.air_combat.weapon_guidance_realism.helpers import (
    _DB_PATH,
    _drive_missile_with_truth_track,
    _make_baseline_kernel,
    _spawn_geometry_pair,
    _spawn_structured_f16_pair,
    ef_py,
)
from tools.diagnostics import air_combat_weapon_employment_process_probe as probe


def _warhead_profile(family: str) -> object:
    profile = ef_py.WarheadProfile()
    profile.family = family
    profile.mass_kg = 12.0
    profile.lethal_radius_m = 35.0
    profile.damage_scalar = 90.0
    profile.synthetic = True
    profile.damage_scalar_synthetic = True
    profile.provenance = "test_continuous_rod_diagnostic_projection"
    return profile


def _run_profiled_diagnostic_case(family: str) -> object:
    sim = ef_py.SimulationKernel()
    sim.reset(20260611)
    assert sim.load_database(_DB_PATH)
    attacker_id, target_id = _spawn_structured_f16_pair(sim)

    ok = sim.debug_apply_profiled_local_proximity_hit_with_velocity(
        attacker_id,
        target_id,
        -0.753,
        7.1,
        0.0,
        _warhead_profile(family),
        0.0,
        -900.0,
        0.0,
    )
    assert ok
    return sim.export_recent_engagement_events()


def _run_no_detonation_diagnostic_case() -> object:
    sim = _make_baseline_kernel()
    sim.set_time_step(0.02)

    fuze = ef_py.FuzeProfile()
    fuze.type = "radar_proximity"
    fuze.trigger_radius_m = 35.0
    fuze.delay_s = 0.0
    fuze.reliability = 0.0
    fuze.synthetic = False
    fuze.provenance = "test_continuous_rod_diagnostic_projection_no_detonation"

    tuning = sim.get_missile_tuning()
    tuning.fuze_profile = fuze
    tuning.has_fuze_profile = True
    tuning.warhead_profile = _warhead_profile("continuous_rod")
    tuning.has_warhead_profile = True
    sim.set_missile_tuning(tuning)

    blue_id, red_id = _spawn_geometry_pair(
        sim,
        red_x=13000.0,
        red_y=9000.0,
        red_heading=270.0,
        red_vx=-260.0,
        red_vy=0.0,
    )
    missile_id = int(sim.fire_missile(blue_id, red_id))
    assert missile_id > 0

    result = _drive_missile_with_truth_track(
        sim,
        missile_id,
        red_id,
        max_steps=3600,
    )
    assert not bool(result["missile_active"])
    return sim.export_recent_engagement_events()


def _diagnostic_rows(events: object) -> list[dict[str, object]]:
    return probe._lethality_chain_rows(
        episode=7,
        step=12,
        sim_time_s=4.5,
        engagement_events=events,
    )


def _stage_rows(rows: list[dict[str, object]], stage: str) -> list[dict[str, object]]:
    return [row for row in rows if str(row.get("stage", "")) == stage]


def test_diagnostics_explain_standard_continuous_rod_facts() -> None:
    rows = _diagnostic_rows(_run_profiled_diagnostic_case("continuous_rod"))
    warhead_rows = _stage_rows(rows, "warhead_mechanism")
    component_rows = _stage_rows(rows, "component_load")

    assert len(warhead_rows) == 1
    assert warhead_rows[0]["source_event_kind"] == "WarheadMechanismEvent"
    assert warhead_rows[0]["mechanism_family"] == "continuous_rod"
    assert float(warhead_rows[0]["rod_cut_margin"]) > 0.0
    assert component_rows
    assert all(row["source_event_kind"] == "ComponentLoadEvent" for row in component_rows)
    assert any(float(row["rod_cut_margin"]) > 0.0 for row in component_rows)
    assert all(
        str(row["component_load_source"]) == "spatial_component_projection"
        for row in component_rows
    )

    snapshot = probe._lethality_chain_snapshot_columns(rows)
    assert snapshot["lethality_chain_mechanism_family"] == "continuous_rod"
    assert float(snapshot["lethality_chain_rod_cut_margin"]) == float(
        warhead_rows[0]["rod_cut_margin"]
    )
    assert float(snapshot["lethality_chain_component_rod_cut_margin"]) == float(
        component_rows[-1]["rod_cut_margin"]
    )


def test_diagnostics_keep_non_rod_cut_facts_zero() -> None:
    rows = _diagnostic_rows(_run_profiled_diagnostic_case("blast_fragmentation"))
    warhead_rows = _stage_rows(rows, "warhead_mechanism")
    component_rows = _stage_rows(rows, "component_load")

    assert len(warhead_rows) == 1
    assert warhead_rows[0]["source_event_kind"] == "WarheadMechanismEvent"
    assert warhead_rows[0]["mechanism_family"] == "blast_fragmentation"
    assert float(warhead_rows[0]["rod_cut_margin"]) == 0.0
    assert component_rows
    assert all(row["source_event_kind"] == "ComponentLoadEvent" for row in component_rows)
    assert all(float(row["rod_cut_margin"]) == 0.0 for row in component_rows)

    snapshot = probe._lethality_chain_snapshot_columns(rows)
    assert snapshot["lethality_chain_mechanism_family"] == "blast_fragmentation"
    assert float(snapshot["lethality_chain_rod_cut_margin"]) == 0.0
    assert float(snapshot["lethality_chain_component_rod_cut_margin"]) == 0.0


def test_no_detonation_does_not_synthesize_rod_diagnostic_rows() -> None:
    events = _run_no_detonation_diagnostic_case()
    rows = _diagnostic_rows(events)
    stages = {str(row["stage"]) for row in rows}

    assert str(events.effects_events[0].outcome_state) == "fuze_no_detonation"
    assert "nearest_approach" in stages
    assert "fuze" in stages
    assert "warhead_mechanism" not in stages
    assert "spatial_coverage" not in stages
    assert "component_load" not in stages

    snapshot = probe._lethality_chain_snapshot_columns(rows)
    assert snapshot["lethality_chain_fuze_triggered"] == 0
    assert snapshot["lethality_chain_fuze_failure_reason"] == "fuze_no_detonation"
    assert math.isnan(float(snapshot["lethality_chain_rod_cut_margin"]))
    assert math.isnan(float(snapshot["lethality_chain_component_rod_cut_margin"]))
