# Exact GPU World-Step Re-Architecture Plan

Status: experimental archive retained for research provenance  
Date: 2026-03-25  
Owner: Codex / migration line

Maintained-mainline note (2026-04-16):
CPU exact world stepping plus selected GPU helper paths is the maintained
execution baseline. This document remains archived as design history for the
exact-step GPU line.

## Why this exists

The current helper-first GPU migration line has produced only modest end-to-end
benefit:

- maintained `p5` training improved by about `1.15x`, not by an order of
  magnitude
- several later hot-path optimizations landed in the noise floor or regressed
  throughput
- the Phase 2 reduced exact-step prototype is still far from exact CPU parity on
  hidden dynamics, even when CPU/GPU shadow parity is perfect

That means the current approach is no longer the highest-value path. The next
migration step must stop approximating the exact CPU step from the outside and
instead rebuild the exact simulation pipeline around explicit system contracts.

This is not a retreat to CPU execution as the end state. CPU is the truth
source; GPU remains the target backend.

## Freeze decisions

- Freeze helper-level micro-optimizations unless they unblock exact-step
  migration.
- Freeze the current reduced exact-step prototype as an experiment branch, not
  as the migration foundation.
- Keep the existing parity artifacts:
  - packed exact-state contract
  - CPU parity trace generator
  - CPU/GPU shadow comparator
- Rebase the migration around exact CPU system inventory and per-system trace.

## Migration objective

Build an exact GPU backend that executes the same ordered system semantics as
the current CPU simulation core, then attach that backend to
`WorldBatchRuntime` and the maintained `p5` training path.

## Re-architecture phases

### Phase A: System Inventory And Stage Trace

Goal:
- make the exact CPU step explicit as an ordered list of named systems
- record stage-by-stage exact-state snapshots after each traceable system

Deliverables:
- frozen system inventory with migration scope flags
- manual per-stage CPU trace harness
- diagnostics artifact that captures:
  - initial packed exact state
  - per-stage truth / instrument / hidden-dynamics snapshots
  - final stage record for one exact CPU frame

Exit criteria:
- traceable pipeline replay matches the corresponding full CPU step on exact
  packed state surfaces

### Phase B: Shared Exact System Contracts

Goal:
- move from monolithic "step parity" to system-local contracts

Deliverables:
- per-system input/output surface inventory
- per-system exact-state dependency notes
- trace comparator that can diff by stage, not only by full step

Exit criteria:
- each traceable system has a declared contract and a stable per-stage diff
  surface

### Phase C: CPU Data-Oriented Exact Backend

Goal:
- reproduce the current exact CPU semantics in a data-oriented executor before
  touching CUDA again

Deliverables:
- SoA or chunked CPU exact backend that runs the same ordered stage contracts
- per-stage parity checks against the live Flecs world

Exit criteria:
- CPU data-oriented backend matches live exact CPU stage-by-stage

### Phase D: CUDA Exact Backend

Goal:
- port the same stage contracts to CUDA without changing semantics

Deliverables:
- CUDA implementation for each exact-stage contract
- CPU vs GPU stage comparator

Exit criteria:
- CPU data-oriented backend and CUDA backend match on packed exact-state and
  stage-local surfaces

### Phase E: Mainline Integration

Goal:
- attach the exact GPU backend to `WorldBatchRuntime`, then to maintained `p5`

Deliverables:
- optional exact GPU step backend in `WorldBatchRuntime`
- training/runtime config switch
- A/B benchmark and parity gates

Exit criteria:
- maintained `p5` can run with the exact GPU backend
- end-to-end speedup is materially above the noise floor

## Immediate implementation order

1. Land exact CPU system inventory and per-stage trace hooks.
2. Validate that the traceable manual pipeline matches one full exact CPU step.
3. Split the current parity tooling so stage diffs can be compared independently.
4. Only then restart backend work.

Current progress on 2026-03-25:

- [x] Exact CPU system inventory landed in `SimulationKernel`.
- [x] Manual per-stage CPU trace harness landed and replays one traceable frame.
- [x] System-stage trace generator landed with per-stage packed exact-state
  snapshots.
- [x] System-stage comparator landed and now reports stage-local surface drift
  plus packed exact-component digest drift.
