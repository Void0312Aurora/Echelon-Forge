# N4 Threat / ROE Bridge

Status: `2026-05-25` accepted as the first post-MVP naval pre-fire
scenario-expansion bridge.

Language:

- English canonical: `README.md`
- Chinese companion: [README.zh.md](README.zh.md)

Inputs:

- [Naval current progress](../naval_current_progress_20260524.md)
- [Subagent usage policy](../../../standards/governance/subagent_usage_policy.md)

## Purpose

Define the next naval scenario after the accepted DDG/T-AKE screen and contact
MVP. The expansion is deliberately an `N3 -> N4` bridge: it adds threat
classification, ROE state, and target-assignment provenance before claiming
weapons engagement or damage realism.

Candidate scenario:

- `ddg51_take1_screen_threat_roe_v1`

Scenario concept:

- a `DDG-51` screens a `T-AKE-1` high-value unit;
- a red surface contact approaches through the existing contact-report and
  shared-track path;
- blue preserves the screen geometry while threat and ROE state evolve;
- the scenario may reach pre-fire authorization state, but it does not require
  weapon release, hit assessment, or damage termination.

## Output

- [N4 threat / ROE bridge task cluster](naval_n4_threat_roe_bridge_cluster_20260524.md)
- [N4 threat / ROE dispatch queue](naval_n4_threat_roe_dispatch_queue_20260524.md)
- [N4 RL task surface preflight](naval_n4_rl_task_surface_preflight_20260525.md)
- [N4 integration acceptance](naval_n4_integration_acceptance_20260525.md)

Documentation budget:

- one README pair for navigation;
- one task-cluster pair for the finite work package;
- one dispatch-queue pair after owner approval to distribute implementation
  work;
- one RL preflight pair and one integration acceptance pair after the
  implementation packets return.

## Scope

In scope:

- the `N4` realism boundary for threatened maneuver and ROE;
- finite task clusters for future scenario, contract, runtime/facade, and RL
  preflight work;
- explicit non-claims for `N5` weapon engagement and `N6` damage outcomes;
- dependency and parallel-safety rules for later subagent distribution.

Out of scope:

- creating scenario JSON, contracts, tests, bindings, or runtime code in this
  planning slice;
- firing weapons as a task objective;
- hit probability, missile flight, CIWS terminal defense, damage propagation,
  ASW, UNREP, embarked-air operations, or multi-ship fleet tactics;
- claiming a learned naval policy.

## Gate

This bridge is complete when the cluster, queue, preflight, and acceptance
documents record:

- why `ddg51_take1_screen_threat_roe_v1` is the next scenario candidate;
- that the realism claim is `N3 -> N4`, not `N5` or `N6`;
- the finite cluster list, goals, write scopes, non-goals, validation commands,
  closure gates, dependency/parallel posture, round caps, and model/reasoning
  choices required by the subagent policy;
- the RL preflight surface without treating it as a trained task.
- the integration decision that N4 is accepted but N5 limited engagement remains
  blocked behind launch/reject and non-damage gates.

Validation for this docs-only slice:

```bash
git diff --check -- docs/task/naval
```
