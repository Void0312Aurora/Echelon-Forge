<!-- Machine-translated draft generated on 2026-05-21 from docs/task/ground/g0_boundary_freeze/README.md. Review before treating this file as authoritative. -->

# G0 边界冻结

状态：`2026-05-21` 主线程 G0-D 已采纳；G1 可先以 `preflight-only` 模式启动。

语言：

- 英文权威版本：`README.md`
- 中文副本：暂不需要；此任务切片变更频繁。

输入：

- [域引导计划](../ground_domain_bootstrap_plan_20260521.md)
- [域标准概述](../../../standards/ground/README.md)
- [域最小任务结构](../../../standards/ground/minimal_task_structure.md)
- [子代理使用策略](../../../standards/governance/subagent_usage_policy.md)

## 目标

在 G1 开始前，冻结第三域命名、层所有权、最小任务词汇表以及 G0 架构承诺。此阶段仅涉及文档和标准工作。

## 输出

- [G0 标准对齐集群](g0_standards_alignment_cluster_20260521.md)
- [G0 子代理调度包](g0_subagent_dispatch_packets_20260521.md)

## 已接受的 Worker 返回

- `G0-A`：通过。标准概述保留了已冻结的默认值，明确了 `army` 和 `land` 别名规范化为 `ground`，并仅将 `spawn_unit(type_name)` 作为兼容性包装器保留。
- `G0-B`：通过。最小任务结构保留了 `TASK_MOVE`、`TASK_OCCUPY` 和 `TASK_SUPPORT` 作为唯一的起始任务形态，同时延迟了移动、感知、火力、后勤、伤害和地形真实性的处理。
- `G0-C`：通过。导航、调度文档以及双语注册表在规范性标准稳定后进行同步。
- `G0-D`：已接受。主线程审查未发现 G0 标准阻塞问题，并在解析器/配置文件范围确认前将 G1 限制为 `preflight-only` 模式。

## 范围

涵盖范围：

- `docs/standards/ground/` 下的标准落地位置
- 最小任务词汇表和架构承诺
- 标准/树导航更新
- 为后续阶段准备的子代理调度结构

不涵盖范围：

- Python 配置文件实现
- C++ DTO 更改
- 场景固件
- 运行时行为

## 关口

G0 已获接受，因为标准、任务导航和调度文档在以下方面达成一致：

- 维护名称：`ground`
- 已接受别名：`army`、`ground`、`land`
- 首个紧密循环单位：`platoon`
- 初始任务：`TASK_MOVE`、`TASK_OCCUPY`、`TASK_SUPPORT`
- 无私有域运行时路径
- 发布顺序：G0-A 和 G0-B 可并行运行；G0-C 在两者均返回后串行运行；G0-D 保持为主线程接受状态
- G1 发布：`preflight-only` 模式；目前未知有剩余 G0 标准阻塞问题，但 G0-D 未发布实现。
