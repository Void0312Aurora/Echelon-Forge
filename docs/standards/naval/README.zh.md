# Naval 标准

Language:
- English canonical: [README.md](README.md)
- Chinese companion: `README.zh.md`

状态：`2026-06-10`，当前维护中的 naval 语义标准入口。

本目录收纳专门的 `naval` specialization 标准文档。

这里已经不是占位目录，而是当前海军任务计划的标准入口。目标是把 `common`、`services/navy` 与 `naval` 清楚分层，避免空军优先的语义继续泄漏到海上运行时。

## 维护中文档

建议将这些文件一起阅读：

1. [海军最小任务结构](minimal_task_structure.zh.md)
2. [舰艇单位参考](ship_unit_references.zh.md)
3. [海军观测合同](obs.zh.md)

## 1. 分层模型

### `common`

共享层保持跨军种合同稳定。

它负责这些字段形状：

- `service_profile`
- `task_family`
- `task_group_id`
- `command_relationship`
- `authority_scope`
- `coordination_mode`
- `supported_node_id / supporting_node_id`
- `recovery_site_id`
- `tactical_unit_type`

这些都是军种无关的形状，不是海军执行语义。

### `services/navy`

Navy service profile 负责说明共享合同在海战语境下应如何阅读。

它负责这些语义：

- `task_group` 与 `task_unit`
- `warfare_role_code`
- `officer_in_tactical_command`
- Navy 在任务封装与权限分配中需要的共享锚点

### `naval`

`naval` specialization 负责 tight-loop 海上语义：

- `screen`
- `support`
- `station`
- `recover`
- 舰艇与编队控制语义
- 海上回收与驻站保持行为

## 2. 最小语义合同

当前被视为一等术语的最小海军语义集是：

- `task_group`
- `task_unit`
- `warfare_role_code`
- `officer_in_tactical_command`
- `screen`
- `support`
- `station`
- `recover`

这些术语足以支撑当前任务计划，而不必过早套用空战 sortie 语言。

## 3. 这里应该写什么

放在这里的文档应描述 naval-specific 语义，例如：

- task-group 与 task-unit 的所有权
- warfare role 的分配
- station 保持与 recovery 行为
- 编队中的 screen / support 关系
- 海上任务中的指挥权
- naval execution 与 reporting specialization

## 4. 这里不应该写什么

以下内容应继续留在 `common` 或 `services/navy`：

- `command_relationship`
- `authority_scope`
- `task_family`
- `service_profile`
- `tactical_unit_type`
- `coordination_mode`
- 其他跨军种合同字段

这里不应重复争论共享 schema，而应专门化它。

## 5. 与 air 的关系

`naval` 不是 air 文档改名。

后续 naval 文档应避免默认使用：

- `lead / wingman`
- `runway`
- `CAP`
- 对 `MissionCommand.command_code` 的 air-style 读法

如果某个概念只适用于空战 sortie 级运行时，就应保留在 `docs/standards/air/`。

## 6. 当前最小海军语义

当前 runtime bridge 需要的最小海军语义是：

- `task_group / task_unit` 作为战术组织边界
- `officer_in_tactical_command` 作为权威所有者
- `warfare_role_code` 作为角色标签
- `screen / support / station / recover` 作为最小作战词汇

这些术语足以支撑当前海军任务计划，而不会假装完整舰队 doctrine 已经建模完成。
