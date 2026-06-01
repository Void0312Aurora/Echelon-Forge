# 冻结领导者基线

此目录包含冻结通用核心基座（common-core substrate）下受维护的领导者层训练入口点。

所有从此处链接的内容状态均为`冻结基线（Frozen Baseline）`，除非某条说明明确标注其继承关系进入`已归档（Archived）`历史。

## 基线配置

- [leader_task_only_frozen_v1.json](leader_task_only_frozen_v1.json)
  - 在基座冻结后保留继承的仅任务（task-only）基线。
- [leader_c2_frozen_v1.json](leader_c2_frozen_v1.json)
  - 在基座冻结后保留继承的报告/全链（reporting/full-chain）基线。

## 执行课程

- [execution/README.md](execution/README.md)
  - 冻结后的执行层`p2 -> p3 -> p4 -> p4b -> p5`课程。

## 重训练配置

- [leader_task_only_retrain_v1.json](leader_task_only_retrain_v1.json)
  - 主要的仅任务重训练配置，用于生成冻结后原生领导者模型。
- [leader_task_only_retrain_smoke_v1.json](leader_task_only_retrain_smoke_v1.json)
  - 仅任务启动验证的短冒烟运行配置。
- [leader_c2_retrain_v1.json](leader_c2_retrain_v1.json)
  - 冻结基座下的主要报告/全链重训练配置。
- [leader_c2_retrain_smoke_v1.json](leader_c2_retrain_smoke_v1.json)
  - 报告/全链启动验证的短冒烟运行配置。

## 继承关系

- `leader_task_only_retrain_*`
  - 源自 [p6_leader_layer_frozen_exec_generalization_v1.json](../../Archive/training/leader_legacy/p6_leader_layer_frozen_exec_generalization_v1.json)
  - 调整为直接在冻结的通用核心基座上运行，并针对当前的随机化仅任务差异
- `leader_c2_retrain_*`
  - 源自 [p7_leader_layer_c2_reporting_generalization_v1.json](../../Archive/training/leader_legacy/p7_leader_layer_c2_reporting_generalization_v1.json) 和 [p7_leader_layer_c2_reporting_generalization_fast_v2.json](../../Archive/training/leader_legacy/p7_leader_layer_c2_reporting_generalization_fast_v2.json)
  - 调整为使用冻结的执行产物和当前的冻结验收集

## 验收目标

- `leader_task_only_retrain_*`
  - [leader_task_only_generalization_frozen_v1.json](../../../../tests/contracts/unit/training/frozen/leader_task_only_generalization_frozen_v1.json)
  - [leader_task_only_randomized_frozen_v1.json](../../../../tests/contracts/unit/training/frozen/leader_task_only_randomized_frozen_v1.json)
- `leader_c2_retrain_*`
  - [leader_full_chain_demo_frozen_v1.json](../../../../tests/contracts/unit/training/frozen/leader_full_chain_demo_frozen_v1.json)
  - [leader_full_chain_randomized_frozen_v1.json](../../../../tests/contracts/unit/training/frozen/leader_full_chain_randomized_frozen_v1.json)

## 推荐场景配对

- `leader_task_only_retrain_*`
  - 冒烟/主要场景：`scenarios/combined/takeoff_to_landing_c2_task_only_train_v1.json`
- `leader_c2_retrain_*`
  - 冒烟场景：`scenarios/combined/takeoff_to_landing_c2_task_demo_fasttrain_v1.json`
  - 主要场景：`scenarios/combined/takeoff_to_landing_c2_task_demo_v1.json`

## 已验证的冒烟命令

```bash
./.venv/bin/python train.py \
  --scenario scenarios/combined/takeoff_to_landing_c2_task_only_train_v1.json \
  --train_config examples/config/training/frozen/leader_task_only_retrain_smoke_v1.json \
  --run_name leader_task_only_retrain_smoke_verify_20260323 \
  --output_base /tmp/cmo_frozen_smoke
```

```bash
./.venv/bin/python train.py \
  --scenario scenarios/combined/takeoff_to_landing_c2_task_demo_fasttrain_v1.json \
  --train_config examples/config/training/frozen/leader_c2_retrain_smoke_v1.json \
  --run_name leader_c2_retrain_smoke_verify_20260323 \
  --output_base /tmp/cmo_frozen_smoke
```

## 产物策略

- 冻结的执行模型：
  - `experiments/_archive_20260322_test_results/root_level/experiments_tmp/20260318_p5_takeoff_to_landing_continuous_v3_retrain_v1/final_model.zip`
- 受维护的执行训练配置继承关系：
  - [execution/p5_continuous_retrain_v1.json](execution/p5_continuous_retrain_v1.json)
- 已归档的历史领导者配置：
  - [examples/config/Archive/training/leader_legacy](../../Archive/training/leader_legacy/README.md)

当维护的合约、桥梁或冒烟配方需要冻结的领导者/执行基线时，请使用此目录，而不是`examples/config/Archive/**`。
