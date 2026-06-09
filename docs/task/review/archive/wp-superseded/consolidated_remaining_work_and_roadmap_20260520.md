# Consolidated Remaining Work And Forward Roadmap

Status: `2026-05-20` roadmap review; WP9 accepted.
Scope: All deferred, follow-up, and planned-but-unassigned architecture work identified
across WP0-WP8 review documents.

Inputs:

- [WP3 acceptance review](archive/wp-acceptance/wp3_engagement_pilot_acceptance_review_20260519.md)
- [WP4 first-wave / second-wave / final acceptance reviews](archive/wp-acceptance/wp4_facade_alignment_acceptance_review_20260519.md)
- [WP5 first-wave / information-belief / final acceptance reviews](archive/wp-acceptance/wp5_validation_harness_acceptance_review_20260519.md)
- [WP6 acceptance review](archive/wp-acceptance/wp6_backend_profile_policy_acceptance_review_20260519.md)
- [WP7.5 acceptance review](archive/wp-acceptance/wp75_training_path_facade_bridge_acceptance_review_20260520.md)
- [WP8 acceptance review](archive/wp-acceptance/wp8_learning_face_acceptance_review_20260520.md)
- [architecture plan review](architecture_plan_review_20260519.md)
- [temp-02 SCAL review](temp-02_review_20260519.md)
- [WP4 facade alignment plan review](archive/wp-superseded/wp4_facade_alignment_plan_review_20260519.md)

## 1. Purpose

WP0 through WP8 are accepted. Across all acceptance reviews, a consistent set
of deferred items has accumulated — most are small, well-understood, and
blocked only by prioritization rather than design uncertainty.

This document consolidates those deferred items into a single compressed work
package (`WP9 Contract And Infrastructure Closure`), then lays out the remaining
architectural roadmap beyond it.

## 2. Consolidated WP9 — Contract And Infrastructure Closure

Acceptance:

- [WP9 acceptance review](wp9_contract_infrastructure_closure_acceptance_review_20260520.md)

Residual:

- `INF-6` real missile terminal effects capture remains a tracked follow-up
  because the current damage system lacks a narrow maintained recorder seam.
  This residual is recorded in WP3 and the WP9 acceptance review.

All items below are extracted verbatim from the "Residual Risks" or "Deferred
Follow-Up" sections of WP3-WP7.5 acceptance reviews. None requires new
architectural discovery. Each has a known solution and a clear owner document.

### 2.1 DTO / Contract Promotion

| ID | Item | Source | Current state | Required output |
|----|------|--------|---------------|-----------------|
| DTO-1 | `RewardReport`: typed fact/shaping attribution | WP4 final §4.3, WP5 final §4.3 | `reward_breakdown_json` is unstructured string; fact/shaping split defined in architecture §6 but not typed | C++ `RewardReport` struct with `fact_terms`, `shaping_terms`, `fact_snapshot_version`, `term_owner` |
| DTO-2 | `TerminationSpec`: typed reason-source attribution | WP4 final §4.3, WP5 final §4.3 | `terminated`/`truncated` are parallel vectors; reason source not typed | C++ `TerminationSpec` struct with `reason`, `reason_source` (simulation/policy/orchestration), `snapshot_version` |
| DTO-3 | `ObservationBatchPacket` metadata: snapshot version, barrier id, source time | WP4 final §4.1, WP5 final §4.2 | `ObservationBatchPacket` lacks WP2.5 provenance fields | Add `snapshot_version`, `barrier_id`, `source_time_s` to existing struct |
| DTO-4 | `ObservationViewSpec`: \<major\>.\<minor\> version, required/optional fields, checkpoint compatibility rules | WP4 first-wave §4.5, WP4 plan review §2.2 | Architecture §6 defines rules; no typed surface exists | C++ `ObservationViewSpec` struct or documented schema with version negotiation |
| DTO-5 | `ActionIntentPacket`: effective_time, valid_until, merge_policy, action family | WP4 first-wave §2, WP4 surface map | Listed as deferred gap in WP4 surface inventory | C++ `ActionIntentPacket` struct aligned with architecture §6 fields |
| DTO-6 | `CoordinationIntentPacket`: source type/id, roster, merge_policy | WP4 first-wave §2, WP4 surface map | Listed as deferred gap | C++ `CoordinationIntentPacket` struct |
| DTO-7 | `AgentRole`: role + authority + information state source + decision model + action interface | WP4 second-wave §4, temp-02 review §2.4 | Python `agent_shim.py` has passive labels; no C++ type | Promote from Python shim to C++ `AgentRole` struct |
| DTO-8 | `DecisionBelief`: formal boundary with `ObservationPacket` | WP5-D §4, temp-02 review §2.3 | Python shim labels exist; no typed enforcement | C++ `DecisionBelief` struct or documented boundary contract |

### 2.2 Infrastructure Closure

| ID | Item | Source | Required output |
|----|------|--------|-----------------|
| INF-1 | `merge_policy` naming collision: WP2.5 clock merge vs architecture §6 cross-layer merge | WP2.5 review | Rename WP2.5 §6 to `clock_merge_policy`; add cross-reference note |
| INF-2 | `DiagnosticsTrace` independent facade surface | WP4 plan review §2.3, WP4 final §4.4 | Dedicated facade query endpoint; separate from engagement-export piggyback |
| INF-3 | `RuntimeCapabilities` population trigger | WP6 review §3 | Document the trigger condition: "when at least one non-reference backend profile is maintained" |
| INF-4 | StageNodeManifest registry completion | WP2.5 review §3 | Add P0-P6, P8-P10 example manifests (currently only P7 exists) |
| INF-5 | Facade split threshold rule | WP4 plan review §3.4 | Document: split `RuntimeFacade` at ~40 methods into Session/Setup/Execution/Observation/Diagnostics/Engagement/Capability groups |
| INF-6 | WP3遗留: real missile terminal effects capture | WP3 task doc §9 | Migrate from debug proximity-hit path to maintained guidance/effects event capture |
| INF-7 | WP3遗留: recent-event storage strategy | WP3 task doc §9 | Migrate from bounded buffer (`kMaxRecentEngagementEvents=64`) to formal event queue aligned with WP2.5 event ordering |

