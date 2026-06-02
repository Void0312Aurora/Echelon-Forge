<!-- Machine-translated draft generated on 2026-05-21 from docs/task/ground/g0_boundary_freeze/g0_standards_alignment_cluster_20260521.md. Review before treating this file as authoritative. -->

# G0 标准对齐集群

状态：`2026-05-21` 由主线程 G0-D 接受；G1 发布为`仅预检`。

输入：

- [地面领域引导计划](../ground_domain_bootstrap_plan_20260521.md)
- [地面领域引导审查](../../review/ground_domain_bootstrap_plan_review_20260521.md)
- [G0子代理调度包](g0_subagent_dispatch_packets_20260521.md)
- [地面标准概述](../../../standards/ground/README.md)
- [地面最小任务结构](../../../standards/ground/minimal_task_structure.md)
- [子代理使用策略](../../../standards/governance/subagent_usage_policy.md)

## 目的

在实现开始前，使 G0 成为真正的标准约束。本集群将经过审查的引导计划转化为维护的标准文档和任务索引。

## 任务项

| ID | 项 | 验收标准 |
|----|------|------------|
| `G0-A1` | 标准入口 | `docs/standards/ground/README.md` 声明层级模型、G0 默认值、阶段覆盖、能力路径、代理和信息状态规则。 |
| `G0-A2` | 最小任务结构 | `docs/standards/ground/minimal_task_structure.md` 冻结 `TASK_MOVE`、`TASK_OCCUPY` 和 `TASK_SUPPORT`。 |
| `G0-A3` | 标准导航 | `docs/standards/README.md` 和 `docs/standards/overview/document_alignment_map.md` 将地面概念路由到 `services/army` 和 `ground/`。 |
| `G0-A4` | 任务导航 | `docs/task/ground/README.md` 指向 G0-G4 阶段和调度队列。 |
| `G0-A5` | 双语表面 | A 级标准文件配有中文对照，且集群注册表已刷新。 |
| `G0-A6` | 调度就绪 | G0 工作线程包将标准概述、任务词汇和集成工作分割为可序列化的写入范围。 |

## 已接受的返回集成

- `G0-A` 返回 `通过`：冻结的默认值保持为 `ground`、`platoon`、`move / occupy / support` 和 `1 Hz`；`army` 和 `land` 别名归一化为 `ground`；能力组合保持规范。
- `G0-B` 返回 `通过`：`TASK_MOVE`、`TASK_OCCUPY` 和 `TASK_SUPPORT` 保持为唯一初始形态；platoon 保持为第一个紧循环所有者；移动、感知、火力、后勤、损伤和地形真实性保持延迟。
- `G0-C` 返回 `通过`：导航、注册表和调度同步已完成。未释放 G1 实现。
- `G0-D` 接受了 G0 并仅释放了 G1 预检。

## 发布建议

接受的下一个状态：`仅预检 G1`。

在已接受的 G0-A 和 G0-B 返回之后，没有已知的 G0 标准阻塞项，但 G1 实现应等待预检确认解析器/配置文件的写入范围以及是否需要 DTO 外壳。

## 写入范围

允许：

- `docs/standards/ground/**`
- `docs/standards/README*.md`
- `docs/standards/overview/document_alignment_map*.md`
- `docs/standards/bilingual_document_clusters.json`
- `docs/task/ground/**`

禁止编辑：

- 运行时代码
- Python 配置文件代码
- `docs/standards/joint/**`，除非某个共享概念确实需要移至那里
- 不相关的任务目录

发布顺序：

- `G0-A` 和 `G0-B` 可并行运行，因为它们的规范写入范围不重叠。
- `G0-C` 在两个返回被接受后运行，仅更新导航、注册表和调度表面。
- `G0-D` 仍为主线程接受步骤。

## 建议验证

```bash
git diff --check
python tools/maintenance/translate_docs_batch.py clusters --write
python tools/maintenance/translate_docs_batch.py audit --show-missing none
```

## 交接

返回：

- 涉及的文件
- 做出的标准决策
- 未解决的 G1 输入
- 运行的命令
- 任何可疑的命名/分层冲突
- 针对 G1 发布的建议：`仅预检`、`实现就绪` 或 `阻塞`
