# M3 Optimal-Stopping Model Selection Task Clusters

Status: `2026-06-05` finite task-cluster plan for
[M3 Optimal-Stopping Model Selection](README.md).

## Boundary Decision

M3 is a research and model-selection subproject. It may create documentation
that defines the abstract mathematical problem and compares candidate model
families. It must not implement training code, change runtime behavior, or claim
that A7, M2, or any new model is accepted.

## Finite Task Cluster List

| Cluster | Owner | Model / reasoning | Goal | Write set | Non-goals | Validation | Closure gate | Dependency / parallel | Round cap | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `M3-P0 Problem Definition` | main thread | current main thread | Define the domain-neutral one-shot timing problem and model-selection criteria. | `README*`, `m3_formal_problem_statement_20260605.md`, parent model README links | research synthesis, implementation | `git diff --check -- docs/task/model` | Formal object is explicit enough for workers to use independently. | serial first | 1 + 1 repair | pass |
| `M3-R1 Self-Designed Algorithm` | subagent | inherited model / high reasoning | Without web search, design candidate algorithms from the formal problem. | `m3_self_designed_algorithm_probe_20260605.md` | citations, implementation patches, final recommendation | markdown inspection; worker packet | Document names objectives, assumptions, failure modes, and recommendation. | parallel after P0 | 1 | pass |
| `M3-R2 Academic Literature Survey` | subagent | inherited model / high reasoning | Use academic sources such as arXiv or primary papers to survey relevant model families. | `m3_academic_literature_model_survey_20260605.md` | implementation patches, broad web summaries without primary sources | source links and short summaries; worker packet | Document maps literature to the formal problem and cites sources. | parallel after P0 | 1 | pass |
| `M3-R3 Existing Model-Family Fit Survey` | subagent | inherited model / high reasoning | Survey suitable model families and toolable designs, including how each would fit the current repo constraints. | `m3_existing_model_family_fit_survey_20260605.md` | code edits, final synthesis, A7 acceptance claims | markdown inspection; worker packet | Document names candidate families, fit criteria, and integration risk. | parallel after P0 | 1 | pass |
| `M3-S1 Synthesis` | main thread | current main thread | Compare R1/R2/R3 and recommend a bounded next model contract. | `m3_model_selection_synthesis_20260605.md`, `README*`, parent model README links | training implementation, broad architecture release | `git diff --check -- docs/task/model` | Synthesis separates recommended, fallback, and rejected paths. | serial after R1-R3 | 1 + 1 repair | pass |
| `M3-P3 Decision Sync` | main thread | current main thread | Open the follow-on planning contract without opening training code. | `README*`, parent model README links, `../m3_s1_censored_optimal_stopping_timing_contract/**` | runtime/training implementation, learned-policy claim | `git diff --check -- docs/task/model` | M3-S1 exists and records architecture/data/loss cut points with code still held. | serial after synthesis | 1 | pass |

## Dispatch Rules

- Every worker packet must map to exactly one cluster above.
- Workers may not edit the README, task-cluster plan, dispatch queue, parent
  model README, or each other's research packet.
- The three research packets are parallel-safe because each has a disjoint write
  set and a distinct evidence source.
- The synthesis pass is serial and starts only after the three research packets
  return or are explicitly marked blocked.
- No worker may create a new Codex conversation thread. Subagents are allowed
  only through the current thread's delegation tooling.

## Worker Packet Requirements

```md
status: pass | partial | blocked | failed
touched files:
commands/outcomes:
remaining paths:
behavior risks:
integration notes:
```

Each research packet must also include:

- assumptions;
- model family;
- objective or pseudo-code;
- treatment of censoring;
- deterministic deployment rule;
- early-hazard control mechanism;
- expected failure modes;
- recommendation status: `recommend`, `fallback`, `reject`, or `needs synthesis`.

## Validation Plan

```bash
git diff --check -- docs/task/model/m3_optimal_stopping_model_selection docs/task/model/README.md docs/task/model/README.zh.md
rg -n "recommend|fallback|reject|censor|hazard|stopping" docs/task/model/m3_optimal_stopping_model_selection
```

## Acceptance Criteria

- The formal problem statement is stable and domain-neutral.
- All three research packets exist and are mapped to distinct evidence routes.
- The synthesis document recommends a next bounded contract and rejects at least
  one structurally weak alternative.
- Parent model README links the subproject while keeping M2 unreleased and A7
  held.

## Residual Map

Immediate:

- M3-S1 is open as a planning contract; complete its data/censoring contract
  before implementation.

Follow-on:

- Define data/censoring evidence in M3-S1 before implementation.

Deferred:

- Any implementation of a new survival, stopping-time, sequence, or
  counterfactual model.
