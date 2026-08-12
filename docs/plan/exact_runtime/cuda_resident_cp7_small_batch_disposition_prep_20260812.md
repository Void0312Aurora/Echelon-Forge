# CP-7 Small-Batch Disposition -- Preparation Note

Language:
- English canonical: `cuda_resident_cp7_small_batch_disposition_prep_20260812.md`
- Chinese companion: [cuda_resident_cp7_small_batch_disposition_prep_20260812.zh.md](cuda_resident_cp7_small_batch_disposition_prep_20260812.zh.md)

Document kind: `plan`
Lifecycle: `draft`
Canonical: `docs/plan/exact_runtime/cuda_resident_cp7_small_batch_disposition_prep_20260812.md`
Owner: `exact-runtime / CUDA-resident promotion workline`
Last verified: `2026-08-12`

- Program: [CP promotion program](cuda_resident_promotion_program_20260808.md),
  iteration CP-7, gate G-F
- Authority boundary: this note prepares the CP-7 decision; it authorizes no
  implementation. CP-7's exit gate is "world 1 is no longer a silent
  regression", satisfied either by a measured fix or by freezing an explicit
  world-count selection rule.

## What CP-7 decides

CR2-6b measured world 1 on the resident lane at 7-36x slower than CPU and
routed it to CPU as a retained advisory, not a maintained selector. CP-7 must
either repair the small-batch overhead or freeze the routing rule explicitly.
The CP-4 counters showed the device near idle even at 256 worlds, which makes
a fixed per-window host-side cost the leading hypothesis for what world count
fails to amortize at the bottom of the matrix. CP-5 removed the largest
per-window launch chain (six window-commit launches are one); what remains is
the synchronization and copy skeleton inventoried below.

## Verified per-window fixed-cost inventory

Read from the current worktree sources (CP-5 fused state) and cross-checked
against the frozen v2 capture's API counts (5 `cudaDeviceSynchronize`,
13 `cudaMemcpy` = 3 h2d + 7 d2h + 3 d2d) and the performance contract's
modeled base ledger (5 launches, 5 syncs, 3 h2d, 5 d2h of 4 bytes, 3 d2d).

Every stage of the window follows one pattern: launch, `cudaDeviceSynchronize`,
then read one 4-byte `barrier_status` word back to the host and fail closed on
it. Five stages do this per window:

| Stage | Site | Sync | D2H |
| --- | --- | --- | --- |
| Input-injection barrier | `cuda_world_store_cuda_barrier.cu` (launch_apply_barrier) | 1 | 4 B |
| Control preparation | `cuda_world_store_cuda_control_preparation.cu` | 1 | 4 B |
| Stage-publish barrier | `cuda_world_store_cuda_barrier.cu` | 1 | 4 B |
| Fused window-commit body | `cuda_world_store_cuda_window.cu` | 1 | 4 B |
| Window-commit barrier | `cuda_world_store_cuda_barrier.cu` | 1 | 4 B |

The copy skeleton per window:

- 3 full-slot device-to-device copies (`slot_bytes` each; 225,792 bytes at
  256-world capacity): the double-buffer copy-on-write in input injection
  (`cuda_world_store_cuda_storage.cu`), control preparation, and stage
  publish/window commit. These scale with world *capacity*, not with how many
  worlds are active, so world 1 pays the full-capacity copy unless capacity is
  also 1.
- 3 host-to-device control copies (doubles, floats, flags) in
  `inject_flight_controls`; sizes scale with world capacity.
- The device-consumer lane adds the pack kernel, its synchronization, and the
  lease event machinery on top (the contract models it as +2 launches and +1
  synchronization); consumer-validation D2H stays deferred per CR2-3.

What this inventory does not establish: how much wall clock each item costs,
or that the skeleton is the bottleneck at all. The CP-4 counters measured
device-side utilization, not host API latency or kernel durations, so this
note assigns no cost figures and does not claim the skeleton explains the
observed 7-36x. The counters showed the device doing very little work per
launch (near-idle occupancy, zero local traffic, zero divergence), which
makes the host-side skeleton the leading *hypothesis* -- not an established
cause. Confirming or refuting it, and ranking the candidates below by
measured contribution, requires a host-side timeline capture (Nsight Systems
over world-1 windows) as CP-7's first action.

## World-1 timeline attribution (2026-08-12, measured)

