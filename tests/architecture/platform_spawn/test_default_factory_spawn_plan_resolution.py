from __future__ import annotations

import textwrap

from tests.architecture.helpers import (
  REPO_ROOT,
  compile_cpp_snippet,
  dependency_include_path,
)

DEFAULT_UNIT_FACTORY_HEADER = REPO_ROOT / "src" / "models" / "core" / "default_unit_factory.h"
PLATFORM_SPAWN_INCLUDE_PATHS = (
  dependency_include_path("spdlog"),
  dependency_include_path("flecs"),
  dependency_include_path("nlohmann_json"),
)


def _compile_and_run(source: str):
  return compile_cpp_snippet(
    source,
    include_paths=PLATFORM_SPAWN_INCLUDE_PATHS,
    syntax_only=True,
    binary_prefix="platform_spawn_default_factory_resolution",
  )


def test_wp14_content_definition_lowering_header_exists() -> None:
  assert DEFAULT_UNIT_FACTORY_HEADER.is_file()


def test_wp14_default_factory_static_lowering_shape_preserves_type_name_projection_path() -> None:
  header = DEFAULT_UNIT_FACTORY_HEADER.read_text(encoding="utf-8")

  for token in (
    "build_platform_capability_bundle_template",
    "resolve_platform_spawn_plan",
    "validate_platform_capability_bundle_template",
    "validate_resolved_platform_spawn_plan",
    "kPlatformSpawnRequestKindTypeNameProjection",
    "kPlatformMaterializationStrategyFactoryProjection",
  ):
    assert token in header

  for evidence_token in (
    '"sensor_refs"',
    '"sensor_ref"',
    '"inline_sensor"',
    '"mounted_sensors"',
    '"sonar"',
    '"default_loadout"',
    '"naval_weapon_system"',
    '"ship_platform_mobility"',
    '"ship_platform_survivability"',
    '"command_link"',
    '"data_link"',
    '"embarked_air_ops"',
    '"health_and_damage_model"',
  ):
    assert evidence_token in header

  spawn_anchor = header.index("flecs::entity spawn(")
  resolution_anchor = header.index(
    "resolve_platform_spawn_plan_for_type_name(unit_name)",
    spawn_anchor,
  )
  validation_anchor = header.index(
    "validate_resolved_platform_spawn_plan(",
    resolution_anchor,
  )
  definition_anchor = header.index(
    "const UnitDefinition &def = it->second;",
    validation_anchor,
  )
  materialization_anchor = header.index("auto e =", definition_anchor)
  assert resolution_anchor < validation_anchor < definition_anchor < materialization_anchor
  assert "spawn_platform" not in header


def test_wp14_aircraft_bundle_and_plan_are_deterministic_and_validate() -> None:
  source = textwrap.dedent(
    r"""
    #include <iostream>
    #include <string>
    #include "models/core/default_unit_factory.h"

    int main() {
      DefaultUnitFactory factory;
      const UnitDefinition* def = factory.get_definition("Aircraft");
      if (def == nullptr) {
        std::cerr << "missing built-in Aircraft definition\n";
        return 1;
      }

      const auto bundle_a = factory.build_platform_capability_bundle_template("Aircraft", *def);
      const auto bundle_b = factory.build_platform_capability_bundle_template("Aircraft", *def);
      if (bundle_a.bundle_id != bundle_b.bundle_id ||
        bundle_a.source_type_name != bundle_b.source_type_name ||
        bundle_a.capabilities.size() != bundle_b.capabilities.size()) {
        std::cerr << "bundle lowering is not deterministic\n";
        return 1;
      }
      if (bundle_a.source_type_name != "Aircraft" ||
        bundle_a.capabilities.empty() ||
        bundle_a.template_evidence_ref.empty()) {
        std::cerr << "bundle missing required evidence\n";
        return 1;
      }

      const auto bundle_validation =
        factory.validate_platform_capability_bundle_template("Aircraft", *def);
      if (!bundle_validation.valid) {
        std::cerr << "aircraft bundle should validate\n";
        return 1;
      }

      const auto plan_a = factory.resolve_platform_spawn_plan("Aircraft", *def);
      const auto plan_b = factory.resolve_platform_spawn_plan("Aircraft", *def);
      if (plan_a.plan_id != plan_b.plan_id ||
        plan_a.capability_bundle_id != bundle_a.bundle_id ||
        plan_a.source_type_name != "Aircraft" ||
        !plan_a.admitted ||
        plan_a.source_request_kind !=
          std::string(runtime::platform_capabilities::
                  kPlatformSpawnRequestKindTypeNameProjection) ||
        plan_a.materialization_strategy !=
          std::string(runtime::platform_capabilities::
                  kPlatformMaterializationStrategyFactoryProjection)) {
        std::cerr << "resolved aircraft plan drifted\n";
        return 1;
      }

      const auto plan_validation =
        factory.validate_resolved_platform_spawn_plan("Aircraft", *def);
      if (!plan_validation.valid) {
        std::cerr << "aircraft plan should validate\n";
        return 1;
      }

      return 0;
    }
    """
  )
  result = _compile_and_run(source)
  assert result.returncode == 0, result.stderr + result.stdout


