# M3-S2 链路断点定位 Probe

父级：[README.zh.md](README.zh.md)。

状态：`2026-06-06` root-cause localization evidence。

## 目的

该 probe 暂停机制猜测，把开火时机链路拆成可证伪断点：

```text
fixed forced-hold trajectory
  -> label/target support
  -> frozen actor latent separability
  -> M3 stopping-head optimization on frozen latent
  -> action-distribution adapter
  -> edge-trigger pulse semantics
  -> current learned policy
```

核心规则：每一段都必须在同一条真实 Stage-1 forced-hold 轨迹上给出 yes/no。

## 实现

新增 diagnostic：

```text
tools/diagnostics/fire_timing_fault_localization_probe.py --mode chain_breakpoint
```

聚焦测试：

```text
tests/training/test_fire_timing_fault_localization_contracts.py
```

验证：

```bash
python -m compileall -q \
  tools/diagnostics/fire_timing_fault_localization_probe.py --mode chain_breakpoint \
  tests/training/test_fire_timing_fault_localization_contracts.py

python -m pytest tests/training/test_fire_timing_fault_localization_contracts.py -q
```

结果：`3 passed in 2.48s`。

## 运行

主运行：

```bash
env PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python \
  tools/diagnostics/fire_timing_fault_localization_probe.py --mode chain_breakpoint \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_m3s2_event_window_state_completed_world_batch_probe_v1.json \
  --model experiments_tmp/m3s2_scale_separated_contract_8k_20260606_r1/final_model.zip \
  --device cuda \
  --episodes 1 \
  --max-steps 2400 \
  --fit-steps 3000 \
  --fit-lr 0.01 \
  --json-out experiments_tmp/m3s2_chain_breakpoint_probe_20260606_scale_contract_r3_3kfit.json
```

学习率对照：

```text
experiments_tmp/m3s2_chain_breakpoint_probe_20260606_scale_contract_r3_3kfit_lr003.json
```

## 结果

固定 forced-hold collection：

| 字段 | 值 |
| --- | ---: |
| rows | 2400 |
| legal rows | 1880 |
| prewindow rows | 840 |
| quality rows | 1040 |
| accepted rollout events | 0 |

断点表：

| Segment | 结果 | 证据 |
| --- | --- | --- |
| Label/target support | pass | 固定轨迹同时包含 prewindow (`840`) 与 quality (`1040`) rows。 |
| Current learned policy | fail | 当前 M3 head 与 event distribution 的 quality boundary 为 `0 / 1040`，event mode fire 为 `0`。 |
| Frozen actor latent + standardized linear head | pass | Accuracy `1.0`；prewindow boundary `0 / 840`；quality boundary `1040 / 1040`；分离 margin `10.698`。 |
| Folded standardized head through action adapter | behavior pass | event mode 在 prewindow `0 / 840`、quality `1040 / 1040`；edge-trigger 模拟在 row `281` 产生一次 quality pulse。 |
| Direct raw M3 head on frozen latent | strict fail / near pass | `lr=0.01` 时残留 `6` 个 prewindow boundary rows、漏掉 `5` 个 quality rows；`lr=0.03` 时残留 `4` 个 prewindow boundary rows、漏掉 `2` 个 quality rows。 |
| Edge-trigger transport | folded head 下 pass | 一个 legal pulse，first pulse 是 quality，没有 prewindow pulse。 |

folded standardized head 仍记录 `delta_identity_pass = false`
（`max_abs` 差异约 `3.52` 到 `4.23`），但这是校准差异，不是行为失败：
安装 folded head 后，action mode 与 edge-trigger pulse 都正确。

## 结论

第一个失败断点不再是环境可达性、label、观测信号、actor latent capacity、
action adapter 行为或 edge-trigger 语义；这些段在固定真实轨迹上都能通过。

局部化断点是：

```text
m3_head_optimization_conditioning
```

通俗地说：当前 actor latent 已经包含窗口信号，经过标准化的线性 stopping head 能把它变成正确的
quality-window executable pulse。在线学到的 M3 head 没有学出这个校准 separator。
直接在 frozen latent 上优化 raw M3 head 时几乎成功，但仍残留少量 prewindow positives；
对于 one-shot stopping，这几个 prewindow rising edges 就足以消耗发射机会。

下一步修复应针对 head normalization/calibration 与在线 auxiliary optimization contract，
而不是继续调整 reward 或直接上更大的 sequence-memory model。
