# Simulation System Architecture Design

Navigation:

- Architecture index: [README.md](README.md)
- Chinese companion: [simulation_system_architecture_design.zh.md](simulation_system_architecture_design.zh.md)
- Prior layering plan: [system_layering_and_engine_encapsulation_plan.md](system_layering_and_engine_encapsulation_plan.md)
- Performance follow-up: [architecture_and_performance_research_followup.md](architecture_and_performance_research_followup.md)
- Task execution entry: [../../task/simulation_architecture/README.md](../../task/simulation_architecture/README.md)

Status: `2026-05-19` strict architecture baseline.

This document is the architecture authority for the maintained simulation
system shape. It turns the earlier layering and performance research documents
into stricter ownership rules, a canonical semantic lifecycle, a multi-rate
execution graph model, and the domain extension model that future task sheets
should follow.

It is not an implementation freeze. Concrete code work still needs a scoped
task plan with acceptance criteria.

## 1. Design Thesis

Echelon Forge should be organized around one canonical simulation lifecycle and
a clocked execution graph, not around vertical service branches such as
`air stack`, `naval stack`, or `weapon stack`.

Domain-specific behavior should enter the lifecycle through explicit model
families and stage contracts:

- platform families
- tasking and doctrine families
- sensor, track, and data-link families
- launcher and mount families
- munition, seeker, guidance, fuze, effects, and damage families
- backend families for CPU, GPU, reduced-fidelity, or external FDM execution

The project ceiling is set by how stable these contracts and scheduling rules
are. A local weapon, naval, or air feature may be useful, but it should not
create a private end-to-end runtime path.

## 2. Architecture Laws

These rules are normative for new architecture work:

1. The maintained frontend depends on `runtime/facade`, not on raw
   `WorldBatchRuntime`, `SimulationKernel`, Flecs entities, or implementation
   ordering.
2. Authoritative state lives in the compiled simulation or physics backend.
   Python and other frontends may keep mirrors, but mirrors are partial,
   delayed, and non-authoritative.
3. `components/` and `runtime/contracts/` define data contracts. They do not
   own per-tick behavior.
4. `systems/` mutates ECS state during scheduled stages. It does not define new
   DTOs, own world lifecycle, or expose external APIs.
5. `models/` owns replaceable behavior implementations. It does not register
   ECS systems, bind Python, or parse mission JSON.
6. `content/` describes static scenario, unit, and configuration content. It
   does not own runtime behavior.
7. `runtime/facade` exposes use-case request and result APIs. It must not copy
   every low-level kernel method upward.
8. `interfaces/` and Python adapters translate formats. They do not own
   simulation semantics.
9. GPU and device-resident paths are backend capabilities, not alternate public
   truth paths. CPU exact semantics remain the baseline until a backend parity
   plan says otherwise.
10. Any domain extension must declare which pipeline stages it participates in,
    what packets it consumes and produces, and which validation proves it did
    not bypass the canonical lifecycle.
11. The `P0-P10` table is semantic, not a forced equal-step linear executor.
    Runtime execution should be modeled as a multi-rate temporal DAG whose
    feedback crosses explicit state or event boundaries.

## 3. Target Layer Model

```mermaid
flowchart TD
    FE["Frontends\ntraining, evaluation, visualization, tools"] --> AD["Adapters\nPython, CLI, future service protocols"]
    AD --> RF["Runtime Facade\nstable request/result API"]
    RF --> SE["Simulation Engine\nworlds, stages, command/tasking, missions, diagnostics"]
    SE --> PE["Physics Engine\ntruth-state propagation, integration, backend state"]
    SE --> DM["Domain Model Families\nplatform, sensor, weapon, effects, doctrine"]
    PE --> DM
    SE --> CT["Contracts and Content\nDTOs, schemas, scenario/unit data"]
    RF --> CT
    AD --> CT
    FE --> CT
    PE --> CT
```

The model refines the earlier
`frontend adapters -> runtime facade -> simulation engine -> physics engine -> model backends`
plan. The important addition is that domain behavior is a set of model families
attached to the shared lifecycle, not separate runtime stacks.

## 4. Canonical Semantic Lifecycle