The host-side timeline this note demanded as CP-7's first action has been
captured and read. Capture: the review session's `rerun_quiet.ps1` ran the
CUDA matrix probe post-CP-5 (`--worlds 1`, the full frozen production
protocol, all four modes, 3,131 windows) under Nsight Systems 2025.3.2 on the
recorded host, machine verified quiet. The raw artifacts exceed the tracked
1 MiB cap and stay host-retained scratch; their identity is pinned here:
`review_w1_timeline.nsys-rep` 179,503,343 bytes sha256
`c9e461315e5136b645c7549f75b7eb4d9fee0ddc6a52e4c86688c011fb71a79f`, probe
report `review_w1_probe.json` 41,116 bytes sha256
`4814773d5b92b2b2d81fdf08ade8bdeb609a1497a62c732934d782ca75d35288`.

Per-window host API attribution, median call duration times calls per window
(all-mode average). Nsight tracing inflates every call, so the *ranking and
counts* are the claim, not the absolute microseconds:

| Family | Calls/window | Median/call | Median cost/window |
|---|---:|---:|---:|
| `cudaMemcpy` (all directions) | 12.1 | 20.4 us | ~247 us |
| `cudaLaunchKernel` | 6.0 | 26.5 us | ~159 us |
| `cudaMemset` (status words) | 5.05 | 11.3 us | ~57 us |
| `cudaDeviceSynchronize` | 5.0 | 9.3 us | ~47 us |
| `cudaMalloc` + `cudaFree` | 2.0 + 2.0 | 8.2 / 4.7 us | ~26 us |
| event family (record/wait/sync) | 3.0 | - | ~9 us |

Three findings with decision weight:

1. **The inventory missed a per-window allocation.** The device-consumer
   lane performs four `cudaMalloc` and four `cudaFree` per window (lease
   values+ids plus consumer output values+ids; 6,269 allocations across
   3,131 windows, half of them device-consumer mode). The ledger's
   `device_consumer_allocation_may_synchronize = true` already documented
   the risk; the timeline shows it is a real per-window cost. Buffer
   pooling/reuse joins the candidate list below as a low-blast-radius fix.
2. **The device itself puts a floor under world 1 that no host fix can
   remove.** `window_commit_body_kernel` at world 1 runs a single thread
   through the whole serial dependency chain: device time is
   median 65.5 us with p10-p90 inside 0.2 us (n=3,128); barriers and
   control preparation add ~7 us more. The CPU lane completes the entire
   world-1 step in ~18-31 us end to end. Even a zero-overhead host skeleton
   leaves the resident lane ~3-4x slower than CPU at world 1. This is
   measured support for candidate 5 (an explicit frozen selection rule) as
   the world-1 disposition, independent of how far candidates 1-4 go.
3. **The skeleton's shape confirms the hypothesis for small-but-not-one
   batches.** Copies and launches dominate the traced skeleton (~75% of
   ~544 us/window median-based host cost); the fused kernel's device time is
   near-flat in world count (65.5 us at world 1, 104.7 us at 256 in the
   CP-5b capture), so every host microsecond removed converts directly into
   small-batch headroom. Candidate 1 (one sync + merged status array,
   removing ~4 syncs, ~4 status reads, and 4 of 5 memsets) is worth roughly
   119-165 us/window of the traced skeleton; candidate 3 (merge the three
   control copies) roughly two calls' worth; candidate 2's three D2D slot
   copies cost call overhead rather than bandwidth at world 1.

The reviewer rerun campaigns accompanying the capture (four reports, hashes
`e6b9c8b3...7ebe657d`, `d6d06fc4...fde16d1f`, `3ad03853...ffd2a61b`,
`92d334d2...a02a1793`) independently reproduce the CP-5 released-state
digests against the frozen CR2-6b capture (zero mismatches, both lanes).
Their world-64 rows carry contention spikes from the CP-5b clean rebuild
that overlapped them; the tracked CP-5 evidence remains the timing
comparator, and those rerun rows must not enter evidence.

## Fix candidates, ranked by expected win against blast radius

None of these is measured yet; CP-7 must measure any candidate it adopts and
re-measure through CP-8. Any change to the execution graph is a new evidence
generation (v4) -- which the contract-derived counter chain now reduces to a
contract extension plus a one-time identity/unit registration, rather than a
re-pinning of collectors.

