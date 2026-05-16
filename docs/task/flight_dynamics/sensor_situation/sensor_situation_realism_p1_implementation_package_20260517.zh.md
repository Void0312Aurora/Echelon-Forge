# 传感器/态势真实化 P1 实施包

状态：`2026-05-17` 验收后收敛版。

关联文档：

- [传感器与态势感知现实性分析](/home/void0312/Workshop/CMO/docs/task/flight_dynamics/sensor_situation/sensor_situation_realism_analysis_20260516.zh.md)
- [传感器/态势感知真实化核实与实现方案](/home/void0312/Workshop/CMO/docs/task/flight_dynamics/sensor_situation/sensor_situation_realism_verification_and_implementation_plan_20260516.zh.md)
- [传感器/态势真实化 P0 实施包](/home/void0312/Workshop/CMO/docs/task/flight_dynamics/sensor_situation/sensor_situation_realism_p0_implementation_package_20260516.zh.md)
- [真实化任务总表](/home/void0312/Workshop/CMO/docs/task/flight_dynamics/program/realism_program_taskboard_20260516.zh.md)
- [传感器/态势真实化 P0 参考说明](/home/void0312/Workshop/CMO/docs/task/flight_dynamics/sensor_situation/sensor_situation_realism_p0_reference_notes_20260516.md)

文档目的：

- 把方向二从 `P0 骨架已落地` 推进到 `P1 可集成、可暴露、可继续标定`。
- 明确哪些问题必须先做“前置集成收尾”，哪些可以保守纳入 `P1` 深化真实化。
- 把本次验收中已经暴露的兼容风险写进任务包，避免后续只按理想系统展开。

---

## 一、P1 定位

`P1` 不再解决“有没有骨架”，而是解决两类问题：

1. `P0` 已落地字段和语义，必须真正打通到 `loader / factory / observation / python binding / 测试合同`
2. 在不引入大范围架构重写的前提下，把传感器/态势从“训练级可跑”推进到“工程上更像样”

换句话说，`P1` 的目标不是做成完整雷达/IFF/融合系统，而是让下面这些表述成立：

- 新增的传感器字段不再只是 C++ 结构体里的隐式默认值，而是可配置、可观察、可测试。
- `TrackDatabase` 的 `status / quality / source` 语义能被上层看到，而不是只在后端内部存在。
- 环境、IFF、融合、航迹质量这些真实化项开始产生可验证影响，但仍保持保守范围。

---

## 二、P0 验收后的现实输入

P1 不是从空白开始，而是从本次 P0 验收后的现状出发。

### 2.1 已经成立的 P0 成果

1. 本地探测已具备 `SNR -> Pd` 近似链路。
2. 本地 track 已具备最小 `2-of-3` 式确认语义。
3. `TrackManager` 已具备最小 `alpha-beta` 预测更新骨架。
4. `DataLink` 已切断“直接写接收方 ContactList”的 truth-style 行为，改为 track/report 语义。

### 2.2 本次验收暴露的兼容风险

这些问题不处理，`P0` 的真实性骨架会停留在“后端局部成立”。

| 风险 | 当前现象 | 对 P1 的直接要求 |
|------|----------|------------------|
| `Sensor` 新字段未完全打通 | 结构体已扩展，但 `loader / factory` 仍需统一补齐默认值与配置读取 | 先做前置集成收尾 |
| observation 未暴露新语义 | `track status / quality / 新 Detection 字段` 仍未稳定暴露给上层 | 先做前置集成收尾 |
| Python binding 表面仍是旧接口 | `ReportTrack`、`CommPacket` 新字段、`Detection` 新字段未完整进入 Python 面 | 先做前置集成收尾 |
| 旧测试仍可能绑定旧语义 | 旧测试可能仍把“共享 track = 本地 contact”当成合法行为 | 先做前置集成收尾 |
| 测试/构建产物路径可能混淆 | 若测试加载的不是当前构建产物，容易出现“源码已改、运行仍旧”的假象 | P1 需要收紧测试入口 |
| 当前 `entity_id` 仍是强关联钩子 | P0 仍通过 `entity_ref`/`entity_id` 辅助关联与 debug | P1 只能继续保守演进，不能贸然切断 |
| `Tentative` 仍是内部语义 | P0 为兼容观测接口，暂未把 tentative track 公开为主观测合同 | P1 需要明确是否暴露、如何暴露 |
| 非本线测试存在噪声失败 | 如 `naval_screen` 相关测试失败未必由本线直接引入 | P1 需要把回归判定与 owned/unowned 风险分层 |

