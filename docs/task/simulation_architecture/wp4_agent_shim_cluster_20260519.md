# WP4-H Dispatch Sheet: Information And Agent Shim

Status: `2026-05-19` second-wave dispatch sheet.

Language:

- English canonical: `wp4_agent_shim_cluster_20260519.md`
- Chinese companion: [wp4_agent_shim_cluster_20260519.zh.md](wp4_agent_shim_cluster_20260519.zh.md)

Inputs:

- [WP4 first-wave acceptance review](../review/wp4_first_wave_acceptance_review_20260519.md)
- [WP4-D/E policy-binding alignment notes](wp4_policy_binding_alignment_notes_20260519.md)
- [WP4-A surface inventory draft](wp4_surface_inventory_wp4a_20260519.md)
- Current `python/rl/runtime/*`, `python/rl/control/*`, and `gym_envs/*`

## 1. Purpose

WP4-H creates the smallest practical Python-side bridge toward `AgentRole`,
`ActionIntentPacket`, and `CoordinationIntentPacket` without promoting new C++
facade DTOs prematurely.

This cluster should produce shims, notes, or narrow tests that make existing
compatibility paths explicit.

## 2. Required Work Items

| Stream | Required output | Write scope | Budget |
|--------|-----------------|-------------|--------|
| `WP4-H1 AgentRole Dataclass Or Note` | Python-side `AgentRole` sketch or documentation mapping single-agent, batch, multi-agent, leader/C2, and scripted director roles. | `python/rl/runtime/*` or docs. | High. |
| `WP4-H2 ActionIntent Compat Wrapper` | Wrapper/note for existing `PilotAction` and `WorldPilotActionAssignment` carrying source id, timing, merge policy, and role metadata where possible. | `python/rl/runtime/*`, `python/rl/control/*`, docs. | High. |
| `WP4-H3 CoordinationIntent Compat Wrapper` | Wrapper/note for task/order/leader/report assignment chains carrying source, roster, update clock, merge policy, and role metadata where possible. | `python/rl/runtime/*`, `gym_envs/*`, docs. | Medium-high. |
| `WP4-H4 Observation Provenance Labels` | Identify variables named `truth` that are actually facade observations, and mark raw/oracle paths diagnostics-only. | docs, optional narrow Python comments/tests. | High. |
| `WP4-H5 Binding Deferral Note` | Confirm that `AgentRole`, `DecisionBelief`, and intent packets should wait for stable WP4-A names before C++ binding. | docs/task/simulation_architecture. | Medium. |

## 3. Non-Goals

- No public C++ binding for `AgentRole`, `DecisionBelief`, `ActionIntentPacket`,
  or `CoordinationIntentPacket` in this cluster.
- No broad refactor of Gymnasium environments.
- No behavior change to policy inference.
- No removal of compatibility adapters.

## 4. Acceptance Gates

This cluster is accepted when:

1. Current policy/coordination paths have explicit role/action/coordination
   metadata mapping or a documented gap.
2. Maintained, compatibility, and diagnostics-only observation paths are
   distinguishable.
3. Python-side shims, if added, are passive wrappers and do not alter runtime
   behavior.
4. Binding expansion remains deferred until surface names and DTO fields are
   stable.