def test_wp14_synthetic_platform_definition_surfaces_sensor_loadout_command_and_naval_evidence() -> None:
  source = textwrap.dedent(
    rf"""
    #include <iostream>
    #include <string>
    #include "models/core/default_unit_factory.h"

    int main() {{
      DefaultUnitFactory factory;

      UnitDefinition synthetic{{}};
      synthetic.type = UnitType::Ship;
      synthetic.name = "Synthetic_DDG";
      synthetic.health = {{100.0, 100.0, false, false, false}};
      synthetic.has_sensor = true;
      synthetic.sensor = make_unit_definition_default_sensor_preset(
        46300.0, 360.0, 0.5, 1.0, 0.0, 0.0, 5.0, 0.0, static_cast<int>(SensorType::Radar));
      synthetic.sensor_ref = "AN/SPS-67(V)_Surface_Search";
      synthetic.sensor_refs = {{
        "AN/SPS-67(V)_Surface_Search",
        "AN/SPY-1D_Volume_Search_MVP",
      }};
      synthetic.mounted_sensors.mounts.push_back(SensorMount{{synthetic.sensor, "synthetic_surface_radar"}});
      synthetic.default_loadout = {{
        {{1, "AIM-120C-7"}},
        {{2, "AIM-9X"}},
      }};
      synthetic.has_command_link = true;
      synthetic.command_link = {{0.2, 0.0}};
      synthetic.has_data_link = true;
      synthetic.data_link_network_id = 1;
      synthetic.has_ship_platform = true;
      synthetic.ship_platform.displacement_full_load_kg = 8362000.0;
      synthetic.ship_platform.length_m = 153.8;
      synthetic.ship_platform.beam_m = 20.4;
      synthetic.ship_platform.draft_m = 9.3;
      synthetic.has_naval_stores = true;
      synthetic.naval_stores.fuel_units_current = 45.0;
      synthetic.naval_stores.fuel_units_max = 90.0;
      synthetic.naval_stores.missile_units_current = 72.0;
      synthetic.naval_stores.missile_units_max = 90.0;
      synthetic.has_naval_weapon_system = true;
      synthetic.naval_weapon_system.mounts.push_back(NavalWeaponMountDefinition{{
        "forward_vls_sam",
        NavalWeaponType::VlsSam,
        29,
        29,
        1,
        2.0,
        -1.0,
        60000.0,
        900.0,
        0.8,
        180.0,
        true,
        false,
        "aegis_sam_mvp",
        "air",
        "synthetic test mount",
      }});
      synthetic.has_embarked_air_ops = false;
      synthetic.has_sonar = true;
      synthetic.sonar.max_range_m = 25000.0;
      synthetic.sonar.scan_period_s = 5.0;
      synthetic.sonar.track_memory_s = 20.0;
      synthetic.sonar.ambient_noise_db = 72.0;
      synthetic.sonar.passive_only = true;
      synthetic.sonar.bearing_only = false;

      const auto bundle = factory.build_platform_capability_bundle_template("Synthetic_DDG", synthetic);
      const auto plan = factory.resolve_platform_spawn_plan("Synthetic_DDG", synthetic);
      const auto bundle_validation =
        factory.validate_platform_capability_bundle_template("Synthetic_DDG", synthetic);
      const auto plan_validation =
        factory.validate_resolved_platform_spawn_plan("Synthetic_DDG", synthetic);

      if (!bundle_validation.valid || !plan_validation.valid || !plan.admitted) {{
        std::cerr << "synthetic platform should validate and admit\n";
        return 1;
      }}

      const auto has_capability = [](const auto& bundle, const char* family, const char* type) {{
        for (const auto& capability : bundle.capabilities) {{
          if (capability.family == family && capability.capability_type == type) {{
            return true;
          }}
        }}
        return false;
      }};

      if (!has_capability(bundle, "sensing", "sensor_refs") ||
        !has_capability(bundle, "sensing", "sensor_ref") ||
        !has_capability(bundle, "sensing", "mounted_sensors") ||
        !has_capability(bundle, "launching", "default_loadout") ||
        !has_capability(bundle, "launching", "naval_weapon_system") ||
        !has_capability(bundle, "mobility", "ship_platform_mobility") ||
        !has_capability(bundle, "survivability", "ship_platform_survivability") ||
        !has_capability(bundle, "command", "command_link") ||
        !has_capability(bundle, "communication", "data_link")) {{
        std::cerr << "synthetic evidence family coverage drifted\n";
        return 1;
      }}

      if (plan.capability_bundle_id != bundle.bundle_id ||
        plan.resolved_capabilities.size() != bundle.capabilities.size()) {{
        std::cerr << "bundle/plan identity drifted\n";
        return 1;
      }}

      return 0;
    }}
    """
  )
  result = _compile_and_run(source)
  assert result.returncode == 0, result.stderr + result.stdout


