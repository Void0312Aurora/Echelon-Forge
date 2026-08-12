# Standards-Implementation Alignment Review

Language:
- English canonical: `standards_implementation_alignment_review_20260610.md`
- Chinese companion: [standards_implementation_alignment_review_20260610.zh.md](standards_implementation_alignment_review_20260610.zh.md)

Status: `2026-06-10` alignment review of `docs/standards/` against current implementation.

Source: cross-reference audit of all maintained standards documents under
`docs/standards/` against `src/`, `gym_envs/`, `python/`, and `tests/` surfaces.
Task-document maturity and acceptance status are out of scope except where a
standard explicitly freezes a concrete runtime contract.

## 1. Purpose

This review answers:

1. Does the current implementation respect the standards ownership hierarchy
   (foundation → joint → services → air/naval/ground specialization → model)?
2. Do the concrete field-level contracts documented in standards match the
   runtime/test artifacts?
3. Which standards documents are stale relative to the implementation?
4. Which semantic mismatches between standard and implementation need to be
   resolved?

## 2. Verdict

**The standards tree and the current implementation are materially aligned in
architecture and field-level contracts.** The layer hierarchy is faithfully
encoded in the `src/components/` directory structure, the `MissionCommand`
owner-slice split, the `TaskOrder`/`LeaderIntent`/`PilotReport` core-and-domain
layering, and the service-profile enum vocabulary.

Six deviations were found. One is a semantic mismatch (ground tasking), five are
documentation lag where the implementation has moved ahead of the standard. None
is a blocker for declaring the standards tree as the project's authoritative
ownership map.

## 3. Evidence Map

### 3.1 Layer Hierarchy — PASS

| Standard Layer | Standard Reference | Implementation Path | Status |
| --- | --- | --- | --- |
| Foundation | `docs/standards/foundation/conventions.md` | ENU coordinates, NAV degrees, meters/seconds used throughout C++ and Python | Aligned |
| Foundation | `docs/standards/foundation/gradient_realism_principles.zh.md` | G0–G7 labels referenced in task docs and scene configs | Aligned |
| Foundation | `docs/standards/foundation/realism_authority_boundary.zh.md` | Authority fields gate A2/M2/M3 release behavior | Aligned |
| Joint | `docs/standards/joint/command_and_modeling_baseline.md` | `src/components/tasking/common/core_tasking_enums.h` — all 7 enums present | Aligned |
| Joint | `docs/standards/joint/command_link_and_reporting_baseline.md` | `src/components/command/common/mission_command_core.h` — core DTO present | Aligned |
| Services | `docs/standards/services/` | 4 service profiles defined; `ServiceProfile` enum matches | Aligned |
| Air | `docs/standards/air/` | `src/components/domains/air/` — command/tasking DTOs + tests | Aligned |
| Naval | `docs/standards/naval/` | `src/components/domains/naval/` — command/tasking DTOs + tests | Aligned |
| Ground | `docs/standards/ground/` | `src/components/domains/ground/` — command/tasking DTOs + tests | Aligned |
| Model | `docs/standards/model/policy_execution_architecture.md` | 18-component implementation map verified; all files exist | Aligned |
| Bridge | `docs/standards/bridge/` | 5-stage runtime workflow matches `gym_envs/scenario_loader/` | Aligned |
| Governance | `docs/standards/governance/` | Bilingual, subagent, WP closure policies all registered | Aligned |

### 3.2 Field-Level Contracts — PASS

