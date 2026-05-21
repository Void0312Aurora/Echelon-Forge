# Ground Domain Bootstrap Plan

Status: `2026-05-22` sealed baseline for G0-G4; G5 is open for the first
minimal MVP scenario shell.

Inputs:

- [Simulation system architecture design](../../plan/architecture/simulation_system_architecture_design.md)
- [US Army profile](../../standards/services/army.md)
- [Common air naval](../common_air_naval/README.md)
- [Stage 3 platform expansion mainline plan](../review/stage3_platform_expansion_mainline_plan_20260521.md)
- [Ground domain bootstrap plan review](../review/ground_domain_bootstrap_plan_review_20260521.md)

## 1. Purpose

This plan opens a dedicated task lane for the repository's third domain:
ground/land execution specialization.

The immediate goal is not to start broad implementation. The immediate goal is
to freeze:

1. naming,
2. layer boundaries,
3. minimum semantic scope,
4. first-step acceptance criteria,
5. the extra cross-cutting surfaces that a new domain must bring with it,
6. the G0 architecture commitments required before `G1 Contract Skeleton`
   begins.

## 2. Architectural Position

The maintained boundary should be:

- `services/army` remains the service-profile layer.
- `ground/` becomes the execution-specialization planning lane.
- future code/runtime work should extend the shared lifecycle through
  capability composition, common-core contracts, and stage-local model
  families.
- the project must not create a separate `army runtime stack`.

Rationale:

- `Army` is a service profile, not the right long-term name for execution
  semantics.
- `ground` keeps room for Army-led land modeling without forcing all future
  land-capable work into a service-specific label.
- this follows the existing split between `services/navy` and `naval/`, and the
  standards note that future land execution should live in a dedicated ground
  specialization rather than in `services/army`.

## 3. Current Repo Position

As of `2026-05-21`, the repository already has:

- an authoritative Army service-profile document
- a `common + air + naval` split across tasking/command DTO layers
- Python tasking-profile dispatch for `air` and `naval`
- architecture law that new domains should add capability implementations
  rather than new runtime paths

The repository does not yet have:

- a maintained `ground/` standards specialization
- a ground tasking profile in Python dispatch
- ground-specific DTO landing points
- ground scenarios, content fixtures, or runtime-contract tests
- a first agreed movement / fires / observation surface

## 4. Proposed Phases

| Phase | Scope | Target output | Non-goals |
|------|-------|---------------|-----------|
| `G0 Boundary Freeze` | naming, layer model, starter scope | this task line, subproject README, planning baseline, required architecture declarations, open-question list | no code/runtime behavior |
| `G1 Contract Skeleton` | minimal profile dispatch and DTO landing points | `ground` profile resolution, starter common-core defaults, empty-or-minimal ground DTO shells, architecture tests | no maneuver model, no fire-control runtime |
| `G2 Content And Test Seed` | first fixtures and compatibility proof | one or two content fixtures, scenario/task specs, roundtrip/mapping tests, contract-shape tests | no broad scenario catalog |
| `G3 Execution Surface Design` | bounded execution semantics | first ground command/task/observation design note, stage coverage, capability map | no full physics or combat implementation |
| `G4 Runtime Slice` | first maintained behavior slice | one selected end-to-end ground behavior through shared lifecycle | no parallel ground-only pipeline |
| `G5 MVP Scenario` | first canonical ground scenario shell | one maintained `scenarios/ground/` smoke fixture proving loader plus tasking status chain | no real ground platform schema, movement, terrain, sensing, fires, or combat claims |

The critical design rule is that `G1-G4` should reuse the existing
`common + specialization + profile bridge` pattern rather than inventing a new
tasking/mission/runtime chain.

G5 extends that rule to scenario content: the first ground MVP scenario must
reuse the shared `ScenarioLoader` and accepted G4 tasking lifecycle instead of
creating a private ground scenario loader or runtime path.

### 4.1 Phase Subprojects And Task Clusters

