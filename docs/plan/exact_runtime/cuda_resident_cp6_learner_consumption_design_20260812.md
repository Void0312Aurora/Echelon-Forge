# CP-6 Learner-Equivalent Device Consumption -- Design Draft

Language:
- English canonical: `cuda_resident_cp6_learner_consumption_design_20260812.md`
- Chinese companion: [cuda_resident_cp6_learner_consumption_design_20260812.zh.md](cuda_resident_cp6_learner_consumption_design_20260812.zh.md)

Document kind: `plan`
Lifecycle: `draft`
Canonical: `docs/plan/exact_runtime/cuda_resident_cp6_learner_consumption_design_20260812.md`
Owner: `exact-runtime / CUDA-resident promotion workline`
Last verified: `2026-08-12`

- Program: [CP promotion program](cuda_resident_promotion_program_20260808.md),
  iteration CP-6, gate G-C
- Prepared by: independent reviewer of the in-flight CP-5 fusion change
  (reviewer edited no implementation files, per program protocol)
- Authority boundary: this draft proposes; it does not authorize. CP-6 work
  starts only when the program owner freezes this scope after CP-5 closes.

## Why this design is written against the long horizon

The program's end state -- the reason a resident backend is worth promoting at
all -- is a rollout loop whose observations never round-trip through the host:
the learner (in this repository, a PyTorch policy behind SB3) consumes device
observations in place and the CPU stops being a copy relay. The promotion
program cannot ship that integration, because its constraints forbid public
ABI and Python surface changes without compatibility shells. CP-6 therefore
closes G-C with a **learner-equivalent** consumer measured at the CR2-3 lease,
and every interface decision below is chosen so the later real-learner
integration is additive, not corrective. Where a cheaper choice would work for
CP-6 but would have to be undone for the torch integration, this draft rejects
it and says why.

## Scope of "learner-equivalent" (correction from independent review)

The lease exposes the resident backend's *fixture* observation contract: the
fifteen fixed-air fields. The production training stack does not consume this
surface today -- the maintained policies take dictionary observations across
instrument/contact/warning/mission domains with per-domain preprocessing
(`python/models/transformer.py`). CP-6 therefore closes G-C for the surface
the resident backend actually owns: a consumer that reads every element of
the lease tensor and performs representative pre-inference work on device is
learner-equivalent *for the resident fixture contract*, and the gate closure
must say so explicitly. Making the production dictionary-observation stack
device-resident is a separate, larger surface recorded under residuals; this
iteration neither delivers nor claims it.

## Verified current facts (2026-08-12, worktree with CP-5 in flight)

Re-verify these if CP-5 lands in a different shape than reviewed.

1. The lease payload is already the tensor a policy forward over this fixture
   surface wants. `pack_device_observation_kernel`
   (`src/runtime/facade/internal/cuda_resident/cuda_world_store_cuda_observation.cu`)
   transposes the simulation's field-major SoA into a world-major,
   C-contiguous `[world_count, 15]` buffer and narrows `double` to finite-clipped
   `float`. Layout and dtype work that a learner adapter would otherwise do is
   already done at pack time.
2. `device_consumer::TensorDescriptor`
   (`src/runtime/contracts/cuda_resident_device_consumer_contract.h`) declares
   element-based `shape`/`strides`/`dtype`. Element-unit strides map 1:1 to a
   future DLPack export; `__cuda_array_interface__` needs only a mechanical
   byte multiplication. No descriptor redesign is required later.
3. The current consumer is a smoke kernel:
   `device_observation_consumer_smoke_kernel` reads one of the fifteen values
   per world and copies ids. It proves the boundary, not consumption. That is
   exactly the residual G-C names: CR2-7 recorded the gate true for the
   **boundary**, not for learner-equivalent consumption.
4. CR2-3 measured-path rules are in force and stay binding: consumer-path
   incremental D2H is zero; diagnostic materialization performs exactly two
   D2H copies outside all sample timers; leases carry
   allocation/reset/window/source epochs; receipts outlive the consumer.

## CP-6 scope

One iteration, one coherent commit, per program protocol.

1. **Learner-equivalent consumer kernel.** Replaces the smoke kernel as the
   measured consumer (the smoke kernel may remain for lifecycle tests). It
   must:
   - read every element of the lease values tensor, not a probe element;
   - apply the pinned per-field observation normalization (the preprocessing a
     policy forward performs on raw observations);
   - write a device-resident policy-input buffer, world-major
     `[world_count, feature_count]` `float`, same layout family as the lease
     payload;
   - pass through ids and honor the epoch checks unchanged.
2. **Single-owner normalization contract.** Normalization constants live in a
   new contract header (`constexpr`, C++ contract as the only owner). Python
   or diagnostics that need them derive from the contract the same way the
   kernel catalog is derived since CP-4b. No second hard-coded copy.
