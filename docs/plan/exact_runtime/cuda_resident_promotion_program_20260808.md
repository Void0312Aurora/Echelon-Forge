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
| CP-1 | CUDA-on compile lane so the 6,229-line surface stops rotting: a CI job (or, if no GPU runner is available, a documented local checkpoint plus an architecture test asserting the CUDA source set stays wired). Must also assert each CUDA probe still *executes*, not merely links -- the retired resource probe compiles cleanly as a stub | Compile regression cannot land silently; a retired-to-stub probe is detected |
| CP-2 | Split `EF_ENABLE_CUDA_EXPERIMENTS` into a helper-surface flag and a resident-backend flag, so the two semantically different surfaces are independently selectable | Enabling one no longer forces the other |
| CP-3 | Retire the private-sequence residue that made RB10's G-A/G-B verdicts possible: demote or remove the public `publish_stage`/`partial_sync_commit` from `CudaResidentBackend` now that only tests and the superseded RB9 probe call them, and add a gate asserting the resident backend exposes no non-SPI window-advance entry point | No caller can advance a window off the SPI; the equivalence claim becomes structurally enforced rather than incidental |
| CP-4 | **G-D: achieved counters under elevation** — occupancy, divergence, global/local/shared traffic for all 10 kernels. This is the one hard blocker and the highest-value iteration | G-D closed with real counters, or a recorded second external blocker |
| CP-5 | Kernel-level optimization driven by CP-4 findings. Known candidates below | Measured improvement against the CR2-6b baseline |
| CP-6 | G-C: learner-equivalent consumption through the CR2-3 lease, without hidden host validation readback | A real consumer, not diagnostics smoke |
| CP-7 | G-F disposition: either fix small-batch overhead or freeze an explicit selection rule with world-count thresholds | World 1 no longer a silent regression |
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
