# Post-WP9 Architecture Route Plan — Gap Analysis

Status: `2026-05-20` precise gap analysis against the architecture baseline.
Source: [post_wp9 route plan](../simulation_architecture/post_wp9_architecture_route_plan_20260520.md)
Authority: [simulation system architecture design](../../plan/architecture/simulation_system_architecture_design.md)

## 1. Method

This analysis takes the architecture baseline as the sole authority. It extracts
every normative requirement that concerns runtime execution, information flow,
cross-layer coupling, and scheduling semantics. Each requirement is checked
against:

1. **WP0-WP9 delivery** — does it exist in code?
2. **post_wp9 coverage** — do the five tracks plan to cover it?
3. **Gap** — if neither delivers it, what exactly is missing?

Architecture document sections evaluated: 2 (Graph-of-Graphs), 3 (Information
State Architecture), 4 (Architecture Laws), 6 (Semantic Lifecycle), 7
(Causal-Temporal Execution Model), 8 (System Layer Coupling Model), 9 (Contract
Taxonomy), 10 (Domain Extension Model), 11 (Backend Policy), 13 (Validation
Gates).

## 2. Section 7 — Causal-Temporal Execution Model

This is the architecture document's most detailed runtime specification and the
primary target of post_wp9 Track 1.

### 2.1 Covered by post_wp9 Track 1

| Requirement | Architecture doc ref | WP0-WP9 | post_wp9 |
|------------|-------------------|---------|----------|
| StageNodeManifest in code | §7: "Every maintained stage node should declare" | ❌ WP2.5 YAML only | ✅ Track 1: "machine-readable StageNodeManifest registry" |
| Event ordering `(timestamp, priority, event_id)` | §7: "Events are ordered deterministically" | ❌ `RecentEngagementEvents` is flat vector | ✅ Track 1: "runtime-visible event order" |
| Deterministic `event_id` | §7: "event_id is generated deterministically from the producing node and local sequence" | ❌ | ✅ Implicit in Track 1 event order |
| State shard versioning | §7: "State versioning starts coarse but must leave room for shards" | ❌ `flecs::world` unversioned | ✅ Track 1: "snapshot...contracts" |
| Barrier visibility | §7: "Consistency boundary where writes become visible" | ❌ All writes visible after `ecs.progress()` | ✅ Track 1: "barrier contracts" |
| `clock_merge_policy` naming | §7: "Reserve `merge_policy` for cross-layer request contracts" | ✅ WP9 INF-1 | Already resolved |
| Stage node declaration fields | §7 table: `semantic_stage, read_set, write_set, clock_domain, latency_policy, sync_policy` | ⚠️ WP2.5 manifest schema, not in code | ✅ Track 1 implies code materialization |
| Acyclic window DAG | §7: "The graph inside the window must be acyclic" | ❌ Linear `ecs.progress()` | ✅ Track 1 implies through manifest |
| Cross-window feedback rule | §7: "Cross-window feedback reads committed StateStore snapshot from a previous window" | ❌ | ✅ Implicit in barrier + StateStore |

### 2.2 Not Explicitly Covered

| Requirement | Architecture doc ref | What's missing |
|------------|-------------------|----------------|
| Same-window edge derivation | §7: "A same-window edge A→B is legal when B.read_set intersects A.write_set and A publishes that write inside the same window" | Track 1 mentions "barrier contracts" but does not specify whether the same-window edge rule will be enforced at schedule-construction time, runtime, or left as documentation. This rule is what prevents the DAG from degenerating into a linear pipeline. |
| Clock domain enforcement | §7: "Clock domains use nested triggering by default. The base tick owns the outer deterministic schedule, and lower-rate nodes run on declared multiples or declared schedule slots." | Track 1 says "manifest registry" but does not specify whether the scheduler will actually skip nodes whose clock domain hasn't fired in the current window. Without clock domain enforcement, the manifest is decorative. |
| Independent clock domain merge gate | §7: "Independent clock domains are allowed only when a freeze plan specifies their deterministic merge policy and event ordering at barriers" | Not in any track. This is a gate for future work, not current work, so it's acceptable to defer — but it should be named as a deferred gate. |

## 3. Section 8 — System Layer Coupling Model

This section defines the scheduling window, external graph input injection, and
10 cross-layer contracts. These are the mechanisms that make the three-layer
architecture (simulation / policy / orchestration) work at runtime.

### 3.1 Cross-Layer Contract Status

