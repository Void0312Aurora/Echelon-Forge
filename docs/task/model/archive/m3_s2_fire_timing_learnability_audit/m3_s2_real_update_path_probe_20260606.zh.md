# M3-S2 真实更新路径探针 - 2026-06-06

父级：[README.zh.md](README.zh.md)。

状态：`root-cause localization evidence`；真实 M3-S2 更新能到达 executable event 参数，
但当前会同时压低 prewindow 与 quality-window logits，而不是形成 quality-window boundary。

## 问题

structural toy probe 已经说明 grouped M3-S2 loss 能学会抽象 one-shot window pulse。
那么真实 Stage-1 policy 为什么仍然不开火？

本探针追问：当前 M3-S2 auxiliary update 应用于真实 Stage-1 observations 与真实 policy
parameters 时，是否会把 executable `fire_once` logit 往正确方向移动？

## 工具

新增诊断：

```text
tools/diagnostics/m3s2_real_update_path_probe.py
```

该 probe：

- 加载 M3-S2 support-preserving checkpoint；
- 采集 forced-hold Stage-1 序列，避免 one-shot support 被消耗；
- 使用与 training sidecar 相同的 legal-open age 与 launch-window 规则重建 M3-S2 groups；
- 对真实 policy 参数执行离线 M3-S2 auxiliary updates；
- 对比 update 前后 prewindow 与 quality-window rows 上的 `fire_once` logit/probability。

测试覆盖：

```bash
python -m pytest tests/training/test_fire_timing_fault_localization_contracts.py -q
```

结果：`2 passed`。

## Artifacts

四步 probe：

```text
experiments_tmp/m3s2_real_update_path_probe_20260606_4step.json
```

四十步 current-scope probe：

```text
experiments_tmp/m3s2_real_update_path_probe_20260606_40step_current.json
```

200-step exploratory run 因两个完整 scope 对交互诊断过慢而中止；该部分不作为证据。

## Collection

forced-hold collection 产生了真实 supported rows：

| Metric | Value |
| --- | ---: |
| `steps` | `2400` |
| `group_count` | `1` |
| `legal_rows` | `1880` |
| `quality_rows` | `1040` |
| `accepted_count` | `0` |
| `launch_min_age` | `32` |

因此本 probe 可排除“没有 quality rows”的解释。

## 初始真实 Logits

离线 update 前：

| Subset | Count | Logit mean | Logit max | Prob mean | Cumulative risk | Boundary count |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Prewindow | `840` | `-5.719286` | `-5.707861` | `0.003271` | `0.936229` | `0` |
| Quality | `1040` | `-5.721806` | `-5.719494` | `0.003263` | `0.966600` | `0` |

policy 几乎无法区分 prewindow 与 quality rows：quality logits 甚至略低于 prewindow logits。

## 四步 Update

这对应 active config 中的 `m3s2_event_window_separate_update_steps = 4`。

| Scope | Selected groups | Quality logit max delta | Prewindow logit max delta | Quality boundary after | Loss delta |
| --- | --- | ---: | ---: | ---: | ---: |
| `current` | `action_net`, `actor_mlp`, `event_head` | `-0.265521` | `-0.264529` | `0` | `-2.033200` |
| `current_plus_features` | `action_net`, `actor_mlp`, `event_head`, `features` | `-0.428197` | `-0.431909` | `0` | `-2.979543` |

该 update 有大梯度，也降低了 loss，但方式是几乎整体降低 hazard。它没有把 quality-window
logits 往 deterministic boundary 抬高。

## 四十步 Current-Scope Update

current-scope 离线更新四十步后的结果：

| Subset | Logit mean delta | Logit max delta | Prob mean delta | Cumulative risk delta | Boundary after |
| --- | ---: | ---: | ---: | ---: | ---: |
| Prewindow | `-1.804984` | `-1.794477` | `-0.002732` | `-0.571688` | `0` |
| Quality | `-1.794544` | `-1.789550` | `-0.002719` | `-0.534545` | `0` |

该趋势持续存在：真实更新主要学到的是“到处更少开火”。它确实让 quality 相对 prewindow
略有分离，但这个分离远小于到 `fire_once` 边界的距离。

## 判定

当前失败不再适合描述为 missing gradients 或 missing support。本 probe 显示：

- 真实 M3-S2 有 supported quality rows；
- auxiliary update 到达 `action_net`、`actor_mlp` 与 `event_head`；
- 梯度很大，参数确实移动；
- loss 下降；
- 但 quality logits 跟 prewindow logits 一起下降，且从未跨过 deterministic mode。

局部化后的失败是：真实 policy update path 中的 feature-to-logit discriminator 没有形成。
模型可以通过共享下移来降低累计 hazard，而这比学习尖锐的 prewindow/quality separator 更容易。
下一步不应继续做 coefficient sweep，而应显式约束或审计 discriminator：

1. 在真实 rows 上增加 contrastive/margin 项：
   `quality_logit - prewindow_logit > margin`；
2. 审计显式 mission-observation quality features 是否穿过 temporal feature extractor 和 actor MLP；
3. 将 event boundary adapter 与 sampled Bernoulli hazard 分开，让 learner 先表示 stopping，
   再转换为 executable pulse；
4. 之后再回头检查 PPO overwrite 或 M2 memory。
