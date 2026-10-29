# ADR: resolved experiment input lock and comparability

Language:
- English canonical: `resolved_experiment_input_lock_adr.md`
- Chinese companion: [resolved_experiment_input_lock_adr.zh.md](resolved_experiment_input_lock_adr.zh.md)

Document kind: `standard`
Lifecycle: `proposed`
Canonical: `docs/architecture/standards/resolved_experiment_input_lock_adr.md`
Owner: `architecture/experiment-contracts`
Last verified: `2026-10-22`

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
| Different or missing host mode | `incomparable` | Dark/shadow references cannot attest a production execution path |
| Lock artifact referenced without owner-observed execution of its semantics | `incomparable` | Durable reference publication is not full experiment execution |

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

Input identity is deeply immutable and independent of subsequent native evidence. Scenario dependencies are projected from ScenarioCompiler rather than recompiled; the compiled semantic snapshot is checked in addition to dependency mtimes. Native topology is distinct from executable-graph identity. Comparability requires bound validated RunReceipt evidence and complete outcomes. The evidence join preserves the host receipt identity, backend system-graph digest, native-validator evidence digest and durable acknowledgement; when a native adapter supplies the same binding, mismatches fail closed. A file-bound helper can consume a host-published canonical RunReceipt and reject noncanonical bytes before invoking the existing validator. Receipt vectors remain synthetic qualification fixtures. The native receipt-reference checkpoint below establishes local publication and reopening only; full experiment execution and production wiring remain open.

### Native receipt-reference checkpoint

The native provenance source now accepts an optional `resolved_input_lock_path`.
It hashes the exact JSON bytes supplied by the experiment owner and does not
redefine that owner's canonicalization or admit the described scenario. The
file ledger verifies the optional lock blob during admission, finalization and
receipt reads. Missing durable bytes reject admission; source drift after
admission makes the host receipt failed. The default source configuration and
existing RunReceipt ABI remain unchanged.

A bounded subprocess uses the existing dark `RuntimeKernelCandidate`, native
RunRecorder and file ledger to reference the compiled first Air matrix lock,
spawn a native Aircraft, step three times, shut down, and reopen the issued
receipt through a read-only ledger owner. It also rejects a missing input blob
and detects loss of that blob on a subsequent process read. Release/rollout
authority inputs are qualification fixtures; no production trust or signature
claim follows. This is an actual local host receipt with a referenced Air lock,
not execution of that entire Air experiment. The probe explicitly reports
`input_lock_semantics_executed=false`, so comparison rejects it. An opt-in
candidate flag now captures the existing kernel owner's realized CPU topology
before shutdown and persists its exact JSON as a run-retained output artifact.
The receipt binds this artifact separately from the immutable composition seal.
Reopening rejects missing or corrupted topology bytes. The file-bound evidence
join requires the bytes when a topology artifact is claimed and checks their
receipt digest, size, media, retention and native topology identity. These checks
establish same-run evidence for this single-world native probe. They do not
establish Air matrix execution. Comparability additionally requires an
owner-observed `input_lock_semantics_executed=true` and matching nonempty
`host_mode`; intentional input axes cannot override those execution boundaries.
Full Air execution/admission, production wiring and external
durable availability remain open gates.

### World identity association

World cardinality alone does not bind an outcome's indexes to receipt worlds.
The default-off `persist_world_scope_binding` candidate option now exports an
owner projection of the actual `RuntimeWorldRef` before shutdown. The candidate
uses the same identity formatter for its existing RunRecorder binding and the
`runtime-world-scope-binding` output artifact. It preserves existing boot,
incarnation, world-ID and world-generation meanings; composition instance IDs
are not substituted for receipt IDs. No published world is claimed when a
candidate is cancelled before start.

The join requires an explicit association for every expected outcome index,
unique world identities matching the receipt, and matching host boot,
incarnation and world epoch. Without the association it retains `unknown` even
when receipt and aggregate outcome say completed. A file-bound association
claim additionally requires its receipt-referenced artifact bytes and metadata.
Comparison rechecks the stored scope and completed per-world coverage. Receipt
ID ordering is not used to infer index association. Native single-world
publication and new-process loss/corruption controls are exercised; two-world
mapping controls remain synthetic owner-contract fixtures. This is not a batch
commit certificate, production trust proof or production multiworld admission.

The first Air matrix smoke requires CUDA. The Windows development environment
still has no CUDA build, but the maintained HEI checkout has an RTX 3090 and
the declared PyTorch CUDA runtime. On 2026-10-22, that checkout completed the
registered `air_combat_1v1_f16c_scripted_red_world_batch_smoke_v1` configuration
for its full 512-step smoke budget through the existing Python
`WorldBatchVecEnv`/`RuntimeFacade` path. This is real Air training execution,
but it did not yet bind a resolved input-lock digest at the existing native
RunReceipt boundary or reopen a durable RunReceipt for that training run.
Consequently it is execution evidence only; it does not satisfy the #239
comparability gate. The dark candidate remains a separate receipt-reference
probe and cannot be substituted for the maintained training path.

The same HEI setup also supplied the first repeat/A-B evidence requested by
#239: a second run of the same registered configuration with seed `239`
completed 512 steps, and a controlled policy-only variant replacing
`HierarchicalMoEExecutionPolicy` with the existing
`SquashedMultiInputPolicy` completed the same 512-step budget. These runs
produced the normal training checkpoints and final models, but neither run was
bound to a native RunReceipt or durably reopened. They therefore establish
repeatable execution and an executable policy-only comparison surface, not
comparability or production acceptance.

See [qualification evidence and remaining gates](../work/issues/rfc_qualified_composition_implementation.md). Lifecycle remains proposed; this checkpoint does not establish owner approval or production admission.
