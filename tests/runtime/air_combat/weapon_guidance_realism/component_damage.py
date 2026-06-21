from __future__ import annotations

from .helpers import *


class ComponentDamageRuntimeMixin:
  def test_phase3_componentized_hitbox_localizes_damage_within_wing(self) -> None:
    target_name = "F-16C_A2_ComponentWing_Test"
    overrides = [_make_f16_componentized_wing_override(target_name)]

    fuel_overlay, _, fuel_event = _profiled_local_hit_overlay_for_target(
      target_name,
      "blast_fragmentation",
      (-0.8, -2.8, 0.0),
      damage=90.0,
      radius=35.0,
      overrides=overrides,
    )
    control_overlay, _, control_event = _profiled_local_hit_overlay_for_target(
      target_name,
      "blast_fragmentation",
      (-0.8, 2.8, 0.0),
      damage=90.0,
      radius=35.0,
      overrides=overrides,
    )

    self.assertTrue(bool(fuel_event.direct_hitbox_intersection))
    self.assertTrue(bool(control_event.direct_hitbox_intersection))
    self.assertGreater(float(fuel_event.component_threshold_scale), 1.0)
    self.assertGreater(float(control_event.component_threshold_scale), 1.0)

    self.assertLess(fuel_overlay["fuel"], control_overlay["fuel"])
    self.assertGreater(fuel_overlay["fuel_leak"], control_overlay["fuel_leak"])
    self.assertAlmostEqual(fuel_overlay["flight_control"], 1.0, delta=1.0e-6)
    self.assertAlmostEqual(fuel_overlay["hydraulic"], 1.0, delta=1.0e-6)

    self.assertLess(control_overlay["flight_control"], fuel_overlay["flight_control"])
    self.assertLess(control_overlay["hydraulic"], fuel_overlay["hydraulic"])
    self.assertAlmostEqual(control_overlay["fuel"], 1.0, delta=1.0e-6)
    self.assertAlmostEqual(control_overlay["fuel_leak"], 0.0, delta=1.0e-6)

  def test_phase3_database_f16_component_geometry_reports_primary_component(self) -> None:
    fuel_overlay, _, fuel_event = _profiled_local_hit_overlay_for_target(
      "F-16C_Block50",
      "blast_fragmentation",
      (-0.8, -2.8, 0.0),
      damage=90.0,
      radius=35.0,
    )
    control_overlay, _, control_event = _profiled_local_hit_overlay_for_target(
      "F-16C_Block50",
      "blast_fragmentation",
      (-0.8, 4.1, 0.0),
      damage=90.0,
      radius=35.0,
    )

    self.assertTrue(bool(fuel_event.direct_hitbox_intersection))
    self.assertGreaterEqual(int(fuel_event.component_hit_count), 1)
    self.assertEqual(str(fuel_event.component_primary_name), "left_wing_fuel_cell")
    self.assertEqual(str(fuel_event.component_primary_system), "fuel")
    self.assertAlmostEqual(float(fuel_event.component_primary_redundancy_group), 1.0, delta=1.0e-6)
    self.assertEqual(str(fuel_event.component_primary_redundancy_group_id), "wing_fuel_cells")
    self.assertTrue(bool(fuel_event.component_primary_critical))
    self.assertLess(float(fuel_event.component_primary_integrity), 1.0)
    self.assertGreater(float(fuel_event.component_redundancy_group_availability), 0.0)
    self.assertEqual(int(fuel_event.component_redundancy_group_member_count), 2)
    self.assertLess(fuel_overlay["fuel"], 1.0)
    self.assertGreater(fuel_overlay["fuel_leak"], 0.0)
    self.assertAlmostEqual(fuel_overlay["flight_control"], 1.0, delta=1.0e-6)

    self.assertTrue(bool(control_event.direct_hitbox_intersection))
    self.assertEqual(int(control_event.component_hit_count), 1)
    self.assertEqual(str(control_event.component_primary_name), "right_aileron_actuator")
    self.assertEqual(str(control_event.component_primary_system), "flight_control")
    self.assertAlmostEqual(float(control_event.component_primary_redundancy_group), 2.0, delta=1.0e-6)
    self.assertEqual(
      str(control_event.component_primary_redundancy_group_id),
      "lateral_flight_control_actuators",
    )
    self.assertFalse(bool(control_event.component_primary_critical))
    self.assertLess(float(control_event.component_primary_integrity), 1.0)
    self.assertEqual(int(control_event.component_redundancy_group_member_count), 2)
    self.assertLess(control_overlay["flight_control"], 1.0)
    self.assertLess(control_overlay["hydraulic"], 1.0)
    self.assertAlmostEqual(control_overlay["fuel"], 1.0, delta=1.0e-6)

  def test_phase3_database_su35_component_geometry_reports_primary_component(self) -> None:
    fuel_overlay, _, fuel_event = _profiled_local_hit_overlay_for_target(
      "Su-35S_Flanker-E",
      "blast_fragmentation",
      (-2.0, -4.4, 0.0),
      damage=90.0,
      radius=35.0,
    )
    control_overlay, _, control_event = _profiled_local_hit_overlay_for_target(
      "Su-35S_Flanker-E",
      "blast_fragmentation",
      (-2.0, 6.2, 0.0),
      damage=90.0,
      radius=35.0,
    )

    self.assertTrue(bool(fuel_event.direct_hitbox_intersection))
    self.assertGreaterEqual(int(fuel_event.component_hit_count), 1)
    self.assertEqual(str(fuel_event.component_primary_name), "left_wing_fuel_cell")
    self.assertEqual(str(fuel_event.component_primary_system), "fuel")
    self.assertAlmostEqual(float(fuel_event.component_primary_redundancy_group), 1.0, delta=1.0e-6)
    self.assertEqual(str(fuel_event.component_primary_redundancy_group_id), "wing_fuel_cells")
    self.assertTrue(bool(fuel_event.component_primary_critical))
    self.assertLess(fuel_overlay["fuel"], 1.0)
    self.assertGreater(fuel_overlay["fuel_leak"], 0.0)
    self.assertAlmostEqual(fuel_overlay["flight_control"], 1.0, delta=1.0e-6)

    self.assertTrue(bool(control_event.direct_hitbox_intersection))
    self.assertEqual(int(control_event.component_hit_count), 1)
    self.assertEqual(str(control_event.component_primary_name), "right_elevon_actuator")
    self.assertEqual(str(control_event.component_primary_system), "flight_control")
    self.assertAlmostEqual(float(control_event.component_primary_redundancy_group), 2.0, delta=1.0e-6)
    self.assertEqual(
      str(control_event.component_primary_redundancy_group_id),
      "lateral_flight_control_actuators",
    )
    self.assertFalse(bool(control_event.component_primary_critical))
    self.assertLess(control_overlay["flight_control"], 1.0)
    self.assertLess(control_overlay["hydraulic"], 1.0)
    self.assertAlmostEqual(control_overlay["fuel"], 1.0, delta=1.0e-6)

  def test_phase3_engine_fuel_feed_damage_can_reduce_propulsion(self) -> None:
    storage_overlay, _, storage_event = _profiled_local_hit_overlay_for_target(
      "Su-35S_Flanker-E",
      "blast_fragmentation",
      (-2.0, -4.4, 0.0),
      damage=100.0,
      radius=35.0,
    )
    feed_overlay, _, feed_event = _profiled_local_hit_overlay_for_target(
      "Su-35S_Flanker-E",
      "blast_fragmentation",
      (-6.5, -1.4, -0.35),
      damage=100.0,
      radius=35.0,
    )

    self.assertEqual(str(storage_event.component_primary_name), "left_wing_fuel_cell")
    self.assertEqual(str(storage_event.component_primary_system), "fuel")
    self.assertLess(storage_overlay["fuel"], 1.0)
    self.assertGreater(storage_overlay["fuel_leak"], 0.0)
    self.assertAlmostEqual(storage_overlay["propulsion"], 1.0, delta=1.0e-6)

    self.assertEqual(str(feed_event.component_primary_name), "left_engine_fuel_feed")
    self.assertEqual(str(feed_event.component_primary_system), "fuel")
    self.assertLess(feed_overlay["fuel"], 1.0)
    self.assertGreater(feed_overlay["fuel_leak"], 0.0)
    self.assertLess(feed_overlay["propulsion"], storage_overlay["propulsion"])

  def test_phase2_lateral_fuel_storage_damage_tracks_fuel_imbalance(self) -> None:
    def run_case(local: tuple[float, float, float]) -> tuple[dict[str, float], dict[str, float], object]:
      sim = _kernel_with_unit_overrides([])
      sim.set_time_step(0.5)
      attacker_id, target_id = _spawn_attacker_and_named_target(sim, "Su-35S_Flanker-E")
      ok = sim.debug_apply_profiled_local_proximity_hit(
        attacker_id,
        target_id,
        float(local[0]),
        float(local[1]),
        float(local[2]),
        _make_warhead_profile("blast_fragmentation", damage=100.0, radius=35.0),
      )
      self.assertTrue(bool(ok))
      event = sim.export_recent_engagement_events().effects_events[-1]
      initial = _aircraft_damage_overlay(sim, target_id)
      for _ in range(20):
        sim.step()
      return initial, _aircraft_damage_overlay(sim, target_id), event

    wing_initial, wing_after, wing_event = run_case((-2.0, -4.4, 0.0))
    center_initial, _, center_event = run_case((-0.6, 0.0, -0.1))
    feed_initial, _, feed_event = run_case((-6.5, -1.4, -0.35))

    self.assertEqual(str(wing_event.component_primary_name), "left_wing_fuel_cell")
    self.assertEqual(str(wing_event.component_primary_system), "fuel")
    self.assertGreater(wing_initial["fuel_leak"], 0.0)
    self.assertGreater(wing_initial["fuel_imbalance"], 0.0)
    self.assertGreater(wing_initial["control_asymmetry"], 0.0)
    self.assertGreater(wing_after["control_asymmetry"], wing_initial["control_asymmetry"])
    self.assertLess(wing_after["roll_control"], wing_initial["roll_control"])
    self.assertAlmostEqual(wing_initial["propulsion"], 1.0, delta=1.0e-6)

    self.assertEqual(str(center_event.component_primary_name), "center_fuselage_fuel_cell")
    self.assertEqual(str(center_event.component_primary_system), "fuel")
    self.assertGreater(center_initial["fuel_leak"], 0.0)
    self.assertAlmostEqual(center_initial["fuel_imbalance"], 0.0, delta=1.0e-6)
    self.assertAlmostEqual(center_initial["control_asymmetry"], 0.0, delta=1.0e-6)

    self.assertEqual(str(feed_event.component_primary_name), "left_engine_fuel_feed")
    self.assertEqual(str(feed_event.component_primary_system), "fuel")
    self.assertGreater(feed_initial["fuel_leak"], 0.0)
    self.assertLess(feed_initial["propulsion"], wing_initial["propulsion"])
    self.assertAlmostEqual(feed_initial["fuel_imbalance"], 0.0, delta=1.0e-6)

  def test_phase3_fighter_component_geometry_covers_nose_avionics_and_engine_runtime_identity(
    self,
  ) -> None:
    cases = [
      ("F-16C_Block50", (6.6, 0.0, 0.0), "apg68_radar_array", "radar", "avionics"),
      ("F-16C_Block50", (1.5, 0.0, 0.25), "mission_computer", "avionics", "avionics"),
      ("F-16C_Block50", (-5.8, 0.0, 0.0), "engine_core", "engine", "propulsion"),
      ("Su-35S_Flanker-E", (9.2, 0.0, 0.0), "irbis_radar_array", "radar", "avionics"),
      ("Su-35S_Flanker-E", (1.8, 0.0, 0.25), "mission_computer", "avionics", "avionics"),
      ("Su-35S_Flanker-E", (-7.5, -1.4, -0.4), "left_engine_core", "engine_left", "propulsion"),
      ("Su-35S_Flanker-E", (-7.5, 1.4, -0.4), "right_engine_core", "engine_right", "propulsion"),
    ]

    for target_type, local, expected_component, expected_system, affected_overlay in cases:
      with self.subTest(target=target_type, component=expected_component):
        overlay, _, event = _profiled_local_hit_overlay_for_target(
          target_type,
          "blast_fragmentation",
          local,
          damage=90.0,
          radius=35.0,
        )

        self.assertTrue(bool(event.direct_hitbox_intersection))
        self.assertEqual(int(event.component_hit_count), 1)
        self.assertEqual(str(event.component_primary_name), expected_component)
        self.assertEqual(str(event.component_primary_system), expected_system)
        self.assertLess(float(event.component_primary_integrity), 1.0)
        self.assertGreater(float(event.component_threshold_scale), 1.0)
        self.assertLess(overlay[affected_overlay], 1.0)

  def test_phase3_representative_aircraft_database_components_cover_uav_helo_c2(self) -> None:
    cases = {
      "mq9_reaper.json": {
        "eo_ir_sensor_turret",
        "synthetic_aperture_radar",
        "satcom_antenna_array",
        "mission_payload_processor",
        "power_distribution_unit",
        "data_link_transceiver",
        "rear_engine_block",
        "engine_fuel_control_unit",
        "starter_generator",
        "pusher_propeller_hub",
        "left_wing_fuel_cell",
        "right_aileron_servo",
        "left_inboard_flap_servo",
        "right_outboard_wing_spar",
      },
      "mh60r_mvp.json": {
        "cockpit_crew_station",
        "surface_search_radar",
        "forward_flir_turret",
        "tactical_navigation_unit",
        "fuel_bladders",
        "dipping_sonar_processor",
        "esm_receiver_rack",
        "power_distribution_panel",
        "left_engine_module",
        "main_gearbox",
        "hydraulic_pump_module",
        "main_rotor_hub",
        "collective_servo",
        "tail_drive_shaft",
        "right_tail_rudder_servo",
      },
      "e3_sentry.json": {
        "flight_deck_crew_station",
        "iff_transponder_suite",
        "rotodome_radar_array",
        "mission_processing_racks",
        "radar_signal_processor",
        "mission_operator_consoles",
        "center_fuselage_fuel_cell",
        "navigation_reference_unit",
        "power_distribution_bus",
        "auxiliary_power_unit",
        "left_engine_pod",
        "right_engine_pod",
        "left_engine_fire_bottle",
        "right_engine_fire_bottle",
        "right_aileron_actuator",
        "right_spoiler_actuator",
      },
    }

    for filename, expected_names in cases.items():
      with self.subTest(filename=filename):
        with open(
          resolve_repo_path("examples", "config", "database", "aircraft", "units", filename),
          "r",
          encoding="utf-8",
        ) as handle:
          unit = json.load(handle)
        components = [
          component
          for hitbox in unit["damage_model"]["hitboxes"]
          for component in hitbox.get("components", [])
        ]
        component_names = {str(component.get("name", "")) for component in components}

        self.assertGreaterEqual(len(components), 20)
        self.assertTrue(expected_names.issubset(component_names))
        for component in components:
          self.assertTrue(str(component.get("name", "")))
          self.assertTrue(str(component.get("system", "")))
          self.assertTrue(str(component.get("redundancy_group_id", "")))
          self.assertGreater(float(component.get("threshold_scale", 0.0)), 0.0)

  def test_phase3_e3_fire_bottles_are_authored_as_suppression_components(self) -> None:
    with open(
      resolve_repo_path("examples", "config", "database", "aircraft", "units", "e3_sentry.json"),
      "r",
      encoding="utf-8",
    ) as handle:
      unit = json.load(handle)
    components = {
      str(component.get("name", "")): component
      for hitbox in unit["damage_model"]["hitboxes"]
      for component in hitbox.get("components", [])
    }
    for name in ("left_engine_fire_bottle", "right_engine_fire_bottle"):
      self.assertEqual(str(components[name].get("system", "")), "fire_suppression")
      self.assertEqual(
        str(components[name].get("redundancy_group_id", "")),
        "engine_fire_suppression",
      )

    sim = ef_py.SimulationKernel()
    sim.reset(20260529)
    self.assertTrue(sim.load_database(_DB_PATH))
    attacker_id, target_id = _spawn_attacker_and_named_target(sim, "E-3_Sentry_AWACS")
    ok = sim.debug_apply_profiled_local_proximity_hit(
      attacker_id,
      target_id,
      -7.0,
      -10.2,
      -0.2,
      _make_warhead_profile("blast_fragmentation", damage=180.0, radius=35.0),
    )
    self.assertTrue(bool(ok))
    event = sim.export_recent_engagement_events().effects_events[-1]
    overlay = _aircraft_damage_overlay(sim, target_id)
    self.assertEqual(str(event.component_primary_name), "left_engine_fire_bottle")
    self.assertEqual(str(event.component_primary_system), "fire_suppression")
    self.assertEqual(int(event.component_redundancy_group_member_count), 2)
    self.assertLess(float(event.component_redundancy_group_availability), 1.0)
    self.assertLess(
      float(event.component_primary_integrity),
      float(event.component_redundancy_group_availability),
    )
    self.assertAlmostEqual(
      overlay["fire_suppression"],
      float(event.component_redundancy_group_availability),
      delta=1.0e-6,
    )
    self.assertAlmostEqual(overlay["fuel"], 1.0, delta=1.0e-6)
    self.assertAlmostEqual(overlay["fuel_leak"], 0.0, delta=1.0e-6)

  def test_phase3_fighter_components_author_mechanism_specific_thresholds(self) -> None:
    cases = [
      (
        "f16c_block50.json",
        {
          "apg68_radar_array",
          "cockpit_crew_station",
          "nose_avionics_bay",
          "iff_interrogator",
          "center_fuselage_fuel_cell",
          "mission_computer",
          "data_link_terminal",
          "flight_control_computer",
          "inertial_navigation_unit",
          "electrical_power_bus",
          "engine_core",
          "afterburner_nozzle",
          "tail_hydraulic_pump",
          "engine_fuel_control_unit",
          "rudder_actuator",
          "left_wing_fuel_cell",
          "right_wing_fuel_cell",
          "left_aileron_actuator",
          "right_aileron_actuator",
          "wing_spar_center",
          "left_leading_edge_flap_actuator",
          "right_leading_edge_flap_actuator",
        },
        {
          "radar",
          "cockpit",
          "avionics",
          "navigation",
          "data_link",
          "engine",
          "hydraulic",
          "flight_control",
          "fuel",
          "wings",
        },
      ),
      (
        "su35s_flanker_e.json",
        {
          "irbis_radar_array",
          "cockpit_crew_station",
          "nose_avionics_bay",
          "irst_sensor",
          "center_fuselage_fuel_cell",
          "mission_computer",
          "data_link_terminal",
          "flight_control_computer",
          "inertial_navigation_unit",
          "electrical_power_bus",
          "left_engine_core",
          "left_engine_fuel_feed",
          "left_thrust_vector_actuator",
          "right_engine_core",
          "right_engine_fuel_feed",
          "right_thrust_vector_actuator",
          "left_wing_fuel_cell",
          "right_wing_fuel_cell",
          "left_elevon_actuator",
          "right_elevon_actuator",
          "wing_spar_center",
          "left_leading_edge_flap_actuator",
          "right_leading_edge_flap_actuator",
        },
        {
          "radar",
          "cockpit",
          "avionics",
          "sensor_payload",
          "navigation",
          "data_link",
          "engine_left",
          "engine_right",
          "flight_control",
          "fuel",
          "wings",
        },
      ),
    ]
    required_families = {"blast", "fragmentation", "blast_fragmentation", "continuous_rod", "hit_to_kill"}

    for filename, expected_components, expected_systems in cases:
      with self.subTest(filename=filename):
        with open(
          resolve_repo_path("examples", "config", "database", "aircraft", "units", filename),
          "r",
          encoding="utf-8",
        ) as handle:
          unit = json.load(handle)
        components = {
          str(component.get("name", "")): component
          for hitbox in unit["damage_model"]["hitboxes"]
          for component in hitbox.get("components", [])
        }
        self.assertGreaterEqual(len(components), 20)
        self.assertTrue(expected_components.issubset(set(components)))
        self.assertTrue(expected_systems.issubset({str(c.get("system", "")) for c in components.values()}))
        for component_name in expected_components:
          thresholds = components[component_name].get("mechanism_thresholds", {})
          self.assertTrue(required_families.issubset(set(thresholds)))
          self.assertGreater(len({float(value) for value in thresholds.values()}), 1)

  def test_phase3_component_mechanism_thresholds_drive_failure_probability(self) -> None:
    low_target = "F-16C_A2_LowRodThreshold_Test"
    high_target = "F-16C_A2_HighRodThreshold_Test"
    low_override = _make_f16_component_mechanism_threshold_override(
      low_target,
      continuous_rod_scale=0.60,
    )
    high_override = _make_f16_component_mechanism_threshold_override(
      high_target,
      continuous_rod_scale=1.00,
    )

    _low_overlay, _, low_event = _profiled_local_hit_overlay_for_target(
      low_target,
      "continuous_rod",
      (-0.8, 4.1, 0.0),
      damage=90.0,
      radius=35.0,
      overrides=[low_override],
    )
    _high_overlay, _, high_event = _profiled_local_hit_overlay_for_target(
      high_target,
      "continuous_rod",
      (-0.8, 4.1, 0.0),
      damage=90.0,
      radius=35.0,
      overrides=[high_override],
    )

    self.assertEqual(str(low_event.component_primary_name), "right_aileron_actuator")
    self.assertEqual(str(high_event.component_primary_name), "right_aileron_actuator")
    self.assertAlmostEqual(
      float(low_event.component_failure_sample),
      float(high_event.component_failure_sample),
      delta=1.0e-9,
    )
    self.assertLess(
      float(low_event.component_threshold_scale),
      float(high_event.component_threshold_scale),
    )
    self.assertLess(
      float(low_event.component_failure_probability),
      float(high_event.component_failure_probability),
    )

  def test_phase3_representative_aircraft_components_author_mechanism_thresholds(
    self,
  ) -> None:
    filenames = [
      "f16c_block50.json",
      "su35s_flanker_e.json",
      "mq9_reaper.json",
      "mh60r_mvp.json",
      "e3_sentry.json",
    ]
    required_families = {"blast", "fragmentation", "blast_fragmentation", "continuous_rod", "hit_to_kill"}

    for filename in filenames:
      with self.subTest(filename=filename):
        with open(
          resolve_repo_path("examples", "config", "database", "aircraft", "units", filename),
          "r",
          encoding="utf-8",
        ) as handle:
          unit = json.load(handle)
        components = [
          component
          for hitbox in unit["damage_model"]["hitboxes"]
          for component in hitbox.get("components", [])
        ]
        self.assertGreaterEqual(len(components), 20)
        for component in components:
          thresholds = component.get("mechanism_thresholds", {})
          self.assertTrue(required_families.issubset(set(thresholds)))
          for family in required_families:
            self.assertGreater(float(thresholds[family]), 0.0)
          self.assertGreater(len({float(value) for value in thresholds.values()}), 1)

  def test_phase3_current_aircraft_unit_database_has_20_plus_component_models(
    self,
  ) -> None:
    units_dir = resolve_repo_path("examples", "config", "database", "aircraft", "units")
    required_families = {"blast", "fragmentation", "blast_fragmentation", "continuous_rod", "hit_to_kill"}
    filenames = sorted(
      filename
      for filename in os.listdir(units_dir)
      if filename.endswith(".json")
    )

    self.assertGreater(len(filenames), 0)
    for filename in filenames:
      with self.subTest(filename=filename):
        with open(os.path.join(units_dir, filename), "r", encoding="utf-8") as handle:
          unit = json.load(handle)
        hitboxes = unit.get("damage_model", {}).get("hitboxes", [])
        components = [
          component
          for hitbox in hitboxes
          for component in hitbox.get("components", [])
        ]
        self.assertGreater(len(hitboxes), 0)
        self.assertGreaterEqual(len(components), 20)
        self.assertEqual(
          len({str(component.get("name", "")) for component in components}),
          len(components),
        )
        for component in components:
          self.assertTrue(str(component.get("name", "")))
          self.assertTrue(str(component.get("system", "")))
          self.assertTrue(str(component.get("redundancy_group_id", "")))
          self.assertGreater(float(component.get("threshold_scale", 0.0)), 0.0)
          thresholds = component.get("mechanism_thresholds", {})
          self.assertTrue(required_families.issubset(set(thresholds)))
          for family in required_families:
            self.assertGreater(float(thresholds[family]), 0.0)
          self.assertGreater(len({float(value) for value in thresholds.values()}), 1)

  def test_phase3_current_aircraft_unit_component_centers_stay_inside_parent_hitboxes(
    self,
  ) -> None:
    units_dir = resolve_repo_path("examples", "config", "database", "aircraft", "units")
    filenames = sorted(
      filename
      for filename in os.listdir(units_dir)
      if filename.endswith(".json")
    )

    for filename in filenames:
      with self.subTest(filename=filename):
        with open(os.path.join(units_dir, filename), "r", encoding="utf-8") as handle:
          unit = json.load(handle)
        for hitbox in unit.get("damage_model", {}).get("hitboxes", []):
          hitbox_offset = [float(value) for value in hitbox["offset"]]
          hitbox_size = [float(value) for value in hitbox["size"]]
          hitbox_min = [
            hitbox_offset[index] - 0.5 * hitbox_size[index]
            for index in range(3)
          ]
          hitbox_max = [
            hitbox_offset[index] + 0.5 * hitbox_size[index]
            for index in range(3)
          ]
          for component in hitbox.get("components", []):
            component_offset = [float(value) for value in component["offset"]]
            for axis in range(3):
              self.assertGreaterEqual(
                component_offset[axis],
                hitbox_min[axis] - 1.0e-9,
                str(component.get("name", "")),
              )
              self.assertLessEqual(
                component_offset[axis],
                hitbox_max[axis] + 1.0e-9,
                str(component.get("name", "")),
              )

  def test_phase3_component_dependencies_are_authored_for_representative_control_and_mission_components(
    self,
  ) -> None:
    cases = [
      ("f16c_block50.json", "right_aileron_actuator", {"hydraulic", "flight_control"}),
      ("su35s_flanker_e.json", "right_elevon_actuator", {"hydraulic", "flight_control"}),
      ("mq9_reaper.json", "right_aileron_servo", {"hydraulic", "flight_control"}),
      ("mh60r_mvp.json", "right_tail_rudder_servo", {"hydraulic", "flight_control"}),
      ("e3_sentry.json", "rotodome_radar_array", {"avionics", "mission_systems"}),
    ]

    for filename, component_name, expected_dependencies in cases:
      with self.subTest(filename=filename, component=component_name):
        with open(
          resolve_repo_path("examples", "config", "database", "aircraft", "units", filename),
          "r",
          encoding="utf-8",
        ) as handle:
          unit = json.load(handle)
        components = [
          component
          for hitbox in unit["damage_model"]["hitboxes"]
          for component in hitbox.get("components", [])
          if str(component.get("name", "")) == component_name
        ]
        self.assertEqual(len(components), 1)
        dependency_systems = {
          str(dependency.get("system", ""))
          for dependency in components[0].get("dependencies", [])
        }
        self.assertTrue(expected_dependencies.issubset(dependency_systems))

  def test_phase3_current_aircraft_units_author_mission_power_and_link_dependencies(
    self,
  ) -> None:
    units_dir = resolve_repo_path("examples", "config", "database", "aircraft", "units")
    cases = [
      ("f16c_block50.json", "electrical_power_bus", {"flight_control", "data_link", "mission_systems"}),
      ("f16c_block50.json", "data_link_terminal", {"avionics", "mission_systems"}),
      ("su35s_flanker_e.json", "electrical_power_bus", {"flight_control", "data_link", "mission_systems"}),
      ("su35s_flanker_e.json", "data_link_terminal", {"avionics", "mission_systems"}),
      ("mq9_reaper.json", "power_distribution_unit", {"flight_control", "data_link", "mission_systems"}),
      ("mq9_reaper.json", "data_link_transceiver", {"avionics", "mission_systems"}),
      ("mh60r_mvp.json", "power_distribution_panel", {"flight_control", "data_link", "mission_systems"}),
      ("mh60r_mvp.json", "data_link_terminal", {"avionics", "mission_systems"}),
      ("e3_sentry.json", "power_distribution_bus", {"flight_control", "data_link", "mission_systems"}),
      ("e3_sentry.json", "wideband_data_link_array", {"avionics", "mission_systems"}),
    ]

    for filename, component_name, expected_dependencies in cases:
      with self.subTest(filename=filename, component=component_name):
        with open(os.path.join(units_dir, filename), "r", encoding="utf-8") as handle:
          unit = json.load(handle)
        matches = [
          component
          for hitbox in unit["damage_model"]["hitboxes"]
          for component in hitbox.get("components", [])
          if str(component.get("name", "")) == component_name
        ]
        self.assertEqual(len(matches), 1)
        dependency_systems = {
          str(dependency.get("system", ""))
          for dependency in matches[0].get("dependencies", [])
        }
        self.assertTrue(expected_dependencies.issubset(dependency_systems))

  def test_phase3_current_aircraft_dependencies_carry_typed_edge_metadata(self) -> None:
    units_dir = resolve_repo_path("examples", "config", "database", "aircraft", "units")
    filenames = (
      "f16c_block50.json",
      "su35s_flanker_e.json",
      "mq9_reaper.json",
      "mh60r_mvp.json",
      "e3_sentry.json",
    )
    allowed_edge_types = {
      "generic",
      "hydraulic_power",
      "electrical_power",
      "control_signal",
      "data_path",
      "airflow_path",
      "exposure_path",
      "fuel_feed",
      "structural_support",
      "crew_operated",
    }
    dependency_count = 0
    observed_edges: dict[tuple[str, str, str], str] = {}

    for filename in filenames:
      with self.subTest(filename=filename):
        with open(os.path.join(units_dir, filename), "r", encoding="utf-8") as handle:
          unit = json.load(handle)
        for hitbox in unit["damage_model"]["hitboxes"]:
          for component in hitbox.get("components", []):
            component_name = str(component.get("name", ""))
            for dependency in component.get("dependencies", []):
              dependency_count += 1
              target_system = str(dependency.get("target_system", ""))
              self.assertTrue(target_system, component_name)
              self.assertEqual(str(dependency.get("system", "")), target_system)
              self.assertIn(str(dependency.get("edge_type", "")), allowed_edge_types)
              self.assertIn(
                "non-authoritative",
                str(dependency.get("provenance", "")),
              )
              observed_edges[(filename, component_name, target_system)] = str(
                dependency.get("edge_type", "")
              )

    self.assertGreaterEqual(dependency_count, 100)
    self.assertEqual(
      observed_edges[("f16c_block50.json", "electrical_power_bus", "flight_control")],
      "electrical_power",
    )
    self.assertEqual(
      observed_edges[("f16c_block50.json", "data_link_terminal", "avionics")],
      "data_path",
    )
    self.assertEqual(
      observed_edges[("f16c_block50.json", "tail_hydraulic_pump", "flight_control")],
      "hydraulic_power",
    )
    self.assertEqual(
      observed_edges[("mq9_reaper.json", "engine_fuel_control_unit", "fuel")],
      "fuel_feed",
    )
    self.assertEqual(
      observed_edges[("e3_sentry.json", "rotodome_radar_array", "avionics")],
      "generic",
    )

  def test_phase3_representative_aircraft_components_report_runtime_identity(self) -> None:
    cases = [
      (
        "MQ-9_Reaper",
        (4.8, 0.0, -0.25),
        "eo_ir_sensor_turret",
        "sensor_payload",
        "mission_sensor_payload",
        1,
        "avionics",
        None,
      ),
      (
        "MQ-9_Reaper",
        (-0.4, 8.0, 0.0),
        "right_aileron_servo",
        "flight_control",
        "lateral_flight_control_actuators",
        2,
        "flight_control",
        "roll_control",
      ),
      (
        "MH-60R_MVP",
        (4.6, 0.0, -0.5),
        "surface_search_radar",
        "sensor_payload",
        "helo_sensor_payload",
        1,
        "avionics",
        None,
      ),
      (
        "MH-60R_MVP",
        (-8.5, 0.35, 0.2),
        "right_tail_rudder_servo",
        "flight_control",
        "yaw_control_servos",
        2,
        "flight_control",
        "yaw_control",
      ),
      (
        "E-3_Sentry_AWACS",
        (5.0, 0.0, 4.4),
        "rotodome_radar_array",
        "radar",
        "awacs_primary_radar",
        1,
        "avionics",
        None,
      ),
      (
        "E-3_Sentry_AWACS",
        (-2.0, 19.0, 0.0),
        "right_aileron_actuator",
        "flight_control",
        "lateral_flight_control_actuators",
        2,
        "flight_control",
        "roll_control",
      ),
    ]

    for (
      target_type,
      local_impact,
      expected_component,
      expected_system,
      expected_group,
      expected_group_members,
      expected_overlay_drop,
      expected_axis_drop,
    ) in cases:
      with self.subTest(target_type=target_type, component=expected_component):
        overlay, _, event = _profiled_local_hit_overlay_for_target(
          target_type,
          "blast_fragmentation",
          local_impact,
          damage=90.0,
          radius=35.0,
        )

        self.assertTrue(bool(event.direct_hitbox_intersection))
        self.assertGreaterEqual(int(event.component_hit_count), 1)
        self.assertEqual(str(event.component_primary_name), expected_component)
        self.assertEqual(str(event.component_primary_system), expected_system)
        self.assertEqual(str(event.component_primary_redundancy_group_id), expected_group)
        self.assertEqual(
          int(event.component_redundancy_group_member_count),
          expected_group_members,
        )
        self.assertLess(float(event.component_primary_integrity), 1.0)
        self.assertGreater(float(event.component_redundancy_group_availability), 0.0)
        self.assertLess(overlay[expected_overlay_drop], 1.0)
        if expected_axis_drop is not None:
          self.assertLess(overlay[expected_axis_drop], 1.0)

  def test_phase3_component_dependency_damage_propagates_to_related_aircraft_systems(self) -> None:
    sim = ef_py.SimulationKernel()
    sim.reset(20260526)
    self.assertTrue(sim.load_database(_DB_PATH))
    attacker_id, target_id = _spawn_attacker_and_named_target(sim, "F-16C_Block50")
    profile = _make_warhead_profile("continuous_rod", damage=160.0, radius=35.0)

    before = _aircraft_damage_overlay(sim, target_id)
    self.assertAlmostEqual(before["hydraulic"], 1.0, delta=1.0e-6)
    self.assertAlmostEqual(before["flight_control"], 1.0, delta=1.0e-6)

    self.assertTrue(
      bool(
        sim.debug_apply_profiled_local_proximity_hit(
          attacker_id,
          target_id,
          -0.8,
          4.1,
          0.0,
          profile,
        )
      )
    )

    event = sim.export_recent_engagement_events().effects_events[-1]
    after = _aircraft_damage_overlay(sim, target_id)

    self.assertEqual(str(event.component_primary_name), "right_aileron_actuator")
    self.assertEqual(
      str(event.component_primary_redundancy_group_id),
      "lateral_flight_control_actuators",
    )
    component_rows = list(event.component_mechanism_load_rows)
    self.assertTrue(component_rows)
    self.assertEqual(int(component_rows[0].component_dependency_propagation_count), 2)
    self.assertIn(
      str(component_rows[0].component_dependency_edge_type),
      {"generic", "hydraulic_power"},
    )
    self.assertIn(
      "non-authoritative",
      str(component_rows[0].component_dependency_provenance),
    )
    self.assertTrue(bool(component_rows[0].component_dependency_propagated))
    self.assertLess(float(event.component_redundancy_group_availability), 1.0)
    self.assertLess(after["hydraulic"], before["hydraulic"])
    self.assertLess(after["flight_control"], before["flight_control"])
    self.assertLess(after["roll_control"], before["roll_control"])

  def test_phase3_mission_component_dependency_damage_propagates_to_avionics_overlay(self) -> None:
    overlay, _, event = _profiled_local_hit_overlay_for_target(
      "E-3_Sentry_AWACS",
      "blast_fragmentation",
      (5.0, 0.0, 4.4),
      damage=90.0,
      radius=35.0,
    )

    self.assertEqual(str(event.component_primary_name), "rotodome_radar_array")
    self.assertEqual(str(event.component_primary_system), "radar")
    self.assertEqual(str(event.component_primary_redundancy_group_id), "awacs_primary_radar")
    self.assertLess(float(event.component_primary_integrity), 1.0)
    self.assertLess(overlay["avionics"], 1.0)

  def test_phase3_power_and_data_link_dependencies_propagate_to_aircraft_overlay(self) -> None:
    cases = [
      (
        "F-16C_Block50",
        (-2.8, 0.45, 0.05),
        "electrical_power_bus",
        {"avionics": 1.0, "flight_control": 1.0},
      ),
      (
        "MQ-9_Reaper",
        (-1.8, 0.0, 0.2),
        "power_distribution_unit",
        {"avionics": 1.0, "flight_control": 1.0},
      ),
      (
        "MH-60R_MVP",
        (-2.0, 0.0, 0.35),
        "power_distribution_panel",
        {"avionics": 1.0, "flight_control": 1.0},
      ),
      (
        "E-3_Sentry_AWACS",
        (-8.0, 0.0, 0.0),
        "power_distribution_bus",
        {"avionics": 1.0, "flight_control": 1.0},
      ),
      (
        "MQ-9_Reaper",
        (1.0, 0.0, 0.2),
        "data_link_transceiver",
        {"avionics": 1.0},
      ),
      (
        "E-3_Sentry_AWACS",
        (7.0, 0.0, 3.2),
        "wideband_data_link_array",
        {"avionics": 1.0},
      ),
    ]

    for target_type, local_impact, expected_component, expected_drops in cases:
      with self.subTest(target_type=target_type, component=expected_component):
        overlay, _, event = _profiled_local_hit_overlay_for_target(
          target_type,
          "blast_fragmentation",
          local_impact,
          damage=120.0,
          radius=35.0,
        )

        self.assertEqual(str(event.component_primary_name), expected_component)
        self.assertLess(float(event.component_primary_integrity), 1.0)
        for overlay_name, baseline in expected_drops.items():
          self.assertLess(overlay[overlay_name], baseline)

  def test_phase3_typed_dependency_target_system_alias_propagates(self) -> None:
    target_name = "F-16C_A2_TypedDependencyAlias_Test"
    overrides = [
      _make_f16_typed_dependency_override(
        target_name,
        [
          {
            "target_system": "hydraulic",
            "edge_type": "hydraulic_power",
            "scale": 1.0,
            "provenance": "unit-test typed dependency",
          }
        ],
      )
    ]

    overlay, _, event = _profiled_local_hit_overlay_for_target(
      target_name,
      "continuous_rod",
      (-0.8, 2.8, 0.0),
      damage=160.0,
      radius=35.0,
      overrides=overrides,
    )

    self.assertEqual(str(event.component_primary_name), "typed_dependency_source")
    component_rows = list(event.component_mechanism_load_rows)
    self.assertEqual(len(component_rows), 1)
    self.assertEqual(int(component_rows[0].component_dependency_propagation_count), 1)
    self.assertEqual(str(component_rows[0].component_dependency_target_system), "hydraulic")
    self.assertEqual(str(component_rows[0].component_dependency_edge_type), "hydraulic_power")
    self.assertEqual(
      str(component_rows[0].component_dependency_provenance),
      "unit-test typed dependency",
    )
    self.assertLess(float(component_rows[0].component_dependency_source_availability), 1.0)
    self.assertGreater(float(component_rows[0].component_dependency_effective_scale), 0.0)
    self.assertTrue(bool(component_rows[0].component_dependency_propagated))
    self.assertLess(overlay["hydraulic"], 1.0)
    self.assertLess(overlay["flight_control"], 1.0)
    self.assertAlmostEqual(overlay["fuel"], 1.0, delta=1.0e-6)

  def test_phase3_typed_dependency_edges_remain_backward_compatible(self) -> None:
    target_name = "F-16C_A2_MixedDependencySchema_Test"
    overrides = [
      _make_f16_typed_dependency_override(
        target_name,
        [
          {
            "system": "fuel",
            "edge_type": "fuel_feed",
            "scale": 0.80,
          },
          {
            "target_system": "hydraulic",
            "edge_type": "hydraulic_power",
            "scale": 0.80,
            "threshold": 1.0,
            "provenance": "unit-test typed dependency",
          },
        ],
      )
    ]

    overlay, _, event = _profiled_local_hit_overlay_for_target(
      target_name,
      "continuous_rod",
      (-0.8, 2.8, 0.0),
      damage=160.0,
      radius=35.0,
      overrides=overrides,
    )

    self.assertEqual(str(event.component_primary_name), "typed_dependency_source")
    component_rows = list(event.component_mechanism_load_rows)
    self.assertEqual(len(component_rows), 1)
    self.assertEqual(int(component_rows[0].component_dependency_propagation_count), 2)
    self.assertTrue(bool(component_rows[0].component_dependency_propagated))
    self.assertLess(overlay["fuel"], 1.0)
    self.assertLess(overlay["propulsion"], 1.0)
    self.assertLess(overlay["hydraulic"], 1.0)
    self.assertGreater(overlay["fuel_leak"], 0.0)
    self.assertAlmostEqual(overlay["fuel_imbalance"], 0.0, delta=1.0e-6)

  def test_phase3_typed_dependency_edge_types_route_to_distinct_aircraft_overlays(self) -> None:
    def run_case(
      suffix: str,
      dependencies: list[dict],
    ) -> tuple[dict[str, float], object]:
      target_name = f"F-16C_A2_TypedDependencyRoute_{suffix}_Test"
      overrides = [_make_f16_typed_dependency_override(target_name, dependencies)]
      return _profiled_local_hit_overlay_for_target(
        target_name,
        "continuous_rod",
        (-0.8, 2.8, 0.0),
        damage=160.0,
        radius=35.0,
        overrides=overrides,
      )[0::2]

    baseline, _ = run_case("Baseline", [])
    data_path, data_event = run_case(
      "DataPath",
      [
        {
          "target_system": "data_link",
          "edge_type": "data_path",
          "scale": 1.0,
          "threshold": 1.0,
        }
      ],
    )
    electrical, electrical_event = run_case(
      "Electrical",
      [
        {
          "target_system": "flight_control",
          "edge_type": "electrical_power",
          "scale": 1.0,
          "threshold": 1.0,
        }
      ],
    )
    crew_operated, crew_event = run_case(
      "CrewOperated",
      [
        {
          "target_system": "mission_systems",
          "edge_type": "crew_operated",
          "scale": 1.0,
          "threshold": 1.0,
        }
      ],
    )
    cooling, cooling_event = run_case(
      "Cooling",
      [
        {
          "target_system": "avionics",
          "edge_type": "cooling",
          "scale": 1.0,
          "threshold": 1.0,
        }
      ],
    )

    self.assertEqual(
      str(list(data_event.component_mechanism_load_rows)[0].component_dependency_edge_type),
      "data_path",
    )
    self.assertLess(data_path["avionics"], baseline["avionics"])
    self.assertLess(data_path["command_navigation"], baseline["command_navigation"])
    self.assertLess(data_path["mission_crew"], baseline["mission_crew"])
    self.assertAlmostEqual(data_path["hydraulic"], baseline["hydraulic"], delta=1.0e-6)
    self.assertAlmostEqual(data_path["fuel"], baseline["fuel"], delta=1.0e-6)
    self.assertAlmostEqual(data_path["propulsion"], baseline["propulsion"], delta=1.0e-6)
    self.assertAlmostEqual(
      data_path["ignition_source"],
      baseline["ignition_source"],
      delta=1.0e-6,
    )

    self.assertEqual(
      str(list(electrical_event.component_mechanism_load_rows)[0].component_dependency_edge_type),
      "electrical_power",
    )
    self.assertLess(electrical["flight_control"], baseline["flight_control"])
    self.assertLess(electrical["avionics"], baseline["avionics"])
    self.assertLess(electrical["command_navigation"], baseline["command_navigation"])
    self.assertGreater(electrical["ignition_source"], baseline["ignition_source"])

    self.assertEqual(
      str(list(crew_event.component_mechanism_load_rows)[0].component_dependency_edge_type),
      "crew_operated",
    )
    self.assertLess(crew_operated["crew"], baseline["crew"])
    self.assertLess(crew_operated["mission_crew"], baseline["mission_crew"])
    self.assertLess(crew_operated["command_navigation"], baseline["command_navigation"])
    self.assertAlmostEqual(crew_operated["hydraulic"], baseline["hydraulic"], delta=1.0e-6)
    self.assertAlmostEqual(crew_operated["fuel"], baseline["fuel"], delta=1.0e-6)

    self.assertEqual(
      str(list(cooling_event.component_mechanism_load_rows)[0].component_dependency_edge_type),
      "cooling",
    )
    self.assertLess(cooling["avionics"], baseline["avionics"])
    self.assertGreater(cooling["ignition_source"], baseline["ignition_source"])
    self.assertGreater(cooling["fire"], baseline["fire"])

  def test_explicit_part_failure_modes_route_to_existing_aircraft_entries(self) -> None:
    target_name = "F-16C_ExplicitPartFailureModes_Test"
    with open(
      resolve_repo_path("examples", "config", "database", "aircraft", "units", "f16c_block50.json"),
      "r",
      encoding="utf-8",
    ) as handle:
      unit = json.load(handle)
    unit["name"] = target_name
    damage_model = unit["damage_model"]
    damage_model.pop("vulnerability", None)
    for hitbox in damage_model["hitboxes"]:
      systems = set(str(system) for system in hitbox.get("systems", []))
      if "wings" in systems and "flight_control" in systems:
        hitbox["components"] = [
          {
            "name": "explicit_failure_payload",
            "system": "auxiliary_payload",
            "offset": [-0.8, 2.8, 0.0],
            "size": [1.2, 1.0, 0.25],
            "armor": 0.2,
            "threshold_scale": 1.0,
            "mechanism_thresholds": {
              "blast": 1.0,
              "fragmentation": 1.0,
              "blast_fragmentation": 1.0,
              "continuous_rod": 1.0,
              "hit_to_kill": 1.0,
            },
            "redundancy_group_id": "explicit_failure_payload",
            "redundancy_group": 0.0,
            "redundancy_weight": 1.0,
            "failure_mode_weights": {
              "fuel_leak": 1.0,
              "hydraulic_pressure_loss": 1.0,
              "electrical_loss": 1.0,
              "data_loss": 1.0,
              "fire_source": 1.0,
            },
            "critical": True,
          }
        ]

    overlay, _, event = _profiled_local_hit_overlay_for_target(
      target_name,
      "continuous_rod",
      (-0.8, 2.8, 0.0),
      damage=220.0,
      radius=35.0,
      overrides=[unit],
    )

    self.assertEqual(str(event.component_primary_name), "explicit_failure_payload")
    self.assertEqual(str(event.component_primary_system), "auxiliary_payload")
    self.assertGreater(int(event.component_failure_count), 0)
    component_rows = list(event.component_mechanism_load_rows)
    self.assertEqual(len(component_rows), 1)
    row = component_rows[0]
    self.assertGreater(float(row.mechanism_rod_cut_margin), 0.0)
    self.assertGreater(float(row.mechanism_penetration_margin), 0.0)
    response = _component_response_for_load_row(event, row)
    self.assertEqual(str(response.failure_mode_source), "component_failure_mode_weights")
    self.assertFalse(bool(response.failure_mode_authority))
    modes = {
      str(name): float(severity)
      for name, severity in zip(
        response.failure_mode_names,
        response.failure_mode_severities,
      )
    }
    self.assertEqual(
      set(modes),
      {
        "fuel_leak",
        "hydraulic_pressure_loss",
        "electrical_loss",
        "data_loss",
        "fire_source",
      },
    )
    self.assertIn(str(response.failure_mode), modes)
    self.assertAlmostEqual(
      float(response.failure_severity),
      modes[str(response.failure_mode)],
      delta=1.0e-12,
    )
    for mode, severity in modes.items():
      self.assertGreater(severity, 0.0, mode)
      self.assertLessEqual(severity, 1.0, mode)
    self.assertGreater(overlay["fuel_leak"], 0.0)
    self.assertLess(overlay["hydraulic_pressure"], 1.0)
    self.assertLess(overlay["avionics"], 1.0)
    self.assertLess(overlay["command_navigation"], 1.0)
    self.assertGreater(overlay["ignition_source"], 0.0)
    self.assertGreater(overlay["fire"], 0.0)

  def test_phase3_typed_dependency_threshold_can_gate_propagation(self) -> None:
    permissive_name = "F-16C_A2_TypedDependencyThresholdPermissive_Test"
    gated_name = "F-16C_A2_TypedDependencyThresholdGated_Test"
    permissive_overrides = [
      _make_f16_typed_dependency_override(
        permissive_name,
        [
          {
            "target_system": "hydraulic",
            "edge_type": "hydraulic_power",
            "scale": 1.0,
            "threshold": 1.0,
          }
        ],
      )
    ]
    gated_overrides = [
      _make_f16_typed_dependency_override(
        gated_name,
        [
          {
            "target_system": "hydraulic",
            "edge_type": "hydraulic_power",
            "scale": 1.0,
            "threshold": 0.0,
          }
        ],
      )
    ]

    permissive_overlay, _, permissive_event = _profiled_local_hit_overlay_for_target(
      permissive_name,
      "continuous_rod",
      (-0.8, 2.8, 0.0),
      damage=160.0,
      radius=35.0,
      overrides=permissive_overrides,
    )
    gated_overlay, _, gated_event = _profiled_local_hit_overlay_for_target(
      gated_name,
      "continuous_rod",
      (-0.8, 2.8, 0.0),
      damage=160.0,
      radius=35.0,
      overrides=gated_overrides,
    )

    self.assertEqual(str(permissive_event.component_primary_name), "typed_dependency_source")
    self.assertEqual(str(gated_event.component_primary_name), "typed_dependency_source")
    permissive_rows = list(permissive_event.component_mechanism_load_rows)
    gated_rows = list(gated_event.component_mechanism_load_rows)
    self.assertEqual(int(permissive_rows[0].component_dependency_propagation_count), 1)
    self.assertEqual(int(gated_rows[0].component_dependency_propagation_count), 0)
    self.assertFalse(bool(gated_rows[0].component_dependency_propagated))
    self.assertLess(permissive_overlay["hydraulic"], gated_overlay["hydraulic"])
    self.assertAlmostEqual(gated_overlay["hydraulic"], 1.0, delta=1.0e-6)

  def test_phase3_typed_dependency_delay_queues_then_applies_cascade(self) -> None:
    target_name = "F-16C_A2_TypedDependencyDelay_Test"
    delay_s = 0.20
    overrides = [
      _make_f16_typed_dependency_override(
        target_name,
        [
          {
            "target_system": "hydraulic",
            "edge_type": "hydraulic_power",
            "scale": 1.0,
            "threshold": 1.0,
            "delay_s": delay_s,
            "provenance": "unit-test delayed typed dependency",
          }
        ],
      )
    ]
    sim = _kernel_with_unit_overrides(overrides)
    sim.set_time_step(0.05)
    attacker_id, target_id = _spawn_attacker_and_named_target(sim, target_name)
    overlay_before = _aircraft_damage_overlay(sim, target_id)
    platform_before = [float(value) for value in sim.get_unit_damage_state(target_id)]

    ok = sim.debug_apply_profiled_local_proximity_hit(
      attacker_id,
      target_id,
      -0.8,
      2.8,
      0.0,
      _make_warhead_profile("continuous_rod", damage=160.0, radius=35.0),
    )
    self.assertTrue(bool(ok))
    event = sim.export_recent_engagement_events().effects_events[-1]
    rows = list(event.component_mechanism_load_rows)
    self.assertEqual(str(event.component_primary_name), "typed_dependency_source")
    self.assertEqual(len(rows), 1)
    self.assertEqual(int(rows[0].component_dependency_propagation_count), 1)
    self.assertTrue(bool(rows[0].component_dependency_propagated))
    self.assertAlmostEqual(float(rows[0].component_dependency_delay_s), delay_s, delta=1.0e-9)

    overlay_after_hit = _aircraft_damage_overlay(sim, target_id)
    self.assertAlmostEqual(
      overlay_after_hit["hydraulic"],
      overlay_before["hydraulic"],
      delta=1.0e-6,
    )

    for _ in range(3):
      sim.step()
    overlay_before_due = _aircraft_damage_overlay(sim, target_id)
    platform_before_due = [float(value) for value in sim.get_unit_damage_state(target_id)]
    self.assertAlmostEqual(
      overlay_before_due["hydraulic"],
      overlay_before["hydraulic"],
      delta=1.0e-6,
    )

    for _ in range(2):
      sim.step()
    overlay_after_due = _aircraft_damage_overlay(sim, target_id)
    platform_after_due = [float(value) for value in sim.get_unit_damage_state(target_id)]
    self.assertLess(overlay_after_due["hydraulic"], overlay_before_due["hydraulic"])
    self.assertLess(overlay_after_due["flight_control"], overlay_before_due["flight_control"])
    self.assertLess(platform_after_due[1], platform_before_due[1])
    self.assertAlmostEqual(overlay_after_due["fuel"], overlay_before["fuel"], delta=1.0e-6)
    self.assertAlmostEqual(overlay_after_due["avionics"], overlay_before["avionics"], delta=1.0e-6)
    self.assertTrue(
      all(0.0 <= value <= 1.0 for value in overlay_after_due.values()),
      overlay_after_due,
    )
    self.assertLess(min(platform_after_due), min(platform_before))

  def test_phase3_component_redundancy_reduces_failure_probability(self) -> None:
    single_name = "F-16C_A2_SingleCriticalActuator_Test"
    redundant_name = "F-16C_A2_RedundantActuator_Test"
    overrides = [
      _make_f16_component_redundancy_override(
        single_name,
        redundancy_group=0.0,
        critical=True,
      ),
      _make_f16_component_redundancy_override(
        redundant_name,
        redundancy_group=2.0,
        critical=False,
      ),
    ]

    _, _, single_event = _profiled_local_hit_overlay_for_target(
      single_name,
      "continuous_rod",
      (-0.8, 4.1, 0.0),
      damage=140.0,
      radius=35.0,
      overrides=overrides,
    )
    _, _, redundant_event = _profiled_local_hit_overlay_for_target(
      redundant_name,
      "continuous_rod",
      (-0.8, 4.1, 0.0),
      damage=140.0,
      radius=35.0,
      overrides=overrides,
    )

    self.assertEqual(str(single_event.component_primary_name), "right_aileron_actuator")
    self.assertEqual(str(redundant_event.component_primary_name), "right_aileron_actuator")
    self.assertTrue(bool(single_event.component_primary_critical))
    self.assertFalse(bool(redundant_event.component_primary_critical))
    self.assertAlmostEqual(float(single_event.component_primary_redundancy_group), 0.0, delta=1.0e-6)
    self.assertAlmostEqual(float(redundant_event.component_primary_redundancy_group), 2.0, delta=1.0e-6)
    self.assertGreater(
      float(single_event.component_failure_probability),
      float(redundant_event.component_failure_probability),
    )

  def test_phase3_component_redundancy_group_tracks_cumulative_integrity(self) -> None:
    sim = ef_py.SimulationKernel()
    sim.reset(20260526)
    self.assertTrue(sim.load_database(_DB_PATH))
    attacker_id, target_id = _spawn_attacker_and_named_target(sim, "F-16C_Block50")
    profile = _make_warhead_profile("continuous_rod", damage=160.0, radius=35.0)

    self.assertTrue(
      bool(
        sim.debug_apply_profiled_local_proximity_hit(
          attacker_id,
          target_id,
          -0.8,
          4.1,
          0.0,
          profile,
        )
      )
    )
    first_event = sim.export_recent_engagement_events().effects_events[-1]
    first_integrity = float(first_event.component_primary_integrity)
    first_group_availability = float(first_event.component_redundancy_group_availability)

    self.assertEqual(str(first_event.component_primary_name), "right_aileron_actuator")
    self.assertEqual(
      str(first_event.component_primary_redundancy_group_id),
      "lateral_flight_control_actuators",
    )
    self.assertEqual(int(first_event.component_redundancy_group_member_count), 2)
    self.assertEqual(int(first_event.component_redundancy_group_failed_count), 0)
    self.assertLess(first_integrity, 1.0)
    self.assertGreater(first_group_availability, first_integrity)

    self.assertTrue(
      bool(
        sim.debug_apply_profiled_local_proximity_hit(
          attacker_id,
          target_id,
          -0.8,
          4.1,
          0.0,
          profile,
        )
      )
    )
    second_event = sim.export_recent_engagement_events().effects_events[-1]
    second_integrity = float(second_event.component_primary_integrity)
    second_group_availability = float(second_event.component_redundancy_group_availability)

    self.assertLess(second_integrity, first_integrity)
    self.assertLess(second_group_availability, first_group_availability)
    self.assertGreater(second_group_availability, second_integrity)

  def test_phase3_component_availability_feeds_aircraft_structure_state(self) -> None:
    sim = _make_kernel()
    attacker_id, target_id = _spawn_structured_f16_pair(sim)
    profile = _make_warhead_profile("blast_fragmentation", damage=140.0, radius=35.0)

    ok = sim.debug_apply_profiled_local_proximity_hit(
      attacker_id,
      target_id,
      -0.8,
      0.0,
      0.0,
      profile,
    )
    self.assertTrue(bool(ok))
    self.assertTrue(sim.is_unit_active(target_id))

    event = sim.export_recent_engagement_events().effects_events[-1]
    overlay = _aircraft_damage_overlay(sim, target_id)

    self.assertEqual(str(event.component_primary_name), "wing_spar_center")
    self.assertEqual(str(event.component_primary_system), "wings")
    self.assertLess(float(event.component_redundancy_group_availability), 1.0)
    self.assertLessEqual(
      overlay["structure"],
      float(event.component_redundancy_group_availability) + 1.0e-6,
    )

  def test_phase3_component_availability_feeds_control_axis_state(self) -> None:
    target_name = "F-16C_A2_SingleAxisAvailability_Test"
    overrides = [
      _make_f16_component_redundancy_override(
        target_name,
        redundancy_group=0.0,
        critical=True,
      )
    ]
    sim = _kernel_with_unit_overrides(overrides)
    attacker_id, target_id = _spawn_attacker_and_named_target(sim, target_name)
    profile = _make_warhead_profile("blast_fragmentation", damage=90.0, radius=35.0)

    before = _aircraft_damage_overlay(sim, target_id)
    ok = sim.debug_apply_profiled_local_proximity_hit(
      attacker_id,
      target_id,
      -0.8,
      4.1,
      0.0,
      profile,
    )
    self.assertTrue(bool(ok))
    self.assertTrue(sim.is_unit_active(target_id))

    event = sim.export_recent_engagement_events().effects_events[-1]
    overlay = _aircraft_damage_overlay(sim, target_id)
    group_availability = float(event.component_redundancy_group_availability)

    self.assertEqual(str(event.component_primary_name), "right_aileron_actuator")
    self.assertEqual(str(event.component_primary_system), "flight_control")
    self.assertEqual(int(event.component_redundancy_group_member_count), 1)
    self.assertLess(group_availability, 1.0)
    self.assertLess(overlay["roll_control"], before["roll_control"])
    self.assertLessEqual(overlay["roll_control"], group_availability + 1.0e-6)
    self.assertAlmostEqual(overlay["pitch_control"], before["pitch_control"], delta=1.0e-6)
    self.assertAlmostEqual(overlay["yaw_control"], before["yaw_control"], delta=1.0e-6)

    sim.step()
    tick_overlay = _aircraft_damage_overlay(sim, target_id)
    self.assertLessEqual(tick_overlay["roll_control"], group_availability + 1.0e-6)

  def test_phase3_component_availability_consequences_flow_into_damage_report(self) -> None:
    target_name = "F-16C_A2_ComponentConsequenceClosure_Test"
    overrides = [
      _make_f16_component_redundancy_override(
        target_name,
        redundancy_group=0.0,
        critical=True,
      )
    ]
    sim = _kernel_with_unit_overrides(overrides)
    attacker_id, target_id = _spawn_attacker_and_named_target(sim, target_name)
    profile = _make_warhead_profile("blast_fragmentation", damage=60.0, radius=35.0)

    event = None
    report = None
    overlay = None
    for _ in range(4):
      ok = sim.debug_apply_profiled_local_proximity_hit(
        attacker_id,
        target_id,
        -0.8,
        4.1,
        0.0,
        profile,
      )
      self.assertTrue(bool(ok))
      self.assertTrue(sim.is_unit_active(target_id))
      events = sim.export_recent_engagement_events()
      event = events.effects_events[-1]
      report = events.damage_reports[-1]
      overlay = _aircraft_damage_overlay(sim, target_id)
      if bool(report.flight_control_kill):
        break
    else:
      self.fail("component damage did not produce a flight-control kill report")

    self.assertIsNotNone(event)
    self.assertIsNotNone(report)
    self.assertIsNotNone(overlay)
    group_availability = float(event.component_redundancy_group_availability)

    self.assertEqual(str(event.component_primary_name), "right_aileron_actuator")
    self.assertEqual(str(event.component_primary_system), "flight_control")
    self.assertLess(group_availability, 1.0)
    self.assertLessEqual(overlay["roll_control"], group_availability + 1.0e-6)
    self.assertTrue(bool(report.forced_landing))
    self.assertTrue(bool(report.flight_control_kill))
    self.assertTrue(bool(report.mobility_kill))
    self.assertFalse(bool(report.propulsion_kill))
    self.assertFalse(bool(report.crew_kill))
    self.assertFalse(bool(report.destroyed))
    self.assertEqual(str(report.loss_state_to), "mobility_kill")
    self.assertEqual(bool(report.forced_landing), bool(overlay["forced_landing"]))
    self.assertEqual(bool(report.flight_control_kill), bool(overlay["flight_control_kill"]))
    self.assertEqual(bool(report.propulsion_kill), bool(overlay["propulsion_kill"]))
    self.assertEqual(bool(report.crew_kill), bool(overlay["crew_kill"]))

  def test_phase3_component_failure_probability_is_sampled_and_reported(self) -> None:
    wing = (-0.753, 4.0, 0.0)

    low_energy_overlay, _, low_event = _profiled_local_hit_overlay(
      "continuous_rod",
      wing,
      damage=35.0,
      radius=35.0,
    )
    high_energy_overlay, _, high_event = _profiled_local_hit_overlay(
      "continuous_rod",
      wing,
      damage=180.0,
      radius=35.0,
    )

    self.assertTrue(bool(high_event.direct_hitbox_intersection))
    self.assertGreater(float(high_event.component_failure_probability), 0.0)
    self.assertLessEqual(float(high_event.component_failure_probability), 1.0)
    self.assertGreaterEqual(float(high_event.component_failure_sample), 0.0)
    self.assertLessEqual(float(high_event.component_failure_sample), 1.0)
    self.assertGreater(
      float(high_event.component_failure_probability),
      float(low_event.component_failure_probability),
    )
    self.assertGreaterEqual(int(high_event.component_hit_count), 1)
    high_row = list(high_event.component_mechanism_load_rows)[0]
    low_row = list(low_event.component_mechanism_load_rows)[0]
    high_response = _component_response_for_load_row(high_event, high_row)
    low_response = _component_response_for_load_row(low_event, low_row)
    self.assertLess(
      float(high_response.integrity_after),
      float(low_response.integrity_after),
    )
    self.assertLess(
      high_energy_overlay["flight_control"],
      low_energy_overlay["flight_control"],
    )
    self.assertLess(
      high_energy_overlay["hydraulic"],
      low_energy_overlay["hydraulic"],
    )

  def test_phase3_component_failure_probability_consumes_mechanism_load_evidence(self) -> None:
    wing = (-0.753, 4.0, 0.0)

    _low_overlay, low_event = _profiled_local_hit_overlay_and_event_with_velocity(
      "continuous_rod",
      wing,
      (0.0, -220.0, 0.0),
      damage=90.0,
      radius=35.0,
    )
    _high_overlay, high_event = _profiled_local_hit_overlay_and_event_with_velocity(
      "continuous_rod",
      wing,
      (900.0, -250.0, 0.0),
      damage=90.0,
      radius=35.0,
    )

    self.assertEqual(str(low_event.component_failure_probability_source), "synthetic_sigmoid")
    self.assertEqual(str(high_event.component_failure_probability_source), "synthetic_sigmoid")
    self.assertFalse(bool(low_event.component_failure_probability_calibrated))
    self.assertFalse(bool(high_event.component_failure_probability_calibrated))
    self.assertAlmostEqual(
      float(low_event.component_failure_sample),
      float(high_event.component_failure_sample),
      delta=1.0e-9,
    )
    self.assertGreater(float(high_event.closure_mps), float(low_event.closure_mps))
    self.assertGreater(
      float(high_event.mechanism_rod_cut_margin),
      float(low_event.mechanism_rod_cut_margin),
    )
    self.assertGreater(
      float(high_event.mechanism_penetration_margin),
      float(low_event.mechanism_penetration_margin),
    )
    self.assertGreater(
      float(high_event.component_failure_probability),
      float(low_event.component_failure_probability),
    )

  def test_phase3_blast_fragmentation_component_failure_probability_tracks_load(self) -> None:
    wing = (-0.753, 4.0, 0.0)

    _low_overlay, _, low_event = _profiled_local_hit_overlay(
      "blast_fragmentation",
      wing,
      damage=55.0,
      radius=35.0,
    )
    _high_overlay, _, high_event = _profiled_local_hit_overlay(
      "blast_fragmentation",
      wing,
      damage=150.0,
      radius=35.0,
    )

    self.assertEqual(str(low_event.component_failure_probability_source), "synthetic_sigmoid")
    self.assertEqual(str(high_event.component_failure_probability_source), "synthetic_sigmoid")
    self.assertLess(
      float(high_event.component_primary_integrity),
      float(low_event.component_primary_integrity),
    )
    self.assertGreater(
      float(high_event.component_failure_probability),
      float(low_event.component_failure_probability),
    )

  def test_phase3_repeated_hits_raise_component_failure_probability_as_integrity_drops(self) -> None:
    sim = ef_py.SimulationKernel()
    sim.reset(20260526)
    self.assertTrue(sim.load_database(_DB_PATH))
    attacker_id, target_id = _spawn_structured_f16_pair(sim)
    profile = _make_warhead_profile("continuous_rod", damage=45.0, radius=35.0)

    for _ in range(2):
      self.assertTrue(
        bool(
          sim.debug_apply_profiled_local_proximity_hit(
            attacker_id,
            target_id,
            -0.753,
            4.0,
            0.0,
            profile,
          )
        )
      )

    events = list(sim.export_recent_engagement_events().effects_events)
    self.assertEqual(len(events), 2)
    first_event, second_event = events

    self.assertEqual(str(first_event.component_primary_name), "right_aileron_actuator")
    self.assertEqual(str(second_event.component_primary_name), "right_aileron_actuator")
    self.assertLess(
      float(second_event.component_primary_integrity),
      float(first_event.component_primary_integrity),
    )
    self.assertLess(
      float(second_event.component_redundancy_group_availability),
      float(first_event.component_redundancy_group_availability),
    )
    self.assertGreaterEqual(
      float(second_event.component_failure_probability),
      float(first_event.component_failure_probability),
    )
    self.assertGreaterEqual(float(second_event.component_failure_sample), 0.0)
    self.assertLessEqual(float(second_event.component_failure_sample), 1.0)
