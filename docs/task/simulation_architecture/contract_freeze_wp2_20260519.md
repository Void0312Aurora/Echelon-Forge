# WP2 Contract Freeze

Status: `2026-05-19` contract freeze complete.

Language:

- English canonical: `contract_freeze_wp2_20260519.md`
- Chinese companion: [contract_freeze_wp2_20260519.zh.md](contract_freeze_wp2_20260519.zh.md)

Inputs:

- [simulation system architecture design](../../plan/architecture/simulation_system_architecture_design.md)
- [WP1 pipeline inventory](pipeline_inventory_wp1_20260519.md)
- Read-only code evidence collected for engagement, facade, validation,
  policy, and orchestration surfaces.

This document freezes the architecture contract shape for `WP2`. It does not
implement new runtime code. Its job is to decide which packet families and
stage-node boundaries are maintained contracts, which existing paths are
compatibility adapters, and which follow-on work packages should implement or
validate those decisions.

## 1. Freeze Position

The architecture framework is closed at the simulation, policy-computation, and
test/orchestration layer boundary. `P0-P10` is the canonical semantic
lifecycle, while real execution is a multi-rate temporal DAG. Cross-window
feedback must cross a `StateStore`, `EventQueue`, or explicit scheduling
barrier.

WP2 therefore freezes contract ownership, not a linear executor.

Required rules:

1. New maintained work must target facade-shaped request/result APIs or
   `runtime/contracts` DTOs.
2. `RuntimeFacade::runtime()`, raw `WorldBatchRuntime`, raw `SimulationKernel`,
   and debug APIs remain compatibility or diagnostics escape hatches only.
3. `MissionCommand` remains a compatibility aggregation surface until narrower
   tasking, command, and engagement packets replace the relevant fields.
4. Simulation facts stay owned by the simulation and compiled mission runtime.
   Policy and orchestration may shape rewards, choose observation views, or
   request truncation, but must not become hidden owners of simulation truth.
5. Stage-node contracts must declare `semantic_stage`, `read_set`,
   `write_set`, `clock_domain`, `latency_policy`, `sync_policy`, facade
   visibility, and deterministic event-ordering requirements.

## 2. Contract Families