Each phase is tracked as a separate task subproject so it can be assigned,
reviewed, and closed without widening the whole ground bootstrap lane.

| Phase | Subproject | Dispatch cluster | Release state |
|-------|------------|------------------|---------------|
| `G0 Boundary Freeze` | [g0_boundary_freeze/](g0_boundary_freeze/README.md) | [G0 standards alignment cluster](g0_boundary_freeze/g0_standards_alignment_cluster_20260521.md) | accepted |
| `G1 Contract Skeleton` | [g1_contract_skeleton/](g1_contract_skeleton/README.md) | [G1 profile and DTO contract cluster](g1_contract_skeleton/g1_profile_dto_contract_cluster_20260521.md) | accepted for Python-profile-only slice |
| `G2 Content And Test Seed` | [g2_content_test_seed/](g2_content_test_seed/README.md) | [G2 content fixture and test cluster](g2_content_test_seed/g2_content_fixture_test_cluster_20260521.md) | accepted |
| `G3 Execution Surface Design` | [g3_execution_surface_design/](g3_execution_surface_design/README.md) | [G3 execution surface preflight cluster](g3_execution_surface_design/g3_execution_surface_preflight_cluster_20260521.md) | accepted |
| `G4 Runtime Slice` | [g4_runtime_slice/](g4_runtime_slice/README.md) | [G4 selected runtime slice cluster](g4_runtime_slice/g4_selected_runtime_slice_cluster_20260521.md) | accepted and sealed for bounded tasking-only lifecycle proof |
| `G5 MVP Scenario` | [g5_mvp_scenario/](g5_mvp_scenario/README.md) | [G5 MVP scenario cluster](g5_mvp_scenario/g5_mvp_scenario_cluster_20260522.md) | open for tasking smoke scenario |

The active assignment queue is
[ground_subagent_dispatch_queue_20260521.md](ground_subagent_dispatch_queue_20260521.md).
It applies the repository's
[Subagent Usage Policy](../../standards/governance/subagent_usage_policy.md):
bounded write scopes, no concurrent edits to the same normative table, main
thread integration ownership, and a required worker return packet before the
next dependent phase is released.

## 5. Minimum Semantic Scope For The First Wave

The first wave should stay narrow. It should only freeze the smallest useful
ground semantic vocabulary that can live on top of the existing common core.

Starter semantic goals:

- maintained execution-specialization name defaults to `ground`
- `tasking_profile` should accept `army`, `ground`, and `land`, then normalize
  to `ground`
- first tight-loop tactical unit defaults to `platoon`
- squad/section and company/troop/battery remain valid scenario/tasking
  context, but the first executable granularity is platoon-centered
- first ground task family defaults to `move / occupy / support`
- command/support relationships expressed through shared fields such as
  `authority_scope`, `command_relationship`, `supported_node_id`, and
  `supporting_node_id`
- a first ground task set that can be mapped without new physics assumptions
- room for later maneuver, fires, sustainment, and mobility-control expansion

Starter non-goals:

- brigade/division/corps as tight-loop runtime units
- full direct-fire / indirect-fire execution semantics
- terrain, cover, concealment, breaching, logistics, and route-clearance
  realism
- large `MissionCommand` expansion before the tasking/core boundary is stable

## 6. G0 Architecture Commitments

G0 now freezes the minimum architecture declarations required before G1 starts.
These are commitments for planning and contract shape, not claims that runtime
behavior already exists.

### 6.1 Stage Coverage

The first ground slice participates in the shared lifecycle as follows:

| Stage | G0 declaration |
|-------|----------------|
| `P0 ContentCompile` | Ground platform definitions should be lowered as capability bundles, not as a new hardcoded type-name path. |
| `P2 TaskingIntent` | G1 owns ground task orders, leader intents, echelon metadata, command relationships, and support relationships. |
| `P3 CommandDelivery` | Deferred to G3 unless G1 explicitly admits a minimal ground command surface. |
| `P6 SenseTrackLink` | Deferred; ground sensing must account for terrain masking, line-of-sight, radio range, and relay topology before becoming maintained. |
| `P10 ObservationExport` | Deferred for formal `ObservationPacket` export; status/report contract tests may precede runtime observation export. |

