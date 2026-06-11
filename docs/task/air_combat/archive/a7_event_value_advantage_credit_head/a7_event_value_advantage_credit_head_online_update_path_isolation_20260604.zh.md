# A7 在线更新路径隔离

状态：`2026-06-04` pass；online blocker 已定位，A7 仍 held。

父级：[README.zh.md](README.zh.md)。

## 目的

`A7-EVC-T` 已证明 S final-model 的固定批不缺状态、正标签或 credit-head
容量：只更新 credit head 就能把 `LEGAL_OPEN_QUALITY` rows 拟合成正
advantage。本 slice 隔离为什么这个本地可拟合信号没有在在线 PPO 训练中保留下来。

本轮检查的怀疑对象包括：

- PPO/shared updates 是否干扰 A7 credit learning；
- loss scaling 与全局 gradient clipping 是否饿死 credit head；
- delta alignment 是否把 event logits 拉向错误方向；
- stochastic rollout distribution 是否移除了 legal-open positives；
- HMoE routing/capacity 是否是更深层 blocker。

## 诊断

新增：

- `tools/diagnostics/event_credit_head_probe.py --mode online_update`

该 probe 分开记录两个上下文：

1. deterministic fixed S batch：复现 T 断点，并保留 legal-open positives；
2. stochastic online rollout batch：包含 PPO-style GAE/returns、actions、
   old log-probs、A7 labels，以及 PPO/A7 gradient 对照。

主命令：

```bash
python tools/diagnostics/event_credit_head_probe.py --mode online_update \
  --episodes 4 \
  --max_steps 640 \
  --online_episodes 4 \
  --online_max_steps 640 \
  --batch_size 512 \
  --eval_batch_size 512 \
  --update_steps 8 \
  --device auto \
  --json_out experiments_tmp/a7_online_update_path_probe_20260604.json
```

Credit-head-only 8-step 对照：

```bash
python tools/diagnostics/event_credit_head_probe.py --mode offline_fit \
  --episodes 4 \
  --max_steps 640 \
  --fit_steps 8 \
  --fit_batch_size 512 \
  --eval_batch_size 512 \
  --fit_lr 0.00018 \
  --scopes credit_head \
  --json_out experiments_tmp/a7_credit_head_only_8step_probe_20260604.json
```

验证：

```bash
python -m compileall -q tools/diagnostics/event_credit_head_probe.py tools/diagnostics/event_credit_head/online_update.py
```

观测：pass。

实验输出保留在 `experiments_tmp/`，不得 staging。

## 固定批结果

Deterministic fixed batch 仍与 T 一致：

| 指标 | 值 |
| --- | ---: |
| rollout steps | `2560` |
| fire-open steps | `2516` |
| launch-open steps | `1356` |
| active labels | `2516` |
| `PREWINDOW` negatives | `1160` |
| `LEGAL_OPEN_QUALITY` positives | `1356` |
| initial legal-open advantage | `-0.8536` |
| initial legal-open event-logit delta | `-1.0071` |
| initial legal-open event-fire probability | `0.2676` |
| initial legal-open deterministic fire fraction | `0.0` |

512-row minibatch 梯度范数：

| Loss | Total norm | Clip scale | Credit head norm / effective | Event head norm / effective | Actor MLP norm / effective | Features norm / effective |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| A7 value | `1.1515` | `0.4342` | `1.0942` / `0.4751` | `0.0000` / `0.0000` | `0.0831` / `0.0361` | `0.3491` / `0.1516` |
| A7 delta-align | `0.6747` | `0.7411` | `0.0000` / `0.0000` | `0.2984` / `0.2211` | `0.1255` / `0.0930` | `0.5109` / `0.3786` |
| A7 combined | `1.1992` | `0.4170` | `1.0942` / `0.4562` | `0.2984` / `0.1244` | `0.0631` / `0.0263` | `0.2417` / `0.1008` |

梯度方向检查：

| 对照 | 参数组 | Cosine |
| --- | --- | ---: |
| delta-align vs value | actor MLP | `-0.8954` |
| delta-align vs value | features | `-0.9097` |
| delta-align vs value | all available grads | `-0.2209` |
| combined vs value | actor MLP | `-0.4642` |
| combined vs value | features | `-0.4786` |
| combined vs value | all available grads | `0.8360` |

解释：

- A7 value loss 不直接更新 event head，但会更新 actor MLP 与 feature
  extractor。因此即使没有 explicit event-head gradient，共享表示更新也会改变
  event logits。
- Delta alignment 不更新 credit head，确认了预期的 `advantage.detach()` 分离。
- Delta alignment 与 A7 value loss 在 actor/features 中强烈相反。这是
  representation-coupling fault，不只是 scalar coefficient 问题。

固定批 8 步更新：

| Update path | Legal-open advantage before | Legal-open advantage after | Positive sign frac after | Legal-open event-logit delta after | Deterministic fire frac after |
| --- | ---: | ---: | ---: | ---: | ---: |
| credit head only | `-0.8536` | `-0.5095` | `0.0` | probe 未改变 | probe 未改变 |
| A7 value, normal online graph | `-0.8536` | `-0.0651` | `0.0` | `-2.6259` | `0.0` |
| A7 combined, normal online graph | `-0.8536` | `-0.2823` | `0.0` | `-0.3088` | `0.0` |

