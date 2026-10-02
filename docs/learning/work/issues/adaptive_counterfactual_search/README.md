# Adaptive Counterfactual Search Experiment Preparation

Status: `draft`\
Lifecycle: `experimental`\
Owner: `learning/training` with runtime-facade review required\
Baseline: `origin/main` at `9ee4558e`\
Preparation branch: `codex/counterfactual-experiment-prep`

## Purpose

This packet turns the locally supplied research note `docs/temp/temp-01.md`
into a bounded first experiment. That path is intentionally ignored by the
repository (`docs/**/temp/`); the preparation packet records the derived
scope without promoting the temporary note into maintained source. The note proposes adaptive counterfactual
search under a finite simulation budget, with allocation across decision point
`t`, temporal horizon `H`, agent interaction order `M`, and local approximation
order `p`.

The first step is a deterministic toy canary. It tests the measurement and
stopping logic without pretending that the current simulation runtime can fork
an authoritative world.

## Current Infrastructure Boundary

- `RuntimeFacade` currently exposes maintained world setup, stepping,
  observation, tasking, and window execution. It does not expose
  snapshot/restore/clone or counterfactual branch methods on `origin/main`.
- Commit `ad9ba9d1` removed the previous counterfactual/evidence surface because
  it had no maintained production consumer. That historical surface is not a
  valid dependency for this experiment.
- `python/experiment/` provides standard-library experiment definitions,
  configuration composition, seed normalization, and report envelopes. The
  current maintained matrix is an experiment registry, not a branch-search
  runner.
- The Arnis Phase 1 adapter produces static continuous environment data and
  explicitly does not release terrain runtime, movement, sensing, LOS, or
  combat behavior. It is not a counterfactual backend.
- The CUDA-resident replay contracts compare a reference and shadow execution
  lane. Replay parity is useful provenance infrastructure, but it is not a
  snapshot/restore contract for alternate actions.

The absence of a runtime fork surface is the first result of this audit. The
toy canary below must pass before a new public runtime contract is designed.

## Research Claims To Test

The note's assumptions and hypotheses are converted into observable gates:

| Claim | First measurable signal | Evidence boundary |
| --- | --- | --- |
| Important decision points are sparse (`H1`, `A6`) | oracle high-gain recall at a fixed candidate budget | synthetic only |
| Uniform + reward/TD proposals find useful points (`H2`) | recall and cost against uniform and oracle baselines | synthetic only |
| Same-state branches improve credit assignment (`H3`, `A1-A2`) | branch return gap from one frozen toy state | toy state only |
| Horizon can stop when ranking stabilizes (`H4`) | best-action identity for `H=1,2,4,8` and stop point | toy model only |
| Low-order interaction is usually enough (`H5`, `A5`) | pairwise residual versus additive baseline | toy model only |
| Local probes can replace exhaustive rollout (`H6`) | fitted probe ranking versus exhaustive ranking | deferred until probe model exists |
| Complexity is non-uniform (`H7`) | budget spent per candidate and per `H/M` escalation | deferred until runtime fork exists |

## Phase Plan

### Phase 0: Toy semantic canary (this branch)

The checked-in module [`python/experiment/counterfactual_toy.py`](../../../../../python/experiment/counterfactual_toy.py)
contains only pure deterministic functions:

- `select_candidates`: uniform, reward/TD, and oracle reference selectors;
- `rollout_branch`: a delayed commitment toy with a measurable horizon effect;
- `best_branch`: exhaustive reference ranking;
- `interaction_residual`: a two-agent finite-difference interaction term.

The focused tests in
[`tests/experiment/test_counterfactual_toy.py`](../../../../../tests/experiment/test_counterfactual_toy.py)
check import isolation, deterministic replay, horizon sensitivity, interaction
residual, and strict candidate-budget accounting. They are local experimental
tests and are not added to CI smoke yet.

### Phase 1: Candidate discovery benchmark

Use a fixed synthetic episode table with an explicit hidden oracle gain. For
each seed and budget, compare:

1. uniform time probing;
2. reward-spike retrospective probing;
3. reward plus TD-surprise probing;
4. oracle ranking as an upper bound.

Record candidate recall, branch count, wall-clock-independent simulated cost,
best-branch regret gap, and deterministic report hash. Use fixed seeds and a
held-out episode table; do not train a proposal network in this phase.

### Phase 2: Runtime contract preflight

Before touching `RuntimeFacade`, specify and test the missing contract:

- an authoritative snapshot identity and restore barrier;
- the state ownership included in a snapshot and the state explicitly held out;
- branch isolation and baseline immutability;
- deterministic event order and seed handling;
- observation/reward export with source snapshot ancestry;
- rejection paths for unsupported resident-GPU, full-clone, or raw-state
  mutation requests.

This phase is blocked until the contract has an owner and a maintained consumer.
Recovering the deleted `ad9ba9d1` surface without a new ownership decision is
not an acceptable shortcut.

### Phase 3: One maintained scenario

Only after Phase 2 passes, select one existing maintained scenario and run a
small branch matrix. Keep scenario, configuration, policy checkpoint, seed,
action interface, and evaluation protocol fixed across all methods. Start with
`M=1`, `p=0`, and horizons `H in {1, 2, 4, 8}`; escalate only when ranking or
residual gates require it. No real-world or combat-performance claim follows
from this experiment.

## Required Report Fields

Every Phase 1+ report should include:

- repository revision and experiment identifier;
- scenario/config reference and exact seed list;
- selector, candidate budget, branch budget, `H`, `M`, and `p`;
- baseline and branch action identities;
- per-branch return vectors and aggregate return;
- candidate recall, regret gap, interaction residual, and stopping reason;
- deterministic replay/hash check result;
- explicit `synthetic`, `toy`, or `runtime` evidence label;
- unsupported-capability and missing-runtime-contract notes.

## Acceptance Gates

1. Same inputs produce byte-equivalent toy results and report fields.
2. Every selector obeys the declared branch budget and has a stable tie break.
3. The oracle selector is used only as an evaluation upper bound.
4. Horizon stopping is based on ranking/value stability, not a fixed claim that
   one horizon is universally sufficient.
5. Interaction residual is measured before assuming additive credit.
6. No output is promoted to a maintained runtime or policy claim until a new
   snapshot/restore contract and its integration tests exist.

## Non-goals

- no changes to the maintained runtime facade in this preparation slice;
- no GPU branch execution or full-world cloning;
- no Arnis regeneration or terrain realism claim;
- no policy training or distillation;
- no claim that reward spikes identify causal decision points;
- no CI smoke promotion before the experimental protocol stabilizes.

## Local Validation

From the preparation worktree:

```bash
python -m pytest tests/experiment/test_counterfactual_toy.py -q
python -m ruff check python/experiment/counterfactual_toy.py tests/experiment/test_counterfactual_toy.py
```