Read/write sets, facade visibility, detailed capability interfaces, and parity
tests remain G3+ work because they depend on the selected execution surface.

### 6.2 Packet Vocabulary

The G1 contract skeleton should use existing packet families first.

Consumed:

- `TaskingPacket` / common tasking-core equivalents
- `AgentRole` for ground squad/platoon/company roles

Produced:

- `TaskOrder` with ground task-family semantics
- `LeaderIntent` with ground command hierarchy and support relationships
- `PilotReport` as the compatibility status/report shell until a better
  ground-neutral report name is introduced

Deferred:

- `CommandPacket`
- `ObservationPacket`
- `TrackPacket`

### 6.3 Capability Composition Path

Ground platforms must be defined as capability bundles. G1 must not introduce a
new hardcoded `spawn_unit(type_name)` dispatch branch as the canonical path.

First-wave capability-family declarations:

| Family | First-wave declaration |
|--------|------------------------|
| `PlatformFamily` | `dismounted_unit`, `ground_vehicle_section` |
| `MotionFamily` | `ground_mobility` with future wheeled, tracked, and dismounted variants |
| `SensorFamily` | `ground_visual`, `ground_acoustic`; deferred to G3+ |
| `LauncherFamily` | `direct_fire_platform`, `indirect_fire_battery`; deferred to G3+ |
| `DoctrineFamily` | `land_tactics` for move, occupy, support, and later screen/secure |
| `EffectsFamily` | deferred to G3+ |

Compatibility behavior: existing `spawn_unit(type_name)` style creation may
remain as a wrapper, but the ground planning target is capability-bundle
lowering.

### 6.4 Clock Domain Assumptions

Ground tasking should not inherit air/naval high-rate motion assumptions by
default.

G0 clock assumptions:

- base tactical evaluation cadence: `1 Hz`
- motion update: low-rate or event-driven, deferred to G3+
- sensing update: terrain-masked and line-of-sight constrained, deferred to G3+
- scheduler integration: any ground cadence must merge through the shared
  causal-temporal scheduler and evidence model, not through a private ground
  loop

### 6.5 Agency Graph Impact

The first ground domain roles should declare the five-part schema required by
the architecture baseline: `role`, `authority_scope`,
`information_state_source`, `decision_model_ref`, and `action_interface`.

| Role | Authority scope | Information state source | Decision model ref | Action interface |
|------|-----------------|--------------------------|--------------------|------------------|
| `ground_squad_leader` | squad | sensed + agent observation | scripted land-task execution, later learned policy | task-order execution |
| `ground_platoon_commander` | platoon | shared tactical picture + agent observation | scripted platoon tasking, later doctrine profile | leader intent and task-order delegation |
| `ground_company_commander` | company | shared tactical picture | company coordination doctrine; deferred to G3+ | coordination intent; deferred to G3+ |

### 6.6 Information-State Boundary

Ground information state follows the six-layer architecture model.

| Layer | G0 ground commitment |
|-------|----------------------|
| `World Truth` | Authoritative terrain, entity, and tasking truth remains internal to the runtime. |
| `Sensed State` | Ground sensing defaults to terrain-masked and line-of-sight constrained, not free-space radar-style propagation. |
| `Track State` | Ground contacts may use visual/acoustic correlation; maintained track fusion is deferred. |
| `Shared Tactical Picture` | Ground sharing is constrained by radio range, relay topology, latency, and permission. |
| `Agent Observation` | Policies or scripted agents consume view-spec-shaped observations, not world truth. |
| `Decision Belief` | Ground decision models must declare which observations or shared-picture inputs produced the belief. |

These rules are placeholders until G3+ implements them, but the boundary is part
of the G0 architecture freeze.

## 7. Recommended First-Step Change Envelope

The first implementation wave should be intentionally conservative.

