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

RB10 applied six frozen gates to RB9 and recorded six failures. CR2 repaired
several of them structurally but closed on two remaining absences. Consolidating
both closures, the live blocker set at this program's start is:

| # | Gate | Predecessor status | Nature |
| --- | --- | --- | --- |
| G-A | Full facade/window advance measured through the public SPI | CUDA used private `inject -> publish_stage -> advance`; `publish_stage` absent from `IWorldBatchBackend` | Architectural |
| G-B | CPU and CUDA invocation surfaces equivalent | `backend_spi_world_batch` vs `backend_private_phase_sequence` | Architectural |
| G-C | Learner-equivalent consumption measured | Device consumer was diagnostics smoke with hidden host readback; CR2-3 added a lease boundary | Partially repaired |
| G-D | Achieved hardware counters complete | `ERR_NVGPUCTRPERM` on two separate attempts (RB9, CR2-5b) | Host permission |
| G-E | Selected-slice parity out of quarantine | CR2-4b released 12 fields | **Repaired by CR2** |
| G-F | Small-batch default does not regress | World 1 regresses 7-36x; CR2-6b advisory routes world 1 to CPU | Open (needs either a fix or a documented selection rule) |

G-B is the root gate. While the two lanes call different surfaces, every timing
ratio in RB9 and CR2-6b compares non-equivalent paths, so no performance number
can support promotion regardless of how favorable it looks.

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
| Nsight Compute | 2025.3.1 |
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
exercise a facade-equivalent window, a learner consumer, or achieved counters —
those are exactly gates G-A/G-B, G-C, and G-D below.

## Iteration plan

Iterations are `CP-<n>`, one coherent commit each, following the
repository-consolidation protocol (analyze / implement / validate / register /
commit). Critical phases get one independent review before landing.

| Iteration | Scope | Exit gate |
| --- | --- | --- |
| CP-0 | This freeze; verify CUDA-on build still compiles on the baseline; record host/toolchain identity | Program frozen; CUDA-on build result recorded honestly |
| CP-1 | CUDA-on compile lane so the 6,229-line surface stops rotting: a CI job (or, if no GPU runner is available, a documented local checkpoint plus an architecture test asserting the CUDA source set stays wired) | Compile regression cannot land silently |
| CP-2 | Split `EF_ENABLE_CUDA_EXPERIMENTS` into a helper-surface flag and a resident-backend flag, so the two semantically different surfaces are independently selectable | Enabling one no longer forces the other |
| CP-3 | **G-B/G-A root fix**: bring the resident backend's window advance onto the public SPI. Either lift a stage-publish concept into `IWorldBatchBackend` for all backends, or make the CUDA lane reach the same observable state through the existing `inject/evaluate/advance/export` sequence. CPU lane must not regress | Both lanes measured through one identical call surface |
| CP-4 | Re-measure the 1/4/16/64/256 matrix on the now-equivalent surface, order-balanced, two campaigns | Timing evidence is a like-for-like comparison |
| CP-5 | Achieved counters under elevation: occupancy, divergence, global/local/shared traffic for all 10 kernels | G-D closed with real counters, or a recorded second external blocker |
| CP-6 | Kernel-level optimization driven by CP-5 findings. Known candidates below | Measured improvement against the CP-4 baseline |
| CP-7 | G-C: learner-equivalent consumption through the CR2-3 lease, without hidden host validation readback | A real consumer, not diagnostics smoke |
| CP-8 | G-F disposition: either fix small-batch overhead or freeze an explicit selection rule with world-count thresholds | World 1 no longer a silent regression |
| CP-9 | Promotion decision: all gates + independent review, or a recorded hold with the exact missing authority | Explicit, evidence-backed verdict |

CP-1 and CP-2 are independent of the rest and can land in any order. CP-3 gates
CP-4; CP-5 gates CP-6. CP-9 requires CP-3 through CP-8.

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

Theoretical occupancy from CR2-5a must not be substituted for achieved
occupancy in any CP-6 justification.

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
