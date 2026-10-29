"""Opt-in RFC proofs against existing native and packet owners.

These proofs do not install a production composition profile or plugin.
"""

from __future__ import annotations

from dataclasses import replace
import hashlib
import json
from pathlib import Path

import pytest

from python.runtime_bootstrap import ensure_repo_imports

ensure_repo_imports()
import ef_py  # noqa: E402

from python.content.platform_blueprint import (  # noqa: E402
    HardpointContract,
    LegacyUnitProjection,
    LoadoutSelection,
    ModuleRecord,
    ModuleSelection,
    PlatformAssemblyError,
    PlatformBlueprint,
    lower_to_legacy_unit_definition,
    resolve_platform_assembly,
)
from python.content.platform_blueprint_adapter import (  # noqa: E402
    to_expanded_typed_platform_request,
)
from python.content.capability_bundles import SpawnPlacement  # noqa: E402
from python.content.capability_bundles.bindings_adapter import (  # noqa: E402
    to_typed_platform_spawn_request,
)
from python.experiment.air_combat_matrix import MATRIX_ENTRIES, REGISTRY  # noqa: E402
from python.experiment.resolved_input_lock import (  # noqa: E402
    InputLockError,
    build_resolved_input_lock,
    project_compiled_scenario_dependencies,
    project_native_composition_evidence,
)
from python.mechanisms.ports import (  # noqa: E402
    GraphEdge,
    MechanismSpec,
    PortSpec,
    compile_mechanism_graph,
    validate_realized_order,
)
from python.mission_obs_taxonomy import (  # noqa: E402
    mission_observation_basic_field_catalogue,
    mission_observation_field_names,
)
from python.scenario_compiler import ScenarioCompiler  # noqa: E402
from python.simulation.air.action import air_action_dimension, build_pilot_action  # noqa: E402
from python.simulation.air.observation import build_air_mission_vector  # noqa: E402
from examples.policies.air_basic_mission_linear import BasicMissionLinearPolicy  # noqa: E402
from python.tasking_contracts.policy import (  # noqa: E402
    ActionContract,
    AgentBinding,
    FieldSpec,
    ObservationContract,
    PolicyDescriptor,
    PolicyCheckpoint,
    PolicyCheckpointLoadError,
    PolicyRuntimeBinding,
    admit_policy,
    validate_policy_action,
)
from python.tasking_contracts.common.decision_registry import (  # noqa: E402
    DecisionModelRegistration,
    DecisionModelRegistry,
)
from python.tasking_contracts.common.decision_runtime import (  # noqa: E402
    DecisionRuntimeAgent,
    DecisionRuntimeAgentSpec,
)
from gym_envs.universal_env_parts.spaces import make_action_space  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
DATABASE = ROOT / "examples/config/database"


def test_declared_order_is_checked_against_native_realized_projection():
    result = ef_py.RuntimeFacade(2).export_composition_evidence()
    native = project_native_composition_evidence(result)
    assert len(native["realized_topology_digest"]) == 64
    assert native["realized_topology_digest"] != native["executable_graph_sha256"]
    order = json.loads(result.cpu_scheduler_topology_json[0])["topology"][
        "pipeline_candidate_order"
    ]
    node = MechanismSpec(
        "qualification.native_stage",
        "1",
        inputs=(PortSpec("in", "Scalar.v1"),),
        outputs=(PortSpec("out", "Scalar.v1"),),
    )
    graph = compile_mechanism_graph(
        "g",
        {"clear": node, "control": node},
        (GraphEdge("clear", "out", "control", "in"),),
        external_inputs=frozenset({"clear.in"}),
    )
    mapping = {"clear": "::ClearForces", "control": "::FlightControl"}
    assert not validate_realized_order(graph, node_systems=mapping, pipeline_order=order)
    inverted = {"control": "::ClearForces", "clear": "::FlightControl"}
    diagnostics = validate_realized_order(graph, node_systems=inverted, pipeline_order=order)
    assert diagnostics[0].code == "mechanism.realized_order_mismatch"