| Family | Current evidence | Freeze decision | Minimum frozen fields | Facade / compatibility path | Validation gate |
|--------|------------------|-----------------|-----------------------|-----------------------------|-----------------|
| `TrackPacket` | `SystemTrack`, `TrackDatabase`, and `AgentObservation.contacts` already carry fused track data. | Maintained `P6/P10` contract. Raw `ContactList` fallback is compatibility only. | `track_id`, entity correlation policy, source, classification, status, quality, confidence, usability, IFF, source time or update age, snapshot version. | Export through observation/facade packets; do not expose raw track database layout. | Observation tests must verify fused-track fields and fallback labeling. |
| `LaunchRequest` | Launch intent is currently spread across `PilotAction`, `MissionCommand`, ROE gates, and `fire_missile()` arguments. | New `P7` request contract. It separates fire-control intent from munition spawning. | shooter ref, target entity or track ref, launcher station or mount, requested munition family, authority source, requested time, `merge_policy`, request id. | Future facade request/result API; old `fire_missile()` and mission-command fields are compatibility adapters. | Facade-only engagement pilot must submit launch intent without raw runtime access. |
| `LaunchEvent` | Accepted/rejected launch outcome is implicit in kernel launch return value, ammo/cooldown mutation, and spawned munition id. | New `P7` event contract. It is the authoritative launch result. | request id, accepted/rejected, rejection reason, selected launcher, selected munition, ammo delta, cooldown delta, spawned munition id, event time, event id. | Produced by simulation and exported through facade diagnostics/event packet. | Air and naval launch tests must converge on the same event shape. |
| `MunitionLifecyclePacket` | `Missile` and guidance systems already track attacker, target, seeker, guidance cadence, launch time, track memory, fuel, burnout, and fuze state. | Maintained `P8` lifecycle packet with minimal external state. Guidance tuning remains component-internal. | munition id, attacker ref, target ref or track ref, launch event id, active flag, seeker mode, guidance cadence, track memory state, fuel or burnout state, max flight time, fuze state, source time. | Facade diagnostics/export; component state is not a public schema. | A non-RL smoke should observe lifecycle progression after a launch event. |
| `EffectsEvent` | Fuze and effects behavior exists in damage systems and weapon effects models. | New event-driven `P9` effects contract. | munition id, target ref, trigger type, hit/miss/proximity state, detonation or nearest approach time, quality/confidence, effect family. | Simulation event queue and facade diagnostics. | Engagement trace must explain why damage did or did not occur. |
| `DamageReport` | `PlatformDamageState` and effects models update HP, system health, kill flags, fire, flooding, breach, and loss state. | Maintained `P9` report contract. Debug health reads are compatibility only. | target ref, source event id, HP delta, system health delta, platform damage-state delta, mission/mobility/sensor/survivability kill flags, loss-state transition, destroyed flag, report time. | Facade report/export packet; debug damage API remains a test helper only. | Damage report must be visible without raw `SimulationKernel` debug calls. |
| `DiagnosticsTrace` | Observation export exists, but launch/damage explanations are not tied into a single trace. | Maintained trace index, not a full logging system in WP2. | trace id, track id, launch request id, launch event id, munition id, effects event id, damage report id, observation packet version. | Facade diagnostics/export. | One trace must connect launch, lifecycle, effect, damage, and observation. |
| `PlatformControlPacket` | `PilotAction`, control model, and control systems exist, but no narrow facade-level `P4` packet exists. | New `P4` contract candidate. WP2 freezes ownership and timing, while exact control fields may be refined in implementation. | target entity, control source, effective time, validity window, direct-control family, normalized action vector or bound fields, hold policy id. | `ActionIntentPacket` translated by facade/simulation at `P3/P4`; existing `PilotAction` is a compatibility target. | Architecture tests must prevent policy code from mutating raw control state. |
| `ObservationViewSpec` / `ObservationPacket` | Facade already has typed observation request flags and packet vectors; Python still assembles some views directly. | Maintained cross-layer contract. Policy/test owns view schema; simulation/facade owns snapshots and packet builders. | schema version, required fields, optional fields, include flags, source snapshot version, source time, normalization/encoding owner, compatibility rule. | `ObservationBatchRequest` / `ObservationBatchPacket`; Python direct assembly remains compatibility until adapter parity is proven. | Checkpoint/schema rules must reject major-incompatible views. |
| `ActionIntentPacket` / `ActionHoldPolicy` | Execution actions and leader actions exist with different cadences and Python mappings. | Maintained policy-to-simulation contract. | action source, target entity, action family, effective time, validity window, refresh cadence, expiry behavior, hold/interpolation/drop rule, `merge_policy`, credit-latency note. | Facade accepts intent and translates to `P3/P4/P5` consumption points. | Policy cadence must be testable without assuming equal `dt` with physics. |
| `CoordinationIntentPacket` | Cooperative director, leader tasking, and C2 paths produce tasking/command intent outside the simulation DAG. | Maintained cross-layer contract. C2 may consume shared situation and reports, but must not directly author low-level mission commands. | source type, source id, roster, target refs, update clock, produced tasking fields, produced leader-intent fields, `merge_policy`, effective time. | Facade-compatible assignment paths for scripted, learned, and human directors. | Tests must prove coordination writes go through facade/adapter paths. |
| `RewardSpec` / `RewardReport` | C++ episode controller returns reward totals, status vectors, termination reasons, and JSON breakdowns; Python still has fallback shaping paths. | Split contract. Simulation owns facts; policy/test owns shaping and experiment composition. | fact snapshot version, fact terms, shaping terms, reward total, breakdown JSON, owner/source for each term, computation latency. | Facade execution step result is maintained; Python reward fallback is compatibility. | Reward reports must identify fact versus shaping terms. |
| `TerminationSpec` / `EpisodeStatus` | Compiled episode flow returns `terminated`, `truncated`, status vectors, and termination reasons; adapters mirror Gymnasium state. | Split contract. Simulation owns semantic termination; orchestration owns test/training truncation requests. | terminated, truncated, reason, reason source, status vector, source time, snapshot version, reset requested flag. | Facade execution result and episode status mirrors. | Termination/truncation tests must attribute reason source. |
| `EpisodeLifecycleContract` | Episode controller and state already track phase, mission command, waypoint, reward, termination, and reset-related state. | Maintained lifecycle authority. Compiled/facade state is authoritative; Gymnasium and batch APIs mirror it. | agent id, step count, phase, waypoint index, mission command ref or JSON, last reward total, last termination reason, last reward breakdown, reset transition id. | Facade execution result and future episode export packet. | Adapters must not advance private authoritative phase machines. |

## 3. Stage-Node Freeze

The table below freezes the first maintained stage-node vocabulary. It is not a
complete scheduler implementation.

