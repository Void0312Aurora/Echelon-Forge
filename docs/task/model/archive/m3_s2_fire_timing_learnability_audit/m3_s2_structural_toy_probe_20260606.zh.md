# M3-S2 结构性 Toy 探针 - 2026-06-06

父级：[README.zh.md](README.zh.md)。

状态：`decisive structural evidence`；grouped M3-S2 objective 在抽象 one-shot
window 任务上可学习，因此剩余失败不只是 loss object 本身。

## 问题

当前 grouped stopping/window objective 在脱离空战环境后，能否学会我们需要的抽象对象？

该对象是：

```text
prewindow:      将累计事件风险压到很小预算以下
quality window: 在窗口内放置至少一次事件
boundary:       在 quality window 内跨过 deterministic fire_once mode
constraint:     quality window 前不能跨边界
```

该测试移除了飞机动力学、reward shaping、C2/ROE 状态转移、rollout collection 与 PPO credit。
剩下的机制只有 ordered logits 上的 M3-S2 grouped survival/event-mass loss。

## 工具

新增诊断：

```text
tools/diagnostics/fire_timing_fault_localization_probe.py --mode structural_toy
```

该 probe 运行两个 toy 模型：

- `free_logits`：每个时间步一个可学习 logit。它直接测试 loss surface。
- `mlp`：一个小 MLP，输入显式 normalized age 与 quality-window features。它测试当所需状态可见时，
  简单参数化 actor 是否能学出 discriminator。

两者都使用 active M3-S2 系数：

```text
early_mass_coef = 2.0
early_mass_budget = 0.02
early_survival_coef = 8.0
window_delay_coef = 0.5
window_deadline_coef = 0.5
window_deadline_steps = 64
```

## 验证

```bash
python -m compileall -q \
  tools/diagnostics/fire_timing_fault_localization_probe.py --mode structural_toy \
  tests/training/test_fire_timing_fault_localization_contracts.py
```

结果：pass。

```bash
python -m pytest tests/training/test_fire_timing_fault_localization_contracts.py -q
```

结果：`2 passed`。

## 长 Toy Run

命令：

```bash
./.venv/bin/python tools/diagnostics/fire_timing_fault_localization_probe.py --mode structural_toy \
  --model both \
  --prewindow-steps 800 \
  --quality-steps 1080 \
  --train-steps 3000 \
  --learning-rate 0.01 \
  --json-out experiments_tmp/m3s2_structural_toy_probe_20260606.json
```

Artifact：

```text
experiments_tmp/m3s2_structural_toy_probe_20260606.json
```

最终指标：

| Model | Pass | Prewindow cumulative risk | Prewindow max logit | Quality max logit | First quality crossing | Quality boundary crosses | Window mass |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `free_logits` | yes | `0.009140485` | `-11.375060` | `2.393876` | `800` | `2` | `0.990859449` |
| `mlp` | yes | `0.000005254` | `-17.986553` | `9.366981` | `800` | `1080` | `0.999994695` |

两种模型的初始状态均为 `initial_logit = -6.0`，对应每步概率约 `0.00247`，在 `800`
个 prewindow steps 上是不安全的 `0.862` 累计风险。toy optimizer 能把 prewindow logits
压到 `1 / horizon` 尺度以下，同时在 quality window 跨过边界。

## 判定

这强力否定了“grouped M3-S2 loss 无法表达所需 one-shot window pulse”的假设。它可以表达。

因此，active air-combat failure 应定位到集成路径，而不是纯 loss object：

- rollout/sidecar construction 可能仍呈现与 toy support contract 不一致的数据分布；
- actor event update 可能没有训练承载 quality-window discriminator 的表示层；
- PPO/shared updates 可能覆盖或稀释辅助 event boundary；
- executable action transport 仍可能需要 stopping-to-pulse adapter；
- reward ordering 仍是单独的 timing-quality 缺陷，但它不是解释本结构 toy 结果所必需的因素。

下一步分析应检查真实 M3-S2 update path 的参数与特征层级：quality-window features 是否真的改变
`fire_once` logit，selected update parameters 是否包含使用这些特征所需的层，以及 post-update
logits 是否被后续 PPO update cycle 覆盖。