- [x] First-scope per-system contracts landed with structured read/write,
  trace-surface, and dependency metadata.
- [x] `ExactWorldStepStateV1` now covers the missing command-lane exact inputs
  (`ActionCommand`, `CommandLink`, and `Pending*Command`) needed for the first
  executor slice.
- [x] `ExactWorldStepStateV1` now also covers `Health` plus the terrain-surface
  metadata needed by `GroundContact`.
- [x] First data-oriented exact CPU executor slice landed for
  `CommandLinkMovement -> CommandLinkAction -> CommandLinkMission -> ActionMapping -> CommandLag`.
- [x] Second data-oriented exact CPU executor slice landed for
  `FlightControl -> ClearForces -> ComputeAeroState`, chained after the
  command-lane slice and validated against the archived `ComputeAeroState`
  stage.
- [x] Third data-oriented exact CPU executor slice landed for
  `ComputeForces -> ComputeAerodynamics -> GroundContact`, chained after the
  first two slices and validated against the archived `GroundContact` stage.
- [x] Fourth data-oriented exact CPU executor slice landed for
  `RotationalIntegrate -> LeapfrogIntegrate -> NavigationSystem -> UpdateInstruments -> FuelConsumption -> MassUpdate`,
  chained after the first three slices and validated against the archived
  `MassUpdate` stage.
- [x] Missile-state exact surfaces and contact-list summaries are now packed into
  `ExactWorldStepStateV1`, and `MissileGuidance` has its own exact CPU trace,
  replay comparator, and reference slice with parity against the archived
  guidance stage.
- [x] Guidance diagnostics now expose combat surfaces (`Missile` and
  `ContactList`) alongside the existing hidden/command surfaces so guidance
  drift is debuggable without falling back to component hashes.
- [x] A canonical first-scope CPU chain replay now exists across the stitched
  command-lane, control/aero, force/ground, missile-guidance, and aircraft-tail
  slices, and it replays `CommandLinkMovement -> MassUpdate` on mixed
  aircraft+missile worlds with exact parity against the archived final stage.
- [x] Phase D entry landed for the stable front half:
  `CommandLinkMovement -> GroundContact` now has a dedicated CUDA backend that
  keeps `CommandLane` on the exact CPU slice, runs `FlightControl ->
  GroundContact` on GPU, and now replays against the archived `GroundContact`
  record with exact packed-state parity.
- [x] Phase D second split landed for the aircraft tail:
  `RotationalIntegrate -> MassUpdate` now has a dedicated CUDA backend that
  replays against the archived `MassUpdate` record with exact packed-state
  parity.
- [x] Both first-scope CUDA slice splits now hit exact parity:
  - front-half warm run: `~215.6 ms` host-to-device, `~8.6 ms` kernel
  - aircraft-tail warm run: `~214.0 ms` host-to-device, `~10.6 ms` kernel
- [x] A resident aircraft-only CUDA chain now exists for
  `CommandLinkMovement -> MassUpdate` with `CommandLane` still on CPU and
  `FlightControl -> MassUpdate` on a single CUDA upload/kernel/download path.
  It replays against the archived `MassUpdate` record with exact packed-state
  parity on aircraft-only system traces.
- [x] The resident aircraft chain cuts the split-path GPU total, but it is
  still upload-bound:
  - stitched aircraft chain warm run: `~353.5 ms` host-to-device, `~11.8 ms` kernel
  - split warm run baseline: `~429.6 ms` host-to-device, `~19.3 ms` kernel
- [x] `MissileGuidance` now has its own exact CUDA slice backend and replays
  against the archived guidance stage with exact packed-state parity.
- [x] Mixed first-scope diagnostics now have a controlled GPU-guidance variant:
  the stitched chain can keep the existing CPU order while swapping the
  `MissileGuidance` slice to CUDA and still match the archived final
  `MassUpdate` record exactly.
- [x] A resident mixed first-scope CUDA chain now exists for the canonical
  `{missile,target}` replay pair, keeping `CommandLane` on CPU and running
  `FlightControl -> GroundContact`, `MissileGuidance`, and
  `RotationalIntegrate -> MassUpdate` on a single CUDA upload / three-kernel /
  single-download path. It replays against the archived final `MassUpdate`
  record with exact packed-state parity.
