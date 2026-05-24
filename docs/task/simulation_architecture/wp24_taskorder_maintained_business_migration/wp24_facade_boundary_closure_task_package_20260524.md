# WP24 Facade Boundary Closure Task Package

Status: closed on `2026-05-24`. The initial parallel subagent verification opened
this corrective package; the close-out implemented the observation/tasking
split, command-chain maintained contract wiring, runtime-window provenance
authorization, facade-owned normal batch stepping, raw setup quarantine, and
legacy single-world visual fallback hard-gating.

Chinese companion:
[wp24_facade_boundary_closure_task_package_20260524.zh.md](wp24_facade_boundary_closure_task_package_20260524.zh.md)

## 1. Verification Result

Four read-only subagent checks were dispatched before opening this package. The
result is not an optional backlog. It is a forced close-out set for confirmed
boundary leaks.

| Concern | Verdict | Evidence | Required response |
| --- | --- | --- | --- |
| `ObservationBatchPacket` mixes agent observation with command-side payloads. | Confirmed, P1. | `ObservationBatchPacket` exposes `mission_commands`, `leader_intents`, and `pilot_reports`; the packet has a single `AgentObservation` provenance. | Split observation export from command/tasking export and guard the packet shape. |
| Scenario loading bypasses facade-owned boundaries. | Confirmed with calibration, P1; setup, normal batch stepping, and visual fallback are now guarded. | `batch_apply.py` now defaults to maintained setup-target APIs; `RuntimeFacadeAdapter.step_worlds()` uses facade `step_batch()` for normal full-batch stepping and rejects partial raw stepping without explicit compatibility opt-in. `UniversalEnv` raw `SimulationKernel` remains gated. Legacy visual fallback now fails closed unless runtime compatibility is explicit. | Keep setup/step paths behind maintained facade/adapter contracts; any raw visual fallback remains compatibility-only. |
| Facade/contract is still a dual-representation host. | Partially confirmed at package open; close-out implemented for command-chain business paths. | TaskOrder public whole-shell APIs are retired. `MissionCommand`, `LeaderIntent`, and `PilotReport` now have maintained contract equivalents for runtime/facade/binding/Python business flow; remaining whole-shell APIs are compatibility/diagnostics transport below the maintained path. | Keep maintained business callers on the contract route and guard against whole-shell writer re-entry. |
| `agent_shim.py` defaults to `COMPATIBILITY_ADAPTER`. | Confirmed with calibration, P2. | The default is fail-closed metadata, not direct runtime execution, but maintained callers can still inherit compatibility provenance accidentally. | Maintained business paths must pass maintained provenance explicitly and be guarded. |

## 2. Mandatory Work Lanes

### WP24-I: Observation And Command Export Split

`ObservationBatchPacket` must become a pure observation export envelope.
Command/tasking payloads must move to a separate maintained export envelope or a
dedicated command/tasking read contract.

Required changes:

- Remove command/tasking first-class fields from `ObservationBatchPacket`:
  `mission_commands`, `leader_intents`, `pilot_reports`, and the maintained
  `task_order_contracts` field if it remains a command/tasking read payload.
- Replace the vector overload that exports all fields by default with an
  explicit request path that cannot silently request command-side state.
- Add a maintained command/tasking packet or contract for legitimate command
  read-side use.
- Add architecture guards that fail if command/tasking shell fields return to
  `ObservationBatchPacket`.

Acceptance criteria:

- Agent observation consumers cannot read command-side state through an
  observation packet.
- Command/tasking reads carry their own maintained provenance or explicit
  compatibility quarantine label.
- Python bindings no longer expose command/tasking shell fields on
  `ObservationBatchPacket`.

### WP24-J: Scenario Setup Facade Ownership

Scenario loading must stop accepting raw-runtime-shaped production inputs.

Required changes:

- Replace `batch_apply.py`'s `batch_runtime` parameter shape with a maintained
  facade/adapter setup target.
- Split `world_setup_compat.py` into maintained setup request construction and
  explicitly named compatibility fallback.
