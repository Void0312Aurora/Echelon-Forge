# 基于分析文档的下一步收束计划

状态：`2026-05-17` 依据五份 `*realism_analysis*` 收口标记重写版。

关联文档：

- [飞行动力学现实性分析](../flight/flight_dynamics_realism_analysis_20260516.zh.md)
- [传感器与态势感知现实性分析](../sensor_situation/sensor_situation_realism_analysis_20260516.zh.md)
- [武器系统与制导回路现实性分析](../weapon_guidance/weapon_guidance_realism_analysis_20260516.zh.md)
- [海战仿真现实性分析](../naval/naval_realism_analysis_20260516.zh.md)
- [指挥链与 C2 通信现实性分析](../c2_command_chain/c2_command_chain_realism_analysis_20260517.zh.md)
- [真实化主线与关联子项目当前状态](realism_program_current_status_20260517.zh.md)
- [海战推进检查点](../../naval/naval_progress_checkpoint_20260517.zh.md)

本文档定位：

- 只从分析文档中仍标记为 `未解决 / 部分解决` 的条目倒推下一步。
- 不把 `已有最小收口 / 已解决` 的方向继续当主线程默认入口。
- 目标是收束当前工作面，避免再次按学科平铺发散。

## 一、先从主阻塞里移除的事项

下列问题已经不应再按“从零开始”或“完全缺失”处理：

1. `flight`
   - 推进瞬态、基础 `Mach` 调度、失速守门和 runtime/debug 骨架已接通。
2. `weapon`
   - `launch gate / seeker-only runtime / 最小 3DoF + PN-autopilot surrogate / midcourse 最小语义` 已接通。
3. `sensor`
   - `track/report` 与 `DataLink / track` 守门面已在本次复核里转绿，当前应按维护态处理。
4. `naval`
   - `screen-hold / sea_state / Sonar / embarked helo token / UNREP` 已不是当前主阻塞，海军武器命令链也已转为维护态验收面。
5. `C2`
   - `MissionCommand roundtrip / DataLink budget / deadband override / 最小 ROE gate` 已接入主线。

这部分的含义不是“这些方向彻底做完了”，而是：
下一步不要再把它们当成新的默认入口重复展开。

## 二、当前只保留三条执行主线

### 2.1 海军武器命令链收口

来源条目：

1. `naval 2.5 / 2.8 / 2.9`
2. `c2 2.1 / 2.3 / 2.4 / 2.11`

为什么先做：

1. 这组问题此前一度是最明确的红点集合，但当前抽样复核已转绿，更适合表述为结构债务收口。
2. 它同时卡住 `naval / C2 / sensor` 三份分析文档里的一批“部分解决”条目。

本线只做：

1. 修 `fire_naval_weapon()` 的主炮直调链路，使“有航迹 -> 可发射 -> 扣减库存”重新成立。
2. 修 `MissionCommand -> CIWS` 命令驱动链，使舰船不依赖 direct weapon API 也能触发近防。
3. 对齐 `MissionCommand / authority / track source / weapon selector` 在 ship 路径上的 shared semantics。

验收线：

1. `tests/runtime/test_naval_ship_database.py::NavalShipDatabaseTests::test_ddg_gun_can_fire_with_track_and_reduce_ammo`
2. `tests/runtime/test_naval_ship_database.py::NavalShipDatabaseTests::test_naval_mission_command_can_trigger_ciws_without_direct_weapon_api`
3. `tests/runtime/test_ship_mission_command_authority.py`
4. `tests/runtime/test_naval_mission_command_mapping.py`

本线明确不展开：

1. `SM-2 / SM-6` 等更细舰空导弹型号分化
2. 完整 naval fire-control AI
3. 完整舰炮/`CIWS` 弹道、射界和跟踪通道细化

### 2.2 航迹生命周期 / IFF / 融合收口

来源条目：

1. `sensor 2.1 / 2.5 / 2.6 / 2.7 / 2.8 / 2.9 / 2.10`

为什么先做：

1. 目前很多“上层看似已接通”的行为，底下仍建立在过于简化的 `track quality / identity / fusion` 语义上。
2. 不先把这层收紧，`weapon / naval / C2` 还是会继续各自绕过它。

本线只做：

