# A2 MLF-3 当前状态

状态：`2026-06-10` MLF-3 标准载荷链 focused accepted。第三阶段已单独立项；MLF-3A 只读盘点已验收，真实起爆路径能导出标准 warhead/spatial/component-load 事件，未起爆路径不再产生标准载荷事件，距离/方向/family/空间覆盖已有标准载荷变化门；不声明真实弹种校准、结构解体、残骸或 Pk 完成。

英文辅文：[missile_lethality_warhead_effects_current_status_20260609.md](missile_lethality_warhead_effects_current_status_20260609.md)

## 成熟度矩阵

| 区域 | 状态 | 证据 | 不能证明什么 |
| --- | --- | --- | --- |
| MLF-2 输入 | accepted / archived | [MLF-2 归档指针](../../../missile_lethality_geometry_fuze/README.zh.md) | 不证明战斗部作用已经高保真 |
| MLF-3A 盘点 | accepted | [盘点验收记录](missile_lethality_warhead_effects_inventory_20260609.zh.md) | 不证明 writer 或诊断已全部完成 |
| 标准事件结构 | live gate focused pass | `WarheadMechanismEvent`、`SpatialCoverageEvent`、`ComponentLoadEvent` 已在合同/绑定表面、event-store writer 和真实起爆路径测试中存在 | 不证明参数已校准 |
| 现有效果模型 | generic load-shape focused pass | `default_effects_model`、`default_effects_warhead_detail.inc`、`default_effects_spatial_projection_detail.inc`；3C 聚焦测试证明 range / direction / family 会改变标准载荷事实 | 不证明阶段边界已标准化，也不证明参数已校准 |
| 空间/部件投影 | focused pass | Euclid 只读审计确认最小入口；`test_warhead_spatial_component_projection.py` 证明空间覆盖/局部投影会改变标准 `ComponentLoadEvent` 的部件、距离、effect scale、破片面密度和爆风超压 | 不证明部件失效概率、结构断裂、残骸、Pk 或具体型号校准 |
| 诊断投影 | standard-event priority / focused pass | process probe 已优先读取 warhead / spatial / component load 标准事件，旧 `EffectsEvent` 只作同链路回退；不同链路仍可回退 | 不证明后续脆弱性或结构失效完成 |
| Runtime handoff gate | no-detonation focused pass | `fuze_no_detonation` 与 `fuze_no_terminal_track` 不提升为标准 warhead/spatial/component-load 事件 | 不证明后续脆弱性或结构失效完成 |
| Research 数据口径 | boundary fixed | 只允许通用、未校准、可替换的数据和方法进入本阶段 | 不证明具体型号参数真实 |
| 第三阶段子项目 | focused accepted | README、状态、任务簇、派发队列、验收记录和 archive 索引已同步到 `MLF-3G` | 不证明高保真杀伤模型整体完成 |

## 当前结论

第二阶段已经归档。第三阶段的工作不是继续调引信半径，也不是让目标直接坠毁；它要把起爆之后的作用拆成可检查的载荷事实。

当前代码已经有一些可复用脚手架：战斗部 profile、空间投影、机制载荷字段、部件受载字段和历史 Phase 3 测试。本轮已经把起爆后的旧 `EffectsEvent` 载荷事实投影到标准 warhead / spatial / component load 事件；普通 debug 命中无部件行时不会凭空生成部件事件；未起爆 `EffectsEvent` 仍保留诊断事实，但不再提升为标准载荷事件。

3C 本轮没有新增 runtime 字段或默认参数；它用合成 profile fixture 钉住现有通用工程假设载荷面：miss distance / range、方向/姿态和 warhead family 会改变标准事件中的破片能量、面密度、爆风超压、冲量和部件载荷。Heisenberg 只读审计同时确认当前 DTO 仍缺少逐默认值 source category / scope / unit / uncertainty / replacement-rule metadata，因此这些常量仍只能视作 generic research assumptions。

3D 本轮没有改核心效果模型或标准事件字段；Euclid 确认现有空间投影入口已经会生成部件候选和 component-load source rows，Fermat 的聚焦测试证明右侧近/远与左右镜像局部投影会改变标准部件受载事实。该结论只说明“部件承受了什么载荷可以被标准事件读出”，不说明部件已经失效、目标已经坠毁或实体应被删除。

本阶段数据按 research 规则处理：只使用通用爆风/破片方法、工程量级、代理资料类别提示和测试用合成值；每个默认值都必须标出来源类别、证据等级、适用范围、单位、不确定性和替换规则。

## 近期任务

1. 后续进入 MLF-4/5/6/8/9 时，只消费 MLF-3 输出的标准载荷事实，不把它当作直接击毁结论。
2. 任何参数面继续使用通用 research 数据，不把当前通用参数说成具体型号真值。
3. 结构解体、残骸、Pk、具体型号校准和逐默认值完整 metadata 继续 held。

## 保持的边界

- 不实现连续杆切割。
- 不实现结构断裂、碎片、残骸或实体删除。
- 不声明 AIM-120C/MQ-9 个案真实杀伤。
- 不把机制载荷变成训练胜负事实。
- 不把通用 research 参数写成具体型号真值。
