# Naval 标准占位

本目录预留给 upcoming `naval` 模块相关的标准文档。

当前作用只有一个：

- 给 `common + air + naval` 拆分提供明确落点
- 给最小海战任务结构提供冻结入口，见 [minimal_task_structure.md](minimal_task_structure.md)
- 给第一批真实舰船单位提供来源与建模边界，见 [ship_unit_references.md](ship_unit_references.md)

## 1. 目录职责

未来放在这里的文档应只描述 naval-specific 语义，例如：

- `warfare_role_code`
- `officer_in_tactical_command`
- `task force / task group / task unit` 的 tight-loop runtime 解释
- screen / support / station 等舰队协同语义
- naval route / recovery / replenishment / station-keeping 规则

## 2. 不应放在这里的内容

- `command_relationship`
- `authority_scope`
- `task_family`
- `service_profile`
- `tactical_unit_type`
- `coordination_mode`
- 其他跨军种仍成立的 `common` 字段

这些应继续由 `docs/standards/joint/` 与 `docs/standards/services/` 约束。

## 3. 与 air 的关系

`naval` 不是把现有 air 文档简单改名。

后续 naval 文档应避免默认使用：

- `lead / wingman`
- `runway`
- `CAP`
- air-style `MissionCommand.command_code` 解释

若某个对象只在空战 sortie 级场景成立，应继续留在 `docs/standards/air/`。

## 4. 当前最小海战占位口径

- `Red_Surface_Combatant_Minimal` 属于 `community-derived approximation`，仅用于替换先前把补给舰当作敌舰的错误占位，不代表某一具体敌方舰级的精确公开参数。
- `ReportTrack` / 任务群级共享属于当前数据链现实收敛的工程近似，用于避免逐步洪泛广播；它不等同完整 `Link 16 / CEC` 语义。
