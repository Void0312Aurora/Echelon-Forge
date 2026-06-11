from __future__ import annotations

from tests.architecture.structural_boundaries.helpers import *


def test_a2_structured_air_effects_do_not_write_rl_score_authority() -> None:
  text = _text(DEFAULT_EFFECTS_MODEL)
  legacy_text = _text(DEFAULT_EFFECTS_LEGACY_DETAIL)
  air_platform_text = _text(DEFAULT_EFFECTS_AIR_DOMAIN)
  routing_text = _text(DEFAULT_EFFECTS_DOMAIN_ROUTING_DETAIL)

  assert (
    '#include "models/weapons/detail/default_effects_legacy_detail.inc"'
    in text
  )
  assert (
    '#include "models/weapons/detail/default_effects_domain_routing_detail.inc"'
    in text
  )
  assert re.search(
    r"if\s*\(\s*hp\s*&&\s*!structured_air_target\s*&&\s*"
    r"apply_legacy_health_damage\s*\(",
    text,
  ), (
    "legacy HP/Score damage must stay behind the non-structured-air gate "
    "in DefaultEffectsModel"
  )
  assert "score->" not in text

  legacy_block = _extract_function_block(
    legacy_text,
    "bool apply_legacy_health_damage(",
  )
  assert "score->total_reward" in legacy_block
  assert "score->hits_landed" in legacy_block
  assert "score->kills_confirmed" in legacy_block

  assert '#include "models/domains/air/default_effects_air_domain.h"' in routing_text
  assert '#include "models/domains/naval/default_effects_naval_domain.h"' in routing_text
  assert '#include "models/domains/ground/default_effects_ground_domain.h"' in routing_text
  assert "route_default_effects_target_domain(" in routing_text
  assert "DefaultEffectsTargetDomain::NavalPlaceholder" in routing_text
  assert "DefaultEffectsTargetDomain::GroundPlaceholder" in routing_text

  structured_block = _extract_function_block(
    air_platform_text,
    "inline bool resolve_default_effects_air_domain_consequences(",
  )
  assert "platform_damage && structured_air_target && scratch.structure_hit" in (
    structured_block
  )
  assert "score->" not in structured_block
  assert "Score*" not in structured_block

def test_domain_component_slices_stay_packaged_under_domains_root() -> None:
  components_readme = _text(REPO_ROOT / "src" / "components" / "README.md")
  domains_readme = _text(COMPONENT_DOMAINS_ROOT / "README.md")

  for required_dir in DOMAIN_COMPONENT_REQUIRED_DIRS:
    assert required_dir.is_dir(), (
      f"{required_dir.relative_to(REPO_ROOT)} is the maintained domain "
      "component owner directory"
    )

  for retired_dir in DOMAIN_COMPONENT_RETIRED_FLAT_DIRS:
    assert not retired_dir.exists(), (
      f"{retired_dir.relative_to(REPO_ROOT)} is a retired flat domain "
      "component directory; use src/components/domains/<domain>/..."
    )

  assert "New domains should follow the same shape" in domains_readme
  assert "instead of adding more top-level component directories" in domains_readme
  assert "Domain-specific command components live under" in components_readme
  assert "components/domains/<domain>" in components_readme

  maintained_sources = _maintained_source_texts()
  for include_prefix in DOMAIN_COMPONENT_RETIRED_INCLUDE_PREFIXES:
    offenders = [
      path.relative_to(REPO_ROOT).as_posix()
      for path, source_text in maintained_sources
      if include_prefix in source_text
    ]
    assert offenders == [], (
      f"{include_prefix} is a retired flat domain component include prefix; "
      f"use components/domains/<domain>/... instead. Offenders: {offenders}"
    )

def test_system_and_model_domain_slices_stay_packaged_under_domains_root() -> None:
  systems_readme = _text(REPO_ROOT / "src" / "systems" / "README.md")
  system_domains_readme = _text(SYSTEM_DOMAINS_ROOT / "README.md")
  models_readme = _text(REPO_ROOT / "src" / "models" / "README.md")
  model_domains_readme = _text(MODEL_DOMAINS_ROOT / "README.md")

  for required_dir in DOMAIN_SYSTEM_REQUIRED_DIRS + DOMAIN_MODEL_REQUIRED_DIRS:
    assert required_dir.is_dir(), (
      f"{required_dir.relative_to(REPO_ROOT)} is the maintained domain "
      "owner directory"
    )

  for retired_dir in DOMAIN_SYSTEM_MODEL_RETIRED_FLAT_DIRS:
    assert not retired_dir.exists(), (
      f"{retired_dir.relative_to(REPO_ROOT)} is a retired flat domain "
      "directory; use the layer's domains/<domain>/ directory"
    )

  assert "new domain runtime owners out of the" in system_domains_readme
  assert "new domain runtime owners should be added here" in systems_readme
  assert "New domain model" in model_domains_readme
  assert "owners should be added here" in model_domains_readme
  assert "new domain model owners should be" in models_readme

  maintained_sources = _maintained_source_texts()
  for include_prefix in DOMAIN_SYSTEM_MODEL_RETIRED_INCLUDE_PREFIXES:
    offenders = [
      path.relative_to(REPO_ROOT).as_posix()
      for path, source_text in maintained_sources
      if include_prefix in source_text
    ]
    assert offenders == [], (
      f"{include_prefix} is a retired flat domain include prefix; "
      f"use */domains/<domain>/... instead. Offenders: {offenders}"
    )

