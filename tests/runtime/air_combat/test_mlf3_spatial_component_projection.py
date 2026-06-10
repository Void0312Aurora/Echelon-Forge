from __future__ import annotations

from dataclasses import dataclass

from tests.runtime.air_combat.weapon_guidance_realism.helpers import (
    _DB_PATH,
    _spawn_structured_f16_pair,
    ef_py,
)


ComponentKey = tuple[str, str]


@dataclass(frozen=True)
class ComponentProjectionCase:
    events: object
    effects: object
    spatial: object
    component_loads: list[object]
    loads_by_component: dict[ComponentKey, object]
    damage_report: object
    target_active: bool


def _generic_synthetic_warhead_profile() -> object:
    profile = ef_py.WarheadProfile()
    profile.family = "blast_fragmentation"
    profile.mass_kg = 12.0
    profile.lethal_radius_m = 35.0
    profile.damage_scalar = 90.0
    profile.synthetic = True
    profile.damage_scalar_synthetic = True
    profile.provenance = "test_mlf3d_spatial_component_projection_generic_research"
    return profile


def _component_key(load: object) -> ComponentKey:
    return str(load.component_name), str(load.component_system)


def _assert_component_loads_match_effect_rows(
    effects: object,
    component_loads: list[object],
) -> None:
    source_rows = [
        row
        for row in effects.component_mechanism_load_rows
        if str(row.component_name) or str(row.component_system)
    ]
    rows_by_component = {_component_key(row): row for row in source_rows}

    assert source_rows
    assert len(rows_by_component) == len(source_rows)
    assert len(component_loads) == len(source_rows)

    for load in component_loads:
        key = _component_key(load)
        assert key in rows_by_component
        row = rows_by_component[key]

        assert str(load.header.stage) == "component_load"
        assert str(load.header.status) == "projected"
        assert str(load.header.fidelity_mode) == "research_runtime"
        assert str(load.header.evidence_level) == "engineering_assumption"
        assert str(load.header.reason) == "generic_research_component_load_projection"
        assert str(load.component_name) == str(row.component_name)
        assert str(load.component_system) == str(row.component_system)
        assert str(load.component_redundancy_group_id) == str(
            row.component_redundancy_group_id
        )
        assert not bool(load.direct_hit)
        assert not bool(row.direct_hit)
        assert str(load.load_source) == "spatial_component_projection"
        assert float(load.distance_m) == float(row.distance_m)
        assert float(load.effect_scale) == float(row.effect_scale)
        assert float(load.fragment_energy_j) == float(row.mechanism_fragment_energy_j)
        assert float(load.fragment_density_per_m2) == float(
            row.mechanism_fragment_areal_density_per_m2
        )
        assert float(load.blast_overpressure_kpa) == float(
            row.mechanism_blast_overpressure_kpa
        )
        assert not hasattr(load, "component_failure_probability")
        assert not hasattr(load, "failure_probability")
        assert not bool(row.component_failure_probability_authority)
        assert not bool(row.component_failure_probability_calibrated)
        assert not bool(row.component_failure_probability_component_specific)


def _assert_no_downstream_kill_or_real_parameter_claims(
    events: object,
    effects: object,
    damage_report: object,
    target_id: int,
    target_active: bool,
) -> None:
    assert len(events.launch_events) == 0
    assert str(effects.trigger_type) == "debug_profiled_local_proximity_hit"
    assert str(effects.effect_family) == "blast_fragmentation"
    assert bool(effects.warhead_profile_synthetic)
    assert bool(effects.damage_scalar_synthetic)
    assert float(effects.warhead_mass_kg) == 12.0
    assert float(effects.warhead_lethal_radius_m) == 35.0
    assert not bool(effects.direct_hitbox_intersection)

    assert int(effects.target.entity_id) == int(target_id)
    assert int(damage_report.target.entity_id) == int(target_id)
    assert int(damage_report.source_event_id) == int(effects.event_id)
    assert float(damage_report.hp_delta) == 0.0
    assert not bool(damage_report.destroyed)
    assert not bool(damage_report.mission_kill)
    assert not bool(damage_report.mobility_kill)
    assert not bool(damage_report.sensor_kill)
    assert not bool(damage_report.survivability_kill)
    assert not bool(damage_report.forced_landing)
    assert not bool(damage_report.flight_control_kill)
    assert not bool(damage_report.propulsion_kill)
    assert not bool(damage_report.crew_kill)
    assert str(damage_report.loss_state_to) != "lost"
    assert target_active

    assert int(effects.component_failure_count) == 0
    assert not bool(effects.component_failure_probability_calibrated)
    assert not bool(effects.vulnerability_pk_authority)
    assert not bool(effects.vulnerability_calibrated_evidence)
    assert not bool(effects.vulnerability_deterministic_fuze_authority)
    assert not bool(effects.vulnerability_evidence_dataset_valid)
    assert str(effects.vulnerability_calibration_status) == "unvalidated"

    assert list(events.component_damage_events) == []
    assert list(events.platform_consequence_events) == []
    assert list(events.structural_breakup_events) == []
    assert list(events.lifecycle_transition_events) == []
    assert list(events.training_projection_events) == []

    real_model_text = " ".join(
        [
            str(effects.effect_family),
            str(effects.fuze_type),
            str(effects.fuze_signature_source),
            str(effects.vulnerability_evidence_dataset_ref),
            str(effects.vulnerability_evidence_source_ref),
            str(effects.vulnerability_evidence_validation_artifact_ref),
            str(effects.producer_node_id),
        ]
    ).lower()
    assert "aim-120" not in real_model_text
    assert "aim120" not in real_model_text
    assert "mq-9" not in real_model_text
    assert "mq9" not in real_model_text


