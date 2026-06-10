# M3-S2 窗口分类器短训

状态：`2026-06-06` implementation slice 已接线；behavioral fire timing 仍 held。

父级：

- [M3-S2 开火时机可学习性审计](README.zh.md)

## 边界

本切片实现了当前建模转向：空战开火时机应先学习识别高质量发射窗口，再把窗口判定转换为
executable one-shot fire pulse。

它不宣称 learned fire timing 成功。本次验收问题是：能否把显式窗口分类器接入、训练并与旧的
cumulative-hazard / stopping-head objective 分开观察。

## 实现内容

- `HierarchicalMoEExecutionPolicy` 新增 dedicated `m3_window_classifier_head`，
  支持可选 LayerNorm 与独立 optimizer lane。
- `hybrid_event_use_m3_window_classifier_head` 会将 executable hybrid hold/fire logit delta
  路由到分类器输出。若分类器与 stopping-head adapter 同时开启，分类器 adapter 是 active
  executable path。
- `AdaptiveKLPPO` 新增 `m3s2_window_classifier_*` 参数。辅助目标复用已有 grouped sidecar rows：
  - 正例：合法且 supported 的 `quality_mask = true` rows；
  - 负例：合法且 supported、但不在 quality window 内的 rows。
- 分类器 loss 是 balanced BCE，加可选 negative-logit ceiling 与 positive-logit floor。
- nonfinite probe 的替换训练循环已同步，使 active run 在 `diagnostics.nonfinite_probe = true`
  时也会执行并记录分类器更新。

## 验证

```bash
python -m compileall -q \
  python/rl/policy_algo/policies.py \
  python/rl/policy_algo/ppo_adaptive_kl.py \
  python/rl/support/nonfinite_probe.py \
  tests/policy/test_execution_policy_surface.py \
  tests/policy/test_auxiliary_training_updates.py \
  tests/training/test_air_combat_training_entry_contracts.py
```

```bash
python -m json.tool \
  examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_m3s2_event_window_state_completed_world_batch_probe_v1.json \
  >/dev/null
```

```bash
python -m pytest \
  tests/policy/test_execution_policy_surface.py \
  tests/policy/test_auxiliary_training_updates.py \
  tests/training/test_air_combat_training_entry_contracts.py \
  -q
```

结果：`83 passed in 33.08s`。

Focused classifier 验收：

- Policy tests 确认分类器默认关闭，开启后有独立 optimizer lane，并可覆盖 executable
  fire-event logits。
- PPO warmup tests 确认一个 quality mask 为 `(False, False, True, True)` 的 grouped sidecar
  能训练分类器，使 positive logits 高于 negative logits，且只有分类器参数改变。

## 短训

```bash
env PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python \
  train.py \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_m3s2_event_window_state_completed_world_batch_probe_v1.json \
  --output_base experiments_tmp \
  --run_name m3s2_window_classifier_8k_20260606_r1
```

Artifacts：

- `experiments_tmp/m3s2_window_classifier_8k_20260606_r1/final_model.zip`
- `experiments_tmp/m3s2_window_classifier_8k_20260606_r1/m3s2_deterministic_probe.json`
- `experiments_tmp/m3s2_window_classifier_8k_20260606_r1/m3s2_stochastic_probe.json`

关键训练观察：

| Step | Positive rows | Negative rows | Positive logit mean | Negative logit mean | 备注 |
| ---: | ---: | ---: | ---: | ---: | --- |
| 2048 | 0 | 1024 | 0.0 | -0.266 | 该 rollout batch 没有 quality-window positives。 |
| 3072 | 900 | 124 | -0.0909 | -0.0991 | 出现正例，但分离很弱。 |
| 4096 | 900 | 124 | 0.0274 | 0.0146 | accuracy 主要来自类别不平衡，不代表边界质量。 |
| 5120 | 900 | 124 | 0.0119 | 0.0100 | 边界接近随机。 |
| 6144 | 900 | 124 | 0.00854 | 0.00656 | 边界接近随机。 |
| 7168 | 200 | 824 | 0.0239 | -0.0124 | 负例变多，但分离仍弱。 |
| 8192 | 0 | 1024 | 0.0 | -0.387 | 最后一批再次没有正例。 |

## Learned-Policy Probes

Deterministic probe：

```bash
env PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python \
  tools/diagnostics/air_combat_stage0_process_probe.py \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_m3s2_event_window_state_completed_world_batch_probe_v1.json \
  --mode model \
  --model experiments_tmp/m3s2_window_classifier_8k_20260606_r1/final_model.zip \
  --device cuda \
  --episodes 1 \
  --max_steps 2400 \
  --json_out experiments_tmp/m3s2_window_classifier_8k_20260606_r1/m3s2_deterministic_probe.json
```

Stochastic probe 使用同一命令并追加 `--stochastic`。

| Probe | Release count | First release | Quality-window rows | Event fire prob mean in open mask | Final missiles |
| --- | ---: | ---: | ---: | ---: | ---: |
| deterministic | 0 | n/a | 1080 | 0.262445 | 4 |
| stochastic | 1 | 5 | 0 | 0.253977 | 3 |

## 诊断

窗口分类器切片已经接线，并且在 focused synthetic sidecar test 中可训练；但 active 8k
Stage-1 run 行为上仍失败：

- deterministic policy 在 `1080` 个 quality-window rows 下仍没有发射；
- stochastic policy 在第 `5` 步提前发射，当时还没有任何 quality-window row；
- online classifier logits 没有形成稳定 prewindow-vs-quality boundary；
- rollout batches 在“没有正例”和“正例严重占优”之间摆动。

这把当前根因进一步收窄：问题已经不只是“模型没有单独的窗口概念”。下一步应直接审计分类器
训练分布和更新目标：

1. sidecar batch 是否应按 group/window 级别重平衡，而不是按 row 级别训练；
2. 分类器是否应先在 offline forced-hold window dataset 上预训练，再接入 executable action；
3. active process probe 是否需要直接记录 `m3_window_classifier` logits，而不是仅通过 event
   adapter 间接观察。