- [x] The resident mixed chain removes the extra guidance round-trip, but it is
  still upload-bound:
  - mixed first-scope GPU compare: `~326.1 ms` host-to-device, `~14.7 ms`
    combined kernels, `~0.03 ms` device-to-host, `~340.9 ms` total
  - mixed first-scope warm rerun: `~332.4 ms` host-to-device, `~15.1 ms`
    combined kernels, `~0.03 ms` device-to-host, `~347.6 ms` total
- [x] The resident first-scope exact GPU backend is now attached to
  `WorldBatchRuntime` behind an experimental batch API, so mixed first-scope
  replay can go through the runtime instead of only through static packed-state
  helpers.
- [x] Runtime-integrated mixed first-scope compare still shows the same
  bottleneck, but with a lower end-to-end wall than the earlier standalone
  packed helper path:
  - runtime GPU compare: `~191.7 ms` host-to-device, `~16.1 ms` combined
    kernels, `~0.03 ms` device-to-host, `~207.9 ms` total
- [x] A true device-resident first-scope carrier now exists at the packed
  exact-state layer, with explicit `upload -> replay -> download` APIs plus
  device-pointer/state-count introspection. It preserves exact parity against
  the archived mixed first-scope `MassUpdate` record.
- [x] The same resident carrier is now lifted to `WorldBatchRuntime` behind
  explicit runtime-level `upload -> replay -> download/apply` APIs, so the
  runtime extract/apply wall can be measured separately from device replay
  without promoting the path into `step_batch()`.
- [x] `WorldBatchRuntime` now also supports a cached exact-state session: it
  extracts first-scope exact state once, keeps that state outside Flecs across
  successive steps, and reuses the exact GPU chain without re-extracting from
  the live world each frame.
- [x] A dedicated multi-step cached-session benchmark now exists for the
  rollout-like hot path. It runs a deterministic single-aircraft action
  schedule through `WorldBatchRuntime` cached exact-state sessions, varies
  write-back cadence, and separately reports prime, first-step, warm-step, and
  final live-world flush behavior while comparing the test path against a CPU
  cached-session reference.
- [x] The new resident carrier demonstrates that the remaining wall in the
  runtime-integrated experiment is not the CUDA kernels themselves:
  - runtime-integrated one-shot compare: `~0.02 ms` host-to-device,
    `~15.4 ms` combined kernels, `~0.01 ms` device-to-host, but `~386.3 ms`
    end-to-end total because the runtime path still pays extract/apply/Python
    glue outside the CUDA stats surface
  - runtime-resident compare: `~0.02 ms` host-to-device, `~16.9 ms` combined
    kernels, `~0.01 ms` device-to-host, but `~238.0 ms` total wall because the
    runtime upload phase still spends `~221.0 ms` on extract/upload work before
    device replay begins
  - packed resident compare: `~0.03 ms` host-to-device, `~24.0 ms` cold
    kernels, `~0.01 ms` device-to-host, `~24.0 ms` total
  - runtime-resident warm replay after one upload: `~0.03 ms` amortized
    upload, `~0.14 ms` combined kernels, `~0.01 ms` device-to-host, `~0.17 ms`
    total for the second replay/download pair
  - runtime cached-session `prime + first step`: `~325.2 ms` total wall; the
    first cached GPU step after priming is still cold at `~233.9 ms`, but the
    second cached step drops to `~0.17 ms` wall with `~0.12 ms` combined
    kernels and `~0.01 ms` device-to-host, confirming that steady-state no
    longer pays the Flecs extract wall
  - packed resident warm replay after one upload: `~0.02 ms` amortized upload,
    `~0.13 ms` combined kernels, `~0.01 ms` device-to-host, `~0.16 ms` total
