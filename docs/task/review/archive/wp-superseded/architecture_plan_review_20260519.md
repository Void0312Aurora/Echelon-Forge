# Architecture Plan Review — Temp-01 Response

Status: `2026-05-19` review response completed.
Source: [temp-01.md](temp-01.md) — external architecture plan critique.
Scope: Architecture design baseline, WP0-WP5 plan structure, contract taxonomy, scheduler semantics, facade design, validation gates.

Related documents:

- [simulation system architecture design](../../plan/architecture/simulation_system_architecture_design.md)
- [WP3 engagement pilot task family](../../task/simulation_architecture/engagement_pilot_wp3_20260519.md)
- [WP3 acceptance review](wp3_engagement_pilot_acceptance_review_20260519.md)
- [WP4 facade alignment](../../task/simulation_architecture/facade_alignment_wp4_20260519.md)

## 1. Source Thesis

temp-01 argues that the architecture plan is "correct but overloaded" — it has the right direction (unified lifecycle, temporal DAG, facade contracts, explicit layer coupling) but has not yet converged into a minimal, freezable, verifiable architecture kernel. It identifies eight specific risks and proposes a reordered work package structure.

This document evaluates each claim against the architecture baseline and WP3 implementation evidence, then records which issues are valid and actionable.

## 2. Claim-by-Claim Assessment

### Claim 1: Architecture baseline "closed too early"

**Source argument**: StateStore, EventQueue, ClockDomain, and Barrier semantics are not frozen, yet the architecture document declares the framework closed. This risks local reinterpretation during implementation.

**Finding: Partially valid, but the closure mechanism is more nuanced than claimed.**

The architecture document (Section 6) defines a four-tier closure model:

- **A-level** (framework shape): closed — layers, layer relations, owns/must-not-own, cross-layer channel are named.
- **B-level** (contract semantics): closed when a rule plus at least one concrete example exists.
- **C-level** (implementation alignment): closed by task plan, migration phase, architecture test, or PR.
- **D-level** (internal design blank): closed by separate layer-specific architecture document.

StateStore, EventQueue, ClockDomain, and Barrier execution semantics fall under B-level, not A-level. The architecture document explicitly states "State versioning starts coarse but must leave room for shards" and "Clock domains use nested triggering by default" — these are design rules, not claims of frozen implementation. The closure rules contain a stop rule: "after the B rules above are present, no temp-04 style review should be opened for the same framework. New findings should be routed as direct B patches, C task plans, or D layer-specific architecture documents."

**Disposition: Acknowledged. The closure model is adequate but the distinction between A-level framework closure and B-level semantic freezing should be made more prominent in the architecture document.**

### Claim 2: P0-P10 risks becoming a "universal label system" without a StageNodeManifest

**Source argument**: Without a machine-checkable manifest, P0-P10 becomes a label anyone can apply, with no enforcement of read/write/sync/latency constraints.

**Finding: Valid. A formal StageNodeManifest is the missing link between the architecture document and verifiable code.**

The architecture document (Section 5) already requires every stage node to declare `semantic_stage`, `read_set`, `write_set`, `clock_domain`, `latency_policy`, and `sync_policy`. The `exact_stage_inventory.cpp` file has 28 stage descriptors with `reads`/`writes`/`depends_on_stages` fields, but these are informational only — no scheduler enforces them.

The suggested manifest schema (15 fields including `input_packets`, `output_packets`, `read_state_shards`, `write_state_shards`, `read_snapshot_policy`, `write_commit_policy`, `allowed_same_window_edges`, `required_barriers`, `event_families_emitted`, `diagnostic_trace_obligations`, `facade_visibility`, `compatibility_adapter_allowed`) is a reasonable refinement of the architecture document's 6-field requirement.

**Disposition: Accepted. StageNodeManifest should become a WP2 or WP2.5 deliverable, initially as a markdown schema, later as a machine-readable format.**

### Claim 3: WP2 Contract Freeze and WP3 Engagement Pilot parallelized too early

**Source argument**: WP3 freezes data shapes before WP2 freezes runtime semantics, creating an "architecture illusion" where contracts look unified but timing semantics diverge.

**Finding: Risk logic is correct, but the assessment of WP3's actual output is inaccurate.**

The risk that data-shape freezing outpaces semantic freezing is real. However, temp-01's specific claim that WP3 produces "just field names unified" does not match the implementation evidence:

- WP3's `DiagnosticsTrace` contract explicitly carries `trace_id`, `parent_trace_id`, `chain_id`, `track_id`, `launch_request_id`, `launch_event_id`, `munition` (EngagementEntityRef), `effects_event_id`, `damage_report_id`, `observation_packet_version` — this is a **causality chain**, not just field name alignment.
- `test_diagnostics_trace_contract.py` verifies all 7 link fields match in a single end-to-end chain identical to the trace temp-01 describes as the desired WP3-0 output.
- WP3 scoped itself strictly to data contracts — it did not touch `simulation_kernel.cpp`'s `ecs.progress()` call, ECS pipeline ordering, or scheduler behavior. The data shapes are frozen, but runtime semantics are explicitly left for WP4/WP5.
- WP3 never claimed to freeze runtime semantics; its document states the pilot goal as "build a contract adapter and cross-domain validation slice."

