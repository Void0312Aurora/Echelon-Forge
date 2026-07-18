# Repository Consolidation Plan

Language:
- English canonical: `README.md`
- Chinese companion: [README.zh.md](README.zh.md)

Document kind: `plan`
Lifecycle: `maintained`
Canonical: `docs/plan/repository_consolidation/README.md`
Owner: `repository consolidation workline`
Last verified: `2026-07-18`

Status: active consolidation plan on branch `codex/redundancy-consolidation`.

## Objective

Reduce redundant code, duplicated authority, compatibility residue, oversized
navigation surfaces, and documentation drift across the repository. The work
may adjust architecture when the evidence supports it, but it must preserve
maintained behavior, explicit compatibility commitments, tests, provenance,
and bounded capability claims.

All consolidation iterations remain on the same branch. Each iteration produces
one independently reviewable commit and must be accepted before the next
iteration changes the same surface.

## Iteration Protocol

Every iteration follows this sequence:

1. **Analyze**
   - inspect the current worktree and callers;
   - identify the duplicated owner or obsolete path;
   - define the behavior and evidence that must survive;
   - freeze the write set and non-goals.
2. **Implement**
   - make the smallest coherent architectural change that moves toward one
     maintained owner;
   - migrate callers before removing compatibility or history;
   - do not mix unrelated cleanup into the iteration.
3. **Validate**
   - run focused tests for every touched behavior;
   - run structural, link, lint, build, or smoke gates appropriate to the risk;
   - record commands and outcomes before review.
4. **Independent review**
   - dispatch a separate subagent that did not author the change;
   - review the frozen diff for behavior loss, removed functionality, caller
     survival, compatibility, documentation authority, test adequacy, and any
     unnecessary parallel mechanism that duplicates an existing owner;
   - the reviewer is read-only and returns blocking findings, non-blocking
     findings, and a verdict.
5. **Repair and re-review**
   - fix blocking findings and rerun affected validation;
   - material fixes require a final independent re-check.
6. **Commit**
   - commit only after the final diff has no unresolved blocking review finding;
   - use one commit for the iteration and record its evidence in the iteration
     register below;
   - do not amend an earlier accepted iteration to hide later repairs.

No implementation change made after the final review may be included in the
commit without another review pass.

## Required Acceptance Evidence

An iteration is accepted only when its handoff identifies:

- exact write set and non-goals;
- caller or consumer inventory for removed/moved surfaces;
- focused validation commands and results;
- broader maintained smoke/build result when production behavior changed;
- line/file delta and remaining duplicate owner, if any;
- independent reviewer identity, reviewed revision/diff, findings, and verdict;
- explicit statement of preserved behavior and retained residuals;
- commit hash after commit creation.

Documentation-only iterations must additionally prove local links for the
touched entry surface, bilingual companion consistency where required, and
`git diff --check`.

## Candidate Priority

The list is a routing order, not pre-authorization. Every candidate requires a
fresh source and caller audit when its iteration begins.

| Priority | Candidate | Intended result | Main risk |
| --- | --- | --- | --- |
| P0 | Correctness defects exposed by duplicate representations | Fix incorrect behavior before mechanical deletion. | A compatibility-preserving patch can still change default semantics. |
| P1 | Unreachable implementations and exact helper duplication | Remove dead bodies and establish one runtime/test helper owner. | Hidden construction or import patterns may bypass normal callers. |
| P2 | Documentation lifecycle and consolidation governance | Establish executable classification, review, archive, and evidence rules. | A policy-only change can add another unused authority unless indexed and enforced. |
| P3 | Maintained navigation and compatibility shims | Repair entry links, migrate internal callers from shims, and leave bounded external compatibility facades. | Moving or deleting a shim before caller migration breaks users not visible in tests. |
| P4 | Repeated Python taxonomy, geometry, objective, C2/ROE, and bootstrap helpers | Create one semantic owner with scalar/tensor or runtime/compiler parity tests. | Similar-looking helpers may contain intentional semantic differences. |
| P5 | World-batch, step-evaluation, effects-event, and configuration schema duplication | Replace field-by-field synchronization with shared payloads or explicit adapters. | Public bindings, ABI shape, serialization, and report schemas may change. |
| P6 | Python package cycles and C++ target/layer boundaries | Enforce dependency direction and smaller build/runtime ownership units. | Broad import, linker, initialization-order, and performance regressions. |
| P7 | Documentation compaction, archive normalization, and evidence manifests | Make maintained navigation small; collapse duplicate archive layers only after provenance mapping. | Path moves can break tools, tests, historical references, and rights evidence. |
| P8 | Final repository-wide residual audit | Classify every surviving duplicate as intentional, held, or not cost-effective. | A scan can miss behavioral duplication or overstate textual similarity. |

