# A7 Short Projection Learned Evidence

状态：`2026-06-04`，`A7-EVC-N Short Projection Learned Evidence` 作为有效证据
pass，但 learned-policy outcome 继续 held。Projected legal-open prototype 已启用并
完成 instrumented logging；但短训 learned run 没有激活 projected credit rows，也没有达到
first-shot timing 验收门。

父级：[README.zh.md](README.zh.md)。Prototype：
[a7_event_value_advantage_credit_head_projected_legal_open_credit_prototype_20260604.zh.md](a7_event_value_advantage_credit_head_projected_legal_open_credit_prototype_20260604.zh.md)。

## 范围

本切片在 `A7-EVC-M` 后运行维护中的 A7 active config，并用 deterministic / stochastic
两种模式 probe final policy。它要回答的问题是：projected legal-open credit 是否相对
post-J shadow-quality repair evidence 改变 learned behavior。

本切片不释放 M2、HMoE redesign、missile physics、Pk/fuze/damage authority、`2v2`、
self-play 或 real-world doctrine claims。`experiments_tmp` artifacts 不入 staging。

## 证据前诊断修复

接受 N 证据前修复了两个 diagnostic issues：

- `NonFiniteTrainingProbe` 会 patch active A7 config 使用的 PPO `train()` path。其 patched
  path 此前没有记录 `FirstEventCreditLoss` 中的 projection stats，因此 projection 可以
  enabled，却没有任何 active projected rows 的 scalar 证据。
- 过长 projection logger names 会在 SB3 stdout truncation 下碰撞。Projection metrics
  现在使用短 tag：
  `a7/evc_proj_enabled`、`a7/evc_proj_value_coef`、
  `a7/evc_proj_delta_coef`、`a7/evc_proj_active_count_mean`、
  `a7/evc_proj_unsupported_count_mean`、`a7/evc_proj_advantage_mean` 与
  `a7/evc_proj_delta_mean`。

Regression coverage：
`tests/hmoe/test_hmoe_ppo_warmup.py::HMoEPPOWarmupTests::test_nonfinite_probe_records_a7_projection_credit_stats`。

## 有效训练运行

Run：
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

Final model：
`experiments_tmp/a7_projection_credit_32k_20260604_r3/final_model.zip`

TensorBoard scalar check from
`experiments_tmp/a7_projection_credit_32k_20260604_r3/logs/PPO_1/`：

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

解释：ordinary A7 event-credit path 是 live 的，但 projected credit branch 在该 learned
run 中没有 active rows。Projection 已启用，且没有 unsupported rows 被拒绝；更像是没有
eligible projected rows 进入 projection loss。

## Probe 命令

Deterministic：

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

Stochastic：

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

Source：
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

Deterministic behavior 继续 held：policy 不请求 `fire_once`，quality-window event-credit
advantage 仍偏向 `hold`。

## Stochastic Probe

Source：
`experiments_tmp/a7_projection_credit_32k_20260604_r3/a7_projection_stochastic_probe.json`

| Episode | First release step | Releases | Authorized | Violations | Repeat releases | Budget violations | Final missiles | A7 open steps before release | Prewindow advantage mean |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `0` | `2` | `1` | `1` | `0` | `0` | `0` | `3` | `0` | `0.0` |
| `1` | `47` | `1` | `1` | `0` | `0` | `0` | `3` | `5` | `-0.878227` |
| `2` | `5` | `1` | `1` | `0` | `0` | `0` | `3` | `1` | `-0.855572` |

Stochastic one-shot discipline 继续 intact：全部 sampled releases 都是 authorized，
无 repeat release、shot-budget violation、legacy 或 unauthorized fallback。Timing 继续
held，因为 release 发生在立即或非常早的阶段，不能作为 quality-window behavior 验收。

## 与 J Repair Evidence 对照

| Evidence slice | Deterministic release | Deterministic open-window fire probability | Quality-window advantage | Stochastic release steps | Projection active rows | Interpretation |
| --- | --- | --- | --- | --- | --- | --- |
| `A7-EVC-J repair r1` | `0` releases | mean/max `25.5%` / `27.2%` | `-0.902` | `4`、`43`、`2` | n/a | Shadow-quality labels 已恢复，但 legal-open quality states 仍为负。 |
| `A7-EVC-N projection r3` | `0` releases | mean/max `25.2%` / `26.2%` | `-0.866` | `2`、`47`、`5` | `0.0` final mean | M projection 没有改变 accepted timing，因为 learned run 中没有 active projected rows。 |

N 证明 focused M implementation 本身还不够。下一根因问题是：projection 已启用，且 focused
tests 证明 projected-loss path 有效，为什么 learned-run rollout/loss path 的 projected
active rows 仍为 0。

## 解释与下一方向

Accepted：

- Projection metrics 已在 normal PPO logger 与 `NonFiniteTrainingProbe` patched train
  path 中可见。
- Stochastic probing 下 A3/A5 one-shot legality 保持 intact。
- 该 run 是有效 learned evidence：ordinary A7 event-credit loss 是 live 的，projection
  enablement 被记录。

Held：

- deterministic policy 仍为 `0` 个 `fire_once` requests；
- stochastic policy 仍采样 early releases；
- quality-window A7 advantage 仍为负；
- projected legal-open credit 在短训 learned run 中有 `0` active rows。

下一有界切片：

- `A7-EVC-O Projection Eligibility Root-Cause Audit`：检查 shadow-quality labels 到
  projected legal-open rows 的真实 rollout/loss path handoff，包括 label source
  distribution、event-info retention、projection eligibility filters 与 nonfinite-probe
  patched train path。

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