| Contract | Standard Doc | Code Location | Fields Match | Notes |
| --- | --- | --- | --- | --- |
| `MissionCommandCore` | `joint/command_link_and_reporting_baseline.md` §3 | `src/components/command/common/mission_command_core.h` | 11/11 core fields present | 4 extra fields not in standard: `threat_state`, `assigned_target_track_id`, `assigned_target_source_id`, `assigned_target_snapshot_time_s` |
| `MissionCommandAir` | `joint/command_link_and_reporting_baseline.md` §3 | `src/components/domains/air/command/mission_command_air.h` | 11/11 air fields present | Uses typed enums instead of raw ints — improvement over standard |
| `MissionCommandNaval` | `joint/command_link_and_reporting_baseline.md` §3 | `src/components/domains/naval/command/mission_command_naval.h` | 7/7 naval fields present | Structuring directives added beyond standard baseline |
| `PilotAction` | `air/act.md` | `src/components/command/pilot_action.h` | 19/19 fields present | Header explicitly cites `act.md` |
| `TaskOrderCore` | `joint/command_and_modeling_baseline.md` §5 | `src/components/tasking/common/task_order_core.h` | All 13 common-core fields present | — |
| `PilotReportCore` | `air/rep.md` | `src/components/tasking/common/pilot_report_core.h` | All 17 core fields present | — |
| `air_combat_hybrid_v1` | `air/act.md` §A5 | `gym_envs/universal_env_parts/air_combat_event_action.py` | 12-dim transport matches | A5 event-action FSM runtime present and tested |
| Mission obs modes | `air/obs.md` | `python/mission_obs_taxonomy.py` | 6/6 air modes present | 3 modes added since standard: `naval_screen_station_v1`, `air_combat_c2_roe_v1`, `air_combat_c2_roe_v2` |

### 3.3 Bilingual Documentation — PASS

All 25 standards documents under `docs/standards/` have a `.zh.md` companion.
No orphaned canonical files. Compliant with
`docs/standards/governance/bilingual_documentation_policy.zh.md`.

### 3.4 Model Architecture Implementation Map — PASS

All 18 implementation surfaces listed in
`docs/standards/model/policy_execution_architecture.md` §Current Implementation Map
exist at the stated paths:

- `python/mission_obs_taxonomy.py` — present
- `gym_envs/scenario_loader/mission_observation.py` — present
- `python/models/transformer.py` — present (`TransformerExtractor`, `TemporalTransformerExtractor`)
- `python/rl/policy_algo/policies.py` — present (`HierarchicalMoEExecutionPolicy`, `_HybridActionDistribution`, etc.)
- `python/rl/policy_algo/hmoe_routing.py` — present
- `gym_envs/universal_env_parts/air_combat_event_action.py` — present
- `python/rl/policy_algo/first_event_hazard.py` — present
- `python/rl/policy_algo/first_event_rollout_buffer.py` — present
- `python/rl/policy_algo/ppo_adaptive_kl.py` — present
- All probe/diagnostic paths under `tools/diagnostics/` — present

## 4. Gap Inventory

### GAP-001: Ground Tasking Semantic Mismatch — `TASK_MOVE` ≠ `HoldStatic`

| Field | Value |
| --- | --- |
| Severity | **MEDIUM** |
| Standard | `docs/standards/ground/minimal_task_structure.zh.md` — `TASK_MOVE` means "机动 (maneuver toward route, phase line, or objective reference)" |
| Implementation | `src/components/domains/ground/tasking/ground_tasking_enums.h` — `GroundTaskMode::HoldStatic = 1` |
| Impact | The only way to encode a `TASK_MOVE` intent is through `HoldStatic`, but `hold` and `move` are contradictory. `OccupyStatic` ↔ `TASK_OCCUPY` and `SupportStatic` ↔ `TASK_SUPPORT` are semantically consistent. |
| Recommendation | Either rename `HoldStatic` → `MoveStatic` (preserving the G0 static limitation), or add a separate `MoveDynamic` enum value and document it as deferred. Update the standard if the G0 scope has been intentionally narrowed to static-only tasking. |
| Reference | `ground_tasking_enums.h:3-8`, `minimal_task_structure.zh.md:66-74` |

### GAP-002: Mission Observation Modes Outpaced The Standard

| Field | Value |
| --- | --- |
| Severity | **LOW** |
| Standard | `docs/standards/air/obs.md` — documents 6 air-specific modes (`basic` through `nav_v2_cooperative_takeoff_v1`) |
| Implementation | `python/mission_obs_taxonomy.py` — 9 modes; added `naval_screen_station_v1`, `air_combat_c2_roe_v1`, `air_combat_c2_roe_v2` |
| Impact | The 3 new modes are in active use by runtime and tests but have no standards-level ownership statement. `naval_screen_station_v1` should be owned by the naval specialization; `air_combat_c2_roe_v1/v2` should be owned by air specialization. |
| Recommendation | Update `air/obs.md` to register `air_combat_c2_roe_v1` and `air_combat_c2_roe_v2`. Create or update a naval observation contract to register `naval_screen_station_v1`. Document field lists for the new modes. |
| Reference | `mission_obs_taxonomy.py:9-11`, `obs.md:35-42` |

