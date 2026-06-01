# 冻结领导者接受集

此目录包含为冻结通用核心底层维护的领导者层接受规范。

## 门控基线规范

- [leader_task_only_generalization_frozen_v1.json](leader_task_only_generalization_frozen_v1.json)
- [leader_full_chain_demo_frozen_v1.json](leader_full_chain_demo_frozen_v1.json)

## 补充矩阵规范

- [leader_full_chain_randomized_frozen_v1.json](leader_full_chain_randomized_frozen_v1.json)
- [leader_task_only_randomized_frozen_v1.json](leader_task_only_randomized_frozen_v1.json)

补充的仅任务随机矩阵被保留用于后续调优，但未被提升为冻结门控集，因为它在当前的领导者/运行时基准下不稳定。

## 用法

```bash
./.venv/bin/python tools/runners/run_scenario_contract.py \
  --spec tests/contracts/unit/training/frozen/leader_full_chain_demo_frozen_v1.json
```

```bash
./.venv/bin/python tools/runners/run_scenario_contract.py \
  --spec tests/contracts/unit/training/frozen/leader_task_only_randomized_frozen_v1.json
```

## 训练映射

- [leader_task_only_retrain_v1.json](../../../../../examples/config/training/frozen/leader_task_only_retrain_v1.json)
  - 门控条件：[leader_task_only_generalization_frozen_v1.json](leader_task_only_generalization_frozen_v1.json)
  - 仅在 [leader_task_only_randomized_frozen_v1.json](leader_task_only_randomized_frozen_v1.json) 稳定后提升
- [leader_c2_retrain_v1.json](../../../../../examples/config/training/frozen/leader_c2_retrain_v1.json)
  - 门控条件：[leader_full_chain_demo_frozen_v1.json](leader_full_chain_demo_frozen_v1.json)
  - 演示链稳定后扩展至 [leader_full_chain_randomized_frozen_v1.json](leader_full_chain_randomized_frozen_v1.json)