Recommended scope:

- `docs/standards/` follow-on planning for future `ground/` specialization
- `docs/task/ground/` planning and convergence records
- Python `tasking_profile` recognition for `Army` / `ground`
- starter `python/rl/profile/ground_profile.py` and adapter shell
- C++ DTO landing points under `components/tasking/ground` and
  `components/command/ground` only if a minimal field set is agreed first
- focused tests proving resolution, defaults, and compatibility behavior

Do not start with:

- `systems/ground/` runtime behavior
- `models/ground/` mobility behavior
- large facade surface expansion
- broad scenario-loader branching
- weapon/damage specialization for ground before the first semantic contract is
  frozen

## 8. Resolved Defaults And Remaining Open Questions

The architecture review resolves the first three G0 questions as defaults:

- maintained execution-specialization name: `ground`
- accepted aliases for profile resolution: `army`, `ground`, `land`
- first tight-loop tactical runtime unit: `platoon`
- first task family: `move / occupy / support`

The remaining topics should be discussed before or during `G1 Contract
Skeleton`.

### 8.1 First Platform Family

- Is the first platform a dismounted unit, ground vehicle section, artillery
  battery abstraction, or logistics/sustainment element?
- Should the first slice prefer one platform family or a unit-level abstract
  token?

### 8.2 Command Surface

- Which semantics belong in `TaskOrder`/`LeaderIntent` first, and which must be
  deferred from `MissionCommand`?
- Do we need a ground execution command in the first wave, or is a tasking-only
  starter slice sufficient?

### 8.3 Observation And Reporting

- What should the first ground observation/reporting surface look like without
  exposing world truth?
- Which land-specific report types must exist before the domain can be called
  credible?

## 9. Cross-Cutting Additions A New Domain Must Bring

Adding a new domain is not only a DTO or scenario exercise. Even a minimal
domain bootstrap should account for the following cross-cutting surfaces:

### 9.1 Standards And Doctrine Placement

- service-profile interpretation
- future ground specialization ownership
- terminology that must not be borrowed from air/naval semantics

### 9.2 Capability Composition Mapping

- which `PlatformFamily`, `MotionFamily`, `SensorFamily`, `LauncherFamily`,
  `DoctrineFamily`, and `EffectsFamily` entries the first ground slice needs
- which entries are placeholders vs. maintained

### 9.3 Content And Database Structure

- first content roots under `examples/config/database/`
- unit/module schema expectations
- compatibility behavior for `spawn_unit(type_name)` before public capability
  composition is promoted further

### 9.4 Contracts, Bindings, And Facade Visibility

- C++ DTO landing points
- Python binding exposure when fields become maintained
- facade request/result visibility rules
- compatibility behavior for existing consumers

### 9.5 Validation And Evidence

- architecture tests
- runtime-contract tests
- scenario or fixture smoke tests
- evidence that no new domain-private runtime path was introduced

### 9.6 Information-State And Agency Boundaries

- sensed vs. observed vs. believed information for ground units
- command/support relationships for land tasking
- authority ownership and delegation rules

### 9.7 Terrain And Environment Dependencies

- terrain, route, obstruction, and line-of-sight requirements
- whether the first slice can avoid needing new environment-model contracts
- what must be explicitly deferred if terrain is left abstract

## 10. Recommended Next Discussion Order

Before implementation, the next discussions should happen in this order:

1. confirm first platform family and fixture style
2. confirm whether phase one is tasking-only or includes a tiny execution
   command surface
3. confirm the first observation/reporting surface
4. confirm which cross-cutting additions are mandatory in the first wave versus
   explicitly deferred
5. confirm what evidence proves no private ground runtime path was introduced

## 11. Success Criteria For This Planning Lane

This planning lane is successful when it gives the repository a stable answer
to the following:

- where the third domain belongs in the layer model
- what the first maintained scope is
- what must be implemented together to keep the architecture honest
- what must stay deferred so the first slice remains small and testable
- which G0 architecture commitments must hold before G1 starts
