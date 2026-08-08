# CUDA-resident Runtime Program 2 closure

- Closure ID: `cr2_7.closed_without_promotion.cuda_resident.20260805`
- Date: `2026-08-05`
- Machine-readable record: [cuda_resident_cr2_closure_20260805.json](cuda_resident_cr2_closure_20260805.json)
- Chinese companion: [cuda_resident_cr2_closure_20260805.zh.md](cuda_resident_cr2_closure_20260805.zh.md)
- Program: [cuda_resident_runtime_program_2_20260731.md](cuda_resident_runtime_program_2_20260731.md)
- Pre-closure head: `356bcd56a61e40f1327d16b6a2dda335d7fdd553`

## Decision

CR2-7 closes Runtime Program 2 without promotion. The CUDA-resident
implementation remains a retained, unmaintained research second backend. It is
not selected by RuntimeFacade, does not alter the maintained CPU default, and
does not acquire public support, ABI, tuning, merge, or push authority.

This is not a conclusion that the backend failed. CR2 completed the structural
split, common-SPI full-window path, device-consumer boundary, selected-slice
parity, static resource/topology capture, and production-shaped small-batch
matrix. Closure follows mechanically because two independent promotion
conditions remain absent:

1. achieved occupancy, divergence, and global/local/shared traffic are still
   unavailable after the real Nsight Compute attempt returned
   `ERR_NVGPUCTRPERM`; and
2. no explicit promotion authorization or integration plan was recorded.

Neither condition may be replaced by an inference from theoretical occupancy,
zero-valued counters, or the timing matrix.

## Retained evidence

The closure binds the exact CR2-6b matrix summary and fresh parity output, plus
canonical `utf8_lf` descriptors for the earlier CR2-5a/5b evidence. The matrix
contains two order-balanced campaigns and keeps its host-specific limitations.
Its advisory remains:

- world 1 common modes: `flecs_cpu_reference`;
- world 4 without host export: `cuda_resident`;
- world 4 with host export: conservative CPU default, with CUDA only as a
  median-throughput opt-in because rollout p95 reverses between campaigns;
- world 16/64/256 common modes: `cuda_resident`;
- device-consumer modes: CUDA required, without a comparative CPU claim; and
- unmeasured world counts: unclassified, with no extrapolation.

This advisory is retained research evidence, not a runtime selector or a
maintained performance contract.

## Repository and maintained boundary

At the final pre-commit topology snapshot:

- the original maintained baseline and the candidate/main merge base were
  `395e02b7dfeaa87baedb2611ec503d14ab137ce3`;
- maintained `main` had independently advanced through PR #21 to
  `a4365cf673cb7995413168cb1e1439c183566268`;
- main and the candidate had 4 and 24 unique commits respectively, including 12
  linear CR2 commits after the retained RB11 parent closure;
- no local remote-tracking ref contained the pre-closure head, without fetching;
- the candidate branch and worktree were retained; and
- no merge, push, deletion, cleanup, profiler-permission change, or maintained
  rollback was performed.

The observed main, remote-ref, branch, and worktree values are a dated
pre-commit snapshot, not permanent pins for future architecture tests. Their
live comparison is an explicit acceptance check; the durable guard verifies the
frozen record, immutable commit graph, evidence, and maintained code boundary.

The maintained CPU backend remains the default. `compiled_experimental_backend`,
`supports_resident_state`, and `supports_device_observation_view` remain false.
CR2-7 changes no runtime, contract, probe, CMake, kernel, launch, or C++ test.
The existing 143-line RB11 architecture guard is narrowed from mutable live refs
to its frozen snapshot and immutable `BASELINE → RB10` commit graph.

## Size and artifact assessment

CR2-7 adds a 546-line validator and a 232-line architecture guard; the adjusted
RB11 guard is 143 lines. All are below the 700-line soft target and 1000-line
hard ceiling. Its closure JSON and two documentation files are small artifacts.

The four retained CR2-6b raw reports total 597,239 bytes; the largest is 194,834
bytes. They exceed 1000 formatted JSON lines but are evidence artifacts, not
code modules. Each remains below the 512 KiB artifact soft cap and 1 MiB hard
cap, and retaining the raw samples is necessary to independently rederive both
order-balanced campaigns. CR2-7 adds no new large raw artifact.

## Validation and future work

Run the durable closure validator and the separate pre-commit live check with:

```powershell
python tools/diagnostics/cuda_resident_cr2_closure.py
python tools/diagnostics/cuda_resident_cr2_closure.py --check-live-snapshot
```

The validator checks exact JSON types, hashes, prior-evidence canonicalization,
the linear commit chain, maintained flags, and the evidence-only write boundary.
The explicit flag additionally compares the variable local refs/worktree with
the dated snapshot. Architecture tests deliberately do not pin future `main` or
worktree state; they reject gate, type, scope, hash, link, immutable-graph, and
size drift. Existing CR2 focused and CUDA-on/off runtime suites remain required
for the final staged snapshot.

The exact staged CR2-7 snapshot must receive a new independent `FINAL APPROVE`
before one closure commit is allowed. That approval does not authorize merge,
push, promotion, tuning, host permission changes, or destructive cleanup.

Future CUDA-resident work requires a new explicit program and user-authorized
scope. Such a program may retry achieved counters after host permission becomes
available or propose integration, but this closed program grants neither action
implicitly.