### 2.3 Deferred Guard Enforcement

| ID | Item | Source | Required output |
|----|------|--------|-----------------|
| GUA-1 | Global `sim.*` AST guard with allowlist | WP5 final §4.5 | Provenance labels + compatibility/diagnostics allowlist before broad bans |
| GUA-2 | Binding surface smoke promotion | WP5 final §4.1 | Fix `test_bindings_engagement_surface.py` empty packet-shell world-index case |

### 2.4 WP9 Work Packages

| Work package | Scope | Exit artifact |
|--------------|-------|---------------|
| `WP9-A DTO Promotion Batch 1` | DTO-1 through DTO-4: `RewardReport`, `TerminationSpec`, `ObservationBatchPacket` metadata, `ObservationViewSpec` | C++ headers + facade surface + Python bindings + focused tests |
| `WP9-B DTO Promotion Batch 2` | DTO-5 through DTO-8: `ActionIntentPacket`, `CoordinationIntentPacket`, `AgentRole`, `DecisionBelief` | C++ headers + facade surface + Python bindings + focused tests |
| `WP9-C Infrastructure Closure` | INF-1 through INF-7: naming fix, diagnostics surface, capabilities trigger, manifest registry, facade split rule, WP3遗留 | Doc patches + registry entries + 1 new facade method |
| `WP9-D Guard Enforcement` | GUA-1, GUA-2: allowlist, binding smoke promotion | Allowlist doc + test fix |
| `WP9-E Integration And Index Sync` | Cross-references, README update, bilingual alignment | Updated indexes |

### 2.5 WP9 Dependency Graph

```
WP9-A ──┐
WP9-B ──┼── WP9-E
WP9-C ──┤
WP9-D ──┘
```

All four sub-packages are independent and can run in parallel. WP9-E is serial.

## 3. WP8 — SCAL Learning Face (Accepted)

WP8 is now accepted as a documentation-only Learning-face task family. Its
three substantive gates have checked artifacts:

| Gate | Minimum checked artifact |
|------|--------------------------|
| WP8-A Curriculum & Scenario Generation | Versioned `CurriculumRequest` / `ScenarioGenerationSpec` schema with seed policy, phase, and request fields |
| WP8-B Evaluation & Capability Profiling | `BenchmarkProtocol` + `CapabilityProfile` schema with score attribution, evidence rules, and "no hidden truth" validation |
| WP8-C World-Model Interface & Learning Evidence | `ObservationPacket` / `DecisionBelief` / `World Truth` boundary contract with provenance and replay/diagnostics ancestry rules |

WP8 is documentation-only. It does not require RL training or new code.

## 4. Forward Roadmap

```
                        WP8              WP9                 WP10+
                   SCAL Learning    Contract & Infra     Architectural
                       Face           Closure             Expansion
                   ─────────────   ─────────────────    ─────────────
State:             accepted        accepted              unscheduled

Delivers:          Curriculum      Typed DTOs (8)       Scheduler impl
                   Evaluation      Naming fixes          Multi-Fidelity
                   World-Model     Facade surface        Capability Graph
                   boundary        Manifest registry     Worldline
                                   Guard allowlist       Experiment Gen
```

### Post-WP9 Architectural Expansion (unscheduled, unordered)

These are the larger architectural items identified in temp-02 and earlier
reviews. None has a hardcoded WP number. Priority should be decided after WP9
closure based on project needs at that time.

| Direction | Prerequisites | Nature |
|-----------|--------------|--------|
| Scheduler Semantics Implementation | WP2.5 (spec complete) | C++ code: StateStore, EventQueue, ClockDomain, Barrier in runtime |
| Multi-Fidelity Architecture + ModelProvider | WP6 + WP7 (backend profiles + multifidelity entry conditions) | Doc + code: fidelity profiles, ModelProvider abstraction, same scenario → different fidelity |
| Capability Graph Migration | WP2 (contract ontology) + WP9 (AgentRole DTO) | Doc + code: `spawn_unit(type_name)` → `spawn_platform({capabilities...})` |
| Worldline / Counterfactual Architecture | WP2.5 (deterministic replay) + state snapshot/restore | Doc + code: branch point, counterfactual rollout, causal difference |
| Experiment Generation Architecture | WP8 (curriculum + evaluation) | Doc + code: scenario generator, adversary generator, capability profiler, generalization tester |

## 5. Immediate Next Actions

1. **Evaluate post-WP9 priority** — choose one of the unscheduled WP10+
   directions based on project needs.
2. **Keep `INF-6` visible** — do not treat terminal effects capture as silently
   closed until a later owner adds the maintained recorder seam.

## 6. Closure Note

This document does not reopen any accepted work package. All items in WP9 are
extracted from deferred/follow-up sections of existing acceptance reviews. The
post-WP9 roadmap is advisory and carries no hardcoded WP numbering — it exists
to prevent these directions from being lost, not to prescribe their order.
