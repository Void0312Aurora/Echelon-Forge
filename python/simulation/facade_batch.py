"""Direct compiled simulation provider for decision models and scenario runners."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping, Sequence

import ef_py


EntityKey = tuple[int, int]
SetupFactory = Callable[[tuple[int, ...]], Any]


@dataclass(frozen=True)
class FacadeBatchSnapshot:
    """Maintained native state for the controlled entities in setup order."""

    entity_keys: tuple[EntityKey, ...]
    observations: tuple[Any, ...]
    instruments: tuple[Any, ...]


class FacadeBatchBackend:
    """Drive the authoritative RuntimeFacade without an environment wrapper."""

    def __init__(
        self,
        *,
        database_path: str,
        setup_factory: SetupFactory,
        world_count: int = 1,
        controlled_spawn_indices: Sequence[int] | None = None,
        worker_threads: int = 1,
    ) -> None:
        if not callable(setup_factory):
            raise TypeError("facade batch setup_factory must be callable")
        if int(world_count) <= 0 or int(worker_threads) <= 0:
            raise ValueError("facade batch world_count and worker_threads must be positive")
        config = ef_py.RuntimeBatchConfig()
        config.world_count = int(world_count)
        config.worker_threads = int(worker_threads)
        self.facade = ef_py.RuntimeFacade(config)
        if not self.facade.load_database(str(database_path)):
            raise RuntimeError(f"facade batch could not load database: {database_path}")
        self.world_count = int(world_count)
        self.setup_factory = setup_factory
        self.controlled_spawn_indices = None if controlled_spawn_indices is None else tuple(
            int(index) for index in controlled_spawn_indices
        )
        self._seeds = tuple(42 for _ in range(self.world_count))
        self._entity_keys: tuple[EntityKey, ...] = ()
        self._ready = False
        self._closed = False

    def seed(self, seed: int) -> tuple[int, ...]:
        self._require_open()
        value = int(seed) & 0xFFFFFFFF
        self._seeds = tuple(value for _ in range(self.world_count))
        return self._seeds

    def reset(self) -> FacadeBatchSnapshot:
        self._require_open()
        self._ready = False
        self._entity_keys = ()
        setup = self.setup_factory(self._seeds)
        spawns = list(getattr(setup, "spawn_requests", ()) or ())
        if len(list(getattr(setup, "seeds", ()) or ())) != self.world_count:
            raise ValueError("facade batch setup must contain one seed per world")
        indices = self.controlled_spawn_indices
        if indices is None:
            indices = tuple(range(len(spawns)))
        if not indices or len(set(indices)) != len(indices) or any(index < 0 or index >= len(spawns) for index in indices):
            raise ValueError("facade batch controlled spawn indices must be unique and in range")
        result = self.facade.apply_world_setup(setup)
        entity_ids = tuple(int(value) for value in result.entity_ids)
        if len(entity_ids) != len(spawns) or any(value <= 0 for value in entity_ids):
            raise RuntimeError("facade batch setup did not materialize every declared spawn")
        self._entity_keys = tuple((int(spawns[index].world_index), entity_ids[index]) for index in indices)
        self._ready = True
        return self.snapshot()

    def snapshot(self) -> FacadeBatchSnapshot:
        self._require_ready()
        refs = self._refs()
        observations = tuple(self.facade.get_agent_observations_batch(refs))
        instruments = tuple(self.facade.get_instrument_states_batch(refs))
        if len(observations) != len(refs) or len(instruments) != len(refs):
            raise RuntimeError("facade batch observation count does not match controlled roster")
        return FacadeBatchSnapshot(self._entity_keys, observations, instruments)

    def air_scripted_observations(
        self,
        *,
        mode: str = "nav_v2_cooperative_takeoff_v1",
        ils: Mapping[EntityKey, Sequence[float]] | None = None,
        max_contacts: int = 8,
        max_rwr: int = 8,
    ) -> tuple[dict[str, Any], ...]:
        """Build neutral Air observations from native facade state."""
        self._require_ready()
        from .air.observation import build_air_scripted_observation

        current = self.snapshot()
        commands = self.read_command_chain()["mission_commands"]
        ils_by_key = {} if ils is None else dict(ils)
        return tuple(
            build_air_scripted_observation(
                observation,
                instrument,
                commands[index] if index < len(commands) else None,
                mode=mode,
                ils=ils_by_key.get(entity_key, (0.0, 0.0, 0.0, 0.0)),
                max_contacts=max_contacts,
                max_rwr=max_rwr,
            )
            for index, (entity_key, observation, instrument) in enumerate(
                zip(current.entity_keys, current.observations, current.instruments)
            )
        )

    def step(self, actions: Mapping[EntityKey, Any]) -> FacadeBatchSnapshot:
        self._require_ready()
        if not isinstance(actions, Mapping):
            raise TypeError("facade batch step requires an entity-keyed mapping")
        missing = set(self._entity_keys).difference(actions)
        if missing:
            raise KeyError(f"facade batch step requires actions for every controlled entity: {sorted(missing)}")
        self._submit("set_pilot_actions_batch", "WorldPilotActionAssignment", "action", actions)
        self.facade.step_batch()
        return self.snapshot()

    def submit_task_orders(self, orders: Mapping[EntityKey, Any]) -> None:
        self._submit("set_task_orders_maintained_batch", "WorldTaskOrderMaintainedAssignment", "task_order", orders, "task_order_maintained_batch_contract")

    def submit_leader_intents(self, intents: Mapping[EntityKey, Any]) -> None:
        self._submit("set_leader_intents_maintained_batch", "WorldLeaderIntentMaintainedAssignment", "leader_intent", intents, "leader_intent_maintained_batch_contract")

    def submit_pilot_reports(self, reports: Mapping[EntityKey, Any]) -> None:
        self._submit("set_pilot_reports_maintained_batch", "WorldPilotReportMaintainedAssignment", "pilot_report", reports, "pilot_report_maintained_batch_contract")

    def submit_mission_commands(self, commands: Mapping[EntityKey, Any]) -> None:
        self._submit("set_mission_commands_maintained_batch", "WorldMissionCommandMaintainedAssignment", "mission_command", commands, "mission_command_maintained_batch_contract")

    def submit_air_director_decisions(
        self,
        decisions: Mapping[EntityKey, Any],
    ) -> None:
        """Submit a direct Air director's complete maintained command chain."""
        if not isinstance(decisions, Mapping):
            raise TypeError("facade batch Air director decisions require an entity-keyed mapping")
        self.submit_task_orders({key: value.task_order for key, value in decisions.items()})
        self.submit_leader_intents({key: value.leader_intent for key, value in decisions.items()})
        self.submit_pilot_reports({key: value.pilot_report for key, value in decisions.items()})
        self.submit_mission_commands({key: value.mission_command for key, value in decisions.items()})

    def read_command_chain(self) -> dict[str, tuple[Any, ...]]:
        self._require_ready()
        refs = self._refs()
        return {
            "task_orders": tuple(self.facade.get_task_orders_maintained_batch(refs)),
            "leader_intents": tuple(self.facade.get_leader_intents_maintained_batch(refs)),
            "pilot_reports": tuple(self.facade.get_pilot_reports_maintained_batch(refs)),
            "mission_commands": tuple(self.facade.get_mission_commands_maintained_batch(refs)),
        }

    def close(self) -> None:
        self._ready = False
        self._closed = True
        self._entity_keys = ()

    def _submit(self, method: str, assignment_type: str, field_name: str, payloads: Mapping[EntityKey, Any], projection: str | None = None) -> None:
        self._require_ready()
        if not isinstance(payloads, Mapping):
            raise TypeError(f"facade batch {method} requires an entity-keyed mapping")
        unexpected = set(payloads).difference(self._entity_keys)
        if unexpected:
            raise KeyError(f"facade batch {method} targets uncontrolled entities: {sorted(unexpected)}")
        assignments = []
        assignment_class = getattr(ef_py, assignment_type)
        for world_index, entity_id in self._entity_keys:
            key = (world_index, entity_id)
            if key not in payloads:
                continue
            assignment = assignment_class()
            assignment.world_index = world_index
            assignment.entity_id = entity_id
            payload = payloads[key]
            if projection is not None:
                payload = getattr(ef_py, projection)(payload)
            setattr(assignment, field_name, payload)
            assignments.append(assignment)
        if assignments:
            getattr(self.facade, method)(assignments)

    def _refs(self) -> list[Any]:
        refs = []
        for world_index, entity_id in self._entity_keys:
            ref = ef_py.WorldEntityRef()
            ref.world_index = world_index
            ref.entity_id = entity_id
            refs.append(ref)
        return refs

    def _require_open(self) -> None:
        if self._closed:
            raise RuntimeError("facade batch backend is closed")

    def _require_ready(self) -> None:
        self._require_open()
        if not self._ready:
            raise RuntimeError("facade batch backend must be reset before use")


__all__ = ["EntityKey", "FacadeBatchBackend", "FacadeBatchSnapshot", "SetupFactory"]