| Stage | Maintained node contract | Read set | Write set | Clock / latency / sync policy | Event ordering |
|-------|--------------------------|----------|-----------|-------------------------------|----------------|
| `P0 ContentCompile` | Content and scenario normalization. | Static content, scenario files, backend capability request. | Content ids, compiled setup packets, default capability shards. | Offline or setup-window only; no per-tick mutation. | Not event-driven in WP2. |
| `P1 WorldSetup` | World, terrain, environment, seed, spawn, and initial state setup. | Compiled content, setup packet, seed, initial environment refs. | Entity refs, world batch refs, initial `StateStore` snapshot. | Setup barrier before simulation windows. | Setup events sort before runtime events. |
| `P2 TaskingIntent` | Mission, leader, and coordination intent ingestion. | Coordination intent, mission plan, roster, prior reports. | Task orders, leader intents, mission-command compatibility fields. | Lower cadence than physics; external inputs injected before the scheduling-window barrier. | Intent events use `(timestamp, priority, event_id)`. |
| `P3 CommandDelivery` | Command link, latency, drop, pending queues, and command materialization. | Tasking/mission command shards, link state, authority state. | Pending command queues, delivered command state, delivery reports. | Event/latency driven; may deliver next window. | Delivery events use deterministic timestamp and priority. |
| `P4 PlatformControl` | Control-command translation and hold policy consumption. | Delivered commands, action intent, platform state, hold policy. | Control inputs, actuator/control state, action validity reports. | Control-rate clock; may consume one policy output across several control ticks. | Control conflicts follow request `merge_policy`. |
| `P5 PhysicsStep` | Kinematics, forces, contacts, and integration. | Control state, physical state, environment. | Updated physical state, contact candidates, capability-affecting state reads for later nodes. | Physics-rate clock with possible substeps; CPU exact path is reference. | Physics outputs commit through state versioning. |
| `P6 SenseTrackLink` | Sensor scan, fusion, datalink, EW, and track snapshots. | Physical state, sensor state, EW/link state, prior tracks. | `TrackPacket`, shared situation, pilot reports, observation-ready track snapshot. | Sensor and link clocks are distinct from physics; snapshots declare source time and version. | Track updates use deterministic timestamp and source priority. |
| `P7 FireControlLaunch` | Fire-control gating, launcher selection, envelope, ammo, cooldown, and launch result. | Track packet, authority state, platform weapon state, launch request. | Launch event, ammo/cooldown state, spawned munition ref, rejection report. | Event-driven or fire-control cadence; same-window only after request barrier. | Launch events use `(timestamp, priority, event_id)`. |
| `P8 MunitionLifecycle` | Guidance, seeker, datalink, fuze arming, and lifecycle state. | Launch event, munition state, target track, environment, datalink. | Munition lifecycle packet, guidance state, fuze/effects trigger candidate. | Guidance, seeker, and fuze clocks may differ; nested triggering is default unless an explicit merge policy is declared. | Lifecycle events preserve launch-event ancestry. |
| `P9 EffectsDamage` | Effects resolution, damage mutation, loss-state transition, and report generation. | Effects event, target state, protection/damage model state. | Damage report, platform damage state, capability degradation, kill/loss events. | Event-driven; feedback to later capability reads crosses state/event barrier. | Damage and kill events sort by timestamp, priority, event id. |
| `P10 ObservationExport` | Snapshot export, facade packet construction, diagnostics trace, and policy/test views. | Committed state snapshot, reports, traces, observation view spec. | Observation packet, diagnostics trace export, mirrored episode status. | Facade-requested, episode-boundary, diagnostic, or batch-collector cadence. | Observation declares source snapshot version and export time. |

## 4. Cross-Layer Freeze

WP2 freezes the interaction between the three top-level layers as follows:

| Boundary | Simulation layer owns | Policy computation layer owns | Test/orchestration layer owns | Required channel |
|----------|-----------------------|-------------------------------|-------------------------------|------------------|
| Observation | Queryable state shards, committed snapshot versions, facade packet builders, diagnostics exports. | `ObservationViewSpec`, field subset, encoding, normalization, masking, stacking, schema version. | Test view selection, assertion views, replay comparison views. | `ObservationBatchRequest` / `ObservationBatchPacket` or documented adapter parity. |
| Action | Command/control ingestion points, validity enforcement, state mutation, deterministic application. | `ActionIntentPacket`, action family, effective time, hold policy, merge policy. | Scripted action injection for tests, seed/replay scheduling. | Facade action/step request, never raw ECS mutation. |
| Coordination | Tasking and command state once accepted into the simulation DAG. | Scripted, learned, or human director output as `CoordinationIntentPacket`. | Scenario-level coordination scripts and validation schedule. | Facade-compatible assignment path before the scheduling-window barrier. |
| Reward | Simulation facts, compiled mission products, damage/kill facts, semantic fact snapshots. | Experiment shaping, curriculum terms, consumer-specific reward composition. | Benchmark reward config and reporting. | `RewardReport` with fact/shaping attribution. |
| Termination | Simulation-semantic `terminated` reasons and authoritative phase. | Policy-visible status mirrors only. | `truncated` requests, max-step or wall-clock policy, reset request. | `EpisodeStatus` and facade execution result. |
| Episode lifecycle | Phase, transition result, reset application, semantic reason. | Mirrors for rollout bookkeeping. | Reset/truncation scheduling and CI episode boundaries. | `EpisodeLifecycleContract`; adapters must not own private truth. |

