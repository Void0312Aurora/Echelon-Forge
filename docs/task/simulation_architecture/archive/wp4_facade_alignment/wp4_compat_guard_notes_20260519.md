# WP4-I Compatibility Guard Notes

Status: `2026-05-19` guard review accepted as WP4 evidence; WP5 handoff completed.

Inputs:

- [WP4-I compatibility guard cluster](wp4_compat_guard_cluster_20260519.md)
- [WP4 first-wave acceptance review](../review/wp4_first_wave_acceptance_review_20260519.md)
- [WP4-A surface inventory draft](wp4_surface_inventory_wp4a_20260519.md)
- [WP4-D/E policy-binding alignment notes](wp4_policy_binding_alignment_notes_20260519.md)
- `tests/architecture/runtime_facade/test_layering.py`

This note reviews the current guard coverage for compatibility-only paths. It
does not remove compatibility adapters or implement facade/runtime changes.

## 1. Guard Conclusion

The existing architecture guard is useful but not complete.

It already prevents the highest-risk regression in the maintained batch facade
path: raw `WorldBatchRuntime` and `RuntimeFacade::runtime()` access must stay
inside explicit adapter surfaces for `world_batch_vec_env` and
`leader_world_batch_runtime`.

It does not yet prevent all direct `sim.*` policy inputs, because the current
repository still has many legacy Gym, scenario-loader, reward, teacher, oracle,
and test paths that intentionally use direct `sim.*` access as
`compatibility_adapter` or `diagnostics_only` behavior. A broad grep/AST ban
would create false positives and block migration work rather than protecting
the maintained facade path.

## 2. Existing Guard Coverage

| Guard area | Current coverage | Assessment |
|------------|------------------|------------|
| `RuntimeFacade::runtime()` use in `world_batch_vec_env.py` | AST test allows `runtime()` only inside `_RuntimeFacadeAdapter`. | Sufficient for the current batch facade adapter boundary. |
| `ef_py.WorldBatchRuntime` fallback in `world_batch_vec_env.py` | AST test allows construction only inside `_RuntimeFacadeAdapter`. | Sufficient for the current fallback placement. |
| Main `WorldBatchVecEnv` class raw-runtime coupling | String guards prevent `_runtime_facade`, `_batch_runtime`, and `.compat_runtime` from appearing in the main class. | Good regression guard for the maintained batch env path. |
| `leader_world_batch_runtime.py` raw world handles | Tests forbid raw `batch_runtime.world(...)`, `world_vec.batch_runtime.world(...)`, direct batch getter/action/step calls, and `runtime()`. | Good guard for the leader batch runtime path. |
| `RuntimeFacade::runtime()` documentation | Test checks C++ header and facade README explain compatibility-only use. | Sufficient documentation gate for the escape hatch. |
| Runtime contract/facade type header layering | Tests prevent contract/facade type headers from including `core/engine/*`. | Good compile-layering guard. |
| `RuntimeFacade` public header ownership boundary | Test confirms engine owner storage remains hidden behind a forward declaration. | Good C++ facade boundary guard. |

## 3. Known Gaps

| Gap | Why it remains pending | Required later guard |
|-----|------------------------|----------------------|
| Direct `sim.*` policy inputs in legacy Gym/scenario paths. | Existing single-world and scenario-loader paths still use direct `sim.get_agent_observation`, `sim.get_instrument_state`, `sim.set_pilot_action`, visual helpers, reward helpers, and teacher/oracle utilities. These are classified as compatibility or diagnostics paths in WP4-A/D/E. | After WP4-H names maintained shims, add an allowlist-based AST guard that forbids direct `sim.*` calls outside registered compatibility modules. |
| Raw `WorldBatchRuntime` Python binding remains exposed. | The binding is intentionally retained for compatibility, tests, and low-level diagnostics. | Add binding-level documentation or tests that prevent new docs from advertising it as a maintained frontend path. |
| `ObservationPacket` provenance is not runtime-enforced. | Current `ObservationBatchPacket` lacks full `SnapshotVersion`, barrier, and `ObservationViewSpec` metadata. | WP5 information/belief gate should fail maintained policy paths that cannot name observation provenance once runtime metadata exists. |
| `DecisionBelief` and `AgentRole` are not runtime DTOs yet. | WP4-A classifies them; WP4-D/H must still create shims or contract sketches. | Add policy shim tests after `AgentRole` and belief labels exist. |
| `DiagnosticsTrace` is piggyback evidence, not a dedicated diagnostics facade. | First-wave acceptance intentionally kept it diagnostics-only and piggybacked on engagement export. | WP5 trace conformance should decide whether a dedicated diagnostics query is required. |

## 4. Direct `sim.*` Policy Input Review

Current direct `sim.*` use falls into four buckets:

1. Legacy single-world Gym paths such as `gym_envs/universal_env.py` and
   `gym_envs/universal_env_parts/*`.
2. Scenario-loader behavior, navigation, command-chain, reward, shaping, and
   step-evaluation helpers.
3. Teacher, oracle, diagnostics, and test-support utilities.
4. Runtime tests that intentionally exercise low-level simulation behavior.

These paths should not be labeled maintained WP4 frontend paths today. They
remain `compatibility_adapter` unless they consume facade-exported
`ObservationPacket` data with declared provenance; they become
`diagnostics_only` when they rely on privileged oracle/truth material.

## 5. Recommended Low-Risk Guard Plan

Do not add a broad ban yet. Use this staged guard plan instead:

1. Keep the existing architecture tests for `_RuntimeFacadeAdapter`,
   `WorldBatchVecEnv`, and `leader_world_batch_runtime.py`.
2. In WP4-H, introduce explicit Python-side labels or shims for `AgentRole`,
   `ActionIntent`, `CoordinationIntent`, observation provenance, and oracle
   paths.
3. After those labels exist, add an AST guard that scans maintained policy
   packages and allows direct `sim.*` only in a small registered compatibility
   list.
4. In WP5, promote the guard into information/belief leakage tests that
   distinguish maintained `ObservationPacket` or declared `DecisionBelief`
   inputs from `WorldTruth` and diagnostics-only oracle inputs.

## 6. Index Status

Checked indexes:

- `docs/task/simulation_architecture/README.md`
- `docs/task/simulation_architecture/README.zh.md`
- `docs/task/review/README.md`
- `docs/task/review/README.zh.md`

Current status:

- WP4 first-wave and second-wave acceptance reviews are indexed.
- WP4-A surface inventory, WP4-B/C notes, and WP4-D/E notes are indexed.
- WP4-G, WP4-H, and WP4-I second-wave clusters are indexed.
- WP4-F integration handoff and final acceptance review are indexed from the
  simulation architecture and review records.

No duplicate review-index entry is needed for this guard note.

## 7. WP5 Handoff

WP5 can validate immediately:

- maintained batch facade paths do not newly escape to raw runtime handles;
- `RuntimeFacade::runtime()` remains documented as compatibility-only;
- contract/facade type headers do not include engine owners;
- engagement diagnostics can be checked as piggyback evidence;
- first-wave surface classifications can be used as validation labels.

WP5 should wait for later runtime/provenance metadata before enforcing:

- direct `sim.*` bans across all policy paths;
- `ObservationViewSpec` schema compatibility;
- `ObservationPacket` source `SnapshotVersion` and barrier metadata;
- `DecisionBelief` provenance;
- `AgentRole` authority and action-interface metadata;
- dedicated diagnostics-facade requirements.