Every maintained scenario step should be explainable through these semantic
stages. Some scenarios can skip stages with empty packets, but they should not
invent a parallel lifecycle.

This table does not require all stages to execute once per outer step, nor does
it require identical `dt`. It defines ownership, packet vocabulary, and
explainability order. The actual runtime schedule is defined by the temporal
DAG in the next section.

| Stage | Owner | Inputs | Outputs | Must not own |
|-------|-------|--------|---------|--------------|
| `P0 ContentCompile` | `content/`, adapters, facade setup | scenario files, unit data, backend capability requests | typed setup packets, content ids | per-tick behavior |
| `P1 WorldSetup` | `runtime/facade`, `core/engine` | setup packets, seeds, terrain/environment refs | world batch, entity refs, initial state | frontend cache policy |
| `P2 TaskingIntent` | `components/tasking`, `core/mission` | task orders, leader intents, doctrine content | tasking state, authority state | low-level actuation |
| `P3 CommandDelivery` | `components/command`, command-link systems | command packets, link QoS, latency/drop state | delivered commands, pending queues | physics or sensor behavior |
| `P4 PlatformControl` | control models, platform systems | commands, platform state, autopilot/control laws | force/torque intents, actuator state | world lifecycle |
| `P5 PhysicsStep` | physics systems/backends | physical state, environment, force/torque inputs | updated truth state, physics traces | mission JSON, reward, gym API |
| `P6 SenseTrackLink` | sensor, track, EW, data-link systems/models | truth state, emissions, environment, link state | tracks, detections, comm packets | weapon effects or damage |
| `P7 FireControlLaunch` | simulation engine and weapon launch models | tracks, ROE, authority, launcher state | launch events, munition entities | closed-loop munition guidance |
| `P8 MunitionLifecycle` | guidance, seeker, fuze models, combat systems | munition state, target tracks/truth, environment | terminal events, misses, fuze events | platform mission ownership |
| `P9 EffectsDamage` | effects models and damage systems | hit/fuze events, warhead/effects content | damage reports, kill state, subsystem effects | observation packing |
| `P10 ObservationExport` | facade, observation systems, diagnostics | state snapshots, reports, traces | observation packets, debug traces, exports | authoritative state mutation |

The stage names are architecture vocabulary. The repository may continue to use
existing function and file names while it migrates, but new docs and tests
should map local behavior back to this table.

## 5. Temporal DAG Execution Model

The execution model is a temporal directed acyclic graph for each scheduling
window, with feedback carried through versioned state and timestamped events.

In a single scheduling window:

```text
State[t] + EventQueue[t]
  -> stage-node DAG
  -> writes, emitted events, diagnostics
  -> State[t + dt] + EventQueue[t + dt...]
```

The graph inside the window must be acyclic. Feedback such as
`damage -> platform capability -> sensor quality -> fire control` is legal only
when it crosses a state-store version, event queue timestamp, or explicit
barrier.

Edges inside a scheduling window are derived from data dependencies, not drawn
by preference. A same-window edge `A -> B` is legal when `B.read_set` intersects
`A.write_set` and `A` publishes that write inside the same window. If `B` reads
only a committed `StateStore` snapshot from a previous window, that is
cross-window feedback, not a same-window DAG edge. This rule keeps the temporal
DAG from becoming a disguised linear pipeline.

Execution graph concepts:

| Concept | Meaning |
|---------|---------|
| `StageNode` | A scheduled unit of work, such as command delivery, control law, sensor scan, fire-control, guidance update, damage apply, or observation export. |
| `StateStore` | Authoritative state with versioning. It may be host-owned, backend-owned, or partially synchronized. |
| `EventQueue` | Delayed or timestamped events such as command arrival, launch, fuze trigger, damage application, and report export. |
| `ClockDomain` | Cadence rule for a node, such as fixed-rate physics, sensor scan interval, command-link tick, event-driven damage, or facade-requested export. |
| `Barrier` | Consistency boundary where writes become visible to later nodes or later windows. |

State versioning starts coarse but must leave room for shards. A single global
state version is acceptable for early CPU-only smoke and diagnostics, but any
resident-state or partial-sync backend must support domain-sharded versions,
for example physics state, tasking state, track state, damage state, and
observation export state. Stage nodes should therefore name the state shard they
read or write whenever that is known.