def test_wp14_spawn_path_uses_observable_type_name_plan_resolution_entrypoint() -> None:
  header = DEFAULT_UNIT_FACTORY_HEADER.read_text(encoding="utf-8")

  assert "resolve_platform_spawn_plan_for_type_name" in header
  spawn_anchor = header.index("flecs::entity spawn(")
  evidence_anchor = header.index(
    "resolve_platform_spawn_plan_for_type_name(unit_name)", spawn_anchor
  )
  validate_anchor = header.index(
    "validate_resolved_platform_spawn_plan(",
    evidence_anchor,
  )
  gate_anchor = header.index(
    "if (!plan_validation.valid || !resolved_spawn_plan.admitted)", validate_anchor
  )
  definition_anchor = header.index("const UnitDefinition &def = it->second;", gate_anchor)
  materialization_anchor = header.index("auto e =", definition_anchor)
  assert evidence_anchor < validate_anchor < gate_anchor < definition_anchor < materialization_anchor
  assert "spawn_platform" not in header


def test_wp14_resolved_spawn_plan_evidence_is_queryable_from_type_name_projection_path() -> None:
  source = textwrap.dedent(
    r"""
    #include <algorithm>
    #include <iostream>
    #include <string>
    #include "models/core/default_unit_factory.h"

    int main() {
      namespace platform = runtime::platform_capabilities;
      DefaultUnitFactory factory;

      const auto plan =
        factory.resolve_platform_spawn_plan_for_type_name("Aircraft");
      const auto validation =
        factory.validate_resolved_platform_spawn_plan_for_type_name("Aircraft");

      if (!validation.valid || !plan.admitted) {
        std::cerr << "type_name projection plan should validate and admit\n";
        return 1;
      }
      if (plan.source_request_kind !=
          std::string(platform::kPlatformSpawnRequestKindTypeNameProjection) ||
        plan.source_type_name != "Aircraft" ||
        !plan.type_name_projection_preserved) {
        std::cerr << "type_name projection evidence drifted\n";
        return 1;
      }
      if (plan.materialization_strategy !=
        std::string(platform::kPlatformMaterializationStrategyFactoryProjection)) {
        std::cerr << "materialization strategy drifted\n";
        return 1;
      }
      if (plan.plan_id.empty() ||
        plan.capability_bundle_id.empty() ||
        plan.resolved_platform_definition_ref.empty() ||
        plan.template_evidence_ref.empty() ||
        plan.resolution_evidence_ref.empty() ||
        plan.materialization_evidence_ref.empty() ||
        plan.evidence_refs.empty() ||
        plan.resolved_capabilities.empty()) {
        std::cerr << "resolved spawn plan evidence is incomplete\n";
        return 1;
      }

      const auto has_evidence = [&](const std::string& value) {
        return std::find(plan.evidence_refs.begin(), plan.evidence_refs.end(), value) !=
          plan.evidence_refs.end();
      };
      if (!has_evidence(plan.template_evidence_ref) ||
        !has_evidence(plan.resolution_evidence_ref) ||
        !has_evidence(plan.materialization_evidence_ref)) {
        std::cerr << "plan-level evidence refs are not inspectable\n";
        return 1;
      }

      const auto has_family = [&](std::string family) {
        return std::any_of(
          plan.resolved_capabilities.begin(),
          plan.resolved_capabilities.end(),
          [&](const auto& capability) {
            return capability.family == family &&
              !capability.capability_id.empty() &&
              !capability.capability_type.empty() &&
              !capability.evidence_refs.empty();
          });
      };
      if (!has_family(std::string(platform::kCapabilityFamilyMobility)) ||
        !has_family(std::string(platform::kCapabilityFamilySensing)) ||
        !has_family(std::string(platform::kCapabilityFamilySurvivability))) {
        std::cerr << "capability family evidence coverage drifted\n";
        return 1;
      }

      const auto missing =
        factory.resolve_platform_spawn_plan_for_type_name("Missing_Type");
      const auto missing_validation =
        factory.validate_resolved_platform_spawn_plan_for_type_name("Missing_Type");
      if (!missing_validation.valid ||
        missing.admitted ||
        !missing.type_name_projection_preserved ||
        missing.source_request_kind !=
          std::string(platform::kPlatformSpawnRequestKindTypeNameProjection) ||
        missing.rejection_reason !=
          "resolved_platform_spawn_plan_type_name_not_found") {
        std::cerr << "missing type_name rejection evidence drifted\n";
        return 1;
      }

      return 0;
    }
    """
  )
  result = _compile_and_run(source)
  assert result.returncode == 0, result.stderr + result.stdout


