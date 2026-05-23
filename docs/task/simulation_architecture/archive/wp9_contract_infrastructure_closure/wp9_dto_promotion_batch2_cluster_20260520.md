# WP9-B DTO Promotion Batch 2

Status: `2026-05-20` complete / accepted WP9 parallel stream.

Language:

- English canonical: `wp9_dto_promotion_batch2_cluster_20260520.md`
- Chinese companion:
  [wp9_dto_promotion_batch2_cluster_20260520.zh.md](wp9_dto_promotion_batch2_cluster_20260520.zh.md)

Inputs:

- [WP9 contract and infrastructure closure](contract_infrastructure_closure_wp9_20260520.md)
- [simulation system architecture design](../../../plan/architecture/simulation_system_architecture_design.md)
- [WP4 facade alignment acceptance review](../../review/archive/wp-acceptance/wp4_facade_alignment_acceptance_review_20260519.md)
- [WP5 information/belief review](../../review/archive/wp-superseded/wp5_information_belief_acceptance_review_20260519.md)
- [WP8 learning face](../wp8_learning_face/learning_face_wp8_20260520.md)

## 1. Purpose

WP9-B promotes the second DTO batch for policy, coordination, role, and belief
boundaries. These DTOs make the agentic side explicit without allowing raw ECS
or hidden truth mutation.

The stream covers:

- DTO-5 `ActionIntentPacket`
- DTO-6 `CoordinationIntentPacket`
- DTO-7 `AgentRole`
- DTO-8 `DecisionBelief`

## 2. Required DTO Shape

| DTO | Required fields | Ownership rule |
|-----|-----------------|----------------|
| `ActionIntentPacket` | `source_id`, `effective_time_s`, `valid_until_s`, `target`, `action_family`, `merge_policy`, action-interface discriminator | Policy emits intent; runtime/facade translates it at command/control injection points. |
| `CoordinationIntentPacket` | `source_type`, `source_id`, `target_roster`, `update_clock`, `merge_policy`, produced tasking/leader-intent references | Scripted, learned, and human directors enter only through tasking/command facade paths. |
| `AgentRole` | `role`, `authority_scope`, `information_state_source`, `decision_model_ref`, `action_interface` | A policy model is not an agent by itself; it is attached to a typed role boundary. |
| `DecisionBelief` | `belief_id`, `source_observation_versions`, `memory_or_estimator_ref`, `confidence_shape`, `maintained_status`, diagnostics reason | Maintained belief must derive from declared observations or memory/estimator state. Truth/raw ECS use is diagnostics-only. |

## 3. Implementation Route

Recommended route:

1. Add typed C++ contract structs in a policy/intent/decision contract header.
2. Keep the DTOs passive and serializable; do not directly mutate runtime state.
3. Add Python bindings and focused shape/default tests.
4. Add architecture checks proving `DecisionBelief` and `ObservationPacket`
   remain distinct.
5. Add compatibility notes for any existing Python shim labels that remain.

Preferred write scope:

- `src/runtime/contracts/*`
- `src/runtime/facade/runtime_facade_types.h`
- `src/interfaces/python/bindings_runtime.cpp`
- `python/rl/runtime/*` only for compatibility label alignment
- `tests/runtime/bindings/*`
- `tests/runtime/test_agent_shim.py`
- `tests/architecture/*`

Collision warning:

- Shared binding glue with WP9-A must be coordinated. If both streams are
  active, WP9-B should prefer adding the C++ contracts and tests first, then
  leave shared Python module wiring to WP9-E unless assigned integration owner.

## 4. Work Items

| Stream | Required output | Budget |
|--------|-----------------|--------|
| `WP9-B1 ActionIntentPacket` | Typed action intent with validity window, action family, and cross-layer `merge_policy`. | High. |
| `WP9-B2 CoordinationIntentPacket` | Typed coordination/director intent with roster, source, clock, and merge semantics. | High. |
| `WP9-B3 AgentRole` | Five-part role schema promoted from passive labels to typed contract. | High. |
| `WP9-B4 DecisionBelief` | Typed belief boundary with maintained/diagnostics-only status and observation provenance. | Xhigh. |

## 5. Non-Goals

- Do not implement a full policy engine.
- Do not let intent DTOs bypass command/tasking facade paths.
- Do not treat learned latent state as world truth.
- Do not remove existing Python shims unless compatibility tests are updated.
- Do not merge policy naming with WP2.5 clock merge semantics.

## 6. Acceptance Gates

WP9-B is ready for WP9-E when:

1. Every DTO-5 through DTO-8 has typed fields and defaults.
2. The Python surface exposes the typed fields, or the exact binding blocker is
   recorded.
3. Tests prove intent DTOs are passive contracts rather than direct mutation
   handles.
4. Tests or docs prove `DecisionBelief` stays separate from `World Truth`.
5. Any remaining shared binding/index work is explicitly handed to WP9-E.

## 7. Validation Commands

```bash
git diff --check
pytest tests/runtime/bindings tests/runtime/test_agent_shim.py tests/architecture
rg -n "ActionIntentPacket|CoordinationIntentPacket|AgentRole|DecisionBelief|merge_policy|World Truth" src python tests docs/task/simulation_architecture/wp9_contract_infrastructure_closure
```
