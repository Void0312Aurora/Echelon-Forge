# ADR: layered simulation failure domains and recovery

Language:
- English canonical: `simulation_failure_domain_adr.md`
- Chinese companion: [simulation_failure_domain_adr.zh.md](simulation_failure_domain_adr.zh.md)

Document kind: `standard`
Lifecycle: `proposed`
Canonical: `docs/architecture/standards/simulation_failure_domain_adr.md`
Owner: `architecture/failure-contracts`
Last verified: `2026-10-13`

**Status:** proposed contract; no new host, transaction engine or production
cutover is authorized. The upstream `main` line is not treated as enforcing
this whole contract. The qualification branch carries a local #210 owner
implementation and its evidence only; that branch evidence must not be
reported as a mainline or production guarantee.

## Decision

Use a layered outcome vocabulary that distinguishes admission, mechanism/stage,
single-world, batch and host/process failures. Each layer reports observed
facts, while native world/ECS truth remains authoritative for state validity.
Facade and Python translate the outcome and must not infer rollback from an
exception.

The target CPU/facade policy is fail-closed: preflight rejection has no
publication; a mid-step or worker fault creates an explicit generation fence
and an unknown/untrusted state unless reliable per-world evidence exists;
callers may not transparently retry. Reset/recreate is explicit and is the
only default recovery for unknown mutation. Read-only operations, idempotent
setup, reset, irreversible step and issued command have separate retry rules.
On this qualification branch, the local #210 port exercises that target for
the tested `WorldBatchRuntime` path. The upstream production path remains an
open integration gate until the owner repair is delivered and re-verified on
its ancestry.

## Current state and transition matrix

The following matrix separates observed branch evidence from the proposed
contract. It does not infer a state transition from an exception alone.

| State | Observed meaning | Allowed operations | Evidence required to leave the state |
| --- | --- | --- | --- |
| `healthy` | The generation has no recorded failure fence | Admitted setup, step, read-only export and reset according to the owning API | Successful operation or successful reset evidence |
| `failed/untrusted` | A preflight-safe failure, worker fault or post-mutation uncertainty has been recorded; rollback is not implied | Diagnostics and an explicit reset/recreate; no mutating retry or synchronized-success export | A successful reset/recreate that reinitializes the complete expected world scope |
| `failed/host-recreate-required` | A running Flecs callback left readonly/defer scopes unfinished | Diagnostics and host retirement; reset, step and synchronized exports remain fenced | A separate replacement host initializes and successfully runs a fresh native batch |
| `healthy` after reset | A new usable generation was initialized | Normal operations for the new generation | Reset result plus native state/setup evidence; this is not proof of rollback |

The current branch proves native-issued generation identity, the reset path for
tested setup/launch faults, and terminal host recreation for an injected running
system exception. Bounded subprocess controls observe fatal exit and kill/reap a
nonterminating callback, followed by successful replacement-host startup. They
do not establish production supervisor isolation, reliable per-world commit,
rollback, cancellation or safe teardown of an interrupted Flecs world.

## Outcome contract

An outcome records operation/generation identity, layer and failure class,
affected world/stage, pre/post-publication certainty, completion state
(`completed`, `failed`, `skipped`, `unknown`), evidence references and permitted
recovery. A partial batch is never reported as synchronized success. A caught
exception does not imply an unmodified batch; `abort`, deadlock and blocked
native code are outside same-process recovery claims and require bounded
subprocess/supervisor qualification.

Mechanism composition reuses this taxonomy for child effects and unknown state;
it does not add a second scheduler or ledger. Existing #209 and #210 retain
their implementation ownership. Existing RunReceipt/evidence and the
resolved-experiment projection (#239) remain evidence authorities.

## Proof gates

Qualification must inject preflight rejection, a mid-step fault and a worker
task exception in serial and parallel 3–4-world batches, record generation and
state evidence, and verify no transparent retry. Dangerous nontermination or
process-fatal controls run only in bounded subprocesses. Candidate host and
CUDA results are reported separately from admitted CPU/facade guarantees.

## Option comparison and implementation checkpoint

| Option | Disposition in this proposed ADR |
| --- | --- |
| Batch-wide fail-stop fence | proposed baseline policy; reuse the native #210 owner and require explicit recovery |
| Per-world outcomes and quarantine | held until native publication evidence can reliably distinguish each world |
| Transactional rollback of all effects | held; no current proof of atomic rollback |

The public `BatchOperationOutcome` constructor requires non-empty expected-world
evidence and exact index coverage for every `completed` result; the default empty
scope cannot be used to bypass that invariant. Skipped/unknown outcomes cannot
masquerade as completion, and aggregate faults project all affected
worlds as unknown without inferring rollback from clocks. The #210 owner repair
from PR #230 has been ported locally onto the qualification branch's current
interfaces, including the
new composition-evidence export guard. See the existing
[WorldBatch failure contract](world_batch_failure_contract.md).

Native 3/4-world serial/parallel proofs exercise mixed world advancement, a setup
exception after timestep mutation, guarded exports/retry, invalid recovery input
and explicit reset. Python and the maintained facade consume the same local
native fence. This is qualification evidence, not proof that upstream `main`
already provides that projection. All-unknown aggregate evidence reports
`failed` with explicit reset/recreate required; it does not claim known per-world
commit status. The mechanism child
fault proof separately observes state mutation without outer packet publication.
The Python qualification adapter now reads `batch_healthy()` and
`batch_failure_reason()` from the native owner before projecting that
all-unknown outcome; it rejects a healthy runtime and never invents a reset
result. The native owner also exposes a batch generation ID that changes only
after successful reset; the Python projection does not synthesize or reinterpret
that identity. A separate `project_host_fault` projection accepts an
independent process-survival observation and emits a host-domain failed outcome
with all affected worlds unknown and generation termination required; it does
not claim to provide the supervisor or isolate a blocked native call.
The native batch proof also injects a worker-launch failure and checks that joined
workers, guarded exports, failed recovery and explicit reset remain fail-closed.
These local changes are not an upstream #210 closure. The running-system probe
mutates native ECS state before throwing; it verifies that unfinished pipeline
scopes reject reset and raw step, while the batch owner reports
`batch_requires_host_recreate()`. Python translates that native decision into
`terminate_generation`. Dangerous controls run only in disposable subprocesses;
the damaged exception-test process exits without claiming safe Flecs teardown.

See [qualification evidence and remaining gates](../work/issues/rfc_qualified_composition_implementation.md). Lifecycle remains proposed; this checkpoint does not establish owner approval or production admission.
