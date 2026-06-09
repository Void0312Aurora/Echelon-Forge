from __future__ import annotations

import math

from tests.runtime.air_combat.weapon_guidance_realism.helpers import (
    _drive_missile_with_truth_track,
    _make_baseline_kernel,
    _spawn_geometry_pair,
)


def _run_live_structured_air_detonation() -> tuple[object, int, int, int]:
    sim = _make_baseline_kernel()
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
    assert sim.is_unit_active(red_id)
    return sim.export_recent_engagement_events(), missile_id, red_id, blue_id


def test_mlf3_live_detonation_exports_standard_warhead_spatial_and_component_events() -> None:
    events, missile_id, red_id, _blue_id = _run_live_structured_air_detonation()

    assert len(events.launch_events) == 1
    assert len(events.nearest_approach_events) == 1
    assert len(events.fuze_evaluation_events) == 1
    assert len(events.effects_events) == 1
    assert len(events.warhead_mechanism_events) == 1
    assert len(events.spatial_coverage_events) == 1
    assert len(events.damage_reports) == 1

    launch = events.launch_events[0]
    nearest = events.nearest_approach_events[0]
    fuze = events.fuze_evaluation_events[0]
    effects = events.effects_events[0]
    warhead = events.warhead_mechanism_events[0]
    spatial = events.spatial_coverage_events[0]
    damage_report = events.damage_reports[0]

    assert int(launch.spawned_munition.entity_id) == missile_id
    assert int(effects.munition.entity_id) == missile_id
    assert int(effects.target.entity_id) == red_id
    assert str(effects.trigger_type) == "proximity_fuze"
    assert str(effects.outcome_state) == "damage_applied"
    assert math.isfinite(float(effects.miss_distance_m))
    assert float(effects.miss_distance_m) < float(effects.warhead_lethal_radius_m)

    assert str(nearest.header.stage) == "nearest_approach"
    assert str(nearest.header.reason) == "fuze_armed"
    assert int(nearest.header.chain_id) == int(launch.event_id)
    assert int(nearest.header.munition.entity_id) == missile_id
    assert int(nearest.header.target.entity_id) == red_id

    assert str(fuze.header.stage) == "fuze_evaluation"
    assert str(fuze.header.reason) == "fuze_armed"
    assert int(fuze.header.chain_id) == int(launch.event_id)
    assert int(fuze.header.parent_event_id) == int(nearest.header.event_id)
    assert int(fuze.header.munition.entity_id) == missile_id
    assert int(fuze.header.target.entity_id) == red_id
    assert bool(fuze.armed)
    assert bool(fuze.triggered)
    assert str(fuze.failure_reason) == ""

    assert str(warhead.header.stage) == "warhead_mechanism"
    assert str(warhead.header.status) == "applied"
    assert str(warhead.header.fidelity_mode) == "research_runtime"
    assert str(warhead.header.evidence_level) == "engineering_assumption"
    assert str(warhead.header.producer_node_id) == "damage_system.warhead_effects"
    assert int(warhead.header.chain_id) == int(launch.event_id)
    assert int(warhead.header.parent_event_id) == int(effects.event_id)
    assert int(warhead.header.munition.entity_id) == missile_id
    assert int(warhead.header.target.entity_id) == red_id
    assert str(warhead.mechanism_family) == str(effects.effect_family)
    assert float(warhead.fragment_energy_j) == float(effects.mechanism_fragment_energy_j)
    assert float(warhead.blast_overpressure_kpa) == float(
        effects.mechanism_blast_overpressure_kpa
    )
    assert float(warhead.fragment_energy_j) > 0.0
    assert float(warhead.blast_overpressure_kpa) > 0.0

    assert str(spatial.header.stage) == "spatial_coverage"
    assert str(spatial.header.status) == "projected"
    assert str(spatial.header.fidelity_mode) == "research_runtime"
    assert str(spatial.header.evidence_level) == "engineering_assumption"
    assert int(spatial.header.chain_id) == int(launch.event_id)
    assert int(spatial.header.parent_event_id) == int(effects.event_id)
    assert int(spatial.header.munition.entity_id) == missile_id
    assert int(spatial.header.target.entity_id) == red_id
    assert int(spatial.sample_count) == int(effects.warhead_spatial_sample_count)
    assert float(spatial.energy_scale) == float(effects.warhead_spatial_energy_scale)
    assert int(spatial.sample_count) > 0

    source_rows = [
        row
        for row in effects.component_mechanism_load_rows
        if str(row.component_name) or str(row.component_system)
    ]
    component_loads = list(events.component_load_events)
    assert source_rows
    assert len(component_loads) == len(source_rows)

    for load, row in zip(component_loads, source_rows):
        assert str(load.header.stage) == "component_load"
        assert str(load.header.status) == "projected"
        assert str(load.header.fidelity_mode) == "research_runtime"
        assert str(load.header.evidence_level) == "engineering_assumption"
        assert int(load.header.chain_id) == int(launch.event_id)
        assert int(load.header.parent_event_id) == int(effects.event_id)
        assert int(load.header.munition.entity_id) == missile_id
        assert int(load.header.target.entity_id) == red_id
        assert str(load.component_name) == str(row.component_name)
        assert str(load.component_system) == str(row.component_system)
        assert bool(load.direct_hit) == bool(row.direct_hit)
        assert float(load.distance_m) == float(row.distance_m)
        assert float(load.effect_scale) == float(row.effect_scale)
        assert float(load.fragment_energy_j) == float(row.mechanism_fragment_energy_j)
        assert float(load.blast_overpressure_kpa) == float(
            row.mechanism_blast_overpressure_kpa
        )
        assert str(load.load_source) in {
            "direct_component_hit",
            "spatial_component_projection",
        }

    assert int(damage_report.source_event_id) == int(effects.event_id)
    assert float(damage_report.hp_delta) == 0.0
    assert not bool(damage_report.destroyed)
    assert str(damage_report.loss_state_to) != "lost"
