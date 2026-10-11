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
    LegacyUnitProjection,
    ModuleRecord,
    ModuleSelection,
    PlatformAssemblyError,
    PlatformBlueprint,
    lower_to_legacy_unit_definition,
    resolve_platform_assembly,
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
from python.tasking_contracts.policy import (  # noqa: E402
    ActionContract,
    AgentBinding,
    FieldSpec,
    ObservationContract,
    PolicyDescriptor,
    admit_policy,
    validate_policy_action,
)
from python.tasking_contracts.common.decision_registry import (  # noqa: E402
    DecisionModelRegistration,
    DecisionModelRegistry,
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
        (f"default_loadout.{station}", ref)
        for station, ref in legacy.get("default_loadout", {}).items()
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


def _snapshot(facade, entity_id):
    ref = ef_py.WorldEntityRef()
    ref.world_index = 0
    ref.entity_id = entity_id
    observation = facade.get_agent_observations_batch([ref])[0]
    return {
        name: repr(getattr(observation, name))
        for name in dir(observation)
        if not name.startswith("_") and not callable(getattr(observation, name))
    }


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


def test_native_projection_rejects_changed_module_parameters_before_loading():
    _, plan, projection, modules = _legacy_projection("aircraft/units/f16c_block50.json")
    key = next(iter(modules))
    modules[key] = replace(modules[key], content_digest="0" * 64)
    with pytest.raises(PlatformAssemblyError, match="native_module_identity_mismatch"):
        lower_to_legacy_unit_definition(plan, projection, modules=modules)


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
