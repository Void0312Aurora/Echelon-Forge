# Unified Architecture Iteration Queue I72+ (2026-07-26)

Language:
- English canonical: `iteration_queue_i72_plus_20260726.md`
- Chinese companion: [iteration_queue_i72_plus_20260726.zh.md](iteration_queue_i72_plus_20260726.zh.md)

Document kind: `plan`
Lifecycle: `maintained`
Canonical: `docs/plan/unified_architecture_program/iteration_queue_i72_plus_20260726.md`
Owner: `unified architecture program workline`
Last verified: `2026-07-27`
Baseline and source landing head: `a272fc04`

Status: renumbered successor to the unlanded 2026-07-23 draft
(`iteration_queue_i67_plus_20260723.md`), which this document supersedes. The
draft was designed against the I61-I66 candidate numbering; that numbering
changed when the I61-I71 landing wave was registered. I72-I85 are now
accepted/landed; I86 is closed held with evidence; I87 is accepted/landed.
I88 was run as the first residual-audit pass and returned findings; I89 is
accepted/landed, and I90 is the final accepted closeout audit. The
later I96-I98 PR-bot remediations are register-only repairs, not members of this
I72-I90 numbering map; `727193b2` is a lineage CI-gate prerequisite and
verification repair, not a new iteration number.

## 0. Numbering Note

The 2026-07-23 draft numbered its scheduled rows I67-I85 against the
then-current candidate register. The landed register instead assigned I63 (T8
gate-net), I65 (T6 third pack), I66 (T11 aero bundle), I67 (T2 learning-runtime
note), I68 (T9 A3 authority-default names; "I66" in the draft), I69 (T10
maintained-run ReplayEnvelope producer; "I65" in the draft), I70 (build-infra
nanobind backport), and I71 (this iteration-queue document) to the landing
wave, so the draft's scheduled rows renumber as follows. This is a historical
numbering map; the current statuses are in sections 2-4 (same content, same
order, except I72, adapted as noted in its row):