- Remove raw runtime fallback from maintained `RuntimeFacadeAdapter` paths once
  facade coverage is complete.
- Migrate `UniversalEnv` away from direct `ef_py.SimulationKernel()` ownership
  onto a single-world facade/adapter path.
- Add architecture guards for `python/scenario/runtime` and
  `gym_envs/universal_env.py` so production scenario paths cannot instantiate or
  consume raw runtimes without an explicit compatibility quarantine.

Acceptance criteria:

- Normal training/runtime paths use facade-owned setup APIs.
- Any remaining `SimulationKernel` or raw `WorldBatchRuntime` use is isolated to
  tests, diagnostics, or named compatibility modules.
- `train.py` cannot reach a raw-runtime production env by default.

### WP24-K: Maintained Contracts For Command-Chain Payloads

`MissionCommand`, `LeaderIntent`, and `PilotReport` cannot remain ambiguous
whole-shell payloads on maintained facade surfaces.

Required changes:

- Create maintained batch contracts for the business slices of
  `MissionCommand`, `LeaderIntent`, and `PilotReport`, or rename and gate their
  existing assignments as compatibility-only.
- Update runtime/facade/bindings to expose maintained contracts for maintained
  business flow and compatibility shells only through explicit quarantine names.
- Ensure command-chain tests prove field preservation through maintained
  contracts, not through whole-shell observation export.
- Add guard coverage matching the TaskOrder deletion standard.

Acceptance criteria:

- No maintained consumer can claim `MissionCommand`, `LeaderIntent`, or
  `PilotReport` shell transport as maintained truth.
- Maintained command-chain flow has typed contract roundtrips for required
  business fields.
- Compatibility shells are named, localized, and fail closed outside the
  quarantine.

### WP24-L: Maintained Provenance Defaults At Call Sites

`agent_shim.py` may keep compatibility defaults for fail-closed behavior, but
maintained business paths must not inherit them implicitly.

Required changes:

- Audit maintained callers of `single_agent_role()` and `roster_slot_role()`.
- Require maintained callers to pass `OBS_FACADE_OBSERVATION_PACKET` or a
  maintained `DecisionBelief` provenance explicitly.
- Add tests proving default compatibility provenance is rejected at maintained
  business entry points.

Acceptance criteria:

- The shim default remains safe compatibility metadata.
- Maintained paths are explicit and cannot accidentally use the compatibility
  default.
- Law 14 read-side guards continue to reject relabeled raw or compatibility
  inputs.

## 3. Closure Ledger

The implementation wave was executed as a forced close-out set, not as optional
backlog.

| Lane | Owner scope | Files to start from | Output |
| --- | --- | --- | --- |
| WP24-I | Facade DTO and Python binding packet split. | `src/runtime/facade/runtime_facade_types.h`, `src/runtime/facade/runtime_facade.cpp`, `src/interfaces/python/bindings_runtime.cpp`, DTO tests. | Pure observation packet plus command/tasking export replacement. |
| WP24-J | Scenario setup facade ownership. | `python/scenario/runtime/batch_apply.py`, `python/scenario/runtime/world_setup_compat.py`, `python/rl/runtime/world_batch/adapter.py`, `gym_envs/universal_env.py`, `train.py`. | Maintained setup target, facade-owned normal batch step, raw setup quarantine, and compatibility-only legacy visual fallback. |
| WP24-K | Command-chain maintained contracts. | `src/runtime/contracts/world_batch_contracts.h`, runtime/facade APIs, command-chain tests. | Implemented maintained MissionCommand/LeaderIntent/PilotReport contracts through runtime/facade/bindings and Python business writers; whole-shell APIs stay compatibility/diagnostics-only. |
| WP24-L | Python provenance call-site hardening. | `python/rl/runtime/agent_shim.py`, runtime Python callers, Law 14 tests. | Explicit maintained provenance at maintained call sites and runtime-window action authorization. |

## 4. Validation Gate

Focused validation for this package must include:

