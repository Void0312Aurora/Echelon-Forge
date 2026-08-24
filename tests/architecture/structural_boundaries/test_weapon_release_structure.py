from __future__ import annotations

from tests.architecture.structural_boundaries.helpers import *


def test_wp22_pilot_weapon_release_moves_to_named_helper_and_simulation_kernel_systems_stays_inline_free() -> None:
  systems_text = _text(SIMULATION_KERNEL_SYSTEMS)
  registry_text = _text(REPO_ROOT / "src" / "core" / "engine" / "system_contribution_registry.cpp")
  helper_text = _text(PILOT_WEAPON_RELEASE_SYSTEM)
  naval_helper_text = _text(NAVAL_MISSION_WEAPON_RELEASE_SYSTEM)
  engagement_event_types_text = _text(ENGAGEMENT_EVENT_TYPES)
  engagement_contracts_text = _text(
    REPO_ROOT / "src" / "runtime" / "contracts" / "engagement_contracts.h"
  )
  kernel_header_text = _text(SIMULATION_KERNEL_HEADER)
  kernel_cpp_text = _text(SIMULATION_KERNEL_CPP)
  kernel_services_text = _text(SIMULATION_KERNEL_SERVICES)
  kernel_services_header_text = _text(SIMULATION_KERNEL_SERVICES_HEADER)
  weapon_api_text = _text(SIMULATION_KERNEL_WEAPON_API)
  release_service_text = _text(SIMULATION_KERNEL_WEAPON_RELEASE_SERVICE)
  release_service_header_text = _text(SIMULATION_KERNEL_WEAPON_RELEASE_SERVICE_HEADER)
  recorder_header_text = _text(ENGAGEMENT_EVENT_RECORDER)
  engagement_store_text = _text(SIMULATION_KERNEL_ENGAGEMENT_EVENT_STORE)
  engagement_store_cpp_text = _text(SIMULATION_KERNEL_ENGAGEMENT_EVENT_STORE_CPP)
  damage_debug_text = _text(SIMULATION_KERNEL_DAMAGE_DEBUG_API)
  damage_bridge_text = _text(WEAPON_RELEASE_DAMAGE_BRIDGE)
  provider_catalog_text = _text(
    REPO_ROOT
    / "src"
    / "runtime"
    / "providers"
    / "default_simulation_provider_catalog.cpp"
  )
  cmake_text = _text(CMAKE_LISTS)
  inline_systems = INLINE_REGISTERED_SYSTEM_PATTERN.findall(systems_text)
  inline_on_update = [name for name, kind in inline_systems if kind == "OnUpdate"]

  assert inline_on_update == [], (
    "simulation_kernel_systems.cpp must not accumulate registered-in-place inline "
    "OnUpdate systems once PilotWeaponRelease has been migrated to a named helper"
  )
  assert '#include "systems/combat/pilot_weapon_release_system.h"' in systems_text
  assert '#include "systems/domains/naval/naval_mission_weapon_release_system.h"' in systems_text
  assert not _contains_cpp_marker(
    systems_text,
    "IWeaponReleaseService& weapon_release_service = *this",
  )
  assert "register_pilot_weapon_release_system" in registry_text
  assert "register_naval_mission_weapon_release_system" in registry_text
  assert "ecs.set<EngagementEventRecorderRef>({this})" not in systems_text
  assert "ecs.set<EngagementEventRecorderRef>" not in systems_text
  assert "&EngagementEventRecorderRef::recorder" in provider_catalog_text
  assert "&WeaponReleaseServiceRef::service" in provider_catalog_text
  assert "class SimulationKernel :" not in kernel_header_text
  assert "public IWeaponReleaseService" not in kernel_header_text
  assert "public IEngagementEventRecorder" not in kernel_header_text
  assert "std::unique_ptr<IWeaponReleaseService> weapon_release_service_" not in kernel_header_text
  assert "engagement_event_store_" not in kernel_header_text
  assert "std::unique_ptr<runtime::providers::DefaultSimulationComposition> composition_" in kernel_header_text
  assert "RecentEngagementEvents recent_engagement_events_" not in kernel_header_text
  assert "struct RecentEngagementEvents" not in kernel_header_text
  assert '#include "core/engine/simulation_kernel_engagement_event_store.h"' not in kernel_header_text
  assert '#include "core/engine/engagement_event_types.h"' in kernel_header_text
  assert '#include "runtime/contracts/engagement_contracts.h"' in engagement_event_types_text
  assert "struct RecentEngagementEvents" not in engagement_event_types_text
  assert "struct RecentEngagementEvents" in engagement_contracts_text
  assert "next_engagement_event_id_" not in kernel_header_text
  assert "pending_effects_launch_event_id_" not in kernel_header_text
  assert "record_legacy_launch_event(" not in kernel_header_text
  assert "record_effects_damage_event(" not in kernel_header_text
  assert "capture_engagement_damage_state(" not in kernel_header_text
  assert "public IEngagementEventStore" in engagement_store_text
  assert '#include "core/interfaces/engagement_event_store.h"' in engagement_store_text
  assert "struct EngagementEffectsDamageEventRecord" in recorder_header_text
  for source_name, source_text in (
    ("engagement_event_recorder.h", recorder_header_text),
    ("simulation_kernel_engagement_event_store.h", engagement_store_text),
    ("simulation_kernel_engagement_event_store.cpp", engagement_store_cpp_text),
  ):
    _assert_effects_damage_recorder_signatures_are_dto_only(source_name, source_text)
    assert "record_effects_damage_event_legacy(" not in source_text, (
      f"{source_name} must not reintroduce the private TM05 long-argument "
      "effects damage recording helper"
    )
  assert "RecentEngagementEvents recent_engagement_events_" in engagement_store_text
  assert "next_engagement_event_id_" in engagement_store_text
  assert "pending_effects_launch_event_id_" in engagement_store_text
  assert "SimulationKernelEngagementEventStore::record_legacy_launch_event(" in engagement_store_cpp_text
  assert "SimulationKernelEngagementEventStore::record_effects_damage_event(" in engagement_store_cpp_text
  assert "EngagementEffectsDamageEventRecord record" in engagement_store_text
  assert "EngagementEffectsDamageEventRecord event_record{}" in release_service_text
  assert "SimulationKernelEngagementEventStore::capture_engagement_damage_state(" in engagement_store_cpp_text
  assert "SimulationKernelEngagementEventStore::" not in damage_debug_text
  _assert_debug_damage_paths_use_dto_builder(damage_debug_text)
  assert "SimulationKernelWeaponReleaseService final : public IWeaponReleaseService" not in kernel_cpp_text
  assert (
    "SimulationKernelEngagementEventRecorder final : public IEngagementEventRecorder"
    not in kernel_cpp_text
  )
  assert "SimulationKernelEngagementEventRecorder" not in kernel_services_text
  assert (
    "SimulationKernelWeaponReleaseService final : public IWeaponReleaseService"
    in release_service_header_text
  )
  assert (
    "SimulationKernelEngagementEventRecorder final : public IEngagementEventRecorder"
    not in kernel_services_text
  )
  assert "make_simulation_kernel_weapon_release_service(" in kernel_services_text
  assert "make_simulation_kernel_weapon_release_service(" not in kernel_cpp_text
  assert "make_simulation_kernel_weapon_release_service(" in provider_catalog_text
  assert not _contains_cpp_marker(
    kernel_cpp_text,
    "make_simulation_kernel_weapon_release_service(*this)",
  )
  assert "std::make_unique<SimulationKernelEngagementEventStore>(world)" in provider_catalog_text
  assert "src/core/engine/simulation_kernel_engagement_event_store.cpp" in cmake_text
  assert "src/core/engine/simulation_kernel_services.cpp" in cmake_text
  assert "src/core/engine/simulation_kernel_weapon_release_service.cpp" in cmake_text
  assert "service->fire_missile(" in weapon_api_text
  assert "service->fire_naval_weapon(" in weapon_api_text
  assert "SimulationKernelWeaponReleaseService::fire_missile(" in release_service_text
  assert "SimulationKernelWeaponReleaseService::fire_weapon_from_pilot_action(" in release_service_text
  assert "SimulationKernelWeaponReleaseService::fire_naval_weapon_from_mission_command(" in release_service_text
  assert "launch_recorder_.record_legacy_launch_event(" in release_service_text
  assert not _contains_cpp_marker(release_service_header_text, "SimulationKernel&")
  assert not _contains_cpp_marker(release_service_text, "SimulationKernel&")
  assert "class IWeaponReleaseDamageBridge" in damage_bridge_text
  assert "virtual bool apply_proximity_hit(" in damage_bridge_text
  assert '#include "core/interfaces/weapon_release_damage_bridge.h"' in release_service_header_text
  assert '#include "core/interfaces/weapon_release_damage_bridge.h"' in provider_catalog_text
  assert "std::unique_ptr<IWeaponReleaseDamageBridge> weapon_release_damage_bridge_" not in kernel_header_text
  assert (
    "class SimulationKernelWeaponReleaseDamageBridge final : public IWeaponReleaseDamageBridge"
    in provider_catalog_text
  )
  assert _contains_cpp_marker(
    provider_catalog_text,
    "std::make_unique<SimulationKernelWeaponReleaseDamageBridge>(kernel)",
  )
  assert _contains_cpp_marker(
    kernel_services_header_text,
    "IWeaponReleaseDamageBridge& damage_bridge",
  )
  assert _contains_cpp_marker(
    kernel_services_text,
    "IWeaponReleaseDamageBridge& damage_bridge",
  )
  assert _contains_cpp_marker(
    release_service_header_text,
    "IWeaponReleaseDamageBridge& damage_bridge_",
  )
  assert "std::function" not in release_service_header_text
  assert "kernel_.fire_weapon_from_pilot_action(" not in kernel_services_text
  assert "kernel_.fire_naval_weapon_from_mission_command(" not in kernel_services_text
  assert 'ecs.system<const PilotAction>("PilotWeaponRelease")' not in systems_text
  assert 'query<const MissionCommand, const NavalWeaponSystem>()' not in kernel_cpp_text

  assert '#include "core/engine/simulation_kernel.h"' not in helper_text
  assert '#include "core/engine/simulation_kernel.h"' not in naval_helper_text
  assert not _contains_cpp_marker(helper_text, "SimulationKernel&")
  assert not _contains_cpp_marker(naval_helper_text, "SimulationKernel&")
  assert '#include "core/interfaces/weapon_release_service.h"' in helper_text
  assert '#include "core/interfaces/weapon_release_service.h"' in naval_helper_text
  assert "register_pilot_weapon_release_system(" in helper_text
  assert not _contains_cpp_marker(helper_text, "IWeaponReleaseService& weapon_release_service")
  assert "e.world().get<WeaponReleaseServiceRef>()" in helper_text
  assert "service_ref->service->fire_weapon_from_pilot_action(" in helper_text
  assert 'ecs.system<const PilotAction>("PilotWeaponRelease")' in helper_text
  assert "fire_weapon_from_pilot_action(" in helper_text
  assert "register_naval_mission_weapon_release_system(" in naval_helper_text
  assert not _contains_cpp_marker(
    naval_helper_text,
    "IWeaponReleaseService& weapon_release_service",
  )
  assert "e.world().get<WeaponReleaseServiceRef>()" in naval_helper_text
  assert "service_ref->service->fire_naval_weapon_from_mission_command(" in naval_helper_text
  assert 'ecs.system<const MissionCommand, const NavalWeaponSystem>("NavalMissionWeaponRelease")' in naval_helper_text
  assert "fire_naval_weapon_from_mission_command(" in naval_helper_text

