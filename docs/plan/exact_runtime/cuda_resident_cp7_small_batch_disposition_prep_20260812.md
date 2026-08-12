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