def _run_profiled_component_projection_case(
    local: tuple[float, float, float],
    velocity: tuple[float, float, float],
) -> ComponentProjectionCase:
    sim = ef_py.SimulationKernel()
    sim.reset(20260610)
    assert sim.load_database(_DB_PATH)
    attacker_id, target_id = _spawn_structured_f16_pair(sim)

    ok = sim.debug_apply_profiled_local_proximity_hit_with_velocity(
        attacker_id,
        target_id,
        float(local[0]),
        float(local[1]),
        float(local[2]),
        _generic_synthetic_warhead_profile(),
        float(velocity[0]),
        float(velocity[1]),
        float(velocity[2]),
    )
    assert ok

    events = sim.export_recent_engagement_events()
    assert len(events.effects_events) == 1
    assert len(events.warhead_mechanism_events) == 1
    assert len(events.spatial_coverage_events) == 1
    assert len(events.damage_reports) == 1
    assert len(events.component_load_events) > 0

    effects = events.effects_events[0]
    warhead = events.warhead_mechanism_events[0]
    spatial = events.spatial_coverage_events[0]
    component_loads = list(events.component_load_events)
    damage_report = events.damage_reports[0]

    assert str(warhead.header.stage) == "warhead_mechanism"
    assert str(warhead.header.status) == "applied"
    assert str(warhead.header.fidelity_mode) == "research_runtime"
    assert str(warhead.header.evidence_level) == "engineering_assumption"
    assert str(warhead.header.reason) == "generic_research_synthetic_warhead_profile"
    assert str(warhead.mechanism_family) == "blast_fragmentation"
    assert float(warhead.warhead_mass_kg) == 12.0
    assert float(warhead.lethal_radius_m) == 35.0

    assert str(spatial.header.stage) == "spatial_coverage"
    assert str(spatial.header.status) == "projected"
    assert str(spatial.header.fidelity_mode) == "research_runtime"
    assert str(spatial.header.evidence_level) == "engineering_assumption"
    assert str(spatial.header.reason) == "generic_research_spatial_projection"
    assert int(spatial.sample_count) == int(effects.warhead_spatial_sample_count)
    assert int(spatial.projected_hitbox_count) == int(effects.projected_hitbox_count)
    assert float(spatial.energy_scale) == float(effects.warhead_spatial_energy_scale)
    assert float(spatial.pattern_scale) == float(effects.warhead_spatial_pattern_scale)
    assert int(spatial.projected_hitbox_count) > 0

    _assert_component_loads_match_effect_rows(effects, component_loads)
    _assert_no_downstream_kill_or_real_parameter_claims(
        events,
        effects,
        damage_report,
        int(target_id),
        bool(sim.is_unit_active(target_id)),
    )

    loads_by_component = {_component_key(load): load for load in component_loads}
    assert len(loads_by_component) == len(component_loads)
    return ComponentProjectionCase(
        events=events,
        effects=effects,
        spatial=spatial,
        component_loads=component_loads,
        loads_by_component=loads_by_component,
        damage_report=damage_report,
        target_active=bool(sim.is_unit_active(target_id)),
    )


def test_mlf3d_component_loads_track_spatial_coverage_and_local_projection() -> None:
    velocity = (900.0, -250.0, 0.0)
    right_near = _run_profiled_component_projection_case(
        (-0.753, 6.0, 0.0),
        velocity,
    )
    right_far = _run_profiled_component_projection_case(
        (-0.753, 10.0, 0.0),
        velocity,
    )
    left_near = _run_profiled_component_projection_case(
        (-0.753, -6.0, 0.0),
        velocity,
    )

    right_aileron = ("right_aileron_actuator", "flight_control")
    left_aileron = ("left_aileron_actuator", "flight_control")
    right_fuel = ("right_wing_fuel_cell", "fuel")
    left_fuel = ("left_wing_fuel_cell", "fuel")

    assert right_aileron in right_near.loads_by_component
    assert right_aileron in right_far.loads_by_component
    assert left_aileron in left_near.loads_by_component
    assert left_aileron not in right_near.loads_by_component
    assert right_aileron not in left_near.loads_by_component
    assert right_fuel in right_near.loads_by_component
    assert left_fuel in left_near.loads_by_component

    near_load = right_near.loads_by_component[right_aileron]
    far_load = right_far.loads_by_component[right_aileron]
    assert float(right_far.effects.miss_distance_m) > float(
        right_near.effects.miss_distance_m
    )
    assert float(right_far.spatial.energy_scale) < float(
        right_near.spatial.energy_scale
    )
    assert float(far_load.distance_m) > float(near_load.distance_m)
    assert float(far_load.effect_scale) < float(near_load.effect_scale)
    assert float(far_load.fragment_density_per_m2) < float(
        near_load.fragment_density_per_m2
    )
    assert float(far_load.blast_overpressure_kpa) < float(
        near_load.blast_overpressure_kpa
    )

    left_load = left_near.loads_by_component[left_aileron]
    assert str(near_load.component_system) == str(left_load.component_system)
    assert str(near_load.load_source) == str(left_load.load_source)
    assert str(left_load.component_name).startswith("left_")
    assert str(near_load.component_name).startswith("right_")
    assert right_near.target_active
    assert right_far.target_active
    assert left_near.target_active
