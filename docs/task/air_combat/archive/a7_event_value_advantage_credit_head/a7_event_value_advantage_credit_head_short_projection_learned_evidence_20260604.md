# A7 Short Projection Learned Evidence

Status: `2026-06-04` `A7-EVC-N Short Projection Learned Evidence` pass as
valid evidence, but held as a learned-policy outcome. The projected
legal-open prototype is enabled and instrumented, but the short learned run
does not activate projected credit rows and does not meet first-shot timing
acceptance.

Parent: [README.md](README.md). Prototype:
[a7_event_value_advantage_credit_head_projected_legal_open_credit_prototype_20260604.md](a7_event_value_advantage_credit_head_projected_legal_open_credit_prototype_20260604.md).

## Scope

This slice runs the maintained A7 active config after `A7-EVC-M` and probes the
final policy in deterministic and stochastic modes. It asks whether projected
legal-open credit changes learned behavior relative to the post-J
shadow-quality repair evidence.

It does not release M2, HMoE redesign, missile physics, Pk/fuze/damage
authority, `2v2`, self-play, or real-world doctrine claims. `experiments_tmp`
artifacts remain unstaged.

## Diagnostic Repair Before Evidence

Two diagnostic issues were fixed before accepting the N evidence:

- `NonFiniteTrainingProbe` patches the PPO `train()` path used by the active A7
  config. Its patched path did not record projection stats from
  `FirstEventCreditLoss`, so projection could be enabled without any scalar
  evidence of active projected rows.
- Long projection logger names collided under SB3 stdout truncation. Projection
  metrics now use short tags:
  `a7/evc_proj_enabled`, `a7/evc_proj_value_coef`,
  `a7/evc_proj_delta_coef`, `a7/evc_proj_active_count_mean`,
  `a7/evc_proj_unsupported_count_mean`, `a7/evc_proj_advantage_mean`, and
  `a7/evc_proj_delta_mean`.

Regression coverage:
`tests/policy/test_auxiliary_training_updates.py::AuxiliaryTrainingUpdateTests::test_nonfinite_probe_records_a7_projection_credit_stats`.

## Valid Training Run

Run:
`experiments_tmp/a7_projection_credit_32k_20260604_r3`

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python train.py \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_a7_event_credit_launch_window_shaped_world_batch_probe_v1.json \
  --output_base experiments_tmp \
  --run_name a7_projection_credit_32k_20260604_r3 \
  --n_envs 4 \
  --torch_threads 1 \
  --seed 20260691
```

Final model:
`experiments_tmp/a7_projection_credit_32k_20260604_r3/final_model.zip`

TensorBoard scalar check from
`experiments_tmp/a7_projection_credit_32k_20260604_r3/logs/PPO_1/`:

| Scalar | Final step | Final value |
| --- | ---: | ---: |
| `a7/event_credit_loss` | `32768` | `0.322098` |
| `a7/event_credit_active_count_mean` | `32768` | `450.0` |
| `a7/event_credit_target_positive_frac` | `32768` | `0.599887` |
| `a7/event_credit_advantage_mean` | `32768` | `-0.962887` |
| `a7/evc_proj_enabled` | `32768` | `1.0` |
| `a7/evc_proj_active_count_mean` | `32768` | `0.0` |
| `a7/evc_proj_unsupported_count_mean` | `32768` | `0.0` |
| `a7/evc_proj_advantage_mean` | `32768` | `0.0` |
| `a7/evc_proj_delta_mean` | `32768` | `0.0` |

Interpretation: the ordinary A7 event-credit path is live, but the projected
credit branch has no active rows in this learned run. The projection is enabled
and supported rows are not being rejected; instead, no eligible projected rows
reach the projection loss.

## Probe Commands

Deterministic:

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python \
  tools/diagnostics/air_combat_stage0_process_probe.py \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_a7_event_credit_launch_window_shaped_world_batch_probe_v1.json \
  --mode model \
  --model experiments_tmp/a7_projection_credit_32k_20260604_r3/final_model.zip \
  --episodes 1 \
  --seed 20260692 \
  --max_steps 2400 \
  --json_out experiments_tmp/a7_projection_credit_32k_20260604_r3/a7_projection_deterministic_probe.json \
  --csv_out experiments_tmp/a7_projection_credit_32k_20260604_r3/a7_projection_deterministic_probe.csv
```

Stochastic:

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python \
  tools/diagnostics/air_combat_stage0_process_probe.py \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_a7_event_credit_launch_window_shaped_world_batch_probe_v1.json \
  --mode model \
  --model experiments_tmp/a7_projection_credit_32k_20260604_r3/final_model.zip \
  --episodes 3 \
  --seed 20260692 \
  --max_steps 2400 \
  --stochastic \
  --json_out experiments_tmp/a7_projection_credit_32k_20260604_r3/a7_projection_stochastic_probe.json \
  --csv_out experiments_tmp/a7_projection_credit_32k_20260604_r3/a7_projection_stochastic_probe.csv
