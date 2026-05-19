# WP5-D Information And Belief Gates Notes

Status: `2026-05-19` focused information/belief gate pass.

Language:

- English canonical: `wp5_information_belief_notes_20260519.md`
- Chinese companion: [wp5_information_belief_notes_20260519.zh.md](wp5_information_belief_notes_20260519.zh.md)

Inputs:

- [WP5-D information/belief dispatch](wp5_information_belief_cluster_20260519.md)
- [WP5 validation harness](validation_harness_wp5_20260519.md)
- [WP5 first-wave acceptance review](../review/wp5_first_wave_acceptance_review_20260519.md)
- [WP5-A harness inventory notes](wp5_harness_inventory_notes_20260519.md)
- [WP4-H agent shim implementation notes](wp4_agent_shim_implementation_notes_20260519.md)
- `python/rl/runtime/agent_shim.py`
- `tests/runtime/test_agent_shim.py`

## 1. Decision

WP5-D keeps information and belief validation label-first. The implemented gate
is `tests/runtime/test_agent_shim.py`; it validates the passive Python shim
vocabulary without changing policy inference, runtime behavior, smoke-suite
membership, or diagnostics/oracle helpers.

No repository-wide direct `sim.*` ban is added in WP5-D. Current Gym,
scenario-loader, reward, teacher, oracle, diagnostics, and test paths still
contain legitimate compatibility or diagnostics access. A future ban must be
allowlist based and must run only after maintained policy adapter labels are
stable.

## 2. Shim Vocabulary Gate

`tests/runtime/test_agent_shim.py` now covers these information/belief labels:

| Gate | Maintained meaning | WP5-D treatment |
|------|--------------------|-----------------|
| `facade_observation_packet` | Observation came from `ObservationBatchPacket`. | May be labeled `maintained` when the role carries facade source metadata such as consumed snapshot and observation packet id. |
| `agent_observation_compat` | Observation came from legacy `get_agent_observation` or batch getter output. | Kept as `compatibility_adapter`; useful during migration but not final maintained policy truth. |
| `raw_world_truth` | Input came from raw runtime or simulation internals. | Must remain `diagnostics_only`; it is not a maintained policy input. |
| `diagnostics_oracle` | Input came from teacher, oracle, debug, or privileged helper logic. | Must remain `diagnostics_only`, even when represented as a provisional `DecisionBelief`-layer label. |
| `AgentRole` five elements | Role, authority scope, information-state source, decision-model reference, and action interface. | Testable today as passive metadata; C++ DTO promotion remains deferred. |
| `ActionIntentCompat` / `CoordinationIntentCompat` | Metadata wrappers for current action and command-chain payloads. | Testable today for source id, snapshot id, timing, role id, payload fields, and maintained/compat labels. |

The tests intentionally do not enforce that an `AgentRole` with diagnostics
source cannot be constructed. The current shim is passive; enforcement belongs
to future maintained adapter code after allowlists and DTO metadata exist.

## 3. Maintained-Path Allowlist Sketch

Future direct `sim.*` restrictions should start from a small maintained-path
allowlist instead of scanning the whole repository.

| Candidate maintained path | Expected information input | Future guard shape |
|---------------------------|----------------------------|--------------------|
| `python/rl/runtime/agent_shim.py` | Passive `ObservationProvenance`, `AgentRole`, action intent, coordination intent metadata. | No direct `sim.*` calls; all truth/oracle labels must be explicit diagnostics-only labels. |
| `python/rl/runtime/world_batch_vec_env.py` main `WorldBatchVecEnv` class | Facade/batch adapter output plus declared compatibility access. | Continue architecture guard that keeps raw runtime handles inside the explicit adapter, not the main class. |
| `python/rl/runtime/leader_world_batch_runtime.py` maintained facade-facing methods | Shared execution request/result outputs, not raw world handles. | Continue architecture guard forbidding direct world handle reach-through and `RuntimeFacade.runtime()` calls. |
| Future policy adapter module that wraps `ActionIntentCompat` | `ObservationProvenance` from facade packet or declared compatibility source. | Forbid direct `sim.*` except in registered compatibility bridge functions. |
| Future belief adapter module that wraps `DecisionBelief` | Consumed observation packet ids or snapshot versions plus model/inference source. | Require label, source versions, and diagnostics-only marker for oracle/truth-derived beliefs. |

This allowlist is a sketch, not an implementation. WP5-E should not promote a
broad AST ban until WP5-D/WP5-E agree which policy packages are maintained and
which modules are registered compatibility adapters.

