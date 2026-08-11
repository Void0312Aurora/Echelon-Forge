# A2 MLF-3A 盘点验收记录

状态：`2026-06-09` accepted for MLF-3A。该记录只验收只读盘点，不表示 MLF-3 整体完成。

英文辅文：[missile_lethality_warhead_effects_inventory_20260609.md](missile_lethality_warhead_effects_inventory_20260609.md)

## 结论

MLF-3A 通过。当前代码里已经有战斗部、空间覆盖和部件受载三类标准事件的结构和绑定，但在本轮开始前没有 live writer。旧 `EffectsEvent` 已经承载不少可复用载荷字段，所以后续工作应做“标准事件投影”，而不是重新定义击毁或坠毁规则。

## 已确认位置

- 事件结构：`src/runtime/contracts/engagement_contracts.h`
- 最近事件容器：`src/core/engine/engagement_event_types.h`
- facade 导出容器：`src/runtime/facade/runtime_facade_types.h`
- Python 绑定：`src/interfaces/python/bindings_runtime.cpp`、`src/interfaces/python/bindings_core.cpp`
- 运行时缺口：`src/core/interfaces/engagement_event_recorder.h`、`src/core/engine/simulation_kernel_engagement_event_store.*`
- 旧字段来源：`src/core/interfaces/effects_model.h`、`src/core/interfaces/engagement_effects_event_builder.h`
- 效果模型入口：`src/models/weapons/default_effects_model.cpp`、`src/models/weapons/detail/default_effects_warhead_detail.inc`
- 诊断入口：`tools/diagnostics/air_combat_weapon_employment_process_probe.py`

## 保持的边界

- 不新增具体 AIM-120C、MQ-9 或其它型号真值。
- 不把 CMO-DB、公开网页、历史测试或工程假设写成型号级权威。
- 不让未起爆路径产生战斗部、空间覆盖或部件受载事件。
- 不把载荷事实直接变成 kill、crash 或实体删除。

## 后续切入点

1. `MLF-3B`：补 recorder/event-store writer，并从现有 `EffectsEvent` 字段投影标准事件。
2. `MLF-3B` 聚焦测试：证明起爆后能导出 warhead、spatial 和 component load 标准事件。
3. `MLF-3E`：诊断 probe 优先消费标准事件，旧 `EffectsEvent` 只作过渡回退。
