# P5-B Production ArtifactLedger Qualification

Status: accepted for the supported local single-process topology after
independent `gpt-5.6-sol` max re-review. P5-C/P5-D/P8 production and broader
provider/topology gates remain open.

## Authority Boundary

The native runtime has one admitted storage writer: `RuntimeFileArtifactLedgerStore`.
`RuntimeKernelCandidate` reaches it through `RuntimeRunRecorderStore`, and the
recorder performs durable journal admission before constructing the simulation
kernel. The local filesystem backend is the only implementation linked into the
native runtime target.

`tools.maintenance.runtime_durable_artifact_ledger.SQLiteArtifactLedger` is a
qualification and restore oracle only. It is not linked, imported, or selected
by the runtime and cannot publish runtime truth. Its purpose is to exercise the
same receipt/checkpoint/frame invariants against an independent transactional
implementation before native release qualification. A test that passes only in
the SQLite oracle is not a native acceptance result.

## Native Contract

The native adapter currently proves the following contract directly:

- exclusive root lock and monotonically fenced journal generations;
- canonical, append-only journal frames with prior-record hash, payload digest,
  explicit frame length, CRC-32 checksum, and frame digest;
- durable temporary-file write, atomic replacement, file flush, and parent
  directory synchronization on supported local filesystems;
- process-restart resume after a newer fence, complete frame-chain scan, and
  immutable receipt/checkpoint retrieval;
- content-addressed artifact blobs with digest, byte size, media type and
  retention metadata; completed receipts may reference only `ledger://blob-*`
  locations whose bytes are present and verified;
- native checkpoint validation binds recoverable state bytes to their digest;
- backup excludes live lock/temp files, and restore verifies every copied journal
  chain and stored receipt before returning success.

The supported native topology is local and single-process. The root lock is
the process-termination gate: Windows opens it with share-deny-read/write and
POSIX takes a non-blocking exclusive `flock`. A second process cannot create a
recovery store while the previous owner is still alive; after the OS releases
the lock, the newer fence and stale-writer checks govern resume. Explicit
multi-process process-registration/termination-provider semantics remain out
of scope and are rejected by the unsupported-topology boundary rather than
being inferred from a timeout.

The 2026-09-20 closure iteration additionally makes admission immutable before
kernel construction:

- the canonical admission header embeds and validates complete ReleaseManifest
  and RolloutDecision authority envelopes, then cross-binds their detached
  digests, release/decision identities, plan digest and reader-generation window;
- `admission_binding_sha256` covers the static receipt projection, is persisted
  in every RunReceipt, and is rechecked by both the recorder and direct file-store
  finalization path;
- the native candidate reads and hashes owner-controlled executable, package,
  wheel, native-module, runtime-dependency, closed-plan and canonical request
  paths before it can construct `SimulationKernel`; scenario/configuration/seed
  identities are derived from the request whose canonical digest is bound by
  P5-A, while content/database identities are derived from the plan's resolved
  manifest and catalog-lock digests; CPU-exact runs require measured host facts
  and `gpu=driver=none`, while unimplemented accelerator collection fails closed;
- the file adapter's raw header, resume, append, checkpoint and receipt methods
  fail closed; the recorder carries an opaque admission capability through every
  production journal mutation, preventing a direct store caller from becoming a
  second run-evidence writer;
- strict receipts can be finalized only from recorder-projected bytes; lifecycle,
  results, artifacts, checkpoint refs, timestamps and authenticity cannot be
  replaced by a resealed caller template;
- restart recovery rehydrates lifecycle, host/incarnation identity, execution
  scope and durable checkpoint refs from verified journal/checkpoint bytes before
  a CrashReconciler may emit a terminal receipt;
- if receipt persistence succeeds but its outcome audit ACK fails, the recorder
  retries the exact retained receipt bytes without appending a second terminal
  frame or resealing a different timestamp;
- the recorder, rather than the receipt template, authors durable
  `journal_admitted`, `construction`, `validation`, `publication`, `episode`,
  `drain`, `shutdown`, `reclamation` and `terminal` lifecycle frames and derives
  completion timestamps from the admitted run;
- native checkpoint and receipt commits re-read the durable journal header and
  reject direct-store attempts whose plan/release/decision/generation graph
  differs from admission;
- the Python qualification ledger accepts a collector-issued
  `ExecutionObservation`, not an arbitrary mapping, for completed-run executable,
  package, platform and input verification.