| Draft id (2026-07-23) | This queue | Content |
|---|---|---|
| I67 | I72 | T6 path-suffix matcher strengthening (accepted/landed; adapted — I65 landed the original two-assertion repair) |
| I68 | I73 | T2/T3 `ScenarioLoader.sim` seam (landed) |
| I69 | I76 | T8 maintained-consumer classifier |
| I70 | I77 | T9 representation adjudication |
| I71 | I78 | T1/T10 lineage vocabulary |
| I72 | I79 | T10 slice 6A ancestry |
| I73 | I74 | T11 ship/submarine bundle (accepted/landed; bundle 4, corrected from the draft's "bundle 3" — the aero bundle is bundle 3) |
| I74 | I75 | T5 experiment-matrix hardening (accepted/landed) |
| I75 | I80 | T4 exact-runtime coverage precondition |
| I76 | I81 | T1/T3 contracts boundary |
| I77 | I82 | T3/T4 ownership move |
| I78 | I83 | T2 `WorldBatchCore` slice 1 |
| I79 | I84 | T10 slice 7 |
| I80 | I85 | T11 capability bundles |
| I81 | I86 | T9 behavioral slice |
| I82 | I87 | T8 typed data-flow pilot |
| I83 | I88 | T7 final residual audit, clean pass 1 |
| I84 | I89 | Narrow repair pack |
| I85 | I90 | T7 final residual audit, clean pass 2 |

Dependency references inside row text were rewritten the same way: the draft's
candidate "I65" (ReplayEnvelope producer) now reads I69 and its candidate
"I66" (T9 authority defaults) now reads I68; all other landed ids referenced by
the draft (I30, I41, I44, I54, I55, I57, I58, I59, I61, I62, I63) were
unchanged at landing. Cross-references between scheduled rows use the new
numbers.

## 1. Scheduling Rules

1. Each iteration has one primary architectural risk. Cross-track labels are used
   only when one deliverable is an explicit dependency seam (for example T1 schema
   machinery serving T10 evidence).
2. A prerequisite failure closes the iteration as **held with evidence**; it does
   not authorize a forced migration.
3. Existing public names, JSON/config shapes, serialized values, retained hashes,
   and default runtime paths remain unchanged unless the row explicitly requires
   a versioned or opt-in surface.
4. A new drift gate must run in the maintained CI smoke manifest unless its
   exclusion is justified with measured cost and another automated owner.
5. T9 behavior changes require domain-evidence review. Parity alone is not enough.
6. T7 runs last, on two separate clean passes. A repair between the passes resets
   the clean-pass count.

## 2. Near-Term Executable Queue

| Iteration | Track | Deliverable | Depends on | Exit evidence and red line |
|---|---|---|---|---|
| I72 (accepted/landed) | T6 | Matcher-strengthening follow-up to T6 ledger §8.9/§9.3: I65 already repaired the two Windows-only `retained_pack/manifest.json` assertions by full `Path` equality, so this slice adds the reusable normalized path-component matcher for suffix checks whose full expected path a test cannot construct, with Windows/POSIX negative cases including boundary-crossing suffixes; I65's two Path-equality call sites stay unchanged. | I57 ledger; I65 §9.3 | Matcher accepts both separator conventions and rejects wrong-component and boundary-crossing paths under Windows and POSIX separators; the two I65-repaired assertions remain byte-identical; the component-fragility calibration red remains separately registered. No retained writer, manifest bytes, or hashes change. |
| I73 (accepted/landed) | T2/T3 | Type the `ScenarioLoader.sim` seam. Census every maintained method used through the handle, define a pure-stdlib structural runtime protocol in the neutral tasking/runtime-contract layer, prove `_ScenarioLoaderRuntimeProxy` implements it, and keep raw-kernel injection test-only. | I62 dead-interface cleanup | Exact caller inventory, import-direction gate, proxy conformance tests, and unchanged loader behavior. No new hub and no `gym_envs -> python.rl` edge. |
| I76 (accepted/landed) | T8 | Close I63's observation-surface escape hatch with a per-file maintained-consumer classifier. Extend the raw-truth scan beyond `reward_runtime` without flagging command/action/loading readers as observation consumers. | I63 | Every maintained observation/reward consumer is classified and registered; injected unregistered consumers fail. No production read migration in this slice. |
| I77 (accepted/landed) | T9 | Adjudicate the representation boundary exposed by I68: echelon authority (`CommandRelationship`/`AuthorityScope`) versus action-interface authority (`AgentRole`/`AgentAuthorityScope`). Produce an evidence-backed mapping or an explicit no-mapping verdict for each relevant A2/A4-A6/A13 path. | I68 | Bilingual verdict matrix, source pointers, domain-review record, and load-bearing consistency gate. Zero C2 behavior change. |
| I78 (accepted/landed) | T1/T10 | Make the lineage vocabulary in C++ `ScenarioGenerationRequestMetadata` and Python `ScenarioGenerationRequest` a shared schema owner (T10 VA-6), generating both faces while preserving field names, order, defaults, and serialization. | I69; T1 generator | Cross-language byte/value parity, freshness gate in smoke, no new runtime import direction, and explicit held verdict for any codec escape hatch. |
| I79 (accepted/landed) | T10 | T10 slice 6A: populate packet ancestry through an additive opt-in/versioned path. Use the facade trace allocator for parent linkage and the I78 typed ref vocabulary; keep all existing default serialized values unchanged. | I78 (landed); I54/I59/I69 | Real-run end-to-end ancestry test, replay validation, retained/default byte parity, and fail-closed foreign-facade evidence handling. Never mutate the default path in place. |
| I74 (accepted/landed) | T11 | Loader table-drive bundle 4: the inner scalar fields of `ship_platform` and `submarine_platform`. Keep object-presence flags and parse-phase order handwritten; generate only the repetitive field reads at their original seams. | I61; I55/I58 | Full-field fixture parity, malformed fail-first parity, 27-definition database parity, C++ full suite, and smoke. Do not absorb the six held `has_*` flags, `default_loadout`, or codec escape hatches. |
| I75 (accepted/landed) | T5 | Harden the typed experiment matrix against the three I30 residuals: JSON object-key escaping, bool-vs-int literal equality, and complete experiment-to-scenario mapping drift. | I30/I44 | Three load-bearing negative tests plus 24/24 byte-identical generated configs. No CLI/config path or matrix file change. |

## 3. Dependency-Gated Queue

| Iteration | Track | Deliverable | Activation gate | Exit evidence and red line |
|---|---|---|---|---|
| I80 (accepted/landed) | T4 | Exact-runtime coverage precondition, still opt-in. | I62 landed; matching C++/Python build | Cross-layer option-cell parity and a gap matrix; no default flip or Python-layer deletion. |
| I81 (accepted/landed) | T1/T3 | I41(f) contracts-boundary disposition. | I80 evidence | The edge has its evidence-backed disposition; dependency direction is not reversed. |
| I82 (accepted/landed) | T3/T4 | Covered-cell controller default resolution, landed disarmed pending performance evidence. | I80 and I81 landed; gpu_host/post-launch constraints remain held as recorded. | No behavior change while disarmed; deletion list remains shrink-only. |
| I83 (accepted/landed) | T2 | `WorldBatchCore` slice 1 from measured common execution/observation seams. | I73 and I82 landed. | One-way graph, single/leader/cooperative compatibility, no speculative plugin method, and measured duplicate reduction. |
| I84 (accepted/landed) | T10 | Opt-in maintained worldline/counterfactual comparison. | I79 landed. | Real-run evidence, no truth promotion, deterministic replay refs, and default-path byte parity. |
| I85 (accepted/landed) | T11 | Capability-bundle truth-source pilot behind `typed_platform_request`. | I74 landed. | Entity/materialization parity, versioned diagnostics, rollback shell, and no `examples/config/**` edit. |
| I86 (held) | T9 | First behavioral Agency slice. | I77/I91 no-mapping evidence chain and this row's explicit held branch. | Closed held; reopening requires a new domain-evidence slice with an explicit registered mapping. |
| I87 (accepted/landed) | T8 | Typed observation data-flow pilot for one bounded TL13 consumer family. | I76, relevant T1 schema, and I83 stable seam all landed. | Typed-view parity, no pilot raw-truth read, no new cross-layer import, and documented empty-list semantics. |

## 4. Closeout Queue

| Iteration | Track | Deliverable | Activation gate | Exit evidence |
|---|---|---|---|---|
| I88 (findings; clean count 0) | T7 | Final residual audit pass 1 over T1-T11 code, callers, gates, docs, held items, and worktree state. | I72-I85 accepted/landed; I86 held with evidence; I87 accepted/landed. | Findings recorded in [I89 residual disposition](t7_i89_residual_disposition_20260727.md); no clean-pass credit. |
| I89 (accepted/landed) | T1-T11 | Narrow repair pack for I88 findings only: bounded sensor-loader parity plus T8/T9 maintenance corrections and explicit residual classification. | I88 findings | Landed as `a272fc04`, with independent review PASS and post-landing gates green. |
| I90 (last; accepted) | T7 | Final residual audit on a fresh checkout and matching build, with two post-repair clean passes. | No changes after I89 review | [Final residual report](t7_i90_final_residual_audit_20260727.md); no new findings, complete ledger hashes, and two consecutive clean passes. |

## 5. Explicitly Unscheduled / Held

- Multi-rate clock domains and barrier scheduling remain gated by exact-runtime
  WP4/WP5 evidence.
- I61's six presence/enablement flags remain local until their paired object-block
  semantics are adjudicated.
- `UnitDefinition::default_loadout` and `ExecutionBatchStepResult` remain held on
  the X-macro comma/type-token boundary.
- No T9 behavioral iteration starts from name similarity; I77's representation
  verdict is mandatory.
- T7 cannot be pulled forward to create an artificial completion signal.

## Related

- [Unified Architecture Program](README.md)
- [Repository Consolidation Plan](../repository_consolidation/README.md)
- [Exact Runtime Refactor Plan](../exact_runtime/cpp_exact_runtime_refactor_plan.md)
- [T6 Residual Ledger](t6_residual_ledger.md)
- [I89 Residual Disposition](t7_i89_residual_disposition_20260727.md)
- [I90 Final Residual Audit](t7_i90_final_residual_audit_20260727.md)
- [T8 G4 Truth-Leak Inventory](t8_g4_truth_leak_inventory.md)
- [T10 Evidence Spine Census](t10_evidence_spine_census_20260721.md)
- [T11 Content Pipeline Census](t11_content_pipeline_census_20260721.md)
