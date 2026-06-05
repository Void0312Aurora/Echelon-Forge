# Ground Domain Bootstrap Plan — Architecture Approval

Status: `2026-05-21` plan reviewed; approved with five required G0 supplements.
Source: [ground_domain_bootstrap_plan_20260521.md](../ground/archive/ground_domain_bootstrap_plan_20260521.md)
Authority: [simulation system architecture design](../../plan/architecture/simulation_system_architecture_design.md)

## 1. Overall Assessment

The plan is **structurally correct**. It follows the existing `common + specialization +
profile bridge` pattern established by the air/naval domains. It explicitly prohibits a
separate "army runtime stack." Its five-phase decomposition (G0 Boundary Freeze through
G4 Runtime Slice) is appropriately scoped, with the first wave intentionally
conservative — small-unit echelon, limited task family, no new physics assumptions.

The plan is approved. However, G0 must produce five additional architecture
commitments before G1 Contract Skeleton begins. These are not implementation
concerns — they are architecture declarations required by Section 10 of the
architecture baseline.

## 2. Architecture Alignment

| Architecture Requirement (§10) | Plan Status | Verdict |
|-------------------------------|-------------|---------|
| stage coverage — which P0-P10 stages are involved | Not declared | ❌ Required for G0 |
| consumed/produced packets — which packet families | Not declared | ❌ Required for G0 |
| capability families — which model families are extended | Listed as open question (§8.2), deferred to G1 | ⚠️ Must be resolved in G0 |
| read/write sets — stage-node declarations | Not declared | Defer to G3 |
| clock domain / latency policy | Not declared | ❌ Required for G0 |
| facade visibility rules | Not declared | Defer to G3 |
| capability interfaces | Not declared | Defer to G3 |
| parity / regression tests | Not declared | Defer to G3 |
| compatibility behavior for existing callers | Implicit in §6 | Adequate for G0 |
| "no private runtime path" (Law 10) | ✅ §2: explicit prohibition | Correct |
| capability composition pathway (Law 15) | Not declared | ❌ Required for G0 |
| information state boundaries (§3) | Partial (§8.6), not mapped to six-layer model | ⚠️ Must be resolved in G0 |

## 3. Required G0 Supplements

G0 currently lists its output as: "this task line, subproject README, planning
baseline, open-question list." Architecture Section 10 requires that every domain
extension document eleven items. For G0 — a documentation-only freeze — the following
five must be added before G1 begins.

### Supplement 1: Stage Coverage Declaration

State which P0-P10 stages the first ground slice participates in.

Recommendation for the G1 tasking-only starter:

```
P0 ContentCompile   — ground platform definitions as capability bundles
P2 TaskingIntent    — ground task orders, leader intents, command relationships
P3 CommandDelivery   — deferred to G3 (command surface only if G1 includes it)
P6 SenseTrackLink    — deferred; ground sensing has terrain-masking constraints
```

### Supplement 2: Packet Vocabulary Declaration

List which existing contract families the ground domain consumes and produces.

Recommendation:

```
Consumed:  TaskingPacket (extended with ground-specific fields)
           AgentRole (ground squad/platoon/company roles)
Produced:  TaskOrder (ground task family)
           LeaderIntent (ground command hierarchy)
           PilotReport (ground unit status)
Deferred:  CommandPacket, ObservationPacket, TrackPacket
```

### Supplement 3: Capability Composition Declaration

State that ground platforms will be defined as capability bundles, not as new
hardcoded type-name dispatch paths. This is the third domain's opportunity to
prove Architecture Law 15 (`spawn_platform({capabilities...})`).

Recommendation for first-wave families:

```
PlatformFamily: ground_vehicle_section, dismounted_unit
MotionFamily:   ground_mobility (wheeled, tracked, dismounted)
SensorFamily:   ground_visual, ground_acoustic (deferred to G3+)
LauncherFamily: direct_fire_platform, indirect_fire_battery (deferred to G3+)
DoctrineFamily: land_tactics (move, occupy, support, screen)
EffectsFamily:  deferred to G3+
```

### Supplement 4: Clock Domain Assumptions

Ground units operate on fundamentally different timescales than air/naval platforms.
A dismounted squad does not maneuver at 60Hz physics — its command cadence may be on
the order of seconds or minutes, not milliseconds.

Recommendation:

```
Base tactical clock: 1 Hz (1-second tasking evaluation window)
  — differs from air/naval 60Hz physics baseline
  — nested triggering: ground tasking runs every Nth base tick
Motion update: event-driven or low-rate (deferred to G3+)
Sensing: terrain-masked, line-of-sight constrained (deferred to G3+)
```

### Supplement 5: Agency Graph Impact

Ground domain introduces new agent roles with different authority scopes and
command/support relationships distinct from air/naval hierarchies.

Recommendation for first-wave roles:

```
ground_squad_leader      — authority: squad; information: sensed + observed;
                           action: task order execution
ground_platoon_commander — authority: platoon; information: shared tactical picture;
                           action: leader intent, task order delegation
ground_company_commander — authority: company; information: shared tactical picture;
                           action: coordination intent (deferred to G3+)
```

Each role must declare its five-part schema per architecture §8: `role`,
`authority_scope`, `information_state_source`, `decision_model_ref`, and
`action_interface`.

## 4. Information State Boundary

Architecture Section 3 requires six-layer information state discipline. Ground
domain introduces information degradation mechanisms (terrain masking, line-of-sight,
radio range) that differ qualitatively from air/naval radar/sonar chains.

For G0, the ground domain should declare:

- `SensedState` for ground units defaults to terrain-masked rather than free-space
  radar propagation.
- `TrackState` for ground contacts may use visual/acoustic correlation rather than
  radar fusion.
- `SharedTacticalPicture` for ground units is constrained by radio range and relay
  topology rather than data-link bandwidth.
- These rules are placeholders until G3+ implements them — but the architecture
  commitment must be made in G0.

## 5. Open Questions Resolution

The original plan listed six open questions "to be discussed before G1." For G0
to produce a meaningful semantic contract, three of these must be resolved:

| Question | Resolution needed for | Suggested default |
|----------|----------------------|-------------------|
| naming: `ground` vs `land` | service-profile alignment, DTO landing points | `ground` (matches existing `air`/`naval` parallelism) |
| first tactical unit | task order granularity, echelon authority scopes | platoon (narrow enough for a first slice, broad enough to express command hierarchy) |
| first task family | DTO field set, task order vocabulary | `move / occupy / support` (fewest new physics assumptions, expressible through existing `TaskOrder` pattern) |

The remaining three (platform family, command surface scope, observation surface)
may remain open for G1.

## 6. Decision

The Ground Domain Bootstrap Plan is **approved** subject to the five G0 supplements
detailed in Section 3 above. G0 should close these before G1 Contract Skeleton
begins.

The five supplements are not new work — they are architecture commitments already
required by the architecture baseline Section 10. Making them explicit in G0
prevents the G1 contract skeleton from being built on implicit assumptions that
later phases must unwind.
