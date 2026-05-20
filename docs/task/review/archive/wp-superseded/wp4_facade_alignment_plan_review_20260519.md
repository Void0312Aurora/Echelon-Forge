# WP4 Facade Alignment — Plan Review

Status: `2026-05-19` plan review completed.
Scope: WP4 facade alignment plan — surface map coverage, architecture document alignment, gap identification.

Related documents:

- [simulation system architecture design](../../plan/architecture/simulation_system_architecture_design.md) — Sections 3, 6, 7, 9, 11
- [WP3 engagement pilot acceptance review](wp3_engagement_pilot_acceptance_review_20260519.md)
- [WP4 facade alignment plan](../../task/simulation_architecture/facade_alignment_wp4_20260519.md)
- [architecture plan review](architecture_plan_review_20260519.md)

## 1. Review Scope

This review assesses the WP4 facade alignment plan against the architecture design document's requirements for the facade layer and cross-layer contracts. The architecture document defines requirements across four sections:

- **Section 3** (Target Layer Model): Facade as the stable request/result API between frontends/adapters and simulation engine.
- **Section 6** (System Layer Coupling Model): Eight cross-layer contracts with specific ownership, field requirements, and governance rules.
- **Section 7** (Contract Taxonomy): Sixteen contract families with defined purpose and long-term owner.
- **Section 9** (Backend And Performance Policy): Device-resident state behind contracts, backend capability exposure through facade.
- **Section 11** (Validation Gates): Ten architecture validation gates.

## 2. Coverage Matrix

### 2.1 Fully Covered

| Architecture requirement | WP4 provision | Assessment |
|--------------------------|---------------|------------|
| Facade as stable request/result API (Section 3) | Section 3 Facade Surface Map — 11 surfaces with maintained shape and validation gate | Matches the architecture doc's target layer model. Surface map format is clear and actionable. |
| `ObservationPacket` (Section 6) | `ObservationBatchRequest` / `ObservationBatchPacket` → "Keep as the maintained observation surface" with snapshot version, source time, include flags | Present and correctly owned by facade. |
| `ActionIntentPacket` / `ActionHoldPolicy` (Section 6) | Explicitly identified as gap → WP4-D, minimum shape includes effective time, validity window, hold/expiry policy, merge policy, action family | Correctly scoped. The minimum shape fields match the architecture doc's cross-layer request fields (effective_time, valid_until, merge_policy). |
| `CoordinationIntentPacket` (Section 6) | Explicitly identified as gap → WP4-D, minimum shape includes source type/id, roster, target refs, update clock, merge policy, produced tasking fields | Correctly scoped. Matches architecture doc's requirement for scripted/learned/human directors. |
| `RewardSpec` / `RewardReport` (Section 6: fact/shaping split) | "Align the maintained result shape with explicit fact/shaping attribution" — fact snapshot version, fact terms, shaping terms, term owner/source | Matches the architecture doc's fact boundary criterion: "A quantity is a simulation fact if and only if it depends only on authoritative simulation state plus static mission/content data." |
| `TerminationSpec` / `EpisodeStatus` (Section 6: terminated/truncated split) | "Align the maintained result shape with explicit reason-source attribution" — reason, reason source, snapshot version, mirrored phase | Matches the architecture doc's requirement: "Simulation owns semantic termination; policy/test/orchestration may request truncation." |
| `EpisodeLifecycleContract` (Section 6) | "Keep the compiled/facade state authoritative and the adapters mirrored" — phase, step count, reset transition id, authoritative source | Matches architecture doc: "Adapters never advance a private authoritative phase machine." |
| `merge_policy` (Section 6: 5 enum values) | Listed under ActionIntentPacket minimum shape | Present in the facade surface vocabulary. |
| Architecture Law #1 (frontend depends on facade) | Gate 2: "Maintained policy/test paths do not depend on `RuntimeFacade::runtime()` or raw `WorldBatchRuntime`" | Direct enforcement of Law #1. |
| Architecture Law #7 (facade doesn't copy kernel) | Section 2 Non-Goals: "Collapsing compatibility adapters into implicit calls" | Prevents method-by-method kernel mirroring. |
| Engagement export world-safety (Section 10) | WP4-B: "Keep engagement export world-safe and make the packet shell explicit" | Maintains the WP3 pilot's world-safety property. |
| Python binding mirror | WP4-E: "Keep Python bindings and helper layers aligned with the maintained facade surface" | Ensures `ef_py` tracks C++ facade surface. |
| Compatibility escape hatch governance | `RuntimeFacade::runtime()` / raw `WorldBatchRuntime` explicitly listed as "compatibility-only" | Architecture tests already enforce this. |

