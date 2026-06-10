from __future__ import annotations

from dataclasses import dataclass

from tests.runtime.air_combat.weapon_guidance_realism.helpers import (
    _DB_PATH,
    _spawn_structured_f16_pair,
    ef_py,
)


@dataclass(frozen=True)
class _RodGeometryCase:
    effects: object
    warhead: object
    component_loads: list[object]


def _warhead_profile() -> object:
    profile = ef_py.WarheadProfile()
    profile.family = "continuous_rod"
    profile.mass_kg = 12.0
    profile.lethal_radius_m = 35.0
    profile.damage_scalar = 90.0
    profile.synthetic = True
    profile.damage_scalar_synthetic = True
    profile.provenance = "test_mlf4_generic_rod_geometry"
    return profile


def _run_profiled_rod_geometry_case(
    local: tuple[float, float, float],
    velocity: tuple[float, float, float],
    attitude_deg: tuple[float, float, float] | None = None,
) -> _RodGeometryCase:
    sim = ef_py.SimulationKernel()
    sim.reset(20260611)
    assert sim.load_database(_DB_PATH)
    attacker_id, target_id = _spawn_structured_f16_pair(sim)
    profile = _warhead_profile()

    if attitude_deg is None:
        ok = sim.debug_apply_profiled_local_proximity_hit_with_velocity(
            attacker_id,
            target_id,
            float(local[0]),
            float(local[1]),
            float(local[2]),
            profile,
            float(velocity[0]),
            float(velocity[1]),
            float(velocity[2]),
        )
    else:
        ok = sim.debug_apply_profiled_local_proximity_hit_with_velocity_and_attitude(
            attacker_id,
            target_id,
            float(local[0]),
            float(local[1]),
            float(local[2]),
            profile,
            float(velocity[0]),
            float(velocity[1]),
            float(velocity[2]),
            float(attitude_deg[0]),
            float(attitude_deg[1]),
            float(attitude_deg[2]),
        )
    assert ok

    events = sim.export_recent_engagement_events()
    assert len(events.effects_events) == 1
    assert len(events.warhead_mechanism_events) == 1
    assert len(events.component_load_events) > 0

    effects = events.effects_events[0]
    warhead = events.warhead_mechanism_events[0]
    assert str(effects.effect_family) == "continuous_rod"
    assert str(warhead.mechanism_family) == "continuous_rod"
    assert float(effects.mechanism_rod_cut_margin) == float(warhead.rod_cut_margin)
    assert float(effects.mechanism_rod_cut_margin) > 0.0

    return _RodGeometryCase(
        effects=effects,
        warhead=warhead,
        component_loads=list(events.component_load_events),
    )


def test_mlf4c_continuous_rod_cut_margin_falls_with_range() -> None:
    velocity = (0.0, -900.0, 0.0)
    near = _run_profiled_rod_geometry_case((-0.753, 7.1, 0.0), velocity)
    far = _run_profiled_rod_geometry_case((-0.753, 14.0, 0.0), velocity)

    assert float(near.effects.miss_distance_m) < float(far.effects.miss_distance_m)
    assert float(near.effects.warhead_spatial_hit_estimate) > float(
        far.effects.warhead_spatial_hit_estimate
    )
    assert float(near.effects.mechanism_rod_cut_margin) > float(
        far.effects.mechanism_rod_cut_margin
    )
    assert float(near.effects.component_primary_mechanism_rod_cut_margin) > float(
        far.effects.component_primary_mechanism_rod_cut_margin
    )


def test_mlf4c_continuous_rod_cut_margin_tracks_side_sweep_axis() -> None:
    local_wing = (-0.753, 7.1, 0.0)
    broadside = _run_profiled_rod_geometry_case(local_wing, (0.0, -900.0, 0.0))
    axial = _run_profiled_rod_geometry_case(local_wing, (-900.0, 0.0, 0.0))

    assert float(broadside.effects.miss_distance_m) == float(axial.effects.miss_distance_m)
    assert float(broadside.effects.warhead_spatial_pattern_scale) > float(
        axial.effects.warhead_spatial_pattern_scale
    )
    assert float(broadside.effects.warhead_spatial_hit_estimate) > float(
        axial.effects.warhead_spatial_hit_estimate
    )
    assert float(broadside.effects.mechanism_rod_cut_margin) > float(
        axial.effects.mechanism_rod_cut_margin
    )


def test_mlf4c_continuous_rod_cut_margin_tracks_local_aspect() -> None:
    velocity = (0.0, -900.0, 0.0)
    beam = _run_profiled_rod_geometry_case((-0.753, 7.1, 0.0), velocity)
    tail = _run_profiled_rod_geometry_case((-7.1, 0.753, 0.0), velocity)

    assert str(beam.effects.vulnerability_aspect_bucket) == "beam"
    assert str(tail.effects.vulnerability_aspect_bucket) == "tail"
    assert abs(float(beam.effects.miss_distance_m) - float(tail.effects.miss_distance_m)) < 1.0e-9
    assert float(beam.effects.vulnerability_aspect_scale) > float(
        tail.effects.vulnerability_aspect_scale
    )
    assert float(beam.effects.mechanism_rod_cut_margin) > float(
        tail.effects.mechanism_rod_cut_margin
    )


def test_mlf4c_continuous_rod_cut_margin_tracks_orientation_axis() -> None:
    local_wing = (-0.753, 7.1, 0.0)
    velocity = (0.0, -900.0, 0.0)
    forward_oriented = _run_profiled_rod_geometry_case(
        local_wing,
        velocity,
        (0.0, 0.0, 0.0),
    )
    right_oriented = _run_profiled_rod_geometry_case(
        local_wing,
        velocity,
        (90.0, 0.0, 0.0),
    )

    assert abs(float(forward_oriented.effects.warhead_orientation_axis_forward)) == 1.0
    assert abs(float(right_oriented.effects.warhead_orientation_axis_right)) == 1.0
    assert float(forward_oriented.effects.warhead_orientation_pattern_scale) > float(
        right_oriented.effects.warhead_orientation_pattern_scale
    )
    assert float(forward_oriented.effects.warhead_spatial_pattern_scale) > float(
        right_oriented.effects.warhead_spatial_pattern_scale
    )
    assert float(forward_oriented.effects.mechanism_rod_cut_margin) > float(
        right_oriented.effects.mechanism_rod_cut_margin
    )
