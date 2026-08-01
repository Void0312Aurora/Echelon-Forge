# CR2-3 Device Consumer Lease Acceptance Candidate

Date: 2026-08-01
Branch: `codex/cuda-resident-runtime-program-2`
Parent: `607c1f33`

## Technical verdict

The bounded CR2-3 engineering gates pass. The CUDA-resident backend now has an
owned, learner-facing device observation lease and a real device consumer smoke
kernel. Consumer validation D2H is outside every recorded sample timer. This is
not a learner-update implementation, a performance promotion, or public support
release.

## Accepted boundary

- Lease: D2D observation values and ids, ready event, device/default-stream
  identity, element-based shape/strides/dtype, and allocation/reset/window/
  source epoch.
- Receipt: independent output/event ownership that retains the input lease.
- Measured work: acquire, submit, and explicit event await; zero incremental
  consumer-validation D2H.
- Diagnostic work: exactly two D2H copies after the sample timer; rollout
  receipts are deferred and included in requested-memory peak accounting.
- Release: in-flight RAII may wait for its event, so release is deferred outside
  every recorded sample timer.
- Failure: stable codes plus one-shot tests for allocation, launch, event,
  wait, materialization, stale epoch, device, stream, and layout errors.
- Lifetime: leases survive reset/backend destruction; receipts survive
  consumer destruction; repeated submit/await is supported.

## Evidence

- CUDA Release: 14/14 cases, 599/599 assertions on RTX 3090.
- CUDA-off Release: 14/14 cases, 91/91 assertions.
- RB9 smoke, two worlds: 4/4 rows available; device rows report consumer D2H
  0, diagnostic D2H 2, event wait 1, allocation-sync risk true, deferred
  receipt count 2, and peak bytes including both owners.
- Focused architecture: 25/25 passed; new guard is Ruff formatted and clean.
- Size: every CR2-3 implementation/test module is below its 700-line soft
  target (contract 209, consumer 246/49, host-internal/lease 33/66,
  observation CUDA 441, C++ test 292, architecture guard 197, RB9
  probe/session/header 597/304/46, store 661, backend 636; headers below 600);
  no exception was added.

## Held boundaries

`IWorldBatchBackend`, RuntimeCapabilities, admission, support flags, and
RuntimeFacade selection are unchanged. Historical RB9 evidence is untouched.
`cudaMalloc` may implicitly synchronize and remains an explicit CR2-5 risk;
in-flight release may also wait for completion and is kept outside the measured path.
Full learner update, parity release, hardware counters, tuning, merge, push,
and promotion remain unaccepted.

The candidate still requires final independent staged-write-set approval before
its single CR2-3 commit.