## 4. Compatibility And Diagnostics Exception List

The following modules or module families should remain exceptions until their
callers carry maintained labels:

| Exception area | Current reason | Required before enforcement |
|----------------|----------------|-----------------------------|
| `gym_envs/universal_env.py` and `gym_envs/universal_env_parts/*` | Legacy single-world Gym path uses direct `sim.get_agent_observation`, `sim.get_instrument_state`, `sim.set_pilot_action`, `sim.step`, and visual helpers. | A facade-shaped observation/action adapter with provenance and action intent metadata. |
| `gym_envs/scenario_loader/*` runtime helpers | Scenario loading, step evaluation, navigation, reward, and behavior helpers read direct simulation state or write mission/task commands. | Labels separating maintained adapter state from compatibility/direct simulation state. |
| `gym_envs/leader_env_parts/*` | Leader environment bridges, decision runtime, and execution runtime still read `env.unwrapped.sim` or `loader.sim` in compatibility flows. | AgentRole and observation provenance labels at the leader policy boundary. |
| `python/rl/runtime/world_batch/adapter.py` | Centralized compatibility adapter intentionally owns `RuntimeFacade.runtime()` / `WorldBatchRuntime` fallback. | Keep as registered compatibility adapter; do not expose as maintained policy API. |
| Domain, oracle, teacher, reward, diagnostics, and test helpers | They may need privileged world truth to audit behavior or build fixtures. | Must be labeled `diagnostics_only` when consumed by policy/belief-facing checks. |

## 5. Truth/Oracle Leakage Boundary

WP5-D distinguishes three information-state classes:

| Class | Allowed in maintained policy input? | Current testable evidence |
|-------|-------------------------------------|---------------------------|
| `ObservationPacket` / `facade_observation_packet` | Yes, if the adapter carries declared source metadata. | `ObservationProvenance` can store `consumed_snapshot_version`, `observation_packet_id`, source layer, and maintained status. |
| `agent_observation_compat` | Not final maintained truth; allowed only as migration compatibility. | Tests preserve `compatibility_adapter` status and keep it visibly separate from maintained source labels. |
| `raw_world_truth` / `diagnostics_oracle` | No. These are diagnostics-only or oracle-derived. | Tests assert diagnostics-only status, explicit source layer, and diagnostics notes for truth/oracle labels. |

The word `DecisionBelief` in the current shim is only a label for the belief
layer; it is not a typed public DTO yet. A truth-derived or oracle-derived
belief must remain `diagnostics_only` until a future maintained belief contract
can name consumed observation versions and inference provenance.

## 6. DecisionBelief Boundary Before Typed DTOs

What can be tested today:

1. A belief-like input can be labeled with `information_state_layer =
   "DecisionBelief"`.
2. Oracle or teacher-derived belief labels remain `diagnostics_only`.
3. Maintained roles can name a facade observation source, consumed snapshot,
   observation packet id, decision-model kind, and decision-model id.
4. Action and coordination intent wrappers can carry source id, input snapshot,
   effective time, validity, role id, and maintained/compat status.

What remains metadata-dependent:

1. Typed `DecisionBelief` DTO shape and C++/Python binding promotion.
2. Runtime-enforced consumed observation packet versions.
3. Uncertainty/confidence, estimator source, memory source, doctrine source, and
   learned-state provenance fields.
4. Rejection of diagnostics-only belief inputs by maintained policy execution
   paths.
5. Cross-checking `DecisionBelief` provenance against `ObservationBatchPacket`
   snapshot/barrier/source-time metadata.

## 7. Smoke Candidate Advice

Recommended WP5-D focused command:

```bash
python -m pytest -q tests/runtime/test_agent_shim.py
```

Recommended WP5-E smoke candidate:

```bash
python -m pytest -q tests/runtime/test_agent_shim.py
```

This file is low-cost and gives the maintained validation harness one explicit
information/belief leakage tier gate. WP5-E may pair it with the WP5-B
architecture gates and WP5-C trace/replay gates, but should not add any broad
direct `sim.*` ban to smoke yet.

## 8. Deferred Gates

Do not solve these in WP5-D:

- policy inference rewrites or Gym adapter migration;
- removal of diagnostics, oracle, teacher, or reward helpers;
- runtime `ObservationViewSpec` or packet-level snapshot/barrier metadata;
- typed `DecisionBelief`, `RewardReport`, or termination reason-source DTOs;
- direct edits to `tests/smoke/ci_smoke_suite.json`;
- global direct `sim.*` bans outside a maintained-path allowlist.