### 2.2 Partially Covered

| Architecture requirement | WP4 status | Gap |
|--------------------------|------------|-----|
| `ObservationViewSpec` (Section 6: schema versioning, required/optional fields, checkpoint compatibility) | Not listed as an independent surface. `ObservationBatchRequest` has only `include_*` boolean flags. | The architecture doc defines `<major>.<minor>` version format, required/optional field declarations, and rules for minor-compatible vs major-incompatible changes. These are absent from WP4's surface map. |
| Cross-layer request fields (Section 6: `source_layer`, `source_id`, `input_snapshot_version`) | Partially present in ActionIntentPacket minimum shape | `source_layer` and `source_id` are not explicitly listed, though `input_snapshot_version` is implied by the observation snapshot version linking. |
| `RuntimeCapabilities` (Section 7 implicit: backend capability exposure) | `RuntimeCapabilities` struct exists but `capabilities()` returns empty `RuntimeCapabilities{}` | WP4 does not plan to implement `capabilities()` query. The struct is a placeholder. |

### 2.3 Not Covered

| Architecture requirement | Gap description | Severity |
|--------------------------|-----------------|----------|
| `DiagnosticsTrace` as independent facade surface (Section 7) | The architecture doc lists `DiagnosticsTrace` as a contract family with owner `core/engine` and facade contracts. WP3 implemented the data structure. WP4's surface map has no dedicated diagnostics/trace endpoint. | Medium. Diagnostics export currently piggybacks on `EngagementEventPacket`. A dedicated surface would separate explainability concerns from engagement data. |
| `BackendCapabilityFacade` (Section 9) | The architecture doc requires device-resident state paths to expose capabilities through facade contracts. WP4's surface map has no backend capability surface. | Low for WP4. GPU code is gated behind `EF_ENABLE_CUDA_EXPERIMENTS`. Can be deferred to the backend profile work package. |
| Observation schema compatibility rules (Section 6: minor vs major version changes) | The architecture doc specifies that checkpoint loading must reject major-version mismatches and that minor-version differences may load with default-filling for missing optional fields. These rules are not reflected in WP4. | Medium. These rules become critical when policy checkpoints need to survive observation schema evolution. Should be added to `ObservationViewSpec` design. |
| Facade endpoint governance (temp-01 suggested: consumer group, request DTO, result DTO, snapshot/version semantics, compatibility adapter, deprecation rule, mainline/diagnostic/experimental classification) | WP4's surface map defines "Minimum maintained shape" and "Validation gate" per surface, but does not mandate per-endpoint metadata. | Low for WP4. Endpoint governance can be added incrementally. The surface map format is a reasonable starting point. |

## 3. Structural Assessment

### 3.1 Work package decomposition quality

WP4 decomposes into 6 sub-packages (WP4-A through WP4-F) with clear write scopes, parallelism rules, and exit artifacts. The dependency graph (A → B/C/D/E → F) is simple and avoids circular dependencies. This is well-structured.

One observation: WP4-A (Facade Surface Inventory) is correctly placed as the first work package — it defines the shared vocabulary before any implementation work begins. This is the same pattern that made WP3-A (Contract DTO Scaffold) effective.

### 3.2 Write-scope rules

The write-scope rules (Section 7) are specific and enforceable:
- "facade worker owns `src/runtime/facade/*`"
- "binding worker owns `src/interfaces/python/bindings_runtime.cpp`"
- "policy/adapter worker owns `python/rl/runtime/*`, `python/rl/control/*`, `gym_envs/*`"
- Rule 6 explicitly prevents parallel edits to `simulation_kernel_weapon_api.cpp`

This is a direct lesson learned from WP3's write-scope rules, which prevented shared-kernel-file conflicts between air and naval adapter workers.

### 3.3 Relationship to scheduler semantics gap

WP4 correctly scopes itself to facade surface alignment and does not attempt to define scheduler semantics. However, two WP4 surfaces have implicit dependencies on unfrozen scheduler concepts:

