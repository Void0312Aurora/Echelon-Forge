# ADR: resolved experiment input lock and comparability

Language:
- English canonical: `resolved_experiment_input_lock_adr.md`
- Chinese companion: [resolved_experiment_input_lock_adr.zh.md](resolved_experiment_input_lock_adr.zh.md)

Document kind: `standard`
Lifecycle: `proposed`
Canonical: `docs/architecture/standards/resolved_experiment_input_lock_adr.md`
Owner: `architecture/experiment-contracts`
Last verified: `2026-10-10`

**Status:** proposed static/qualification projection; native composition and
RunReceipt authorities remain canonical.

## Decision

Add an opt-in `ResolvedExperiment` projection that references, rather than
recomputes or replaces, existing native composition identities, scheduler
topology evidence, RunReceipt and ledger records. It separates experiment
intent, resolved input closure, native admitted composition, run receipt and
comparison profile.

The input lock records effective scenario/content/platform/force/mechanism/
policy references, schema versions, evaluation protocol and effective seed
policy. It distinguishes physics-affecting inputs from report metadata and
labels values as claimed, admitted, observed or referenced. A shared lock may
be used by multiple run receipts; a logical experiment may resolve to a new
lock when dependencies change.

## Canonicalization and comparability

Canonical identity uses logical IDs, versions, normalized JSON and dependency
closure; key order and import traversal do not change semantics. Missing or
stale resources, unsupported schemas and native identity mismatches prevent a
full-comparability claim. Hash equality alone does not establish calibration,
scientific validity or cross-machine numerical determinism.

Comparison profiles must state allowed axes such as policy-only or
mechanism-only changes. A partially failed or state-uncertain batch is
segregated from successful samples using the failure-domain and RunReceipt
owners. Declarative composition identity is not a substitute for realized
Flecs scheduler topology; the experiment layer only references the existing
topology evidence.

## Proof and non-goals

The first proof is non-running and covers one existing Air experiment, key
order/import reorder, a truth-affecting change, effective seeds, a stale
resource, native identity mismatch, a policy-only comparison and a failed-run
segregation. Existing `Experiment`, report envelopes, matrix output and
RunReceipt ABI remain unchanged by default. No second ledger, replay engine,
composition authority or telemetry bus is introduced.