def test_domain_separation_split_generic_files_route_domain_owned_runtime() -> None:
  systems_text = _text(SIMULATION_KERNEL_SYSTEMS)
  logistics_text = _text(GENERIC_LOGISTICS_SYSTEM)
  naval_logistics_text = _text(NAVAL_LOGISTICS_SYSTEM)
  instrument_text = _text(REPO_ROOT / "src" / "systems" / "physics" / "instrument_system.h")
  air_propulsion_text = _text(
    REPO_ROOT / "src" / "systems" / "domains" / "air" / "propulsion_system.h"
  )
  sensor_text = _text(DEFAULT_SENSOR_MODEL)
  maritime_adapter_text = _text(NAVAL_SENSOR_MARITIME_ADAPTER)
  effects_text = _text(DEFAULT_EFFECTS_MODEL)
  routing_text = _text(DEFAULT_EFFECTS_DOMAIN_ROUTING_DETAIL)

  for retired_path in DOMAIN_SEPARATION_RETIRED_PUBLIC_FILES:
    assert not retired_path.exists(), (
      f"{retired_path.relative_to(REPO_ROOT)} is a retired domain-split "
      "compatibility/public entry and must not be recreated"
    )

  maintained_sources = _maintained_source_texts()
  for include_string in DOMAIN_SEPARATION_RETIRED_INCLUDE_STRINGS:
    offenders = [
      path.relative_to(REPO_ROOT).as_posix()
      for path, source_text in maintained_sources
      if include_string in source_text
    ]
    assert offenders == [], (
      f"{include_string} is retired by the domain split and still appears in "
      f"maintained source files: {offenders}"
    )

  assert "NavalUnderwayResupply" not in logistics_text
  assert "underway_replenishment_enabled" not in logistics_text
  assert "NavalUnderwayResupply" in naval_logistics_text
  assert "underway_replenishment_enabled" in naval_logistics_text
  assert '#include "systems/domains/naval/naval_logistics_system.h"' in systems_text
  assert "register_logistics_system(ecs);" in systems_text
  assert "register_naval_logistics_system(ecs);" in systems_text
  assert '#include "systems/domains/air/propulsion_system.h"' in systems_text
  assert "register_propulsion_system(ecs);" in systems_text

  assert '#include "components/physics/propulsion_readouts.h"' in logistics_text
  assert '#include "systems/domains/air/propulsion_system.h"' not in logistics_text
  assert "propulsion_readouts::fuel_flow_kg_per_s(" in logistics_text
  assert "flight_dynamics::propulsion_fuel_flow_kg_per_s(" not in logistics_text
  assert '#include "components/physics/propulsion_readouts.h"' in instrument_text
  assert '#include "systems/domains/air/propulsion_system.h"' not in instrument_text
  assert "propulsion_readouts::fuel_flow_kg_per_s(" in instrument_text
  assert "propulsion_readouts::engine_rpm_pct(" in instrument_text
  assert "flight_dynamics::propulsion_engine_rpm_pct(" not in instrument_text
  assert "propulsion_fuel_flow_kg_per_s(" not in air_propulsion_text
  assert "propulsion_engine_rpm_pct(" not in air_propulsion_text

  assert "components/domains/naval/platform/ship_platform.h" not in sensor_text
  assert "ShipPlatform" not in sensor_text
  assert '#include "models/domains/naval/naval_sensor_maritime_adapter.h"' in sensor_text
  assert "components/domains/naval/platform/ship_platform.h" in maritime_adapter_text
  assert "ShipPlatform" in maritime_adapter_text

  assert "is_structured_damage_air_target" not in effects_text
  assert "default_effects_air_platform_resolution_detail.inc" not in effects_text
  assert "route_default_effects_target_domain(" in routing_text
  assert '#include "models/domains/air/default_effects_air_domain.h"' in routing_text
  assert '#include "models/domains/naval/default_effects_naval_domain.h"' in routing_text
  assert '#include "models/domains/ground/default_effects_ground_domain.h"' in routing_text

def test_wp22_structural_docs_keep_noether_and_remaining_non_counterfactual_blockers_explicit() -> None:
  text_en = _text(STRUCTURAL_DOC_EN)
  text_zh = _text(STRUCTURAL_DOC_ZH)

  for required in (
    "Noether pass",
    "`PilotWeaponRelease` and naval mission weapon release now route through named",
    "`default_unit_factory.h` no longer direct-includes `legacy_command.h`",
    "`default_factory_legacy_spawn_compat.h` seed seam remains evaluation/guard",
  ):
    assert required in text_en

  for required in (
    "Noether pass",
    "`PilotWeaponRelease` 与 naval mission weapon release 现在都通过命名 helper system 注册",
    "`default_unit_factory.h` 已不再 direct include `legacy_command.h`",
    "`default_factory_legacy_spawn_compat.h` seed seam 在 typed control-state",
  ):
    assert required in text_zh

  for forbidden in (
    "naval post-step fire loop remains the explicit ordering blocker",
    "naval post-step ordering blocker remains live",
    "naval post-step fire loop 仍开放",
  ):
    assert forbidden not in text_en
    assert forbidden not in text_zh
