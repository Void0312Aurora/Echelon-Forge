# Simulation Kernel 契约

本目录包含直接用脚本化 pilot 输入步进 `SimulationKernel` 的 `unit_regression` 契约。

## 当前失败策略

`tests/runners/test_contract_batches.py` 中的 `sim_kernel` batch 当前通过 glob 选择全部 `tests/contracts/unit/kernel/*.json` 文件。任一被选中契约失败都会使 batch 非零退出，因此当前执行层面是 hard-fail。

这种 runner 行为还没有编码语义层级。稳定的 repeatability、sign、takeoff、ground-roll 和 level-flight 护栏可以作为 gate 候选；紧凑参数扫描和 realism probe 在 metadata 或 manifest 明确提升前，应视为 supplemental 或 diagnostic。

这里有意不修改 `pitch_hold_throttle_scan.json`。它当前的行为仍以 runner 结果为准；本 README 只记录 `sim_kernel` 需要显式区分 gate 与 diagnostic，之后才能把扫描失败解释为已校准验收失败。