def test_tm04_weapon_release_service_is_not_a_kernel_forwarding_adapter() -> None:
  kernel_header_text = _text(SIMULATION_KERNEL_HEADER)
  kernel_services_text = _text(SIMULATION_KERNEL_SERVICES)
  weapon_api_text = _text(SIMULATION_KERNEL_WEAPON_API)
  release_service_text = _text(SIMULATION_KERNEL_WEAPON_RELEASE_SERVICE)
  release_service_header_text = _text(SIMULATION_KERNEL_WEAPON_RELEASE_SERVICE_HEADER)

  assert "friend class SimulationKernelWeaponReleaseService" not in kernel_header_text
  assert "fire_weapon_from_pilot_action(uint64_t attacker_id)" not in kernel_header_text
  assert "try_fire_naval_mission_weapon(" not in kernel_header_text
  assert '#include "simulation_kernel.h"' not in release_service_text
  assert not _contains_cpp_marker(release_service_header_text, "SimulationKernel&")
  assert not _contains_cpp_marker(release_service_text, "SimulationKernel&")
  assert "kernel_." not in kernel_services_text
  assert "kernel_." not in release_service_text
  assert "SimulationKernel::fire_weapon_from_pilot_action(" not in weapon_api_text
  assert "SimulationKernel::try_fire_naval_mission_weapon(" not in weapon_api_text
  for marker in (
    "SimulationKernelWeaponReleaseService::fire_missile(",
    "resolve_missile_launch_definition(",
    "naval_weapon_mounts::consume_mount_shot(",
    "launch_recorder_.record_legacy_launch_event(",
    "damage_recorder_.record_effects_damage_event(",
    "damage_bridge_.apply_proximity_hit(",
  ):
    assert marker in release_service_text