Events are ordered deterministically by `(timestamp, priority, event_id)`.
`timestamp` decides simulated time, `priority` is fixed by event family, and
`event_id` is generated deterministically from the producing node and local
sequence. Insert order must not be the only tie-breaker for maintained
simulation behavior because parallel stage nodes and mixed CPU/GPU producers
would make replay fragile.

Clock domains use nested triggering by default. The base tick owns the outer
deterministic schedule, and lower-rate nodes run on declared multiples or
declared schedule slots. Independent clock domains are allowed only when a
freeze plan specifies their deterministic merge policy and event ordering at
barriers.

Every maintained stage node should declare:

| Field | Requirement |
|-------|-------------|
| `semantic_stage` | Which `P0-P10` stage or stages this node belongs to. |
| `read_set` | State, packets, snapshots, or events the node reads. |
| `write_set` | State, packets, events, or diagnostics the node writes. |
| `clock_domain` | How often or under which event condition the node runs. |
| `latency_policy` | Whether outputs are same-window, next-window, delayed, or link-latency controlled. |
| `sync_policy` | Host-owned, backend-owned, partial sync, observation-only sync, or explicit export. |

Typical clock domains:

| Stage family | Expected cadence |
|--------------|------------------|
| Physics integration | Fixed high-rate inner loop or backend substep. |
| Platform control | Control-rate update, often slower than physics but faster than tasking. |
| Sensor and track | Sensor-specific scan intervals plus track-fusion cadence. |
| Command and data link | Link tick plus latency/drop event scheduling. |
| Fire control | Track/ROE/authority-driven, usually lower rate than physics. |
| Munition lifecycle | Guidance-rate and fuze/event-driven hybrid. |
| Effects and damage | Event-driven, with delayed reports when needed. |
| Observation export | Facade request, episode boundary, diagnostic trigger, or batch collector cadence. |

The design rule is:

```text
P0-P10 = semantic lifecycle
Temporal DAG = execution scheduler
StateStore/EventQueue = feedback boundary
Contracts = packet/state/event vocabulary
```

## 6. Contract Taxonomy

The facade and adapters should converge on typed packets with clear ownership:

| Contract family | Purpose | Long-term owner |
|-----------------|---------|-----------------|
| `ScenarioSpec` / `ContentSpec` | Static scenario and content description | `content/` plus adapter schemas |
| `WorldSetupRequest` / `WorldSetupResult` | Batch reset and entity creation | `runtime/contracts` |
| `TaskingPacket` | Mission intent, authority, relationships, task state | `components/tasking` and `runtime/contracts` |
| `CommandPacket` | Deliverable execution commands and link behavior | `components/command` and `runtime/contracts` |
| `TrackPacket` | Sensor/track/data-link output | `components` or `runtime/contracts` after ownership review |
| `LaunchRequest` / `LaunchEvent` | Fire-control and launcher boundary | `runtime/contracts` plus weapon components |
| `MunitionState` | Munition lifecycle state | combat/weapon components |
| `EffectsEvent` / `DamageReport` | Hit, fuze, damage, and kill reporting | effects model plus combat components |
| `ObservationPacket` | Frontend-facing state export | `runtime/facade` contracts |
| `DiagnosticsTrace` | Explainability, replay, and validation trace | `core/engine` and facade contracts |

`MissionCommand` remains a compatibility aggregation point, not the preferred
future shape for shared semantics. Future work should move toward narrower
tasking, command, fire-control, and observation packets instead of extending a
flat all-domain command object.

## 7. Domain Extension Model

Domain extensions must be stage-local and contract-driven.

Allowed extension families:

- `PlatformFamily`: aircraft, ship, submarine, future ground or space units.
- `MotionFamily`: aero, ship motion, submarine motion, future ground mobility.
- `SensorFamily`: radar, visual, sonar, EW, passive detection.
- `LinkFamily`: command link, data link, relay, degraded communication.
- `LauncherFamily`: rail, cell, pylon, tube, close-in mount, virtual launcher.
- `MunitionFamily`: missile, shell, torpedo, bomb, decoy, future effectors.
- `GuidanceFamily`: PN, command guidance, active seeker, passive seeker,
  terminal homing, reduced surrogate.