| Contract | Architecture doc req | WP0-WP9 DTO | Runtime enforcement |
|----------|-------------------|------------|-------------------|
| `ObservationViewSpec` | §8: version format, required/optional fields, checkpoint compatibility | ✅ WP9 DTO-4 | ❌ Checkpoint compatibility not runtime-checked |
| `ObservationPacket` | §8: sampled at declared barrier, source time, schema metadata | ✅ WP9 DTO-3 (+ metadata fields) | ❌ Barrier id populated? |
| `DecisionBelief` | §8: boundary rules — maintained only when derived from ObservationPacket; diagnostics-only when using World Truth | ✅ WP9 DTO-8 | ❌ No runtime enforcement of the boundary |
| `AgentRole` | §8: 5-part schema — role, authority_scope, information_state_source, decision_model_ref, action_interface | ✅ WP9 DTO-7 | ❌ Authority scope not enforced; information_state_source not verified |
| `ActionIntentPacket` | §8: effective_time, valid_until, merge_policy, source_layer, source_id, input_snapshot_version | ✅ WP9 DTO-5 | ❌ effective_time not enforced by scheduler; merge_policy not applied |
| **`ActionHoldPolicy`** | **§8: hold-last, interpolation, expiry, or drop semantics across control-rate and physics-rate ticks** | **❌ DTO NEVER CREATED** | **❌** |
| `CoordinationIntentPacket` | §8: source type/id, target roster, merge_policy | ✅ WP9 DTO-6 | ❌ merge_policy not enforced |
| `RewardSpec` / `RewardReport` | §8: fact/shaping split | ✅ WP9 DTO-1 | ❌ Fact boundary not runtime-verified |
| `TerminationSpec` / `EpisodeStatus` | §8: terminated/truncated split by source layer | ✅ WP9 DTO-2 | ⚠️ Fields exist but reason_source attribution not machine-checked |

### 3.2 Scheduling Window Semantics — Not Covered

The architecture document §8 contains a detailed specification of how the
scheduling window orchestrates cross-layer requests. This is the mechanism that
makes the architecture's "three coupled layers" model work at runtime. It
includes:

| Requirement | Architecture doc ref | post_wp9 coverage |
|------------|-------------------|-------------------|
| **Window orchestration loop** | §8 design consequence 9: "At the start of a window, the facade collects arrived cross-layer requests, translates them into state writes or event enqueues, and then runs the DAG." | Neither Track 1 nor Track 2 explicitly addresses the window loop. Track 1 covers barriers and snapshots; Track 2 covers facade export. The loop that connects them — collect → inject → DAG → commit → export — is not named as a deliverable. |
| **External graph input injection** | §8: "External graph inputs are injected before the scheduling-window barrier." Cross-layer request fields: `source_layer, source_id, input_snapshot_version, effective_time, valid_until, merge_policy` | DTOs have the fields (WP9), but the injection mechanism — facade collecting requests at window boundary, translating to state writes/events, making them visible after input_injection barrier — has no implementation plan. |
| **Policy cadence example** | §8: Detailed example with policy 10 Hz, platform control 20 Hz, physics 60 Hz, showing window N and N+1 timing | No track plans to implement multi-rate scheduling that would make this example runnable. Track 2 says "facade vertical slice" but the slice described is engagement/observation, not policy/control/physics multi-rate. |
| **ActionHoldPolicy runtime** | §8 design consequence 5: "Policy inference cadence is a first-class clock domain. A policy running at 10 Hz... is legal only when ActionHoldPolicy declares how one policy output is consumed by multiple control ticks." | **ActionHoldPolicy has no DTO (never created in WP9). No track addresses hold-last/interpolation/expiry runtime.** |

### 3.3 Assessment

post_wp9 Track 1 covers the low-level primitives (StateStore, EventQueue,
Barrier, StageNodeManifest). Track 2 covers the facade export path. But the
**scheduling window loop itself** — the orchestration layer that connects facade
request collection → input injection → DAG execution → commit → export — is not
explicitly assigned to any track. It sits between Track 1's primitives and Track
2's facade slice, belonging fully to neither.

## 4. Section 3 — Information State Architecture

### 4.1 Six-Layer Model Status

| Layer | Architecture doc ref | Runtime implementation | post_wp9 |
|-------|-------------------|----------------------|----------|
| World Truth | §3: "Never consumed directly by maintained policy paths except diagnostics-only tests" | ❌ No enforcement. Policy can read any ECS component. | Not addressed |
| Sensed State | §3: "Export with source time, sensor id, confidence, latency/drop metadata" | ⚠️ Implicit in sensor system, not labeled | Not addressed |
| Track State | §3: "Export as TrackPacket-equivalent data, with source snapshot/version provenance" | ⚠️ TrackPacket exists, provenance fields populated? | Not addressed |
| Shared Tactical Picture | §3: "Export only after link latency, loss, permission, and roster constraints" | ⚠️ Implicit in data-link system | Not addressed |
| Agent Observation | §3: "Expose only fields allowed by the view spec, schema version, and snapshot source" | ⚠️ ObservationPacket + ObservationViewSpec exist as DTOs, but field masking not enforced | Track 2 touches observation export |
| Decision Belief | §3: "Must declare observation inputs, inference source, source versions, and whether it is maintained or diagnostics-only" | ❌ DecisionBelief DTO exists but the boundary — diagnostics-only when using World Truth — is not enforced | Not addressed |

