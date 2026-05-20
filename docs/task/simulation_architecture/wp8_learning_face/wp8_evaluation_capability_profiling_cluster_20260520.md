# WP8-B Evaluation And Capability Profiling

Status: `2026-05-20` complete / accepted WP8 second-wave dispatch sheet.

Language:

- English canonical: `wp8_evaluation_capability_profiling_cluster_20260520.md`
- Chinese companion:
  [wp8_evaluation_capability_profiling_cluster_20260520.zh.md](wp8_evaluation_capability_profiling_cluster_20260520.zh.md)

Inputs:

- [WP8 SCAL Learning Face](learning_face_wp8_20260520.md)
- [WP7.5 Training Path Facade Bridge](../wp75_training_path_facade_bridge/training_path_facade_bridge_wp75_20260520.md)
- [WP7-B Runtime Capability Projection](../wp7_backend_capability_materialization/wp7_runtime_capability_projection_cluster_20260519.md)
- [WP5 validation harness](../wp5_validation_harness/validation_harness_wp5_20260519.md)
- [WP8 acceptance review](../../review/wp8_learning_face_acceptance_review_20260520.md)

Naming note:

- WP8 is the SCAL Learning-face task family.
- `WP8-B` is the evaluation and capability-profiling stream inside that family.
- The maintained training-path bridge remains `WP7.5`; `WP8-B` must cite it
  as the maintained facade-shaped bridge reference rather than redefining it.
- `WP8-B` is a docs-first line. It must not infer support from helper or probe
  presence, and it must not touch `WP8-A`, `WP8-C`, or `WP8-D` files.

## 1. Purpose

`WP8-B` defines how evaluation runs, benchmark protocols, capability profiles,
score attribution, and capability evidence should be described so the Learning
face can compare outputs without becoming a hidden truth source.

This is a high-reasoning stream because the easiest failure mode is to treat
helper or probe availability as proof of support. That is not allowed. Helper
and probe presence may explain observability or deployment state, but they do
not by themselves prove maintained capability.

`WP8-B` should answer:

1. What is the benchmark protocol for evaluation runs?
2. What fields belong in a capability profile schema, and which fields are only
   metadata?
3. How is score attribution recorded without collapsing into a support claim?
4. What counts as capability evidence, and what explicitly does not?

## 2. Scope Boundary

`WP8-B` can:

1. Define benchmark protocol vocabulary, run identity, and reproducibility
   requirements.
2. Define capability profile schema fields and separate metadata from support
   claims.
3. Define score attribution rules, weighting, and traceability requirements.
4. Define capability evidence bundles and evidence acceptance rules.
5. Define parallel worker roles, reasoning budgets, and doc-only validation
   checks for the cluster.

`WP8-B` cannot:

1. Add a new simulation lifecycle or alter the simulation authority boundary.
2. Promote capability support because a helper, probe, or diagnostic path
   exists.
3. Collapse metadata, profile claims, and hidden support claims into one
   undifferentiated record.
4. Change runtime code, tests, or review artifacts outside this doc pair.
5. Reassign the maintained training-path bridge from `WP7.5` into `WP8-B`.

## 3. Work Packages

| Stream | Required output | Write scope | Budget |
|--------|-----------------|-------------|--------|
| `WP8-B1 Benchmark Protocol Boundary` | Define benchmark identity, inputs, seed/version discipline, and reproducibility fields. | docs under `docs/task/simulation_architecture/wp8_learning_face/`. | High. |
| `WP8-B2 Profile Schema And Claim Separation` | Define the profile schema and the separation between metadata, profile claims, and hidden support claims. | docs only. | High. |
| `WP8-B3 Score Attribution And Evidence` | Define score decomposition, weighting, evidence bundling, and anti-overclaim rules. | docs only; may cite `WP7.5`. | High. |
| `WP8-B4 Validation And Publication Sync` | Define acceptance gates, doc-only validation commands, and cross-linking to `WP8` and `WP7.5`. | docs only; serial publication pass. | Medium. |

## 4. Dispatch Plan

