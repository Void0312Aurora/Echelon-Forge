from __future__ import annotations

import pytest

from python.runtime_bootstrap import ensure_repo_imports, resolve_repo_path


ensure_repo_imports()

import ef_py  # noqa: E402


def _facts_tuple(value: object) -> tuple[object, ...]:
    return (
        value.step,
        value.state_digest,
        value.event_cursor,
        value.rng_digest,
        value.terminated,
        value.episode_seed,
    )


def test_maintained_facade_exposes_native_identity_and_isolated_child_branch() -> None:
    facade = ef_py.RuntimeFacade(1)
    parent_before = facade.native_snapshot_facts()

    child = facade.fork_native_branch(0, "a" * 64, 2)
    assert child is not None
    assert child.valid()
    assert _facts_tuple(child.snapshot_facts()) == _facts_tuple(parent_before)

    assert facade.step_batch() is None
    assert facade.native_snapshot_facts().step == parent_before.step + 1
    assert child.snapshot_facts().step == parent_before.step

    assert child.step_pilot_actions([])
    assert child.snapshot_facts().step == parent_before.step + 1
    assert facade.native_snapshot_facts().step == parent_before.step + 1
    packet = child.read_observation_packet([])
    assert packet.snapshot_version == child.snapshot_facts().step + 1
    assert packet.barrier_id == "export"

    checkpoint = child.checkpoint()
    assert checkpoint is not None
    assert checkpoint.valid()
    assert _facts_tuple(checkpoint.snapshot_facts()) == _facts_tuple(child.snapshot_facts())
    assert checkpoint.fork_native_branch("b" * 64, 1).valid()


def test_native_branch_preserves_agent_handles_across_restore_and_nested_fork() -> None:
    facade = ef_py.RuntimeFacade(1)
    setup = ef_py.BatchWorldSetupRequest()
    setup.seeds = [42]
    setup.time_steps = [1.0]
    spawn = ef_py.WorldSpawnRequest()
    spawn.type_name = "Aircraft"
    spawn.entity_name = "controlled_aircraft"
    spawn.is_agent = True
    spawn.z = 3000.0
    spawn.vx = 150.0
    setup.spawn_requests = [spawn]
    entity_id = facade.apply_world_setup(setup).entity_ids[0]
    ref = ef_py.WorldEntityRef()
    ref.entity_id = entity_id

    child = facade.fork_native_branch(0, "a" * 64, 2)
    assert child is not None
    initial = child.read_observation_packet([ref]).agent_observations[0]
    assert initial.id == entity_id
    assert initial.speed == 150.0

    action = ef_py.PilotAction()
    action.active = True
    action.throttle = 0.0
    assignment = ef_py.WorldPilotActionAssignment()
    assignment.entity_id = entity_id
    assignment.action = action
    invalid = ef_py.WorldPilotActionAssignment()
    invalid.entity_id = entity_id + 1
    invalid.action = action
    before_rejection = child.snapshot_facts()
    assert not child.step_pilot_actions([assignment, invalid])
    assert _facts_tuple(child.snapshot_facts()) == _facts_tuple(before_rejection)
    assert child.step_pilot_actions([assignment])
    child_observation = child.read_observation_packet([ref]).agent_observations[0]
    parent_observation = facade.get_agent_observations_batch([ref])[0]
    assert child_observation.id == entity_id
    assert child_observation.speed < initial.speed
    assert parent_observation.speed == initial.speed

    grandchild = child.fork_native_branch("b" * 64, 1)
    assert grandchild is not None
    assert grandchild.read_observation_packet([ref]).agent_observations[0].id == entity_id


def test_maintained_facade_rejects_invalid_native_branch_admission() -> None:
    facade = ef_py.RuntimeFacade(1)

    assert facade.fork_native_branch(0, "A" * 64, 1) is None
    assert facade.fork_native_branch(0, "a" * 63, 1) is None
    assert facade.fork_native_branch(0, "a" * 64, 0) is None


def test_native_branch_of_a_non_default_seed_steps_like_its_parent() -> None:
    # The review found children kept a fresh kernel's seed 42 identity and a
    # float-rounded clock. Seed 7, dt = 1/60 and a fork after step 3 expose both.
    facade = ef_py.RuntimeFacade(1)
    setup = ef_py.BatchWorldSetupRequest()
    setup.seeds = [7]
    setup.time_steps = [1.0 / 60.0]
    spawn = ef_py.WorldSpawnRequest()
    spawn.type_name = "Aircraft"
    spawn.entity_name = "controlled_aircraft"
    spawn.is_agent = True
    spawn.z = 3000.0
    spawn.vx = 150.0
    setup.spawn_requests = [spawn]
    facade.apply_world_setup(setup)
    for _ in range(3):
        facade.step_batch()

    child = facade.fork_native_branch(0, "a" * 64, 5)
    assert child is not None
    assert _facts_tuple(child.snapshot_facts()) == _facts_tuple(facade.native_snapshot_facts())
    for _ in range(5):
        facade.step_batch()
        assert child.step_pilot_actions([])
        assert _facts_tuple(child.snapshot_facts()) == _facts_tuple(
            facade.native_snapshot_facts()
        )


def test_native_branch_rejects_untransferred_loaded_unit_definitions() -> None:
    facade = ef_py.RuntimeFacade(1)
    assert facade.fork_native_branch(0, "a" * 64, 1) is not None
    definition = resolve_repo_path(
        "examples", "config", "database", "ground", "units", "ground_infantry_soldier_mvp.json"
    )
    assert facade.load_unit_definitions(str(definition))
    before = _facts_tuple(facade.native_snapshot_facts())
    assert facade.fork_native_branch(0, "b" * 64, 1) is None
    assert _facts_tuple(facade.native_snapshot_facts()) == before


@pytest.mark.parametrize("seed", [0, 7, 2**32 - 1])
def test_native_episode_seed_is_an_owner_fact_preserved_by_forks(seed: int) -> None:
    facade = ef_py.RuntimeFacade(1)
    request = ef_py.BatchResetRequest()
    request.seeds = [seed]
    facade.reset_batch(request)
    initial = facade.native_snapshot_facts()
    assert initial.episode_seed == seed
    with pytest.raises(AttributeError):
        initial.episode_seed = seed + 1
    child = facade.fork_native_branch(0, "a" * 64, 2)
    assert child is not None
    assert child.snapshot_facts().episode_seed == seed
    assert child.step_pilot_actions([])
    checkpoint = child.checkpoint()
    assert checkpoint is not None
    assert checkpoint.snapshot_facts().episode_seed == seed
    nested = checkpoint.fork_native_branch("b" * 64, 1)
    assert nested is not None
    assert nested.snapshot_facts().episode_seed == seed
