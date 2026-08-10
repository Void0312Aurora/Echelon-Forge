# Flight-Control / Hydraulic / Fuel / Fire / Sensor / Crew 后果模型路线

状态：`2026-05-28` 平台后果路线。本文把组件损伤到平台能力下降拆成六条可工程化后果线；每条线都应保持 monotonic、bounded、auditable，并明确哪些参数必须等校准。

## 共同建模规则

- 后果线读取 component integrity、redundancy group availability、dependency graph system availability 和 `AircraftDamageState`，不从 RL reward 或 HP 反推物理结果。
- 每条线先定义工程化 0-1 integrity/capability，再由 `AircraftDamageState` 下推到 `PlatformDamageState`。
- 所有阈值、速率、概率在未授权前只可标注为 engineering scaffold。
- live missile 测试只验证事件链路和审计字段，精确后果用 deterministic local hit diagnostics 固定。
- 不同平台族允许不同 projection，例如 fixed-wing、rotorcraft、UAV、C2 large aircraft 不共享同一 mobility kill 解释。

## 1. Flight-Control 后果线

当前已有：flight-control components、aileron/elevon/rudder/flap/thrust-vector/cyclic/collective 等代表控制件，三轴 control integrity、control asymmetry、turn-rate/g-limit/accel/climb 派生。

后续路线：

1. 把控制件映射到 axis role：roll、pitch、yaw、lift augmentation、thrust vector、rotor cyclic、rotor collective、tail rotor yaw。
2. 引入 axis authority aggregation：同轴多作动器按冗余组和左右侧位置合成 authority。
3. 引入 asymmetry model：左右或前后不均衡损伤增加 `control_asymmetry`，但不立即等价 mobility kill。
4. 把 flight-control computer、power bus、hydraulic supply 纳入依赖图。
5. 区分 fixed-wing 与 rotorcraft：rotor collective/cyclic/tail-rotor failure 应走 helicopter-specific mobility/forced landing 规则。

必须等校准：真实控制律、气动导数、控制面效率、作动器力矩/速率、失控边界、spin/departure、fly-by-wire degraded mode。

## 2. Hydraulic 后果线

当前已有：`hydraulic_integrity`、`hydraulic_pressure_availability`、hydraulic pump 组件、flight-control actuator 对 hydraulic 的依赖、液压损伤继续拖累飞控并增加结构过载暴露。

2026-05-29 最小增量：新增 `hydraulic_pressure_availability` 作为 pressure/capacity 工程代理。hydraulic pump/source 命中会比普通 actuator 更强地降低 pressure availability；flight-control actuator/servo 的 `hydraulic_power` 依赖可产生较小压力损失；`AircraftDamageStateUpdate` 会把压力不足和 `hydraulic_integrity` 一起投射到 flight-control 派生、turn-rate 和 mobility capability。该语义仍不是真实液压回路、蓄压器时间常数、管线隔离或压力-作动器曲线。

后续路线：

1. 分离 hydraulic source、line、reservoir、actuator consumer 四类节点。
2. 引入 pressure/capacity 代理值，用 0-1 表达残余 hydraulic availability。（`hydraulic_pressure_availability` 已启动）
3. 把 hydraulic availability 投射到 axis authority，而不是直接全局降低 flight_control。（pressure 已进入 aggregate control；按轴 hydraulic supply 分配仍未启动）
4. 对多液压源平台引入 load-sharing 和 isolation scaffold。
5. 对 helicopter 增加 rotor servo 对 hydraulic pressure 的高权重依赖。

必须等校准：真实液压回路、压力-作动器曲线、泄漏速率、蓄压器时间常数、隔离阀逻辑和平台 specific redundancy。

## 3. Fuel 后果线

当前已有：fuel system integrity、fuel leak severity、FuelSystem 油量消耗、Mass 燃油质量同步、engine fuel control/feed 组件和 wing/fuselage fuel cells。

2026-05-29 最小增量：fuel storage 与 engine fuel feed/control 已开始分化。普通 fuel cell 命中仍主要造成 fuel integrity、fuel leak、fire risk 和 quantity loss，不直接等价 thrust loss；命名 `*_fuel_feed` / `*_fuel_control*` 组件或 `edge_type=fuel_feed` 依赖会额外投射到 `propulsion_integrity` / mobility，表示工程化 engine starvation 后果。left/right wing fuel storage 命中会额外写入 `fuel_imbalance_severity`，并在后续帧轻微增加 control asymmetry / 降低 roll authority；center fuselage fuel cell 与 engine fuel feed 不触发该左右不平衡语义。该语义仍非校准供油管路、阀门、油压、油箱几何、横向重心或发动机控制模型。

后续路线：

1. 区分 fuel storage、fuel feed、fuel control、fuel quantity、fuel leak、fuel fire risk。
2. 让 fuel storage hit 主要产生 leak/quantity loss/fire risk，不直接等价 thrust loss。（最小工程语义已启动）
3. 让 fuel feed/control hit 影响 engine starvation、propulsion integrity 和 forced landing。（propulsion integrity 影响已启动；forced landing 仍由既有低 propulsion / fuel exhaustion 阈值间接触发）
4. 引入 internal/external fuel 分层和左右侧 fuel imbalance scaffold。（左右侧 engineering overlay 已启动；internal/external fuel 分层仍未启动）
5. 对 large aircraft/helo 分别处理多油箱、多发动机供油和 mission endurance 后果。