### 4.2 Five Transformation Rules — Not Covered

Architecture doc §3 specifies explicit transformations between layers:

```
WT → SS → TS → STP → AO → DB → ActionIntentPacket
```

These transformations are normative: "Transformations between layers must be
explicit." Currently they are implicit in system code. No post_wp9 track
addresses making any of these transformations machine-checkable or
facade-visible.

### 4.3 Architecture Law 14

§4 Law 14: "Maintained decision paths consume `ObservationPacket` and, when
needed, `DecisionBelief`. They must not consume `World Truth` unless the path is
marked diagnostics-only."

This law has no runtime enforcement mechanism. DTOs exist (WP9) but nothing
prevents policy code from calling `get_agent_observation()` (which returns raw
ECS data) instead of consuming `ObservationPacket` through the facade. No
post_wp9 track addresses making this law machine-checkable.

## 5. Section 2 — Graph-of-Graphs Architecture

### 5.1 Agency Graph

Architecture doc §2 defines Agency Graph as producing "Agents, roles, authority
scopes, decision models, action interfaces, and coordination relationships" and
controlling "Injects explicit action or coordination requests through
facade-compatible graph inputs."

| Requirement | Status |
|------------|--------|
| AgentRole DTO | ✅ WP9 DTO-7 |
| AgentRole runtime enforcement (authority scope, information state source verification) | ❌ |
| Decision model dispatch (scripted/learned/human/LLM/MCTS) through AgentRole interface | ❌ |
| Role-based information access control | ❌ |

post_wp9 coverage: No track explicitly addresses Agency Graph runtime
materialization. The architecture doc places Agency Graph as co-equal with
Causal Graph and Information Graph, but post_wp9 prioritizes Causal/Temporal
(Track 1) over Agency.

This may be a correct prioritization — causal runtime foundation is a
prerequisite for agency enforcement — but the gap should be explicit: **Agency
Graph runtime is not covered by any post_wp9 track.**

## 6. Section 9 — Contract Taxonomy

### 6.1 Missing DTO

| Contract family | Architecture doc ref | WP9 | post_wp9 |
|----------------|-------------------|-----|----------|
| `ActionHoldPolicy` | §9: "Policy action, validity window, hold/interpolation/expiry, and control-rate alignment" | ❌ Not created | Not addressed |
| `Capability` / `CapabilityBundle` | §9: "Typed platform capability composition for mobility, sensing, communication, launching, survivability, command, and doctrine profile" | ❌ Not created | Track 4 addresses conceptually but DTO must precede runtime |

## 7. Section 10 — Domain Extension Model

### 7.1 Capability Composition

Architecture doc §10: "The architecture target is `spawn_platform({capabilities...})`.
`spawn_unit(type_name)` may remain a convenience shortcut for compatibility, but
it should expand internally to a typed `CapabilityBundle`."

post_wp9 Track 4 covers this. ✅

But Track 4's prerequisite list says "WP2, WP9, tracks 1-3." It should also list
the `Capability` / `CapabilityBundle` DTO creation as a prerequisite, since the
DTOs don't exist yet.

## 8. Consolidated Gap Register

### 8.1 Gaps in post_wp9 That Should Be Added to Existing Tracks

| ID | Gap | Architecture doc ref | Should be added to |
|----|-----|-------------------|-------------------|
| **GAP-1** | `ActionHoldPolicy` DTO never created. Architecture §8 and §9 define it as a contract family. | §8, §9 | Track 2 (as prerequisite DTO before facade slice proves policy→control→physics cadence) |
| **GAP-2** | Scheduling window orchestration loop. Collect → inject → DAG → commit → export. | §8 design consequence 9 | Track 1 (the loop is what connects StateStore, EventQueue, Barrier, and StageNodeManifest into a working scheduler) |
| **GAP-3** | Cross-layer request injection semantics. `effective_time`, `valid_until`, scheduling window visibility. | §8 cross-layer request field table + policy cadence example | Track 1 or Track 2 (injection is part of the window loop, not a separate concern) |
| **GAP-4** | Information state provenance labeling. Runtime-enforceable labels on ObservationPacket and DecisionBelief that distinguish which information layer the data came from. | §3 six-layer model + 5 transformation rules | Track 2 (facade export path is the natural place to attach provenance labels) |

### 8.2 Gaps Not Covered by Any Track