| Stream | Main concern | Notes |
|--------|--------------|-------|
| `WP8-B1 Benchmark Protocol Boundary` | Benchmark protocol, run identity, scenario/seed/version discipline. | Establishes the shared vocabulary for all later profile work. |
| `WP8-B2 Profile Schema And Claim Separation` | Metadata fields, profile claims, hidden support claims. | Must stay conservative and explain what is not support. |
| `WP8-B3 Score Attribution And Evidence` | Score breakdown, evidence references, helper/probe anti-overclaim. | Highest boundary discipline inside the cluster. |
| `WP8-B4 Validation And Publication Sync` | Acceptance gates, validation commands, bridge references. | Serial check before publication is considered complete. |

Parallel rule:

- `WP8-B1` and `WP8-B2` may run in parallel once the shared benchmark
  vocabulary is fixed.
- `WP8-B3` can proceed once the profile schema is stable enough to hold
  evidence references and score attribution.
- `WP8-B4` is serial and should only run after the other streams stabilize.

## 5. Protocol And Boundary Rules

### 5.1 Benchmark Protocol

Each benchmark run must be versioned and reproducible. The protocol must state
at least:

- benchmark or scenario family name,
- protocol version,
- seed or seed policy,
- environment or runner identity,
- input slice or dataset selector,
- score dimensions,
- evidence bundle references,
- result status and timestamp.

An evaluation write-up must describe the protocol explicitly. A vague sentence
such as "the model performed well" is not a protocol.

### 5.2 Profile Schema

The profile schema must keep three categories separate:

| Category | Purpose | Rule |
|----------|---------|------|
| Metadata | Identity, provenance, versioning, run context, ownership, timestamps. | Descriptive only. Metadata never proves support. |
| Profile claims | Evaluation-facing claims derived from a benchmark run. | Must cite the protocol and evidence bundle. |
| Hidden support claims | Maintained support statements that would imply real capability ownership. | Must not be inferred from metadata, profile claims, or helper/probe presence. |

The schema may record a capability as "observed", "proposed", "blocked", or
"unsupported", but those labels must remain evidence-bound. They are not
synonyms for maintained support.

### 5.3 Score Attribution

Score attribution must be decomposed into explicit dimensions rather than a
single opaque number. Each score component must record:

- what was measured,
- which benchmark run produced it,
- which evidence bundle supports it,
- whether the score is descriptive, comparative, or gating-related.

Score attribution must not silently upgrade capability status. A high score can
indicate promise or benchmark fit, but it does not by itself prove maintained
support.

### 5.4 Capability Evidence

Capability evidence may include:

- benchmark logs,
- trace digests,
- seeded configuration records,
- result artifacts,
- reproducibility notes,
- review references that explicitly describe the evidence.

Capability evidence does not include:

- the mere existence of a helper or probe,
- the presence of a code symbol,
- an implementation shortcut,
- an unexplained success log,
- any claim that skips the benchmark protocol.

### 5.5 Highest-Reasoning Boundary Discipline

This cluster must remain fail-closed on overclaiming. The rule is:

- helper or probe presence may improve observability,
- helper or probe presence may explain how an evaluation was run,
- helper or probe presence does not imply support.

If the only evidence is that a helper or probe exists, the correct output is
`unknown`, `observed`, or `unsupported`, depending on the protocol. It is not
`supported`.

## 6. Acceptance Artifacts

No `WP8-B` gate may be reported as passed unless the acceptance packet includes
the following normative artifacts:

| Artifact | Required status | Purpose |
|----------|-----------------|---------|
| `docs/task/simulation_architecture/wp8_learning_face/wp8_evaluation_capability_profiling_cluster_20260520.md` | required | English normative dispatch sheet for evaluation and capability profiling. |
| `docs/task/simulation_architecture/wp8_learning_face/wp8_evaluation_capability_profiling_cluster_20260520.zh.md` | required | Chinese companion for the same normative rules. |
| `docs/task/simulation_architecture/wp8_learning_face/learning_face_wp8_20260520.md` | required | Task-family anchor for the Learning face. |
| `docs/task/simulation_architecture/wp75_training_path_facade_bridge/training_path_facade_bridge_wp75_20260520.md` | required | Maintained bridge reference for facade-shaped training-path consumption. |

Artifact rule:

