# Unified Architecture Iteration Queue I72+ (2026-07-26)

Language:
- English canonical: `iteration_queue_i72_plus_20260726.md`
- Chinese companion: [iteration_queue_i72_plus_20260726.zh.md](iteration_queue_i72_plus_20260726.zh.md)

Document kind: `plan`
Lifecycle: `maintained`
Canonical: `docs/plan/unified_architecture_program/iteration_queue_i72_plus_20260726.md`
Owner: `unified architecture program workline`
Last verified: `2026-07-27`
Baseline commit: `9362a136`

Status: renumbered successor to the unlanded 2026-07-23 draft
(`iteration_queue_i67_plus_20260723.md`), which this document supersedes. The
draft was designed against the I61-I66 candidate numbering; that numbering
changed when the I61-I71 landing wave was registered, and the scheduled rows
below re-issue the same queue content under the landed register's numbers
(except I72, adapted as noted in its row; see section 0). The I73 sim-seam
slice has landed; seven rows are currently in flight: I72, I74, and I75
(near-term wave 1) and I76, I77, I78 (partial), and I80 (wave 2, built and
under independent review). Every other row remains scheduled, not accepted; its
activation still follows the repository protocol: focused validation,
independent read-only review, repair/re-review when needed, one iteration
commit, and ledger registration.

## 0. Numbering Note

The 2026-07-23 draft numbered its scheduled rows I67-I85 against the
then-current candidate register. The landed register instead assigned I63 (T8
gate-net), I65 (T6 third pack), I66 (T11 aero bundle), I67 (T2 learning-runtime
note), I68 (T9 A3 authority-default names; "I66" in the draft), I69 (T10
maintained-run ReplayEnvelope producer; "I65" in the draft), I70 (build-infra
nanobind backport), and I71 (this iteration-queue document) to the landing
wave, so the draft's scheduled rows renumber as follows (same content, same
order, except I72, adapted as noted in its row):