def test_wp14_resolved_spawn_plan_air_and_naval_type_names_share_materialization_chain() -> None:
  source = textwrap.dedent(
    r"""
    #include <iostream>
    #include <string>
    #include "models/core/default_unit_factory.h"

    int main() {
      namespace platform = runtime::platform_capabilities;
      DefaultUnitFactory factory;

      const auto air =
        factory.resolve_platform_spawn_plan_for_type_name("F-16C_Block50");
      const auto naval =
        factory.resolve_platform_spawn_plan_for_type_name("DDG-51_Flight_I_USS_Arleigh_Burke");

      const auto same_chain = [&](const auto& plan, const char* type_name) {
        if (!plan.admitted) {
          std::cerr << type_name << " plan was not admitted\n";
          return false;
        }
        if (plan.source_request_kind !=
            std::string(platform::kPlatformSpawnRequestKindTypeNameProjection) ||
          !plan.type_name_projection_preserved ||
          plan.materialization_strategy !=
            std::string(platform::kPlatformMaterializationStrategyFactoryProjection)) {
          std::cerr << type_name << " drifted off the type_name projection chain\n";
          return false;
        }
        if (plan.resolution_evidence_ref.empty() ||
          plan.materialization_evidence_ref.empty()) {
          std::cerr << type_name << " is missing plan-level evidence refs\n";
          return false;
        }
        return true;
      };

      if (!same_chain(air, "F-16C_Block50") ||
        !same_chain(naval, "DDG-51_Flight_I_USS_Arleigh_Burke")) {
        return 1;
      }

      return 0;
    }
    """
  )
  result = _compile_and_run(source)
  assert result.returncode == 0, result.stderr + result.stdout