### 2.3 P1 的基本策略

P1 采取两个原则：

1. `先收口，再深化`
   - 先把 `loader / factory / observation / binding / test contract` 补齐
   - 再做更深的真实化
2. `先做保守真实化，不做架构革命`
   - 允许继续保留 `entity_ref` 作为 debug/truth hook
   - 不在 P1 直接引入 `JPDA / MHT / 完整 Link 16 / 完整 NCTR`

---

## 三、P1 前置集成收尾

这一层不是“算法更真实”，而是“让 P0 真正成为系统级能力”。

### 3.1 目标

1. 让 `Sensor` 新字段从配置进入运行时。
2. 让 `Track status / quality / Detection 扩展字段` 可以被 observation 和 Python 看到。
3. 让旧测试合同迁移到新语义，而不是继续偷偷依赖旧行为。
4. 让测试与构建入口更稳定，降低“跑到旧产物”的风险。

### 3.2 保守纳入 P1 的内容

#### 1. Loader / factory 默认值补齐

建议文件范围：

- [src/content/unit_definition_loader.cpp](/home/void0312/Workshop/CMO/src/content/unit_definition_loader.cpp)
- [src/models/core/default_unit_factory.h](/home/void0312/Workshop/CMO/src/models/core/default_unit_factory.h)
- 如有需要，补 [src/content/unit_definition.h](/home/void0312/Workshop/CMO/src/content/unit_definition.h)

建议补齐：

- `reference_snr_db`
- `reference_range_m`
- `reference_rcs_m2`
- `pfa`
- `confirm_hits_m`
- `confirm_window_n`
- `velocity_noise_std`
- `alpha_beta_alpha`
- `alpha_beta_beta`

建议默认口径：

- 雷达默认 `range_power = 4.0`
- `pfa = 1e-6`
- fighter radar 默认 `confirm = 2-of-3`
- surveillance radar 默认 `confirm = 2-of-2` 或 `3-of-4`

P1 不建议在这一层就把 `Pt / G / B / F / PRF` 一次性塞入 schema。

#### 2. Observation / runtime 合同补齐

建议文件范围：

- [src/core/engine/simulation_kernel_observation_api.cpp](/home/void0312/Workshop/CMO/src/core/engine/simulation_kernel_observation_api.cpp)
- [src/core/engine/simulation_kernel.h](/home/void0312/Workshop/CMO/src/core/engine/simulation_kernel.h)

P1 需要明确的观测口径：

- 是否继续默认只暴露 `confirmed/coasted` track
- 是否把 `status` 直接暴露给上层 agent
- 是否补暴露：
  - `track_quality`
  - `track_confidence`
  - `last_local_update_time`
  - `last_datalink_update_time`
  - `closing_speed` 是否改由 `vx/vy/vz` 反算

保守建议：

- 默认 observation 仍只暴露 `confirmed/coasted`
- 新增 `status / quality / confidence` 字段
- tentative 若需暴露，走 `debug observation` 或显式可选出口，不直接改主合同

#### 3. Python binding 暴露与兼容别名

建议文件范围：

- [src/interfaces/python/bindings_core.cpp](/home/void0312/Workshop/CMO/src/interfaces/python/bindings_core.cpp)
- [src/interfaces/python/bindings_command.cpp](/home/void0312/Workshop/CMO/src/interfaces/python/bindings_command.cpp)

P1 需要补齐：

- `Detection.snr_db`
- `Detection.detection_prob_used`
- `Detection.measured_vr`
- `Detection.sensor_type`
- `Detection.local_sensor_hit`
- `CommPacket.track_ref`
- `CommPacket.velocity_x/y/z`
- `CommPacket.quality`
- `CommMsgType.ReportTrack`

兼容建议：

- `ReportTrack` 与 `ReportContact` 在 Python 面可同时保留
- 旧字段名不移除，只新增

#### 4. 旧测试语义迁移

建议文件范围：

- `tests/runtime/test_kernel_observation_sanity.py`
- `tests/runtime/test_execution_step_runtime.py`
- `tests/runtime/test_mission_runtime.py`
- `tests/runtime/test_naval_screen_scenario.py`
- `tests/runtime/test_air_combat_1v1_fire_missile.py`
- `tests/runtime/test_bindings_command_surface.py`
- `tests/runtime/test_sensor_situation_realism_p0.py`

P1 需要清理的旧语义：