The suggested split into WP3-0 (Contract Trace Prototype) and WP3-1 (Implementation Pilot) is already effectively what happened: the DiagnosticsTrace chain is the trace prototype, and the air/naval adapters are the implementation pilot.

**Disposition: Risk noted but already mitigated by WP3's scope discipline. No plan change required.**

### Claim 4: Facade risks becoming a new god object

**Source argument**: If all cross-layer concerns route through RuntimeFacade, it becomes a second monolith. Should be split into Session, Setup, Execution, Observation, Diagnostics, Engagement, and Capability facades.

**Finding: Long-term risk is real, but splitting prematurely at current scale would be over-engineering.**

Current state:
- `RuntimeFacade` has approximately 30 public methods organized into setup, action ingestion, step execution, observation query, and engagement export groups.
- `RuntimeFacade::runtime()` is explicitly documented as "Compatibility escape hatch for diagnostics and legacy adapters only."
- Architecture tests (9 in `test_runtime_facade_layering.py`) enforce that maintained code does not depend on the escape hatch.
- The `runtime_facade_contract_plan.md` already recommends splitting into functional groups.

At the current project scale (single team, one primary developer), a 7-facade split would increase boilerplate without proportional benefit. The trigger for splitting should be: facade method count exceeding ~40, or multiple independent teams needing to own different facade surfaces.

**Disposition: Deferred. Add a split threshold to the facade governance rules. Record the suggested facade groups as the target split architecture.**

### Claim 5: Contract taxonomy needs explicit data classification

**Source argument**: Everything is called "contract," conflating component, event, view, and diagnostic. Need a five-way classification: Internal State, Contract Event, Contract Request, Observation View, Diagnostics Trace.

**Finding: Valid refinement. The architecture document already has implicit distinctions that should be made explicit.**

The architecture document (Section 7) lists 16 contract families, each with a defined purpose and long-term owner. The distinction between internal state (component-owned), events (LaunchEvent, EffectsEvent), requests (LaunchRequest, ActionIntentPacket), views (ObservationPacket), and traces (DiagnosticsTrace) exists implicitly in the owner assignments and naming conventions. Making it explicit would:

1. Prevent DTO inflation — a new field proposal would need to declare which category it belongs to.
2. Guide code generation — each category has different serialization, versioning, and replay rules.
3. Simplify WP2 contract freeze decisions — category determines freeze criteria.

The suggested rules are:
- Component is for mutation.
- Event is for causality.
- Packet is for boundary crossing.
- View is for consumption.
- Trace is for explanation.

**Disposition: Accepted. The five-category classification should be added to the architecture baseline as a contract governance rule. The existing 16 contract families should be tagged with their category.**

### Claim 6: StateStore / EventQueue / Barrier are concepts, not executable specifications

**Source argument**: No event priority family table, no deterministic event_id generation rules, no state shard version increment rules, no barrier visibility rules. The temporal DAG remains "advanced but vague" without these.

**Finding: Fully valid. This is the most important gap identified.**

Current state of each concept:

| Concept | Architecture doc | Code |
|---------|-----------------|------|
| StateStore | Described as authoritative state with versioning, may be host-owned, backend-owned, or partially synchronized | No abstraction exists. `flecs::world` is the sole authoritative state with no versioning. |
| EventQueue | Described as delayed/timestamped events ordered by `(timestamp, priority, event_id)` | `RecentEngagementEvents` is a flat `std::vector` with append/clear, no priority field, no deterministic ordering. |
| ClockDomain | Described as cadence rule with nested triggering by default | All systems run at single 60Hz. No multi-rate mechanism exists. |
| Barrier | Described as consistency boundary where writes become visible | No barrier exists. All writes are visible after `ecs.progress()` returns. |

The suggested WP2.5 "Scheduler Semantics Freeze" with six deliverables (event_family_priority_table.md, state_shard_versioning_rules.md, barrier_visibility_rules.md, clock_domain_merge_rules.md, deterministic_replay_contract.md, stage_node_manifest_schema.md) is the correct prescription. None of these require code implementation — they are specification documents that constrain future implementation.

**Disposition: Accepted. A Scheduler Semantics Freeze work package should be inserted between WP2 and WP4. This is the single most impactful improvement to the current plan.**

### Claim 7: GPU / resident-state strategy needs backend profiles and parity budget

**Source argument**: "CPU exact baseline" will become unenforceable without explicit backend profiles (Reference, Accelerated, ResidentState, Approximate) and parity declarations.

**Finding: Valid but lower priority than scheduler semantics.**

The architecture document (Section 9) already has clear rules:
- CPU exact is the semantic baseline.
- CUDA helpers attach through facade/backend packets.
- Device-resident state requires contracts declaring host sync, snapshot export, and partial view rules.
- Exact GPU world-step is not a maintained replacement until parity is proven.

GPU code is gated behind `EF_ENABLE_CUDA_EXPERIMENTS` and lives in a separate `src/gpu/` directory. The four suggested backend profiles are a useful formalization but are not blocking any current work.