| ID | Gap | Architecture doc ref | Why not covered |
|----|-----|-------------------|----------------|
| **GAP-5** | Architecture Law 14 enforcement. No mechanism to prevent policy code from consuming World Truth. | §4 Law 14 | Neither Track 1 (causal primitives) nor Track 2 (facade export) addresses read-side enforcement of information state boundaries. |
| **GAP-6** | Agency Graph runtime. Authority scope enforcement, role-based information access, decision model dispatch. | §2 Agency Graph row | AgentRole DTO exists (WP9) but its five-part schema has no runtime enforcement. Tracks 1-2 focus on Causal/Temporal, not Agency. |
| **GAP-7** | Five information state transformation rules as machine-checkable or facade-visible. | §3: "Transformations between layers must be explicit" | Currently implicit in system code. No track addresses surfacing them. |
| **GAP-8** | Same-window edge derivation rule enforcement. | §7: "A same-window edge A→B is legal when B.read_set intersects A.write_set" | Track 1 mentions manifest and barriers but not whether the edge rule will be enforced at schedule construction time. |
| **GAP-9** | Clock domain enforcement. Scheduler must skip nodes whose clock domain hasn't fired. | §7: "lower-rate nodes run on declared multiples or declared schedule slots" | Track 1 says "manifest registry" but doesn't specify whether clock domain cadence is enforced or advisory. |

### 8.3 Correctly Excluded

| Concern | Why correctly excluded from post_wp9 |
|---------|--------------------------------------|
| Multi-fidelity profiles + ModelProvider | Needs causal foundation (barriers + snapshots) before fidelity can be compared. Correctly in Track 3. |
| `spawn_platform({capabilities...})` | Needs stable setup/content contract. Correctly in Track 4. |
| Counterfactual / worldline branching | Needs deterministic replay + snapshot/restore. Correctly in Track 5. |
| Full Learning Graph implementation | Deferred beyond post_wp9. Architecture doc itself defers Learning Graph. |
| Exact GPU world-step promotion | Blocked by WP6/WP7 profile registry rules. Not a post_wp9 concern. |

## 9. Recommended Adjustments to post_wp9

### 9.1 Add to Track 1 (Causal Runtime Foundation)

The track should explicitly deliver:

1. **Scheduling window loop skeleton** — not a full multi-rate scheduler, but a
   minimal window loop that demonstrates: collect facade requests → input_injection
   barrier → run acyclic DAG (from manifest) → window_commit barrier → export
   barrier. This is what connects the four primitives (StateStore, EventQueue,
   Barrier, StageNodeManifest) into a working system.

2. **Same-window edge validation** — at schedule construction time (not runtime),
   verify that declared edges obey the architecture doc §7 rule: B.read_set must
   intersect A.write_set and A must declare same-window output.

### 9.2 Add to Track 2 (Facade Vertical Slice)

The track should explicitly deliver:

3. **`ActionHoldPolicy` DTO** — prerequisite before the slice can demonstrate
   policy→control→physics cadence. Fields: `hold_last`, `interpolate`, `expiry`,
   `drop`, with validity duration and refresh cadence.

4. **Information state provenance labels** — on the existing ObservationPacket
   metadata fields (WP9 DTO-3), demonstrate that snapshots carry a provenance
   label identifying which information layer they were sampled from.

### 9.3 Record as Deferred (Not in Current Tracks)

5. **GAP-5** (Law 14 enforcement) — requires read-side AST analysis or runtime
   guard. Defer until information state provenance labels (GAP-4) exist.

6. **GAP-6** (Agency Graph runtime) — authority enforcement, role-based access
   control. Defer until causal foundation (Track 1) and facade slice (Track 2)
   are stable.

7. **GAP-7** (Transformation rule surfacing) — defer until provenance labels
   exist as a stable vocabulary.

8. **GAP-9** (Clock domain enforcement) — defer until the window loop skeleton
   (GAP-2) is working. Advisory clock domains in the manifest registry are an
   acceptable first step.

## 10. Conclusion

post_wp9's five-track route is correct in its ordering logic. The causal
foundation must come first; capability composition and counterfactual work
cannot precede it.

However, post_wp9 under-specifies what Track 1 and Track 2 must deliver to make
the architecture document's Section 7 and Section 8 real. Specifically:

- **Track 1** has the primitives (StateStore, EventQueue, Barrier, Manifest) but
  not the **scheduling window loop** that connects them (GAP-2/GAP-3).
- **Track 2** has the facade export path but not **ActionHoldPolicy** (GAP-1)
  and not **information state provenance labels** (GAP-4).

These four items are not architectural discovery. They are implementation of
requirements already fully specified in the architecture document. Adding them
to Track 1 and Track 2 does not expand scope — it makes the existing scope
precise enough to verify.
