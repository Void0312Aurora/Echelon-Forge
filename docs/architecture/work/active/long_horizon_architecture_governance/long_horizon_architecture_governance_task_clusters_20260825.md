# Long-Horizon Architecture Governance Task Clusters

Status: `2026-08-25` finite long-horizon execution plan for
[Long-Horizon Architecture Governance](README.md). P0 is accepted, P1 target
decisions are ready, and no runtime implementation cluster is accepted.

Parent subproject: [README.md](README.md)

## Boundary Decision

This program owns the transition to immutable admitted kernels, host-owned
replacement, a consolidated composition authority chain, facade-only production
bindings, lifecycle-governed controls, purpose-specific CI, and sustainable
evidence retention.

Finite clusters divide execution and protect overlapping write sets. They do
not reduce the strategic destination. A worker or reviewer may propose a
different mechanism, dependency order, or compatibility bridge, but replacing
the program with test cleanup, documentation cleanup, CI renaming, or another
short-term-only slice is outside the assigned review boundary.

## Finite Task Cluster List

| Cluster | Owner | Capability tier / model ID / reasoning | Goal | Write set | Non-goals | Validation | Closure gate | Dependency / parallel | Round cap | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `P0-A` | main thread | architecture-critical / model ID: n/a / high | Create the owner-linked project packet and verified long-horizon baseline. | project directory, `docs/architecture/README*`, bilingual registry | runtime implementation or acceptance claims | diff check, document links, bilingual audit, source-fact commands | required files exist, parent links resolve, baseline separates facts and unknowns | serial first cluster | 1 + 1 repair | accepted |
| `P0-B` | independent diagnostics reviewer | strongest available review tier / `gpt-5.6-sol` / max | Review the complete plan for missing long-term architecture, migration, authority, safety, and sustainability obligations. | read-only review; findings returned to main thread | substituting a smaller or short-term objective; editing implementation | inspect every project file and cited current source | all findings are dispositioned; no unresolved critical/high plan flaw | after P0-A draft; serial review gate | 1 initial review + up to 2 repair reviews | accepted |
| `P0-C` | main thread | architecture-critical / model ID: n/a / high | Persist and disposition P0-B findings, repair the project packet, and obtain independent repair review. | project files, architecture review record, parent index | implementing runtime phases during plan repair | document audits plus independent finding-by-finding re-review | every P1 finding is accepted into a named cluster/gate and reviewer confirms closure | after P0-B; serial | up to 2 repairs + 2 repair reviews | accepted |
| `P1-A` | future architecture worker | architecture-critical / model ID: n/a / high+ | Freeze the host lifecycle state machine, publication linearization point, monotonic epoch, fencing, leases, drain/backpressure, reclamation, native episode authority, and replacement rollback semantics. | architecture standards/reviews, lifecycle and compatibility designs | immediate deletion or public cutover | caller census, lifecycle transition table, failure/concurrency/state-transfer matrix | decision covers every caller and state category and names one episode barrier owner | after P0 accepted; serial integration with P1-B/P1-C | 2 + 1 repair | ready |
| `P1-B` | future architecture worker | architecture-critical / model ID: n/a / high+ | Freeze durable request/resolved-plan/RunReceipt authority, derivation ownership, and artifact compatibility. | composition standards/contracts design, Cordis/native authority map | weakening native revalidation or allowing parallel resolvers | schema/authority review and byte-level artifact derivation graph | every current artifact is durable, derived, transitional, or historical with version route | after P0; research parallel-safe, normative integration serial | 2 + 1 repair | ready |
| `P1-C` | future operations/security architecture worker | architecture-critical / model ID: n/a / high+ | Define N/N-1 rollout/backout, supported platform/process topology, operational owner/SLO/runbook, and multi-process security activation contracts. | architecture/operations/release decisions and compatibility matrix | admitting multi-process or a platform by aspiration | support matrix, rollout state machine, canary/backout and security threat/failure review | in-process and supported platforms are explicit; unsupported topology fails closed | after P0; integrates serially with P1-A/P1-B | 2 + 1 repair | ready |
| `P2-A` | future governance worker | cross-cutting architecture / model ID: n/a / high | Classify controls and attach lifecycle metadata to existing gate/suite declarations: owner, invariant, kind, creation/expiry, successor, renewal count, and removal proof. | existing architecture/test/tool/doc gate declarations and governing standard | new registry-generator-fixture chain or silent renewal | complete live-control census, expiry simulation, sampled source verification | expired migration controls retire or fail for disposition; at most one sponsored bounded renewal exists | after P1 terminology; parallel with P2-B | 2 + 1 repair | planned |
| `P2-B` | future diagnostics/operations worker | diagnostics / model ID: n/a / medium+ | Measure control yield/false positives, CI/evidence cost, host replacement success/rollback, drain latency/timeouts, stale-ref rejection, resource leaks, plan skew, caller adoption, and evidence retrieval. | diagnostics/reporting tools, runbook/SLO inputs, current-status evidence | turning every metric into a blocking gate without admission | reproducible commands, representative samples, owner and cadence review | baseline is repeatable and every admitted SLO/trigger has an operational owner | after P1; parallel with P2-A | 2 + 1 repair | planned |
| `P3-A` | future contract/build worker | public-contract critical / model ID: n/a / high+ | Establish an engine-independent `ef_runtime_contracts` target and final public world/entity/request/result DTO shell with incarnation epochs. | public contracts, CMake target/visibility foundation, focused negative build checks | full private-link cleanup or host publication | clean builds, header/include/link checks, ABI review | host work can compile against final engine-independent public types | P1 accepted; serial public-contract owner | 2 + 1 repair | planned |
| `P3-B` | future composition-contract worker | public-contract critical / model ID: n/a / high+ | Introduce the versioned `ResolvedCompositionPlan` shell and single-owner adapters from current request/lock/projection/manifest artifacts. | composition contracts, native/Cordis adapters, canonical fixtures | full artifact retirement or hidden fallback | N/N-1 parse/reject matrix, canonical hashes, native/Cordis conformance | one versioned plan shell exists before host cutover and adapters cannot author parallel truth | after P3-A DTO terminology; serial on plan contract | 2 + 1 repair | planned |
| `P3-C` | future release/compatibility worker | public-contract critical / model ID: n/a / high | Implement the rollout contract: single writer, bounded dual readers, stored-plan downgrade/reject semantics, canary/shadow receipts, rollback checkpoints, kill switch, and backout triggers. | compatibility adapters, release policy, tests and fixtures | irreversible production cutover | N/N-1 matrix, simulated skew, canary/backout and stored-artifact tests | mixed-version rollout can advance and revert without two writers or hidden downgrade | after P3-B; before P4 candidate publication and P5-D production cutover | 2 + 1 repair | planned |
| `P4-A` | future runtime worker | highest-risk runtime / model ID: n/a / highest justified | Implement the host lifecycle state machine, instance leases, epoch fencing, drain timeout/cancellation/backpressure, publication linearization, and reclamation in dark/shadow mode. | runtime facade/backend host owner and focused native tests | truth-changing publication or caller cutover | lifecycle model checking, concurrency/failure/stale-ref/resource tests | dark/shadow host proves safe construction and reclamation without becoming execution truth | P3-A/P3-B contract foundation; P3-C rollout available before publication | 2 + 1 repair | planned |
| `P4-B` | future runtime/evidence worker | highest-risk semantics / model ID: n/a / highest justified | Establish unique native episode-barrier authority and explicit transfer/reset/reject rules for ECS, RNG, clock, queues/events, command/link pending state, Python mirrors, device/backend leases, and in-flight requests. | state/evidence contracts, runtime/Python handshake, replay fixtures | claiming state-complete replay without evidence | positive/negative transfer matrix, barrier handshake, replay and stale-handle tests | every state category and in-flight operation has versioned owner-approved semantics | after P4-A dark host; hard predecessor of P4-C | 2 + 1 repair | planned |
| `P4-C` | future runtime integration worker | highest-risk runtime / model ID: n/a / highest justified | Publish only an internal candidate seam, migrate test/shadow adapters to epoch-bearing references, and prove the candidate kernel composition immutable. | `SimulationKernel` candidate path, world batch/facade adapters, native/Python shadow tests | production caller cutover, production publication, or rebuild retirement | caller inventory, dark/shadow parity, C++/Python build, stress, teardown, simulated rollback | candidate host/facade path is state-complete and fenced but cannot become production truth | after P4-A/P4-B and P3-C; serial candidate integration | 2 + 1 repair | planned |
| `P5-A` | future contract worker | public-contract critical / model ID: n/a / high+ | Close the resolved executable plan and consolidate manifest/lock/projection joins behind it. | composition contracts, native validation, generated inputs, Cordis producer | hidden default selection or weakened owner admission | schema fixtures, canonical hashes, native/Cordis conformance, negative admission | one closed plan is production interchange and fully binds admitted derivations | P4 dark/shadow candidate evidence and P3 plan shell | 2 + 1 repair | planned |
| `P5-B` | future evidence worker | public-contract critical / model ID: n/a / high+ | Implement versioned `RunReceipt` with plan bytes/hash, executable/module/wheel digests, build/toolchain/ABI/platform, scenario/content/config/seed, run identities, lifecycle receipts, determinism profile, result hashes, and completion state. | composition/run evidence, provenance, parity, retrieval tooling | deleting reproducibility or claiming state-complete replay | receipt schema/version matrix, actual digest checks, replay/comparison negatives, retrieval drill | every accepted run is bound to actual inputs, executable, lifecycle, result, and completion | after P5-A; serial evidence schema | 2 + 1 repair | planned |
| `P5-C` | future build/binding worker | architecture-critical build / model ID: n/a / high | Finish private engine, public contracts, facade, and diagnostics targets; prepare production bindings/wheel as facade-only packages without activating maintained callers. | CMake targets, visibility, nanobind/package layout, wheel contents, binding/package adapters | production caller activation or removal of required diagnostics without replacement | clean supported-platform builds, link maps, isolated wheel, import/facade/diagnostics tests | production candidate wheel cannot include/link implicit raw engine ownership; diagnostics are explicit opt-in | after P4 candidate seam and P3-A target shell | 2 + 1 repair | planned |
| `P5-D` | future release/runtime integration worker | highest-risk release / model ID: n/a / highest justified | Execute the single truth-changing production cutover after P5-A/B/C, migrate maintained callers, run supported-platform canary/backout, retire production rebuild, and complete operational handoff. | release/workflow/runbook/evidence surfaces, maintained callers, final runtime/facade integration, rebuild retirement | cutover before P5-A/B/C, a second publication point, or declaring unsupported topology | repeated canary/backout, caller migration, rebuild-unreachability, SLO/telemetry, operator and rollback-window drills | one cutover receipt publishes the admitted path; callers adopt it, rollback remains bounded, and rebuild loses production authority | after P5-A/B/C; unique serial production cutover gate | 2 + 1 repair | planned |
| `P6-A` | future test-architecture worker | cross-cutting implementation / model ID: n/a / high | Replace non-retention migration scans/meta-manifests while preserving defect coverage and the invariant that every maintained test has one execution strategy. | non-retention tests/runners, single-source test metadata or derived non-authoritative reports, CTest labels | archive-retention policy/gate/suite changes owned by P7-A; deleting gates by size/age; silently orphaning tests | defect replay/mutation, suite comparisons, orphan detection, focused behavior tests | each retired guard has replacement evidence and every maintained test has an owner/lane | after P2 lifecycle and P5 boundaries; archive-specific work waits for P7-A | 2 + 1 repair | planned |
| `P6-B` | future CI worker | build/release critical / model ID: n/a / high | Implement fast, qualification, nightly, release, and research lanes with explicit failure audiences and parallelism. | workflows, runner entry points, CI docs | weakening wheel/native/composition/replay evidence to hit a timing target | repeated CI runs, dependency and duration evidence, failure routing drills | lane budgets and required gates pass without duplicate execution authority | after P6-A selection model; can prototype without editing P6-A files | 2 + 1 repair | planned |
| `P7-A` | future documentation/evidence worker | governance architecture / model ID: n/a / high | Reconcile the archive-policy/gate conflict and route standards, current references, reviews, accepted evidence, generated output, and retired history to singular lifecycle owners with durability SLOs. | owner docs, lifecycle/subproject standards, archive-retirement gate and suite node, review/index/ledger routes, evidence publishing | erasing provenance, preserving contradictory authorities, or duplicating current status | link/bilingual/lifecycle audits, clean-baseline retirement gate, backup/restore and provider-migration drills, access checks | policy, template, gate, suite, repository route, and retrieval model agree; closed packets leave active authority | after P2/P5 classifications; serial predecessor to archive-specific gate/suite/path changes | 2 + 1 repair | planned |
| `P7-B` | future integration worker | cross-cutting integration / model ID: n/a / high+ | Retire superseded ratchets, zero inventories, migration vocabulary, generators, fixtures, and duplicate documents after replacement gates land. | classified residual write sets across tests/tools/docs | cleanup before replacement, broad unverified deletion | full targeted suites, diff audit, archive/retrieval verification | every deletion is contained by accepted replacement evidence and owner routing | after P3-P7 replacement gates; serial integration | 2 + 1 repair | planned |
| `P8-A` | future acceptance worker | highest-risk integration / model ID: n/a / highest justified | Run supported-topology/platform compatibility, rollout/backout, replay, parity, packaging, performance/resource, failure, operations, security-activation, and governance sustainability acceptance. | acceptance evidence and narrow repairs only | expanding scope during acceptance or accepting docs-only proof | complete matrix plus SLO/adoption/restore/rollback drills | all gates pass; unsupported topology fails closed; residuals have owners without weakening target | after P3-P7 mergeable | 2 + 1 repair | planned |
| `P8-B` | independent reviewer and main thread | strongest available review tier / model ID selected at dispatch / max justified | Independently review the implemented long-horizon result, promote lasting standards, and retire task history through the admitted route. | review document, standards/index/retention-route synchronization | accepting a short-term subset as program closure | independent source/build/evidence review plus doc audits | no unresolved critical/high finding; owner standards and history-retention routes are current | after P8-A; strictly serial closure | 1 review + 1 repair review | planned |