- “共享 track 后，接收方本地 `ContactList` 自动出现目标”
- “`ReportContact` 是唯一合法消息类型名”
- “track 没有 `status / quality` 字段也不影响合同”

#### 5. 构建/测试入口收紧

建议文件范围：

- `python/testing/runtime.py`
- `tests/README.md`
- 必要时补一个最小测试说明文档，但不要改任务总表

P1 要求至少做到：

- 运行测试时优先加载当前构建产物
- 明确 `build ef_py -> run runtime tests` 的标准顺序
- 避免出现“源码已变，但测试仍加载旧安装模块”的歧义

### 3.3 继续留到 P2 的内容

以下内容不建议塞进“前置集成收尾”：

1. 重写 observation 主合同
2. 完整拆掉 `entity_ref`
3. 完整重构 Python API 命名面
4. 全量修所有 unrelated 运行回归

### 3.4 最小测试清单

#### 1. 配置/默认值

- `sensor` 新字段可从数据库读取
- 缺省字段时 factory/default 值稳定
- 雷达默认 `range_power` 不再误落到 `2.0`

#### 2. observation / binding

- Python 可读到新 `Detection` 字段
- Python 可读到 `Track status / quality`
- `ReportTrack` 与 `ReportContact` 兼容表面可用

#### 3. 语义迁移

- DataLink 共享后接收方 `ContactList` 仍为空
- 接收方 `TrackDatabase` 能看到 `TrackSource::DataLink`
- 旧测试若依赖旧语义，已改成检查新语义或显式废弃

### 3.5 验收口径

前置集成收尾完成后，至少应满足：

1. P0 新字段不再依赖“结构体隐式默认 + 手工注入”才能工作。
2. runtime observation 和 Python binding 能看到 P0 关键新语义。
3. 旧测试不再把“共享 contact”当成合法行为。
4. 从构建到测试的路径是可重复、可说明、可交接的。

---

## 四、P1 深化真实化

这一层是在前置集成收尾之后，开始继续提升真实性，但保持保守范围。

### 4.1 应保守纳入 P1 的内容

#### 1. Track quality / confirm 语义细化

建议文件范围：

- [src/components/systems/track_management.h](/home/void0312/Workshop/CMO/src/components/systems/track_management.h)
- [src/systems/systems/track_manager_system.h](/home/void0312/Workshop/CMO/src/systems/systems/track_manager_system.h)
- [src/core/engine/simulation_kernel_observation_api.cpp](/home/void0312/Workshop/CMO/src/core/engine/simulation_kernel_observation_api.cpp)

P1 建议做：

- 把当前简化的 hit 累加，收紧为更明确的滑动 `M-of-N`
- 明确 `Tentative -> Confirmed -> Coasted -> Dropped` 生命周期
- 区分：
  - 本地最新更新时间
  - 数据链最新更新时间
  - 航迹整体 age
- 让 `quality` 同时受 `hits / misses / staleness / source` 影响

这是 P1，因为它直接影响上层战术决策，但不要求完整 Kalman 协方差体系。

#### 2. 保守环境/杂波建模

建议文件范围：

- [src/core/interfaces/environment_model.h](/home/void0312/Workshop/CMO/src/core/interfaces/environment_model.h)
- [src/models/environment/default_environment_model.cpp](/home/void0312/Workshop/CMO/src/models/environment/default_environment_model.cpp)
- [src/models/systems/default_sensor_model.cpp](/home/void0312/Workshop/CMO/src/models/systems/default_sensor_model.cpp)

P1 建议做：

- 把 `weather attenuation` 从固定 `0.0` 提升为最小非零模型
- 给 look-down / low radial velocity 场景增加基础 clutter penalty
- 保留当前数据链地平线公式
- 在传感器探测侧补最小“曲率/低空几何惩罚”或 horizon-style penalty

P1 不建议做：

- 完整 terrain ray cast
- 海况驱动海杂波图
- 波导/超折射/亚折射

#### 3. IFF 状态机最小化落地

建议文件范围：

- [src/components/systems/track_management.h](/home/void0312/Workshop/CMO/src/components/systems/track_management.h)
- [src/components/systems/sensor.h](/home/void0312/Workshop/CMO/src/components/systems/sensor.h)
- [src/systems/systems/track_manager_system.h](/home/void0312/Workshop/CMO/src/systems/systems/track_manager_system.h)
- observation / binding 对应出口

P1 只建议做：

- `IFF reply present / no reply / ambiguous / pending`
- 周期性 interrogation 的最小时间语义
- 友机 reply 优先把 `identity` 从 `Unknown` 提升到 `Friendly`

