# 真实化 P1 任务总表

状态：`2026-05-17` 验收后收敛版。

关联文档：

- [真实化任务总表（P0）](realism_program_taskboard_20260516.zh.md)
- [飞行动力学真实化 P1 实施包](../flight/flight_dynamics_realism_p1_implementation_package_20260517.zh.md)
- [传感器/态势真实化 P1 实施包](../sensor_situation/sensor_situation_realism_p1_implementation_package_20260517.zh.md)
- [武器/制导真实化 P1 实施包](../weapon_guidance/weapon_guidance_realism_p1_implementation_package_20260517.zh.md)

文档目的：

- 把 `P0` 验收中暴露出的“未正式签收项”统一收编到 `P1`。
- 明确哪些内容属于 `P1 前置集成收尾`，哪些属于 `P1 深化真实化`。
- 给主线程后续排期、分支拆分和测试验收提供统一入口。

---

## 一、为什么把这些问题并入 P1

本次 `P0` 已经完成了三条线的最小真实性骨架：

1. 飞行动力学已经具备最小 `aero / propulsion / stall` 趋势。
2. 传感器/态势已经具备最小 `SNR/Pd / M-of-N / alpha-beta / track-report` 语义。
3. 武器/制导已经切断 target truth 直读，并具备最小 `3DoF + PN accel surrogate`。

但验收同时说明，这些成果还没有完全变成“系统级正式能力”。

暴露出来的问题大多不是“方向错了”，而是：

1. 新字段和新状态已经在运行时存在，但还没有完整接进 `loader / factory / database / binding / observation`。
2. 旧测试和旧接口仍带着 `P0` 之前的语义假设。
3. 部分实现仍保留 `default constant / lazy init / debug-only path` 这类过渡写法。

因此，这些问题更适合并入 `P1`，原因是：

1. 它们已经超出 `P0 最小骨架` 的目标。
2. 它们又明显早于 `P2` 那类更重的模型深度扩展。
3. 如果不先收掉这些集成债，后续更深的真实性工作会继续建立在半接通的接口上。

需要强调的是：

- 这些问题虽然并入 `P1`，但不应和更深的真实性建模混在同一优先级。
- `P1` 必须先做“前置集成收尾”，再做“深化真实化”。

---

## 二、P1 的两层结构

### 2.1 P1-A：前置集成收尾

这一层处理：

1. 配置与数据库挂接
2. shared runtime 语义对齐
3. observation / Python binding 暴露
4. 旧测试合同迁移
5. 生命周期、构建、测试入口稳定化

判断标准不是“模型更复杂”，而是“P0 骨架真正接入主线”。

### 2.2 P1-B：深化真实化

这一层处理：

1. 飞行动力学更完整的 `Mach / compressibility / engine transient / stall semantics`
2. 传感器更完整的 `track quality / minimal clutter / minimal IFF / minimal fusion`
3. 武器更完整的 `seeker type / midcourse / parameterized 3DoF / fuze-damage layering`

判断标准不是“接口接通”，而是“因果链更接近可信战术仿真”。

---

## 三、P1-A 前置集成收尾

这是 `P1` 的第一阶段，也是推荐最先开的工作包。

### 3.1 跨三线共同目标

1. 新字段不再只靠结构体默认值或代码常量生效。
2. 新运行时状态能被上层观测、测试和 Python 接口稳定看到。
3. 旧语义不再偷偷穿透新系统。
4. 构建与测试入口可重复、可交接、可解释。

### 3.2 三条线的前置收尾重点

#### 飞行动力学

1. `AeroTuning / EngineTuning / StallState` 打通 `unit_definition -> loader -> factory`
2. `Propulsion` 成为 `Force / Logistics / Instrument / Observation` 的一致事实来源
3. `propulsion_system` 明确是否正式注册为独立系统
4. 修复 runtime test / `ef_py` 生命周期不稳定问题

#### 传感器/态势

1. `Sensor` 新字段完成 `loader / factory` 默认值与数据库接线
2. `Track status / quality / Detection` 扩展字段进入 observation 与 Python binding
3. 旧测试从“共享 contact 伪装成本地探测”迁移到“共享 track report”语义
4. 收紧 `build -> ef_py -> runtime tests` 标准路径