- [x] The cached-session multi-step benchmark confirms the steady-state/runtime
  split and now has a clean repeated-step parity gate:
  - aircraft-only cached-session prime is negligible (`~0.03 ms`) once the
    runtime is already live, and the first GPU step dominates the cold cost
    (`~15.6-24.0 ms` depending on cadence)
  - after warmup, GPU cached-session steps settle around `~0.17 ms`, with
    warm no-write-back steps around `~0.14 ms`, warm `every-4` write-back steps
    around `~0.24 ms`, and warm `every-step` write-back around `~0.17 ms`
  - final live-world write-back remains semantically correct
    (`final_live_component_digests_match=true`), so cadence itself is no longer
    the blocker
  - after canonicalizing the repeated-step `ComputeAeroState` and
    `ComputeForces` scalar outputs across live CPU, CPU reference slices, and
    CUDA backends, the GPU cached-session now matches the CPU cached-session
    for all `8` deterministic benchmark steps (`first_divergence_step=0`)
- [x] A fixed-seed multi-step exact CPU trace now exists for the cached-session
  benchmark fixture, together with a comparator that replays CPU or GPU cached
  sessions against the archived per-step `MassUpdate` record and localizes the
  first repeated-step divergence with slice-level packed-state checks.
- [x] The repeated-step comparator and stage-stop drill-down were used to close
  the cached-session blocker:
  - the original first repeated-step divergence was localized to
    `FrontHalf -> ComputeAeroState`
  - after canonicalizing repeated-step `aero_state` scalars, the first
    remaining divergence moved to `FrontHalf -> ComputeForces`
  - after canonicalizing repeated-step thrust and thrust-projected force
    scalars, the GPU cached-session replay now stays exact for all `8`
    benchmark steps
  - `MissileGuidance` and `AircraftTail` were therefore confirmed not to be the
    first repeated-step blockers on this fixture
- [x] The cached-session path now exposes runtime-owned timing breakdown in
  addition to the CUDA helper stats:
  - `prime_extract_ms`
  - per-step `pilot_update_ms`
  - per-step `step_total_ms`
  - per-step `write_back_ms`
  - embedded chain timings for `command_lane`, upload, kernels, download, and
    total helper time
- [x] Fresh runtime-integration benchmark after the repeated-step parity fixes
  now shows the remaining wall much more clearly:
  - aircraft-only cached-session prime extract is only `~0.018 ms`
  - the cold first GPU step is still dominated by first-use kernel cost at
    `~14.94 ms` total runtime step time
  - warm no-write-back GPU cached-session steps are now `~0.151 ms` total at
    runtime level, with `~0.1508 ms` inside the exact GPU chain and only
    `~0.00031 ms` of residual runtime overhead
  - the final write-back step stays semantically correct but adds about
    `~0.170 ms` on top of the warm chain replay
  - on this fixture, the remaining steady-state wall is therefore no longer
    Flecs extraction or Python glue; it is almost entirely the exact GPU chain
    itself, while extract/apply cost is now isolated to prime/flush cadence
- [ ] Next: use this cleaned-up cached-session path as the promotion gate for a
  broader runtime/backend experiment, then quantify the same breakdown on
  larger first-scope batches where upload, command-lane, and write-back costs
  become meaningful again.
- [x] The broader aircraft-only cached-session runtime/backend gate now exists
  as a configurable multi-world batch benchmark:
  - `benchmark_exact_world_step_first_scope_chain_cached_session.py` now
    accepts `world_count` and runs the same cached-session loop across
    `N` deterministic worlds / cached states
  - `benchmark_exact_world_step_first_scope_chain_cached_session_matrix.py`
    now sweeps a batch-size matrix and aggregates the same runtime-owned
    breakdown (`prime_extract`, upload, command-lane, chain total, write-back,
    and per-state warm cost)
  - fresh GPU matrix on `world_count=1,4,16` now shows the broader-batch gate
    has advanced:
    - `world_count=1`: `first_cpu_divergence_step=0`,
      `final_cached_component_digests_match=true`,
      warm runtime step `~0.220 ms`, warm chain `~0.158 ms`
    - `world_count=4`: `first_cpu_divergence_step=0`,
      `final_cached_component_digests_match=true`,
      warm runtime step `~0.518 ms`, warm chain `~0.172 ms`,
      averaged warm write-back `~0.346 ms`
    - `world_count=16`: `first_cpu_divergence_step=0`,
      `final_cached_component_digests_match=true`,
      warm runtime step `~1.916 ms`, warm chain `~0.224 ms`,
      averaged warm write-back `~1.691 ms`
  - on this aircraft-only sweep, upload amortization improves with batch size
    and `command_lane_ms` stays negligible, while write-back grows into the
    dominant runtime-side cost once the chain itself is warm
  - the former `world_count=4` and `world_count=16` blockers are now closed
    end-to-end on the deterministic 8-step cached-session sweep