必须等校准：油箱位置/容积、管路和阀门、燃油类型、自密封能力、泄漏截面积、耗油率变化、燃油不平衡飞行影响。

## 4. Fire 后果线

当前已有：fire severity、fuel leak/fire 级联、火灾对结构、航电、机组、液压和燃油系统的时间传播。

2026-05-29 最小增量：新增 `flammable_fluid_exposure`、`ignition_source_severity` 与 `fire_suppression_integrity` 三个 aircraft overlay 轴。fuel/hydraulic leak 作为可燃流体暴露代理，engine/avionics/mission-system 损伤作为点火源代理，E-3 engine fire bottle 已从普通 `fuel` 组件改为 `fire_suppression` 组件；`AircraftDamageStateUpdate` 会从 `ComponentDamageState` 的 suppression 组件/冗余组可用性派生 suppression integrity，命名 suppression 冗余组存在时优先使用组可用性，并用它调制 fire growth / extinguish decay。新增 engine bay、wing、fuselage、mission bay 四个 fire-zone severity，用组件/系统命名把局部火源投射到不同二次损伤方向。该语义仍是工程化状态机，不是校准点火概率、灭火成功概率、喷嘴/灭火剂分布或真实 fire-zone 模型。

后续路线：

1. 区分 ignition risk、active fire、fire spread、suppression availability、secondary damage。（最小 overlay 已启动）
2. 把 fire source 绑定到 fuel、engine、avionics、电源、hydraulic fluid 等不同源。（flammable/ignition 代理已启动）
3. 引入 fire compartment/zone scaffold：nose、fuselage、engine bay、wing、rotor/transmission、mission bay。（engine/wing/fuselage/mission 四区 engineering overlay 已启动；nose、rotor/transmission 和真实邻接图仍未启动）
4. 让 fire suppression components 通过 dependency graph 降低 spread rate 或 active fire duration。（E-3 fire bottle 的最小 direct component path 已启动）
5. 对 crew/mission systems 增加 smoke/heat incapacitation 的工程化影响，但保持非权威。

必须等校准：点火概率、热释放、灭火系统能力、舱段通风、火焰传播、烟雾毒性、结构热损伤速率。

## 5. Sensor 后果线

当前已有：avionics/crew/mission crew/command-navigation 到 sensor range、Pd、noise、track memory 的派生；radar/sensor payload/data-link/mission systems 组件样例；E-3 radar hit 会降低 sensor/mission capability。

后续路线：

1. 分离 sensor aperture/antenna、receiver/transmitter、processor、cooling/power、operator/mission system、data link。
2. 按 sensor mode 投射后果：radar、IRST/EO、ESM、SAR、surface-search、rotodome radar。
3. 把 sensor damage 映射到 max range、detection probability、false alarm/noise、track memory、update rate 和 classification quality。
4. 对 C2/AEW 平台增加 mission crew/operator consoles 和 data-link relay 对 sensor exploitation 的影响。
5. 对 UAV 增加 command/data-link loss 对 sensor tasking 和 report latency 的影响。

必须等校准：真实 radar equation 参数、阵面损伤到增益/Pd 曲线、处理机/冷却/电源 degradation、operator workload、track fusion 质量。

## 6. Crew 后果线

当前已有：crew effectiveness、pilot effectiveness、mission crew effectiveness、command/navigation integrity；cockpit crew station、mission operator consoles、flight deck crew station 等组件。

后续路线：

1. 分离 pilot/control crew、mission crew/operator、command/navigation crew、remote operator/UAV command link。
2. 把 pilot effectiveness 主要投射到 control authority、forced landing 和 mobility capability。
3. 把 mission crew effectiveness 投射到 sensor exploitation、mission capability、data-link/tasking。
4. 把 command/navigation integrity 投射到 mission coordination、navigation quality 和 C2 platform effectiveness。
5. 增加 crew station 与 fire/smoke、cockpit hit、avionics loss 的依赖传播。

必须等校准：人员伤害准则、座舱防护、冗余乘员职责、任务岗位替代、伤害到操作能力的时间线。

## Loss State 投射建议

| 后果 | 工程投射 | 边界 |
|---|---|---|
| `SensorKill` | sensor capability 低于阈值，且 mission/sensor consumers 可观察 | 不等价 aircraft destroyed |
| `MissionKill` | mission crew、avionics、command/navigation、payload 或 data-link 使任务无法继续 | 不等价 Pk |
| `MobilityKill` | flight-control、hydraulic、propulsion、结构或 rotor/drive train 使平台无法继续有效飞行/机动 | 固定翼/直升机/UAV/C2 阈值应分族 |
| `ForcedLanding` | overlay 状态，不应通过重排 `PlatformLossState` 枚举实现 | 可作为 aircraft-only 后果和训练读数 |
| `Lost` | 结构/火灾/控制/推进/机组等综合达到平台丧失条件 | 未校准前不要作为真实 kill probability |
