# P5-D Facade Caller Migration Evidence

Status: `2026-09-23` — maintained contract-caller migration slice; not a
production cutover or P5-D acceptance.

This packet records the first P5-D caller migration slice after the local
RolloutDecision admission gate. The migrated callers now construct the
facade-owned batch adapter and scenario-loader runtime instead of constructing
the raw `SimulationKernel` or reaching raw world methods directly. The change
does not authorize production routing, package publication, or removal of the
compatibility surface.

## Migrated surfaces

- `python/testing/contracts/loader_command_chain.py`
- `python/testing/contracts/route_generator.py`
- `python/testing/contracts/unit/comm.py`
- `python/testing/contracts/unit/kernel.py`
- `python/tasking_contracts/bridge_views.py`
- `python/rl/runtime/world_batch/adapter.py`

The native facade now exposes the bounded command-link configuration DTO and
the batch communication-packet query used by the migrated contracts. The DTO
is generated through the repository schema registry. CPU execution applies
both surfaces; the CUDA resident backend rejects them explicitly as unsupported
instead of silently accepting a partial capability.

## Verification

Executed in the isolated `codex/long-horizon-governance-architecture`
worktree with the rebuilt `build-long-horizon-p5c-shared` Debug binding:

```powershell
cmake --build build-long-horizon-p5c-shared --config Debug --target ef_facade_backend ef_py --parallel 4
$env:CMO_BUILD_DIR='build-long-horizon-p5c-shared'
powershell -NoProfile -ExecutionPolicy Bypass -File tools/maintenance/cmo_env.ps1 python -m ruff check python/rl/runtime/world_batch/adapter.py python/tasking_contracts/bridge_views.py python/testing/contracts/loader_command_chain.py python/testing/contracts/route_generator.py python/testing/contracts/unit/comm.py python/testing/contracts/unit/kernel.py
```

Build and Ruff completed successfully. The rebuilt binding reports
`WorldCommandLinkAssignment`, `RuntimeFacade.set_command_links_batch`, and
`RuntimeFacade.get_unit_messages_batch`.

Focused architecture gates passed:

- runtime-facade escape/tasking boundary group: **39 passed**;
- tasking/runtime-contract boundary group: **30 passed**;
- runtime-spine facade-caller group: **14 passed**;
- DTO-schema freshness: **5 passed**;
- runtime-bootstrap ownership: **5 passed**;
- command/tasking bridge guardrails: included in the 30-pass group.

Focused maintained contracts passed:

- loader command chain: **1 passed**;
- same-process comm set: **4 passed**;
- migrated naval/common-core and screen contracts: **10 passed**;
- route-generator contracts: **2 passed**.

The full unit batch remains non-green on existing rows outside this migration
slice: `leader_phase_manager_approach_arm` reports an expected transition count
of `1` but observes `0`; the route distribution row reports seed `5` first leg
`17084.4 m` outside `[18000.0, 24000.0]`. These residual contracts remain
explicitly open and are not reclassified as P5-D acceptance evidence.

## Remaining P5-D work

This slice proves caller construction and contract-path routing only. P5-D
still requires release-manifest/RunReceipt binding, same-release checkpoint
recovery, stop/restart package rollback, support-row telemetry and SLO
evidence, a bounded canary/backout drill, and retirement or explicit
quarantine of the in-kernel rebuild authority. Production cutover remains
closed until those gates pass.