```

## Deterministic Probe

Source:
`experiments_tmp/a7_projection_credit_32k_20260604_r3/a7_projection_deterministic_probe.json`

| Metric | Observed |
| --- | ---: |
| Episodes | `1` |
| Fire requests | `0` |
| Releases | `0` |
| Final missiles | `4` |
| Open-window steps | `1880` |
| Open-window fire probability mean / max | `0.251826` / `0.261581` |
| Policy event fire probability mean / max | `0.197264` / `0.261581` |
| A7 prewindow / quality steps | `800` / `1080` |
| A7 prewindow cumulative fire probability | `1.0` |
| A7 prewindow advantage mean | `-0.866903` |
| A7 quality-window advantage mean | `-0.865751` |
| Advantage positive frac, prewindow / quality | `0.0` / `0.0` |
| Advantage negative frac, prewindow / quality | `1.0` / `1.0` |

Deterministic behavior remains held: the policy does not request `fire_once`,
and the quality-window event-credit advantage still prefers `hold`.

## Stochastic Probe

Source:
`experiments_tmp/a7_projection_credit_32k_20260604_r3/a7_projection_stochastic_probe.json`

| Episode | First release step | Releases | Authorized | Violations | Repeat releases | Budget violations | Final missiles | A7 open steps before release | Prewindow advantage mean |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `0` | `2` | `1` | `1` | `0` | `0` | `0` | `3` | `0` | `0.0` |
| `1` | `47` | `1` | `1` | `0` | `0` | `0` | `3` | `5` | `-0.878227` |
| `2` | `5` | `1` | `1` | `0` | `0` | `0` | `3` | `1` | `-0.855572` |

Stochastic one-shot discipline remains intact: all sampled releases are
authorized, with no repeat release, no shot-budget violation, and no legacy or
unauthorized fallback. Timing remains held because the releases happen
immediately or very early, before quality-window behavior can be accepted.

## Comparison With J Repair Evidence

| Evidence slice | Deterministic release | Deterministic open-window fire probability | Quality-window advantage | Stochastic release steps | Projection active rows | Interpretation |
| --- | --- | --- | --- | --- | --- | --- |
| `A7-EVC-J repair r1` | `0` releases | mean/max `25.5%` / `27.2%` | `-0.902` | `4`, `43`, `2` | n/a | Shadow-quality labels were restored, but legal-open quality states stayed negative. |
| `A7-EVC-N projection r3` | `0` releases | mean/max `25.2%` / `26.2%` | `-0.866` | `2`, `47`, `5` | `0.0` final mean | M projection did not change accepted timing because no projected rows were active in the learned run. |

N confirms that the focused M implementation is not enough by itself. The next
root-cause question is why the learned-run rollout/loss path produces zero
projected active rows despite projection being enabled and focused tests proving
the projected-loss path.

## Interpretation And Next Direction

Accepted:

- Projection metrics are now visible in both the normal PPO logger and
  `NonFiniteTrainingProbe` patched train path.
- A3/A5 one-shot legality remains intact in stochastic probing.
- The run is valid learned evidence because the ordinary A7 event-credit loss
  is live and projection enablement is recorded.

Held:

- deterministic policy still makes `0` `fire_once` requests;
- stochastic policy still samples early releases;
- quality-window A7 advantage remains negative;
- projected legal-open credit has `0` active rows in the short learned run.

Next bounded slice:

- `A7-EVC-O Projection Eligibility Root-Cause Audit`: inspect the handoff from
  shadow-quality labels to projected legal-open rows in the real rollout/loss
  path, including label source distribution, event-info retention,
  projection eligibility filters, and the nonfinite-probe patched train path.

## Worker Packet

```md
status: pass; held outcome
touched files:
- docs/task/air_combat/a7_event_value_advantage_credit_head/a7_event_value_advantage_credit_head_short_projection_learned_evidence_20260604.md
- docs/task/air_combat/a7_event_value_advantage_credit_head/a7_event_value_advantage_credit_head_short_projection_learned_evidence_20260604.zh.md
commands/outcomes:
- A7 projection r3 32768-step train -> completed
- TensorBoard scalar check -> projection enabled, ordinary event-credit live, projection active count 0
- deterministic probe -> 0 requests, 0 releases, negative quality-window advantage
- stochastic probe -> 3/3 authorized one-shot releases at steps 2, 47, 5 with zero violations
remaining paths:
- A7-EVC-O Projection Eligibility Root-Cause Audit
behavior risks:
- projected credit is enabled but not active in the learned run
- timing remains early or absent, so A7 is not accepted
integration notes:
- experiments_tmp remains unstaged
- A3/A5 legality remains authoritative
- M2, HMoE redesign, missile authority, 2v2, self-play, and doctrine remain held
```
