# 领导者培训合约

已维护的冻结基线验收规范现位于 [frozen](frozen/README.md)。

此条目界面使用的状态分类法：

- `权威 (Authoritative)`
  - 我们应首先以此作为门控依据的当前验收矩阵。
- `冻结基线 (Frozen Baseline)`
  - 为冻结的领导者/执行底层维护的、刻意保持稳定的验收合约。
- `兼容性 (Compatibility)`
  - 过渡性的维护入口点，可验证维护中的冻结配置，或在不重新开放归档合约的情况下桥接较旧的语义形态。
- `已归档 (Archived)`
  - 仅保留用于可追溯性和来源查找的历史合约。

- 使用 `frozen/` 作为当前权威的领导者验收/泛化矩阵。
- 历史性的弱基线和替代任务链变体已移至 [tests/archive/contracts/unit/training/leader_legacy](../../../archive/contracts/unit/training/leader_legacy/README.md)。
- 冻结前的历史性根级别领导者合约已移至 [tests/archive/contracts/unit/training/leader_pre_frozen](../../../archive/contracts/unit/training/leader_pre_frozen/README.md)。

活跃的领导者验收入口点现为 `frozen/`。此目录中的根级别文件不再用于领导者门控。
如果维护的桥接或包装检查需要较旧的行为形态，请将合约本身保留在维护树中，但将其指向维护中的 `冻结基线` 配置，而不是原始的 `已归档` 配置路径。