这确认了一个更微妙的失败模式：允许 A7 value loss 反传进 actor
representation，确实能比 credit-head-only 8 步更快移动 credit advantage，
但也可能破坏或扰动 event-logit surface。Delta alignment 可以部分修复
event-logit delta，但它在 shared representation 空间里与 value gradient 冲突。

## 在线 PPO 结果

Stochastic online rollout batch 与 deterministic fixed batch 不同：

| 指标 | 值 |
| --- | ---: |
| rollout steps | `2560` |
| fire-open steps | `19` |
| launch-open steps | `1356` |
| accepted events | `4` |
| accepted steps | `[6, 46, 9, 2]` |
| active labels | `1375` |
| positive labels | `1356` |
| `PREWINDOW` negatives | `15` |
| `EARLY_ACCEPTED` negatives | `4` |
| `SHADOW_QUALITY` positives | `1356` |

Online batch 上 PPO/A7 梯度对照：

| Loss | Total norm | Clip scale | Credit head norm / effective | Event head norm / effective | Features norm / effective | Value-net norm / effective |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| A7 combined alone | `5.0605` | `0.0988` | `4.9141` / `0.4855` | `0.5839` / `0.0577` | `0.8597` / `0.0849` | `0.0000` / `0.0000` |
| PPO alone | `356.3418` | `0.001403` | `0.0000` / `0.0000` | `0.0274` / `0.000038` | `142.4263` / `0.1998` | `314.2057` / `0.4409` |
| PPO + A7 | `356.4866` | `0.001403` | `4.9141` / `0.00689` | `0.6047` / `0.00085` | `142.7010` / `0.2001` | `314.2057` / `0.4407` |

PPO-alone 对 `hybrid_event_credit_head` 的直接梯度为 `0.0`。因此 PPO
不会直接覆盖 credit-head 参数。blocker 是 PPO 的 value/feature/value-net
梯度支配了共享全局梯度范数，使单次 PPO-style
`clip_grad_norm_(self.policy.parameters(), 0.5)` 将 A7 credit-head 的有效梯度
从 A7-alone 训练中的约 `0.4855` 压到 PPO+A7 中的约 `0.00689`。在该诊断批上，
head 的 clipped update budget 大约被压低 70 倍。

真实 S TensorBoard scalars 与此一致：

| Scalar | 观测 |
| --- | --- |
| `train/value_loss` | max `6526.7822`；final `0.2110` |
| `train/loss` | max `4348.9019`；final `0.4425` |
| `a7/event_credit_loss` | max `1.0749`；final `0.3186` |
| `a7/event_credit_advantage_mean` | 从约 `-0.0442` 漂移到 `-0.9239` |
| `a7/event_credit_target_positive_frac` | final `0.6445` |
| `a7/evc_src_legal_open_quality_positive_count_mean` | final `330.0` |

这说明 online run 不只是“短训不够”。它是在一个 early/value-dominated PPO
阶段可以先塑造负 event-credit surface，而后续正样本 A7 窗口没有足够受保护
update budget 将其拉回来的机制下训练。

## 怀疑对象判定

| 怀疑对象 | U 发现 | 状态 |
| --- | --- | --- |
| 缺失正标签 | fixed deterministic batch 有 `1356` legal-open positives；online stochastic batch 有 `1356` shadow positives | 排除为 primary |
| 缺失显式状态 | T/S 已暴露 v2 state；U 仍复现 fixed-batch separability | 排除为 primary |
| Credit-head 容量 | T 可拟合固定批；U 确认 credit-head gradients 非零 | 排除为 primary |
| PPO 直接覆盖 credit head | PPO-alone credit-head gradient 为 `0.0` | 排除 |
| Loss scaling / global clipping | PPO+A7 clip scale 约 `0.0014`；credit-head effective norm 降到 `0.00689` | 确认为 primary |
| Shared actor/feature drift | A7 value gradients 进入 actor/features，并可恶化 event-logit delta | 确认为 primary |
| Delta-align 拖拽 policy | delta-align 不碰 credit head，但在 actor/features 中与 value loss 冲突 | 确认为 contributing |
| Rollout non-stationarity | deterministic legal-open rows 与 stochastic shadow rows 差异明显 | 确认为 contributing |
| HMoE hierarchy gap | HMoE 有小梯度，但 U 将失败定位在 hierarchy-attributable gate 之前 | watch item，非当前 primary |

## 结论

结构性故障是 online update-contract bug：

```text
A7 credit 被实现为同一次 PPO backward、同一次 global clip、同一套 shared
actor representation 与同一次 optimizer step 中的 auxiliary loss。

这会让本地可分离的 event-credit target，与 PPO value loss 和 event-logit
distillation 竞争同一套 representation 与 gradient budget。
```

因此下一步不应是 coefficient-only training。下一有界合同应将 A7 credit
learning 从 shared PPO update 中解耦：

- 让 A7 value update 只更新 credit head，或提供独立 credit encoder/critic lane，
  并 detach actor features；
- 为 A7 credit 使用独立 optimizer step 与独立 gradient clipping budget，而不是
  PPO global clip；
- 将 delta alignment 变成 credit sign 可靠后的 second-stage / gated update，
  并限制其 write surface，避免在 shared actor representation 中与 A7 value 对抗；
- 保持 A3/A5 masks 与 one-shot event authority。

M2 与 HMoE redesign 继续 held。U 将当前直接 root cause 收窄到 A7/PPO
update contract，而不是 memory、labels、state 或 credit-head capacity。