def _sha(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _legacy_projection(relative_path):
    legacy = json.loads((DATABASE / relative_path).read_text(encoding="utf-8"))
    records = {}
    for path in sorted(DATABASE.rglob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        rows = data.get("units", [data]) if isinstance(data, dict) else data
        for row in rows:
            if isinstance(row, dict) and "name" in row:
                records[row["name"]] = row
    fields = [
        (key, value)
        for key, value in legacy.items()
        if key.endswith("_ref") and isinstance(value, str)
    ]
    fields += [
        (f"default_loadout.{station}", stores[0] if isinstance(stores, list) else stores)
        for station, stores in legacy.get("default_loadout", {}).items()
    ]
    modules = {
        field: ModuleRecord(
            f"legacy.{ref}",
            records[ref]["type"],
            evidence_refs=("legacy-content:" + ref,),
            content_digest=_sha(records[ref]),
            native_ref=ref,
        )
        for field, ref in fields
    }
    blueprint = PlatformBlueprint(
        "qualification." + legacy["name"],
        "1",
        legacy["type"],
        slots=tuple((field, modules[field].kind) for field, _ in fields),
    )
    plan = resolve_platform_assembly(
        assembly_id=legacy["name"] + "@1",
        blueprint=blueprint,
        selections=tuple(ModuleSelection(field, field) for field, _ in fields),
        modules=modules,
    )
    projection = LegacyUnitProjection(
        plan.blueprint_ref, legacy, slot_paths=tuple((field, field) for field, _ in fields)
    )
    return legacy, plan, projection, modules


def _snapshot(facade, entity_id, world_index=0):
    ref = ef_py.WorldEntityRef()
    ref.world_index = world_index
    ref.entity_id = entity_id
    observation = facade.get_agent_observations_batch([ref])[0]
    return {
        name: repr(getattr(observation, name))
        for name in dir(observation)
        if not name.startswith("_") and not callable(getattr(observation, name))
    }


def _f16_native_expanded_request(*, factory_plan=None):
    legacy, _, projection, original_modules = _legacy_projection(
        "aircraft/units/f16c_block50.json"
    )
    capability_by_field = {
        "engine_ref": "mobility",
        "sensor_ref": "sensing",
        "ew_suite_ref": "survivability",
        "rcs_profile_ref": "survivability",
        "default_loadout.1": "launching",
        "default_loadout.2": "launching",
        "default_loadout.8": "launching",
        "default_loadout.9": "launching",
    }
    modules = {
        field: replace(module, capabilities=frozenset({capability_by_field[field]}))
        for field, module in original_modules.items()
    }
    blueprint = PlatformBlueprint(
        "qualification." + legacy["name"],
        "1",
        legacy["type"],
        slots=tuple((field, modules[field].kind) for field in modules),
        required_capabilities=frozenset(capability_by_field.values()),
    )
    plan = resolve_platform_assembly(
        assembly_id=legacy["name"] + "@native-typed",
        blueprint=blueprint,
        selections=tuple(ModuleSelection(field, field) for field in modules),
        modules=modules,
    )
    return to_expanded_typed_platform_request(
        plan=plan,
        blueprint=blueprint,
        modules=modules,
        projection=projection,
        source_type_name=legacy["name"],
        request_id="platform-blueprint:f16c:native-typed",
        placement=SpawnPlacement(
            world_index=1,
            side="blue",
            entity_name="BlueprintF16",
            x=100000.0,
            y=100000.0,
            z=1200.0,
            heading=90.0,
            vy=180.0,
        ),
        factory_plan=factory_plan,
    )


def _f16_native_typed_request():
    return to_typed_platform_spawn_request(ef_py, _f16_native_expanded_request())


def test_platform_assembly_projects_to_native_typed_spawn_and_preserves_observations():
    typed = _f16_native_typed_request()
    assert typed.resolved_spawn_plan.source_request_kind == "typed_platform_request"
    assert typed.resolved_spawn_plan.materialization_strategy == "resolved_spawn_plan_bridge"
    assert not bool(typed.type_name_projection_preserved)
    assert not bool(typed.capability_bundle.type_name_projection_preserved)
    assert not bool(typed.resolved_spawn_plan.type_name_projection_preserved)
    assert len(typed.capability_bundle.capabilities) == 8

    facade = ef_py.RuntimeFacade(2)
    assert facade.load_database(str(DATABASE))
    setup = ef_py.BatchWorldSetupRequest()
    setup.seeds = [123, 123]
    setup.time_steps = [0.05, 0.05]
    reference = ef_py.WorldSpawnRequest()
    reference.world_index = 0
    reference.side = ef_py.Side.Blue
    reference.type_name = "F-16C_Block50"
    reference.entity_name = "ReferenceF16"
    reference.x = 100000.0
    reference.y = 100000.0
    reference.z = 1200.0
    reference.heading = 90.0
    reference.vy = 180.0
    setup.spawn_requests = [reference]
    setup.typed_platform_spawn_requests = [typed]

    result = facade.apply_world_setup(setup)
    assert len(result.entity_ids) == 1
    typed_result = result.typed_platform_spawn_results[0]
    assert bool(typed_result.admitted)
    assert bool(typed_result.materialized)
    assert typed_result.setup_surface == "maintained_typed_setup"
    assert typed_result.rejection_reason == ""
    assert "platform_blueprint.native_typed_plan_adapter" in list(typed_result.evidence_refs)

    reference_id = int(result.entity_ids[0])
    typed_id = int(typed_result.entity_id)
    assert _snapshot(facade, reference_id, 0) == _snapshot(facade, typed_id, 1)
    for _ in range(4):
        facade.step_batch()
    assert _snapshot(facade, reference_id, 0) == _snapshot(facade, typed_id, 1)


def test_real_f16_factory_plan_rejects_partial_authored_capability_mapping():
    runtime = ef_py.WorldBatchRuntime(1)
    assert runtime.load_database(str(DATABASE))
    factory_plan = runtime.resolve_factory_platform_spawn_plan(0, "F-16C_Block50")
    assert bool(factory_plan.admitted)
    assert factory_plan.source_type_name == "F-16C_Block50"
    assert {capability.family for capability in factory_plan.resolved_capabilities} == {
        "sensing",
        "mobility",
        "launching",
        "communication",
        "survivability",
    }
    with pytest.raises(PlatformAssemblyError, match="factory_plan_capability_semantics_mismatch"):
        _f16_native_expanded_request(factory_plan=factory_plan)


@pytest.mark.parametrize(
    "relative_path",
    [
        "aircraft/units/f16c_block50.json",
        "ground/units/ground_infantry_soldier_mvp.json",
    ],
)
def test_platform_projection_preserves_native_setup_and_step_observations(relative_path, tmp_path):
    legacy, plan, projection, modules = _legacy_projection(relative_path)
    lowered = lower_to_legacy_unit_definition(plan, projection, modules=modules)
    assert lowered == legacy
    path = tmp_path / "resolved-unit.json"
    path.write_text(json.dumps({"units": [lowered]}), encoding="utf-8")
    facades = [ef_py.RuntimeFacade(1), ef_py.RuntimeFacade(1)]
    ids = []
    for index, facade in enumerate(facades):
        assert facade.load_database(str(DATABASE))
        if index == 1:
            assert facade.load_unit_definitions(str(path))
        setup = ef_py.BatchWorldSetupRequest()
        setup.seeds = [123]
        setup.time_steps = [0.05]
        spawn = ef_py.WorldSpawnRequest()
        spawn.world_index = 0
        spawn.type_name = legacy["name"]
        spawn.entity_name = "Reference"
        spawn.side = ef_py.Side.Blue
        spawn.x = 100000.0
        spawn.y = 100000.0
        spawn.z = 1200.0 if legacy["type"] == "Aircraft" else 0.0
        spawn.vy = 180.0 if legacy["type"] == "Aircraft" else 0.0
        setup.spawn_requests = [spawn]
        ids.append(int(facade.apply_world_setup(setup).entity_ids[0]))
    assert all(ids)
    for _ in range(4):
        assert _snapshot(facades[0], ids[0]) == _snapshot(facades[1], ids[1])
        for facade in facades:
            facade.step_batch()
    assert _snapshot(facades[0], ids[0]) == _snapshot(facades[1], ids[1])


def test_explicit_single_store_loadout_reaches_existing_native_loader(tmp_path):
    legacy, _, base_projection, original_modules = _legacy_projection(
        "aircraft/units/f16c_block50.json"
    )
    slot_modules = {
        field: module
        for field, module in original_modules.items()
        if not field.startswith("default_loadout.")
    }
    weapon_mounts = {
        "default_loadout.2": "Pylon",
        "default_loadout.8": "Pylon",
    }
    modules = dict(slot_modules)
    for field, mount_class in weapon_mounts.items():
        module = original_modules[field]
        modules[field] = replace(
            module,
            mass_kg=152.0 if "120" in module.native_ref else 85.0,
            mount_classes=frozenset({mount_class}),
        )
    hardpoints = tuple(
        HardpointContract(
            str(item["station_id"]),
            next(iter(item["type"])),
            float(item["capacity_kg"]),
            frozenset({"Missile"}),
        )
        for item in legacy["hardpoints"]
        if str(item["station_id"]) in {"2", "8"}
    )
    blueprint = PlatformBlueprint(
        "qualification." + legacy["name"] + ".explicit-loadout",
        "1",
        legacy["type"],
        slots=tuple((field, module.kind) for field, module in slot_modules.items()),
        hardpoints=hardpoints,
    )
    plan = resolve_platform_assembly(
        assembly_id=legacy["name"] + "@explicit-loadout",
        blueprint=blueprint,
        selections=tuple(ModuleSelection(field, field) for field in slot_modules),
        modules=modules,
        loadout=tuple(
            LoadoutSelection(station, f"default_loadout.{station}")
            for station in ("2", "8")
        ),
    )
    projection = replace(
        base_projection,
        blueprint_ref=plan.blueprint_ref,
        slot_paths=tuple((field, field) for field in slot_modules),
        loadout_paths=tuple(
            (station, f"default_loadout.{station}")
            for station in ("2", "8")
        ),
    )
    lowered = lower_to_legacy_unit_definition(plan, projection, modules=modules)
    assert lowered["default_loadout"] == legacy["default_loadout"]
    path = tmp_path / "explicit-loadout.json"
    path.write_text(json.dumps({"units": [lowered]}), encoding="utf-8")

    facades = [ef_py.RuntimeFacade(1), ef_py.RuntimeFacade(1)]
    ids = []
    for index, facade in enumerate(facades):
        assert facade.load_database(str(DATABASE))
        if index:
            assert facade.load_unit_definitions(str(path))
        setup = ef_py.BatchWorldSetupRequest()
        setup.seeds = [123]
        setup.time_steps = [0.05]
        spawn = ef_py.WorldSpawnRequest()
        spawn.type_name = legacy["name"]
        spawn.entity_name = "ExplicitLoadoutF16"
        spawn.side = ef_py.Side.Blue
        spawn.x = spawn.y = 100000.0
        spawn.z = 1200.0
        spawn.vy = 180.0
        setup.spawn_requests = [spawn]
        ids.append(int(facade.apply_world_setup(setup).entity_ids[0]))
    assert all(ids)
    assert _snapshot(facades[0], ids[0]) == _snapshot(facades[1], ids[1])
    for facade in facades:
        facade.step_batch()
    assert _snapshot(facades[0], ids[0]) == _snapshot(facades[1], ids[1])


def test_native_projection_rejects_changed_module_parameters_before_loading():
    _, plan, projection, modules = _legacy_projection("aircraft/units/f16c_block50.json")
    key = next(iter(modules))
    modules[key] = replace(modules[key], content_digest="0" * 64)
    with pytest.raises(PlatformAssemblyError, match="native_module_identity_mismatch"):
        lower_to_legacy_unit_definition(plan, projection, modules=modules)


def test_native_projection_rejects_changed_or_missing_physical_parameters_before_loading():
    _, plan, projection, modules = _legacy_projection("aircraft/units/f16c_block50.json")
    with pytest.raises(PlatformAssemblyError, match="native_module_physical_projection_incomplete"):
        lower_to_legacy_unit_definition(replace(plan, module_physical_parameters=()), projection, modules=modules)
    key = next(iter(modules))
    modules[key] = replace(modules[key], mass_kg=1.0)
    with pytest.raises(PlatformAssemblyError, match="native_module_physical_mismatch"):
        lower_to_legacy_unit_definition(plan, projection, modules=modules)


def test_bounded_fuel_override_reaches_existing_loader_and_native_observations(tmp_path):
    legacy, original_plan, projection, modules = _legacy_projection("aircraft/units/f16c_block50.json")
    blueprint = PlatformBlueprint(
        "qualification." + legacy["name"], "1", legacy["type"],
        slots=tuple((slot, module.kind) for slot, module in modules.items()),
        override_types=(("max_fuel_kg", "float"),),
        override_ranges=(("max_fuel_kg", 100.0, 3175.0),),
    )
    plan = resolve_platform_assembly(
        assembly_id=original_plan.assembly_id + ".reduced-fuel",
        blueprint=blueprint,
        modules=modules,
        selections=tuple(ModuleSelection(slot, slot) for slot in modules),
        parameter_overrides={"max_fuel_kg": 1500.0},
    )
    projection = replace(projection, override_paths=(("max_fuel_kg", "airframe.max_fuel_kg"),))
    lowered = lower_to_legacy_unit_definition(plan, projection, modules=modules)
    assert legacy["airframe"]["max_fuel_kg"] == 3175.0
    assert lowered["airframe"]["max_fuel_kg"] == 1500.0
    path = tmp_path / "reduced-fuel.json"
    path.write_text(json.dumps({"units": [lowered]}), encoding="utf-8")
    facades = [ef_py.RuntimeFacade(1), ef_py.RuntimeFacade(1)]
    ids = []
    for index, facade in enumerate(facades):
        assert facade.load_database(str(DATABASE))
        if index:
            assert facade.load_unit_definitions(str(path))
        setup = ef_py.BatchWorldSetupRequest()
        setup.seeds = [123]
        setup.time_steps = [0.05]
        spawn = ef_py.WorldSpawnRequest()
        spawn.type_name = legacy["name"]
        spawn.entity_name = "FuelOverrideProof"
        spawn.side = ef_py.Side.Blue
        spawn.x = spawn.y = 100000.0
        spawn.z = 1200.0
        spawn.vy = 180.0
        setup.spawn_requests = [spawn]
        ids.append(int(facade.apply_world_setup(setup).entity_ids[0]))
    # The existing public observation DTO does not expose fuel mass. The
    # snapshot is initially equal, but the existing dynamics owner makes the
    # different mass observable through motion after advancing the world.
    assert _snapshot(facades[0], ids[0]) == _snapshot(facades[1], ids[1])
    for facade in facades:
        facade.step_batch()
    assert _snapshot(facades[0], ids[0]) != _snapshot(facades[1], ids[1])


def test_existing_air_experiment_uses_compiler_owned_dependency_closure():
    experiment = MATRIX_ENTRIES[0].experiment
    compiled = ScenarioCompiler.compile_path(str(ROOT / experiment.scenario.path))
    dependencies = project_compiled_scenario_dependencies(compiled, repo_root=ROOT)
    candidate = build_resolved_input_lock(
        experiment, REGISTRY, repo_root=ROOT, effective_seeds=(23,), dependencies=dependencies
    )
    assert dependencies[experiment.scenario.path]["role"] == "semantic_input"
    assert candidate.status == "static_candidate"
    assert candidate.as_dict()["input_lock"]["effective_seed_set"] == [23]


def test_scenario_dependency_change_invalidates_owner_snapshot(tmp_path):
    path = tmp_path / "scenario.json"
    path.write_text('{"entities": []}', encoding="utf-8")
    compiled = ScenarioCompiler.compile_path(str(path))
    before = project_compiled_scenario_dependencies(compiled, repo_root=tmp_path)
    assert before["scenario.json"]["content_digest"]
    path.write_text('{"entities": [], "meta": {"changed": true}}', encoding="utf-8")
    with pytest.raises(InputLockError, match="dependencies_stale"):
        project_compiled_scenario_dependencies(compiled, repo_root=tmp_path)


def test_two_policy_implementations_share_owned_air_catalogue_and_native_action():
    fields = tuple(FieldSpec(**row) for row in mission_observation_basic_field_catalogue())
    assert [field.name for field in fields] == mission_observation_field_names("basic")
    observation = ObservationContract("air.mission.basic", 1, 0, required=fields)
    action = ActionContract(
        "air.takeoff4", 1, 0, air_action_dimension("takeoff4"), "platform_control"
    )
    binding = AgentBinding(
        "pilot",
        frozenset({"agent_observation"}),
        frozenset({action.interface_ref}),
        frozenset({action.authority_scope}),
    )

    class Scripted:
        def reset(self, *, context):
            self.closed = False

        def decide(self, *, observation, context, dt):
            return [0.1, 0.2, 0.0, 0.8]

        def close(self):
            self.closed = True

    class StandIn(Scripted):
        def decide(self, *, observation, context, dt):
            # A distinct deterministic stand-in, not a trained checkpoint.
            return [observation[0] / 10, observation[1] / 10, 0.0, observation[3] / 10]

    registry = DecisionModelRegistry(
        (
            DecisionModelRegistration("a", "air", ("pilot",), Scripted, "scripted"),
            DecisionModelRegistration("b", "air", ("pilot",), StandIn, "learned"),
        )
    )
    space = make_action_space("takeoff4")
    bounds = tuple(zip(map(float, space.low), map(float, space.high)))
    assert space.shape == (action.dimension,)
    outputs = []
    for category, model_id in (("scripted", "a"), ("community.stand_in", "b")):
        policy = PolicyDescriptor(category, "1", (category,), observation, action)
        admission = admit_policy(
            policy,
            binding,
            field_catalogue={f.name: f for f in fields},
            observation_version=(1, 0),
            action_versions={action.interface_ref: (1, 0)},
            action_dimensions={action.interface_ref: air_action_dimension("takeoff4")},
            action_timings={action.interface_ref: "window"},
        )
        assert admission.admitted
        implementation = registry.create_for(domain="air", role_id="pilot", model_id=model_id)
        implementation.reset(context=None)
        values = implementation.decide(observation=(1, 2, 0, 8), context=None, dt=0.05)
        assert not validate_policy_action(policy, values, bounds=bounds, timing="window")
        native = build_pilot_action(values, action_mode="takeoff4")
        outputs.append((native.stick_pitch, native.stick_roll, native.rudder, native.throttle))
        implementation.close()
        assert implementation.closed
    assert outputs[0] == outputs[1]
    with pytest.raises(ValueError, match="kind"):
        registry.create_for(domain="air", role_id="pilot", model_id="a", model_kind="learned")


@pytest.mark.parametrize("mode", [
    "complete", "bad_digest", "mask_closed", "expired", "out_of_bounds",
    "wrong_schema", "wrong_observation_order", "nonfinite_parameter",
])
def test_external_checkpoint_decision_runtime_reaches_native_action_owner(tmp_path, mode):
    fields = tuple(FieldSpec(**row) for row in mission_observation_basic_field_catalogue())
    action = ActionContract("air.takeoff4", 1, 0, air_action_dimension("takeoff4"), "platform_control")
    observation = ObservationContract("air.mission.basic", 1, 0, required=fields)
    agent = AgentBinding("pilot", frozenset({"agent_observation"}),
                         frozenset({action.interface_ref}), frozenset({action.authority_scope}))
    space = make_action_space("takeoff4")
    bounds = tuple(zip(map(float, space.low), map(float, space.high)))
    source = ROOT / "examples/policies/air_basic_mission_linear.v1.json"
    artifact = tmp_path / "external-policy.json"
    document = json.loads(source.read_bytes())
    if mode == "out_of_bounds":
        document["bias"][3] = 2.0
    if mode == "wrong_schema":
        document["schema_version"] = "unsupported"
    if mode == "wrong_observation_order":
        document["observation_fields"].reverse()
    if mode == "nonfinite_parameter":
        document["weights"][0][0] = float("nan")
    artifact.write_text(json.dumps(document), encoding="utf-8")
    checkpoint = PolicyCheckpoint(
        checkpoint_ref=artifact.as_uri(), artifact_sha256=hashlib.sha256(artifact.read_bytes()).hexdigest(),
        policy_id="example.air.basic.linear", policy_version="1",
        observation_view_ref=observation.view_ref, observation_major=1, observation_minor=0,
        action_interface_ref=action.interface_ref, action_major=1, action_minor=0,
        owner_ref="example.air.basic.linear",
    )
    policy = PolicyDescriptor(checkpoint.policy_id, "1", ("community.linear_stand_in",),
                              observation, action, legacy_model_kind="scripted", checkpoint=checkpoint)
    admission = admit_policy(
        policy, agent, field_catalogue={field.name: field for field in fields},
        observation_version=(1, 0), action_versions={action.interface_ref: (1, 0)},
        action_dimensions={action.interface_ref: action.dimension},
        action_timings={action.interface_ref: "window"}, checkpoint=checkpoint,
    )
    assert admission.admitted
    facade = ef_py.RuntimeFacade(2)
    assert facade.load_database(str(DATABASE))
    setup = ef_py.BatchWorldSetupRequest()
    setup.seeds, setup.time_steps = [42, 42], [0.05, 0.05]
    spawns = []
    for index in range(2):
        spawn = ef_py.WorldSpawnRequest()
        spawn.world_index, spawn.type_name, spawn.entity_name = index, "F-16C_Block50", "Pilot"
        spawn.side, spawn.z, spawn.vy = ef_py.Side.Blue, 1200.0, 220.0
        spawns.append(spawn)
    setup.spawn_requests = spawns
    ids = [int(value) for value in facade.apply_world_setup(setup).entity_ids]
    assert len(ids) == 2 and all(ids)
    refs = []
    commands = []
    for index, entity_id in enumerate(ids):
        ref = ef_py.WorldEntityRef()
        ref.world_index, ref.entity_id = index, entity_id
        refs.append(ref)
        command = ef_py.MissionCommand()
        command.command_code, command.cmd_heading_deg = 1, 45.0
        command.cmd_altitude_m, command.cmd_speed_mps = 1200.0, 220.0
        # Observe a maintained command packet; direct PilotAction remains the
        # control input exercised here, without an active autopilot command.
        command.active = False
        assignment = ef_py.WorldMissionCommandMaintainedAssignment()
        assignment.world_index, assignment.entity_id = index, entity_id
        assignment.mission_command = ef_py.mission_command_maintained_batch_contract(command)
        commands.append(assignment)
    facade.set_mission_commands_maintained_batch(commands)
    native_command = facade.get_mission_commands_maintained_batch(refs)[0]
    vector = build_air_mission_vector(native_command.shared_core, mode="basic")
    visible = dict(zip(mission_observation_field_names("basic"), map(float, vector)))
    assert list(visible.values()) == [1.0, 45.0, 1200.0, 220.0]
    before = [_snapshot(facade, entity_id, index) for index, entity_id in enumerate(ids)]
    initial_observation = facade.get_agent_observations_batch([refs[0]])[0]
    initial_position = tuple(float(getattr(initial_observation, axis)) for axis in ("x", "y", "z"))
    projected = []
    loaded = []

    def load_owner(payload):
        model = BasicMissionLinearPolicy.from_checkpoint_bytes(payload, action_dimension=action.dimension)
        loaded.append(model)
        return model

    def authorize_owner(_values, context, _dt):
        if context.get("action_mask_open") is not True:
            return "policy.action_mask_closed"
        if context["authority_scope"] != "platform_control":
            return "policy.action_authority_missing"
        if context["clock_s"] > context["action_expires_at_s"]:
            return "policy.action_expired"
        return True

    def project_owner(values):
        projected.append(tuple(values))
        return build_pilot_action(values, action_mode="takeoff4",
                                 instrument_state=facade.get_instrument_states_batch([refs[0]])[0])

    payload = artifact.read_bytes() if mode != "bad_digest" else b"tampered"
    if mode in ("bad_digest", "wrong_schema", "wrong_observation_order", "nonfinite_parameter"):
        with pytest.raises(PolicyCheckpointLoadError):
            PolicyRuntimeBinding.from_checkpoint_artifact(
                policy, admission, payload, owner_loader=load_owner, bounds=bounds, timing="window"
            )
        assert not loaded and not projected
        assert [_snapshot(facade, entity_id, index) for index, entity_id in enumerate(ids)] == before
        return
    binding = PolicyRuntimeBinding.from_checkpoint_artifact(
        policy, admission, payload, owner_loader=load_owner, bounds=bounds, timing="window",
        observation_projector=lambda values, _sources: values,
        action_authorizer=authorize_owner, action_projector=project_owner,
    )
    runtime = DecisionRuntimeAgent(
        DecisionRuntimeAgentSpec(agent_id="pilot", model_id=policy.policy_id, domain="air",
                                 role_id="pilot", model_kind="scripted", authority_scope="platform_control"),
        binding,
    )
    runtime.reset(episode_seed=42)
    try:
        context = {"action_mask_open": mode != "mask_closed",
                   "action_expires_at_s": -0.01 if mode == "expired" else 1.0}
        if mode != "complete":
            error = {"mask_closed": "action_mask_closed", "expired": "action_expired",
                     "out_of_bounds": "action_out_of_bounds"}[mode]
            with pytest.raises(ValueError, match=error):
                runtime.step(observation=visible, clock_s=0.0, observation_version="air.mission.basic@1.0",
                             context=context)
            assert not projected
            assert [_snapshot(facade, entity_id, index) for index, entity_id in enumerate(ids)] == before
            return
        decision = runtime.step(observation=visible, clock_s=0.0, observation_version="air.mission.basic@1.0",
                                context=context)
        assert len(projected) == 1
        assert projected[0] == pytest.approx((0.1, 0.2, 0.0, 0.8))
        assert loaded[0].last_context["policy_checkpoint_sha256"] == checkpoint.artifact_sha256
        assert loaded[0].last_context["policy_checkpoint_ref"] == checkpoint.checkpoint_ref
        assignments = []
        for index, entity_id in enumerate(ids):
            assignment = ef_py.WorldPilotActionAssignment()
            assignment.world_index, assignment.entity_id = index, entity_id
            assignment.action = decision.action if index == 0 else build_pilot_action(
                (0.1, 0.2, 0.0, 0.8), action_mode="takeoff4",
                instrument_state=facade.get_instrument_states_batch([refs[index]])[0],
            )
            assignments.append(assignment)
        initial_throttle = float(facade.get_instrument_states_batch([refs[0]])[0].throttle_pos)
        facade.set_pilot_actions_batch(assignments)
        for _ in range(3):
            facade.step_batch()
        instruments = facade.get_instrument_states_batch(refs)
        assert float(instruments[0].throttle_pos) == pytest.approx(0.8, abs=1e-6)
        assert float(instruments[0].throttle_pos) != pytest.approx(initial_throttle, abs=1e-4)
        assert _snapshot(facade, ids[0], 0) == _snapshot(facade, ids[1], 1)
        assert float(facade.get_agent_observations_batch([refs[0]])[0].sim_time) == pytest.approx(0.15)
        # A later native mission update must alter the checkpoint model's
        # action. This rules out a fixed-vector stand-in for the observation
        # projection and proves another decision reaches native control.
        for assignment in commands:
            changed = ef_py.MissionCommand()
            changed.command_code, changed.cmd_heading_deg = 1, 45.0
            changed.cmd_altitude_m, changed.cmd_speed_mps = 1200.0, 110.0
            changed.active = False
            assignment.mission_command = ef_py.mission_command_maintained_batch_contract(changed)
        facade.set_mission_commands_maintained_batch(commands)
        changed_core = facade.get_mission_commands_maintained_batch(refs)[0].shared_core
        changed_vector = build_air_mission_vector(changed_core, mode="basic")
        changed_visible = dict(zip(mission_observation_field_names("basic"), map(float, changed_vector)))
        decision = runtime.step(observation=changed_visible, clock_s=0.15,
                                observation_version="air.mission.basic@1.0", context=context)
        assert len(projected) == 2
        assert projected[1] == pytest.approx((0.1, 0.2, 0.0, 0.4))
        assignments[0].action = decision.action
        assignments[1].action = build_pilot_action(
            (0.1, 0.2, 0.0, 0.4), action_mode="takeoff4",
            instrument_state=facade.get_instrument_states_batch([refs[1]])[0],
        )
        facade.set_pilot_actions_batch(assignments)
        for _ in range(3):
            facade.step_batch()
        assert float(facade.get_instrument_states_batch([refs[0]])[0].throttle_pos) == pytest.approx(0.4, abs=1e-6)
        assert _snapshot(facade, ids[0], 0) == _snapshot(facade, ids[1], 1)
        final_observation = facade.get_agent_observations_batch([refs[0]])[0]
        assert float(final_observation.sim_time) == pytest.approx(0.3)
        assert tuple(float(getattr(final_observation, axis)) for axis in ("x", "y", "z")) != initial_position
    finally:
        runtime.close()
        assert loaded[0].closed
