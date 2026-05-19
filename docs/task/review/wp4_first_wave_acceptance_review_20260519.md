# WP4 First Wave Acceptance Review

Status: `2026-05-19` first-wave acceptance completed.

Scope: WP4-A surface inventory, WP4-B/C engagement and step/lifecycle probe,
WP4-D/E policy/binding probe.

Related documents:

- [WP4 facade alignment](../simulation_architecture/facade_alignment_wp4_20260519.md)
- [WP4-A surface inventory draft](../simulation_architecture/wp4_surface_inventory_wp4a_20260519.md)
- [WP4-B/C engagement-step alignment notes](../simulation_architecture/wp4_engagement_step_alignment_notes_20260519.md)
- [WP4-D/E policy-binding alignment notes](../simulation_architecture/wp4_policy_binding_alignment_notes_20260519.md)
- [WP4 surface inventory cluster](../simulation_architecture/wp4_surface_inventory_cluster_20260519.md)
- [WP4 engagement-step cluster](../simulation_architecture/wp4_engagement_step_cluster_20260519.md)
- [WP4 policy-binding cluster](../simulation_architecture/wp4_policy_binding_cluster_20260519.md)

## 1. Acceptance Decision

WP4 first-wave work is accepted as a successful discovery and surface-freeze
input. It is not the completion of WP4 implementation.

The first wave produced enough evidence to start the second wave:

1. `WP4-A` now has a canonical surface inventory draft with maintained,
   compatibility, diagnostics-only, and deferred classifications.
2. `WP4-B/C` has bounded evidence on engagement export, producer coverage,
   diagnostics piggybacking, and execution-step/lifecycle gaps.
3. `WP4-D/E` has a policy/binding discovery map for `AgentRole`, action
   intent, coordination intent, observation/belief paths, and compatibility
   escape hatches.

## 2. Accepted Findings

| Area | Accepted result | Routing |
|------|-----------------|---------|
| Surface classification | `ObservationViewSpec`, `ObservationPacket`, `DecisionBelief`, reward/termination/lifecycle surfaces are maintained concepts; `RuntimeFacade::runtime()` and raw `WorldBatchRuntime` are compatibility-only; `DiagnosticsTrace` remains diagnostics-only piggyback for WP4. | Use as the second-wave vocabulary. |
| Deferred agent/action concepts | `ActionIntentPacket`, `CoordinationIntentPacket`, and `AgentRole` remain deferred from C++ facade promotion until WP4-D creates adapter shims and contract sketches. | Route to policy/agent shim cluster. |
| Engagement producer coverage | `track_packets`, recent launch/effects/damage events, and diagnostics traces have current producers; `launch_requests` and `munition_lifecycle_packets` are explicit deferred placeholders. | Route to facade evidence tests and WP4-F documentation. |
| Diagnostics boundary | Engagement diagnostics are piggyback evidence, not a complete diagnostics logging surface. | Keep WP4 scope narrow; promote dedicated diagnostics surface only if WP5 trace gates require it. |
| Step/lifecycle coverage | `ExecutionBatchStepResult` exposes step result, reward, terminated/truncated, status, termination reason, reward JSON, step info, controller state changed flag, and observation packet. | Add semantic evidence tests and document typed DTO gaps. |
| Step/lifecycle gaps | Missing typed reward fact/shaping attribution, termination reason source, observation snapshot/barrier/source-time provenance, and top-level episode authoritative-source marker. | Do not churn facade signatures until second-wave tests clarify minimum DTO additions. |
| Policy/binding map | Current policy/batch/multi-agent/leader/director paths are mostly `compatibility_adapter`; Python bindings mirror stable facade DTOs but should not bind `AgentRole`, `DecisionBelief`, or intent packets yet. | Route to Python shim and oracle-audit cluster. |
| World-truth risk | Direct `sim.*`, `RuntimeFacade.runtime()`, `WorldBatchRuntime.world(...)`, visual/candidate helpers, and teacher/oracle paths must not become maintained policy input. | Route to compatibility guard tests. |

## 3. Required Second-Wave Work

Second-wave WP4 work should be implementation-light but test/evidence-heavy:

| Cluster | Purpose |
|---------|---------|
| `WP4-G Facade Evidence Gates` | Add or document focused tests for engagement producer coverage, deferred placeholders, diagnostics piggybacking, multi-world retagging, and current step-result semantic shape. |
| `WP4-H Information And Agent Shim` | Draft Python-side `AgentRole`, `ActionIntent`, and `CoordinationIntent` shims or notes, add observation provenance labels, and identify oracle paths as diagnostics-only. |
| `WP4-I Compatibility Guard And Integration` | Add architecture/doc gates for raw-runtime compatibility boundaries, integrate accepted first-wave findings into WP4 docs, and prepare the handoff to WP5. |

## 4. Non-Blocking Open Questions

These remain open but do not block second-wave dispatch:

1. Whether `ObservationViewSpec` becomes a C++ DTO during WP4 or remains a
   documented policy/test-owned concept until WP5 metadata enforcement.
2. Whether `DiagnosticsTrace` receives a dedicated facade query/export during
   WP4 or remains engagement-piggyback evidence until WP5.
3. Whether `RuntimeCapabilities` remains deferred to backend profile work.
4. What exact `RuntimeFacade` method-count rule triggers a future split.
5. Whether ownship position inside `AgentObservation` is maintained by default
   or only when a view spec explicitly allows ownship truth-state projection.

## 5. Acceptance Gate

The first wave is accepted because it satisfies the dispatch-sheet exit
criteria:

1. Surface names and classifications are available for later workers.
2. Engagement and step/lifecycle gaps are specific enough to test.
3. Policy and binding gaps are classified without premature C++ surface
   expansion.
4. Compatibility-only and diagnostics-only paths are clearly separated from
   maintained policy/training truth.