- `EffectsFamily`: blast, fragmentation, penetration, subsystem damage,
  soft-kill, mission kill.
- `DoctrineFamily`: task templates, ROE, authority delegation, engagement
  policy.

Each extension must document:

1. stage coverage,
2. required components and content records,
3. consumed and produced packets,
4. stage-node read/write sets,
5. clock domain and latency policy,
6. facade visibility,
7. parity or regression tests,
8. compatibility behavior for existing Python callers.

An extension that needs a new lifecycle stage should first update this design
or a derived freeze plan.

## 8. Backend And Performance Policy

Performance work must preserve the same semantic lifecycle.

- CPU exact execution is the semantic baseline for maintained behavior.
- CUDA helpers should attach through facade/backend packets, especially for
  visual, observation, broadphase, flight shaping, and future resident-state
  paths.
- Device-resident state is allowed only behind contracts that can describe
  host-owned state, backend-owned state, partial sync, and observation-only
  sync.
- Device-resident nodes must declare when host-visible state is synchronized
  and whether observations are snapshots, partial views, or explicit exports.
- Exact GPU world-step work is not a maintained replacement until parity,
  ownership, and sync rules are frozen.
- Rust remains a possible future service or serialization boundary, not a
  near-term replacement for the C++ simulation backend.

The key performance rule is simple: move ownership and data residency downward
without creating a second semantic path.

## 9. Weapon And Engagement Pilot Slice

The weapon line is the best first architecture pilot because it crosses the
whole semantic lifecycle and exercises temporal feedback:

`tasking -> command delivery -> sensor/track -> fire control -> launcher -> munition -> seeker/guidance/fuze -> effects -> damage -> observation`

The pilot should avoid separate `air weapon` and `naval weapon` runtime stacks.
Instead it should prove that one engagement lifecycle can host different
launcher and munition families while using stage nodes with different clock
domains.

Initial architecture deliverables should be:

1. launcher/mount contract and content shape,
2. launch event and munition lifecycle packet,
3. seeker/guidance/fuze/effects split,
4. damage report contract that can later replace ad hoc HP-only reporting,
5. observation and diagnostics export for launch, intercept, miss, and damage.
6. clock-domain and event-queue rules for command delivery, seeker scan,
   guidance update, fuze trigger, and damage application.

This pilot is useful only if it exercises at least two platform families, for
example aircraft pylon launch and naval mount launch.

## 10. Validation Gates

New architecture work should pass these gates before becoming the maintained
path:

1. Docs name the stage, owner, consumed packets, and produced packets.
2. Docs name the stage-node read/write sets, clock domain, latency policy, and
   sync policy.
3. Public access goes through facade request/result APIs or a documented
   compatibility adapter.
4. Architecture tests prevent frontends from reaching raw runtime owners.
5. Include and build boundaries do not introduce reverse dependencies.
6. CPU semantic behavior remains the reference for any backend acceleration.
7. Cross-domain smoke tests show that domain extensions use the shared
   lifecycle and clocked execution model.
8. Diagnostics can explain where a command, launch, munition, effect, or damage
   report entered and left the pipeline.

Local Windows work may stop at build/import/smoke validation when RL training
dependencies are unavailable, but the contracts should still be shaped for
future batch and training use.

## 11. Relationship To Existing Documents

This document does not delete the earlier plans. It repositions them:

- [system_layering_and_engine_encapsulation_plan.md](system_layering_and_engine_encapsulation_plan.md)
  remains the source for layer motivation and engine encapsulation background.
- [architecture_and_performance_research_followup.md](architecture_and_performance_research_followup.md)
  remains the source for performance route ordering and backend trade-offs.
- [../runtime_facade/runtime_facade_contract_plan.md](../runtime_facade/runtime_facade_contract_plan.md)
  remains the facade contract input.
- [../../task/common_air_naval/README.md](../../task/common_air_naval/README.md)
  remains the historical task line for the `common / air / naval` split.
- [../../task/simulation_architecture/README.md](../../task/simulation_architecture/README.md)
  is the execution subproject for turning this architecture into scoped work.

Future architecture task sheets should cite this document first, then cite the
older documents only for rationale or evidence.
