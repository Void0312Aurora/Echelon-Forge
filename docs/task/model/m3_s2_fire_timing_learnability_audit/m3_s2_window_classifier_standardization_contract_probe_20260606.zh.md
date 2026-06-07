# M3-S2 窗口分类器标准化合同探针 - 2026-06-06

## 目的

本探针跟进 calibrated-standardization 之后的失败：训练日志显示 replay batch
已经能分开正负样本，但 deterministic execution probe 仍然完全不发射。这里要确认
剩余 no-fire 行为来自轨迹错配、随机/确定采样错配，还是更深的 classifier/head 合同问题。

## 诊断改动

- `tools/diagnostics/m3s2_real_update_path_probe.py` 新增
  `--collector-action model_event_hold`。
- `model_event_hold` 保留模型动作，只把 hybrid action 第 `9` 维
  （`fire_once`）强制为 `0.0`；它比旧的硬编码 `hold` 动作更接近
  support-preserving collection 合同。
- `tools/diagnostics/m3s2_chain_breakpoint_probe.py` 现在接受
  `--collector-action`，并记录
  `window_classifier_fixed_batch_recalibration`。
- recalibration probe 会保存并恢复模型 buffer，不修改模型 artifact。

## 验证

```bash
./.venv/bin/python -m pytest tests/diagnostics/test_m3s2_chain_breakpoint_probe.py -q
```

结果：`5 passed`。

## 轨迹错配检查

模型：

```text
experiments_tmp/m3s2_window_classifier_calibrated_std_8k_20260606_r2/final_model.zip
```

硬 `hold` 与 `model_event_hold` 均以同一方式失败：

| Collector | Quality rows | 当前 quality logit mean | Quality boundary | First breakpoint |
| --- | ---: | ---: | ---: | --- |
| `hold` | `1040` | `-9.902827` | `0 / 1040` | `m3_head_optimization_conditioning` |
| `model_event_hold` | `1080` | `-9.837499` | `0 / 1080` | `m3_head_optimization_conditioning` |
| `model_event_hold --stochastic` | `1080` | `-9.653772` | `0 / 1080` | `m3_head_optimization_conditioning` |

这排除了早先怀疑的硬 `hold` 诊断轨迹错配作为主要 no-fire 原因，也排除了
deterministic-vs-stochastic collection 作为主要原因。

## 优化预算检查

同一个固定 `model_event_hold` batch 还使用线上短预算进行了探针
（`64` steps，`fit_lr = 0.003`）。fresh linear head 达到
`1078 / 1080` 个 quality-boundary rows；从当前 M3 head 初始化的 direct head
达到 `1080 / 1080` 个 quality-boundary rows，但仍保留 `13` 个 prewindow positives。
这说明 frozen actor latent 已包含窗口信号，而且 head 在在线尺度预算下可以移动，
只是严格 one-shot stopping 合同仍未完全满足。

Artifact：

```text
experiments_tmp/m3s2_window_classifier_calibrated_std_8k_20260606_r2/m3s2_chain_breakpoint_probe_final_model_event_hold_fit64_lr003.json
```

## 标准化合同断点

增强后的 chain probe 随后只在 collected fixed batch 上重算 classifier 输入标准化
buffer，不改变 classifier 权重。

Artifact：

```text
experiments_tmp/m3s2_window_classifier_calibrated_std_8k_20260606_r2/m3s2_chain_breakpoint_probe_final_model_event_hold_recalibration_r1.json
```

关键字段：

| Metric | 保存的 buffer | fixed-batch 重校准 buffer |
| --- | ---: | ---: |
| prewindow logit mean | `-13.132194` | `-3.017594` |
| quality logit mean | `-9.837499` | `2.195754` |
| prewindow boundary | `0 / 800` | `232 / 800` |
| quality boundary | `0 / 1080` | `1053 / 1080` |
| event-mode fire count | `0` | `1285` |
| event-mode fire in quality rows | `0` | `1053` |

Buffer shift diagnostics：

| Metric | Value |
| --- | ---: |
| saved fixed-batch z mean abs mean | `2.439337` |
| saved fixed-batch z std mean | `0.633167` |
| mean delta L2 | `2.462030` |
| std ratio mean | `0.633167` |
| std ratio min | `0.055305` |
| std ratio max | `3.032915` |

## 解释

当前最强根因不是缺少窗口信号，不是 action adapter，也不是硬 `hold` 诊断轨迹。
classifier 权重中已经包含可用的 timing 信号，但保存的
`m3_window_classifier_input_*` 标准化 buffer 校准到的是最新 balanced
replay/support 分布，而不是稳定的 execution 分布。在固定 execution-support 轨迹上，
这些 buffer 会把 prewindow 与 quality rows 一起推到负 logit 区域。

只在 fixed batch 上重校准 buffer 后，quality-window logits 会立刻恢复为正。
这还不是 accepted policy，因为同时会产生 prewindow positives；但它足以解释当前
no-fire plateau：可执行 classifier 路径正在一个与实际发射轨迹不一致的 inference-time
normalization 合同下运行。

## 后果

继续调系数大概率不是根治。下一步应把 standardization 当作模型合同问题处理：

- 要么从 executable classifier path 移除 mutable population standardizer，
  依赖 per-sample `LayerNorm` 加 linear head；
- 要么把 latest-balanced replay calibration 替换为稳定的 execution-support
  population normalizer，并在 evaluation 前冻结；
- 要么保证训练与执行使用完全相同的 normalized feature 合同，并在每次 post-update
  都对 fixed execution-support batch 做诊断。

当前切片仍保持 held，直到 deterministic execution 能产生一次 quality-window
single-pulse release，且不在 prewindow 消耗 pulse。
