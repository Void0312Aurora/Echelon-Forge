# WP4-D + WP4-E Dispatch Sheet: Policy, AgentRole, And Python Mirror

Status: `2026-05-19` dispatch sheet; starts after WP4-A publishes stable surface
names for action, coordination, observation, belief, and agent roles.

Language:

- English canonical: `wp4_policy_binding_cluster_20260519.md`
- Chinese companion: [wp4_policy_binding_cluster_20260519.zh.md](wp4_policy_binding_cluster_20260519.zh.md)

Inputs:

- [WP4 facade alignment](facade_alignment_wp4_20260519.md)
- [WP4-A surface inventory cluster](wp4_surface_inventory_cluster_20260519.md)
- [Temp-02 SCAL architecture vision review](../review/temp-02_review_20260519.md)
- [simulation system architecture design](../../plan/architecture/simulation_system_architecture_design.md)
- Current `python/rl/runtime/*`, `python/rl/control/*`, `gym_envs/*`, and
  `src/interfaces/python/bindings_runtime.cpp`

## 1. Purpose

This sheet groups the WP4 work that touches policy/orchestration adapters and
Python exposure:

- `WP4-D Policy And Coordination Bridge`
- `WP4-E Python Mirror And Cleanup`

The cluster's central rule is: **RL policy is not the agent.** Learned,
scripted, human, LLM, MCTS, or rule-based decision models attach to an
`AgentRole` that declares role, authority, information state, decision model,
and action interface.

## 2. Dispatch Deliverables

| Stream | Required output | Primary write scope | Reasoning budget |
|--------|-----------------|---------------------|------------------|
| `WP4-D1 AgentRole Contract Sketch` | Five-element `AgentRole` schema and mapping to current policy/coordination adapters. | docs and policy adapter notes; code only if surface is stable. | High. |
| `WP4-D2 ActionIntent Adapter Path` | Document or implement explicit facade-compatible action intent path with `effective_time`, `valid_until`, and `merge_policy`. | `python/rl/runtime/*`, `python/rl/control/*`, `gym_envs/*`; avoid facade signature churn. | High. |
| `WP4-D3 CoordinationIntent Adapter Path` | Document or implement explicit coordination path for scripted, learned, and human producers. | `python/rl/runtime/*`, `gym_envs/*`. | Medium-high. |
| `WP4-D4 Observation/Belief Leakage Review` | Identify maintained observation/belief paths and mark truth-derived oracle paths diagnostics-only. | Python adapter docs/tests. | High. |
| `WP4-E1 Binding Surface Mirror` | Ensure Python bindings mirror stable maintained facade DTOs and do not expose new raw-runtime paths. | `src/interfaces/python/bindings_runtime.cpp`, binding tests. | Medium. |
| `WP4-E2 Helper Cleanup Notes` | Document helper-layer paths that remain compatibility-only and their deprecation condition. | Python helper docs/tests. | Medium. |

## 3. Write-Scope Rules

1. Policy/adapter workers own `python/rl/runtime/*`, `python/rl/control/*`, and
   `gym_envs/*`.
2. Binding workers own `src/interfaces/python/bindings_runtime.cpp` and binding
   tests.
3. This cluster MUST NOT add new raw `WorldBatchRuntime` maintained paths.
4. This cluster SHOULD wait for WP4-A names before adding public C++ binding
   surfaces. If names are not stable, write a compatibility note or pending
   test instead.
5. This cluster MUST treat diagnostics-only oracle data as non-maintained
   policy input.
6. If facade DTO changes are required, coordinate with the WP4-B/C owner and
   keep signature changes serial.

## 4. AgentRole Minimum Shape

`AgentRole` MUST include:

| Field | Rule |
|-------|------|
| `role_id` | Stable id for replay, diagnostics, and policy/binding references. |
| `role_type` | Example values: `flight_lead`, `wingman`, `autopilot`, `fire_control`, `coordinator`, `human_operator`, `diagnostic_oracle`. |
| `authority_scope` | Entities, roster, command families, or tasking scope the role may affect. |
| `information_state_source` | `ObservationPacket`, `DecisionBelief`, shared tactical picture, or diagnostics-only oracle. |
| `decision_model_ref` | Scripted doctrine, learned policy checkpoint, human source, search planner, LLM planner, or compatibility helper. |
| `action_interface` | `ActionIntentPacket`, `CoordinationIntentPacket`, tasking/command adapter, or diagnostics-only output. |
| `maintained_status` | `maintained`, `compatibility_adapter`, or `diagnostics_only`. |

## 5. Action And Coordination Rules

Maintained policy/orchestration outputs MUST declare:

1. `source_layer`,
2. `source_id`,
3. `input_snapshot_version` or consumed observation/belief version,
4. `effective_time`,
5. `valid_until`,
6. `merge_policy`,
7. action or coordination family,
8. target entity, roster, or scope,
9. associated `AgentRole`.

Where current adapters cannot carry all fields, WP4-D SHOULD document the gap
and create a compatibility shim or pending WP5 validation gate instead of
silently writing raw runtime state.

## 6. Python Mirror Rules

WP4-E MUST keep Python exposure aligned with the maintained C++ surface:

1. Bindings mirror stable DTO names and field semantics.
2. Binding tests cover field presence for maintained DTOs.
3. Compatibility-only helpers remain labeled and do not become the documented
   maintained path.
4. Diagnostics-only oracle/belief material must not be exposed as maintained
   observation data.
5. If C++ surface names are not stable, WP4-E should wait or document a pending
   mirror gap rather than locking in a premature binding.

## 7. Validation Targets

Recommended focused commands after signatures stabilize:

```powershell
.\tools\maintenance\cmo_env.ps1 python -m pytest -q tests\runtime\bindings tests\architecture\test_runtime_facade_layering.py
```

Adapter-specific tests may be narrower if RL training dependencies are not
available locally.

## 8. Exit Criteria

This cluster exits when:

1. `AgentRole` has a five-element contract sketch connected to current adapters.
2. Action and coordination paths are facade-compatible or explicitly marked as
   compatibility gaps.
3. Maintained adapter paths do not consume `World Truth` as observations.
4. Python bindings mirror stable maintained facade DTOs.
5. Compatibility-only helper paths have deprecation or promotion conditions.
