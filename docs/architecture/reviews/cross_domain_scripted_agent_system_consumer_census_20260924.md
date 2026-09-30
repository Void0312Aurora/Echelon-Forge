# Cross-Domain Scripted Agent System Consumer Census — 2026-09-24

Language: English canonical; Chinese companion: not maintained (English-only
review surface).

Document kind: `review`
Lifecycle: `maintained`
Canonical: `docs/architecture/reviews/cross_domain_scripted_agent_system_consumer_census_20260924.md`
Owner: `architecture/cross-domain-agency/reviews`
Last verified: `2026-09-24`
Review basis: baseline `36c2a0ec` on `codex/scripted-agent-system-architecture-plan`,
plus the current source tree in the isolated worktree.

## Scope And Independence

This is the WP0 read-only census for the
[Cross-Domain Scripted Agent System Plan](../work/issues/cross_domain_scripted_agent_system_plan.md).
It inventories current consumers, producers, adapters, contracts, and
operator surfaces related to scripted decision models and playable execution.
It does not change runtime behavior, promote a draft plan to active work, or
authorize a new interface.

The census covers Python, C++, scenario inputs, CLI/visualization surfaces,
tests, and domain-owner boundaries. File locations are evidence of ownership
or use, not proof of capability.

## Findings

### F1 — Neutral scripted execution already exists

The canonical low-level air controllers live under `python/tasking_contracts`:

| Surface | Evidence | Current role | Boundary |
| --- | --- | --- | --- |
| `BaseScriptedController` | `python/tasking_contracts/air/execution/base_controller.py` | shared controller state/action helpers | low-level execution only |
| takeoff | `python/tasking_contracts/air/execution/takeoff.py` | instrument/mission driven takeoff | air specialization |
| stable flight | `python/tasking_contracts/air/execution/stable_flight.py` | heading/altitude/speed stabilization | air specialization |
| landing | `python/tasking_contracts/air/execution/landing.py` | ILS/final/rollout control | air specialization |
| mission vocabulary | `python/tasking_contracts/common/mission_defs.py` | phase and command mapping | tasking vocabulary |
| phase execution | `gym_envs/leader_env_parts/scripted_exec.py` | switches the three controllers | environment adapter |

The matching `python/rl/control/*.py` modules are compatibility shells that
re-export the neutral implementations. Creating another low-level scripted
controller package would duplicate maintained behavior and violate the
repository complexity rule.

### F2 — A narrow neutral runtime seam exists, but it is not a full Agent Runtime

`python/tasking_contracts/common/runtime_contract.py` defines a stdlib-only
`ScenarioLoaderRuntime` protocol for observation, instrument, time-step,
position, command, missile, task order, leader intent, mission command, and
pilot report access. `bridge_views.py` provides loader-owned views and keeps
profile-specific adapters in `python.rl`.

This is a reusable runtime seam for the future scripted line. It does not yet
provide agent identity, role lifecycle, decision cadence, belief provenance,
termination ownership, roster routing, or a complete independent playable
loop.

### F3 — The compiled policy contract is the current authority for role and intent shape

`src/runtime/contracts/policy_contracts.h` and
`src/interfaces/python/bindings_runtime_policy.cpp` expose:

- `AgentRole`
- `DecisionBelief`
- `ActionIntentPacket`
- `CoordinationIntentPacket`
- `ActionHoldPolicy`
- authority scopes and action-interface descriptors

The five `AgentRole` fields and the intent merge/hold semantics are already
compiled and bound. A new scripted abstraction must wrap or extend these
contracts rather than define a second Python-only authority model.

### F4 — The Python Agency Registry is declarative and neutral

`python/tasking_contracts/common/agency_registry.py` is a pure declaration layer with
no `ef_py`, `python.rl`, or `gym_envs` import. It records roles such as:

- `autopilot_controller`
- `flight_lead`
- `scripted_c2`
- `cooperative_director`
- naval and ground command identities

The registry is suitable as vocabulary and census input. It does not yet
instantiate or schedule decision models, so it cannot be treated as a full
script registry.

### F5 — RL-adjacent adapters still own several maintained seams

`python/rl/runtime/agent_shim.py` contains provenance labels, maintained versus
diagnostics-only status, action-intent metadata, and policy-route construction.
`python/rl/tasking/leader_tasking.py` owns the scripted C2/leader phase
implementation and imports `ef_py` plus the RL tasking bridge.

These are real entanglement points. They cannot be moved by path renaming
alone because current bridge/profile dispatch and reverse-dependency rules are
part of the maintained architecture. The next contract slice must start with
a consumer map and equivalence tests, not a bulk move.

### F6 — Current scripted C2 and low-level execution are separate roles

`gym_envs/leader_env.py` documents that the leader policy emits high-level
command adjustments while a scripted or frozen execution backend flies the
aircraft. `RuleBasedLeaderPhaseManager` and `ScriptedC2TaskManager` therefore
belong to mission/C2 and command-chain roles; they are not platform autopilots.

The current implementation also declares a maintained own-ship World Truth
read in `leader_tasking.py`. That is an adjudicated doctrine exception and must
remain explicitly labeled if the new system reuses it.

### F7 — Scripted opponent and scripted playable unit have different evidence levels