- [x] The remaining `world_count=16` cached-session divergence has now been
  localized and closed with the per-world / per-stage comparator before any
  promotion toward `step_batch()`:
  - `AircraftTail` host-side unpack/postprocess now normalizes
    `environment_sample` and `instrument_state.g_load_*` with the same semantic
    basis used by the CPU exact path, including the pre-`MassUpdate` mass basis
    that `UpdateInstruments` expects
  - the first-scope chain unpack path now applies the same postprocess even
    when the direct helper bypasses the runtime batch wrapper, so both direct
    cached-session replay and runtime-owned cached sessions share the same
    normalization
  - the residual broader-batch final-output drift in
    `FrontHalf -> ComputeAerodynamics` was then closed by aligning the final
    `force_accumulator` and `ground_state` outputs against a CPU front-half
    reference built from the same post-command basis states
  - as of `2026-03-26`, the `world_count=16` deterministic cached-session
    comparator now reaches `first_divergence_step=0` with matching apply
    signatures and packed component digests across all 8 steps
- [x] The broader-batch cached-session comparator now has formal per-world /
  per-stage localization instead of ad hoc digest inspection:
  - `generate_exact_world_step_cached_session_multistep_trace.py` now accepts
    `world_count` and records multi-world per-step stage traces for the same
    deterministic aircraft fixture
  - `compare_exact_world_step_cached_session_multistep.py` now replays cached
    sessions against those traces with per-state packed-digest localization at
    both the slice level and the internal `FrontHalf` / no-missile
    `AircraftTail` stage levels
  - the original `world_count=4` blocker was traced through
    `AircraftTail -> UpdateInstruments`, then through
    `FrontHalf -> ComputeForces`, and is now closed
  - fresh post-fix `world_count=4` replay now reaches
    `first_divergence_step=0` with both apply signatures and packed component
    digests matching across all 8 cached-session steps
  - the earlier `MissileGuidance` attribution was a diagnostic false lead caused
    by comparing `GroundContact`-derived packed state directly against the live
    `MissileGuidance` stage without accounting for the intervening
    `RotationalIntegrate` stage
  - the former `world_count=16` blocker was narrowed from the final
    `FrontHalf -> GroundContact` mismatch into
    `FrontHalf -> ComputeAeroState`, then through the cached-session write-back
    semantics, and is now closed
- [x] Phase E runtime-switch entry has now landed in experimental form:
  `WorldBatchRuntime` exposes an explicit `WorldBatchExactStepBackend`
  selection, and `step_batch()` can now opt into the cached first-scope exact
  backend after an explicit prime step.
  - `CpuSimulationKernel` remains the default and trivial fallback.
  - `ExactFirstScopeChainCachedCpu` and `ExactFirstScopeChainCachedGpu` reuse
    the runtime-owned cached exact-state session instead of re-extracting from
    Flecs every frame.
  - `set_pilot_actions_batch(...)` and `set_mission_commands_batch(...)` now
    mirror matching assignments into that cached exact-state session while the
    experimental backend is active.
  - worlds not covered by the primed cached refs still fall back to the
    existing CPU `SimulationKernel::step()` path.
  - the cached-session benchmark/comparator tooling now also has a matching
    `--runtime-step-batch-backend` mode, so the same deterministic multistep
    fixtures can be driven through the experimental runtime switch instead of
    only through the direct cached-session helper APIs.
  - as of `2026-03-26`, the explicit runtime-switch path also reaches
    `first_divergence_step=0` on the deterministic `world_count=16` 8-step
    fixture when replayed with `--runtime-step-batch-backend`.
  - this is still intentionally experimental and is not yet the maintained
    training default or the hidden `p5` exact-step path.
