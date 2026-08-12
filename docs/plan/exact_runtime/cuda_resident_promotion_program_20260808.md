# CUDA-resident Promotion Program (CP)

Language:
- English canonical: `cuda_resident_promotion_program_20260808.md`
- Chinese companion: [cuda_resident_promotion_program_20260808.zh.md](cuda_resident_promotion_program_20260808.zh.md)

Document kind: `plan`
Lifecycle: `maintained`
Canonical: `docs/plan/exact_runtime/cuda_resident_promotion_program_20260808.md`
Owner: `exact-runtime / CUDA-resident promotion workline`
Last verified: `2026-08-08`

- Program id: `cp.promotion_target.cuda_resident.20260808`
- Branch: `codex/cuda-resident-promotion-program`
- Worktree: `.codex/worktrees/cuda-promotion` (ignored path)
- Baseline: `a4a2b932` (main, PR #25 merge)
- Predecessors: [RB0-RB11](cuda_resident_rb11_closure_20260731.md),
  [CR2-0..CR2-7](cuda_resident_cr2_closure_20260805.md)

## Authorization

Both predecessor programs closed without promotion and required "a new explicit
program and user-authorized scope" to reopen. The repository owner authorized
this program on `2026-08-08` with the stated goal of **promotion**: making the
CUDA-resident backend a selectable maintained backend.

This authorization covers implementation and evidence work toward the promotion
gates. It does **not** pre-approve promotion itself. Promotion remains a
separate, explicitly recorded decision that requires all gates green plus an
independent review. Until then every maintained boundary from CR2-7 holds:
CPU stays the default, `compiled_experimental_backend` /
`supports_resident_state` / `supports_device_observation_view` stay false.

## Why the predecessors closed

RB10 applied six frozen gates to RB9 and recorded six failures. CR2 then
repaired most of them structurally. The CR2-7 closure record
(`cuda_resident_cr2_closure_20260805.json`) is the authority on the resulting
state, and it reports `common_spi_full_window_available=true`,
`device_consumer_boundary_available=true`,
`selected_slice_parity_complete=true`, `resource_static_topology_complete=true`,
`production_matrix_complete=true`, and
`small_batch_selection_advisory_complete=true`, with only
`achieved_counter_gate_complete=false` among the measurement gates.

Consolidating both closures against the code as it stands on baseline
`a4a2b932`:

| # | Gate | Status at this program's start | Verification |
| --- | --- | --- | --- |
| G-A | Full facade/window advance measured through the public SPI | **Repaired by CR2** | `cuda_resident_cr2_matrix_session.cpp` runs `inject -> evaluate -> advance -> export_state` only; surface id `cuda_resident.full_window_spi.v1`; the probe declares `operation_sequence = [inject, evaluate_empty, advance_world_batch, ...]` |
| G-B | CPU and CUDA invocation surfaces equivalent | **Repaired by CR2** | Same SPI-only session drives both lanes. `CudaWorldStore::advance_window()` self-publishes when the window is merely `input_injected` (`cuda_world_store.cpp:348`), so no caller needs the public `publish_stage` |
| G-C | Learner-equivalent consumption measured | Boundary exists (CR2-3 lease); a real learner consumer does not | `cuda_resident_device_consumer.cpp` present; CR2-7 gate true is for the *boundary*, not for learner-equivalent consumption |
| G-D | Achieved hardware counters complete | **CLOSED 2026-08-10 (CP-4c)** | Collected under elevation; tracked in `cuda_resident_cp_counter_evidence_20260810.json` with `cr2_5_achieved_counter_gate_complete=true` |
| G-E | Selected-slice parity out of quarantine | **Repaired by CR2-4b** | 12 fields released |
| G-F | Small-batch default does not regress | Advisory exists, no fix | World 1 regresses 7-36x; CR2-6b routes world 1 to CPU |

Correction to an earlier reading of this program's own scope: G-A and G-B are
**not** open architectural work. `publish_stage` survives as a public method on
`CudaResidentBackend`, but its only remaining callers are C++ tests and the
superseded RB9 probe — not the CR2 matrix or full-window paths that produced the
closing evidence. The RB10 verdict on those two gates was correct when written
and is now stale.

The practical consequence is that this program is much shorter than a
six-gate repair. The real remaining work is G-D (a host-permission problem, not
a code problem), G-C, G-F, and the promotion authorization itself.

## Confirmed root cause of the counter blocker

`ERR_NVGPUCTRPERM` is not a code defect. On this host the registry key
`HKLM\SOFTWARE\NVIDIA Corporation\Global\NVTools` is absent, so the driver
applies its default admin-only counter policy (`RmProfilingAdminOnly` defaults
to enabled). Owner decision (2026-08-08): collect counters by running Nsight
Compute **elevated**, and do not modify the registry. The system-wide
`RmProfilingAdminOnly=0` alternative was considered and rejected as an
unnecessary security-posture change.

Consequence for this program: counter collection is an operator-assisted step,
not an automatable one. Every counter artifact must record that it was collected
under elevation.

## Verified host and toolchain

| Item | Value |
| --- | --- |
| GPU | NVIDIA GeForce RTX 3090 (SM86) |
| Driver | 595.95 |
| CUDA Toolkit | 13.0.88 (`nvcc` at `CUDA/v13.0`) |
| Host compiler | MSVC 14.44.35207 (VS 2022 BuildTools) |
| Generator | Ninja |
| Nsight Compute | 2025.3.1 (collector requires `2025.3.1.0`) |
| Nsight Systems | 2025.3.2.474 (validator requires `2025.3.2`) |
| OS | Windows 11 build 26200 |

## CP-0 verified baseline result

CUDA-on configure, build, and test all verified green on baseline `a4a2b932`
with `EF_ENABLE_CUDA_EXPERIMENTS=ON` and `CMAKE_CUDA_ARCHITECTURES=86`:

| Step | Result |
| --- | --- |
| CMake configure (Ninja, CUDA 13.0.88) | Success, 431s |
| `ef_cuda_resident_backend` | Built 15/15, static library linked |
| `ef_cuda_resident_lifecycle_test` | **14 cases / 599 assertions, all passed** |
| `ef_cuda_resident_replay_test` | **4 cases / 77 assertions, all passed** |

Both test executables ran against the real RTX 3090. ptxas reported zero spill
stores and zero spill loads across the CUDA translation units, consistent with
CR2-5a.

This is a materially better starting position than the zero-CI-coverage risk
implied: despite no CI lane and a toolchain now at CUDA 13.0, the 6,229-line
surface still compiles and its CUDA-on suites still pass. The bit-rot risk is
real but has not yet materialized, which makes CP-1 (a compile lane) cheap
insurance rather than a repair job.

Scope note: these suites cover the fixed-air fixture lifecycle, state barriers,
phase A/B/D CPU-reference parity, and the replay/shadow harness. They do not
exercise a learner consumer or achieved counters — gates G-C and G-D below. The
SPI-equivalent full window is exercised by the separate CR2 matrix and
full-window probes rather than by these two suites.

## Iteration plan

Iterations are `CP-<n>`, one coherent commit each, following the
repository-consolidation protocol (analyze / implement / validate / register /
commit). Critical phases get one independent review before landing.

| Iteration | Scope | Exit gate |
| --- | --- | --- |
| CP-0 | This freeze; verify CUDA-on build still compiles on the baseline; record host/toolchain identity; re-verify the RB10 gate verdicts against current code | Program frozen; CUDA-on build result recorded honestly; stale gate verdicts corrected |
| CP-1 | CUDA-on compile lane so the 6,229-line surface stops rotting: a CI job (or, if no GPU runner is available, a documented local checkpoint plus an architecture test asserting the CUDA source set stays wired). Must also assert each CUDA probe still *executes*, not merely links -- the retired resource probe compiles cleanly as a stub | **LANDED 2026-08-11.** Both clauses met: `ci-cuda-compile` builds and links the CUDA-on surface, and 14 toolkit-free gates catch a retired-to-stub probe. See "CP-1 landed" below |
| CP-2 | Split `EF_ENABLE_CUDA_EXPERIMENTS` into a helper-surface flag and a resident-backend flag, so the two semantically different surfaces are independently selectable | **LANDED 2026-08-11.** `EF_ENABLE_CUDA_RESIDENT_BACKEND` gates the resident device sources and probes; `EF_ENABLE_CUDA_EXPERIMENTS` gates `src/gpu/*.cu`; either triggers `enable_language(CUDA)` |
| CP-3 | Retire the private-sequence residue that made RB10's G-A/G-B verdicts possible: demote or remove the public `publish_stage`/`partial_sync_commit` from `CudaResidentBackend` now that only tests and the superseded RB9 probe call them, and add a gate asserting the resident backend exposes no non-SPI window-advance entry point | **LANDED 2026-08-11.** `publish_stage` and `partial_sync_commit` removed from `CudaResidentBackend` public interface; all 9 callers migrated to `store.publish_stage()` / `store.partial_sync_commit()` via `CudaResidentBackendTestAccess`; architecture gate `test_cuda_resident_backend_has_no_non_spi_window_advance_entry_points` added to `test_cuda_surface_wiring.py` |
| CP-4 | **G-D: achieved counters under elevation** — occupancy, divergence, global/local/shared traffic for all 10 kernels. This is the one hard blocker and the highest-value iteration | G-D closed with real counters, or a recorded second external blocker |
| CP-5 | Kernel-level optimization driven by CP-4 findings. Known candidates below | **LANDED 2026-08-12.** The six window-commit launches are one fused `window_commit_body_kernel` (12 -> 7 launches per captured window); kernel catalog v3 supersedes v2 through a static-asserted fold; released-state digests stay bit-identical to the frozen CR2-6b capture across both lanes and both campaigns; warmed end-to-end p50 improved in all 20 CR2-6b comparison rows (0.63-0.99x). See "CP-5 landed" below |
| CP-6 | G-C: learner-equivalent consumption through the CR2-3 lease, without hidden host validation readback | **LANDED 2026-08-12.** `learner_equivalent_consumer_kernel` reads every element of the lease tensor, applies the contract-owned per-field affine normalization, and writes a device-resident world-major `[world, 15]` float policy-input buffer; measured at production protocol as matrix mode `no_export_learner_consumer` behind an explicit probe flag; CPU-reference parity over the full normalized tensor is a C++ oracle; released digests stay byte-identical to the CP-7b baseline in both lanes. See "CP-6 landed" below |
| CP-7 | G-F disposition: either fix small-batch overhead or freeze an explicit selection rule with world-count thresholds | **LANDED 2026-08-12, both halves.** CP-7a: `cp7.small_batch_selection_rule.v1` freezes world counts below 4 to the CPU reference as documentation-grade policy (no runtime selector; an architecture gate enforces zero runtime consumers), on the measured basis that world 1 carries a ~65.5 us single-thread device floor against a ~18-31 us CPU step; crossover value is a named CP-8 review item. CP-7b: the stage_publish and window_commit barriers are per-world epilogues of their stage kernels (5 -> 3 launches, syncs, status readbacks, and memsets per window); released-state digests stay bit-identical to frozen CR2-6b in all 30 rows, warmed e2e p50 falls 20-30% at world 1 and 8-21% (campaign 1) / 3-52% (campaign 2) elsewhere. See "CP-7b landed" below |
| CP-8 | Re-measure the 1/4/16/64/256 matrix after CP-5/CP-7 land, order-balanced, two campaigns | Post-optimization evidence comparable to CR2-6b |
| CP-9 | Promotion decision: all gates + independent review, or a recorded hold with the exact missing authority | Explicit, evidence-backed verdict |

CP-1, CP-2, and CP-3 are independent of the rest and can land in any order.
CP-4 gates CP-5. CP-8 follows CP-5 and CP-7. CP-9 requires CP-3 through CP-8.

**CP-4 first if sequencing by value.** Because CR2 already repaired the
call-surface gates, the achieved-counter blocker is the only thing standing
between the existing evidence base and a promotion decision on measurement
grounds. It is also the cheapest: it needs an elevated shell, not a code change.

## CP-4 blocker discovered: the resource probe was retired after CR2 closed

Attempting the counter collection revealed a second blocker in front of G-D that
neither closure records, because it was introduced after both closed.

`ef_cuda_resident_resource_probe` — the frozen Release/SM86 binary that CR2-5a
and CR2-5b profiled — **no longer exists as a working probe**. The semantic stage
migration (`cuda_resident_semantic_stage_migration_20260807.md`, landed in PR #25
as `8884146b`) replaced its 350-line body with an 18-line stub that fails closed:

```
CUDA resident resource probe retired: semantic kernel catalog requires a
versioned resource-evidence recapture
```

`kCaptureProbeV1Retired = true` in
`src/runtime/contracts/cuda_resident_resource_evidence_contract.h` enforces this
with a `static_assert`.

**This retirement is correct and must not simply be reverted.** The migration
record states the reasoning plainly: the frozen evidence contract and its
captured JSON "describe a historical binary, not the renamed current source. A
fresh resource claim requires a new schema version and a new capture; the
existing probe must fail closed on the old trace signature rather than relabeling
historical evidence."

### What actually changed, and what did not

The renaming was a pure 1:1 relabel of the same ten kernels. Comparing the
contract's frozen catalog against the current `.cu` sources:

| Contract catalog (frozen, historical) | Current source symbol |
| --- | --- |
| `prepare_phase_a_controls_kernel` | `control_preparation_kernel` |
| `phase_b_forces_kernel` | `flight_dynamics_forces_kernel` |
| `phase_b_aerodynamics_kernel` | `flight_dynamics_aerodynamics_kernel` |
| `phase_b_integrate_kernel` | `flight_dynamics_integrate_kernel` |
| `phase_d_instruments_kernel` | `instrument_projection_kernel` |
| `phase_d_configuration_kernel` | `configuration_projection_kernel` |
| `phase_d_episode_kernel` | `episode_projection_kernel` |
| `phase_d_pack_observation_kernel` | `pack_device_observation_kernel` |
| `phase_d_consumer_smoke_kernel` | `device_observation_consumer_smoke_kernel` |
| `apply_barrier_kernel` | `apply_barrier_kernel` (unchanged) |

Ten kernels before, ten after; the launch count (12), grid (`2x1x1`), block
(`128x1x1`), and world count (256) are unchanged in the contract. So the
recapture is a re-freeze against renamed symbols, not a re-derivation of the
execution graph. The trace signature `cb31675ee34e5015` / 80,469 bytes in the
contract still matches the CR2-5a evidence JSON, which is exactly why it must
fail closed: that digest describes the pre-rename binary.

### CP-4a result: recapture complete and validated

The v2 recapture landed and reproduces the frozen capture exactly.

Contract: `kKernelSpecsV2` / `kLaunchSequenceV2` carry the semantic symbols, and
`kKernelSpecsV2Migration` pins the 1:1 correspondence to v1. Four new
`static_assert`s enforce it at compile time — v2 catalog completeness, migration
bijection in both directions, and launch-for-launch correspondence at identical
indices. The v1 catalog, trace digest, and profile id are untouched.

Probe: restored against the semantic accessors, emitting schema
`cuda_resident.cp.resource_capture_probe.v2` with `supersedes_schema_version`
pointing at v1. Two additions the v1 probe lacked: `require_catalog_alignment`
fails closed if the emitted rows ever drift from the v2 catalog, and the report
carries `achieved_counters_present: false` so a static capture can never be
mistaken for a counter capture. CMake restores the backend, profiler, and JSON
dependencies — the precondition stated at retirement ("a versioned kernel
catalog") is now met.

Validation on the RTX 3090 under CUDA 13.0.88:

| Check | Result |
| --- | --- |
| Trace signature | `cb31675ee34e5015` / 80,469 bytes — **identical to v1** |
| Kernel resource table vs frozen v1 | **0 mismatches across 10 kernels** (registers, stack bytes, shared bytes, theoretical occupancy, blocks/warps per SM) |
| `ef_cuda_resident_lifecycle_test` | 14 cases / 599 assertions passed |
| `ef_cuda_resident_replay_test` | 4 cases / 77 assertions passed |
| Internal-code governance | **0 errors, 0 warnings** (baseline for these two files was 37 errors) |

The zero-mismatch result is the load-bearing one: it means the rename really was
cosmetic, the v2 capture measures the same execution graph, and the three
optimization leads below carry over unchanged rather than needing re-derivation.
It also confirms the toolchain move to CUDA 13.0 did not shift register
allocation or occupancy.

Governance note: the frozen v1 catalog and the v1 side of the migration table
necessarily contain phase-lettered identifiers, which the internal-code gate
flags. Each is annotated `internal-code: compatibility` per-line with its reason
rather than renamed — renaming them would invalidate the evidence they key.

### CP-4b result: the duplicate catalog is gone

The static-resource parser under `tools/diagnostics/` held its own hard-coded
copy of the kernel catalog. Its filename is
`cuda_resident_cr2_resource_static.py`, where `cr2` means the historical
runtime-program-2 label, kept because renaming the module is out of scope.
That second owner is the direct cause of the drift:
when the migration renamed the kernels, the C++ contract moved and nothing forced
the Python side to follow, so the collector kept validating against symbols that
no longer existed and reported nothing wrong.

The module now parses both catalogs out of the C++ contract, which becomes the
single owner. `kernel_catalog(1)` and `kernel_catalog(2)` return the frozen and
semantic catalogs respectively; the retained `KERNELS` alias still resolves to v1
so every existing v1 validator and the frozen evidence it checks are unaffected.
An unknown version raises rather than silently returning something plausible.

Three tests replace the single retirement test, which asserted the probe stays a
stub and so was falsified by CP-4a by design:

- `test_frozen_v1_capture_identity_survives_the_semantic_kernel_migration` —
  v1's catalog, digest, and profile id must not follow the rename.
- `test_v2_capture_supersedes_v1_without_reviving_the_retired_probe` — v2 exists,
  the retirement marker survives, all five `static_assert`s are present, and
  every v2 symbol is one the current `.cu` sources actually emit.
- `test_python_kernel_catalog_has_no_second_owner` — a literal catalog cannot be
  reintroduced, both parsed catalogs match the contract, and v1/v2 agree on shape
  while differing on names.

The third test is the one that would have caught the original drift.

### CP-4c blockers found before spending an elevated run

Elevation alone will not produce usable counter evidence. Checking the collector
chain against the v2 probe surfaced two further blockers, both worth recording
before an operator-assisted step is requested.

**1. Both collectors are pinned to v1 identity.** The counter collector sets
`PROFILE = resource.PROFILE`, which resolves to the frozen v1 profile id
`cr2.resource.steady_full_window_body.sm86.v1` -- its leading `cr2` means the
historical runtime-program-2 label. It then validates
`parent["profile_id"] == PROFILE`. The v2 probe emits
`cp.resource.steady_full_window_body.sm86.v2`, so the run would be rejected on
profile mismatch. The counter collector also requires a *parent resource-evidence
JSON* and checks the v2 report's `binary_sha256` / `probe_sha256` against it — and
no v2 parent artifact exists yet, because producing one needs its own collector
run first.

So the real chain is: v2 static evidence JSON must be produced and accepted
before a v2 counter attempt can be validated at all. Both collectors need a
version-aware identity path, mirroring what CP-4b did for the kernel catalog.

**2. ~~The installed Nsight Systems is older than the pinned version.~~
Withdrawn — this blocker was an error on my part.** The resource schema validator
requires `nsight_systems_version == "2025.3.2"` exactly, and **2025.3.2.474 is
installed on this host**. The original claim that only 2024.6.2 and 2022.4.2 were
present came from listing the Nsight install root and reading the first two
entries instead of enumerating all of them. Nsight Compute is likewise fine:
2025.3.1 installed against a required `2025.3.1.0`.

The three options that were offered — install 2025.3.2, relax the pin to a
version range, or accept unparented counters — are therefore all moot. The pin
matches reality and needs no change, and no provenance gate has to be weakened.
Recorded rather than deleted because the owner selected the "install 2025.3.2"
option in response, and the outcome should not silently look like an install
happened.

### CP-4c-B result: collectors are version-aware

With blocker 2 withdrawn, blocker 1 was the only real prerequisite and is now
closed.

- The schema validator (`cuda_resident_cr2_resource_schema.py`: `cr2` means the
  historical runtime-program-2 filename prefix, retained throughout) gains
  `SCHEMA_V2` / `PROFILE_V2` and a
  `schema_version_of()` dispatcher. `validate_report` now validates a report
  against the generation it declares: v1 keeps its exact frozen `evidence_date`,
  `baseline_commit`, and `candidate_state` pins, while v2 accepts its own ISO
  date and commit but must still declare an `*_unpromoted_worktree` state — a
  recapture grants no authority.
- `LAUNCH_SEQUENCE` was a third duplicate of contract data and is now derived
  from it via a new `launch_sequence(version)` in the static module, alongside
  `kernel_catalog(version)`.
- The evidence collector `cuda_resident_cr2_resource_evidence.py` means the
  runtime-program-2-prefixed module: it gains `PROBE_SCHEMA_V2` and accepts
  either generation's key set. A v2 probe must additionally declare the
  schema it supersedes, assert `trace_signature_matches_v1`, and carry
  `achieved_counters_present: false` so a static capture can never be read as a
  counter capture.

Verified: the frozen v1 evidence still validates byte-for-byte as v1, the v2
probe output is now accepted by the collector, an unknown generation fails closed
rather than defaulting to v1, and 25 tests pass.

This is a real cost increase over the CP-0 estimate, and it is worth stating
why it happened: the semantic migration correctly refused to relabel frozen
evidence, but it retired the only capture tool without a replacement, so the
next counter attempt inherits a recapture obligation. CP-1's compile lane would
not have caught this — the stub compiles fine. A probe-executability check
belongs in CP-1's scope.

## CP-6 landed: consumption is learner-equivalent, not a smoke probe (2026-08-12)

The owner froze the reviewer's design draft on 2026-08-12 (mode id
`no_export_learner_consumer`; per-field affine normalization with fifteen
representative constants; feature count 15; smoke kernel retained for
lifecycle coverage) and the iteration landed the same day. Scope statement
carried from the draft: this closes G-C on the resident **fixture** contract
(the fixed-air fifteen-field observation); the production dictionary
observation stack stays outside the gate's coverage and in the residual list.

What changed:

- `learner_equivalent_consumer_kernel`
  (`cuda_world_store_cuda_observation.cu`) reads every element of the lease
  value tensor, applies `(value - offset) * scale` per field, and writes a
  device-resident world-major `[world_count, 15]` float32 policy-input buffer;
  ids pass through with epoch semantics unchanged. The constants live in
  `cuda_resident_learner_consumption_contract.h` as the single owner — field
  identities are statically asserted against the projection contract's packed
  order, and the kernel receives the table by value, so no device symbol can
  drift.
- The consumer seam carries the output honestly: `ConsumerRequest` gains
  `learner_equivalent`, the receipt's `first_values` became `values` with
  `values_per_world` and a `TensorDescriptor outputs` (`[world, 1]` for the
  smoke consumer, `[world, 15]` for the learner), and the learner submission
  fail-closes with `incompatible_layout` unless the lease carries the
  fifteen-field layout. CR2-3 discipline re-pinned for the new kernel: no
  device-to-host copies in submit or await; the two-copy diagnostic
  materialization stays outside every sample timer.
- Measurement went through the existing matrix machinery: the session `Mode`
  gained a `learner_consumer` kind, and the CUDA probe appends the mode behind
  an explicit `--learner-consumer` flag.

Deviations from the draft's letter, with reasons. The draft said "replace the
smoke kernel as the measured consumer" and "add a mode to the matrix": the
frozen CR2-6a `kModes` table was **not** extended, because the matrix evidence
validators are still single-generation pinned (the CP-8 kickoff's finding) and
unflagged reports must keep the frozen shape for CR2-6b comparability. The
learner mode is therefore the measured-consumer lane for G-C, while the frozen
`*_device_consumer` modes keep the smoke consumer so their rows remain
comparable with CR2-6b and the CP-5/CP-7b baselines. Registering the mode in
the frozen table and making the evidence builder generation-aware stays in
CP-8's lane. Likewise the RB9 ledger still models the frozen RB9 mode set; the
learner mode's transfer profile is documented here, not retrofitted into the
frozen ledger. The captured-window kernel catalog stays at v4: the learner
kernel is not part of the captured window's operation sequence, and its static
capture rides with CP-8's re-matrix generation refresh.

Validation and evidence:

- CUDA-on, RTX 3090: lifecycle 16/16 (643 assertions, including the new CP-6
  parity case), replay 4/4, full-window 6/6. The parity oracle rebuilds every
  policy input on the host from the public export with the same clip-to-float
  conversion and contract constants.
- Architecture gates (new `test_cuda_resident_learner_consumption.py`): the
  measured learner path reads the full tensor (a single-element probe can
  never satisfy G-C again), submit/await carry no hidden D2H, the policy
  layout/dtype/feature count are pinned to the contract, the normalization
  table has exactly one owner, and the mode id stays out of the frozen table
  with the probe taking it from the contract constant.
- Production-protocol campaigns, order-balanced (cpu, cuda, cuda, cpu), five
  modes, in `cuda_resident_cp6_learner_consumption_20260812/`
  (sha256/16: cpu1 `4eda3f663bb35d23`, cpu2 `118a6dc168b44bd5`, cuda1
  `d0c7e0c058c2a3e9`, cuda2 `4b7d771b903cc217`). Released digests are
  byte-identical to the CP-7b baseline in both lanes at every world count
  (CUDA `2df3698050d55a9a`, CPU `881cff2cea79e49a` at world 1), so the
  consumer change provably touched no simulation output.
- Cost of learner-equivalent versus smoke consumption is inside this host's
  run-to-run noise: warmed end-to-end p50 deltas are sign-mixed across the two
  campaigns (-12% to +45%, with the frozen smoke mode itself drifting -47% to
  +43% against CP-7b session-to-session), and rollout per-window deltas at
  world 256 are -1.1%. No world count shows a consistent penalty in both
  campaigns. G-C closes on consumption *existing and being measured*, not on a
  performance claim; the consumer's 15x read-and-write amplification is below
  the measurement floor at these world counts.

## CP-7b landed: the in-window barriers are epilogues (2026-08-12)

The world-1 timeline attribution ranked the host skeleton: copies, then
launches, then memsets and synchronizations, five of each per window. CP-7b
takes the candidate-1 slice with the smallest semantic blast radius: the
stage_publish barrier is now the final per-world epilogue of
`control_preparation_kernel`, and the window_commit barrier the final epilogue
of `window_commit_body_kernel`, each an exact mirror of the corresponding
`apply_barrier_kernel` branch. `apply_barrier` keeps its input-injection
launch (inject is a separate SPI call that must report its own result) and
its generic body. Per window the base path falls from five launches, five
synchronizations, five status readbacks, and five status memsets to three of
each; the staging copies are untouched.

The deferred-check shape the prep note sketched was rejected during design:
with two state slots and three stages, deferring all checks to the window end
destroys the rollback point for an inject-stage failure (the next stage's
staging copy overwrites the only clean slot). The epilogue fold keeps every
stage's host check and flip exactly where they were, so per-stage failure
attribution, the retry contract, and the fault-injection hooks survive with
their observable behavior unchanged -- the barrier-commit hook now fails the
stage after a clean kernel, before the flip, which is the same external
contract the separate barrier launch gave it.

Equivalence and improvement, both measured on the recorded host:

| Check | Result |
| --- | --- |
| ctest | lifecycle 14 cases / 579 assertions, replay 4/77, full-window: pass |
| Released-state digests | **bit-identical to frozen CR2-6b in all 30 rows** (20 CUDA + 10 CPU), both campaigns |
| Workload identity | trace signature `cb31675ee34e5015` unchanged |
| Captured window (nsys) | exactly 5 launches, 3 synchronizations, 11 memcpys, 3 memsets -- the predicted v4 profile, measured |

Timing against the tracked CP-5 evidence (same protocol, quiet machine,
order-balanced): warmed e2e p50 at world 1 falls 20-30% across the four modes
(no-export 0.396 -> 0.279/0.318 ms); world 16/64/256 rows improve 1-25% in
campaign 1 and 3-52% in campaign 2 (campaign 1's world-4 rows carry transient
spikes and are not claimed; campaign 2's world-4 rows improve 5-26%).
Cumulatively from the pre-CP-5 baseline, the world-1 no-export window is down
~36-44%. The CPU lane still wins world 1 by ~15x -- the CP-7a rule stands,
unchanged. Raw reports are content-addressed under
[cuda_resident_cp7b_barrier_fold_20260812/](cuda_resident_cp7b_barrier_fold_20260812/):

| Report | Bytes | SHA-256 |
|---|---:|---|
| Post CPU campaign 1 | 104,021 | `7e97c5f2fe58ef461cb93892744f6bc21824bcaf4b474b8aacb6e17b1ac8960f` |
| Post CUDA campaign 1 | 194,458 | `e84a7f059adf3acd743071d247060cfa4d986238ae155951f45ebf0250ddd6da` |
| Post CUDA campaign 2 | 194,262 | `bd7d68315a93fdaca0ceb2faeb919d7802bb3e1011def2af977b29ee936cc989` |
| Post CPU campaign 2 | 103,615 | `af8cf7f349c080503859452f64ac7541f44a4ba714e50a5095440a0e5e04bbd7` |

Catalog v4 carries the governance: the same five kernels as v3 (a checked
claim -- `kernel_sets_match_v3_to_v4()`), five launches with compound stage
names for the folded pair, and a static-asserted absorption walk
(`launch_sequences_correspond_v3_to_v4()`) that reproduces v4 from v3 by
merging each in-window barrier into the launch before it. The probe emits
schema v4 with a `launch_absorption` table derived by the same walk; the
collectors dispatch on generation with v4-specific API and transfer
expectations (launches 7 -> 5, syncs 5 -> 3, memcpys 13 -> 11, memsets
5 -> 3, and nothing else -- measured, not asserted); the counter chain
derives `kRequiredLaunchCountV4 = 5` from the contract. v1/v2/v3 stay frozen
and their tracked evidence validates byte-for-byte. The fused window body
with its epilogue is 112 registers / 40-byte stack / zero spills (down from
116 registers at v3); `window_commit_body.cu` crossed the 700-line soft
target (748) and is registered as a watch item rather than split, because
the phase bodies are verbatim copies of the retired kernels kept for parity
fidelity. The generation-supersession gates moved to their own module
(`test_cuda_resident_resource_generations.py`) to keep both test files under
the soft target.

### CP-7c: the v4 static parent exists (2026-08-12)

[cuda_resident_cp7b_resource_evidence_20260812.json](cuda_resident_cp7b_resource_evidence_20260812.json)
(11,032 bytes,
`3c1fbb40f9acdbe92f3f509161efd24d0b69b4a5cff8d95ee4fcd4351031e7e3`) is the
v4 static/topology capture, baseline-pinned to the CP-7b commit. Five
launches over five kernels, trace digest unchanged, and the nsys API
inventory measures the fold delta exactly: launches 7 -> 5, synchronizations
5 -> 3, memcpys 13 -> 11, memsets 5 -> 3, with every other count and every
transfer byte total matching v3 (the two removed status readbacks account
for the eight-byte D2H difference). One honest correction surfaced by the
recapture: the Nsight synchronization *activity* row count is
timing-dependent on WDDM (6 and 7 both observed for the same binary), so the
v4 validator pins a narrow band instead of an exact value; the stable
invariants are the API counts. The next achieved-counter attempt
(elevation-gated, CP-8) has its v4 parent.

## CP-5 landed: the window graph is one launch (2026-08-12)

The CP-4 achieved counters redirected CP-5 away from register pressure and
stack elimination toward the decomposition itself: the split window graph ran
at 8.33-10.89% achieved occupancy with zero local traffic and zero divergence
on a device that was 99.8% idle, so the wall clock was the sequential launch
chain, not the kernels. RB6/RB7 split these kernels to bound register live
ranges; the counters showed occupancy was limited by warps, not registers, so
the split's benefit was measured to be absent while its cost -- five extra
launches and their inter-kernel gaps per window -- was the dominant term.

CP-5 therefore fuses the six window-commit launches (forces, aerodynamics,
integrate, and the three projections) into one `window_commit_body_kernel` in
`cuda_world_store_cuda_window_body.cu`. Per captured window the launch count
falls from 12 to 7 (base path 10 to 5); synchronization, copy, and allocation
counts are unchanged, and the versioned collector expectations pin exactly
that: the only CUDA API count that differs between the v2 and v3 generations
is `cudaLaunchKernel`.

### Equivalence is checked, not assumed

Every phase keeps its original kernel body verbatim -- including its global
loads and stores, its internal early returns, and its per-world guard
semantics -- as a `__device__` phase function; the fused kernel runs all six
phases unconditionally per world, which is exactly what the split graph did
(no kernel ever read the status flag; a failed world only marked status and
the host discarded the staged slot). The staging copy, host status check, and
barrier flip are untouched, so the fail-closed window contract is unchanged.

Verified on the RTX 3090 host:

| Check | Result |
| --- | --- |
| `ef_cuda_resident_lifecycle_test` | 14 cases / 579 assertions pass (includes per-phase CPU-reference parity; 599 pre-fusion, the delta is the six per-kernel resource-query checks folding into one) |
| `ef_cuda_resident_replay_test` | 4 cases / 77 assertions pass |
| `ef_cuda_resident_full_window_test` | pass |
| Released-state digests, CUDA lane | **bit-identical to the frozen CR2-6b capture** in all 20 rows, in both post-change campaigns and in the pre-change control run |
| Released-state digests, CPU lane | bit-identical to the frozen CR2-6b CPU capture (control: CPU code untouched) |
| Workload identity | trace signature `cb31675ee34e5015` / 80,469 bytes unchanged |

The digest table means the fused binary reproduces the exact released bytes of
the binary that CR2-6b measured, per world count and per mode. Cross-lane
digest inequality is a pre-existing property of the reset-determinism metric
(the frozen CPU and CUDA captures already differ there); cross-lane value
parity remains owned by the CR2-4b twelve-field comparison, which the matrix
session revalidates on every run.

### Catalog v3: a fold, not a relabel

The v2 catalog is now frozen history exactly as v1 became at CP-4: the
retained v2 static and counter evidence hashes against the pre-fusion
symbols, so `kKernelSpecsV2` and its migration table stay untouched. The new
generation is deliberately a different execution graph, and the contract
carries that as checked structure:

- `kKernelSpecsV3` (five kernels) and `kLaunchSequenceV3` (seven launches);
- `kKernelSpecsV3Fold`, total on v2 and surjective onto v3 -- six v2 kernels
  map to `window_commit_body`, the other four map 1:1;
- `launch_sequences_correspond_v2_to_v3()`: mapping every v2 launch through
  the fold and collapsing consecutive runs that land on the same fused kernel
  must reproduce the v3 sequence exactly, as a `static_assert`.

The capture probe emits schema v3 (`kernel_id_fold` replaces the 1:1
`kernel_id_migration`), aligns its rows against the v3 catalog fail-closed,
executes end-to-end on the 3090, and its report is accepted by the collector
as generation 3. The Python static parser, schema validator, and evidence
collector dispatch on the declared generation; the frozen v1 and v2 evidence
JSONs still validate byte-for-byte, and unknown generations fail closed. The
`WindowTransferLedger` diagnostic contract, the surface-wiring source pins
(eight files to seven), and the RB6/RB7 architecture tests now pin the fused
phase order instead of the split launch order.

Static resources of the fused kernel (ptxas, Release/SM86): 116 registers per
thread, 40-byte stack frame, zero spill stores, zero spill loads, 4 blocks
per SM, theoretical occupancy 33.3%. Theoretical occupancy is *lower* than
any split kernel's (58.3-100%); per the CP-4 counters that metric was never
the constraint at two-block grids, and CP-8 re-measures achieved values
against the v3 topology before any further conclusion is drawn from it.

### Measured improvement against CR2-6b (exit gate)

Protocol: the frozen CR2-6b production protocol, order-balanced across two
campaigns (CPU -> CUDA, then CUDA -> CPU), lanes never concurrent, same host
identity as CR2-6b, quiet machine, plus one pre-change CUDA control campaign
collected the same session from the CP-3 binary. Raw reports are
content-addressed under
[cuda_resident_cp5_window_fusion_20260812/](cuda_resident_cp5_window_fusion_20260812/):

| Report | Bytes | SHA-256 |
|---|---:|---|
| Pre-change CUDA control | 194,684 | `925543aca7759852937dd02aa08aceaf4bd2c5d67ee0a267e6b4f063920f7917` |
| Post CPU campaign 1 | 103,404 | `9d8f207bee871ec420a4088761cbb264ff7c6d9de85def94cd439795a5f4d01d` |
| Post CUDA campaign 1 | 194,455 | `012deaa2c5215eeef3a11c326ebdcb2d62dce2427363bc864d4402984c81794b` |
| Post CUDA campaign 2 | 194,585 | `3f4a85e67e9ef44cc1a6c5bc149d4b2cd19a09fec1b9a956da990a98abf95f52` |
| Post CPU campaign 2 | 103,303 | `ddf5ea2d6b71fe12172231b000c339779b87f412f58610160c4b3982b7e5d897` |

Against the frozen CR2-6b CUDA campaign (the program's stated comparator),
warmed end-to-end p50 improved in **all 20 rows**; ratios (post/baseline,
lower is better) by world count across the four modes:

| Worlds | e2e p50 ratio range | rollout p50/window ratio range |
|---:|---|---|
| 1 | 0.773-0.857 | 0.744-0.972 |
| 4 | 0.633-0.787 | 0.522-0.749 |
| 16 | 0.718-0.816 | 0.678-0.778 |
| 64 | 0.684-0.765 | 0.602-0.693 |
| 256 | 0.848-0.989 | 0.924-0.976 |

The same-session pre/post A/B isolates the fusion itself from four days of
host drift: warmed e2e p50 falls 8-25% at worlds 1-4, 0-12% at world 16,
0-26% at world 64 (largest in the device-consumer modes), and is flat to -11%
at world 256, where the two full-slot device copies and the five
synchronization points -- not launches -- dominate the window. Nearest-rank
p95 on 100 samples is noisy in both directions and is not claimed. Two
honest attributions follow: part of the all-rows improvement against the
frozen baseline is host drift rather than the fusion, and the world-256
steady-state window is now bounded by the fixed synchronization/copy cost
that CP-7 owns. World 1 remains 13-28x slower than the CPU lane end to end
-- G-F stands, unchanged in kind, for CP-7.

CP-8 re-runs the full order-balanced matrix as formal evidence after CP-7;
the reports above are the CP-5 gate measurement, not a replacement for that
campaign.

### CP-5b: the v3 static parent exists (2026-08-12)

[cuda_resident_cp_resource_evidence_20260812.json](cuda_resident_cp_resource_evidence_20260812.json)
(11,912 bytes,
`1bb3729aa159fe5ab7aa33dc496a06094dd11d552c81a3f21a50823cc4afec8b`) is the
v3 static/topology capture -- probe under Nsight Systems 2025.3.2 plus the
generation-aware collector, baseline-pinned to the CP-5 commit. It records
seven launches over five kernels with the trace digest unchanged, and its
nsys API inventory measures the fusion claim rather than asserting it: only
`cudaLaunchKernel` (12 -> 7) differs from the frozen v2 capture; every
synchronization, copy, memset, and allocation count and every transfer byte
total is identical. The fused kernel is 116 registers, 40-byte stack, zero
spills, theoretical occupancy 33.3%. The next achieved-counter attempt
(elevation-gated, CP-8) has its v3 parent; the v2 parent stays valid for the
frozen v2 counter evidence only.

## CP-3 landed

**Date:** 2026-08-11. **CUDA-on build:** 16/16 targets, BUILD_EXIT=0, zero
warnings. **ctest:** 3/3 (lifecycle 14 cases / 599 assertions, replay 4 cases /
77 assertions, full-window). **Architecture gates:** 44/44 (new gate included).

### What was removed

`CudaResidentBackend::publish_stage()` and
`CudaResidentBackend::partial_sync_commit()` are no longer declared in
`cuda_resident_backend.h` and no longer implemented in
`cuda_resident_backend.cpp`.

Before CP-3, the public interface exposed two non-SPI window-advance entry
points. Any C++ caller could call `inject → publish_stage → advance` and
sequence a window transition outside the SPI's `advance()` method. The SPI
contract ("`advance()` atomically runs a full world step") was held by
convention among callers, not by structure.

After CP-3, `advance()` is the only public path that advances a window.
Internally, `CudaWorldStore::advance_window()` calls `publish_stage()` when the
window state is `input_injected`, so the sequencing guarantee is now inside the
implementation, not delegated to callers.

### Caller migration

Nine callers updated:

| File | Line (approx) | Change |
| --- | --- | --- |
| `test_cuda_resident_backend_state.cpp` | 198 | `CHECK(store.publish_stage())` via `CudaResidentBackendTestAccess` |
| `test_cuda_resident_backend_state.cpp` | 211 | `CHECK_FALSE(store.partial_sync_commit())` via test access |
| `test_cuda_resident_backend_state.cpp` | 278 | `CHECK_FALSE(store.publish_stage())` — store declaration moved before this line; `CHECK_THROWS_AS` semantics replaced by `CHECK_FALSE` because `CudaWorldStore::publish_stage()` returns `bool`, not throw |
| `test_cuda_resident_control_preparation.cpp` | 121, 131, 132 | store declaration moved up; `CHECK(store.publish_stage())` / `CHECK_FALSE(...)` / `CHECK(...)` |
| `test_cuda_resident_flight_dynamics.cpp` | 87 | removed (advance handles it internally) |
| `test_cuda_resident_flight_dynamics.cpp` | 135 | `CHECK(store.publish_stage())` |
| `test_cuda_resident_full_window.cpp` | 376 | store declaration moved up; `CHECK(store.publish_stage())` |
| `test_cuda_resident_observation_projection.cpp` | 84 | removed (advance handles it internally) |
| `test_cuda_resident_replay_support.cpp` | 102 | removed (advance handles it internally) |
| `cuda_resident_rb9_probe_session.cpp` | 187 | removed — the RB9 probe called `publish_stage()` then `advance()`; since `advance_window()` calls `publish_stage()` internally when state is `input_injected`, the explicit call was redundant |

Three callers (flight_dynamics:87, observation_projection:84, replay_support:102)
were pure redundancy: `advance()` already called `publish_stage()` internally,
so removing the explicit call is a no-op behaviorally. Three callers
(control_preparation:121, full_window:376, flight_dynamics:135) needed the stage
published before inspecting intermediate state or before a forced failure
injection — these were rerouted through `CudaResidentBackendTestAccess::world_store()`
so they now call `CudaWorldStore::publish_stage()` directly. The state test
(backend_state:278) needed the store declaration hoisted; the `CHECK_THROWS_AS`
became `CHECK_FALSE` because the store method returns a bool rather than throwing.

### New architecture gate

`test_cuda_resident_backend_has_no_non_spi_window_advance_entry_points` added to
`tests/architecture/build_system/test_cuda_surface_wiring.py`. The gate reads
`cuda_resident_backend.h` up to the `namespace testing {` boundary and asserts
neither `publish_stage` nor `partial_sync_commit` appears in the public class
body. The `namespace testing` section is explicitly excluded — `CudaWorldStore`
still exposes those methods and the test-access helper legitimately uses them.

The gate is toolkit-free and runs on every machine. It catches a declaration
snuck back into the header even if no caller was added simultaneously.
next counter attempt inherits a recapture obligation. CP-1's compile lane would
not have caught this — the stub compiles fine. A probe-executability check
belongs in CP-1's scope.

## Known optimization space (from CR2-5a static evidence)

CR2-5a already measured static resources for all ten kernels. Three concrete
leads, all pending CP-5 achieved counters before acting:

1. **Four kernels carry 40 bytes/thread of stack**: Phase B forces, Phase B
   aerodynamics, Phase B integrate, Phase D instruments. Each contains three
   `LDL.64` and two `STL.64` SASS instructions. ptxas reported **zero spill
   stores and zero spill loads**, so these are genuine stack/local operations,
   not compiler spills. Removing the stack traffic is a real lead but must not
   be described as spill elimination.
2. **Occupancy floor at 58.33%**: the two Phase B 66-register kernels
   (forces, aerodynamics); integrate and Phase D instruments sit at 66.67% with
   64 registers. The other six kernels are at 100%. The build uses
   `-maxrregcount=0` (no cap), so a register-pressure experiment is available
   but was explicitly forbidden under the closed programs and is only unlocked
   here after CP-5.
3. **Launch shape is uniform and small**: all 12 launches use grid `2x1x1`,
   block `128x1x1` at 256 worlds. That is 256 threads total per launch for a
   256-world batch, i.e. one thread per world. Whether this is the right
   decomposition is an open question that achieved occupancy will inform.

Small-batch overhead (G-F) has a separate suspected cause: 5
`cudaDeviceSynchronize` and 13 `cudaMemcpy` calls per captured window. At world
1 that fixed cost dominates, which matches the observed 7-36x regression.

Theoretical occupancy must not be substituted for achieved occupancy in any
CP-5 justification. The leads above are stated against the pre-rename kernel
names; CP-4a re-established every one of them against the current symbols with
zero numeric drift, so they carry over directly (read `flight_dynamics_forces`
for `Phase B forces`, and so on through the migration table).

## G-D closed: achieved counters collected (2026-08-09)

The external blocker that stopped RB9 and CR2-5b is **resolved**. Under
elevation, Nsight Compute 2025.3.1 profiled all 12 launches (42-43 replay passes
each) and wrote a 19,049,324-byte report
(`sha256 ebdec20b3f8b37a42ccb409855013112b6df196948ea1edd5c9d643baee59553`).
No `ERR_NVGPUCTRPERM`. The unelevated run was executed first and reproduced the
predecessor blocker exactly, so the difference is attributable to elevation
alone.

`--set full` captured 1,699 metric columns. Achieved values for all five
required families, per launch, at 256 worlds:

| Family | Metric | Result |
| --- | --- | --- |
| Achieved occupancy | `sm__warps_active.avg.pct_of_peak_sustained_active` | 8.33-10.89%, mean 9.24% |
| Divergence | `smsp__thread_inst_executed_per_inst_executed.ratio` | 32.00 on every launch |
| Local traffic | `l1tex__t_sectors_pipe_lsu_mem_local_op_{ld,st}.sum` | **0** across all 12 launches |
| Global traffic | `l1tex__t_sectors_pipe_lsu_mem_global_op_{ld,st}.sum` | 64-3,664 ld / 72-3,904 st sectors |
| Shared traffic | `l1tex__data_pipe_lsu_wavefronts_mem_shared.sum` | 8-24 wavefronts |

### All three static leads are refuted, not confirmed

1. **The 40-byte stack frames cost nothing measurable.** Local-memory sectors
   are exactly zero on every launch, including the four kernels ptxas reported
   with 40-byte stack frames and `LDL.64`/`STL.64` instructions. Those
   instructions exist in the SASS but generate no measured local traffic —
   consistent with the addresses resolving in L1 without reaching the local
   memory path. Lead 1 is closed: there is no stack traffic to remove.
2. **Occupancy is not register-limited.** `launch__occupancy_limit_registers`,
   `_blocks`, and `_shared_mem` all report 16 while `_warps` reports 12, so
   registers are not the binding constraint. A register-pressure experiment
   would not move achieved occupancy. Lead 2 is closed as stated.
3. **Lead 3 is the whole story, and it is a grid-size problem.** Every launch is
   256 threads (2 blocks x 128) = 8 warps. An RTX 3090 has 82 SMs x 48 resident
   warps = 3,936 warp slots, so this grid occupies 0.20% of the machine and
   lands on 2 of 82 SMs. Achieved 9.24% is 6.3x below even CR2-5a's 58.33%
   theoretical floor because theoretical occupancy is a per-SM-if-resident
   figure and says nothing about whether the grid is large enough to occupy the
   device.

Divergence at 32.00 is the maximum on a 32-lane warp, i.e. **zero divergence** —
full convergence, not 32x divergence. The one-thread-per-world decomposition is
branch-efficient; it is simply far too small.

### What this redirects

CP-5 should not pursue register pressure or stack elimination. The measured
finding is that the kernels are latency-bound on a nearly-empty device, so the
CP-5 candidate becomes the decomposition itself: more parallelism per world
(so a 256-world batch produces far more than 256 threads) or batching windows to
raise grid size. This also plausibly bears on G-F, since a device this idle at
256 worlds explains why world 1 loses to CPU by 7-36x.

Both facts are measurements, not yet a validated optimization. CP-5 must
re-measure after any change; this section records what the counters show, not a
promise that a larger grid is faster.

### Tracked artifacts and independent reproduction

The counters are now a tracked evidence pair rather than a scratch capture:

- [cuda_resident_cp_resource_evidence_20260810.json](cuda_resident_cp_resource_evidence_20260810.json)
  — the v2 static/topology parent.
- [cuda_resident_cp_counter_evidence_20260810.json](cuda_resident_cp_counter_evidence_20260810.json)
  — the achieved-counter capture, with `attempt.status=available`,
  `collected_launch_count=12`, and
  `cr2_5_disposition=achieved_counter_evidence_complete`.

The counter report hashes its parent, and both files are marked `-text` so the
link survives checkout under `core.autocrlf`.

The capture was taken twice, in separate elevated sessions, with a GPU-lost
driver fault (`nvlddmkm` Event ID 153) and a recovery in between. The second run
reproduced the first independently: occupancy 8.32-11.38% versus 8.33-10.89%,
and identical divergence, local, global, and shared values. Occupancy varies at
the third significant figure because it is a sampled ratio; the memory and
divergence counters are exact and did not move.

All four authority flags remain false in the tracked artifact. Closing a
measurement gate grants no promotion, maintained-support, or tuning authority —
those require the separate recorded decision at CP-9.

## CP-1 landed: the CUDA surface can no longer rot silently (2026-08-11)

CP-1 closes the zero-coverage exposure with two complementary halves, because
neither one alone is sufficient.

### The compile lane

[ci-cuda-compile.yml](../../../.github/workflows/ci-cuda-compile.yml) configures
with `EF_ENABLE_CUDA_EXPERIMENTS=ON` and `CMAKE_CUDA_ARCHITECTURES=86`, then
builds the two device surfaces and links all three CUDA test targets plus all
four CUDA-only probes. It is path-scoped to CUDA sources, the CUDA CMake wiring,
and the workflow itself, so it runs when it has something to say.

The toolkit comes from the Ubuntu archive (`nvidia-cuda-toolkit`) rather than a
third-party action, so the lane adds no new supply-chain dependency. Its nvcc
predates the runner image's default gcc, so `g++-12` is installed and pinned as
`CMAKE_CUDA_HOST_COMPILER`; without that pin nvcc rejects the host toolchain.

Three limits are stated in the workflow itself so a green check is not
over-read:

- **It runs nothing.** Hosted runners have no NVIDIA device, so the
  `cuda_resident_*` suites would fail at `cudaGetDeviceCount`. Runtime
  validation stays a local GPU-host step recorded per iteration.
- **It is not the evidence toolchain.** The tracked evidence was captured with
  CUDA 13.0 on an RTX 3090; the lane uses whatever nvcc the image ships. It is a
  rot detector, not an evidence host.
- **It cannot detect a probe that compiles but does nothing.** That is the second
  half.

### The toolkit-free gates

[test_cuda_surface_wiring.py](../../../tests/architecture/build_system/test_cuda_surface_wiring.py)
adds 14 gates that need no CUDA toolkit and no GPU, registered in
`ci_smoke_suite.json` so they run on every PR rather than only when CUDA paths
change. They cover two things a CUDA-off build cannot:

1. **Source wiring** (7 gates): the `.cu` files on disk and the `.cu` files
   CMake compiles are the same set; the resident backend's 8-file device surface
   is pinned because the tracked counter evidence measures kernels from exactly
   those files; the device sources stay behind the CUDA guard; and the helper and
   resident surfaces stay separate. Two negative cases pin the orphan and
   missing-file checks.
2. **Probe executability** (7 gates): each of the four CUDA-only probe targets
   exists, names only sources that exist, names the backend it links, and has
   exactly one entry point with a success path.

The second group exists because of a specific regression this program already
paid for. CP-4a retired the v1 capture probe by replacing its 335-line body with
a stub that printed the retirement reason and returned `EXIT_FAILURE`
(`44e2b64e`), while leaving the CMake target intact — still compiling the replay
harness, still linking `ef_cuda_resident_backend` and `nlohmann_json`, which the
stub referenced not at all. That state compiles and links cleanly. A compile lane
would have reported green on a probe that could no longer produce evidence, and
CP-4c then had to pay for the missing tool. The gate encodes the two structural
signatures of that state: a vestigial backend link, and an entry point with no
success return.

Both halves were verified load-bearing by mutation, not by assertion that they
should work:

| Mutation | Result |
| --- | --- |
| Drop `cuda_world_store_cuda_window.cu` from its CMake list | 3 wiring gates red |
| Restore the real `44e2b64e` stub into the working tree | probe gate red on both counts, naming the vestigial link and the missing success path |
| Remove only the success return, keeping the backend construction | entry-point check red, vestigial-link check correctly stays green |
| Split entry point from a sibling session TU (the real probe shape) | stays green — the check accepts the backend being named by a sibling source |

Every mutation was reverted and the tree re-verified clean before landing.

### CP-1 local CUDA-on result

Recorded per the program's own requirement that each iteration state a real
CUDA-on build result rather than deferring to CI:

- Nine targets configured and built CUDA-on: both device libraries, three test
  targets, four probes. Exit 0.
- `ctest -R "cuda_resident_lifecycle|cuda_resident_replay|cuda_resident_full_window"`:
  3/3 passed (1.49s, 0.85s, 0.81s) on the RTX 3090 host recorded above.

CP-1's exit gate is met on both clauses: a compile regression cannot land
silently, and a retired-to-stub probe is detected — the latter by the gate that
the retirement itself proved was missing.

## Constraints

- CPU remains the maintained world-step truth for the entire program until CP-9
  says otherwise.
- No public ABI, Python name, CLI flag, or config-key change without a
  compatibility shell and migration note.
- Evidence artifacts stay content-addressed with `utf8_lf` canonicalization and
  `-text` gitattributes, per the CR2 precedent.
- Counter artifacts must record elevation; no theoretical value may be inserted
  into an achieved-counter field.
- No registry or driver-policy modification.
- Timing evidence collected on this single host is host-specific. It cannot
  become a maintained performance contract without a documented second host or
  an explicit single-host acceptance.
- Independent review may not edit the implementation under review.

## Rollback boundary

`main` is untouched by this program. All work lives on
`codex/cuda-resident-promotion-program` in an ignored worktree. Abandoning the
program requires deleting the branch and worktree; no maintained rollback is
needed.