P1 不建议做：

- 完整 Mode 4/5 密钥与时间同步
- 欺骗性 IFF
- 完整 NCTR 识别链

关于 `NCTR`：

- `NCTR` 可以在 P1 只预留字段或 source slot
- 具体微多普勒/JEM 识别逻辑继续留到 `P2`

#### 4. 多源融合的保守落地

建议文件范围：

- [src/components/systems/track_management.h](/home/void0312/Workshop/CMO/src/components/systems/track_management.h)
- [src/systems/systems/track_manager_system.h](/home/void0312/Workshop/CMO/src/systems/systems/track_manager_system.h)
- [src/systems/systems/data_link_system.h](/home/void0312/Workshop/CMO/src/systems/systems/data_link_system.h)

P1 建议做：

- 增加 `source_mask`
- 允许 `TrackSource::Fused` 真正出现
- 对 `Radar + DataLink` 做最小融合规则：
  - 本地更新优先刷新几何
  - 数据链更新优先补足 stale track
  - 质量取加权或上限，而不是简单覆盖

P1 不建议做：

- `JPDA / MHT`
- 真正的 track-to-track 协方差融合
- 完整多传感器数据库

#### 5. 雷达参数化继续补一层

建议文件范围：

- [src/components/systems/sensor.h](/home/void0312/Workshop/CMO/src/components/systems/sensor.h)
- [src/models/systems/default_sensor_model.cpp](/home/void0312/Workshop/CMO/src/models/systems/default_sensor_model.cpp)
- `examples/config/database/aircraft/modules/sensors/*.json`
- `examples/config/database/ships/` 下相关传感器配置

P1 建议做：

- 按 `SensorType` 推导/校验默认 `range_power`
- 明确 `reference_range_m / reference_rcs_m2 / reference_snr_db` 的标定口径
- 继续使用前/侧/后 RCS，但把参数表补成可追溯值
- 让 `doppler notch` 由硬常量向“可调阈值/可调退化”推进一步

P1 不建议做：

- 完整 `Pt / G / lambda / B / F / PRF` 方程级参数化
- `Swerling 0-IV`
- 波形/PRF 自适应切换

### 4.2 明确继续留到 P2 的内容

以下项目应继续留到 `P2`，避免 P1 失控：

1. 完整 `Kalman / IMM / JPDA / MHT`
2. 真正摆脱 `entity_id` 的轨迹关联体系
3. 完整 Link 16 / J-series / reporting responsibility / 时隙容量
4. 完整 `Mode 4/5`、时钟同步、加密问答
5. `NCTR` 的微多普勒/JEM 识别
6. 详细地形遮蔽、海杂波图、地杂波图、波导传播
7. 完整雷达参数方程、波形切换、Swerling 闪烁
8. DRFM / RGPO / VGPO / 角度欺骗
9. IRST / MAWS / DAS 的独立高保真建模

---

## 五、建议文件范围

### 5.1 P1 前置集成收尾

- `src/content/unit_definition_loader.cpp`
- `src/models/core/default_unit_factory.h`
- `src/core/engine/simulation_kernel_observation_api.cpp`
- `src/interfaces/python/bindings_core.cpp`
- `src/interfaces/python/bindings_command.cpp`
- `python/testing/runtime.py`
- `tests/runtime/test_bindings_command_surface.py`
- `tests/runtime/test_sensor_situation_realism_p0.py`
- 其他受影响的 runtime/contract 测试

### 5.2 P1 深化真实化

- `src/components/systems/sensor.h`
- `src/components/systems/track_management.h`
- `src/models/systems/default_sensor_model.cpp`
- `src/models/environment/default_environment_model.cpp`
- `src/systems/systems/track_manager_system.h`
- `src/systems/systems/data_link_system.h`
- `examples/config/database/aircraft/modules/sensors/*.json`
- `examples/config/database/aircraft/units/*.json`
- `examples/config/database/ships/**/*.json`

---

## 六、最小测试清单

### 6.1 前置集成收尾

1. `sensor` 新字段可从配置正确读入，且默认值稳定。
2. Python observation 能看到 `track status / quality / confidence`。
3. Python `Detection` 能看到 `snr_db / detection_prob_used / measured_vr`。
4. `ReportTrack` 与 `ReportContact` 在 Python 面兼容存在。
5. 运行测试不再把接收方本地 `ContactList` 当成数据链共享结果。