## Iteration Register

| Iteration | Status | Commit / branch evidence | Scope and result | Validation / review evidence |
| --- | --- | --- | --- | --- |
| I1 Runtime and test infrastructure consolidation | `accepted` | `aaec45882173d57c679e3e7233a81980ee9d8fdc` on `codex/redundancy-consolidation` | Fixed sparse missile-tuning override semantics, removed the unreachable `UniversalEnv` body, centralized `ef_py` runtime bootstrap and suite-manifest parsing, and consolidated repeated test helpers. Net change: 1,413 insertions and 2,390 deletions. | Focused regressions and the maintained smoke suite passed (`361 passed`, `41 subtests passed` in the final iteration closeout). An independent review reported no unresolved blocking finding before commit. |
| I2 Documentation lifecycle and consolidation governance | `accepted` | `c844bd900856682f18d6dc72fcb442b95e75c18a` on `codex/redundancy-consolidation` | Added lifecycle and consolidation authority, one shared maintained-document scope, a strict link audit, selective bilingual-registry refresh, and link-safe repairs without a baseline allowlist. The strict registry now covers 76 pairs. Final diff: 57 files, 1,960 insertions, 427 deletions. | Default audit: 155 documents, 2,592 internal links, zero issues. Focused governance tests: `15 passed`; maintained smoke: `371 passed`, `41 subtests passed`; Ruff and `git diff --check` passed. Registry: 70 synced, 6 preserved legacy divergences, 1 legacy missing English companion. `iteration2_independent_review` found two archive-authority blockers; both were repaired. Final `bilingual_registry_audit` re-review left no unresolved blocker. |
| I3 Documentation de-duplication and bilingual residual closure | `accepted` | `d0dbf0d7ee68643baa30d41e66e3955407d3a3ba` on `codex/redundancy-consolidation` | Rejected a proposed root-README registry special case, compressed the duplicate realism-authority standard into a compatibility routing pair backed by existing owners, removed copied archive implementation detail from the air-combat index, restored the missing review route, and refreshed four verified legacy baselines. Final diff: 17 files, 184 insertions, 192 deletions (net -8). | Registry: 77/77 synced with zero missing peers or drift. Link audit: 156 documents, 2,590 links, zero issues. Focused governance: `25 passed`; maintained smoke: `372 passed`, `41 subtests passed`; Ruff and `git diff --check` passed. Independent review found authority and registry-gate blockers; both were repaired, and final re-review approved the candidate with zero blockers. |
| I4 Scenario compiler compatibility owner consolidation | `accepted` | `afe03257e26f9355013293fb0bace77cfeb4091b` on `codex/redundancy-consolidation` | Replaced the incomplete 64-name manual facade binding with canonical `__all__`-driven forwarding for all 86 exports, migrated 15 maintained callers to `python.scenario.compiler`, and kept tests/archive on the compatibility path. A structural gate prevents new maintained callers from using the facade. Final diff: 22 files, 77 insertions, 86 deletions (net -9). | Direct star-import parity: 86/86 exports with object identity. Focused scenario, world-batch, multi-agent, and architecture tests: `81 passed`; maintained smoke: `374 passed`, `41 subtests passed`; Ruff and `git diff --check` passed. Independent review found one parallel-scan blocker; after reusing the existing full-repository scanner with AST import checks, final re-review approved the candidate with zero blockers. |
| I5 MissionCommand shared-core owner consolidation | `accepted` | `9c999b81` on `codex/redundancy-consolidation` | Made `MissionCommandCore` the equality-capable shared owner, replaced the duplicate directive struct with an alias, collapsed projection and maintained-contract writeback to value copies, and made episode-state equivalence consume owner equality. This fixes four serialized fields that the handwritten comparison omitted while retaining the Python type name; complete and mixed umbrella/core equality are explicitly deleted so domain slices cannot be silently ignored. Final diff: 9 files, 65 insertions, 74 deletions (net -9). | Rebuilt `ef_core`, `ef_py`, and `ef_test`; `ef_test_all` passed. Focused architecture, binding, episode, world-batch, and domain regressions: `119 passed`, `1 skipped`, `6 subtests passed`; maintained smoke: `375 passed`, `45 subtests passed`; Ruff and `git diff --check` passed. Independent review first found inherited partial umbrella equality and missing positive test baselines, then found two mixed umbrella/core comparison directions. All findings were repaired with compile and runtime guards; final re-review approved the candidate with zero blockers. |
| I6 Execution runtime behavior-owner consolidation | `accepted` | `143ee4e9` on `codex/redundancy-consolidation` | Removed the duplicate `execution_frame_runtime.cpp`, moved the retained Frame compatibility symbols into the Episode-owned implementation, and made both APIs share one internal common-products path and one batch scheduler. Public Frame/Episode DTOs, Python names, nominal type separation, the 64-item parallel threshold, ordering, and exception propagation remain intact. Final diff: 13 files, 147 insertions, 151 deletions (net -4). | Rebuilt `ef_core`, `ef_py`, and `ef_test`; `ef_test_all` passed. Focused scalar/batch/fallback/architecture regressions: `46 passed`, `226 subtests passed`; maintained multi-agent/world-batch callers: `71 passed`, `1 skipped`, `5 subtests passed`; maintained smoke: `375 passed`, `45 subtests passed`. Registry: 77/77 synced; link audit: 156 documents, 2,592 links, zero issues; Ruff and `git diff --check` passed. Independent re-review approved the candidate with zero blockers. |
| I7 Mode-choice surface owner consolidation | `accepted` | `587df736` on `codex/redundancy-consolidation` | Made `python.mission_obs_taxonomy` (mission-observation modes) and `python.env_config` (action, execution-step-runtime, step-info, and flight-shaping modes) the single ordered owners for mode surfaces. Training/eval CLI choice lists and validation sets now derive from the owner tuples, removing the five hand-written literal copies in `python/training/cli.py`, `python/env_config.py`, `tools/eval/eval_utils.py`, and `tools/eval/sb3_eval_base.py`. Exported names, choice contents, and ordering are unchanged; new parity tests pin every derived surface to its owner. Final diff: 9 files, 111 insertions, 27 deletions. | Focused env-config/taxonomy, training-bootstrap, and evaluation-CLI regressions: `48 passed`, `2 skipped`, `20 subtests passed`; maintained smoke: `380 passed`, `45 subtests passed` (baseline 375 plus the five new parity guards). Ruff, `git diff --check`, bilingual registry audit (77 pairs), and maintained link audit passed. Independent review approved the candidate with zero blockers. |
| I8 Scalar helper and mode-literal owner consolidation | `accepted` | `aa5b537c` on `codex/redundancy-consolidation` | Established the dependency-free owners `python.angles` (signed/heading wraps, sign-preserving heading error, bearings, planar distance) and `python.coercion` (`coerce_nonnegative_int`), migrating about nineteen maintained angle-helper call sites and all five coercion copies onto them through thin aliases that keep every public name importable. Deliberate variants stay local and test-pinned: the 1e-9 zero-snap wraps, the degenerate-bearing fallback, and the plain-`%360` bearing form with a measured ~1e-13 degree bit-level divergence from the owner form. Remaining runtime mode literals (ScenarioLoader backend checks, world-batch and cooperative vec-env checks, scenario-loader normalizers, diagnostics benchmark CLIs) now derive from `python.env_config`; the previously reported `universal_env.py` residue does not exist at this baseline. `ModeChoiceSurfaceParityTests` gained an `ACTION_MODES` content pin and quote-agnostic negative guards. Final diff: 33 files, 560 insertions, 119 deletions (code and tests: 27 modified files +117/-115 plus three new files; remainder is this register update and the registry refresh). | New 25-case parity suite compares the owners bit-for-bit against embedded copies of the removed formulas (±180/360/negative/non-finite coverage) and joined the CI smoke manifest. Focused naval/world-batch/multi-agent/leader/scenario-compiler/navigation/eval regressions: `325 passed`, `3 skipped`, `51 subtests passed`. Maintained smoke: `406 passed`, `45 subtests passed` (baseline 380 plus 26 new guards). Ruff and `git diff --check` passed. Independent review reproduced numeric parity on a separate 14k-point bit-level grid with zero failures and approved the candidate with zero blockers. |
| I9 Training and evaluation entry-point consolidation | `accepted` | `c20d2366` on `codex/redundancy-consolidation` | Sank the implementation bulk of the root `train.py` (927 to 331 lines) into `python/training/`: lazy SB3/torch dependency loading (`deps.py`), safe action-bias initialization (`action_bias.py`), and vec-env selection/construction (`vec_env_factory.py`). `train.py` keeps a thin `main()`, compatibility re-exports (including the restored `apply_global_seed` that `tools/diagnostics/trace_training_nonfinite_source.py` imports), and the WP24 UniversalEnv retirement guard strings. `evaluate.py` now loads checkpoints through the single owner `tools/eval/sb3_eval_base.load_sb3_policy` (new optional `env=` parameter; all fifteen existing callers unaffected). One deliberate behavior improvement is recorded: historical HMoE/Squashed checkpoints that previously failed to load through `evaluate.py` now load via the shared historical policy-class detection. Two new end-to-end entry smoke tests pin the evaluate CLI and the `train.py --test_only` path. Final diff: 14 files, 1251 insertions, 762 deletions (code and tests: 6 modified files +121/-758 plus five new files; remainder is this register update and the registry refresh). | Independent review verified behavior preservation by AST-normalized function-by-function comparison (action-bias values, all vec-env kwargs, `main()` orchestration and log text), confirmed `import train` loads no torch, and byte-compared all four `--help` outputs against the baseline. Focused training/policy/eval/architecture regressions: `251 passed`, `2 skipped` (one pre-existing GBK-console failure reproduced on the unpatched baseline). Maintained smoke on the landed tree: `406 passed`, `45 subtests passed`. Ruff and `git diff --check` passed. Independent review approved the candidate with zero blockers and adjudicated the two new entry smoke tests keep. |
| I10 Flight-shaping field-tax elimination | `accepted` | `c1a8b2f4` on `codex/redundancy-consolidation` | Hoisted the 89 config-static shaping fields shared by `FlightShapingRuntimeInputs` and `StepEvaluationBatchConfig` into one X-macro list (`src/core/mission/runtime/detail/flight_shaping_shared_fields.inc`); both struct field blocks, the batch-prepare field copy, and the FlightShaping `def_rw` bindings now expand from that single owner. Field types, names, defaults, ordering, and the Python attribute surface (118/15 attributes) are unchanged; the two mission-dynamic `target_*` fields stay hand-written to preserve member order. Final diff: 8 files, 136 insertions, 373 deletions (code: 5 files, +128/-367, net -239; remainder is this register update and the registry refresh). | Rebuilt `ef_core`, `ef_py`, and `ef_test` in an isolated worktree; `ef_test_all` passed. Field audit: 118/118 and 112/112 identical (type/name/default/order); old-vs-new build parity probe produced byte-identical 546-line output. Focused execution/facade/world-batch/architecture regressions: `282 passed`, `1 skipped` (the pre-existing window-loop string-style and local winsock link failures reproduced unchanged on the unpatched baseline). Maintained smoke: `380 passed`, `45 subtests passed`. `git diff --check` passed. Independent review found one register-accounting blocker; after the register repair, the final re-check approved the candidate with zero blockers. |
| I11 Effects-event field-surface owner consolidation | `accepted` | same branch; hash recorded in the next register refresh | Extracted the 135-field `EffectsEvent` inventory into the X-macro list `src/runtime/contracts/detail/effects_event_fields.inc` (48 event-only plus 87 `EffectsResult`-overlap entries) and expanded the contract struct, the `apply_effects_result_fields` projection, and the Python `def_rw` bindings from that single owner. The overlap count corrects the earlier 88-field estimate: `destroy_missile` is a result-only control flag that was never copied. `weapon_launch_adapter.h` (`EffectsEventSnapshot`, `make_effects_event`) was confirmed build-unreachable (text-only shape-test references) and is registered as a deletion candidate, untouched this iteration. The contract shape test now expands the include textually so every field assertion keeps failing on list removals. Final diff: 8 files, 197 insertions, 433 deletions (code and tests: 4 modified files +39/-429 plus the 150-line list; remainder is this register update and the registry refresh). | Independent review verified all 135 fields (type/name/default/order) and the 87/48 split item-by-item against the pre-change sources, re-ran 204 targeted engagement/bindings/air-combat/architecture tests and `ef_test` (113 cases, 18,753 assertions) green, and reproduced the cross-build parity probe (dir() sequence and per-field defaults identical to mainline); verdict approve with zero blockers. On the merged landing tree (I8+I9+I10+I11) the incremental rebuild passed `ef_test_all`, engagement/execution regressions returned `87 passed`, `226 subtests passed`, and maintained smoke returned `406 passed`, `45 subtests passed`. `git diff --check` passed. |