1. **One synchronization per window with a consolidated status array.** Give
   each stage its own status word in a small device array; keep every stage
   fail-closed on device, but synchronize and read the whole array once at
   window end (or use mapped pinned memory for the status words). Removes up
   to 4 of 5 syncs and 4 of 5 status readbacks. Blast radius: the fail-closed
   semantics move from "host checks after every stage" to "host checks once
   per window, statuses still per stage"; replay/parity fixtures should be
   unaffected because failed windows already discard the staged slot, but the
   error-attribution tests that expect a stage-precise host failure will need
   their expectation restated per window.
   **LANDED as CP-7b (2026-08-12), in a corrected shape.** Design review
   found the deferred-check form unsound: with two state slots and three
   stages, deferring all checks destroys the rollback point for an
   inject-stage failure (the next stage's staging copy overwrites the only
   clean slot). The landed form folds the stage_publish and window_commit
   barriers into their stage kernels as per-world epilogues instead:
   5 -> 3 launches, syncs, status readbacks, and memsets per window, with
   every stage's host check, flip, retry contract, and fault hook keeping
   its observable behavior. Measured: world-1 warmed e2e p50 down 20-30%,
   all 30 released-state digests bit-identical to frozen CR2-6b; evidence
   generation v4 records the launch absorption. The residual candidate-1
   slice (merging the input-injection stage into the same discipline) and
   mapped-pinned status words stay open for a future iteration if CP-8
   still wants them.
2. **Retire the full-slot copy-on-write chain.** The three per-window
   `slot_bytes` device-to-device copies exist so each stage writes into a
   fresh slot. Candidates: rotate slot pointers and copy only the fields the
   stage does not rewrite, or collapse staging so one copy (or zero, with a
   write-through discipline) serves the window. Largest byte-volume win and
   the only item that also helps large batches; highest blast radius because
   it touches the state-slot model that replay, readback, and the barrier
   contract all assume.
3. **Batch the three control copies into one staging copy.** Pack doubles,
   floats, and flags into one pinned staging buffer and issue one
   host-to-device copy. Small, low risk, bounded win (two copy submissions).
4. **CUDA Graph capture of the whole window.** Subsumes candidate 1 and the
   remaining launch overhead. Largest structural change: a new execution
   graph, a new capture methodology, and the evidence chain's first
   graph-launch generation. Defensible only if candidates 1-3 leave world 1
   still regressing and the program still wants a fix rather than a rule.
5. **Freeze the explicit selection rule instead.** CR2-6b's advisory (route
   world 1 to CPU) becomes a frozen, documented threshold with a measured
   crossover point from the CP-8 matrix. This is the no-fix disposition; it
   satisfies the gate because the regression stops being silent.
   **LANDED as CP-7a (2026-08-12):** `cp7.small_batch_selection_rule.v1` in
   the performance contract freezes world counts below 4 to the CPU
   reference, documentation-grade (architecture gate enforces zero runtime
   consumers), with the crossover value named as a CP-8 review item. The
   world-1 timeline attribution above upgraded this from a routing
   preference to the only honest disposition for world 1: the single-thread
   device floor (~65.5 us) exceeds the whole CPU step (~18-31 us) before any
   host cost is counted. Owner selected rule + candidate 1 as the CP-7
   disposition; candidate 1 remains as CP-7b.

## Sequencing

1. CP-5 must land and the post-fusion matrix (including world 1) must be read
   first: removing five launches per window may already have moved the
   small-batch picture, and the crossover point for candidate 5 comes from
   that data either way. Alongside it, capture a world-1 host-side timeline
   (Nsight Systems) to attribute the fixed cost to the inventoried items
   before choosing a candidate.
2. If a fix is attempted, prefer the smallest set that clears the gate
   (3 before 1 before 2; 4 only with explicit owner scope), one candidate per
   iteration, each with a fresh generation of capture evidence when the graph
   changes.
3. The learner-equivalent consumer (CP-6) measures through the same matrix
   lane; land CP-6 and CP-7 in whichever order the owner freezes, but do not
   interleave their measurements in one campaign.

## Non-goals

- No promotion, support-flag, or tuning authority; all four authorization
  flags stay false.
- No public ABI, Python name, CLI flag, or config key changes.
- No performance claims from this note: the inventory is structural; cost
  attribution awaits the world-1 timeline capture.
