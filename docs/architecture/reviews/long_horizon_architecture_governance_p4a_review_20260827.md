# Long-Horizon Architecture Governance P4-A Independent Review

Document kind: `review`
Lifecycle: `accepted`
Canonical: `docs/architecture/reviews/long_horizon_architecture_governance_p4a_review_20260827.md`
Owner: `cross-domain architecture`
Last verified: `2026-08-27`

Status: `pass`

Review target: `codex/long-horizon-governance-architecture` in the isolated
worktree created from `origin/main` at
`82d5b6e893c442950e334eb3e9ec92f8174eeb35`.

Reviewer: independent `gpt-5.6-sol`, reasoning `max`, after the P4-A repair
round. The reviewer was instructed not to reduce the long-horizon target to
short-term cleanup.

## Review Scope

This review covers the P4-A dark/shadow host lifecycle candidate only:

- one active-slot compare-and-swap publication primitive with monotonic
  publication tickets for initial, replacement, recovery and unpublish paths;
- host-minted boot/object identities, candidate handles, incarnation fences,
  episode capabilities and cross-host resource-identity exclusion;
- bounded candidate lifecycle deadlines, cooperative cancellation, quarantine,
  reclamation and orphan ownership;
- lease settlement and terminal-result admission linearized under the host
  mutex, including duplicate-result rejection;
- terminal shutdown, active-fault drain, quiesce/fault timeout CAS-loss retry,
  multiple-quarantine retention, and reentrant fault-injector behavior;
- CMake target/link/install isolation and native/Python executable evidence.

It does not qualify P4-B state-transfer/episode semantics, P4-C immutable
candidate integration, production publication, P5-B durable production
ledger/RunReceipt, P5-C packaging, or P5-D caller cutover.

## Repair Verification

The prior independent repair review returned three High and one Medium finding.
The repaired tree closes them as follows:

- a candidate whose lifecycle deadline expires with cancellation unacknowledged
  is converted to `Quarantined`, retained in the quarantine vector, and removed
  from the active candidate reference; the live-truth timeout path settles the
  candidate before fail-stop completion;
- lease release and `validate_result` both take the host mutex, and result
  admission rechecks the token's active state under that same lock; a threaded
  race test exercises the settlement/result boundary;
- the CAS fault injector is invoked only by an explicit helper outside the host
  mutex; a reentrant injector calls `snapshot()` while injecting loss;
- `QuiesceTimeoutUnpublish` and `FaultTimeoutUnpublish` each have injected
  first-loss and successful retry behavior tests, including state restoration,
  publication-ticket preservation and retained resource ownership.

## Evidence

- Fresh Windows AMD64 MSVC/Ninja configure and build in
  `build-long-horizon-p4a-review` completed successfully.
- Native candidate executable: `22/22` test cases and `706/706` assertions
  passed.
- Focused CTest: `runtime_host_candidate` and
  `runtime_host_candidate_boundary`, `2/2` passed.
- Candidate architecture contract: `3 passed`.
- Adjacent authority/ledger composition contracts: `31 passed`, with two
  existing `jsonschema.RefResolver` deprecation warnings.
- Source gate confirms one `state.active.compare_exchange_strong` and no direct
  `state_->active.compare_exchange` bypass; `force_loss` is reached only by the
  mutex-external injector helper.
- `git diff --check` passed; only the repository's existing LF/CRLF conversion
  warning was reported for `CMakeLists.txt`.

## Structural Confirmation

- P4-A exposes only `Dark` and `Shadow` modes and rejects production-authorized
  proofs. It therefore cannot become production truth through a runtime flag.
- Active publication is centralized in one CAS wrapper that increments the
  publication ticket only after successful exchange.
- Quarantined slots are retained as a vector; exceeding the budget fail-stops
  the host without dropping references.
- Resource callbacks and final control destruction occur outside the host mutex.
- Host boot/object nonce and candidate/episode capabilities reject replay,
  stale references and cross-host forgery.

## Residual Boundaries

- P4-B still owns the versioned native episode handshake and the complete
  ECS/RNG/clock/queue/command/Python-mirror/backend-lease/in-flight-request
  state census. The current transfer proofs intentionally remain opaque and
  non-production.
- P4-C still owns the real immutable candidate kernel seam, adapter migration,
  replay/state completeness and shadow parity.
- P5-B still owns production durable pre-mutation journaling, crash atomicity,
  complete `RunReceipt`, authenticity/attestation and restore qualification.
- P5-C/P5-D still own facade-only packaging, supported-row qualification,
  production caller activation and the sole production cutover.

## Verdict

`pass`

No unresolved Critical, High or Medium P4-A blocker remains, and no short-term
scope substitution was accepted. This verdict accepts only the bounded
dark/shadow host lifecycle foundation described above; P4-B/P4-C and the
overall long-horizon program remain open.