`examples/agents/red_agent.py` is a deterministic air-combat opponent. It uses
kernel position geometry, direct command writes, and direct missile firing,
with agent observations used for contact and firing gates. Its correct current
labels are demo/opponent/diagnostic baseline. It is not automatically a
maintained sensor-only pilot.

`gym_envs/scenario_loader/behavior_runtime/scripted_opponents.py` is the
scenario/runtime adapter that constructs and updates those opponents. It is a
valid integration seam for hostile fixtures, not a complete cross-domain
script registry.

### F8 — Cooperative director and roster routing are reusable, RL-adjacent infrastructure

`python/rl/runtime/world_batch/cooperative_director.py` and
`python/rl/runtime/cooperative_world_batch_vec_env.py` already route active
roster members, `policy_route`, formation metadata, mission commands, leader
intents, and pilot reports through a shared world step.

This is the right multi-unit runtime substrate. The current gap is a domain-
neutral scripted decision source and a playable operator path. A new
domain-specific two-unit runtime is unnecessary.

### F9 — Scenario, evaluation, and visualization surfaces are fragmented

| Surface | Current evidence | Status |
| --- | --- | --- |
| Scenario declarations | `scripted_agent`, `is_agent`, active/cooperative roster, `policy_route` | partially reusable; legacy first `agent_id` remains |
| Task evaluation | `tools/eval/task_eval_driver.py` scripted backend builders | air execution-focused |
| Visualization | `examples/viz/runtime/viz_session.py` scripted execution and leader backend | cooperative `--scripted` rejected; leader `--scripted` ignored |
| Training configs | frozen execution scripted baseline and active RL residual configs | RL-oriented configuration surface |
| Behavior runtime | scripted red opponent adapter | scenario-owned opponent only |

The system lacks one scenario-declared, role-aware entry point that can run a
complete scripted lifecycle without a training config or checkpoint.

### F10 — Domain maturity places a hard capability boundary

| Domain | Maintained current surface | Scripted-system implication |
| --- | --- | --- |
| Air | flight execution, mission/C2, air-combat fixtures, cooperative runtime | first complete playable vertical slice |
| Naval | N4 tasking/contact/reporting, screen/station/recovery fixtures | bounded playable slice only |
| Ground | native identity and static task/status shells | common lifecycle bootstrap; no full playable claim |
| Joint | common command, authority, service-profile carriers | owns shared vocabulary, not domain execution |

## Dependency And Ownership Map

```text
src/runtime/contracts/policy_contracts.h
        │ compiled AgentRole / Intent / Hold / Belief authority
        ▼
src/interfaces/python/bindings_runtime_policy.cpp
        │
        ├── python/tasking_contracts/common/agency_registry.py
        ├── python/rl/runtime/agent_shim.py
        └── python/rl/runtime/world_batch/adapter.py

python/tasking_contracts  <── gym_envs
        ▲                         │
        └──────── python.rl ──────┘

python/tasking_contracts
        ├── neutral low-level air controllers
        ├── ScenarioLoaderRuntime protocol and bridge views
        └── agency vocabulary

python.rl.tasking / python.rl.profile / python.rl.runtime
        ├── profile dispatch and scripted C2
        ├── world-batch and cooperative director
        └── RL-facing adapters and training entry points

examples / tools / scenarios / tests
        └── operator, fixture, evaluation, and compatibility consumers
```

The neutral direction is already enforced for low-level scripted controllers.
The remaining RL-adjacent seams are genuine profile/runtime entanglements and
need bounded migration decisions.

## Missing Or Unresolved Consumers

1. No independent role-aware script registry instantiates a complete lifecycle.
2. No common lifecycle contract covers reset, observation, decision, intent,
   action, report, termination, and replay for all supported domains.
3. No scenario capability manifest distinguishes `baseline`, `demo`,
   `playable`, `realistic`, and `diagnostics-only` at runtime.
4. Legacy first-agent compatibility remains visible beside active rosters.
5. Cooperative visualization has no scripted operator path.
6. `ScriptedC2TaskManager` retains a declared own-ship truth exception.
7. Ground has no admitted movement/sensing/effects runtime, so its scripted
   path cannot yet receive a full playable label.
8. No cross-domain evidence gate proves single-world/batch parity for scripted
   decisions.

## WP0 Disposition

WP0 is sufficient to constrain the next slice:

1. Reuse `python/tasking_contracts` and the compiled policy contracts.
2. Do not create a parallel `ScriptedAgent` hierarchy beside existing neutral
   contracts.
3. Keep `python/rl` profile/runtime modules as adapters until a specific
   consumer census authorizes a migration.
4. Build the first implementation slice around a role-aware scripted registry
   and a complete Air single-unit lifecycle.
5. Add Naval and Ground through capability-gated domain adapters.
6. Treat the existing red opponent as a separate demo/diagnostic route.

## Verdict

Advisory WP0 review. The evidence is sufficient to start a bounded WP1 contract
placement and Air vertical-slice design. It is not evidence that the project
already has a complete cross-domain playable scripted-agent system.

## Follow-up Routes

- [Cross-domain Scripted Agent System Plan](../work/issues/cross_domain_scripted_agent_system_plan.md)
- [Simulation system architecture standard](../standards/simulation_system_architecture_design.md)
- [Truth-leak inventory](../reference/t8_g4_truth_leak_inventory.md)
- [Naval owner boundary](../../domains/naval/README.md)
- [Ground owner boundary](../../domains/ground/README.md)
