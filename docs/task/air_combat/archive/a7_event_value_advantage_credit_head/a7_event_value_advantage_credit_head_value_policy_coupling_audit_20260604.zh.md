# A7 Value/Policy 耦合审计

状态：`2026-06-04` 通过；断点已验证，A7 仍 held。

父项目：[README.zh.md](README.zh.md)。

## 目的

本切片验证 S 之后怀疑的断点：

```text
LEGAL_OPEN_QUALITY 正标签和显式状态都已经存在，
但学习后的模型仍给出负的 Q_fire_once - Q_hold。
```

问题是：失败发生在 label/value 对象本身，还是发生在在线 PPO、共享表征、
delta alignment 与 event policy 的后续耦合链路里。

## 诊断方式

新增：

- `tools/diagnostics/event_credit_head_probe.py --mode offline_fit`

探针流程：

1. 加载 S final model；
2. 用与 PPO rollout collection 相同的 policy observation fire-mask /
   launch-window 路径采集固定 deterministic rollout batch；
3. 从固定 batch 重建 A7 first-event labels；
4. 冻结除指定诊断 scope 以外的 policy 参数；
5. 只用 A7 supervised credit objective 做离线拟合；
6. 对比拟合前后各 source 的 advantage 符号。

主实验：

```bash
python tools/diagnostics/event_credit_head_probe.py --mode offline_fit \
  --episodes 4 \
  --max_steps 640 \
  --fit_steps 1200 \
  --fit_batch_size 512 \
  --eval_batch_size 512 \
  --scopes credit_head,credit_head_actor_mlp \
  --json_out experiments_tmp/a7_credit_head_offline_fit_probe_20260604.json
```

训练预算对照：

```bash
python tools/diagnostics/event_credit_head_probe.py --mode offline_fit \
  --episodes 4 \
  --max_steps 640 \
  --fit_steps 256 \
  --fit_batch_size 512 \
  --eval_batch_size 512 \
  --fit_lr 0.00018 \
  --scopes credit_head \
  --json_out experiments_tmp/a7_credit_head_offline_fit_training_budget_probe_20260604.json
```

```bash
python tools/diagnostics/event_credit_head_probe.py --mode offline_fit \
  --episodes 4 \
  --max_steps 640 \
  --fit_steps 256 \
  --fit_batch_size 512 \
  --eval_batch_size 512 \
  --fit_lr 0.000072 \
  --scopes credit_head \
  --json_out experiments_tmp/a7_credit_head_offline_fit_valuecoef_budget_probe_20260604.json
```

## 结果

固定 batch 并不缺少来源信号：

| 指标 | 数值 |
| --- | ---: |
| rollout steps | `2560` |
| fire-open steps | `2516` |
| launch-open steps | `1356` |
| accepted releases | `0` |
| active A7 labels | `2516` |
| pre-window negatives | `1160` |
| `LEGAL_OPEN_QUALITY` positives | `1356` |

S final model 在同一 batch 上的初始符号：

| 子集 | advantage mean | 正号比例 |
| --- | ---: | ---: |
| all active labels | `-0.8553` | `0.000` |
| pre-window negatives | `-0.8573` | `0.000` |
| `LEGAL_OPEN_QUALITY` positives | `-0.8536` | `0.000` |

离线 supervised fit：

| 拟合范围 / 预算 | legal-open advantage mean | legal-open 正号比例 | pre-window advantage mean | pre-window 负号比例 |
| --- | ---: | ---: | ---: | ---: |
| only credit head, `1200` steps, lr `1e-3` | `+0.6417` | `1.000` | `-0.9382` | `0.734` |
| credit head + actor MLP, `1200` steps, lr `1e-3` | `+4.2450` | `0.976` | `-11.7457` | `0.983` |
| only credit head, `256` steps, lr `1.8e-4` | `+0.0292` | `1.000` | `-0.0329` | `0.592` |
| only credit head, `256` steps, lr `7.2e-5` | `+0.0083` | `1.000` | `-0.0142` | `0.685` |

## 判定

断点属实，但它不在直接 label/value 对象内部：

- `LEGAL_OPEN_QUALITY` 正样本在固定 deterministic rollout batch 中真实存在。
- S final model 在同一 batch 上复现了 learned probe 中的负 legal-open
  advantage。
- 只放开 `hybrid_event_credit_head`，冻结其余 policy 参数，就足以在同一
  latent 表征上把所有 legal-open 正样本翻成正 advantage。
- 即使用折算 `value_coef` 后更保守的预算，legal-open rows 也能在离线环境中
  翻到零上方。

因此当前失败已经越过了 label construction、credit head 容量和当前 latent
可分性的层面。更可能的失败区间是在线联合训练耦合链路：PPO/shared 更新、
on-policy rollout 分布漂移、组合目标中的 loss scaling，或 delta/event-head
distillation 持续抵消或带偏了 credit 信号，使最终 checkpoint 仍保持负
advantage。

这也收窄了 M2 问题。真正的记忆机制长期上仍可能有价值，但 S/T 证据说明当前
batch 已经有显式状态和可分 credit 信号；此时直接释放 M2 会绕开一个已确认的
在线耦合故障。

## 下一步

不要再做盲目的系数训练。下一步应直接检查在线 update path：

- 记录进入 `hybrid_event_credit_head` 的各 loss 梯度范数；
- 对比每个 PPO train phase 前后的 credit-head 参数漂移；
- 跑一个只更新 A7 credit head、冻结 PPO/shared/event-head 的单 rollout
  训练变体；
- 再判断修复是 scheduling、optimizer/loss-scale contract，还是更深的
  policy/value coupling redesign。

## 验证

```bash
python -m compileall -q tools/diagnostics/event_credit_head_probe.py tools/diagnostics/event_credit_head/offline_fit.py
```

结果：通过。

实验输出保留在 `experiments_tmp/`，不得纳入 staging。