- [x] The closed `world_count=16` gate now has durable regression coverage,
  explicit experiment-boundary documentation, and runtime-side promotion
  quantification:
  - cached-session multistep regression coverage now locks the closed
    `world_count=16` GPU gate for both the direct helper path and the explicit
    `--runtime-step-batch-backend` path
  - the first-scope cached-session benchmark tests now also lock the explicit
    16-world GPU `step_batch()` backend sweep, so the runtime switch and the
    direct helper no longer rely on ad hoc replay commands for protection
  - the diagnostics README now states directly that
    `--runtime-step-batch-backend` remains an explicit experiment boundary and
    is not the maintained default exact-step path
  - `benchmark_exact_world_step_first_scope_chain_cached_session.py` and the
    matching batch-size matrix now expose warm write-back share / chain share /
    write-back-vs-chain ratios, CPU-vs-test speedup ratios, explicit
    `promotion_blockers`, and a final `promotion_ready` verdict, and the
    matrix can sweep the same fixture through the explicit runtime backend
    switch
  - the current conservative promotion gate for that experimental runtime line
    is now explicit: parity must stay closed, total-wall and warm runtime-step
    speedup must both be at least CPU parity (`>= 1.0x`), warm write-back
    share must stay at or below `25%`, and warm write-back-vs-chain ratio must
    stay at or below `0.5`
  - the runtime-switch backend now advances cached session state lazily inside
    `WorldBatchRuntime.step_batch()`: covered cached worlds are marked dirty,
    and live ECS write-back happens only when a live-world accessor or extract
    path explicitly touches those worlds
  - fresh GPU runtime-switch matrix on `world_count=1,4,16`
    (`steps=8`, `write_back_every=1`) stays at
    `first_cpu_divergence_step=0` across all rows; after the lazy-sync pass,
    warm write-back cost is now `0.0 ms` across those rows, so warm
    write-back share and write-back-vs-chain ratio both collapse to `0.0`
  - as of `2026-03-27`, that experimental runtime-switch line also has a
    conservative resident fast path for command-lane-stable cached sessions:
    `WorldBatchRuntime.step_batch()` can now keep the first-scope GPU state
    resident across steps, apply a small host-side command-lane projection,
    replay the CUDA chain in place, and defer host materialization until an
    explicit extract / live-world access / write-back asks for it
  - regression coverage now locks that runtime-step backend behavior:
    `chain_device_to_host_ms == 0.0` inside the cached-session `step_batch()`
    step body for the covered GPU fixture, while later extract / live-world
    access still matches the cached-session and live ECS packed state
  - fresh post-resident runtime-switch matrix on `world_count=1,4,16`
    (`steps=8`, `write_back_every=1`) still holds
    `first_cpu_divergence_step=0`, keeps warm write-back cost at `0.0 ms`,
    and improves the warm runtime-step line notably for larger rows
    (`test_vs_cpu_warm_runtime_step_speedup ~= 0.137x` at `world_count=4`,
    `~= 0.324x` at `world_count=16`), but `world_count=1` remains
    cold/overhead dominated (`~= 0.073x`)
  - the newest `2026-03-27` follow-on narrows that resident path further for
    the benchmark-style quiescent command lane: if the cached session would
    only advance `world_time_s`, `WorldBatchRuntime.step_batch()` now skips the
    CPU command-lane batch entirely, advances `world_time_s` in the host shadow
    directly, and reuses the resident projection/replay flow
  - the latest pass narrows that quiescent replay again by replacing the old
    full resident projection upload with a smaller `pilot + world_time`
    projection, so the runtime-step path no longer needs to clone the full
    cached exact-state batch before each replay just to express those covered
    updates
  - regression coverage now locks that narrower behavior too:
    benchmark-style runtime-step backend sweeps report
    `chain_command_lane_ms == 0.0` while keeping
    `first_cpu_divergence_step=0` and matching packed component digests
  - fresh post-quiescent matrix on `world_count=1,4,16`
    (`steps=8`, `write_back_every=1`) still keeps warm write-back cost at
    `0.0 ms`, now drives `test_warm_chain_command_lane_ms` to `0.0` across the
    covered runtime-step rows, and now measures approximate warm runtime-step
    speedups of `0.142x` at `world_count=1`, `0.175x` at `world_count=4`, and
    `0.397x` at `world_count=16`
  - the newest `2026-03-27` follow-on now also caches the uploaded missile-row
    count inside the resident first-scope CUDA carrier and skips the guidance
    counter memset, `MissileGuidance` kernel launch, and missile-counter D2H
    copy entirely when the uploaded batch has no missile rows
  - regression coverage now locks that no-missile resident behavior too:
    the explicit runtime-step backend benchmark fixture records
    `last_cuda_step_stats["missile_count"] == 0` on the covered aircraft-only
    rows while keeping `first_cpu_divergence_step=0`
  - fresh post-no-missile matrix on `world_count=1,4,16`
    (`steps=8`, `write_back_every=1`) keeps warm write-back cost and
    `test_warm_chain_command_lane_ms` at `0.0`, lowers warm runtime-step time
    to about `0.100 ms`, `0.112 ms`, and `0.109 ms`, and now measures
    approximate warm runtime-step speedups of `0.132x` at `world_count=1`,
    `0.173x` at `world_count=4`, and `0.502x` at `world_count=16`
  - the newest `2026-03-27` follow-on then fuses the quiescent
    `pilot + world_time` resident sync itself with the no-missile aircraft-only
    replay, so the covered runtime-step hot path now does one projection H2D
    copy and one CUDA launch/sync instead of a separate projection-apply launch
    followed by a second replay launch
  - fresh post-sync+replay-fusion matrix on `world_count=1,4,16`
    (`steps=8`, `write_back_every=1`) keeps warm write-back cost and
    `test_warm_chain_command_lane_ms` at `0.0`, lowers
    `test_warm_chain_host_to_device_ms` to about `0.0082 ms`, `0.0084 ms`, and
    `0.0093 ms`, lowers warm runtime-step time to about `0.093 ms`,
    `0.094 ms`, and `0.096 ms`, and now measures approximate warm runtime-step
    speedups of `0.194x` at `world_count=1`, `0.197x` at `world_count=4`, and
    `0.583x` at `world_count=16`
  - a later `2026-03-27` follow-on then moved the resident first-scope CUDA
    carrier off `cudaDeviceSynchronize()` onto a dedicated cache stream,
    swapped the hot-path copies to `cudaMemcpyAsync(...)`, and initially
    regressed warm runtime-step wall by creating/destroying CUDA timing events
    every step; that host overhead is now removed again by caching and reusing
    the timing events inside the resident carrier
  - fresh post-stream matrix on `world_count=1,4,16`
    (`steps=8`, `write_back_every=1`) still keeps warm write-back cost and
    `test_warm_chain_command_lane_ms` at `0.0`, lands
    `test_warm_chain_total_ms` around `0.083 ms`, `0.086 ms`, and `0.091 ms`,
    and now measures warm runtime-step time at about `0.096 ms`, `0.099 ms`,
    and `0.108 ms` with approximate warm runtime-step speedups of `0.136x`,
    `0.190x`, and `0.439x`; this narrows synchronization semantics but does
    not materially beat the earlier sync+replay-fusion checkpoint
  - a later `2026-03-27` host-side follow-on then teaches
    `WorldBatchRuntime` to fill the resident `pilot + world_time` projection
    through raw pointer entrypoints backed by a reusable pinned host buffer,
    so the no-missile graph can keep a fixed memcpy source and skip per-step
    memcpy-node param updates on the covered aircraft-only path
  - that pinned-buffer line initially regressed the first measured runtime step
    by lazily allocating host-pinned memory inside `step_batch()`, but the same
    pass now preallocates the buffer during cache/upload setup so the cold
    spike is removed again before benchmarking
  - fresh post-pinned-buffer matrix on `world_count=1,4,16`
    (`steps=8`, `write_back_every=1`) keeps warm write-back cost and
    `test_warm_chain_command_lane_ms` at `0.0`, lowers
    `test_warm_chain_total_ms` to about `0.077 ms`, `0.080 ms`, and
    `0.081 ms`, lands warm runtime-step time around `0.089 ms`, `0.092 ms`,
    and `0.100 ms`, restores first runtime-step wall to about `20.3 ms`,
    `1.9 ms`, and `2.2 ms`, and now measures approximate warm runtime-step
    speedups of `0.150x`, `0.200x`, and `0.571x`; this is a better
    fixed-overhead checkpoint than the plain scratch-vector graph pass, but the
    runtime-switch backend still fails promotion on CPU-vs-GPU slowdown alone
  - a fresh cold-process sanity run on the explicit `world_count=16`
    runtime-step backend also confirms that the earlier event-timing regression
    is gone again: the first runtime step is still down around `20 ms`
    rather than the abandoned `~950 ms` cold spike
  - the same runtime-switch sweep now also shows that none of those rows are
    promotion-ready yet: `world_count=1`, `world_count=4`, and
    `world_count=16` are now all blocked only by CPU-vs-GPU slowdown at the
    current runtime boundary (`total_wall_speedup` and
    `warm_runtime_step_speedup`), not by write-back burden
  - the newest `2026-03-27` follow-on then lets the benchmark-style
    quiescent/no-missile resident path skip projection H2D entirely: when the
    host-side cached session has no pending pilot/mission projection updates,
    `WorldBatchRuntime.step_batch()` now advances `world_time_s` inside the
    resident first-scope CUDA state itself and replays the aircraft-only chain
    in place
  - that first device-side advance-time pass did remove the remaining covered
    H2D copy (`test_warm_chain_host_to_device_ms == 0.0`) but initially gave
    some wall back to single-launch/runtime overhead, so the next pass wrapped
    the same device-only resident replay in its own cached CUDA graph to
    recover most of that fixed cost
  - regression coverage still locks that clean resident runtime behavior after
    the graph follow-on: the explicit runtime-step backend keeps
    `chain_command_lane_ms == 0.0`, `chain_host_to_device_ms == 0.0`,
    `chain_device_to_host_ms == 0.0`, and `first_cpu_divergence_step=0` on the
    covered cached-session fixture while later extract/live access still
    matches the cached and live packed-state digests
  - stable rerun post-device-advance-time-graph matrix on `world_count=1,4,16`
    (`steps=8`, `write_back_every=1`) keeps warm write-back cost and both
    `chain_command_lane_ms` / `chain_host_to_device_ms` at `0.0`, lands around
    `0.111 ms`, `0.096 ms`, and `0.099 ms` warm runtime-step time with warm
    chain totals near `0.078 ms`, `0.079 ms`, and `0.082 ms`, and measures
    approximate warm runtime-step speedups of `0.121x` at `world_count=1`,
    `0.193x` at `world_count=4`, and `0.466x` at `world_count=16`
  - that latest checkpoint shows the projection-traffic line is now mostly
    exhausted for the covered runtime-step experiment: `world_count=4/16`
    roughly recover the earlier pinned/raw wall while keeping hot-path H2D at
    zero, but the runtime-switch backend is still promotion-blocked by
    CPU-vs-GPU slowdown, so the remaining fixed wall now looks more like replay
    body / runtime glue cost than projection materialization
- [ ] Next: if promotion toward `step_batch()` is still desired, stop spending
  more time on H2D/write-back/synchronization micro-passes first and instead
  reduce the remaining fixed replay wall inside the resident CUDA chain until
  the experimental gate is green, then add a maintained `p5` end-to-end A/B
  gate before revisiting adoption.

## Current first-scope stage list

The first traceable GPU-migration scope is:

1. `CommandLinkMovement`
2. `CommandLinkAction`
3. `CommandLinkMission`
4. `ActionMapping`
5. `CommandLag`
6. `FlightControl`
7. `ClearForces`
8. `ComputeAeroState`
9. `ComputeForces`
10. `ComputeAerodynamics`
11. `GroundContact`
12. `RotationalIntegrate`
13. `MissileGuidance`
14. `LeapfrogIntegrate`
15. `NavigationSystem`
16. `UpdateInstruments`
17. `FuelConsumption`
18. `MassUpdate`

Deferred for later stages:

- `SensorSystem`
- `DataLinkFusionSystem`
- `ProximityFuze`
- EW and logistics tail systems

Those systems are still part of the full runtime, but they are not in the first
exact-GPU scope because the current exact-state parity contract does not yet
cover their full surfaces.