#### 武器/制导

1. `MissileTuning` 正式扩展进入 shared API
2. 发射阶段正确初始化导弹质量、推进剂与运行时状态
3. seeker / energy / autopilot 关键状态进入 Python/debug 观测面
4. 固定 missile `heading / ground track / seeker reference` 的 shared 语义

### 3.3 P1-A 建议顺序

建议顺序：

1. `schema + loader/factory`
2. `shared runtime semantics`
3. `observation + binding`
4. `test contract migration`
5. `runtime lifecycle stabilization`

不建议的顺序：

- 先做更复杂公式，再回头补配置和接口

---

## 四、P1-B 深化真实化

这一层在 `P1-A` 稳定后展开。

### 4.1 飞行动力学

优先项：

1. 更完整的 `Mach / drag rise / compressibility` 调度
2. 更真实的发动机瞬态、干推/加力语义
3. 更真实的 `stall / post-stall / hysteresis / recovery`
4. 首批机型参数表与来源分级

### 4.2 传感器/态势

优先项：

1. `track status / quality / coast-drop` 细化
2. 最小 clutter / weather penalty
3. 最小 IFF 状态机
4. `Radar + DataLink` 最小融合
5. 第一批可追溯雷达参数表

### 4.3 武器/制导

优先项：

1. seeker type 分化
2. `ARH midcourse + activation + datalink`
3. 参数化 `3DoF boost/sustain/coast + drag + mass`
4. fuze / damage layering
5. countermeasure interaction 第一版

---

## 五、哪些内容继续留到 P2

为了避免 `P1` 再次失控，下面这些内容继续留到 `P2`：

1. 飞行动力学完整二维/三维查表、完整 FBW、完整 post-stall/spin
2. 传感器完整 `JPDA / MHT / full Link 16 / full Mode 4/5 / NCTR / high-fidelity propagation`
3. 武器完整 `6DoF missile / DRFM/HOJ 高阶逻辑 / 完整破片几何 / 型号级高精度复刻`

---

## 六、推荐的主线程拆分

建议按下面顺序拆任务，而不是按学科边界各自单飞：

1. `P1-A1 schema/integration PR`
   - 三条线的 `loader / factory / shared init` 一次收口
2. `P1-A2 observation/binding PR`
   - 三条线的新状态统一暴露
3. `P1-A3 test-contract PR`
   - 更新旧测试语义，固定 runtime 测试入口
4. `P1-B1 dynamics PR`
   - 先推进飞行动力学深化
5. `P1-B2 tracking PR`
   - 再推进传感器/态势深化
6. `P1-B3 missile PR`
   - 最后推进武器/制导深化

这样拆的好处是：

1. 先解决所有方向共享的“接口未接通”问题
2. 再进入更重的真实性改进
3. 每轮都有清晰验收面，不会把兼容债和模型深度改动混在一起

---

## 七、P1 总体验收口径

`P1-A` 完成后，至少应满足：

1. 三条线的 `P0` 新字段和新状态都能从配置、运行时、观测、Python 面被一致访问。
2. 旧测试不再依赖 `P0` 前语义。
3. runtime 测试入口稳定，不再依赖规避式技巧。

`P1-B` 完成后，至少应满足：

1. 平台、传感器、武器三条因果链的输入输出关系更接近公开资料支持的工程语义。
2. 真实化参数开始进入数据库与参考表，而不是继续散落在代码默认常量中。
3. 可以重新评估更深入训练和更强场景结论的可信度。

---

## 八、当前建议

如果现在就继续推进，建议不是立刻改更复杂公式，而是：

1. 先按这份任务总表开 `P1-A`。
2. 把本次验收暴露的未签收项统一消化掉。
3. 再根据三条分包进入 `P1-B`。

当前最值钱的结论不是“P0 不够”，而是：

- `P0` 已经把方向走对了
- `P1` 的首要任务是把这条方向变成主线正式能力
- 然后再继续把真实性往更深处推