### GAP-003: `MissionCommandCore` Contains Undocumented Fields

| Field | Value |
| --- | --- |
| Severity | **LOW** |
| Standard | `joint/command_link_and_reporting_baseline.md` §2–3 — lists known core fields |
| Implementation | `src/components/command/common/mission_command_core.h` — adds `threat_state`, `assigned_target_track_id`, `assigned_target_source_id`, `assigned_target_snapshot_time_s` |
| Impact | These fields are in the active runtime contract (`mission_command_codec.cpp` serializes them) but their ownership (joint, sensor/track, or engagement) is not defined in the standard. |
| Recommendation | Add these fields to `joint/command_link_and_reporting_baseline.md` §2 with ownership classification. If they cross-cut sensor/track concerns, reference the pending sensor/track standard. |
| Reference | `mission_command_core.h:19-22`, `command_link_and_reporting_baseline.md:27-45` |

### GAP-004: Standard Document Dates Are Stale

| Field | Value |
| --- | --- |
| Severity | **LOW** |
| Scope | Several authoritative standards carry dates that predate the latest implementation changes they describe: |

| Document | Standard Date | Last Implementation Change | Drift |
| --- | --- | --- | --- |
| `air/act.md` | 2026-06-02 | 2026-06-08 (A5 event-action runtime acceptance) | 6 days |
| `air/obs.md` | 2026-05-18 | 2026-06-04 (C2/ROE mode additions) | 17 days |
| `bridge/runtime_workflow_and_contract_baseline.md` | 2026-05-18 | 2026-06-08 | 21 days |
| `joint/command_and_modeling_baseline.md` | no date | — | Undated |
| `naval/minimal_task_structure.md` | no date | — | Undated |

| Impact | Readers cannot determine from the standard alone whether it reflects the current runtime contract. |
| Recommendation | Add or refresh date stamps on `joint/command_and_modeling_baseline.md`, `joint/command_link_and_reporting_baseline.md`, `naval/minimal_task_structure.md`, and `air/obs.md`. The `air/act.md` stamp is recent but should acknowledge A5 in the status line. |
| Reference | Standards file headers |

### GAP-005: Modularization Plan Not Aligned With Current `src/` Layout

| Field | Value |
| --- | --- |
| Severity | **LOW** (document self-declares as "active planning, not current runtime contract") |
| Standard | `docs/standards/planning/modularization_plan.md` — target `core/` → `systems/` → `interfaces/` with one-way dependencies |
| Implementation | `src/components/` is the dominant organizational layer; `systems/` is less populated than planned; `core/` responsibilities are split across `core/engine/`, `core/mission/`, and `runtime/facade/` |
| Impact | The plan can confuse readers who expect it to describe the current code. |
| Recommendation | Either (a) update the plan to reflect the actual `components/domains/{air,naval,ground}/` tri-domain split as a realized target, or (b) archive it with a forward pointer if the project direction has shifted. |
| Reference | `modularization_plan.md:53-59` |

### GAP-006: New MLF-3 Test File Has No Corresponding Standards Entry

| Field | Value |
| --- | --- |
| Severity | **LOW** (task-document level, not standards-defect) |
| Observation | `tests/runtime/air_combat/test_warhead_spatial_component_projection.py` is newly added (untracked). The warhead effects spatial projection contract is not captured in any weapons/damage specialization standard under `docs/standards/`. |
| Impact | If the spatial projection contract stabilizes, it needs a standards-level ownership slot. Currently the foundation-level `realism_authority_boundary.zh.md` provides authority gating but not field-level contract documentation. |
| Recommendation | When the MLF-3 warhead effects work reaches acceptance, add a weapon-effects specialization entry under `docs/standards/air/` or a new `docs/standards/weapons/` directory. Do not let the contract live only in task documents and test files. |
| Reference | `tests/runtime/air_combat/test_warhead_spatial_component_projection.py`, `docs/systems/effects/reviews/a2_high_fidelity_damage_model_20260602/missile_lethality_evidence_20260619/missile_lethality_warhead_effects/` |

