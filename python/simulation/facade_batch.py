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
        setup_factory: SetupFactory | None = None,
        scenario_path: str | None = None,
        compiled_scenario: Any | None = None,
        randomization_overrides: Mapping[str, Any] | None = None,
        world_count: int = 1,
        controlled_spawn_indices: Sequence[int] | None = None,
        worker_threads: int = 1,
    ) -> None:
        if setup_factory is not None and not callable(setup_factory):
            raise TypeError("facade batch setup_factory must be callable")
        if scenario_path is not None and compiled_scenario is not None:
            raise ValueError("facade batch accepts either scenario_path or compiled_scenario, not both")
        if setup_factory is None and scenario_path is None and compiled_scenario is None:
            raise ValueError(
                "facade batch requires setup_factory, scenario_path, or compiled_scenario"
            )
        if int(world_count) <= 0 or int(worker_threads) <= 0:
            raise ValueError("facade batch world_count and worker_threads must be positive")
        config = ef_py.RuntimeBatchConfig()
        config.world_count = int(world_count)
        config.worker_threads = int(worker_threads)
        self.facade = ef_py.RuntimeFacade(config)
        if not self.facade.load_database(str(database_path)):
            raise RuntimeError(f"facade batch could not load database: {database_path}")
        self._world_count = int(world_count)
        self.setup_factory = setup_factory
        self.scenario_path = None if scenario_path is None else str(scenario_path)
        self.compiled_scenario = compiled_scenario
        self.randomization_overrides = (
            None if randomization_overrides is None else dict(randomization_overrides)
        )
        self.controlled_spawn_indices = None if controlled_spawn_indices is None else tuple(
            int(index) for index in controlled_spawn_indices
        )
        self._seeds = tuple(42 for _ in range(self._world_count))
        self._entity_keys: tuple[EntityKey, ...] = ()
        self._ready = False
        self._closed = False

    def seed(self, seed: int) -> tuple[int, ...]:
        self._require_open()
        value = int(seed) & 0xFFFFFFFF
        self._seeds = tuple((value + index) & 0xFFFFFFFF for index in range(self._world_count))
        return self._seeds

    def reset(self) -> FacadeBatchSnapshot:
        self._require_open()
        self._ready = False
        self._entity_keys = ()
        if self.setup_factory is not None:
            setup = self.setup_factory(self._seeds)
            spawns = list(getattr(setup, "spawn_requests", ()) or ())
            if len(list(getattr(setup, "seeds", ()) or ())) != self._world_count:
                raise ValueError("facade batch setup must contain one seed per world")
            indices = self._validate_controlled_indices(len(spawns))
            result = self.facade.apply_world_setup(setup)
            entity_ids = tuple(int(value) for value in result.entity_ids)
            if len(entity_ids) != len(spawns) or any(value <= 0 for value in entity_ids):
                raise RuntimeError("facade batch setup did not materialize every declared spawn")
            self._entity_keys = tuple(
                (int(spawns[index].world_index), entity_ids[index]) for index in indices
            )
        else:
            from python.scenario.compiler import ScenarioCompiler
            from python.scenario.runtime import load_compiled_scenario_for_setup_target

            compiled = self.compiled_scenario
            if compiled is None:
                compiled = ScenarioCompiler.compile_path(str(self.scenario_path))
                self.compiled_scenario = compiled
            applied_worlds = load_compiled_scenario_for_setup_target(
                self,
                compiled,
                seeds=self._seeds,
                randomization_overrides=self.randomization_overrides,
            )
            if len(applied_worlds) != self._world_count:
                raise RuntimeError("facade batch scenario setup did not materialize every world")
            template_spawns = tuple(
                getattr(getattr(compiled, "runtime_metadata", None), "layout_template", None).spawns
            )
            keys: list[EntityKey] = []
            for world_index, applied in enumerate(applied_worlds):
                indices = self._validate_controlled_indices(len(template_spawns))
                for index in indices:
                    spawn = template_spawns[index]
                    entity_id = int(applied.entities.get(spawn.entity_name, 0))
                    if entity_id <= 0:
                        raise RuntimeError(
                            "facade batch scenario setup did not materialize controlled spawn "
                            f"{spawn.entity_name!r} in world {world_index}"
                        )
                    keys.append((int(world_index), entity_id))
            self._entity_keys = tuple(keys)
        self._ready = True
        return self.snapshot()

    def world_count(self) -> int:
        """Expose provider-neutral world cardinality to scenario materializers."""

        return int(self._world_count)

    def apply_world_setup(self, request: Any) -> Any:
        """Apply a maintained setup request for the scenario materializer."""

        self._require_open()
        return self.facade.apply_world_setup(request)

    def _validate_controlled_indices(self, spawn_count: int) -> tuple[int, ...]:
        indices = self.controlled_spawn_indices
        if indices is None:
            indices = tuple(range(int(spawn_count)))
        indices = tuple(int(index) for index in indices)
        if not indices or len(set(indices)) != len(indices) or any(
            index < 0 or index >= int(spawn_count) for index in indices
        ):
            raise ValueError("facade batch controlled spawn indices must be unique and in range")
        return indices

    def snapshot(self) -> FacadeBatchSnapshot:
        self._require_ready()
        refs = self._refs()
        observations = tuple(self.facade.get_agent_observations_batch(refs))
        instruments = tuple(self.facade.get_instrument_states_batch(refs))
        if len(observations) != len(refs) or len(instruments) != len(refs):
            raise RuntimeError("facade batch observation count does not match controlled roster")
        return FacadeBatchSnapshot(self._entity_keys, observations, instruments)

    @property
    def entity_keys(self) -> tuple[EntityKey, ...]:
        """Controlled roster identity for explicit cross-domain adapters."""

        self._require_ready()
        return self._entity_keys

    @property
    def slots_per_world(self) -> int:
        """Number of controlled cooperative slots exposed by this provider."""

        if self._entity_keys:
            return len(self._entity_keys)
        return len(self.controlled_spawn_indices or ())

    def cooperative_slot_metadata(self) -> tuple[dict[str, Any], ...]:
        """Expose controlled entity identity without leaking provider internals."""

        self._require_ready()
        return tuple(
            {
                "world_index": int(world_index),
                "slot_index": int(index),
                "entity_id": int(entity_id),
                "entity_name": f"entity:{world_index}:{entity_id}",
                "formation_role_id": "Unspecified",
                "target_owner_name": "",
            }
            for index, (world_index, entity_id) in enumerate(self._entity_keys)
        )

    def air_scripted_observations(
        self,
        *,
        mode: str | None = None,
        ils: Mapping[EntityKey, Sequence[float]] | None = None,
        mission_facts: Mapping[EntityKey, Mapping[str, Any]] | None = None,
        max_contacts: int = 8,
        max_rwr: int = 8,
    ) -> tuple[dict[str, Any], ...]:
        """Build neutral Air observations from native facade state."""
        self._require_ready()
        from .air.observation import AIR_SCRIPTED_MISSION_MODE, build_air_scripted_observation

        mission_mode = AIR_SCRIPTED_MISSION_MODE if mode is None else mode

        current = self.snapshot()
        commands = self.read_command_chain()["mission_commands"]
        ils_by_key = {} if ils is None else dict(ils)
        facts_by_key = {} if mission_facts is None else dict(mission_facts)
        return tuple(
            build_air_scripted_observation(
                observation,
                instrument,
                commands[index] if index < len(commands) else None,
                mode=mission_mode,
                ils=ils_by_key.get(entity_key, (0.0, 0.0, 0.0, 0.0)),
                mission_facts=facts_by_key.get(entity_key),
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
        unexpected = set(actions).difference(self._entity_keys)
        if unexpected:
            raise KeyError(f"facade batch step targets uncontrolled entities: {sorted(unexpected)}")
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

    def apply_launch_requests(
        self,
        requests: Sequence[Any],
        *,
        diagnostic_only: bool = False,
    ) -> tuple[Any, ...]:
        """Apply raw launch requests only for explicit diagnostics/tests."""

        self._require_ready()
        if not diagnostic_only:
            raise PermissionError(
                "raw launch requests are diagnostic-only; use maintained pilot actions or commands"
            )
        if not isinstance(requests, Sequence) or isinstance(requests, (str, bytes)):
            raise TypeError("facade batch launch requests require a sequence")
        return tuple(self.facade.apply_launch_requests_batch(list(requests)))

    def export_engagement_events(
        self,
        *,
        entity_keys: Sequence[EntityKey] | None = None,
        include_launch_requests: bool = True,
        include_launch_events: bool = True,
        include_damage_reports: bool = True,
        include_effects_events: bool = True,
        include_track_packets: bool = False,
    ) -> Any:
        """Export the declared engagement event packet for controlled entities."""

        self._require_ready()
        keys = self._entity_keys if entity_keys is None else tuple(entity_keys)
        unexpected = set(keys).difference(self._entity_keys)
        if unexpected:
            raise KeyError(f"facade batch engagement export targets uncontrolled entities: {sorted(unexpected)}")
        request = ef_py.EngagementBatchRequest()
        request.refs = self._engagement_refs_for(keys)
        request.include_launch_requests = bool(include_launch_requests)
        request.include_launch_events = bool(include_launch_events)
        request.include_damage_reports = bool(include_damage_reports)
        request.include_effects_events = bool(include_effects_events)
        request.include_track_packets = bool(include_track_packets)
        return self.facade.export_engagement_event_packet(request)

    def evaluate_air_combat_terminal(
        self,
        *,
        own_entity_ids: Sequence[int | EntityKey],
        target_entity_ids: Sequence[int | EntityKey],
        entity_keys: Sequence[EntityKey] | None = None,
    ) -> Any:
        """Evaluate Air terminal state from the facade-owned event packet."""

        if self._world_count > 1:
            bare_ids = [
                value
                for values in (own_entity_ids, target_entity_ids)
                for value in values
                if not isinstance(value, (tuple, list)) or len(value) != 2
            ]
            if bare_ids:
                raise ValueError(
                    "facade batch multi-world terminal evaluation requires world-qualified entity keys"
                )

        from .air.terminal import AirCombatTerminalEvaluator

        packet = self.export_engagement_events(
            entity_keys=entity_keys,
            include_launch_requests=False,
            include_launch_events=True,
            include_damage_reports=True,
            include_effects_events=True,
        )
        return AirCombatTerminalEvaluator().evaluate(
            packet,
            own_entity_ids=own_entity_ids,
            target_entity_ids=target_entity_ids,
        )

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
        return self._refs_for(self._entity_keys)

    @staticmethod
    def _refs_for(keys: Sequence[EntityKey]) -> list[Any]:
        refs = []
        for world_index, entity_id in keys:
            ref = ef_py.WorldEntityRef()
            ref.world_index = world_index
            ref.entity_id = entity_id
            refs.append(ref)
        return refs

    @staticmethod
    def _engagement_refs_for(keys: Sequence[EntityKey]) -> list[Any]:
        refs = []
        for world_index, entity_id in keys:
            ref = ef_py.EngagementEntityRef()
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