```bash
git diff --check
python -m py_compile python/scenario/runtime/batch_apply.py python/scenario/runtime/world_setup_compat.py python/rl/runtime/world_batch/adapter.py python/rl/runtime/world_batch/command_chain_cache.py python/rl/runtime/world_batch_vec_env.py python/rl/runtime/cooperative_world_batch_vec_env.py python/rl/runtime/multi_agent_runtime.py python/rl/runtime/agent_shim.py gym_envs/universal_env.py train.py
cmake --build build-workshop --target ef_py -j4
PYTHONPATH=build-workshop python -m pytest -q tests/runtime/bindings/test_bindings_runtime_dto_surface.py tests/runtime/test_agent_shim.py
PYTHONPATH=build-workshop python -m pytest -q tests/architecture/test_runtime_facade_layering.py tests/architecture/test_policy_belief_boundaries.py tests/architecture/test_wp12_law14_read_side_enforcement.py tests/architecture/test_wp22_dto_domain_shell_guard.py
PYTHONPATH=build-workshop python -m pytest -q tests/world_batch/test_world_batch_vec_env.py -k "observation or batch_runtime or task_order or command_chain or visual"
PYTHONPATH=build-workshop python -m pytest -q tests/runtime/multi_agent/test_cooperative_world_batch_vec_env.py -k "observation or batch_runtime or task_order or command_chain"
```

The package closes only when the guards prove the raw-runtime and compatibility
shell paths cannot re-enter maintained production flow by default.

## 5. Implementation Notes

### WP24-K

Implemented the command-chain maintained route through runtime contracts,
facade/binding surfaces, and Python business writers:

- added slice-based `MissionCommandMaintainedBatchContract`,
  `LeaderIntentMaintainedBatchContract`, and `PilotReportMaintainedBatchContract`;
- added corresponding `World*MaintainedAssignment` transport structs that carry
  only maintained contracts, not whole-shell payloads;
- kept `WorldMissionCommandAssignment`, `WorldLeaderIntentAssignment`, and
  `WorldPilotReportAssignment` explicitly compatibility-shell transports;
- added `WorldBatchRuntime` and `RuntimeFacade` maintained batch read/write
  methods for the three payload families, projecting to compatibility storage
  internally until the ECS storage split is scheduled;
- exposed Python bindings for the maintained contracts, maintained assignment
  structs, maintained batch methods, and shell-to-contract projectors;
- migrated Python scenario-loader, VecEnv, cooperative VecEnv, and multi-agent
  tasking reads/writes to `World*MaintainedAssignment` and
  `get/set_*_maintained_batch`;
- added architecture and runtime tests that reject old whole-shell writer
  re-entry on Python maintained business paths.

`WorldMissionCommandAssignment`, `WorldLeaderIntentAssignment`, and
`WorldPilotReportAssignment` remain only as lower-level compatibility shell
transports for runtime-window coordination, diagnostics, and low-level tests.
They are not accepted maintained Python business APIs.

### WP24-J / WP24-L

Additional close-out hardening completed after focused review:

- `RuntimeFacadeAdapter.step_worlds()` now uses facade-owned `step_batch()` for
  normal full-batch stepping and fails closed before raw runtime partial stepping
  unless `runtime_compatibility_enabled=True` is explicit;
- `apply_world_setup_request_maintained()` rejects raw-runtime-shaped setup
  targets even if future bindings add similarly named setup methods;
- `run_maintained_window()` requires an explicit maintained
  ObservationPacket/DecisionBelief provenance label before injecting actions and
  calls `authorize_maintained_action_intent()` before executing the runtime
  window;
- single-world and leader runtime callers pass
  `facade_observation_packet` provenance explicitly.

- legacy visual observation fallback now fails closed at the batch refresh
  boundary and adapter visual methods unless `runtime_compatibility_enabled=True`
  is explicit; maintained auto/compiled visual export continues to use the
  facade-owned batch helper.

The default maintained production path accepts no WP24 boundary debt. Residual
raw runtime use is either below maintained contracts as storage
implementation detail or explicitly named compatibility/diagnostics quarantine.