- `ActionHoldPolicy` requires hold-last/interpolation/expiry semantics across control-rate and physics-rate ticks — this depends on clock domain definitions that don't yet exist.
- `ObservationViewSpec` requires snapshot version semantics — this depends on state shard versioning rules that don't yet exist.

WP4 can proceed with these surfaces by defining the contract shapes (field layouts, enum values) while leaving the runtime enforcement to the scheduler semantics freeze. The WP4 document should explicitly note this dependency.

### 3.4 Facade monolith risk

WP4 chooses the path of "narrowing and naming existing surfaces" rather than splitting `RuntimeFacade` into multiple facade classes. This is the correct choice for the current project scale (~30 public methods). However, the WP4 surface map already identifies 11 distinct surfaces. As new surfaces are added (ActionIntentPacket, CoordinationIntentPacket), the monolithic class risk increases.

Recommendation: Add a split threshold rule to WP4-A output — when `RuntimeFacade` exceeds 40 public methods, split into `RuntimeSessionFacade`, `WorldSetupFacade`, `ExecutionStepFacade`, `ObservationFacade`, `DiagnosticsFacade`, `EngagementFacade`, and `BackendCapabilityFacade`.

## 4. Recommendations

### Add to WP4-A (Facade Surface Inventory)

| Item | Rationale |
|------|-----------|
| `ObservationViewSpec` as independent surface | Architecture Section 6 defines it as policy/test-owned with schema version, required/optional fields, and checkpoint compatibility rules. Currently missing from surface map. |
| `DiagnosticsTrace` as independent facade surface | Architecture Section 7 lists it as a contract family. WP3 implemented the data structure. Deserves a dedicated query endpoint separate from engagement export. |
| Facade split threshold rule | Defer splitting to ~40 methods, but document the target split architecture now. |
| Per-surface dependency declaration on scheduler semantics | Surfaces that depend on clock domains or state versioning should note this explicitly. |

### Add to WP4-C (Step And Lifecycle Alignment)

| Item | Rationale |
|------|-----------|
| Observation schema compatibility rules | Architecture Section 6 defines `<major>.<minor>` version format and checkpoint compatibility behavior. These should be documented in `ObservationViewSpec` design. |

### Defer to backend profile work package

| Item | Rationale |
|------|-----------|
| `BackendCapabilityFacade` | Architecture Section 9 requires it, but GPU code is experimental. Defer to post-WP5. |

## 5. Acceptance Gate Coverage

WP4 defines 8 acceptance gates. Cross-referencing with the architecture document's 10 validation gates (Section 11):

| Architecture gate | WP4 gate | Status |
|-------------------|----------|--------|
| 1. Docs name stage, owner, packets | Implicit in surface map | Covered |
| 2. Docs name read/write sets, clock, latency, sync | Not in WP4 scope (belongs to scheduler semantics) | Correctly excluded |
| 3. Public access through facade | Gate 1, Gate 2 | Covered |
| 4. Architecture tests prevent raw runtime access | Gate 2 | Covered |
| 5. Include/build boundaries | WP4-E binding alignment | Covered |
| 6. CPU semantic baseline | Section 2 Non-Goals | Covered |
| 7. Cross-domain smoke | Gate 7 (local validation) | Covered |
| 8. Diagnostics explainability | Gate 8 | Covered |
| 9. Cross-layer contract ownership | Gates 3-5 | Covered |
| 10. Policy/test adapters use facade APIs | Gates 2, 5 | Covered |

All 10 architecture gates are addressed, either directly by WP4 gates or correctly excluded as out of WP4 scope.

## 6. Conclusion

WP4's facade alignment plan is well-scoped and well-structured. It covers approximately 80% of the architecture document's facade and cross-layer contract requirements. The three main gaps are:

1. **`ObservationViewSpec` missing as independent surface** — the architecture doc's schema versioning and checkpoint compatibility rules need a home.
2. **`DiagnosticsTrace` missing as independent facade surface** — currently rides on engagement export but deserves its own endpoint.
3. **Implicit dependency on unfrozen scheduler semantics** — `ActionHoldPolicy` and `ObservationViewSpec` snapshot semantics need clock domain and state versioning definitions that don't yet exist.

These can be resolved by adding three items to WP4-A's surface inventory without restructuring the work package decomposition. The WP4 plan is ready to proceed with these additions.
