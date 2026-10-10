# ADR: layered simulation failure domains and recovery

Language:
- English canonical: `simulation_failure_domain_adr.md`
- Chinese companion: [simulation_failure_domain_adr.zh.md](simulation_failure_domain_adr.zh.md)

Document kind: `standard`
Lifecycle: `proposed`
Canonical: `docs/architecture/standards/simulation_failure_domain_adr.md`
Owner: `architecture/failure-contracts`
Last verified: `2026-10-10`

**Status:** proposed contract; no new host, transaction engine or production
cutover is authorized.

## Decision

Use a layered outcome vocabulary that distinguishes admission, mechanism/stage,
single-world, batch and host/process failures. Each layer reports observed
facts, while native world/ECS truth remains authoritative for state validity.
Facade and Python translate the outcome and must not infer rollback from an
exception.

The minimum active CPU/facade policy is fail-closed: preflight rejection has
no publication; a mid-step or worker fault creates an explicit generation
fence and an unknown/untrusted state unless reliable per-world evidence exists;
callers may not transparently retry. Reset/recreate is explicit and is the
only default recovery for unknown mutation. Read-only operations, idempotent
setup, reset, irreversible step and issued command have separate retry rules.

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
