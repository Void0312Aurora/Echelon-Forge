from __future__ import annotations

from .helpers import *


def _make_f16_wing_without_components_override(name: str) -> dict:
    with open(
        resolve_repo_path("examples", "config", "database", "aircraft", "units", "f16c_block50.json"),
        "r",
        encoding="utf-8",
    ) as handle:
        unit = json.load(handle)
    unit["name"] = name
    damage_model = unit["damage_model"]
    damage_model.pop("vulnerability", None)
    for hitbox in damage_model["hitboxes"]:
        systems = {str(system) for system in hitbox.get("systems", [])}
        if {"wings", "flight_control", "fuel"}.issubset(systems):
            hitbox["components"] = []
    return unit


def _local_hit_event_for_target(
    target_type: str,
    family: str,
    local: tuple[float, float, float],
    *,
    damage: float = 90.0,
    radius: float = 35.0,
    velocity: tuple[float, float, float] = (900.0, -250.0, 0.0),
    overrides: list[dict] | None = None,
) -> tuple[object, object]:
    sim = _kernel_with_unit_overrides(overrides or [])
    attacker_id, target_id = _spawn_attacker_and_named_target(sim, target_type)
    ok = sim.debug_apply_profiled_local_proximity_hit_with_velocity(
        attacker_id,
        target_id,
        float(local[0]),
        float(local[1]),
        float(local[2]),
        _make_warhead_profile(family, damage=damage, radius=radius),
        float(velocity[0]),
        float(velocity[1]),
        float(velocity[2]),
    )
    if not ok:
        raise AssertionError(f"profiled local hit failed for {family} against {target_type}")
    events = sim.export_recent_engagement_events()
    if len(events.effects_events) != 1:
        raise AssertionError(f"expected one effects event for {family} against {target_type}")
    if len(events.damage_reports) != 1:
        raise AssertionError(f"expected one damage report for {family} against {target_type}")
    return events.effects_events[0], events.damage_reports[0]


def _component_row_by_name(event: object) -> dict[str, object]:
    return {str(row.component_name): row for row in event.component_mechanism_load_rows}