## Dispatch Rules

- Every worker packet maps to exactly one cluster.
- No two workers edit the same public contract, normative table, status line, or
  generated artifact family concurrently.
- Architecture decisions, integration, acceptance, and independent review stay
  serial even when evidence collection is parallel.
- A reviewer may challenge any mechanism or sequence, but a recommendation to
  replace the long-horizon outcome with narrower cleanup or short-term delivery
  is non-responsive and must not close a finding.
- If a mechanism is infeasible, the worker returns a blocker and a replacement
  path that preserves immutable composition, single authority, facade
  containment, control retirement, and evidence sustainability.
- Round caps limit churn inside a cluster; they do not authorize removal of the
  strategic outcome. Exceeding a cap triggers re-baselining of execution, not
  automatic scope contraction.
- Follow the [Subagent Usage Policy](../../../../engineering/automation/standards/subagent_usage_policy.md).

## Worker Packet Requirements

```md
status: pass | partial | blocked | failed
cluster:
touched files:
commands/outcomes:
accepted facts:
remaining paths:
long-horizon risks:
compatibility risks:
integration notes:
```

Review packets additionally require:

```md
review basis:
independence statement:
critical/high findings:
medium/low findings:
long-horizon omissions:
short-term substitution detected: yes | no
verdict: pass | repair-required | blocked
```