## 5. Non-Gaps (Verified Aligned)

The following areas were checked and found to require no action:

| Area | Check | Result |
| --- | --- | --- |
| `CommandRelationship` enum | Match `joint/command_and_modeling_baseline.md` §2 (COCOM, OPCON, TACON, ADCON, support, coordinating authority, DIRLAUTH) | All 7 values present |
| `CoordinationMode` enum | Match joint standard §5 | All 8 values present |
| `ServiceProfile` enum | Match `services/` four profiles | AirForce, Army, Navy, MarineCorps |
| `MissionCommand` owner-slice pattern | Air/Naval/Ground each have `OwnerSlice` typedef + `kMissionCommand*OwnedDomainSlice` constexpr | Consistent across domains |
| `PilotReportCore` fields | Match `air/rep.md` §Core Report Fields | All 17 fields present |
| `PilotReportAir` fields | Match `air/rep.md` §Air Report Extension Fields | All 7 fields present |
| C++ roundtrip tests | Standards require roundtrip preservation for air/naval/ground command fields | Tests present for all three domains |
| `air_combat_hybrid_v1` event-action FSM | `air/act.md` §A5 defines engagement state machine | `air_combat_event_action.py` implements full FSM |
| `CommandLink` and `DataLink` | `joint/command_link_and_reporting_baseline.md` §4–5 | Headers present: `command_link.h`, `command_link_qos.h`, `data_link.h` |
| `fidelity_profile_contracts.h` | Foundation gradient realism principles | 6 labels defined, `exact_evaluation` admitted |

## 6. Recommended Action Order

| Priority | Gap ID | Action | Effort |
| --- | --- | --- | --- |
| 1 | GAP-001 | Resolve ground `TASK_MOVE` ↔ `HoldStatic` mismatch (rename enum or update standard) | Small |
| 2 | GAP-002 | Register `air_combat_c2_roe_v1/v2` and `naval_screen_station_v1` in observation standards | Small |
| 3 | GAP-003 | Document `threat_state`, `assigned_target_track_id`, `assigned_target_source_id`, `assigned_target_snapshot_time_s` in joint standard | Small |
| 4 | GAP-004 | Refresh date stamps on stale standards documents | Trivial |
| 5 | GAP-005 | Decide modularization plan disposition (update or archive) | Medium |
| 6 | GAP-006 | Create weapon-effects standards entry when MLF-3 reaches acceptance | Medium |

## 7. Validation Notes

The alignment was verified by:

- `find` traversal of `src/components/` comparing directory structure against standards ownership hierarchy
- Field-by-field comparison of `MissionCommand*`, `TaskOrder*`, `PilotReport*`, `PilotAction` headers against standard field lists
- Enum value comparison (`core_tasking_enums.h`, `ground_tasking_enums.h`, `naval_tasking_enums.h`, `air_tasking_enums.h`) against standard vocabularies
- `python/mission_obs_taxonomy.py` mode list comparison against `air/obs.md` mode table
- Model architecture implementation map file-existence check (18 paths, all present)
- Bilingual companion existence check (25 pairs, all present)

## 8. Related Documents

- [Standards Documentation Overview](../../standards/README.md)
- [Document Alignment Map](../../standards/overview/document_alignment_map.md)
- [Joint Command and Modeling Baseline](../../standards/joint/command_and_modeling_baseline.md)
- [Joint Command-Link and Reporting Baseline](../../standards/joint/command_link_and_reporting_baseline.md)
- [Runtime Workflow and Contract Baseline](../../standards/bridge/runtime_workflow_and_contract_baseline.md)
- [Air Platform Specialization](../../standards/air/README.md)
- [Naval Specialization](../../standards/naval/README.md)
- [Ground Specialization](../../standards/ground/README.md)
- [Model Architecture Baseline](../../standards/model/policy_execution_architecture.md)
- [Documentation System Readiness Review](documentation_system_readiness_review_20260601.md)
