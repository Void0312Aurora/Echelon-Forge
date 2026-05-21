<!-- Machine-translated draft generated on 2026-05-21 from docs/task/ground/g2_content_test_seed/README.md. Review before treating this file as authoritative. -->

# G2 内容和测试种子

状态：`2026-05-21` 已由主线程 G2-C 集成验收。

语言：

- 英文规范：`README.md`
- 中文配套：暂时不需要；这是一个高频变动的任务片段。

输入：

- [G1 合约框架](../g1_contract_skeleton/README.md)
- [基础标准概述](../../../standards/ground/README.md)
- [基础最小任务结构](../../../standards/ground/minimal_task_structure.md)
- [子代理使用策略](../../../standards/governance/subagent_usage_policy.md)

## 目的

添加第一批基础内容和测试，证明合约框架在不声明运行时行为的情况下可用。

## 输出

- [G2 内容固定装置和测试集群](g2_content_fixture_test_cluster_20260521.md)

## 分派结构

G2 拆分为两个可并行化的工作单元，外加一个串行整合阶段：

- `G2-A`：仅限固定装置/内容种子，负责 `examples/config/database/ground/**`。
- `G2-B`：仅限合约/测试种子，负责 `tests/contracts/unit/ground/**`，如果需要，还包括一个聚焦的基础合约运行器或引导测试。
- `G2-C`：主线程整合，在两个工作单元返回后执行，负责本 README、G2 集群以及基础分派队列。

`G2-A` 和 `G2-B` 不得编辑彼此的文件族或本文档。主线程拥有最终验收权。

## 范围

范围内：

- 一个或两个基础内容固定装置
- 用于验证配置档案默认值的最小任务/场景规范
- 合约形状与映射测试
- 证明 `spawn_unit(type_name)` 兼容性不会成为基础构建的标准路径

范围外：

- 广泛的场景目录
- 地形真实性
- 移动或战斗运行时

## 已验收结果

G2 已验收：

- 第一批 ground 内容根：
  `examples/config/database/ground/units/ground_platoon_starter.seed`
- 本地能力说明：
  `examples/config/database/ground/units/CAPABILITY_NOTE.md`
- 可运行的起步合同：
  `tests/contracts/unit/ground/task_order_ground_profile_defaults.json`
  `tests/contracts/unit/ground/task_order_ground_minimal_structures.json`
  `tests/contracts/unit/ground/task_order_ground_support_relationships.json`

starter seed 刻意使用 `.seed` 而不是 `.json`，因为当前 runtime database
loader 会递归把 `examples/config/database/` 下的 `.json` 当作具体 unit
definition。G2 不新增受维护的 ground runtime unit schema。

## 门控条件

当固定装置和测试能够证明 G1 合约框架可以通过维护的入口点加载并规范化时，G2 即可合并。

门控结果：通过。G2 合同通过已验收的 G1 ground profile 和 common-core 字段完成规范化，
没有引入 runtime movement、terrain、sensing、fires、weapon、damage、C++ DTO、
binding 或 scenario-loader 改动。