### 6.2 深化真实化

1. 雨/雾等最小天气衰减会降低远距 `Pd`，且趋势单调。
2. look-down / low radial velocity 目标在 clutter penalty 下更难确认。
3. `2-of-3` 不再只是累加命中，而是对 miss/窗口语义有明确表现。
4. `Coasted` 航迹质量会随时间下降，并在超时后 drop。
5. 友机 IFF reply 能让 `identity` 从 `Unknown`/`AssumedFriendly` 向 `Friendly` 收敛。
6. 同一目标的 `Radar + DataLink` 不再生成重复航迹，且 `Fused/source_mask` 语义成立。

### 6.3 回归守门

1. `naval_screen`、`mission_runtime`、`air_combat_1v1` 中与态势相关的关键场景至少抽样复跑。
2. 若仍存在 unrelated 失败，需在验收记录里区分：
   - 本线引入
   - 历史存在
   - 共享集成导致

---

## 七、数据源落地方案

P1 不追求机密级型号复刻，但必须把参数来源做成“可追溯、可替换、可分级”。

### 7.1 数据源分级

#### A 级：优先采用

- MathWorks 公开 Radar/Tracking 文档
- ITU-R 公开建议书
  - 雨衰减
  - 大气吸收
  - 无线电地平线/路径损耗相关公开模型
- 公开目标跟踪教材/alpha-beta filter 资料

适用：

- `Pd/SNR`
- `M-of-N`
- `alpha-beta`
- 天气衰减
- 无线电视距

#### B 级：工程可用

- 公开平台/雷达宣传资料
- AWACS、舰艇桅顶高度、雷达量级、典型扫描周期
- 公开 RCS 量级区间、目标分类资料

适用：

- `reference_range_m`
- `reference_rcs_m2`
- 舰艇/预警机高度
- fighter radar / AWACS baseline defaults

#### C 级：仅作初值或 sanity check

- 社区数据库
- 军迷资料
- 论坛整理
- 开源仿真配置

适用：

- 没有更好来源时的初始参数
- 与 A/B 级资料交叉检查

### 7.2 落地方式

建议同时保留两层落地：

1. `代码配置层`
   - 把最终采用的默认参数写入 `examples/config/database/.../sensors/*.json`
2. `溯源文档层`
   - 在 `docs/task/flight_dynamics/` 下新增一份参考表文档或表格文件
   - 至少记录：
     - 参数名
     - 采用值
     - 适用对象
     - 来源级别
     - 公开来源描述
     - 是否为工程近似

P1 不建议现在就把数据源溯源塞进 README 或任务总表。

---

## 八、验收口径

P1 完成后，至少应满足：

1. `P0` 新字段和新语义已打通到配置、运行时、observation 和 Python。
2. 态势主合同不再混淆“本地探测 contact”和“共享 track”。
3. track 的 `status / quality / source` 能被上层稳定读取。
4. 环境、IFF、融合、航迹质量至少各有一项真实化进入运行结果，并有守门测试覆盖。
5. 旧测试语义已迁移或显式废弃，不再默认接受旧 truth-style 行为。

---

## 九、推荐实现顺序

### 步骤 1

先补 `loader / factory / observation / binding`，把 P0 的字段和语义真正打通。

### 步骤 2

统一迁移旧测试合同，特别是数据链共享和 observation 表面。

### 步骤 3

细化 `track status / quality / sliding M-of-N / coast-drop`，让航迹语义先稳住。

### 步骤 4

引入保守环境/杂波与最小 IFF 状态机，让“发现-确认-识别”链条第一次完整一些。

### 步骤 5

做 `Radar + DataLink` 的最小融合与 `TrackSource::Fused` 落地，再补一层雷达参数化。

---

## 十、P1 与 P2 的边界总结

### 应保守纳入 P1

1. 新字段的 `loader/factory/observation/binding` 收尾
2. 旧测试语义迁移
3. `track status / quality / M-of-N` 细化
4. 最小天气衰减与 clutter penalty
5. 最小 IFF 状态机
6. `Radar + DataLink` 最小融合
7. 一层可追溯的雷达参数化与默认值校正

### 继续留到 P2

1. 完整多目标跟踪与复杂关联
2. 完整 Link 16 协议仿真
3. 完整 Mode 4/5 与 NCTR
4. 详细环境传播与杂波场
5. 完整雷达方程与波形/PRF
6. 欺骗干扰与高保真 ECM/ESM

本包冻结到下一次明确重开方向二任务前为止。