### I2 Residual Disposition In I3

- The repository-root README pair remains deliberately direct-reviewed. The
  maintained link audit already covers it, so one special pair did not justify
  a second registry path model.
- The standalone realism-authority content now routes to the existing gradient
  realism, source-admission, and lifecycle owners instead of duplicating them.
- The six legacy divergences are closed by four evidence-backed baseline
  refreshes, removal of copied air-combat archive detail, and restoration of
  the missing review route.
- Legacy archive normalization and evidence compaction remain P7 work and were
  not folded into I3.

## Surfaces That Must Not Be Deleted Without Additional Gates

The following are not deletion candidates merely because they are large, old,
or duplicated:

- public or compatibility APIs before internal and plausible external callers
  have a migration path and deprecation boundary;
- tests before their behavioral assertions are replaced by equal or stronger
  coverage and the relevant bug history is preserved;
- frozen configs, canonical scenarios, accepted evidence, source-rights
  records, third-party inputs, and provenance manifests;
- generated artifacts consumed by a maintained release or validation path until
  clean regeneration is proven;
- archive records solely because they are stale or verbose;
- ignored/private/local workspaces not admitted into the tracked scope;
- user-owned unrelated worktree changes;
- behavior that has no characterization test until that behavior is first
  measured and its intended boundary is decided.

