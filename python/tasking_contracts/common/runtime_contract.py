"""Structural runtime contract for the ``ScenarioLoader.sim`` seam (this iteration).

``gym_envs.scenario_loader.core.ScenarioLoader`` receives a runtime handle at
construction (``ScenarioLoader(sim_kernel)``) and stores it as ``self.sim``.
On the maintained training path that handle is
``python.rl.runtime.world_batch.adapter._ScenarioLoaderRuntimeProxy`` (built
exclusively by ``RuntimeFacadeAdapter._scenario_loader_runtime`` and injected
via ``ScenarioLoader(self._scenario_loader_runtime(int(index)))``); raw
``ef_py.SimulationKernel`` injection is a test-only convenience that lives
under ``tests/`` and ``python/testing/`` (single-kernel contract harnesses).
This module gives that seam a name: a pure-stdlib structural
``typing.Protocol`` that both the maintained proxy and the test-only raw
kernel satisfy, without this neutral layer importing either side.

Layering (G2): ``gym_envs -> python.tasking_contracts <- python.rl``. This
module imports **stdlib ``typing`` only** — no ``ef_py``, no ``numpy``, no
``gym_envs``, no ``python.rl`` — so it is dependency-terminal. The boundary is
enforced by ``tests/architecture/tasking_contracts/test_tasking_contracts_boundary.py``
and by the stdlib-only import gate in
``tests/architecture/tasking_contracts/test_scenario_loader_runtime_contract.py``.

Census: maintained accesses through the ``ScenarioLoader.sim`` handle
=====================================================================

Every maintained method used through the loader's ``sim`` handle, as of this
iteration's census (file:line values are the census snapshot; the conformance
test's fixture re-verifies each caller by stable text needle so drift is
caught without depending on line numbers).

Access routes to the handle
---------------------------

R1. Direct ``self.sim`` on the loader (TL13 read seam):
    ``gym_envs/scenario_loader/core.py:1010`` and ``:1019``.
R2. ``resolve_loader_runtime_sim(loader)`` (= ``getattr(loader, "sim")``),
    ``python/rl/runtime/world_batch/runtime_support.py:8-10``; feeds
    ``loader.compute_full_step(obs, sim, ...)`` and
    ``build_step_info(loader, sim, ...)``.
R3. ``LoaderOwnedRuntimeView`` / ``LoaderOwnedScriptedOpponentKernelView``
    (``python/tasking_contracts/bridge_views.py``), which resolve
    ``getattr(loader, "sim")`` lazily and duck-call methods via
    ``call_optional``/``supports``.
R4. ``loader.sim`` re-exposed as ``env.unwrapped.sim``:
    ``python/rl/runtime/leader_world_batch_runtime.py:50``
    (``_LeaderExecutionWorldView.sim``) and
    ``python/rl/runtime/world_batch/runtime_access.py:20``
    (``WorldBatchVecEnvAccess.sim``), consumed by ``gym_envs/leader_env_parts``
    and ``python/rl/control/wrappers.py``.

Required methods (the protocol below; the maintained proxy implements all 11)
-----------------------------------------------------------------------------

1.  ``get_agent_observation(entity_id)`` —
    gym_envs/scenario_loader/core.py:1010 (R1);
    gym_envs/scenario_loader/execution_runtime/mainline.py:376 (R2);
    gym_envs/universal_env_parts/info.py:62,85 (R2);
    python/tasking_contracts/bridge_views.py:149-150,207-208 (R3);
    gym_envs/observation_view.py:156 ``support_agent_observation`` used by
    gym_envs/scenario_loader/mission_observation.py:490 (R3);
    gym_envs/leader_env_parts/execution_runtime/policy_runtime.py:175 (R4).
2.  ``get_instrument_state(entity_id)`` —
    gym_envs/scenario_loader/core.py:1019 (R1);
    gym_envs/scenario_loader/execution_runtime/mainline.py:382 (R2);
    gym_envs/universal_env_parts/info.py:60 (R2);
    python/tasking_contracts/bridge_views.py:152-153 (R3);
    gym_envs/leader_env_parts/execution_runtime/policy_runtime.py:170 (R4).
3.  ``get_time_step()`` —
    python/tasking_contracts/bridge_views.py:118-122 ``read_time_step_s`` and
    :296-298 ``resolve_loader_time_step`` (R3);
    python/rl/control/wrappers.py:573,
    gym_envs/leader_env_parts/runtime_facade.py:194,387,405,
    gym_envs/leader_env_parts/scripted_exec.py:33,
    gym_envs/leader_env_parts/decision_runtime/observations.py:168 (R4).
4.  ``is_unit_active(entity_id)`` —
    python/tasking_contracts/bridge_views.py:146-147,201-202 (R3);
    gym_envs/scenario_loader/behavior_runtime/naval_screen.py:101 (R3);
    gym_envs/scenario_loader/reward_runtime/air_combat.py:1480-1482
    (hasattr-guarded, via observation_view.unit_active) (R2).
5.  ``get_unit_position(entity_id)`` —
    python/tasking_contracts/bridge_views.py:140-141,204-205 (R3);
    gym_envs/scenario_loader/behavior_runtime/naval_screen.py:82 (R3);
    gym_envs/observation_view.py:161 ``support_unit_position`` used by
    gym_envs/scenario_loader/mission_observation.py:515 (R3).
6.  ``set_command(entity_id, heading, speed, altitude)`` —
    python/tasking_contracts/bridge_views.py:155-168,210-224 (R3; naval-screen
    station hold and scripted opponents).
7.  ``fire_missile(entity_id, target_id)`` —
    python/tasking_contracts/bridge_views.py:170-174,226-230 (R3; scripted
    opponents).
8.  ``set_mission_command(entity_id, command)`` —
    python/tasking_contracts/bridge_views.py:136-138 (R3);
    ``supports("set_mission_command")`` probe at
    gym_envs/scenario_loader/behavior_runtime/command_chain.py:70.
9.  ``set_task_order(entity_id, order)`` —
    python/tasking_contracts/bridge_views.py:124-126 (R3).
10. ``set_leader_intent(entity_id, intent)`` —
    python/tasking_contracts/bridge_views.py:128-130 (R3).
11. ``set_pilot_report(entity_id, report)`` —
    python/tasking_contracts/bridge_views.py:132-134 (R3).

Optional, absence-tolerated methods (NOT part of the protocol)
--------------------------------------------------------------

Every caller below probes with ``hasattr``/``call_optional`` and takes a
defined fallback when the handle lacks the method. The maintained proxy
deliberately omits them (its ``__getattr__`` raises ``AttributeError``), so on
the maintained path these branches are dead and only the test-only raw kernel
exercises them:

* ``get_unit_velocity(entity_id)`` — bridge_views.py:143-144, consumed by
  naval_screen.py:83 (falls back to None -> reference motion unavailable).
* ``get_unit_messages(entity_id)`` — reward_runtime/naval.py:126,288
  (hasattr-guarded) and observation_view.py:169-171
  ``support_unit_messages_optional`` used by mission_observation.py:502
  (call_optional default ``[]``).
* ``export_recent_engagement_events()`` — reward_runtime/air_combat.py:462
  (hasattr-guarded, default None).
* ``get_unit_health(entity_id)`` — reward_runtime/objectives.py:53
  (hasattr-guarded).
* ``debug_get_aircraft_damage_state(entity_id)`` — air_combat.py:706
  (hasattr-guarded diagnostic).
* ``debug_get_ground_contact_state(entity_id)`` — air_combat.py:714,726
  (hasattr-guarded diagnostic).

Raw-kernel-only quarantine (NOT part of the protocol)
-----------------------------------------------------

``apply_loader_owned_world_layout_to_kernel`` (bridge_views.py:241-248) hands
``loader.sim`` to ``python.scenario.runtime.apply_world_layout_to_kernel``;
it is reached only from ``load_instantiated_scenario``
(gym_envs/scenario_loader/loading.py:364), i.e. the raw single-kernel load
path. The maintained world-batch path loads via ``load_prepared_world``
(python/rl/runtime/world_batch/vec_env.py:488) and applies layouts through the
facade (``RuntimeFacadeAdapter.apply_world_layout``), never through
``loader.sim``.

Open questions recorded by the census (no behavior change made)
---------------------------------------------------------------

* ``LoaderOwnedRuntimeView.get_unit_velocity`` and the reward-runtime
  optionals have no maintained (facade/proxy) implementation, so naval-screen
  reference motion, report-chain reads, engagement-event shaping and
  damage-state diagnostics silently degrade on the maintained path. Whether
  the proxy should grow facade-backed equivalents is a follow-up decision,
  not part of this typing-only slice.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


#: Methods every maintained ``ScenarioLoader.sim`` handle must provide
#: (mirrors :class:`ScenarioLoaderRuntime`; used by the conformance test).
SCENARIO_LOADER_RUNTIME_REQUIRED_METHODS: frozenset[str] = frozenset(
    {
        "get_agent_observation",
        "get_instrument_state",
        "get_time_step",
        "is_unit_active",
        "get_unit_position",
        "set_command",
        "fire_missile",
        "set_mission_command",
        "set_task_order",
        "set_leader_intent",
        "set_pilot_report",
    }
)

#: Duck-typed optionals: probed via ``hasattr``/``call_optional`` with a
#: defined fallback; the maintained proxy deliberately omits every one.
SCENARIO_LOADER_RUNTIME_OPTIONAL_METHODS: frozenset[str] = frozenset(
    {
        "get_unit_velocity",
        "get_unit_messages",
        "export_recent_engagement_events",
        "get_unit_health",
        "debug_get_aircraft_damage_state",
        "debug_get_ground_contact_state",
    }
)


@runtime_checkable
class ScenarioLoaderRuntime(Protocol):
    """Structural type of the ``ScenarioLoader.sim`` seam.

    Satisfied structurally by the maintained facade-backed
    ``_ScenarioLoaderRuntimeProxy`` (python/rl/runtime/world_batch/adapter.py)
    and, on explicitly test-only paths, by a raw ``ef_py.SimulationKernel``.
    Signatures mirror the maintained proxy exactly; the conformance test
    compares them member-for-member.
    """

    def get_agent_observation(self, entity_id: int) -> Any: ...

    def get_instrument_state(self, entity_id: int) -> Any: ...

    def get_time_step(self) -> float: ...

    def is_unit_active(self, entity_id: int) -> bool: ...

    def get_unit_position(self, entity_id: int) -> tuple[float, float, float]: ...

    def set_command(
        self,
        entity_id: int,
        target_heading_deg: float,
        target_speed_mps: float,
        target_altitude_m: float,
    ) -> None: ...

    def fire_missile(self, entity_id: int, target_id: int) -> int: ...

    def set_mission_command(self, entity_id: int, command: Any) -> None: ...

    def set_task_order(self, entity_id: int, order: Any) -> None: ...

    def set_leader_intent(self, entity_id: int, intent: Any) -> None: ...

    def set_pilot_report(self, entity_id: int, report: Any) -> None: ...


__all__ = [
    "SCENARIO_LOADER_RUNTIME_OPTIONAL_METHODS",
    "SCENARIO_LOADER_RUNTIME_REQUIRED_METHODS",
    "ScenarioLoaderRuntime",
]
