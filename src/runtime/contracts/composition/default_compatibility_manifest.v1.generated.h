#pragma once

#include <array>
#include <string_view>

namespace runtime::composition_contracts::generated {

inline constexpr std::array<std::string_view, 7> kDefaultCompatibilityResolvedJsonChunks = {
    R"EFJSON({
  "manifest": {
    "backend_request": {
      "backend_profile_id": "cpu_exact.reference",
      "provider_id": "builtin.backend.flecs_cpu",
      "required_capabilities": [
        "runtime.cpu_exact"
      ]
    },
    "compatibility_claims": [
      "legacy.cpu_exact_backend.v1",
      "legacy.default_kernel_construction.v1",
      "legacy.registration_order.v1"
    ],
    "component_contributions": [
      {
        "component_id": "AcousticModelRef",
        "plugin_id": "builtin.core_runtime",
        "registration_id": "flecs.component.acoustic_model_ref"
      },
      {
        "component_id": "ActionCommand",
        "plugin_id": "builtin.core_runtime",
        "registration_id": "flecs.component.action_command"
      },
      {
        "component_id": "ActionSpaceConfig",
        "plugin_id": "builtin.core_runtime",
        "registration_id": "flecs.component.action_space_config"
      },
      {
        "component_id": "AeroState",
        "plugin_id": "builtin.core_runtime",
        "registration_id": "flecs.component.aero_state"
      },
      {
        "component_id": "AeroTuning",
        "plugin_id": "builtin.core_runtime",
        "registration_id": "flecs.component.aero_tuning"
      },
      {
        "component_id": "AircraftDamageBaseline",
        "plugin_id": "builtin.core_runtime",
        "registration_id": "flecs.component.aircraft_damage_baseline"
      },
      {
        "component_id": "AircraftDamageState",
        "plugin_id": "builtin.core_runtime",
        "registration_id": "flecs.component.aircraft_damage_state"
      },
      {
        "component_id": "Alliance",
        "plugin_id": "builtin.core_runtime",
        "registration_id": "flecs.component.alliance"
      },
      {
        "component_id": "Ammo",
        "plugin_id": "builtin.core_runtime",
        "registration_id": "flecs.component.ammo"
      },
      {
        "component_id": "AngularVelocity",
        "plugin_id": "builtin.core_runtime",
        "registration_id": "flecs.component.angular_velocity"
      },
      {
        "component_id": "CommQueue",
        "plugin_id": "builtin.core_runtime",
        "registration_id": "flecs.component.comm_queue"
      },
      {
        "component_id": "CommandLag",
        "plugin_id": "builtin.core_runtime",
        "registration_id": "flecs.component.command_lag"
      },
      {
        "component_id": "CommandLink",
        "plugin_id": "builtin.core_runtime",
        "registration_id": "flecs.component.command_link"
      },
      {
        "component_id": "ComponentDamageState",
        "plugin_id": "builtin.core_runtime",
        "registration_id": "flecs.component.component_damage_state"
      },
      {
        "component_id": "ContactList",
        "plugin_id": "builtin.core_runtime",
        "registration_id": "flecs.component.contact_list"
      },
      {
        "component_id": "ControlLawState",
        "plugin_id": "builtin.core_runtime",
        "registration_id": "flecs.component.control_law_state"
      },
      {
        "component_id": "ControlModelRef",
        "plugin_id": "builtin.core_runtime",
        "registration_id": "flecs.component.control_model_ref"
      },
      {
        "component_id": "ControlSurfaceState",
        "plugin_id": "builtin.core_runtime",
        "registration_id": "flecs.component.control_surface_state"
      },
      {
        "component_id": "Countermeasures",
        "plugin_id": "builtin.core_runtime",
        "registration_id": "flecs.component.countermeasures"
      },
      {
        "component_id": "DataLink",
        "plugin_id": "builtin.core_runtime",
        "registration_id": "flecs.component.data_link"
      },
      {
        "component_id": "EGI",
        "plugin_id": "builtin.core_runtime",
        "registration_id": "flecs.component.egi"
      },
      {
        "component_id": "ESMReceiver",
        "plugin_id": "builtin.core_runtime",
        "registration_id": "flecs.component.esmreceiver"
      },
      {
        "component_id": "EffectsModelRef",
        "plugin_id": "builtin.core_runtime",
        "registration_id": "flecs.component.effects_model_ref"
      },
      {
        "component_id": "EmbarkedAirOps",
        "plugin_id": "builtin.core_runtime",
        "registration_id": "flecs.component.embarked_air_ops"
      },
      {
        "component_id": "EngagementEventRecorderRef",
        "plugin_id": "builtin.core_runtime",
        "registration_id": "flecs.component.engagement_event_recorder_ref"
      },
      {
        "component_id": "EngineTuning",
        "plugin_id": "builtin.core_runtime",
        "registration_id": "flecs.component.engine_tuning"
      },
      {
        "component_id": "EnvironmentModelRef",
        "plugin_id": "builtin.core_runtime",
        "registration_id": "flecs.component.environment_model_ref"
      },
      {
        "component_id": "FlightModel",
        "plugin_id": "builtin.core_runtime",
        "registration_id": "flecs.component.flight_model"
      },
      {
        "component_id": "ForceAccumulator",
        "plugin_id": "builtin.core_runtime",
        "registration_id": "flecs.component.force_accumulator"
      },
      {
        "component_id": "FuelSystem",
        "plugin_id": "builtin.core_runtime",
        "registration_id": "flecs.component.fuel_system"
      },
      {
        "component_id": "GearState",
        "plugin_id": "builtin.core_runtime",
        "registration_id": "flecs.component.gear_state"
      },
      {
        "component_id": "GroundState",
        "plugin_id": "builtin.core_runtime",
        "registration_id": "flecs.component.ground_state"
      },
      {
        "component_id": "GuidanceModelRef",
        "plugin_id": "builtin.core_runtime",
        "registration_id": "flecs.component.guidance_model_ref"
      },
      {
        "component_id": "Health",
        "plugin_id": "builtin.core_runtime",
        "registration_id": "flecs.component.health"
      },
      {
        "component_id": "HitboxConfig",
        "plugin_id": "builtin.core_runtime",
        "registration_id": "flecs.component.hitbox_config"
      },
      {
        "component_id": "Inertia",
        "plugin_id": "builtin.core_runtime",
        "registration_id": "flecs.component.inertia"
      },
      {
        "component_id": "InstrumentState",
        "plugin_id": "builtin.core_runtime",
        "registration_id": "flecs.component.instrument_state"
      },
      {
        "component_id": "Jammer",
        "plugin_id": "builtin.core_runtime",
        "registration_id": "flecs.component.jammer"
      },
      {
        "component_id": "KeyEntity",
        "plugin_id": "builtin.core_runtime",
        "registration_id": "flecs.component.key_entity"
      },
      {
        "component_id": "LaggedCommand",
        "plugin_id": "builtin.core_runtime",
        "registration_id": "flecs.component.lagged_command"
      },
      {
        "component_id": "LandingGear",
        "plugin_id": "builtin.core_runtime",
        "registration_id": "flecs.component.landing_gear"
      },
      {
        "component_id": "LeaderIntent",
        "plugin_id": "builtin.core_runtime",
        "registration_id": "flecs.component.leader_intent"
      },
      {
        "component_id": "Lifetime",
        "plugin_id": "builtin.core_runtime",
        "registration_id": "flecs.component.lifetime"
      },
      {
        "component_id": "Loadout",
        "plugin_id": "builtin.core_runtime",
        "registration_id": "flecs.component.loadout"
      },
      {
        "component_id": "LogisticsNode",
        "plugin_id": "builtin.core_runtime",
        "registration_id": "flecs.component.logistics_node"
      },
      {
        "component_id": "Mass",
        "plugin_id": "builtin.core_runtime",
        "registration_id": "flecs.component.mass"
      },
      {
        "component_id": "MassProperties",
        "plugin_id": "builtin.core_runtime",
        "registration_id": "flecs.component.mass_properties"
    )EFJSON",
    R"EFJSON(  },
      {
        "component_id": "Missile",
        "plugin_id": "builtin.core_runtime",
        "registration_id": "flecs.component.missile"
      },
      {
        "component_id": "MissionCommand",
        "plugin_id": "builtin.core_runtime",
        "registration_id": "flecs.component.mission_command"
      },
      {
        "component_id": "MissionCommandControlState",
        "plugin_id": "builtin.core_runtime",
        "registration_id": "flecs.component.mission_command_control_state"
      },
      {
        "component_id": "MissionCommandPendingQueue",
        "plugin_id": "builtin.core_runtime",
        "registration_id": "flecs.component.mission_command_pending_queue"
      },
      {
        "component_id": "MountedSensors",
        "plugin_id": "builtin.core_runtime",
        "registration_id": "flecs.component.mounted_sensors"
      },
      {
        "component_id": "MountedSonars",
        "plugin_id": "builtin.core_runtime",
        "registration_id": "flecs.component.mounted_sonars"
      },
      {
        "component_id": "MovementCommand",
        "plugin_id": "builtin.core_runtime",
        "registration_id": "flecs.component.movement_command"
      },
      {
        "component_id": "Munition",
        "plugin_id": "builtin.core_runtime",
        "registration_id": "flecs.component.munition"
      },
      {
        "component_id": "NavalStores",
        "plugin_id": "builtin.core_runtime",
        "registration_id": "flecs.component.naval_stores"
      },
      {
        "component_id": "NavalWeaponSystem",
        "plugin_id": "builtin.core_runtime",
        "registration_id": "flecs.component.naval_weapon_system"
      },
      {
        "component_id": "PendingActionCommand",
        "plugin_id": "builtin.core_runtime",
        "registration_id": "flecs.component.pending_action_command"
      },
      {
        "component_id": "PendingMissionCommand",
        "plugin_id": "builtin.core_runtime",
        "registration_id": "flecs.component.pending_mission_command"
      },
      {
        "component_id": "PendingMovementCommand",
        "plugin_id": "builtin.core_runtime",
        "registration_id": "flecs.component.pending_movement_command"
      },
      {
        "component_id": "PilotAction",
        "plugin_id": "builtin.core_runtime",
        "registration_id": "flecs.component.pilot_action"
      },
      {
        "component_id": "PilotReport",
        "plugin_id": "builtin.core_runtime",
        "registration_id": "flecs.component.pilot_report"
      },
      {
        "component_id": "PilotWeaponReleaseState",
        "plugin_id": "builtin.core_runtime",
        "registration_id": "flecs.component.pilot_weapon_release_state"
      },
      {
        "component_id": "PlatformDamageState",
        "plugin_id": "builtin.core_runtime",
        "registration_id": "flecs.component.platform_damage_state"
      },
      {
        "component_id": "Propulsion",
        "plugin_id": "builtin.core_runtime",
        "registration_id": "flecs.component.propulsion"
      },
      {
        "component_id": "RCSProfile",
        "plugin_id": "builtin.core_runtime",
        "registration_id": "flecs.component.rcsprofile"
      },
      {
        "component_id": "RWR",
        "plugin_id": "builtin.core_runtime",
        "registration_id": "flecs.component.rwr"
      },
      {
        "component_id": "ResupplyState",
        "plugin_id": "builtin.core_runtime",
        "registration_id": "flecs.component.resupply_state"
      },
      {
        "component_id": "Score",
        "plugin_id": "builtin.core_runtime",
        "registration_id": "flecs.component.score"
      },
      {
        "component_id": "Sensor",
        "plugin_id": "builtin.core_runtime",
        "registration_id": "flecs.component.sensor"
      },
      {
        "component_id": "SensorModelRef",
        "plugin_id": "builtin.core_runtime",
        "registration_id": "flecs.component.sensor_model_ref"
      },
      {
        "component_id": "ShipPlatform",
        "plugin_id": "builtin.core_runtime",
        "registration_id": "flecs.component.ship_platform"
      },
      {
        "component_id": "Sonar",
        "plugin_id": "builtin.core_runtime",
        "registration_id": "flecs.component.sonar"
      },
      {
        "component_id": "StallState",
        "plugin_id": "builtin.core_runtime",
        "registration_id": "flecs.component.stall_state"
      },
      {
        "component_id": "StructuralBreakupState",
        "plugin_id": "builtin.core_runtime",
        "registration_id": "flecs.component.structural_breakup_state"
      },
      {
        "component_id": "SubmarinePlatform",
        "plugin_id": "builtin.core_runtime",
        "registration_id": "flecs.component.submarine_platform"
      },
      {
        "component_id": "SystemHealth",
        "plugin_id": "builtin.core_runtime",
        "registration_id": "flecs.component.system_health"
      },
      {
        "component_id": "TaskOrder",
        "plugin_id": "builtin.core_runtime",
        "registration_id": "flecs.component.task_order"
      },
      {
        "component_id": "TrackDatabase",
        "plugin_id": "builtin.core_runtime",
        "registration_id": "flecs.component.track_database"
      },
      {
        "component_id": "Transform",
        "plugin_id": "builtin.core_runtime",
        "registration_id": "flecs.component.transform"
      },
      {
        "component_id": "Velocity",
        "plugin_id": "builtin.core_runtime",
        "registration_id": "flecs.component.velocity"
      },
      {
        "component_id": "WeaponCooldown",
        "plugin_id": "builtin.core_runtime",
        "registration_id": "flecs.component.weapon_cooldown"
      },
      {
        "component_id": "WeaponReleaseServiceRef",
        "plugin_id": "builtin.core_runtime",
        "registration_id": "flecs.component.weapon_release_service_ref"
      }
    ],
    "composition_id": "builtin.default_compatibility",
    "contract_versions": {
      "composition": "1.0.0",
      "content": "1.0.0",
      "runtime": "1.0.0",
      "stage": "1.0.0"
    },
    "evidence_policy": {
      "canonicalization": "echelon_forge.sorted_utf8_json.v1",
      "hash_algorithm": "sha256",
      "include_graph_hash": true,
      "include_provider_versions": true,
      "include_scope_generations": true
    },
    "plugins": [
      {
        "artifact": {
          "identity": "echelon-forge-source-tree",
          "kind": "repository_builtin",
          "sha256": null
        },
        "composition_contract_range": ">=1.0.0 <2.0.0",
        "configuration": {},
        "conflicts": [],
        "determinism_class": "truth_affecting_deterministic",
        "host_support": [
          "native"
        ],
        "implementation_id": "echelon_forge.native_builtin",
        "plugin_id": "builtin.core_runtime",
        "plugin_version": "1.0.0",
        "required_capabilities": []
      }
    ],
    "providers": [
      {
        "after_provider_ids": [],
        "cardinality": "one_per_scope",
        "configuration": {},
        "conflicts": [],
        "implementation_version": "1.0.0",
        "offered_services": [
          "simulation.acoustic.model"
        ],
        "plugin_id": "builtin.core_runtime",
        "provider_id": "builtin.acoustic.default",
        "required_capabilities": [],
        "required_services": [
          "simulation.environment.model"
        ],
        "restart_policy": "rebuild_scope_generation",
        "scope": "world",
        "teardown_policy": "reverse_dependency_order"
      },
      {
        "after_provider_ids": [],
        "cardinality": "one_per_scope",
        "configuration": {},
        "conflicts": [],
        "implementation_version": "1.0.0",
        "offered_services": [
          "runtime.world_batch_backend"
        ],
        "plugin_id": "builtin.core_runtime",
        "provider_id": "builtin.backend.flecs_cpu",
        "required_capabilities": [],
    )EFJSON",
    R"EFJSON(    "required_services": [],
        "restart_policy": "rebuild_scope_generation",
        "scope": "backend",
        "teardown_policy": "reverse_dependency_order"
      },
      {
        "after_provider_ids": [],
        "cardinality": "one_per_scope",
        "configuration": {},
        "conflicts": [],
        "implementation_version": "1.0.0",
        "offered_services": [
          "simulation.control.model"
        ],
        "plugin_id": "builtin.core_runtime",
        "provider_id": "builtin.control.default",
        "required_capabilities": [],
        "required_services": [
          "simulation.environment.model"
        ],
        "restart_policy": "rebuild_scope_generation",
        "scope": "world",
        "teardown_policy": "reverse_dependency_order"
      },
      {
        "after_provider_ids": [],
        "cardinality": "one_per_scope",
        "configuration": {},
        "conflicts": [],
        "implementation_version": "1.0.0",
        "offered_services": [
          "simulation.effects.model"
        ],
        "plugin_id": "builtin.core_runtime",
        "provider_id": "builtin.effects.default",
        "required_capabilities": [],
        "required_services": [],
        "restart_policy": "rebuild_scope_generation",
        "scope": "world",
        "teardown_policy": "reverse_dependency_order"
      },
      {
        "after_provider_ids": [],
        "cardinality": "one_per_scope",
        "configuration": {},
        "conflicts": [],
        "implementation_version": "1.0.0",
        "offered_services": [
          "runtime.engagement_event_recorder",
          "runtime.engagement_event_store"
        ],
        "plugin_id": "builtin.core_runtime",
        "provider_id": "builtin.engagement_event_store",
        "required_capabilities": [],
        "required_services": [],
        "restart_policy": "rebuild_scope_generation",
        "scope": "world",
        "teardown_policy": "reverse_dependency_order"
      },
      {
        "after_provider_ids": [],
        "cardinality": "one_per_scope",
        "configuration": {},
        "conflicts": [],
        "implementation_version": "1.0.0",
        "offered_services": [
          "simulation.environment.model"
        ],
        "plugin_id": "builtin.core_runtime",
        "provider_id": "builtin.environment.default",
        "required_capabilities": [],
        "required_services": [],
        "restart_policy": "rebuild_scope_generation",
        "scope": "world",
        "teardown_policy": "reverse_dependency_order"
      },
      {
        "after_provider_ids": [],
        "cardinality": "one_per_scope",
        "configuration": {},
        "conflicts": [],
        "implementation_version": "1.0.0",
        "offered_services": [
          "simulation.guidance.model"
        ],
        "plugin_id": "builtin.core_runtime",
        "provider_id": "builtin.guidance.default",
        "required_capabilities": [],
        "required_services": [
          "runtime.engagement_event_recorder",
          "simulation.environment.model"
        ],
        "restart_policy": "rebuild_scope_generation",
        "scope": "world",
        "teardown_policy": "reverse_dependency_order"
      },
      {
        "after_provider_ids": [],
        "cardinality": "one_per_scope",
        "configuration": {},
        "conflicts": [],
        "implementation_version": "1.0.0",
        "offered_services": [
          "simulation.sensor.model"
        ],
        "plugin_id": "builtin.core_runtime",
        "provider_id": "builtin.sensor.default",
        "required_capabilities": [],
        "required_services": [
          "simulation.environment.model"
        ],
        "restart_policy": "rebuild_scope_generation",
        "scope": "world",
        "teardown_policy": "reverse_dependency_order"
      },
      {
        "after_provider_ids": [],
        "cardinality": "one_per_scope",
        "configuration": {},
        "conflicts": [],
        "implementation_version": "1.0.0",
        "offered_services": [
          "simulation.unit_factory"
        ],
        "plugin_id": "builtin.core_runtime",
        "provider_id": "builtin.unit_factory.default",
        "required_capabilities": [],
        "required_services": [],
        "restart_policy": "rebuild_scope_generation",
        "scope": "world",
        "teardown_policy": "reverse_dependency_order"
      },
      {
        "after_provider_ids": [],
        "cardinality": "one_per_scope",
        "configuration": {},
        "conflicts": [],
        "implementation_version": "1.0.0",
        "offered_services": [
          "runtime.weapon_release.damage_bridge"
        ],
        "plugin_id": "builtin.core_runtime",
        "provider_id": "builtin.weapon_release.damage_bridge",
        "required_capabilities": [],
        "required_services": [
          "simulation.effects.model"
        ],
        "restart_policy": "rebuild_scope_generation",
        "scope": "world",
        "teardown_policy": "reverse_dependency_order"
      },
      {
        "after_provider_ids": [],
        "cardinality": "one_per_scope",
        "configuration": {},
        "conflicts": [],
        "implementation_version": "1.0.0",
        "offered_services": [
          "runtime.weapon_release.service"
        ],
        "plugin_id": "builtin.core_runtime",
        "provider_id": "builtin.weapon_release.service",
        "required_capabilities": [],
        "required_services": [
          "runtime.engagement_event_store",
          "runtime.weapon_release.damage_bridge",
          "simulation.unit_factory"
        ],
        "restart_policy": "rebuild_scope_generation",
        "scope": "world",
        "teardown_policy": "reverse_dependency_order"
      }
    ],
    "reconfiguration_policy": {
      "active_episode_change": "forbidden",
      "allowed_barriers": [
        "episode_end",
        "pre_run",
        "world_rebuild"
      ],
      "truth_affecting_change": "rebuild_scope_generation"
    },
    "requested_profile": {
      "profile_id": "builtin.default_compatibility",
      "profile_version": "1.0.0"
    },
    "schema_version": "echelon_forge.simulation_composition_manifest.v1",
    "scope_policies": [
      {
        "cardinality": "singleton",
        "parent_scope": null,
        "rebuild_trigger": "host_reconfiguration_or_shutdown",
        "scope": "application"
      },
      {
        "cardinality": "singleton",
        "parent_scope": "application",
        "rebuild_trigger": "backend_switch_or_failure",
        "scope": "backend"
      },
      {
        "cardinality": "one_per_parent",
        "parent_scope": "backend",
        "rebuild_trigger": "batch_resize_or_reconfiguration",
        "scope": "batch"
      },
      {
        "cardinality": "one_per_parent",
        "parent_scope": "batch",
        "rebuild_trigger": "world_replacement_or_composition_change",
        "scope": "world"
      },
      {
        "cardinality": "one_per_parent",
        "parent_scope": "world",
        "rebuild_trigger": "reset_or_episode_completion",
        "scope": "episode"
      }
    ],
    "service_bindings": [
      {
        "consumer_id": "builtin.acoustic.default",
        "consumer_kind": "provider",
        "provider_id": "builtin.environment.default",
        "service_key": "simulation.environment.model"
      },
      {
        "consumer_id": "builtin.control.default",
        "consumer_kind": "provider",
        "provider_id": "builtin.environment.default",
        "service_key": "simulation.environment.model"
      },
      {
        "consumer_id": "builtin.guidance.default",
        "consumer_kind": "provider",
        "provider_id": "builtin.engagement_event_store",
        "service_key": "runtime.engagement_event_recorder"
      },
      {
        "consumer_id": "builtin.guidance.default",
        "consumer_kind": "provider",
        "provider_id": "builtin.environment.default",
        "service_key": "simulation.environment.model"
    )EFJSON",
    R"EFJSON(  },
      {
        "consumer_id": "builtin.sensor.default",
        "consumer_kind": "provider",
        "provider_id": "builtin.environment.default",
        "service_key": "simulation.environment.model"
      },
      {
        "consumer_id": "builtin.weapon_release.damage_bridge",
        "consumer_kind": "provider",
        "provider_id": "builtin.effects.default",
        "service_key": "simulation.effects.model"
      },
      {
        "consumer_id": "builtin.weapon_release.service",
        "consumer_kind": "provider",
        "provider_id": "builtin.engagement_event_store",
        "service_key": "runtime.engagement_event_store"
      },
      {
        "consumer_id": "builtin.weapon_release.service",
        "consumer_kind": "provider",
        "provider_id": "builtin.weapon_release.damage_bridge",
        "service_key": "runtime.weapon_release.damage_bridge"
      },
      {
        "consumer_id": "builtin.weapon_release.service",
        "consumer_kind": "provider",
        "provider_id": "builtin.unit_factory.default",
        "service_key": "simulation.unit_factory"
      },
      {
        "consumer_id": "builtin.system.aero_state",
        "consumer_kind": "system",
        "provider_id": "builtin.environment.default",
        "service_key": "simulation.environment.model"
      },
      {
        "consumer_id": "builtin.system.aerodynamics",
        "consumer_kind": "system",
        "provider_id": "builtin.environment.default",
        "service_key": "simulation.environment.model"
      },
      {
        "consumer_id": "builtin.system.control",
        "consumer_kind": "system",
        "provider_id": "builtin.control.default",
        "service_key": "simulation.control.model"
      },
      {
        "consumer_id": "builtin.system.damage_common",
        "consumer_kind": "system",
        "provider_id": "builtin.effects.default",
        "service_key": "simulation.effects.model"
      },
      {
        "consumer_id": "builtin.system.ground_contact",
        "consumer_kind": "system",
        "provider_id": "builtin.environment.default",
        "service_key": "simulation.environment.model"
      },
      {
        "consumer_id": "builtin.system.guidance",
        "consumer_kind": "system",
        "provider_id": "builtin.guidance.default",
        "service_key": "simulation.guidance.model"
      },
      {
        "consumer_id": "builtin.system.naval_weapon_release",
        "consumer_kind": "system",
        "provider_id": "builtin.weapon_release.service",
        "service_key": "runtime.weapon_release.service"
      },
      {
        "consumer_id": "builtin.system.pilot_weapon_release",
        "consumer_kind": "system",
        "provider_id": "builtin.weapon_release.service",
        "service_key": "runtime.weapon_release.service"
      },
      {
        "consumer_id": "builtin.system.propulsion",
        "consumer_kind": "system",
        "provider_id": "builtin.environment.default",
        "service_key": "simulation.environment.model"
      },
      {
        "consumer_id": "builtin.system.sensor",
        "consumer_kind": "system",
        "provider_id": "builtin.sensor.default",
        "service_key": "simulation.sensor.model"
      },
      {
        "consumer_id": "builtin.system.ship_motion",
        "consumer_kind": "system",
        "provider_id": "builtin.environment.default",
        "service_key": "simulation.environment.model"
      },
      {
        "consumer_id": "builtin.system.sonar",
        "consumer_kind": "system",
        "provider_id": "builtin.acoustic.default",
        "service_key": "simulation.acoustic.model"
      }
    ],
    "system_contributions": [
      {
        "after": [
          "builtin.system.command_link"
        ],
        "before": [],
        "conflicts": [],
        "contribution_id": "builtin.system.action_mapping",
        "domain": "common",
        "executable_node_ids": [
          "ActionMapping"
        ],
        "plugin_id": "builtin.core_runtime",
        "provided_components": [],
        "read_state_shards": [],
        "registration_factory_id": "register_action_mapping_system",
        "required_barriers": [],
        "required_capabilities": [],
        "required_components": [],
        "required_services": [],
        "semantic_stage_ids": [],
        "write_state_shards": []
      },
      {
        "after": [
          "builtin.system.force"
        ],
        "before": [],
        "conflicts": [],
        "contribution_id": "builtin.system.actuator",
        "domain": "air",
        "executable_node_ids": [
          "AdvanceControlSurfaces"
        ],
        "plugin_id": "builtin.core_runtime",
        "provided_components": [],
        "read_state_shards": [],
        "registration_factory_id": "flight_dynamics.register_actuator_system",
        "required_barriers": [],
        "required_capabilities": [],
        "required_components": [],
        "required_services": [],
        "semantic_stage_ids": [],
        "write_state_shards": []
      },
      {
        "after": [
          "builtin.system.force_clear"
        ],
        "before": [],
        "conflicts": [],
        "contribution_id": "builtin.system.aero_state",
        "domain": "air",
        "executable_node_ids": [
          "ComputeAeroState"
        ],
        "plugin_id": "builtin.core_runtime",
        "provided_components": [],
        "read_state_shards": [],
        "registration_factory_id": "register_aero_state_system",
        "required_barriers": [],
        "required_capabilities": [],
        "required_components": [],
        "required_services": [
          "simulation.environment.model"
        ],
        "semantic_stage_ids": [],
        "write_state_shards": []
      },
      {
        "after": [
          "builtin.system.actuator"
        ],
        "before": [],
        "conflicts": [],
        "contribution_id": "builtin.system.aerodynamics",
        "domain": "air",
        "executable_node_ids": [
          "ComputeAerodynamics"
        ],
        "plugin_id": "builtin.core_runtime",
        "provided_components": [],
        "read_state_shards": [],
        "registration_factory_id": "register_aerodynamics_system",
        "required_barriers": [],
        "required_capabilities": [],
        "required_components": [],
        "required_services": [
          "simulation.environment.model"
        ],
        "semantic_stage_ids": [],
        "write_state_shards": []
      },
      {
        "after": [
          "builtin.system.damage_common"
        ],
        "before": [],
        "conflicts": [],
        "contribution_id": "builtin.system.aircraft_damage",
        "domain": "air",
        "executable_node_ids": [],
        "plugin_id": "builtin.core_runtime",
        "provided_components": [],
        "read_state_shards": [],
        "registration_factory_id": "register_aircraft_damage_system",
        "required_barriers": [],
        "required_capabilities": [],
        "required_components": [],
        "required_services": [],
        "semantic_stage_ids": [],
        "write_state_shards": []
      },
      {
        "after": [
          "builtin.system.action_mapping"
        ],
        "before": [],
        "conflicts": [],
        "contribution_id": "builtin.system.command_lag",
        "domain": "common",
        "executable_node_ids": [
          "CommandLag"
        ],
        "plugin_id": "builtin.core_runtime",
        "provided_components": [],
        "read_state_shards": [],
        "registration_factory_id": "register_command_lag_system",
        "required_barriers": [],
        "required_capabilities": [],
        "required_components": [],
        "required_services": [],
        "semantic_stage_ids": [],
        "write_state_shards": []
      },
      {
        "after": [],
        "before": [],
        "conflicts": [],
        "contribution_id": "builtin.system.command_link",
        "domain": "common",
        "executable_node_ids": [
        )EFJSON",
    R"EFJSON(  "CommandLinkAction",
          "CommandLinkMission",
          "CommandLinkMovement"
        ],
        "plugin_id": "builtin.core_runtime",
        "provided_components": [],
        "read_state_shards": [],
        "registration_factory_id": "register_command_link_system",
        "required_barriers": [],
        "required_capabilities": [],
        "required_components": [],
        "required_services": [],
        "semantic_stage_ids": [],
        "write_state_shards": []
      },
      {
        "after": [
          "builtin.system.command_lag"
        ],
        "before": [],
        "conflicts": [],
        "contribution_id": "builtin.system.control",
        "domain": "air",
        "executable_node_ids": [
          "FlightControl"
        ],
        "plugin_id": "builtin.core_runtime",
        "provided_components": [],
        "read_state_shards": [],
        "registration_factory_id": "register_control_system",
        "required_barriers": [],
        "required_capabilities": [],
        "required_components": [],
        "required_services": [
          "simulation.control.model"
        ],
        "semantic_stage_ids": [],
        "write_state_shards": []
      },
      {
        "after": [
          "builtin.system.instrument"
        ],
        "before": [],
        "conflicts": [],
        "contribution_id": "builtin.system.damage_common",
        "domain": "common",
        "executable_node_ids": [],
        "plugin_id": "builtin.core_runtime",
        "provided_components": [],
        "read_state_shards": [],
        "registration_factory_id": "register_damage_system_common",
        "required_barriers": [],
        "required_capabilities": [],
        "required_components": [],
        "required_services": [
          "simulation.effects.model"
        ],
        "semantic_stage_ids": [],
        "write_state_shards": []
      },
      {
        "after": [
          "builtin.system.track_manager"
        ],
        "before": [],
        "conflicts": [],
        "contribution_id": "builtin.system.data_link",
        "domain": "common",
        "executable_node_ids": [
          "DataLinkFusionSystem"
        ],
        "plugin_id": "builtin.core_runtime",
        "provided_components": [],
        "read_state_shards": [],
        "registration_factory_id": "register_data_link_system",
        "required_barriers": [],
        "required_capabilities": [],
        "required_components": [],
        "required_services": [],
        "semantic_stage_ids": [],
        "write_state_shards": []
      },
      {
        "after": [
          "builtin.system.data_link"
        ],
        "before": [],
        "conflicts": [],
        "contribution_id": "builtin.system.embarked_air_ops",
        "domain": "naval",
        "executable_node_ids": [],
        "plugin_id": "builtin.core_runtime",
        "provided_components": [],
        "read_state_shards": [],
        "registration_factory_id": "register_embarked_air_ops_system",
        "required_barriers": [],
        "required_capabilities": [],
        "required_components": [],
        "required_services": [],
        "semantic_stage_ids": [],
        "write_state_shards": []
      },
      {
        "after": [
          "builtin.system.ground_damage"
        ],
        "before": [],
        "conflicts": [],
        "contribution_id": "builtin.system.ew",
        "domain": "cross_domain",
        "executable_node_ids": [
          "EW_Lifetime_Manager",
          "EW_Release_Chaff",
          "EW_Release_Flare"
        ],
        "plugin_id": "builtin.core_runtime",
        "provided_components": [],
        "read_state_shards": [],
        "registration_factory_id": "register_ew_system",
        "required_barriers": [],
        "required_capabilities": [],
        "required_components": [],
        "required_services": [],
        "semantic_stage_ids": [],
        "write_state_shards": []
      },
      {
        "after": [
          "builtin.system.propulsion"
        ],
        "before": [],
        "conflicts": [],
        "contribution_id": "builtin.system.force",
        "domain": "air",
        "executable_node_ids": [
          "ComputeForces"
        ],
        "plugin_id": "builtin.core_runtime",
        "provided_components": [],
        "read_state_shards": [],
        "registration_factory_id": "register_force_system",
        "required_barriers": [],
        "required_capabilities": [],
        "required_components": [],
        "required_services": [],
        "semantic_stage_ids": [],
        "write_state_shards": []
      },
      {
        "after": [
          "builtin.system.control"
        ],
        "before": [],
        "conflicts": [],
        "contribution_id": "builtin.system.force_clear",
        "domain": "air",
        "executable_node_ids": [
          "ClearForces"
        ],
        "plugin_id": "builtin.core_runtime",
        "provided_components": [],
        "read_state_shards": [],
        "registration_factory_id": "register_force_clear_system",
        "required_barriers": [],
        "required_capabilities": [],
        "required_components": [],
        "required_services": [],
        "semantic_stage_ids": [],
        "write_state_shards": []
      },
      {
        "after": [
          "builtin.system.aerodynamics"
        ],
        "before": [],
        "conflicts": [],
        "contribution_id": "builtin.system.ground_contact",
        "domain": "ground",
        "executable_node_ids": [
          "GroundContact"
        ],
        "plugin_id": "builtin.core_runtime",
        "provided_components": [],
        "read_state_shards": [],
        "registration_factory_id": "register_ground_contact_system",
        "required_barriers": [],
        "required_capabilities": [],
        "required_components": [],
        "required_services": [
          "simulation.environment.model"
        ],
        "semantic_stage_ids": [],
        "write_state_shards": []
      },
      {
        "after": [
          "builtin.system.naval_damage"
        ],
        "before": [],
        "conflicts": [],
        "contribution_id": "builtin.system.ground_damage",
        "domain": "ground",
        "executable_node_ids": [],
        "plugin_id": "builtin.core_runtime",
        "provided_components": [],
        "read_state_shards": [],
        "registration_factory_id": "register_ground_damage_system",
        "required_barriers": [],
        "required_capabilities": [],
        "required_components": [],
        "required_services": [],
        "semantic_stage_ids": [],
        "write_state_shards": []
      },
      {
        "after": [
          "builtin.system.rotational_integration"
        ],
        "before": [],
        "conflicts": [],
        "contribution_id": "builtin.system.guidance",
        "domain": "cross_domain",
        "executable_node_ids": [
          "MissileGuidance"
        ],
        "plugin_id": "builtin.core_runtime",
        "provided_components": [],
        "read_state_shards": [],
        "registration_factory_id": "register_guidance_system",
        "required_barriers": [],
        "required_capabilities": [],
        "required_components": [],
        "required_services": [
          "simulation.guidance.model"
        ],
        "semantic_stage_ids": [],
        "write_state_shards": []
      },
      {
        "after": [
          "builtin.system.naval_weapon_release"
        ],
        "before": [],
        "conflicts": [],
        "contribution_id": "builtin.system.instrument",
        "domain": "common",
        "executable_node_ids": [
          "UpdateInstruments"
        ],
        "plugin_id": "builtin.core_runtime",
        "provided_components": [],
        "read_state_shards": [],
        "registration_factory_id": "register_instrument_system",
        "required_barriers": [],
        "required_capabilities": [],
        "required_components": [],
        "required_services": [],
        "semantic_stage_ids": [],
   )EFJSON",
    R"EFJSON(     "write_state_shards": []
      },
      {
        "after": [
          "builtin.system.guidance"
        ],
        "before": [],
        "conflicts": [],
        "contribution_id": "builtin.system.leapfrog_integration",
        "domain": "common",
        "executable_node_ids": [
          "LeapfrogIntegrate"
        ],
        "plugin_id": "builtin.core_runtime",
        "provided_components": [],
        "read_state_shards": [],
        "registration_factory_id": "register_leapfrog_integration_system",
        "required_barriers": [],
        "required_capabilities": [],
        "required_components": [],
        "required_services": [],
        "semantic_stage_ids": [],
        "write_state_shards": []
      },
      {
        "after": [
          "builtin.system.ew"
        ],
        "before": [],
        "conflicts": [],
        "contribution_id": "builtin.system.logistics",
        "domain": "common",
        "executable_node_ids": [
          "FuelConsumption",
          "LogisticsAction",
          "MassUpdate",
          "ResupplyLogic"
        ],
        "plugin_id": "builtin.core_runtime",
        "provided_components": [],
        "read_state_shards": [],
        "registration_factory_id": "register_logistics_system",
        "required_barriers": [],
        "required_capabilities": [],
        "required_components": [],
        "required_services": [],
        "semantic_stage_ids": [],
        "write_state_shards": []
      },
      {
        "after": [
          "builtin.system.structural_consequence"
        ],
        "before": [],
        "conflicts": [],
        "contribution_id": "builtin.system.naval_damage",
        "domain": "naval",
        "executable_node_ids": [],
        "plugin_id": "builtin.core_runtime",
        "provided_components": [],
        "read_state_shards": [],
        "registration_factory_id": "register_naval_damage_system",
        "required_barriers": [],
        "required_capabilities": [],
        "required_components": [],
        "required_services": [],
        "semantic_stage_ids": [],
        "write_state_shards": []
      },
      {
        "after": [
          "builtin.system.logistics"
        ],
        "before": [],
        "conflicts": [],
        "contribution_id": "builtin.system.naval_logistics",
        "domain": "naval",
        "executable_node_ids": [],
        "plugin_id": "builtin.core_runtime",
        "provided_components": [],
        "read_state_shards": [],
        "registration_factory_id": "register_naval_logistics_system",
        "required_barriers": [],
        "required_capabilities": [],
        "required_components": [],
        "required_services": [],
        "semantic_stage_ids": [],
        "write_state_shards": []
      },
      {
        "after": [
          "builtin.system.pilot_weapon_release"
        ],
        "before": [],
        "conflicts": [],
        "contribution_id": "builtin.system.naval_weapon_release",
        "domain": "naval",
        "executable_node_ids": [],
        "plugin_id": "builtin.core_runtime",
        "provided_components": [],
        "read_state_shards": [],
        "registration_factory_id": "register_naval_mission_weapon_release_system",
        "required_barriers": [],
        "required_capabilities": [],
        "required_components": [],
        "required_services": [
          "runtime.weapon_release.service"
        ],
        "semantic_stage_ids": [],
        "write_state_shards": []
      },
      {
        "after": [
          "builtin.system.submarine_motion"
        ],
        "before": [],
        "conflicts": [],
        "contribution_id": "builtin.system.navigation",
        "domain": "common",
        "executable_node_ids": [
          "NavigationSystem"
        ],
        "plugin_id": "builtin.core_runtime",
        "provided_components": [],
        "read_state_shards": [],
        "registration_factory_id": "register_navigation_system",
        "required_barriers": [],
        "required_capabilities": [],
        "required_components": [],
        "required_services": [],
        "semantic_stage_ids": [],
        "write_state_shards": []
      },
      {
        "after": [
          "builtin.system.embarked_air_ops"
        ],
        "before": [],
        "conflicts": [],
        "contribution_id": "builtin.system.pilot_weapon_release",
        "domain": "air",
        "executable_node_ids": [],
        "plugin_id": "builtin.core_runtime",
        "provided_components": [],
        "read_state_shards": [],
        "registration_factory_id": "register_pilot_weapon_release_system",
        "required_barriers": [],
        "required_capabilities": [],
        "required_components": [],
        "required_services": [
          "runtime.weapon_release.service"
        ],
        "semantic_stage_ids": [],
        "write_state_shards": []
      },
      {
        "after": [
          "builtin.system.aero_state"
        ],
        "before": [],
        "conflicts": [],
        "contribution_id": "builtin.system.propulsion",
        "domain": "air",
        "executable_node_ids": [
          "ComputePropulsion"
        ],
        "plugin_id": "builtin.core_runtime",
        "provided_components": [],
        "read_state_shards": [],
        "registration_factory_id": "flight_dynamics.register_propulsion_system",
        "required_barriers": [],
        "required_capabilities": [],
        "required_components": [],
        "required_services": [
          "simulation.environment.model"
        ],
        "semantic_stage_ids": [],
        "write_state_shards": []
      },
      {
        "after": [
          "builtin.system.ground_contact"
        ],
        "before": [],
        "conflicts": [],
        "contribution_id": "builtin.system.rotational_integration",
        "domain": "air",
        "executable_node_ids": [
          "RotationalIntegrate"
        ],
        "plugin_id": "builtin.core_runtime",
        "provided_components": [],
        "read_state_shards": [],
        "registration_factory_id": "register_rotational_integration_system",
        "required_barriers": [],
        "required_capabilities": [],
        "required_components": [],
        "required_services": [],
        "semantic_stage_ids": [],
        "write_state_shards": []
      },
      {
        "after": [
          "builtin.system.navigation"
        ],
        "before": [],
        "conflicts": [],
        "contribution_id": "builtin.system.sensor",
        "domain": "cross_domain",
        "executable_node_ids": [
          "SensorSystem"
        ],
        "plugin_id": "builtin.core_runtime",
        "provided_components": [],
        "read_state_shards": [],
        "registration_factory_id": "register_sensor_system",
        "required_barriers": [],
        "required_capabilities": [],
        "required_components": [],
        "required_services": [
          "simulation.sensor.model"
        ],
        "semantic_stage_ids": [],
        "write_state_shards": []
      },
      {
        "after": [
          "builtin.system.leapfrog_integration"
        ],
        "before": [],
        "conflicts": [],
        "contribution_id": "builtin.system.ship_motion",
        "domain": "naval",
        "executable_node_ids": [],
        "plugin_id": "builtin.core_runtime",
        "provided_components": [],
        "read_state_shards": [],
        "registration_factory_id": "register_ship_motion_system",
        "required_barriers": [],
        "required_capabilities": [],
        "required_components": [],
        "required_services": [
          "simulation.environment.model"
        ],
        "semantic_stage_ids": [],
        "write_state_shards": []
      },
      {
        "after": [
          "builtin.system.sensor"
        ],
        "before": [],
        "conflicts": [],
        "contribution_id": "builtin.system.sonar",
        "domain": "naval",
        "executable_node_ids": [],
        "plugin_id": "builtin.core_runtime",
        ")EFJSON",
    R"EFJSON(provided_components": [],
        "read_state_shards": [],
        "registration_factory_id": "register_sonar_system",
        "required_barriers": [],
        "required_capabilities": [],
        "required_components": [],
        "required_services": [
          "simulation.acoustic.model"
        ],
        "semantic_stage_ids": [],
        "write_state_shards": []
      },
      {
        "after": [
          "builtin.system.structural_failure"
        ],
        "before": [],
        "conflicts": [],
        "contribution_id": "builtin.system.structural_consequence",
        "domain": "air",
        "executable_node_ids": [],
        "plugin_id": "builtin.core_runtime",
        "provided_components": [],
        "read_state_shards": [],
        "registration_factory_id": "register_structural_consequence_system",
        "required_barriers": [],
        "required_capabilities": [],
        "required_components": [],
        "required_services": [],
        "semantic_stage_ids": [],
        "write_state_shards": []
      },
      {
        "after": [
          "builtin.system.aircraft_damage"
        ],
        "before": [],
        "conflicts": [],
        "contribution_id": "builtin.system.structural_failure",
        "domain": "air",
        "executable_node_ids": [],
        "plugin_id": "builtin.core_runtime",
        "provided_components": [],
        "read_state_shards": [],
        "registration_factory_id": "register_structural_failure_system",
        "required_barriers": [],
        "required_capabilities": [],
        "required_components": [],
        "required_services": [],
        "semantic_stage_ids": [],
        "write_state_shards": []
      },
      {
        "after": [
          "builtin.system.ship_motion"
        ],
        "before": [],
        "conflicts": [],
        "contribution_id": "builtin.system.submarine_motion",
        "domain": "naval",
        "executable_node_ids": [],
        "plugin_id": "builtin.core_runtime",
        "provided_components": [],
        "read_state_shards": [],
        "registration_factory_id": "register_submarine_motion_system",
        "required_barriers": [],
        "required_capabilities": [],
        "required_components": [],
        "required_services": [],
        "semantic_stage_ids": [],
        "write_state_shards": []
      },
      {
        "after": [
          "builtin.system.sonar"
        ],
        "before": [],
        "conflicts": [],
        "contribution_id": "builtin.system.track_manager",
        "domain": "common",
        "executable_node_ids": [],
        "plugin_id": "builtin.core_runtime",
        "provided_components": [],
        "read_state_shards": [],
        "registration_factory_id": "register_track_manager_system",
        "required_barriers": [],
        "required_capabilities": [],
        "required_components": [],
        "required_services": [],
        "semantic_stage_ids": [],
        "write_state_shards": []
      }
    ]
  },
  "provider_construction_order": [
    "builtin.backend.flecs_cpu",
    "builtin.effects.default",
    "builtin.engagement_event_store",
    "builtin.environment.default",
    "builtin.acoustic.default",
    "builtin.control.default",
    "builtin.guidance.default",
    "builtin.sensor.default",
    "builtin.unit_factory.default",
    "builtin.weapon_release.damage_bridge",
    "builtin.weapon_release.service"
  ],
  "requested_manifest_sha256": "c6581f81cc50b8f3ce155919a45737683c9a503645db59ef280cbcebac020c46",
  "resolved_manifest_sha256": "138e82a8a59fa4d3960da23f1c0acdda4e7a634f3a02e7f9268933c3a38bc7a5",
  "resolver_contract_version": "echelon_forge.simulation_composition_resolver.v1",
  "schema_version": "echelon_forge.resolved_simulation_composition.v1",
  "system_registration_order": [
    "builtin.system.command_link",
    "builtin.system.action_mapping",
    "builtin.system.command_lag",
    "builtin.system.control",
    "builtin.system.force_clear",
    "builtin.system.aero_state",
    "builtin.system.propulsion",
    "builtin.system.force",
    "builtin.system.actuator",
    "builtin.system.aerodynamics",
    "builtin.system.ground_contact",
    "builtin.system.rotational_integration",
    "builtin.system.guidance",
    "builtin.system.leapfrog_integration",
    "builtin.system.ship_motion",
    "builtin.system.submarine_motion",
    "builtin.system.navigation",
    "builtin.system.sensor",
    "builtin.system.sonar",
    "builtin.system.track_manager",
    "builtin.system.data_link",
    "builtin.system.embarked_air_ops",
    "builtin.system.pilot_weapon_release",
    "builtin.system.naval_weapon_release",
    "builtin.system.instrument",
    "builtin.system.damage_common",
    "builtin.system.aircraft_damage",
    "builtin.system.structural_failure",
    "builtin.system.structural_consequence",
    "builtin.system.naval_damage",
    "builtin.system.ground_damage",
    "builtin.system.ew",
    "builtin.system.logistics",
    "builtin.system.naval_logistics"
  ]
}
)EFJSON",
};

inline constexpr std::string_view kDefaultCompatibilityRequestedSha256 =
    "c6581f81cc50b8f3ce155919a45737683c9a503645db59ef280cbcebac020c46";
inline constexpr std::string_view kDefaultCompatibilityResolvedSha256 =
    "138e82a8a59fa4d3960da23f1c0acdda4e7a634f3a02e7f9268933c3a38bc7a5";

inline constexpr std::string_view kDefaultBackendProfileId = "cpu_exact.reference";
inline constexpr std::string_view kDefaultBackendProviderId = "builtin.backend.flecs_cpu";
inline constexpr std::string_view kDefaultBackendImplementationVersion = "1.0.0";
inline constexpr std::array<std::string_view, 1> kDefaultBackendRequiredCapabilities = {
    "runtime.cpu_exact",
};

} // namespace runtime::composition_contracts::generated