| Draft id (2026-07-23) | This queue | Content |
|---|---|---|
| I67 | I72 | T6 path-suffix matcher strengthening (in-flight; adapted — I65 landed the original two-assertion repair) |
| I68 | I73 | T2/T3 `ScenarioLoader.sim` seam (landed) |
| I69 | I76 | T8 maintained-consumer classifier |
| I70 | I77 | T9 representation adjudication |
| I71 | I78 | T1/T10 lineage vocabulary |
| I72 | I79 | T10 slice 6A ancestry |
| I73 | I74 | T11 ship/submarine bundle (in-flight; bundle 4, corrected from the draft's "bundle 3" — the aero bundle is bundle 3) |
| I74 | I75 | T5 experiment-matrix hardening (in-flight) |
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
| I72 (in-flight) | T6 | Matcher-strengthening follow-up to T6 ledger §8.9/§9.3: I65 already repaired the two Windows-only `retained_pack/manifest.json` assertions by full `Path` equality, so this slice adds the reusable normalized path-component matcher for suffix checks whose full expected path a test cannot construct, with Windows/POSIX negative cases including boundary-crossing suffixes; I65's two Path-equality call sites stay unchanged. | I57 ledger; I65 §9.3 | Matcher accepts both separator conventions and rejects wrong-component and boundary-crossing paths under Windows and POSIX separators; the two I65-repaired assertions remain byte-identical; the component-fragility calibration red remains separately registered. No retained writer, manifest bytes, or hashes change. |
| I73 (landed) | T2/T3 | Type the `ScenarioLoader.sim` seam. Census every maintained method used through the handle, define a pure-stdlib structural runtime protocol in the neutral tasking/runtime-contract layer, prove `_ScenarioLoaderRuntimeProxy` implements it, and keep raw-kernel injection test-only. | I62 dead-interface cleanup | Exact caller inventory, import-direction gate, proxy conformance tests, and unchanged loader behavior. No new hub and no `gym_envs -> python.rl` edge. |
| I76 (in-flight) | T8 | Close I63's observation-surface escape hatch with a per-file maintained-consumer classifier. Extend the raw-truth scan beyond `reward_runtime` without flagging command/action/loading readers as observation consumers. | I63 | Every maintained observation/reward consumer is classified and registered; injected unregistered consumers fail. No production read migration in this slice. |
| I77 (in-flight) | T9 | Adjudicate the representation boundary exposed by I68: echelon authority (`CommandRelationship`/`AuthorityScope`) versus action-interface authority (`AgentRole`/`AgentAuthorityScope`). Produce an evidence-backed mapping or an explicit no-mapping verdict for each relevant A2/A4-A6/A13 path. | I68 | Bilingual verdict matrix, source pointers, domain-review record, and load-bearing consistency gate. Zero C2 behavior change. |
| I78 (in-flight) | T1/T10 | Make the lineage vocabulary in C++ `ScenarioGenerationRequestMetadata` and Python `ScenarioGenerationRequest` a shared schema owner (T10 VA-6), generating both faces while preserving field names, order, defaults, and serialization. | I69; T1 generator | Cross-language byte/value parity, freshness gate in smoke, no new runtime import direction, and explicit held verdict for any codec escape hatch. |
| I79 | T10 | T10 slice 6A: populate packet ancestry through an additive opt-in/versioned path. Use the facade trace allocator for parent linkage and the I78 typed ref vocabulary; keep all existing default serialized values unchanged. | I78; I54/I59/I69 | Real-run end-to-end ancestry test, replay validation, retained/default byte parity, and fail-closed foreign-facade evidence handling. Never mutate the default path in place. |
| I74 (in-flight) | T11 | Loader table-drive bundle 4: the inner scalar fields of `ship_platform` and `submarine_platform`. Keep object-presence flags and parse-phase order handwritten; generate only the repetitive field reads at their original seams. | I61; I55/I58 | Full-field fixture parity, malformed fail-first parity, 27-definition database parity, C++ full suite, and smoke. Do not absorb the six held `has_*` flags, `default_loadout`, or codec escape hatches. |
| I75 (in-flight) | T5 | Harden the typed experiment matrix against the three I30 residuals: JSON object-key escaping, bool-vs-int literal equality, and complete experiment-to-scenario mapping drift. | I30/I44 | Three load-bearing negative tests plus 24/24 byte-identical generated configs. No CLI/config path or matrix file change. |

## 3. Dependency-Gated Queue

| Iteration | Track | Deliverable | Activation gate | Exit evidence and red line |
|---|---|---|---|---|
| I80 (in-flight) | T4 | Close the exact-runtime coverage precondition before any layer retirement: exercise post-launch evaluation and every maintained `flight_shaping_backend` option through `execution_episode_controller_mainline`, still opt-in. | I62 landed; matching C++/Python build | Cross-layer parity for all option cells and an explicit gap matrix. No default flip and no Python layer deletion. |
| I81 | T1/T3 | Resolve the I41(f) contracts boundary around `WorldExecutionEpisodeStepRequest` borrowing mission evaluation types. Use T1 schema ownership if byte-equivalent; otherwise freeze a precise held verdict. | I80 evidence | Either shrink the include-direction allowlist by one with 57-binding parity, or register why the edge remains held. Do not reverse the dependency. |
| I82 | T3/T4 | Move the next exact-runtime ownership boundary only if I80 proves coverage: make the compiled episode controller own the covered batch slice and retire only superseded private Python orchestration. | I80 pass; I81 disposition. Owner-delegated disposition (2026-07-27): the I80 gap matrix's gpu_host cells are HELD (EF_ENABLE_CUDA_EXPERIMENTS is experimental and default-off; the mainline's construction-time rejection stands); the post-launch-evaluation cells bind the red line — the ownership move's shrink-only deletion list must exclude every path the default-path post-launch assessment needs, and porting the assessment into the controller is registered as its own future work item, not folded into I82. | Default-path before/after parity, hot-path measurements, public-surface audit, and a shrink-only deletion list. Stop if a maintained option needs Python fallback. |
| I83 | T2 | Extract `WorldBatchCore` slice 1 from measured common execution/observation seams, using the I73 loader protocol and I82 ownership boundary. | I73 and I82 | One-way dependency graph, single/leader/cooperative compatibility, no speculative plugin method, and measured duplicate reduction. |
| I84 | T10 | T10 slice 7: expose worldline/counterfactual comparison through the maintained adapter as opt-in, consuming I69 envelopes and I79 ancestry. | I79 | Real-run comparison evidence, no truth promotion, deterministic replay refs, and default-path byte parity. |
| I85 | T11 | Pilot content capability bundles as a truth source for one bounded platform family behind `typed_platform_request`; keep `spawn_unit` compatibility as the reference path. | I74 | Entity/materialization parity, versioned validation diagnostics, rollback shell, and no edit to `examples/config/**`. |
| I86 | T9 | First behavioral Agency slice, chosen from the I77-approved mapping (prefer the smallest A13 who-may-fire or A2 default-dispatch seam). | I77 mapping accepted by domain review. I77's owner-delegated sign-off recorded no-mapping (2026-07-27), so I86 is expected to close held once that record lands. | One semantic owner, adversarial authorization tests, no observation/reward ownership leak, and explicit before/after doctrine evidence. If I77 returns no mapping, I86 closes held instead. |
| I87 | T8 | Typed observation data-flow pilot for one bounded TL13 consumer family, using I76 classification and T1 DTO machinery; the structural `ObservationViewSpec` export becomes consumed data rather than metadata only. | I76; relevant T1 schema; I83 stable seam | Typed-view parity, no raw truth read in the pilot, no new cross-layer import, and a documented meaning for empty required/optional field lists. |

## 4. Closeout Queue

| Iteration | Track | Deliverable | Activation gate | Exit evidence |
|---|---|---|---|---|
| I88 | T7 | Final residual audit, clean pass 1, covering T1-T11 code, callers, gates, docs, held items, and worktree state. | I72-I87 accepted or explicitly held | Every survivor classified `intentional` / `held` / `uneconomic`; zero unclassified findings. |
| I89 | T1-T11 | Narrow repair pack for findings from I88 only. No opportunistic work. | I88 findings | One commit per repaired iteration risk, full affected gates, independent review. If I88 is clean, I89 is skipped. |
| I90 | T7 | Final residual audit, clean pass 2 on a fresh checkout and matching build. | No changes after the last repair | Same classifications as pass 1, no new findings, complete ledger hashes, and two consecutive clean passes. |

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
- [T8 G4 Truth-Leak Inventory](t8_g4_truth_leak_inventory.md)
- [T10 Evidence Spine Census](t10_evidence_spine_census_20260721.md)
- [T11 Content Pipeline Census](t11_content_pipeline_census_20260721.md)