Deletion of any evidence or archive package requires a consumer/reference scan,
rights and provenance review, and proof that a smaller retained set preserves
the same bounded claim.

## Commit And Review Discipline

- Keep every iteration on `codex/redundancy-consolidation` unless the user
  explicitly changes the branch strategy.
- One iteration equals one coherent commit.
- The independent reviewer must not edit the implementation under review.
- Review must ask whether functionality was removed and whether the change
  duplicates an existing owner, not only whether tests pass or code is shorter.
- Passing narrow tests does not prove repository-wide compatibility.
- If an iteration discovers a materially different problem, record it as a
  later candidate instead of expanding the current write set.
- Do not commit with unresolved blocking findings, failing required validation,
  or unexplained deletions.

## Stop Conditions

The consolidation program may be declared complete only after a final audit
proves all of the following:

1. maintained entry surfaces have one named owner and no known broken internal
   navigation;
2. no confirmed unreachable production body or unowned compatibility path
   remains in the active tree;
3. remaining duplicate schemas/helpers have either one shared owner or an
   explicit documented reason for separate representations;
4. remaining archive/evidence duplication is required for provenance, rights,
   reproducibility, or bounded acceptance;
5. remaining candidates are classified as intentional, held behind a named
   compatibility decision, or demonstrably higher-risk/cost than their benefit;
6. focused tests, maintained smoke/build gates, document gates, and final
   independent review pass;
7. the final residual report identifies what was deliberately retained and why.

Operationally, run at least two consecutive residual-audit passes after the
last material consolidation. The second pass must find no new high-confidence,
safe consolidation candidate. Absence of a textual duplicate alone is not
proof of completion; caller, behavior, documentation, and evidence ownership
must also be audited.

If progress requires an external compatibility decision, unavailable source
rights, or behavior that cannot be characterized from the repository, mark the
candidate `held` with the exact missing authority. Do not delete it to satisfy a
line-count target.

## Related Authority

- [Document Lifecycle Policy](../../standards/governance/document_lifecycle_policy.md)
- [Agent Document Authority Map](../../agent/rules/document_authority_map.md)
- [Standards Maintenance Policy](../../standards/governance/standards_maintenance_policy.md)
- [Subagent Usage Policy](../../standards/governance/subagent_usage_policy.md)
