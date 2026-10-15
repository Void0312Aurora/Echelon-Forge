# ADR: resolved experiment input lock and comparability

Language:
- English canonical: `resolved_experiment_input_lock_adr.md`
- Chinese companion: [resolved_experiment_input_lock_adr.zh.md](resolved_experiment_input_lock_adr.zh.md)

Document kind: `standard`
Lifecycle: `proposed`
Canonical: `docs/architecture/standards/resolved_experiment_input_lock_adr.md`
Owner: `architecture/experiment-contracts`
Last verified: `2026-10-12`

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

The lifecycle has two evidence moments. The pre-run lock freezes intended
inputs and dependency closure; it cannot contain observed completion or mint a
RunReceipt. A post-run evidence join references the native admitted composition,
realized scheduler identity and RunReceipt/status emitted by their owners. The
experiment layer never recomputes or replaces those native hashes.

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

The comparison result follows this matrix:

| Case | Result | Reason |
| --- | --- | --- |
| Equal resolved lock, native identities and complete successful receipt | `comparable` | All truth-affecting inputs and realized execution evidence agree |
| Explicit policy-only or mechanism-only change allowed by the profile, with otherwise equal evidence | `conditionally comparable` | The changed axis is declared and must be analyzed separately |
| Hidden content, native manifest, executable graph or realized topology difference | `incomparable` | An undeclared truth-affecting difference invalidates the comparison |
| Effective seed set differs | `incomparable` unless the profile explicitly admits seed variation | Seed identity changes the sampled experiment |
| Partial, failed or state-unknown WorldBatch outcome | `incomparable` to a completed successful sample | #251/#210 outcome authority does not establish synchronized success |

## Proof and non-goals

The first proof is non-running and covers one existing Air experiment, key
order/import reorder, a truth-affecting change, effective seeds, a stale
resource, native identity mismatch, a policy-only comparison and a failed-run
segregation. It proves static lock construction only; it does not prove runtime
reproducibility, native receipt equivalence or durable host publication.
Existing `Experiment`, report envelopes, matrix output and
RunReceipt ABI remain unchanged by default. No second ledger, replay engine,
composition authority or telemetry bus is introduced.

## Option comparison and implementation checkpoint

| Option | Disposition in this proposed ADR |
| --- | --- |
| Use native composition evidence unchanged | does not close Experiment/scenario/policy/content references |
| Immutable opt-in projection using existing compiler and receipt | proposed route; preserves independent input and observed runtime identities |
| New experiment runtime/receipt/ledger | rejected; duplicates native execution and durable evidence owners |

Input identity is deeply immutable and independent of subsequent native evidence. Scenario dependencies are projected from ScenarioCompiler rather than recompiled; the compiled semantic snapshot is checked in addition to dependency mtimes. Native topology is distinct from executable-graph identity. Comparability requires bound validated RunReceipt evidence and complete outcomes. The evidence join preserves the host receipt identity, backend system-graph digest, native-validator evidence digest and durable acknowledgement; when a native adapter supplies the same binding, mismatches fail closed. A file-bound helper can consume a host-published canonical RunReceipt and reject noncanonical bytes before invoking the existing validator. Receipt vectors are synthetic qualification fixtures; durable host publication and production wiring remain open.

See [qualification evidence and remaining gates](../work/issues/rfc_qualified_composition_implementation.md). Lifecycle remains proposed; this checkpoint does not establish owner approval or production admission.
