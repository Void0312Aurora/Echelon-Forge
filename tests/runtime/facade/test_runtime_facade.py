from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

from python.testing.runtime import ensure_repo_imports
from python.testing.runtime import resolve_repo_path


ensure_repo_imports()

import ef_py  # noqa: E402
from python.scenario_compiler import ScenarioCompiler  # noqa: E402
from python.scenario_runtime import BatchWorldApplyBuffer  # noqa: E402
from python.scenario_runtime import active_roster_world_entity_refs  # noqa: E402
from python.scenario_runtime import find_active_roster_member  # noqa: E402
from python.scenario_runtime import load_compiled_scenario_batch  # noqa: E402
from python.scenario_runtime import resolve_active_controllable_roster  # noqa: E402


_RUNTIME_CAPABILITY_EXPECTATIONS = {
    "supports_batch_runtime": True,
    "supports_compiled_episode_controller": True,
    "supports_compiled_execution_step": True,
    "supports_gpu_visual": False,
    "supports_gpu_observation": False,
    "supports_gpu_flight_shaping": False,
    "supports_device_observation_view": False,
    "supports_resident_state": False,
    "supports_exact_gpu_backend": False,
    "supports_shadow_compare": False,
}

_RUNTIME_CAPABILITY_METADATA_EXPECTATIONS = {
    "maintained_baseline_backend_profile_id": "cpu_exact.reference",
    "maintained_baseline_parity_budget_ref": "parity_budget.cpu_exact.reference.v1",
    "maintained_baseline_profile_status": "maintained_exact_baseline",
    "device_observation_view_candidate_profile_id": "gpu_helpers.diagnostics_only",
    "device_observation_view_rejection_reason": (
        "gpu_helpers_diagnostics_only_is_not_a_maintained_device_observation_view_profile"
    ),
    "exact_gpu_backend_candidate_profile_id": "gpu_exact.unmaintained_candidate",
    "exact_gpu_backend_rejection_reason": "gpu_exact.unmaintained_candidate_is_not_maintained",
    "resident_state_candidate_profile_id": "resident_state.unmaintained_candidate",
    "resident_state_candidate_parity_budget_ref": (
        "parity_budget.resident_state.unmaintained_candidate.v1"
    ),
    "resident_state_rejection_reason": (
        "resident_state.unmaintained_candidate_is_not_maintained"
    ),
    "shadow_compare_candidate_profile_id": "shadow_compare.unmaintained_candidate",
    "shadow_compare_candidate_parity_budget_ref": (
        "parity_budget.shadow_compare.unmaintained_candidate.v1"
    ),
    "shadow_compare_rejection_reason": (
        "shadow_compare.unmaintained_candidate_is_not_maintained"
    ),
    "multi_fidelity_rejection_reason": (
        "multi_fidelity_profiles_require_a_maintained_registry_revision_and_acceptance_gate"
    ),
}

_RUNTIME_FIDELITY_PROVIDER_FAMILY_EXPECTATIONS = {
    "none": "none",
    "reference_cpu": "reference_cpu",
}


def _entity_ref(world_index: int, entity_id: int) -> ef_py.WorldEntityRef:
    ref = ef_py.WorldEntityRef()
    ref.world_index = int(world_index)
    ref.entity_id = int(entity_id)
    return ref


def _public_observations_for_entity_range(
    facade: ef_py.RuntimeFacade,
    world_index: int,
    start_entity_id: int,
    end_entity_id: int,
) -> list[ef_py.AgentObservation]:
    refs = [
        _entity_ref(world_index, entity_id)
        for entity_id in range(int(start_entity_id), int(end_entity_id))
    ]
    return list(facade.get_agent_observations_batch(refs))


def _has_public_observation_at(
    observations: list[ef_py.AgentObservation],
    *,
    x: float,
    y: float,
    z: float,
) -> bool:
    return any(
        abs(float(observation.x) - x) < 1e-6
        and abs(float(observation.y) - y) < 1e-6
        and abs(float(observation.z) - z) < 1e-6
        for observation in observations
    )


def _build_route_state(entity_id: int) -> ef_py.ExecutionEpisodeState:
    state = ef_py.ExecutionEpisodeState()
    state.agent_id = int(entity_id)
    state.has_mission_command = True
    state.mission_command.command_code = 3
    state.mission_command.cmd_heading_deg = 90.0
    state.mission_command.cmd_altitude_m = 1200.0
    state.mission_command.cmd_speed_mps = 180.0
    state.mission_command.active = True
    state.has_mission_command_json = True
    state.mission_command_json = json.dumps(
        {
            "command_code": 3,
            "route_ref_id": int(entity_id),
            "target_altitude": 1200.0,
            "target_heading": 90.0,
            "target_speed": 180.0,
            "waypoint_mode": "flyby",
            "waypoints": [
                {"x": -1350.0, "y": 0.0, "z": 1200.0, "radius_m": 1200.0},
            ],
        },
        ensure_ascii=True,
        sort_keys=True,
    )
    route_waypoint = ef_py.SpatialRouteWaypoint()
    route_waypoint.x_m = -1350.0
    route_waypoint.y_m = 0.0
    route_waypoint.z_m = 1200.0
    route_waypoint.radius_m = 1200.0
    route_waypoint.altitude_m = 1200.0
    route_waypoint.speed_mps = 180.0
    route_waypoint.waypoint_mode = "flyby"
    state.route_waypoints = [route_waypoint]
    state.has_post_waypoint_transition_json = True
    state.post_waypoint_transition_json = json.dumps(
        {
            "command_code": 2,
            "phase_name": "post_route",
            "target_altitude": 900.0,
            "target_heading": 45.0,
            "target_speed": 160.0,
            "transition_reward": 123.0,
        },
        ensure_ascii=True,
        sort_keys=True,
    )
    return state


