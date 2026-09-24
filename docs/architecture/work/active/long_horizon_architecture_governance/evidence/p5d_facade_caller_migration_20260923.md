# P5-D Facade Caller Migration Evidence

Status: `2026-09-24` — maintained contract-caller migration slice; not a
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

## Follow-up parity verification

The two residuals above were reproduced and corrected without changing the
production route or leader implementation:

- route geometry now measures the first leg and turn from the scenario's
  actual randomized policy-agent origin rather than an implicit `(0, 0)`;
  all **7** route-generator contracts pass;
- the leader fixture now exposes the loader-level runway-frame query and the
  keyword-compatible post-waypoint transition hook; the approach-arm contract
  passes.

The unit batch was rerun after these repairs. The unavailable historical
`frozen_model` row now reports an explicit `SKIP` because neither its declared
path nor the registered archive alias exists in this checkout; no replacement
model is substituted. The batch still exposes unrelated legacy flight-model
rows (`pitch_hold_speed_scan` and `pitch_hold_throttle_scan`) and is therefore
not claimed as a full-unit green result. Those rows remain outside this
facade-caller migration slice and are not reclassified as P5-D acceptance
evidence.

The manual-takeoff contract's test controller also gained bounded roll-rate
feedback, preserving its original altitude/speed thresholds; the contract now
passes in **519** steps under the randomized takeoff scenario.

## Remaining P5-D work

This slice proves caller construction and contract-path routing only. P5-D
still requires release-manifest/RunReceipt binding, same-release checkpoint
recovery, stop/restart package rollback, support-row telemetry and SLO
evidence, a bounded canary/backout drill, and retirement or explicit
quarantine of the in-kernel rebuild authority. Production cutover remains
closed until those gates pass.