- If any required artifact is missing, the result is `fail`.
- If the docs do not explicitly separate metadata, profile claims, and hidden
  support claims, the result is `fail`.
- If helper or probe presence is allowed to imply support, the result is
  `fail`.

## 7. Strict Gate Rules

Each gate below must be evaluated independently in the acceptance review. A
gate may end only as `pass`, `fail`, or `blocked`.

| Gate | Required evidence | Pass rule | Fail rule | Blocked-environment downgrade |
|------|-------------------|-----------|-----------|-------------------------------|
| `WP8-B1 Benchmark Protocol Boundary` | The acceptance review must name the benchmark protocol fields checked, state the versioning or seed discipline used, and cite the exact doc-only validation commands used to verify the protocol is explicit and reproducible. | Pass only if benchmark protocol vocabulary is explicit, versioned, and sufficient to reproduce or compare runs without hidden assumptions. | Fail if protocol fields are implicit, versioning is absent, reproducibility is unclear, or the evidence is missing. | If local validation is blocked by missing docs, broken links, or workspace state, record `blocked` with the exact command, exact blocker, and the limited static claim that remains. |
| `WP8-B2 Profile Schema And Claim Separation` | The acceptance review must name the profile-schema fields checked, show where metadata ends and support claims begin, and cite the exact doc-only validation commands used to confirm the separation. | Pass only if the schema keeps metadata, profile claims, and hidden support claims distinct and no field silently stands in for support. | Fail if metadata and support claims collapse into one record, if schema labels are ambiguous, or if hidden support claims are inferred from descriptive fields. | If the schema cannot be fully checked because a reference doc is missing, record `blocked` with the exact command, exact blocker, and the remaining doc-only claim. |
| `WP8-B3 Score Attribution And Evidence` | The acceptance review must name the score components checked, show the evidence bundles used for each component, and cite the exact doc-only validation commands used to verify that score attribution does not imply support. | Pass only if score attribution is decomposed, evidence-bound, and conservative about capability status. | Fail if a score is treated as support, if evidence is not traceable, or if helper/probe presence is used as proof. | If evidence traces are unavailable locally, record `blocked` with the exact command, exact blocker, and the limited descriptive claim that remains. |
| `WP8-B4 Validation And Publication Sync` | The acceptance review must confirm the English and Chinese docs are aligned, cite `WP8` and `WP7.5` references, and list the exact doc-only validation commands used to check publication readiness. | Pass only if the pair is aligned, the bridge reference points to `WP7.5`, and no wording reassigns maintained training-path migration into `WP8-B`. | Fail if alignment drifts, bridge references are missing, or helper/probe anti-overclaim wording is weakened. | If publication sync is blocked by workspace state or missing source docs, record `blocked` and keep the gate open. |

Decision rule:

- `pass` requires all required evidence for that gate and no contradictory
  evidence in the same review packet.
- `fail` is mandatory when required evidence is missing, contradicted, or
  replaced by intention-only wording.
- `blocked` is allowed only for environment or workspace limitations and must
  preserve the gate as unresolved.

## 8. Validation Commands

```bash
git diff --check
rg -n "WP8-B|benchmark protocol|profile schema|score attribution|capability evidence|hidden support|helper|probe|support claim|WP7.5" docs/task/simulation_architecture/wp8_learning_face/wp8_evaluation_capability_profiling_cluster_20260520*.md docs/task/simulation_architecture/wp8_learning_face/learning_face_wp8_20260520*.md docs/task/simulation_architecture/wp75_training_path_facade_bridge/training_path_facade_bridge_wp75_20260520*.md
```

Validation wording rule:

- If a command runs and passes, the acceptance review should say `passed` and
  include the exact command.
- If a command runs and fails, the acceptance review should say `failed` and
  include the exact command plus the failing symptom.
- If a command cannot run, the acceptance review should say `blocked` and
  include the exact command, exact blocker, and next environment needed.

## 9. Non-Goals

- Do not add benchmark runner code or change runtime execution paths.
- Do not treat helper or probe presence as support evidence.
- Do not collapse metadata, profile claims, and hidden support claims.
- Do not touch `WP8-A`, `WP8-C`, `WP8-D`, or review artifacts.
- Do not redefine the maintained bridge that belongs to `WP7.5`.