class DefaultEffectsModularizationRuntimeMixin:
    def test_dfm_p4_direct_component_hit_populates_primary_component_event_fields(self) -> None:
        event, report = _local_hit_event_for_target(
            "F-16C_Block50",
            "blast_fragmentation",
            (-0.8, 4.1, 0.0),
        )

        self.assertEqual(str(event.effect_family), "blast_fragmentation")
        self.assertTrue(bool(event.direct_hitbox_intersection))
        self.assertEqual(int(event.projected_hitbox_count), 0)
        self.assertEqual(int(event.component_hit_count), 1)
        self.assertEqual(str(event.component_primary_name), "right_aileron_actuator")
        self.assertEqual(str(event.component_primary_system), "flight_control")
        self.assertEqual(
            str(event.component_primary_redundancy_group_id),
            "lateral_flight_control_actuators",
        )
        self.assertEqual(int(event.component_redundancy_group_member_count), 2)
        self.assertFalse(bool(event.component_primary_critical))
        self.assertLess(float(event.component_primary_integrity), 1.0)
        self.assertEqual(str(event.component_failure_probability_source), "synthetic_sigmoid")
        self.assertFalse(bool(event.component_failure_probability_calibrated))
        self.assertGreater(float(event.component_failure_probability), 0.0)
        self.assertGreaterEqual(float(event.component_failure_sample), 0.0)
        self.assertLessEqual(float(event.component_failure_sample), 1.0)
        self.assertGreater(int(event.component_failure_count), 0)

        rows = list(event.component_mechanism_load_rows)
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(str(row.component_name), "right_aileron_actuator")
        self.assertEqual(str(row.component_system), "flight_control")
        self.assertTrue(bool(row.direct_hit))
        self.assertAlmostEqual(float(row.distance_m), 0.0, delta=1.0e-6)
        self.assertEqual(str(row.component_failure_probability_source), "synthetic_sigmoid")
        self.assertAlmostEqual(
            float(row.component_failure_probability),
            float(event.component_failure_probability),
            delta=1.0e-12,
        )
        self.assertAlmostEqual(
            float(row.component_failure_sample),
            float(event.component_failure_sample),
            delta=1.0e-12,
        )
        self.assertGreater(float(event.mechanism_fragment_energy_j), 0.0)
        self.assertGreater(float(event.mechanism_blast_overpressure_kpa), 0.0)
        self.assertGreater(int(event.warhead_spatial_sample_count), 100)
        self.assertAlmostEqual(float(report.hp_delta), 0.0, delta=1.0e-6)
        self.assertLess(float(report.system_health_delta), 0.0)
        self.assertFalse(bool(report.destroyed))

    def test_dfm_p4_direct_hit_without_component_uses_protected_system_fallback(self) -> None:
        target_name = "F-16C_A2_DFM_P4_ProtectedFallback_Test"
        event, report = _local_hit_event_for_target(
            target_name,
            "blast_fragmentation",
            (-0.8, 4.1, 0.0),
            overrides=[_make_f16_wing_without_components_override(target_name)],
        )

        self.assertTrue(bool(event.direct_hitbox_intersection))
        self.assertEqual(int(event.projected_hitbox_count), 0)
        self.assertEqual(int(event.component_hit_count), 0)
        self.assertEqual(list(event.component_mechanism_load_rows), [])
        self.assertEqual(str(event.component_primary_name), "")
        self.assertEqual(str(event.component_primary_system), "")
        self.assertAlmostEqual(float(event.component_primary_integrity), 1.0, delta=1.0e-9)
        self.assertEqual(int(event.component_redundancy_group_member_count), 0)
        self.assertGreater(float(event.component_threshold_scale), 1.0)
        self.assertEqual(str(event.component_failure_probability_source), "synthetic_sigmoid")
        self.assertGreater(float(event.component_failure_probability), 0.0)
        self.assertGreaterEqual(float(event.component_failure_sample), 0.0)
        self.assertLessEqual(float(event.component_failure_sample), 1.0)
        self.assertGreater(int(event.component_failure_count), 0)
        self.assertGreater(float(event.mechanism_fragment_energy_j), 0.0)
        self.assertGreater(float(event.mechanism_blast_overpressure_kpa), 0.0)
        self.assertGreater(int(event.warhead_spatial_sample_count), 100)
        self.assertAlmostEqual(float(report.hp_delta), 0.0, delta=1.0e-6)
        self.assertLess(float(report.system_health_delta), 0.0)
        self.assertEqual(str(report.loss_state_to), "combat_capable")
        self.assertFalse(bool(report.destroyed))

    def test_dfm_p4_broad_spatial_near_miss_projects_boxes_and_component_rows(self) -> None:
        event, report = _local_hit_event_for_target(
            "F-16C_Block50",
            "blast_fragmentation",
            (-0.753, 7.1, 0.0),
        )

        self.assertEqual(str(event.effect_family), "blast_fragmentation")
        self.assertFalse(bool(event.direct_hitbox_intersection))
        self.assertGreater(int(event.projected_hitbox_count), 1)
        self.assertGreater(int(event.component_hit_count), int(event.projected_hitbox_count))
        self.assertEqual(str(event.component_primary_name), "flight_control_computer")
        self.assertEqual(str(event.component_primary_system), "flight_control")
        self.assertEqual(str(event.component_failure_probability_source), "synthetic_sigmoid")
        self.assertGreater(float(event.spatial_effect_scale), 0.0)
        self.assertLess(float(event.spatial_effect_scale), 1.0)
        self.assertGreater(float(event.mechanism_effect_scale), float(event.spatial_effect_scale))
        self.assertGreater(float(event.mechanism_fragment_energy_j), 0.0)
        self.assertGreater(float(event.mechanism_blast_overpressure_kpa), 0.0)
        self.assertGreater(int(event.warhead_spatial_sample_count), 1000)
        self.assertGreater(float(event.warhead_spatial_hit_estimate), 0.0)
        self.assertGreater(float(event.warhead_spatial_hit_fraction), 0.0)
        self.assertLess(float(event.warhead_spatial_hit_fraction), 0.10)

        rows = _component_row_by_name(event)
        self.assertEqual(len(rows), int(event.component_hit_count))
        self.assertTrue(
            {
                "right_aileron_actuator",
                "right_wing_fuel_cell",
                "flight_control_computer",
                "engine_fuel_control_unit",
            }.issubset(set(rows)),
        )
        for row in rows.values():
            self.assertFalse(bool(row.direct_hit))
            self.assertGreater(float(row.distance_m), 0.0)
            self.assertGreater(float(row.effect_scale), 0.0)
            self.assertEqual(str(row.component_failure_probability_source), "synthetic_sigmoid")
        self.assertGreaterEqual(
            float(rows["right_aileron_actuator"].component_failure_sample),
            0.0,
        )
        self.assertLessEqual(
            float(rows["right_aileron_actuator"].component_failure_sample),
            1.0,
        )
        self.assertGreater(
            float(rows["flight_control_computer"].distance_m),
            float(rows["right_aileron_actuator"].distance_m),
        )
        self.assertAlmostEqual(float(report.hp_delta), 0.0, delta=1.0e-6)
        self.assertLess(float(report.system_health_delta), 0.0)
        self.assertFalse(bool(report.destroyed))

    def test_dfm_p4_component_limited_near_miss_does_not_expand_to_broad_box_projection(self) -> None:
        event, report = _local_hit_event_for_target(
            "F-16C_Block50",
            "hit_to_kill",
            (-0.753, 7.1, 0.0),
        )

        self.assertEqual(str(event.effect_family), "hit_to_kill")
        self.assertFalse(bool(event.direct_hitbox_intersection))
        self.assertEqual(int(event.projected_hitbox_count), 1)
        self.assertEqual(int(event.component_hit_count), 1)
        self.assertEqual(str(event.component_primary_name), "right_aileron_actuator")
        self.assertEqual(str(event.component_primary_system), "flight_control")
        self.assertEqual(str(event.component_failure_probability_source), "synthetic_sigmoid")
        self.assertEqual(int(event.warhead_spatial_sample_count), 1)
        self.assertGreater(float(event.warhead_spatial_hit_estimate), 0.0)
        self.assertGreater(float(event.warhead_spatial_energy_scale), 0.0)
        self.assertAlmostEqual(float(event.mechanism_fragment_energy_j), 0.0, delta=1.0e-9)
        self.assertAlmostEqual(float(event.mechanism_blast_overpressure_kpa), 0.0, delta=1.0e-9)
        self.assertGreater(float(event.mechanism_penetration_margin), 0.0)

        rows = list(event.component_mechanism_load_rows)
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(str(row.component_name), "right_aileron_actuator")
        self.assertFalse(bool(row.direct_hit))
        self.assertGreater(float(row.distance_m), 0.0)
        self.assertGreaterEqual(float(row.component_failure_sample), 0.0)
        self.assertLessEqual(float(row.component_failure_sample), 1.0)
        self.assertAlmostEqual(
            float(row.effect_scale),
            float(event.spatial_effect_scale),
            delta=1.0e-12,
        )
        self.assertEqual(str(row.component_failure_probability_source), "synthetic_sigmoid")
        self.assertAlmostEqual(float(report.hp_delta), 0.0, delta=1.0e-6)
        self.assertLess(float(report.system_health_delta), 0.0)
        self.assertFalse(bool(report.destroyed))
