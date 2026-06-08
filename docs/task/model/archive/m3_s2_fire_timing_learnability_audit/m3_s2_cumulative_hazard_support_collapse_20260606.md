# M3-S2 Cumulative Hazard And Support Collapse - 2026-06-06

Parent: [README.md](README.md).

Status: `root-cause evidence`; support-preserving collection confirms the
support-collapse mechanism and repairs collection support, while M3-S2 behavior
remains held.

## Question

Why did direct event-window supervision fail even though it reached the
executable hybrid `fire_once` event logits and produced nonzero gradients?

The key distinction is per-step probability versus one-shot cumulative hazard.
For a one-shot event sampled at each legal-open step, a small per-step fire
probability `p_t` is not small over a long prewindow:

```text
P(early fire before quality window) = 1 - product_t(1 - p_t)
```

If `p_t` is approximately constant, this becomes:

```text
P_early = 1 - (1 - p)^n
```

## Probe Evidence

Artifact:

```text
experiments_tmp/m3s2_event_window_8k_20260605_r2/
```

Deterministic probe:

| Metric | Value |
| --- | ---: |
| `a7_prewindow_step_count` | `800` |
| `a7_prewindow_event_fire_prob_mean` | `0.005541579` |
| calculated `1 - (1 - p)^n` | `0.988269849` |
| reported `a7_prewindow_event_fire_prob_cum` | `0.988269851` |
| `a7_quality_window_step_count` | `1080` |
| `policy_event_prob_fire_once_max` | `0.005557978` |
| `policy_event_mode_fire_once_count` | `0` |
| `release_count` | `0` |

The deterministic policy does not fire because `argmax(fire_once)` never
crosses the event boundary. However, the same logits imply that stochastic
sampling would almost surely consume the one-shot somewhere in the 800-step
prewindow.

Stochastic probe:

| Metric | Value |
| --- | ---: |
| `a7_prewindow_step_count` before release | `11` |
| `a7_prewindow_event_fire_prob_mean` | `0.005408502` |
| calculated `1 - (1 - p)^n` | `0.057910495` |
| reported `a7_prewindow_event_fire_prob_cum` | `0.057910509` |
| `first_release_step` | `14` |
| `release_count` | `1` |
| `a7_quality_window_step_count` | `0` |
| `effects_event_count` | `0` |
| `damage_report_count` | `0` |

The stochastic release is therefore an early low-probability sample, not a
learned quality-window fire.

## Training-Trace Evidence

TensorBoard scalars from the same run:

| Step | Accepted events | Early-prefix groups | Window groups | Active groups | Closed rows | Early mass | Window mass | Grad norm |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2048 | `3` | `3` | `0` | `4` | `4` | `0.223625` | `0.000000` | `7.566911` |
| 3072 | `0` | `0` | `1` | `1` | `768` | `0.058136` | `0.332401` | `21.615065` |
| 4096 | `0` | `0` | `1` | `1` | `768` | `0.074416` | `0.397732` | `20.607054` |
| 5120 | `1` | `0` | `1` | `1` | `768` | `0.105678` | `0.141995` | `22.187145` |
| 6144 | `0` | `0` | `0` | `0` | `1024` | `0.000000` | `0.000000` | `0.000000` |
| 7168 | `0` | `0` | `0` | `0` | `1024` | `0.000000` | `0.000000` | `0.000000` |
| 8192 | `0` | `0` | `0` | `0` | `1024` | `0.000000` | `0.000000` | `0.000000` |

This explains the apparent contradiction:

- early stochastic samples consume the one-shot event before the quality window;
- the runtime state switches to `FiredAssess`, which closes `fire_mask`;
- the grouped sidecar then loses supported quality-window rows;
- later updates have `active_group_count = 0`, so the M3-S2 auxiliary path has
  no useful training support even though the code path is connected.

## Severity

The current prewindow probability is small only in row-wise classification
terms. It is large in one-shot stopping terms.

To keep cumulative prewindow risk below `0.02` for `800` legal-open prewindow
steps, a roughly constant per-step probability must satisfy:

```text
p <= 1 - 0.98^(1 / 800) ~= 0.00002525
logit(p) ~= -10.59
```

The deterministic executable event boundary still requires `fire_once` to beat
`hold`, i.e. a logit delta above `0` in the quality window. The learned policy
therefore needs a very sharp transition:

```text
prewindow:      logit << -10
quality window: logit > 0
```

The observed M3-S2 logits do not show that transition. At 3072 to 5120 updates,
prewindow and quality-window means remain close together around `-6` to `-5.6`.

## Root-Cause Decision

The hidden failure is not simply "the event head lacks gradients." It is a
training-support and event-transport mismatch:

- M3-S2 optimizes a grouped event-mass objective over the executable event
  logits.
- The same stochastic policy is also used to collect on-policy trajectories.
- A prewindow per-step probability around `0.5%` is enough to destroy most
  one-shot support before quality-window evidence can be collected.
- Once support is destroyed, the state machine correctly closes the legal fire
  mask, but the learner loses the positive rows needed to sharpen the boundary.

The current `early_mass_budget = 0.02` has the right interpretation, but the
existing penalty is too weak to force the per-step prewindow hazard down to the
required `1 / horizon` scale. More importantly, coefficient tuning alone is not
a robust fix when the same sampled policy can erase its own supervision.

## Consequence For Next Work

The next slice should be framed as a model/training contract repair, not as
another coefficient sweep.

Candidate repairs:

1. Add a support-preserving training path that can collect or replay
   quality-window groups under forced hold before the first quality window,
   while still training the executable event logits.
2. Add an event-to-pulse adapter: train a stopping decision separately from the
   sampled Bernoulli transport, then deterministically emit a low-high-low
   executable pulse under `fire_mask`.
3. Strengthen the survival contract so prewindow cumulative hazard is bounded
   directly and logged as a first-class metric, not only as a small quadratic
   excess penalty.
4. Repair reward ordering, but treat that as necessary for timing quality rather
   than sufficient for the no-fire/early-sample support collapse.

M2 memory should not be released as the primary fix unless it explicitly owns
this stopping-to-pulse adapter or support-preserving collection contract.

## Follow-Up Repair Evidence

Maintained follow-up:
[m3_s2_support_preserving_collect_probe_20260606.md](m3_s2_support_preserving_collect_probe_20260606.md).

The whole-window support-preserving collector blocks the diagnosed collection
failure: accepted rollout events stay at `0`, active groups remain present, and
closed-mask rows no longer dominate the final update. This validates the
support-collapse diagnosis.

The behavioral failure remains: deterministic probing after the repair still
records `0` releases with `1080` quality-window steps, and the learned event
logits never cross the deterministic `fire_once` boundary.