## Validation Plan

Repository-root validation grows with implementation. P0 requires:

```powershell
git diff --check
python tools/maintenance/document_link_audit.py --repo-root . --format text
python tools/maintenance/translate_docs_batch.py audit --root docs --registry docs/engineering/documentation/reference/bilingual_document_clusters.json
python -m pytest -q --confcutdir tests/architecture tests/architecture/governance/test_docs_information_architecture.py tests/architecture/governance/test_document_link_audit.py
```

Implementation clusters must add the affected native build, focused Python,
contract, isolated-wheel, replay/parity, failure-injection, resource, and CI
evidence named in their rows. Passing P0 commands never unlocks runtime phases.

## Acceptance Criteria

- Every cluster reaches `accepted` or returns a named blocker and replacement
  path that preserves the complete long-horizon outcome.
- P3-P7 implementation is not inferred from plans, inventories, or source scans.
- No second resolver, execution owner, hidden default, raw production binding,
  or permanent migration-control chain survives P8 acceptance.
- P8-B independent review has no unresolved critical/high finding.

## Residual Map

Immediate:

- P1-A/P1-B/P1-C lifecycle, artifact, rollout, platform/topology, operations,
  and security decisions against the accepted P0 inventory;
- independent P1 architecture review before implementation dispatch.

Follow-on:

- immutable-kernel host migration;
- contract/evidence consolidation;
- physical boundary and lifecycle-control implementation.

Deferred but retained in the target:

- dynamic in-place replacement only after a real identity-preserving consumer
  and complete transfer semantics exist;
- external plugin distribution after security admission;
- CUDA canonical promotion after independent exactness and operational gates.