Merge policy is mandatory for cross-layer producers. Legal values remain:

- `last_write_wins`
- `priority_override`
- `reject_on_conflict`
- `merge_by_field`
- `append_only`

External graph input is injected before the scheduling-window barrier. If an
action or coordination path needs next-window semantics, it must set an
`effective_time` in a later window rather than relying on hidden call order.

## 5. Compatibility Classification

| Surface | Classification | WP2 rule |
|---------|----------------|----------|
| `RuntimeFacade::runtime()` | Diagnostics and legacy adapter escape hatch. | No new maintained engagement, policy, or validation path may depend on it. |
| Direct `WorldBatchRuntime` Python exposure | Compatibility. | Allowed inside explicit adapters only. |
| `MissionCommand` engagement fields | Compatibility aggregation. | Do not add new `P7-P9` semantics here unless mirrored by narrower contracts. |
| Raw `ContactList` observation fallback | Compatibility fallback. | Maintained exports should prefer `TrackPacket` / fused-track semantics. |
| Debug damage and raw health reads | Test helper / diagnostics. | Maintained damage visibility should use `DamageReport`. |
| Python reward and observation fallback assembly | Compatibility / migration support. | Maintained path should converge on facade packets and explicit view/reward specs. |

## 6. Validation Gates

WP2 is complete only when the repository has enough tests or documented gates
to protect the frozen contract shape. The immediate local gates are:

```powershell
.\tools\maintenance\cmo_env.ps1 validate
.\tools\maintenance\cmo_env.ps1 python -m pytest -q tests\architecture\test_runtime_facade_layering.py tests\architecture\test_cmake_target_readiness.py
.\tools\maintenance\cmo_env.ps1 python -m pytest -q tests\runtime\facade\test_runtime_facade.py
.\tools\maintenance\cmo_env.ps1 python tools\runners\run_pytest_suite.py --suite tests\smoke\ci_smoke_suite.json
```

For a clean local build window:

```powershell
cmake -S . -B build-local-win -G Ninja -DCMAKE_BUILD_TYPE=Release
cmake --build build-local-win --target ef_core ef_py -j2
.\tools\maintenance\cmo_env.ps1 validate
.\tools\maintenance\cmo_env.ps1 python tools\runners\run_pytest_suite.py --suite tests\smoke\ci_smoke_suite.json
```

Missing validation to schedule after this freeze:

1. Contract-document consistency tests for `P0-P10` stage vocabulary,
   packet ownership, read/write sets, clock domains, event ordering, and merge
   policy.
2. A facade-only engagement path test covering launch, munition lifecycle,
   effects, damage, and observation export.
3. A stage-aligned local non-RL smoke test that explicitly exercises the
   architecture vocabulary.
4. A diagnostics trace test tying track, launch request/event, munition,
   effects, damage, and observation packet version.

## 7. Handoff To Later Work Packages

`WP3 Engagement Pilot` should implement the first cross-domain slice after this
freeze:

1. read a `TrackPacket`,
2. submit a `LaunchRequest`,
3. receive a `LaunchEvent`,
4. observe a `MunitionLifecyclePacket`,
5. receive an `EffectsEvent` and `DamageReport`,
6. export an `ObservationPacket` and `DiagnosticsTrace`.

The pilot must cover at least aircraft pylon launch and naval mount launch
without creating separate private lifecycle stacks.

`WP2.5 Scheduler Semantics Freeze` [task family](scheduler_semantics_wp25_20260519.md)
should freeze event ordering, state versioning, barrier visibility, clock-domain
merge policy, replay contract, and stage-node manifests before facade
hardened alignment begins.

`WP4 Facade Alignment` [task family](facade_alignment_wp4_20260519.md) should
add or adapt request/result APIs so the pilot is reachable without raw runtime
access.

`WP5 Validation Harness` should turn the gates above into maintained tests and
local Windows smoke commands.

## 8. Exit Criteria

WP2 exits when:

1. The contract families in this document are either implemented as maintained
   DTOs or explicitly tracked as implementation tasks.
2. Every maintained `P0-P10` node has documented ownership, read/write sets,
   clock domain, latency policy, sync policy, and event-ordering rule.
3. Compatibility paths are documented and do not become new mainline
   dependencies.
4. Policy and orchestration producers use facade-shaped requests with
   `merge_policy` and `effective_time`.
5. Local validation can run without RL training dependencies.