1. 把 `Tentative -> Confirmed -> Coasted -> Dropped` 明确成运行时合同。
2. 给 `track` 补最小 `quality / velocity / source_mask`，避免 `Radar + DataLink` 继续只是覆盖式假象。
3. 做最小 `IFF` 状态机，至少区分 `pending / friendly / unknown / hostile` 的收敛路径。
4. 保持 `DataLink = track/report` 口径，不回退到 raw contact 共享，同时收紧 `sensor / DataLink` 的时序和接收端边界。

验收线：

1. `tests/runtime/test_sensor_situation_realism_p0.py`
2. `tests/runtime/test_data_link_qos_runtime.py`
3. 新增或补强 `track lifecycle / IFF / fused track` 定向守门测试

本线明确不展开：

1. 完整 `SNR/Pd` 物理检测模型
2. `PRF / waveform / micro-Doppler` 细化
3. `DRFM / cross-eye / full ECM` 对抗系统

### 2.3 武器末段真实性最小收口

来源条目：

1. `weapon 2.3 / 2.4 / 4.4 / 5.1 / 5.2 / 5.3 / 6.1 / 6.2 / 6.4 / 8.2`

为什么现在做：

1. 武器线前段“能发、能飞、能切 seeker”已经不是主问题。
2. 当前更大的结构风险是 truth shortcut、引信 shortcut 和 damage shortcut 仍然并存。

本线只做：

1. 收紧 truth-based `LOS/target state` 的使用边界，让 seeker/track 输入与 guidance contract 更一致。
2. 补一个最小 seeker reject/decoy contract，避免“任何 strongest signal 都可无条件跟踪”。
3. 把 `fuze / hit / damage` 先收成一致的最小合同，避免 `HP` 路线与 subsystem 路线继续漂移。
4. 明确发射高度/速度对 terminal behavior 的最小可见影响测试。

验收线：

1. 现有 `tests/runtime/test_weapon_guidance_realism_guards.py`
2. 现有 `tests/runtime/test_air_combat_1v1_fire_missile.py`
3. 新增 `truth guidance dependency / fuze timing / damage contract` 定向守门测试

本线明确不展开：

1. 完整 seeker family 分化
2. 完整 warhead geometry
3. 完整 `IRCCM / SARH / LOAL` 体系

## 三、其余方向一律转维护或后置

1. `flight`
   - 当前只接受不破坏现有 guard 的边界收口，以及为 `compressibility / RSS / FBW` 做接口准备。
2. `naval`
   - 当前不单开新舰型、全套浮性/隔舱/稳性，或更大编队 doctrine。
3. `C2`
   - 当前不单开完整 authority transfer state machine，也不单开完整 `multi-hop / retry / jamming` 网络。
4. `sensor`
   - 当前不单开全套雷达方程、全套杂波链或完整电子战对抗体系。

这样做的目的不是保守，而是避免“尚未收紧 shared semantics，就继续往每条线深处挖”。

## 四、建议的并行分发方式

1. worker A
   - `sensor / DataLink / track` 维护态收口与回归补测。
2. worker B
   - 海军武器命令链/authority 回归补测与结构债减载。
3. worker C
   - 武器末段 `fuze / damage / truth guidance` 一致性收口。
4. 主线程
   - 负责 shared schema、`MissionCommand`、`DataLink`、bindings 和验收测试整合，避免多 worker 交叉改同一条 shared contract。

## 五、完成判据

下一轮工作只有在满足下面这些条件时，才算真正“往前推进了一步”：

1. 海军与 `sensor/DataLink/track` 的守门面持续保持绿，不再回退成行为红点。
2. `Track / IFF / Fused` 形成独立守门测试，而不是继续依赖场景偶然成立。
3. weapon 末段不再同时依赖相互矛盾的 truth shortcut 与 damage shortcut。
4. 五份分析文档里当前仍标记为 `未解决` 的条目，至少在 `naval / sensor / weapon` 三条线上各减少一批，而不是继续新增新方向。

## 六、一句话结论

下一步不再按 `flight / sensor / weapon / naval / C2` 五条线平铺推进，而是只收三件事：

1. 海军武器命令链与海事验收面
2. 航迹生命周期 / `IFF` / 融合合同
3. 武器末段 `fuze / damage / truth guidance` 一致性