def _build_route_request(entity_id: int) -> ef_py.WorldExecutionEpisodeStepRequest:
    request = ef_py.WorldExecutionEpisodeStepRequest()
    request.world_index = 0
    request.entity_id = int(entity_id)
    request.config = ef_py.StepEvaluationBatchConfig()
    request.env_state.steps = 1
    request.env_state.truth_x = -1400.0
    request.env_state.truth_y = 0.0
    request.env_state.truth_z = 1200.0
    request.env_state.truth_speed = 180.0
    request.env_state.has_safety = True
    request.env_state.safety.finite_state_valid = True
    request.env_state.safety.health = 100.0
    request.env_state.safety.survival_reward = 0.02
    request.env_state.has_waypoint = True
    request.env_state.waypoint.valid = True
    request.env_state.waypoint.waypoint_index = 0
    request.env_state.waypoint.waypoint_count = 1
    request.env_state.waypoint.dist_m = 50.0
    request.env_state.waypoint.waypoint_radius_m = 1200.0
    request.env_state.waypoint.has_prev_dist = True
    request.env_state.waypoint.prev_dist_m = 120.0
    request.env_state.waypoint.progress_weight = 0.1
    request.env_state.waypoint.distance_weight = -0.001
    request.env_state.waypoint.reached_bonus = 20.0
    return request


def _build_single_aircraft_setup(seed: int = 123) -> ef_py.BatchWorldSetupRequest:
    setup_request = ef_py.BatchWorldSetupRequest()
    setup_request.seeds = [int(seed)]
    terrain = ef_py.WorldTerrainAssignment()
    terrain.world_index = 0
    terrain.terrain_type = "legacy"
    wind = ef_py.WorldWindAssignment()
    wind.world_index = 0
    spawn = ef_py.WorldSpawnRequest()
    spawn.world_index = 0
    spawn.side = ef_py.Side.Blue
    spawn.type_name = "Aircraft"
    spawn.entity_name = "CounterfactualLead"
    spawn.is_agent = True
    spawn.x = -1400.0
    spawn.y = 0.0
    spawn.z = 1200.0
    spawn.heading = 90.0
    spawn.vy = 180.0
    setup_request.terrain_assignments = [terrain]
    setup_request.wind_assignments = [wind]
    setup_request.spawn_requests = [spawn]
    setup_request.time_steps = [0.05]
    return setup_request


def _build_reference_fidelity_request() -> ef_py.RuntimeFidelityRequest:
    request = ef_py.RuntimeFidelityRequest()
    request.request_label = "exact_evaluation"
    request.backend_profile_id = "cpu_exact.reference"
    request.parity_budget_ref = "parity_budget.cpu_exact.reference.v1"
    request.provider_family = "reference_cpu"
    request.model_family_scope = ["P0-P10 semantic lifecycle", "counterfactual_selected_slice"]
    request.validation_gate = "WP17-F selected counterfactual runtime slice"
    request.facade_evidence_refs = [
        "RuntimeFacade.admit_fidelity_request",
        "RuntimeFacade.run_counterfactual_branch",
    ]
    return request


def _make_typed_platform_spawn_request(
    *,
    world_index: int = 0,
    request_id: str = "typed-spawn:lead",
    source_type_name: str = "Aircraft",
    entity_name: str = "TypedLead",
) -> ef_py.TypedPlatformSpawnRequest:
    request = ef_py.TypedPlatformSpawnRequest()
    request.world_index = int(world_index)
    request.side = ef_py.Side.Blue
    request.request_id = request_id
    request.source_type_name = source_type_name
    request.entity_name = entity_name
    request.is_agent = True
    request.x = -1450.0
    request.y = 25.0
    request.z = 1200.0
    request.heading = 90.0
    request.vy = 180.0

    mobility = ef_py.PlatformCapability()
    mobility.capability_id = f"mobility:{source_type_name}"
    mobility.family = "mobility"
    mobility.capability_type = "fixed_wing_flight"
    mobility.implementation_ref = "DefaultUnitFactory"
    mobility.evidence_refs = [f"capability:{source_type_name}:mobility"]

    bundle = ef_py.CapabilityBundle()
    bundle.bundle_id = f"bundle:{source_type_name}"
    bundle.source_type_name = source_type_name
    bundle.capabilities = [mobility]
    bundle.template_evidence_ref = f"template:{source_type_name}"
    bundle.evidence_refs = [
        f"bundle:{source_type_name}:evidence",
        f"shared:{source_type_name}:evidence",
    ]
    bundle.compatibility_path_preserved = True
    request.capability_bundle = bundle

    plan = ef_py.ResolvedPlatformSpawnPlan()
    plan.plan_id = f"plan:{request_id}"
    plan.source_request_kind = "typed_platform_request"
    plan.source_type_name = source_type_name
    plan.capability_bundle_id = bundle.bundle_id
    plan.resolved_platform_definition_ref = f"definition:{source_type_name}"
    plan.materialization_strategy = "resolved_spawn_plan_bridge"
    plan.template_evidence_ref = bundle.template_evidence_ref
    plan.resolution_evidence_ref = f"resolution:{request_id}"
    plan.materialization_evidence_ref = f"materialization:{request_id}"
    plan.evidence_refs = [
        f"plan:{request_id}:evidence",
        f"shared:{source_type_name}:evidence",
    ]
    plan.resolved_capabilities = [mobility]
    plan.compatibility_path_preserved = True
    plan.admitted = True
    request.resolved_spawn_plan = plan
    request.facade_evidence_refs = [
        "BatchWorldSetupRequest.typed_platform_spawn_requests",
        f"facade:{request_id}",
    ]
    request.compatibility_path_preserved = True
    return request


def _build_counterfactual_branch_request() -> ef_py.RuntimeCounterfactualBranchRequest:
    request = ef_py.RuntimeCounterfactualBranchRequest()
    request.baseline_setup = _build_single_aircraft_setup()
    request.entity_ref = _entity_ref(0, 0)
    request.fidelity_request = _build_reference_fidelity_request()
    request.deterministic_seed = 123
    request.replay_envelope_id = "replay:wp17f:0001"
    request.branch_point_id = "branch_point:wp17f:0001"
    request.branch_worldline_id = "worldline:wp17f:branch"
    request.mutation_dx = 25.0
    request.mutation_dvy = 5.0
    request.mutation_dheading = 15.0
    request.evidence_refs = ["cadence:wp17c:selected_slice"]
    return request


