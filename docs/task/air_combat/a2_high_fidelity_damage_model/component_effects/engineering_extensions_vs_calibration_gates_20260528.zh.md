# 可工程化扩展项 vs 必须等校准项

状态：`2026-05-28` 路线边界。本文区分可以继续工程推进的数据结构/确定性规则/审计面，以及必须等待校准数据或 validated surrogate 后才能声明 authority 的内容。

## 可工程化扩展项

这些项目可以在不声称真实 Pk 或真实平台脆弱性的前提下继续推进：

| 方向 | 可做内容 | 验收口径 |
|---|---|---|
| 组件 taxonomy | 冻结 `system`、`component name`、`redundancy_group_id` 命名规范，定义 fighter/UAV/helo/C2 的最小必备系统族 | JSON lint、schema fixture、跨平台 inventory report |
| 几何覆盖 | 为当前代表平台补齐可解释 hitbox/component 几何，增加 left/right、forward/aft、upper/lower 语义 | direct local hit 能稳定选中预期组件，event 记录 primary component |
| 依赖图 schema | 把 `dependencies` 从 `system+scale` 扩展为 typed edge，例如 supply、control-signal、cooling、data、hydraulic-power、crew-operated | loader 接受旧 schema，event 能暴露依赖传播摘要 |
| 冗余组状态 | 继续完善 group availability、member count、failed count、weighted availability、single-point criticality | 连续命中同组组件时组可用性单调下降，非同组不误降 |
| aircraft overlay | 继续把组件损伤映射到 `AircraftDamageState` 的结构、飞控、液压、燃油、火灾、传感器、机组字段 | overlay 单调/有界，平台 capability 与 sensor/flight/fuel consumers 可观察 |
| 诊断 API | 增加只读 debug helpers，固定局部命中点、warhead profile、component identity、依赖传播结果 | diagnostics-only，不进入战术 AI authority |
| 事件契约 | 固定 `EffectsEvent` 和 `DamageReport` 字段，新增字段保持 append-only 或兼容缺省 | engagement contract shape tests |
| 验收场景 | 为每条后果线建立 deterministic local hit 回归和 live missile smoke 分层测试 | local hit 判断后果，live missile 判断事件链路 |
| 文档与边界 | 给每个 platform family 写 modeling note 和 non-authoritative disclaimer | 文档、schema、event provenance 一致 |

## 必须等待校准项

以下项目不能仅靠工程 scaffold 放行 authority：

| 方向 | 需要的外部或校准证据 | 不得提前声明 |
|---|---|---|
| component failure probability | 外部校准数据、试验数据、已验证 physics surrogate 或经审计的 vulnerability evidence rows | “组件命中概率真实”“失效概率可信” |
| Pk / mission kill probability | target/weapon/aspect/closure/miss-distance 轴齐备的 calibrated dataset，且通过 authority gate | “Pk 完成”“一发杀伤概率可信” |
| deterministic fuze | 引信模型、探测器可靠度、目标 signature、PN miss-distance 基线和 kill-chain 验证 | “确定性引信放行”“RNG hit roll 可移除” |
| warhead spatial effects | 破片云、连续杆展开/切割、blast overpressure/impulse、HTK 接触几何的校准或验证 surrogate | “真实破片云”“真实连续杆切割” |
| fuel/fire propagation rates | 燃油类型、管路/油箱、自密封、灭火、通风、热传导和时间尺度证据 | “真实火灾扩散速率”“真实燃油耗尽时间” |
| hydraulic failure thresholds | 液压系统架构、泵/管路/蓄压器/隔离阀、压力-作动器 authority 曲线 | “真实液压残余控制能力” |
| flight-control controllability | 控制律、气动导数、surface effectiveness、actuator rate/force、飞控计算机 degraded mode | “真实可控性/失控边界” |
| crew casualty/incapacitation | 人员位置、座舱防护、伤害准则、任务岗位替代规则 | “真实人员杀伤或任务岗位伤亡率” |
| sensor degradation curves | 雷达/IRST/EO/ESM 架构、阵面/处理机/电源/冷却/天线损伤到 Pd/range/noise 的证据 | “真实探测概率和量测误差曲线” |

## 分层放行原则

1. **结构先行**：先让 component identity、mechanism load、redundancy state 和 dependency propagation 可审计。
2. **工程后果可用但不权威**：允许 monotonic、bounded、可解释的 capability degradation 作为训练和回归的工程近似。
3. **概率和阈值必须 gate**：任何概率、阈值、扩散速率、kill probability、deterministic fuze claim 都必须由 calibrated evidence 或 validated surrogate 授权。
4. **event 必须说清来源**：同一字段被 synthetic scaffold、engineering surrogate 或 calibrated row 驱动时，事件面必须能反查 source、calibration status、authority flag 和 row provenance。
5. **测试不能把工程近似写成真值**：测试应固定“方向、单调、有界、可审计、分层消费”，不固定未校准的真实数值。

## 当前建议

短期继续推进工程化扩展项，尤其是 taxonomy、依赖图 schema、后果 overlay 和验收测试；同时保持 vulnerability evidence descriptor 的 authority gate 严格关闭。中期再为一个窄场景选择 calibration candidate，例如 `F-16C_Block50` vs AIM-120C blast-fragmentation beam/high near miss，把 component failure probability、effect scale 和 Pk 分开校准，不把一个数据源泛化成全域 authority。