3. **Measurement through the existing matrix lane.** The CR2 matrix session
   gains a learner-equivalent consumer mode (mode ids frozen at CP-6 start),
   measured identically to the current `*_device_consumer` modes so rows stay
   comparable to CR2-6b and to the post-CP-5 campaigns.
4. **Architecture gates**, toolchain-free where possible:
   - the measured consumer reads the full tensor (structurally pinned, so a
     single-element smoke can never again satisfy G-C);
   - zero hidden host readback on the measured path (pin the CR2-3 rule
     against the new kernel);
   - policy-input layout/dtype pinned against the contract;
   - normalization constants have exactly one owner.
5. **CUDA-on validation.** Consumer kernel CPU-reference parity for the
   normalization math, lifecycle/replay suites green, and a recorded local
   RTX 3090 run, per the program's per-iteration requirement.

## Forward-compatibility decisions

| Decision | CP-6 choice | What it buys the future |
| --- | --- | --- |
| Policy-input layout | world-major `[world, feature]` `float`, C-contiguous | A later DLPack/`__cuda_array_interface__` export wraps the buffer zero-transform; `torch.from_dlpack` yields the policy input directly. |
| Stride semantics | keep element-based `TensorDescriptor` | DLPack strides are element-based; no descriptor migration. |
| Synchronization | keep the event-based ordering: the lease pins `producer_stream = 0` (`legacy_default_stream` per the contract) and the consumer orders itself with `cudaStreamWaitEvent` on the ready event, never a device-wide sync | The ready event is what a torch export waits on. The legacy-default-stream identity is a current pin, not the end state: the export design must decide the stream-interop mapping explicitly. |
| Lifetime/safety | epochs + shared-owner lease/receipt semantics unchanged | A future Python handle inherits staleness detection instead of inventing it. |
| Exposure | consumer stays a private seam; no `RuntimeFacade` or binding change | Public exposure is a promotion-scope decision (CP-9 or later), not a measurement-iteration side effect. |
| Normalization ownership | contract header, single owner | The torch-side preprocessing later reads the same constants; CPU/GPU/learner can never drift apart silently. |

## Non-goals

- No learner update and no training-loop integration: CR2-3's closure language
  ("this does not mean a learner update is implemented") continues to hold;
  G-C asks for measured learner-equivalent consumption, not training.
- No public ABI, Python name, CLI flag, or config key changes.
- No performance claims beyond what the matrix rows measure, and no promotion,
  support-flag, or tuning authority. All four authorization flags stay false.

## Prerequisites and sequencing

1. **CP-5 closes first.** The fusion commit, its post-change matrix campaign,
   and the v3 static recapture are in flight in this worktree as of this
   draft. CP-6 starts from that landed state.
2. **Counter-chain version awareness (CP-5/CP-8 lane, recorded here so it is
   not lost).** The independent review of CP-5 found
   `tools/diagnostics/cuda_resident_cr2_counter_evidence.py` still pinned to
   the pre-fusion world: `PARENT_PROFILES` accepts only the v1/v2 profile ids,
   `REQUIRED_LAUNCH_COUNT = 12`, and the Nsight Compute invocation hard-codes
   `--launch-count=12`. A v3 counter capture (7 launches, 5 kernels) would be
   rejected by our own collector -- the same failure class CP-4c documented.
   The forward-serving fix is derivation, not another pin: take parent
   profiles, launch counts, and kernel identities from the contract via the
   existing `kernel_catalog(version)` / `launch_sequence(version)` accessors.
   A later generation then never re-pins launch counts or command budgets; it
   still registers its identity in the schema module and its measured-unit
   map in the parser, once each. Do not request an elevated capture session
   before this lands.
3. CP-7 (small-batch disposition) stays after CP-5 evidence: launch-chain
   reduction may already move the world-1 picture, so the fix-vs-threshold
   decision should read the post-fusion matrix first.

## Acceptance evidence this iteration must produce

- Matrix campaign JSON rows for the learner-equivalent consumer modes,
  comparable against CR2-6b and the post-CP-5 baseline.
- C++ consumer tests including normalization CPU-reference parity; CUDA-on
  lifecycle/replay/full-window suites green on the recorded host.
- New architecture gates green in `ci_smoke_suite.json`, plus the usual
  `git diff --check` and bilingual audit for the documentation pair.
- An iteration record in the program document, including any deviation from
  this draft and why.

## Residuals deliberately left open

- The DLPack/`__cuda_array_interface__` export itself, and any torch-side
  consumer, remain post-promotion work; this draft only keeps their path
  unobstructed.
- The production dictionary-observation stack (instrument/contact/warning/
  mission domains with per-domain preprocessing) has no device-resident path
  and is not covered by CP-6's gate closure; giving it one is its own program
  scope after the fixture surface proves the pattern.
- Whether the learner-equivalent consumer should also feed the leader/world
  batch cooperative lane is out of scope until the air-domain line proves the
  pattern.
- Registration of this draft into the directory README reading order is
  deferred to the CP-6 freeze commit, to keep this draft zero-conflict with
  the in-flight CP-5 session.