**Disposition: Accepted for future planning. Should be a WP7 deliverable, not inserted into the current WP0-WP5 sequence.**

### Claim 8: Validation gates test existence, not proof

**Source argument**: Gates should be upgraded to Design Conformance, Trace Conformance, and Boundary Conformance. WP3's real acceptance should be "one DiagnosticsTrace can explain the full chain" rather than "air and naval both produce LaunchEvent."

**Finding: The critique of the architecture document's general gates (Section 11) is valid, but WP3's specific gates are already closer to evidence-driven than claimed.**

The architecture document's 10 validation gates are indeed checklist-style (e.g., "Docs name the stage, owner, consumed packets, and produced packets"). However, WP3's 8 acceptance gates are evidence-driven:

- Gate 1: "Air pylon launch and naval mount/VLS launch emit or adapt to the same LaunchEvent shape" → verified by `test_air_launch_adapter.py` and `test_naval_launch_adapter.py`
- Gate 6: "DiagnosticsTrace can connect track, launch request/event, munition, effects, damage, and observation packet version" → verified by `test_diagnostics_trace_contract.py` which checks all 7 link fields

The specific trace chain temp-01 demands — "who requested launch, based on which track snapshot, why fire-control accepted/rejected, how munition inherits launch event, when fuze/effects triggered, how damage changes state shard, which committed snapshot observation reads, that air/naval differences are only in launcher/munition/doctrine family" — is partially verified by WP3 (items 1-4 and 8 are proven; items 5-7 require scheduler semantics that WP3 explicitly does not touch).

**Disposition: The three-tier conformance model (Design/Trace/Boundary) should be adopted for WP5 validation harness design. Architecture document Section 11 should be updated to reference these tiers.**

## 3. Recommendations

### Immediate (insert into current WP0-WP5 sequence)

| Priority | Action | Rationale |
|----------|--------|-----------|
| **P0** | Insert WP2.5 Scheduler Semantics Freeze between WP2 and WP4 | Addresses Claim 6 — the single most consequential gap. Six spec files, zero code. |
| **P1** | Add five-category contract classification to architecture baseline | Addresses Claim 5 — prevents DTO inflation. Tag existing 16 contract families. |
| **P1** | Define StageNodeManifest schema as WP2.5 deliverable | Addresses Claim 2 — bridges architecture document and verifiable code. |

### Deferred (future work packages)

| Priority | Action | Rationale |
|----------|--------|-----------|
| P2 | Add backend profile taxonomy (WP7) | Addresses Claim 7 — formalizes Reference/Accelerated/ResidentState/Approximate. |
| P2 | Upgrade architecture document Section 11 to three-tier conformance model | Addresses Claim 8 — Design/Trace/Boundary tiers. |
| P3 | Add facade split threshold rule | Addresses Claim 4 — split at ~40 methods into Session/Setup/Execution/Observation/Diagnostics/Engagement/Capability groups. |
| P3 | Make A-level vs B-level closure distinction more prominent | Addresses Claim 1 — prevents premature semantic freezing. |

### Not accepted

| Claim | Rationale |
|-------|-----------|
| Split WP3 into WP3-0 + WP3-1 | WP3 already delivered the contract trace prototype (DiagnosticsTrace chain). Restructuring would add process overhead without new output. |
| Immediate 7-way facade split | Premature at current project scale. Defer to threshold-based trigger. |

## 4. Updated Work Package Map

```
WP0 Architecture Thesis        [complete]
WP1 Pipeline Inventory         [complete]
WP2 Contract Ontology Freeze   [active]  ← add five-category classification
WP2.5 Scheduler Semantics Freeze [NEW]  ← event priority, state versioning, barrier visibility, clock merge, replay contract, stage manifest
WP3 Engagement Pilot           [complete]
WP4 Facade Alignment           [planned] ← add facade split threshold rule
WP5 Validation Harness         [planned] ← adopt three-tier conformance model
WP6 Backend Profile Policy     [NEW]     ← deferred
```

## 5. Conclusion

temp-01 is a serious and professional architecture review. Its core diagnosis — "correct but overloaded, needs a minimal freezable architecture kernel" — is accurate. Of the eight specific risks identified:

- **One is the most consequential finding** (Claim 6: scheduler semantics under-specified) and warrants a new WP2.5 work package.
- **Two are valid refinements** (Claims 2 and 5: StageNodeManifest and contract classification) that should be incorporated into WP2/WP2.5.
- **Two are valid long-term concerns** (Claims 4 and 7: facade monolith and backend profiles) that can be deferred.
- **Two are partially valid but overstated** (Claims 1 and 8: premature closure and validation gates) — the existing mechanisms are more robust than credited.
- **One is logically sound but factually inaccurate about WP3's output** (Claim 3: WP2/WP3 parallelization risk) — WP3 already delivered the contract trace the critique demands.

The recommended WP2.5 insertion does not invalidate the current WP0-WP5 plan. It strengthens it by closing the single largest specification gap before WP4 begins facade hardening.