- the native store applies role-specific write authorization: `RuntimeHost` owns
  runtime journals/checkpoints/results, `PlanCompiler` may write only the closed
  execution-plan media type, `ReleaseArtifactPipeline` may write only release
  manifest/package/inventory media types, and crash/backup/auditor roles cannot
  create runtime artifacts;
- every mutation records intent and outcome events in a chained audit directory,
  with the audit identity persisted in each event; the availability report
  verifies that chain, journal/receipt/checkpoint/blob hashes, and the protected
  private-root invariant before reporting the store available;
- checkpoint reads, receipt finalization, backup and restore require exact
  source/created reference agreement with the durable receipt scope, and restore
  deletes the target when any copied checkpoint or blob fails validation.

Checkpoint `source_refs` are durable content-addressed references: native
read/restore validates the checkpoint envelope, state bytes, replay aggregate,
reader window, release graph, scope coverage and validation evidence before it
can be returned. Importing those bytes into live ECS/episode state remains the
owner runtime path established by P4-B and the later P5-D cutover drill; this
ledger packet does not claim to be a second state-import authority.

## Qualification Matrix

| Contract | Native evidence | Qualification evidence |
| --- | --- | --- |
| pre-admission mutation fence | `RuntimeKernelCandidate` recorder test | SQLite open/append/finalize test |
| torn frame rejection | native torn-frame test plus frame CRC fields | SQLite payload/length/checksum mutations |
| restart and stale fence | native resume test | SQLite process termination/tombstone/recovery matrix |
| actual output durability | native `put_artifact` and receipt verification | SQLite completed-output blob verification |
| recoverable checkpoint | native validation `state_payload_hex` | SQLite checkpoint validation/replay/reader-range negatives |
| restore | native backup/restore test | SQLite backup/restore/integrity tests |
| role and audit boundary | native role/media-type negatives, chained intent/outcome audit, availability report | SQLite role/media-type and audit permissions |

## Verification Snapshot (2026-09-20)

- `python -m pytest -q --confcutdir=tests/architecture` over
  `test_runtime_authority_contracts.py`, `test_runtime_artifact_ledger.py` and
  `test_runtime_run_receipt.py`: **50 passed**, with two upstream jsonschema
  deprecation warnings.
- Windows/MSVC Debug `runtime_run_recorder`: **16 cases / 148 assertions passed**.
- Windows/MSVC Debug `runtime_kernel_candidate`: **7 cases / 2,683 assertions passed**;
  the candidate test mutates a measured package after admission and proves the
  terminal receipt fails closed.
- Windows/MSVC Debug CTest selection `runtime_kernel_candidate`,
  `runtime_kernel_candidate_parity`, `runtime_run_recorder` and
  `runtime_run_recorder_boundary`: **4/4 passed**.
- relevant Ruff checks, CI YAML parsing, canonical RunReceipt and authority
  vector freshness, and `git diff --check`: passed.
- negative coverage includes tampered authority envelopes, canonical-request and
  measured-file digest mismatch before header commit, incomplete build-owner
  facts, raw store mutation/finalization calls, caller-authored strict receipts,
  torn frame, stale fence/restart with checkpoint rehydration, forged crash
  marker, ephemeral output, incompatible checkpoint replay/reader window, and a
  schema-valid receipt whose plan differs from its durable header.

The final closure verification also included the audit crash-window repair:

- audit enumeration accepts only `event-` plus a 20-digit sequence and `.json`;
- after exclusive root-lock acquisition, only exact `.json.tmp-` plus a
  16-hex-digit durable-write residue is removed;
- complete and truncated audit temporary files are both covered by a native
  restart/availability test;
- Windows/MSVC Debug `runtime_run_recorder` and
  `runtime_run_recorder_boundary`: **2/2 passed** after the repair;
- the independent max review found no unresolved Critical, High, or Medium
  P5-B finding.

This acceptance is bounded: package/wheel bytes are measured and bound to the
admission and receipt, while release-package ledger retrieval belongs to P5-C,
ledger-only cutover belongs to P5-D, and provider replication/migration belongs
to P8.

The matrix is intentionally not a claim that the two stores are interchangeable:
the native adapter owns production runtime writes, while the SQLite backend
detects contract drift and provides an independent qualification implementation.
Any future provider migration must be admitted by P7/P8 and must retire this
oracle boundary explicitly before it can become a runtime writer.
