# A2 MLF-4A 连续杆只读盘点包

状态：`2026-06-10` accepted inventory packet。原 `MLF-4A-X1` worker 未返回可验收包，主线程按同一只读范围完成异常恢复复核。

英文辅文：[missile_lethality_continuous_rod_inventory_20260610.md](missile_lethality_continuous_rod_inventory_20260610.md)

## Worker Packet

status: pass

touched files:

- 无 runtime 源码改动。
- 本盘点包和 MLF-4 状态/队列文档由主线程更新。

commands/outcomes:

- `wait_agent 019eb210-9e5e-7b80-bc77-335b98d5796c`：未取得完成包。
- `resume_agent 019eb210-9e5e-7b80-bc77-335b98d5796c`：返回 `pending_init`。
- `close_agent 019eb210-9e5e-7b80-bc77-335b98d5796c`：关闭时仍为 `pending_init`。
- `rg -n "rod_cut_margin|continuous_rod|rod_cut|cut_margin" src/runtime src/models src/components tools tests/runtime/air_combat`：确认字段、模型分支、诊断和历史测试入口。
- `rg -n "warhead_mechanism_events|component_load_events|mechanism_rod|rod_cut|LETHALITY_CHAIN_STAGES" tools/diagnostics tests/runtime/air_combat`：确认诊断读取路径和已有 guard 测试。

remaining paths:

- `MLF-4B-W1`：稳定标准 rod/cut 事件面和聚焦测试。
- `MLF-4C-W1`：把通用连续杆几何作为当前 MLF-4 accepted 测试重新验证，不直接提升历史 Phase 3 测试。
- `MLF-4D-W1`：把部件切割曝光投影到标准部件受载事实，但不输出失效。
- `MLF-4E-W1`：诊断和未起爆/非 rod guard。

behavior risks:

- 现有连续杆逻辑已经影响部件损伤和历史部件失败测试；MLF-4 后续必须把“切割事实”与“部件失效/结构后果”隔离。
- 现有常量是通用 research 假设，不是 AIM-120C 或任何真实弹种的连续杆参数。
- 历史 Phase 3 测试覆盖了很多有用现象，但不是本阶段 accepted 证据。

integration notes:

- 现有 `WarheadMechanismEvent::rod_cut_margin` 和 `ComponentLoadEvent::rod_cut_margin` 看起来足以承载 MLF-4B 的标准事件面；暂不建议新增专门 rod/cut 事件，除非 4B 发现需要区分更多切割子字段。
- 未起爆 gate 已有证据：未起爆路径没有标准 warhead/spatial/component 载荷事件，且 effects 上 rod 值保持为零。
- 非 rod gate 有历史证据：blast 路径 rod 值为零；但 4B/4E 仍需要新增 MLF-4 聚焦测试，把这件事固定到标准事件和诊断面。

## 只读发现

### 事件和导出字段

- 标准战斗部事件已经有 `rod_cut_margin`：[../../../../../src/runtime/contracts/engagement_contracts.h](../../../../../../../../src/runtime/contracts/engagement_contracts.h)。
- 标准部件受载事件已经有 `rod_cut_margin`：[../../../../../src/runtime/contracts/engagement_contracts.h](../../../../../../../../src/runtime/contracts/engagement_contracts.h)。
- 旧的效果事件和部件行也保留 rod 字段：`mechanism_rod_cut_margin`、`component_primary_mechanism_rod_cut_margin`、`ComponentMechanismLoadRow::mechanism_rod_cut_margin`。
- Python 绑定已暴露上述字段：[../../../../../src/interfaces/python/bindings_runtime.cpp](../../../../../../../../src/interfaces/python/bindings_runtime.cpp)。
- 事件存储会把 `EffectsEvent` 的 rod 值抽到标准 `WarheadMechanismEvent` 和 `ComponentLoadEvent`：[../../../../../src/core/engine/simulation_kernel_engagement_event_store.cpp](../../../../../../../../src/core/engine/simulation_kernel_engagement_event_store.cpp)。

### 连续杆模型切入点

- `continuous_rod` 已在默认效果模型里有家族权重、空间投影、穿透/切割估计、方向权重和脆弱性筛选入口：[../../../../../src/models/weapons/detail/default_effects_warhead_detail.inc](../../../../../../../../src/models/weapons/detail/default_effects_warhead_detail.inc)。
- `rod_cut_margin` 的当前计算来自通用杆数量、杆段质量、闭合速度、距离质量、方向权重、空间命中估计和目标装甲厚度；这些值应标为通用假设。
- 空间投影已经能把 `mechanism_load` 记录到部件行：[../../../../../src/models/weapons/detail/default_effects_spatial_projection_detail.inc](../../../../../../../../src/models/weapons/detail/default_effects_spatial_projection_detail.inc)。
- scratch/result/builder 链路已经把 sampled rod 值传到 `EffectsEvent`：[../../../../../src/models/weapons/detail/default_effects_state_detail.inc](../../../../../../../../src/models/weapons/detail/default_effects_state_detail.inc)、[../../../../../src/models/weapons/detail/default_effects_result_detail.inc](../../../../../../../../src/models/weapons/detail/default_effects_result_detail.inc)、[../../../../../src/core/interfaces/engagement_effects_event_builder.h](../../../../../../../../src/core/interfaces/engagement_effects_event_builder.h)。

### 诊断路径

- 诊断行字段已包含 `rod_cut_margin`：[../../../../../tools/diagnostics/air_combat_weapon_employment_process_probe.py](../../../../../../../../tools/diagnostics/air_combat_weapon_employment_process_probe.py)。
- 诊断优先读取标准 `warhead_mechanism_events` 和 `component_load_events`，没有标准事件时才从 `EffectsEvent` fallback。
- 现有诊断 contract 测试主要固定字段形状和标准事件优先级，但还没有 MLF-4 专用连续杆正/负例。

### 测试隔离

- `tests/runtime/air_combat/weapon_guidance_realism/warhead_effects.py` 里已有历史 Phase 3 测试，覆盖方向轴、方向姿态、rod 正值、非 rod 为零、部件行 rod 值等现象。
- `component_damage.py` 和 `aircraft_damage.py` 中已有连续杆触发部件失败或结构影响的历史测试。这些不能作为 MLF-4 验收证据，因为 MLF-4 不验收失效或结构后果。
- 4B/4C/4D/4E 应新增或拆出 MLF-4 聚焦测试，只检查切割事实、标准事件和诊断，不检查部件失败、坠毁或结构解体。

## 验收结论

`MLF-4A-X1` 可验收。它完成了“现有字段、分支、历史测试和缺口”的只读盘点，并足以解锁 `MLF-4B-W1 Standard Rod Event Surface`。

本验收不表示 MLF-4 runtime 已完成，也不表示连续杆杀伤模型高保真。它只说明下一步可以安全进入标准 rod/cut 事件面的实现和测试设计。