def _repo_text(*parts: str) -> str:
    return Path(resolve_repo_path(*parts)).read_text(encoding="utf-8")


def _method_body(source: str, signature: str) -> str:
    start = source.index(signature)
    body_start = source.index("{", start)
    depth = 0
    for index in range(body_start, len(source)):
        char = source[index]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return source[body_start:index + 1]
    raise AssertionError(f"could not find method body for {signature}")


class RuntimeFacadeTests(unittest.TestCase):
    def test_runtime_facade_fidelity_admission_admits_reference_baseline(self) -> None:
        facade = ef_py.RuntimeFacade(1)
        request = ef_py.RuntimeFidelityRequest()
        request.request_label = "exact_evaluation"
        request.backend_profile_id = "cpu_exact.reference"
        request.parity_budget_ref = "parity_budget.cpu_exact.reference.v1"
        request.provider_family = "reference_cpu"
        request.model_family_scope = [
            "P0-P10 semantic lifecycle",
            "observation_packet",
            "diagnostics_trace",
        ]
        request.validation_gate = (
            "WP17-D facade-owned exact-evaluation baseline admission"
        )
        request.facade_evidence_refs = [
            "RuntimeFacade.capabilities",
            "RuntimeFacade.admit_fidelity_request",
        ]

        admission = facade.admit_fidelity_request(request)

        self.assertTrue(bool(admission.admitted))
        self.assertTrue(bool(admission.baseline_exact_evaluation))
        self.assertEqual(admission.requested_provider_family, "reference_cpu")
        self.assertEqual(admission.selected_provider_family, "reference_cpu")
        self.assertEqual(admission.selected_stage_node_id, "p10.observation_export.v1")
        self.assertEqual(admission.rejection_reason, "")
        self.assertIn("RuntimeFacade.capabilities", list(admission.evidence_refs))

    def test_runtime_facade_fidelity_admission_rejects_unmaintained_provider_families(self) -> None:
        facade = ef_py.RuntimeFacade(1)

        for provider_family, rejection in (
            ("gpu", "exact_gpu_fidelity_requires_maintained_backend_profile"),
            ("accelerated_exact", "exact_gpu_fidelity_requires_maintained_backend_profile"),
            ("resident_state", "resident_state_fidelity_requires_maintained_backend_profile"),
            ("shadow", "shadow_fidelity_requires_maintained_backend_profile"),
        ):
            request = ef_py.RuntimeFidelityRequest()
            request.request_label = "exact_evaluation"
            request.backend_profile_id = "cpu_exact.reference"
            request.parity_budget_ref = "parity_budget.cpu_exact.reference.v1"
            request.provider_family = provider_family
            request.model_family_scope = ["P0-P10 semantic lifecycle"]
            request.validation_gate = "WP17-D unsupported-provider fail-closed"
            request.facade_evidence_refs = ["RuntimeFacade.admit_fidelity_request"]

            admission = facade.admit_fidelity_request(request)

            self.assertFalse(bool(admission.admitted), msg=provider_family)
            self.assertEqual(admission.requested_provider_family, provider_family)
            self.assertEqual(admission.selected_provider_family, "none")
            self.assertEqual(admission.selected_stage_node_id, "")
            self.assertEqual(admission.rejection_reason, rejection)

    def test_runtime_facade_declares_engagement_packet_shell_types(self) -> None:
        header = _repo_text("src", "runtime", "facade", "runtime_facade_types.h")

        self.assertIn('#include "runtime/contracts/engagement_contracts.h"', header)
        self.assertIn("struct EngagementBatchRequest", header)
        self.assertIn("struct EngagementEventPacket", header)

        request_block = re.search(
            r"struct EngagementBatchRequest \{(?P<body>.*?)\};",
            header,
            flags=re.S,
        )
        self.assertIsNotNone(request_block)
        request_body = request_block.group("body")
        self.assertIn("std::vector<EngagementEntityRef> refs", request_body)
        self.assertIn("std::vector<std::uint64_t> trace_ids", request_body)
        for flag in [
            "include_track_packets",
            "include_launch_requests",
            "include_launch_events",
            "include_munition_lifecycle_packets",
            "include_effects_events",
            "include_damage_reports",
            "include_diagnostics_traces",
        ]:
            self.assertIn(flag, request_body)

        packet_block = re.search(
            r"struct EngagementEventPacket \{(?P<body>.*?)\};",
            header,
            flags=re.S,
        )
        self.assertIsNotNone(packet_block)
        packet_body = packet_block.group("body")
        for field in [
            "std::uint64_t snapshot_version",
            "std::string barrier_id",
            "std::uint64_t barrier_sequence",
            "std::string barrier_detail",
            "double source_time_s",
            "std::string producer_node_id",
            "InformationStateSource packet_provenance",
            "InformationStateSource diagnostics_provenance",
            "std::vector<EngagementEntityRef> refs",
            "std::vector<std::uint64_t> trace_ids",
            "std::vector<TrackPacket> track_packets",
            "std::vector<LaunchRequest> launch_requests",
            "std::vector<LaunchEvent> launch_events",
            "std::vector<MunitionLifecyclePacket> munition_lifecycle_packets",
            "std::vector<EffectsEvent> effects_events",
            "std::vector<DamageReport> damage_reports",
            "std::vector<DiagnosticsTrace> diagnostics_traces",
        ]:
            self.assertIn(field, packet_body)

        observation_block = re.search(
            r"struct ObservationBatchPacket \{(?P<body>.*?)\};",
            header,
            flags=re.S,
        )
        self.assertIsNotNone(observation_block)
        observation_body = observation_block.group("body")
        self.assertIn("InformationStateSource provenance", observation_body)

    def test_runtime_facade_exports_read_only_engagement_snapshot_without_weapon_escape(self) -> None:
        facade_header = _repo_text("src", "runtime", "facade", "runtime_facade.h")
        facade_source = _repo_text("src", "runtime", "facade", "runtime_facade.cpp")

        self.assertIn(
            "EngagementEventPacket export_engagement_event_packet("
            "const EngagementBatchRequest& request) const;",
            facade_header,
        )
        self.assertIn(
            "std::vector<DiagnosticsTrace> export_diagnostics_traces("
            "const EngagementBatchRequest& request) const;",
            facade_header,
        )

        body = _method_body(
            facade_source,
            "EngagementEventPacket RuntimeFacade::export_engagement_event_packet",
        )
        self.assertIn("EngagementEventPacket packet{}", body)
        self.assertIn("packet.refs = request.refs", body)
        self.assertIn("packet.trace_ids = request.trace_ids", body)
        self.assertIn("stable_sort_engagement_packet(&packet)", body)
        self.assertIn("apply_export_packet_metadata(", body)
        self.assertIn("finalize_recent_event_metadata(&packet)", body)
        self.assertIn("finalize_diagnostics_ancestry(&packet)", body)
        self.assertTrue(
            "get_agent_observations_batch" in body or "build_observation_packet" in body,
            "engagement export should read live AgentObservation contacts via the facade/runtime observation path",
        )
        self.assertIn("include_track_packets", body)
        self.assertIn("include_diagnostics_traces", body)
        self.assertIn("packet.track_packets.push_back", body)
        self.assertIn("packet.diagnostics_traces.push_back", body)
        self.assertIn("return packet", body)
        self.assertNotIn(".runtime(", body)
        self.assertNotIn("fire_missile", body)
        self.assertNotIn("fire_naval_weapon", body)
        for field in [
            "launch_requests",
            "launch_events",
            "munition_lifecycle_packets",
            "effects_events",
            "damage_reports",
        ]:
            self.assertNotIn(f"packet.{field}.push_back", body)
            self.assertNotIn(f"packet.{field} =", body)

    def test_runtime_facade_exports_dedicated_diagnostics_trace_surface(self) -> None:
        facade_source = _repo_text("src", "runtime", "facade", "runtime_facade.cpp")

        body = _method_body(
            facade_source,
            "std::vector<DiagnosticsTrace> RuntimeFacade::export_diagnostics_traces",
        )
        self.assertIn("std::vector<DiagnosticsTrace> traces", body)
        self.assertIn("append_recent_diagnostics_traces", body)
        self.assertIn("request.include_track_packets || request.include_diagnostics_traces", body)
        self.assertIn("runtime_->get_agent_observations_batch", body)
        self.assertIn("diagnostics_trace_from_track_packet", body)
        self.assertIn("stable_sort_diagnostics_traces(&traces)", body)
        self.assertNotIn("EngagementEventPacket packet{}", body)
        self.assertNotIn("fire_missile", body)
        self.assertNotIn("fire_naval_weapon", body)

    def test_resolve_active_controllable_roster_returns_active_members(self) -> None:
        scenario = {
            "scenario_name": "roster_resolution",
            "environment": {
                "time_step": 0.05,
                "terrain_type": "legacy",
                "wind": {"speed_mps": 0.0, "dir_from_deg": 0.0, "shear_mps_per_km": 0.0},
                "zones": [],
            },
            "mission_command": {
                "command_code": 2,
                "target_heading": 90.0,
                "target_altitude": 1200.0,
                "target_speed": 180.0,
            },
            "entities": [
                {"name": "Lead", "type": "Aircraft", "side": "Blue", "is_agent": True, "pos": [-1400.0, 0.0, 1200.0], "vel": [0.0, 180.0, 0.0], "heading": 90.0},
                {"name": "Wing", "type": "Aircraft", "side": "Blue", "is_agent": True, "pos": [-1550.0, -120.0, 1200.0], "vel": [0.0, 180.0, 0.0], "heading": 90.0},
            ],
            "cooperative_roster": {
                "team_id": 7001,
                "members": [
                    {
                        "entity": "Lead",
                        "role_code": 21,
                        "formation_role_id": "ElementLead",
                        "relative_slot_code": 11,
                        "policy_route": "shared_execution",
                    },
                    {
                        "entity": "Wing",
                        "role_code": 22,
                        "formation_role_id": "Wingman",
                        "relative_slot_code": 12,
                        "reference_entity": "Lead",
                        "policy_route": "shared_execution",
                    },
                ],
            },
        }

        compiled = ScenarioCompiler.compile_data(scenario)
        worlds = load_compiled_scenario_batch(
            ef_py.WorldBatchRuntime(1),
            compiled,
            seeds=[123],
        )

        self.assertEqual(len(worlds), 1)
        roster = worlds[0].active_roster
        self.assertEqual(len(roster), 2)
        self.assertEqual({member.entity_name for member in roster}, {"Lead", "Wing"})
        self.assertEqual(int(roster[0].team_id), 7001)
        self.assertEqual(int(roster[0].role_code), 21)
        self.assertEqual(int(roster[1].reference_entity_id), int(worlds[0].entities["Lead"]))

    def test_resolve_active_controllable_roster_falls_back_to_agent_entities(self) -> None:
        scenario = {
            "scenario_name": "roster_fallback",
            "entities": [
                {"name": "Lead", "type": "Aircraft", "side": "Blue", "is_agent": True},
                {"name": "Wing", "type": "Aircraft", "side": "Blue", "is_agent": True},
                {"name": "Observer", "type": "Aircraft", "side": "Blue", "is_agent": False},
            ],
        }
        entities = {"Lead": 101, "Wing": 102, "Observer": 103}

        roster = resolve_active_controllable_roster(scenario, entities, world_index=7)

        self.assertEqual(len(roster), 2)
        self.assertEqual([int(member.world_index) for member in roster], [7, 7])
        self.assertEqual({member.entity_name for member in roster}, {"Lead", "Wing"})
        self.assertTrue(all(bool(member.is_agent) for member in roster))

    def test_active_roster_helpers_find_members_and_build_refs(self) -> None:
        scenario = {
            "scenario_name": "roster_helpers",
            "entities": [
                {"name": "Lead", "type": "Aircraft", "side": "Blue", "is_agent": True},
                {"name": "Wing", "type": "Aircraft", "side": "Blue", "is_agent": True},
            ],
            "cooperative_roster": {
                "team_id": 8001,
                "members": [
                    {"entity": "Lead", "role_code": 21, "formation_role_id": "ElementLead"},
                    {"entity": "Wing", "role_code": 22, "formation_role_id": "Wingman", "reference_entity": "Lead"},
                ],
            },
        }
        entities = {"Lead": 201, "Wing": 202}
        roster = resolve_active_controllable_roster(scenario, entities, world_index=3)

        wing = find_active_roster_member(roster, entity_name="Wing")
        self.assertIsNotNone(wing)
        self.assertEqual(int(wing.entity_id), 202)
        self.assertEqual(int(wing.reference_entity_id), 201)

        lead = find_active_roster_member(roster, role_code=21)
        self.assertIsNotNone(lead)
        self.assertEqual(str(lead.formation_role_id), "ElementLead")

        refs = active_roster_world_entity_refs(roster)
        self.assertEqual(len(refs), 2)
        self.assertEqual([int(ref.world_index) for ref in refs], [3, 3])
        self.assertEqual([int(ref.entity_id) for ref in refs], [201, 202])

    def test_runtime_facade_exposes_capabilities_and_batch_config(self) -> None:
        config = ef_py.RuntimeBatchConfig()
        config.world_count = 3
        config.worker_threads = 2

        facade = ef_py.RuntimeFacade(config)
        capabilities = facade.capabilities()
        returned = facade.batch_config()

        self.assertEqual(int(facade.world_count()), 3)
        self.assertEqual(int(returned.world_count), 3)
        self.assertEqual(int(returned.worker_threads), 2)
        for field, expected in _RUNTIME_CAPABILITY_EXPECTATIONS.items():
            self.assertTrue(hasattr(capabilities, field), msg=f"missing RuntimeCapabilities.{field}")
            self.assertIs(
                bool(getattr(capabilities, field)),
                expected,
                msg=f"unexpected RuntimeCapabilities.{field}",
            )

        for field, expected in _RUNTIME_CAPABILITY_METADATA_EXPECTATIONS.items():
            self.assertTrue(hasattr(capabilities, field), msg=f"missing RuntimeCapabilities.{field}")
            self.assertEqual(
                getattr(capabilities, field),
                expected,
                msg=f"unexpected RuntimeCapabilities.{field}",
            )

        self.assertFalse(bool(capabilities.supports_resident_state))
        self.assertFalse(bool(capabilities.supports_exact_gpu_backend))
        self.assertFalse(bool(capabilities.supports_shadow_compare))

    def test_runtime_facade_fidelity_surface_declares_provider_selection_metadata(self) -> None:
        header = _repo_text("src", "runtime", "facade", "runtime_facade_types.h")
        facade_header = _repo_text("src", "runtime", "facade", "runtime_facade.h")
        binding_source = _repo_text("src", "interfaces", "python", "bindings_runtime.cpp")
        facade_source = _repo_text("src", "runtime", "facade", "runtime_facade.cpp")

        for token in (
            "struct RuntimeFidelityRequest",
            "std::string provider_family = \"none\"",
            "struct RuntimeFidelityAdmission",
            "std::string requested_provider_family = \"none\"",
            "std::string selected_provider_family = \"none\"",
            "std::string selected_stage_node_id",
        ):
            self.assertIn(token, header)

        self.assertIn("RuntimeFidelityAdmission admit_fidelity_request(", facade_header)
        self.assertIn('"RuntimeFidelityRequest"', binding_source)
        self.assertIn('"RuntimeFidelityAdmission"', binding_source)
        self.assertIn('"admit_fidelity_request"', binding_source)

        for provider_family in _RUNTIME_FIDELITY_PROVIDER_FAMILY_EXPECTATIONS.values():
            self.assertIn(provider_family, facade_source)
        self.assertIn("p10.observation_export.v1", facade_source)

    def test_runtime_capability_surface_declares_stable_backend_metadata_fields(self) -> None:
        header = _repo_text("src", "runtime", "facade", "runtime_facade_types.h")
        binding_source = _repo_text("src", "interfaces", "python", "bindings_runtime.cpp")
        facade_source = _repo_text("src", "runtime", "facade", "runtime_facade.cpp")

        for field in _RUNTIME_CAPABILITY_METADATA_EXPECTATIONS:
            self.assertIn(field, header)
            self.assertIn(f'"{field}"', binding_source)

        for value in _RUNTIME_CAPABILITY_METADATA_EXPECTATIONS.values():
            self.assertIn(value, facade_source)

    def test_runtime_facade_counterfactual_branch_reports_selected_slice_delta(self) -> None:
        facade = ef_py.RuntimeFacade(1)
        request = _build_counterfactual_branch_request()

        result = facade.run_counterfactual_branch(request)

        self.assertTrue(bool(result.admitted))
        self.assertEqual(result.rejection_reason, "")
        self.assertTrue(bool(result.fidelity_admission.admitted))
        self.assertEqual(result.fidelity_admission.selected_provider_family, "reference_cpu")
        self.assertEqual(result.fidelity_admission.selected_stage_node_id, "p10.observation_export.v1")
        self.assertEqual(result.parent_snapshot.barrier_id, "counterfactual_selected_slice")
        self.assertEqual(result.branch_snapshot.barrier_id, "counterfactual_selected_slice")
        self.assertEqual(result.parent_snapshot.cadence_reason, request.cadence_reason)
        self.assertEqual(result.branch_snapshot.provider_family, "reference_cpu")
        self.assertTrue(bool(result.comparison.comparable))
        self.assertAlmostEqual(float(result.comparison.dx), 25.0, places=6)
        self.assertAlmostEqual(float(result.comparison.dvy), 5.0, places=6)
        self.assertAlmostEqual(float(result.comparison.dheading), 15.0, places=6)
        self.assertIn("RuntimeFacade.run_counterfactual_branch", list(result.evidence_refs))
        self.assertIn("branch_point_id=branch_point:wp17f:0001", list(result.comparison.evidence_refs))

    def test_runtime_facade_counterfactual_branch_rejects_raw_authoritative_mutation(self) -> None:
        facade = ef_py.RuntimeFacade(1)
        request = _build_counterfactual_branch_request()
        request.allow_raw_authoritative_state_mutation = True

        result = facade.run_counterfactual_branch(request)

        self.assertFalse(bool(result.admitted))
        self.assertEqual(
            result.rejection_reason,
            "counterfactual_raw_authoritative_state_mutation_forbidden",
        )

    def test_runtime_facade_counterfactual_branch_rejects_unmaintained_fidelity(self) -> None:
        facade = ef_py.RuntimeFacade(1)
        request = _build_counterfactual_branch_request()
        request.fidelity_request.provider_family = "resident_state"

        result = facade.run_counterfactual_branch(request)

        self.assertFalse(bool(result.admitted))
        self.assertEqual(result.rejection_reason, "counterfactual_fidelity_request_not_admitted")
        self.assertFalse(bool(result.fidelity_admission.admitted))
        self.assertEqual(
            result.fidelity_admission.rejection_reason,
            "resident_state_fidelity_requires_maintained_backend_profile",
        )

    def test_runtime_facade_exports_typed_observation_packet(self) -> None:
        facade = ef_py.RuntimeFacade(1)
        facade.load_database(resolve_repo_path("examples", "config", "database"))

        setup_request = ef_py.BatchWorldSetupRequest()
        setup_request.seeds = [123]
        terrain = ef_py.WorldTerrainAssignment()
        terrain.world_index = 0
        terrain.terrain_type = "legacy"
        wind = ef_py.WorldWindAssignment()
        wind.world_index = 0
        spawn = ef_py.WorldSpawnRequest()
        spawn.world_index = 0
        spawn.side = ef_py.Side.Blue
        spawn.type_name = "Aircraft"
        spawn.entity_name = "Lead"
        spawn.is_agent = True
        spawn.x = -1400.0
        spawn.y = 0.0
        spawn.z = 1200.0
        spawn.heading = 90.0
        spawn.vy = 180.0
        setup_request.terrain_assignments = [terrain]
        setup_request.wind_assignments = [wind]
        setup_request.spawn_requests = [spawn]
        setup_request.time_steps = [0.05]

        setup_result = facade.apply_world_setup(setup_request)
        self.assertEqual(len(setup_result.entity_ids), 1)

        ref = _entity_ref(0, int(setup_result.entity_ids[0]))
        obs_request = ef_py.ObservationBatchRequest()
        obs_request.refs = [ref]
        obs_request.include_agent_observations = True
        obs_request.include_instrument_states = True
        packet = facade.export_observation_packet(obs_request)

        self.assertEqual(len(packet.refs), 1)
        self.assertEqual(len(packet.agent_observations), 1)
        self.assertEqual(len(packet.instrument_states), 1)
        self.assertEqual(int(packet.agent_observations[0].id), int(setup_result.entity_ids[0]))

    def test_runtime_facade_typed_platform_setup_materializes_through_legacy_compatibility_path(self) -> None:
        facade = ef_py.RuntimeFacade(1)
        self.assertTrue(
            facade.load_database(resolve_repo_path("examples", "config", "database"))
        )

        setup_request = ef_py.BatchWorldSetupRequest()
        setup_request.seeds = [123]
        terrain = ef_py.WorldTerrainAssignment()
        terrain.world_index = 0
        terrain.terrain_type = "legacy"
        wind = ef_py.WorldWindAssignment()
        wind.world_index = 0
        legacy_spawn = ef_py.WorldSpawnRequest()
        legacy_spawn.world_index = 0
        legacy_spawn.side = ef_py.Side.Blue
        legacy_spawn.type_name = "Aircraft"
        legacy_spawn.entity_name = "LegacyLead"
        legacy_spawn.is_agent = True
        legacy_spawn.x = -1400.0
        legacy_spawn.y = 0.0
        legacy_spawn.z = 1200.0
        legacy_spawn.heading = 90.0
        legacy_spawn.vy = 180.0
        setup_request.terrain_assignments = [terrain]
        setup_request.wind_assignments = [wind]
        setup_request.spawn_requests = [legacy_spawn]
        setup_request.typed_platform_spawn_requests = [
            _make_typed_platform_spawn_request()
        ]
        setup_request.time_steps = [0.05]

        setup_result = facade.apply_world_setup(setup_request)

        self.assertEqual(len(setup_result.entity_ids), 1)
        self.assertEqual(len(setup_result.typed_platform_spawn_results), 1)

        typed_result = setup_result.typed_platform_spawn_results[0]
        self.assertEqual(int(typed_result.request_index), 0)
        self.assertEqual(int(typed_result.world_index), 0)
        self.assertGreater(int(typed_result.entity_id), 0)
        self.assertTrue(bool(typed_result.admitted))
        self.assertTrue(bool(typed_result.materialized))
        self.assertFalse(bool(typed_result.fail_closed))
        self.assertEqual(typed_result.request_id, "typed-spawn:lead")
        self.assertEqual(typed_result.source_type_name, "Aircraft")
        self.assertEqual(typed_result.plan_id, "plan:typed-spawn:lead")
        self.assertEqual(typed_result.capability_bundle_id, "bundle:Aircraft")
        self.assertEqual(typed_result.rejection_reason, "")
        self.assertEqual(list(typed_result.errors), [])
        self.assertIn(
            "BatchWorldSetupRequest.typed_platform_spawn_requests",
            list(typed_result.evidence_refs),
        )
        self.assertIn("plan:typed-spawn:lead:evidence", list(typed_result.evidence_refs))
        self.assertNotEqual(int(typed_result.entity_id), int(setup_result.entity_ids[0]))

        observations = _public_observations_for_entity_range(
            facade,
            0,
            int(setup_result.entity_ids[0]),
            int(setup_result.entity_ids[0]) + 4,
        )
        self.assertTrue(
            _has_public_observation_at(
                observations,
                x=-1400.0,
                y=0.0,
                z=1200.0,
            )
        )
        self.assertTrue(
            _has_public_observation_at(
                observations,
                x=-1450.0,
                y=25.0,
                z=1200.0,
            )
        )

    def test_runtime_facade_typed_platform_setup_fail_closed_does_not_spawn_on_validation_or_world_guard(self) -> None:
        facade = ef_py.RuntimeFacade(1)
        self.assertTrue(
            facade.load_database(resolve_repo_path("examples", "config", "database"))
        )

        setup_request = ef_py.BatchWorldSetupRequest()
        setup_request.seeds = [123]
        terrain = ef_py.WorldTerrainAssignment()
        terrain.world_index = 0
        terrain.terrain_type = "legacy"
        wind = ef_py.WorldWindAssignment()
        wind.world_index = 0
        setup_request.terrain_assignments = [terrain]
        setup_request.wind_assignments = [wind]

        invalid_request = _make_typed_platform_spawn_request(
            request_id="typed-spawn:invalid",
            entity_name="InvalidTypedLead",
        )
        invalid_request.request_id = ""

        out_of_range_request = _make_typed_platform_spawn_request(
            world_index=7,
            request_id="typed-spawn:oob",
            entity_name="OutOfRangeTypedLead",
        )

        setup_request.typed_platform_spawn_requests = [
            invalid_request,
            out_of_range_request,
        ]
        setup_request.time_steps = [0.05]

        setup_result = facade.apply_world_setup(setup_request)

        self.assertEqual(len(setup_result.entity_ids), 0)
        self.assertEqual(len(setup_result.typed_platform_spawn_results), 2)

        validation_failure = setup_result.typed_platform_spawn_results[0]
        self.assertEqual(int(validation_failure.request_index), 0)
        self.assertEqual(int(validation_failure.world_index), 0)
        self.assertEqual(int(validation_failure.entity_id), 0)
        self.assertFalse(bool(validation_failure.admitted))
        self.assertFalse(bool(validation_failure.materialized))
        self.assertTrue(bool(validation_failure.fail_closed))
        self.assertEqual(validation_failure.request_id, "")
        self.assertEqual(validation_failure.source_type_name, "Aircraft")
        self.assertEqual(validation_failure.plan_id, "plan:typed-spawn:invalid")
        self.assertEqual(validation_failure.capability_bundle_id, "bundle:Aircraft")
        self.assertEqual(
            validation_failure.rejection_reason,
            "typed_platform_spawn_request_id_required",
        )
        self.assertIn("request_id is required", list(validation_failure.errors))
        self.assertIn(
            "BatchWorldSetupRequest.typed_platform_spawn_requests",
            list(validation_failure.evidence_refs),
        )

        world_guard_failure = setup_result.typed_platform_spawn_results[1]
        self.assertEqual(int(world_guard_failure.request_index), 1)
        self.assertEqual(int(world_guard_failure.world_index), 7)
        self.assertEqual(int(world_guard_failure.entity_id), 0)
        self.assertFalse(bool(world_guard_failure.admitted))
        self.assertFalse(bool(world_guard_failure.materialized))
        self.assertTrue(bool(world_guard_failure.fail_closed))
        self.assertEqual(world_guard_failure.request_id, "typed-spawn:oob")
        self.assertEqual(world_guard_failure.source_type_name, "Aircraft")
        self.assertEqual(world_guard_failure.plan_id, "plan:typed-spawn:oob")
        self.assertEqual(world_guard_failure.capability_bundle_id, "bundle:Aircraft")
        self.assertEqual(
            world_guard_failure.rejection_reason,
            "typed_platform_spawn_world_index_out_of_range",
        )
        self.assertIn(
            "typed platform spawn world_index is outside the configured runtime batch",
            list(world_guard_failure.errors),
        )
        self.assertIn(
            "BatchWorldSetupRequest.typed_platform_spawn_requests",
            list(world_guard_failure.evidence_refs),
        )

        observations = _public_observations_for_entity_range(facade, 0, 1, 8)
        self.assertFalse(
            _has_public_observation_at(
                observations,
                x=-1450.0,
                y=25.0,
                z=1200.0,
            )
        )

    def test_runtime_facade_step_execution_batch_returns_results_and_observations(self) -> None:
        entity_id = 77
        facade = ef_py.RuntimeFacade(1)

        ref = _entity_ref(0, entity_id)
        state = _build_route_state(entity_id)
        facade.prime_execution_episode_batch([ref], [state])

        exported_states = facade.export_execution_episode_states([ref])
        self.assertEqual(len(exported_states), 1)
        self.assertEqual(int(exported_states[0].agent_id), entity_id)

        batch_request = ef_py.ExecutionBatchStepRequest()
        batch_request.step_requests = [_build_route_request(entity_id)]
        batch_request.include_agent_observations = False

        result = facade.step_execution_batch(batch_request)
        post_step_exported_state = facade.export_execution_episode_states([ref])[0]

        self.assertEqual(len(result.step_results), 1)
        self.assertEqual(len(result.execution_episode_states), 1)
        self.assertEqual(len(result.rewards), 1)
        self.assertEqual(len(result.terminated), 1)
        self.assertEqual(len(result.truncated), 1)
        self.assertEqual(len(result.status_vectors), 1)
        self.assertEqual(len(result.termination_reasons), 1)
        self.assertEqual(len(result.reward_breakdown_jsons), 1)
        self.assertEqual(len(result.step_infos), 1)
        self.assertEqual(len(result.step_info_valid_flags), 1)
        self.assertEqual(len(result.controller_state_changed_flags), 1)
        self.assertEqual(len(result.observation_packet.refs), 1)
        self.assertEqual(len(result.observation_packet.agent_observations), 0)

        step_result = result.step_results[0]
        execution_episode_state = result.execution_episode_states[0]
        self.assertTrue(bool(step_result.valid))
        self.assertTrue(bool(step_result.structural_state_changed))
        self.assertAlmostEqual(float(result.rewards[0]), float(step_result.reward_total), places=6)
        self.assertEqual(bool(result.terminated[0]), bool(step_result.terminated))
        self.assertEqual(bool(result.truncated[0]), bool(step_result.truncated))
        self.assertEqual(
            [float(value) for value in result.status_vectors[0]],
            [
                float(step_result.status0),
                float(step_result.status1),
                float(step_result.status2),
                float(step_result.status3),
            ],
        )
        self.assertEqual(
            str(result.termination_reasons[0]),
            str(step_result.controller_state.last_termination_reason),
        )
        self.assertEqual(
            str(result.reward_breakdown_jsons[0]),
            str(step_result.controller_state.last_reward_breakdown_json),
        )
        self.assertEqual(bool(result.step_info_valid_flags[0]), bool(step_result.step_info_valid))
        self.assertEqual(
            float(result.step_infos[0].gear_stress),
            float(step_result.step_info.gear_stress),
        )
        self.assertEqual(
            bool(result.controller_state_changed_flags[0]),
            bool(step_result.structural_state_changed),
        )
        self.assertTrue(
            bool(ef_py.execution_episode_states_equivalent(execution_episode_state, post_step_exported_state))
        )
        self.assertEqual(int(execution_episode_state.mission_command.command_code), 2)
        self.assertEqual(str(execution_episode_state.mission_phase_name), "post_route")
        self.assertEqual(int(step_result.controller_state.mission_command.command_code), 2)
        self.assertEqual(str(step_result.controller_state.mission_phase_name), "post_route")

    def test_runtime_facade_step_execution_products_batch_advances_runtime_state(self) -> None:
        entity_id = 91
        facade = ef_py.RuntimeFacade(1)

        ref = _entity_ref(0, entity_id)
        state = _build_route_state(entity_id)
        facade.prime_execution_episode_batch([ref], [state])

        products = facade.step_execution_products_batch([_build_route_request(entity_id)])
        exported_states = facade.export_execution_episode_states([ref])

        self.assertEqual(len(products), 1)
        self.assertEqual(len(exported_states), 1)
        self.assertTrue(bool(products[0].valid))
        self.assertGreater(float(products[0].compiled_reward_total), 0.0)
        self.assertFalse(bool(products[0].terminated))
        self.assertEqual(str(exported_states[0].mission_phase_name), "post_route")
        self.assertEqual(int(exported_states[0].mission_command.command_code), 2)
        self.assertEqual(int(exported_states[0].step_count), 1)
        self.assertEqual(len(list(exported_states[0].route_waypoints)), 0)

    def test_runtime_facade_supports_batch_world_setup_via_scenario_runtime(self) -> None:
        scenario = {
            "scenario_name": "runtime_facade_batch_setup",
            "environment": {
                "time_step": 0.05,
                "terrain_type": "legacy",
                "wind": {
                    "speed_mps": 4.0,
                    "dir_from_deg": 180.0,
                    "shear_mps_per_km": 0.0,
                },
                "zones": [
                    {
                        "name": "Runway_A",
                        "x": 0.0,
                        "y": 0.0,
                        "width": 60.0,
                        "length": 2500.0,
                        "heading": 90.0,
                        "surface": "Concrete",
                    }
                ],
            },
            "mission_command": {
                "command_code": 2,
                "target_heading": 90.0,
                "target_altitude": 1200.0,
                "target_speed": 180.0,
            },
            "entities": [
                {
                    "name": "Lead",
                    "type": "Aircraft",
                    "side": "Blue",
                    "is_agent": True,
                    "pos": [-1400.0, 0.0, 1200.0],
                    "vel": [0.0, 180.0, 0.0],
                    "heading": 90.0,
                },
                {
                    "name": "Wing",
                    "type": "Aircraft",
                    "side": "Blue",
                    "is_agent": False,
                    "pos": [-1550.0, -120.0, 1200.0],
                    "vel": [0.0, 180.0, 0.0],
                    "heading": 90.0,
                },
            ],
        }
        compiled = ScenarioCompiler.compile_data(scenario)
        facade = ef_py.RuntimeFacade(2)
        self.assertTrue(facade.load_database(resolve_repo_path("examples", "config", "database")))

        worlds = load_compiled_scenario_batch(
            facade,
            compiled,
            seeds=[11, 17],
            apply_buffer=BatchWorldApplyBuffer(2),
        )

        self.assertEqual(len(worlds), 2)
        self.assertIsNotNone(worlds[0].agent_id)
        self.assertIsNotNone(worlds[1].agent_id)
        self.assertIn("Lead", worlds[0].entities)
        self.assertIn("Wing", worlds[1].entities)

        refs = [_entity_ref(0, int(worlds[0].agent_id)), _entity_ref(1, int(worlds[1].agent_id))]
        obs_request = ef_py.ObservationBatchRequest()
        obs_request.refs = refs
        obs_request.include_agent_observations = True
        packet = facade.export_observation_packet(obs_request)
        obs0 = packet.agent_observations[0]
        obs1 = packet.agent_observations[1]
        self.assertEqual(int(obs0.id), int(worlds[0].agent_id))
        self.assertEqual(int(obs1.id), int(worlds[1].agent_id))


if __name__ == "__main__":
    unittest.main()
