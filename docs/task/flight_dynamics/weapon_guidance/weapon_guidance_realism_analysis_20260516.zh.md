# 武器系统与制导回路现实性分析

状态：`2026-05-16` 冻结分析版。

关联文件：

- [Missile 组件定义](../../../../src/components/combat/weapon.h)
- [Ammo / WeaponCooldown / Munition 组件](../../../../src/components/combat/weapon.h)
- [HitboxConfig / SystemHealth 组件](../../../../src/components/combat/damage.h)
- [Health / Score 组件](../../../../src/components/combat/health.h)
- [IGuidanceModel 接口](../../../../src/core/interfaces/guidance_model.h)
- [IEffectsModel 接口](../../../../src/core/interfaces/effects_model.h)
- [DefaultGuidanceModel（PN 制导）](../../../../src/models/weapons/default_guidance_model.cpp)
- [DefaultEffectsModel（命中效果）](../../../../src/models/weapons/default_effects_model.cpp)
- [DamageSystem（近炸引信）](../../../../src/systems/combat/damage_system.h)
- [SimulationKernel 武器 API（发射逻辑）](../../../../src/core/engine/simulation_kernel_weapon_api.cpp)
- [武器与交战规则路线图](../../../systems/weapons/work/issues/weapons_engagement.zh.md)
- [传感器与态势感知现实性分析（关联）](../sensor_situation/sensor_situation_realism_analysis_20260516.zh.md)
- [飞行动力学现实性分析（关联）](../flight/flight_dynamics_realism_analysis_20260516.zh.md)

文档定位：

- 本文档仅记录已知缺陷及其对应的真实物理/工程情况。
- 不涵盖可接受的简化，不提供优先级排序，不给出工作计划。
- 当前判断以本分析中的 `2026-05-18` 收口标记为准，不再引用 `program/` 或 `archive/` 作为当前状态来源。

## 补记：`2026-05-18` 收口标记

标记口径：

- `未解决`：原论点基本仍成立。
- `部分解决`：已有局部实现或运行时守门，但核心真实性缺口仍在。
- `已有最小收口`：不宜再按“完全缺失”表述，最小可运行闭环已存在。
- `已解决`：该条旧论述已不再适合作为当前状态描述。

本补记仅用于回答这些论点今天还是否可直接当作当前问题。

| 条目 | 当前标记 | 说明 |
|------|----------|------|
| 第一节当前武器管线 | `部分解决` | 当前应按 `seeker-only guidance + 最小 3DoF/PN-autopilot surrogate + shared missile tuning` 重读，不再是旧版单层链路 |
| `2.1` 速度向量旋转替代加速度指令 | `已有最小收口` | 已有有界侧向加速度与响应滞后的最小 surrogate，但仍非完整弹体动力学 |
| `2.2` 无导弹自动驾驶仪环节 | `已有最小收口` | `autopilot_tau` 等最小内环语义已接入，但仍不是完整 autopilot/body dynamics |
| `2.3` LOS 率计算使用真实目标位置 | `已解决` | 当前制导已消费 detection/track state 与过滤后的 track memory，不再直接依赖原始目标真值位置/速度 |
| `2.4` 诱饵逻辑是粗糙 seduction 近似 | `未解决` | 仍缺 centroid、运动学鉴别和更真实诱饵时序 |
| `2.5` 导航增益为固定常量 | `部分解决` | `nav_gain` 已进入 shared tuning，但仍非真实变增益制导 |
| `2.6` 坐标体系中的符号不一致 | `部分解决` | 当前符号口径已有守门线，但这条更接近结构/验证债务而非主行为红点 |
| `3.1` 恒定速度——无推力/阻力/质量变化 | `已有最小收口` | `boost/sustain/drag/mass depletion` 已进入运行时 |
| `3.2` 最大速度的意义被扭曲 | `部分解决` | 速度已不再恒定，但仍未形成更可信的包线级解释 |
| `3.3` 气动阻力完全缺失 | `已有最小收口` | 多类阻力项已进入运行时与守门测试 |
| `4.1` 导引头传感器是完整副本 | `部分解决` | 现状更接近 `seeker-only` 最小实现，但 seeker 分型仍未深化 |
| `4.2` 锁定距离与 FOV 未反映真实约束 | `已有最小收口` | `sensor_max_range / seeker fields / activation range` 已接通，但仍非真实导引头约束模型 |
| `4.3` 缺少发射前锁定（LOBL）要求 | `已解决` | `lobl_required` 已进入正式拒射守门 |
| `4.4` 无目标识别/拒止能力 | `未解决` | 仍缺 seeker discrimination / reject contract |
| `5.1` 引信逻辑无法分辨脱靶方向 | `未解决` | 末段几何与方向性引信仍未收口 |
| `5.2` 命中概率模型品质-规避耦合不合理 | `未解决` | 命中概率合同仍未重构 |
| `5.3` 引信延迟和破片传播时间缺失 | `未解决` | 引信时序仍未进入当前主线 |
| `6.1` HP 扣除与几何毁伤双轨不一致 | `未解决` | `HP` 路径与 subsystem 路径仍未统一 |
| `6.2` 部件毁伤是二值瞬杀 | `已有最小收口` | `PlatformDamageState` 与命中后持续退化已提供最小连续毁伤路径，但更高保真 subsystem 模型仍缺 |
| `6.3` 坐标变换存在不确定性 | `部分解决` | 当前更像验证债务，尚无证据表明它仍是主行为红点 |
| `6.4` 无战斗部类型区分 | `未解决` | warhead family 仍未进入运行时 |
| `7.1` 无发射包线判断 | `已有最小收口` | `min range / off-boresight / LOBL` 已形成最小拒射合同 |
| `7.2` 无快速射击/多目标发射限制 | `部分解决` | `ammo/cooldown` 已在，但更真实 salvo/多目标约束仍缺 |
| `8.1` 无中制导数据链 | `已有最小收口` | `midcourse_datalink_supported / seeker_activation_range_m` 已接通 |
| `8.2` 发射高度/速度对 `Pk` 影响为零 | `已解决` | 发射高度/速度已不再对导弹行为“零影响”，因为 atmosphere、drag、thrust 与 mass depletion 都会改变飞行剖面，但更广义 envelope/`Pk` 保真度仍未收口 |

---

## 一、当前武器管线的处理链路

```
fire_weapon_from_pilot_action / fire_missile()
  → 发射条件检查（弹药、冷却、存在接触航迹）
  → 导弹实体生成（继承载机速度、固定导弹参数）
  → 导引头Sensor组册（扫描周期 0.05s）

GuidanceSystem
  → DefaultGuidanceModel.update()
    → 延时 / 更新周期门控
    → 从 ContactList 选最强信号目标（诱饵逻辑）
    → PN 制导计算（LOS rate → 速度向量旋转）
    → 速度归一化为 max_speed（无能量变化）

DamageSystem（ProximityFuze）
  → 最近距离追踪
  → 距离开始增大时触发引信
  → fuse_distance 门控
  → 命中概率（距离品质 × 机动规避）
  → on_proximity_hit()

DefaultEffectsModel
  → 通用 HP 扣除
  → 几何命中盒判定 → 系统级毁伤（radar/engine/fuel）
  → 随机化退化毁伤（回退路径）
```

---

## 二、比例导航（PN）制导律的缺陷

### 2.1 速度向量旋转替代加速度指令

```cpp
// default_guidance_model.cpp:242-271
// 对速度向量执行 Rodrigues 旋转，然后归一化到 max_speed
double v_new_x = vm_x*cos_t + cross_x*sin_t + axis_x*dot*(1.0-cos_t);
velocity.vx = (v_new_x / vn_norm) * missile.max_speed;
velocity.vy = (v_new_y / vn_norm) * missile.max_speed;
velocity.vz = (v_new_z / vn_norm) * missile.max_speed;
```

真实 PN 制导律输出的是**加速度指令**（垂直于导弹速度向量），而非速度
向量的几何旋转。导弹通过气动控制面（或推力矢量）产生法向加速度来实现
转弯。当前实现直接旋转速度向量的后果是：

- 导弹的转弯是**瞬时完成的几何操作**，无气动响应延迟、无过载建立时间。
  真实导弹从接收加速度指令到弹体建立稳态过载需 0.05-0.2 秒
  （取决于空速和动压）。
- 速度向量的旋转本质上改变了导弹的飞行路径方向，但**不伴随产生
  法向加速度约束**。真实导弹的可用过载（以 G 为单位）由 `n_max = q_bar × CL_max × S / (m × g)` 确定，在低动压（高空/低速）时显著下降。
  当前模型的 `turn_rate` 限制是对角速率的约束，而非过载约束——这两个量在高空
  存在物理分歧（同样的角速率 → 低空需要高 G，高空需要低 G）。
- `turn_rate` 的单位硬限制在低速时可能允许物理上不可实现的急转弯，
  在高速时则可能过度约束（导弹高速时本应有更高的可用转弯角速率）。

### 2.2 无导弹自动驾驶仪（autopilot）环节

真实制导回路是：

```
导引头测量 → 跟踪滤波器(状态估计) → 制导律(加速度指令)
  → 自动驾驶仪(舵面/推力矢量指令) → 弹体动力学(过载响应)
  → IMU/加速度计(反馈) → 回到制导律
```

当前实现缺失整个自动驾驶仪和弹体动力学环节。制导律的输出
（LOS rate → 速度旋转）直接驱动运动学，没有经过：

- **舵回路**：执行机构（fin servo）的偏转速率限制（典型值 200-300°/s）
  和偏转角度限制（典型 ±25°）
- **弹体传递函数**：从舵偏角到弹体角速率再到法向加速度的空气动力学延迟。
  典型战术导弹的短周期时间常数约 0.05-0.15 秒
- **加速度/角速率反馈**：自动驾驶仪需要使用 IMU 的角速率和加速度
  测量来闭合内环，否则无法跟踪制导律的加速度指令

### 2.3 LOS 率计算使用真实目标位置

```cpp
// default_guidance_model.cpp:118-139
const Transform* t_pos = world.entity(missile.target_id).get<Transform>();
const Velocity* t_vel = world.entity(missile.target_id).get<Velocity>();
// ...
double rx = t_pos ? (t_pos->x - transform.x) : /* fallback */;
double vt_x = t_vel ? t_vel->vx : 0.0;
```

相对位置和相对速度直接取自目标的真实 `Transform` 和 `Velocity`，
而非从导引头测量值中估计。代码注释坦承此问题：

> "In a strict sense, we should use 'det->bearing' history to estimate rate.
>  For MVP High-Fidelity, using Truth for Guidance Law is acceptable."

真实情况下：

- 导引头仅提供**带有噪声的**方位角、俯仰角和距离（主动雷达）或角度
  信息（被动红外/半主动雷达）
- LOS 角速率必须从带噪声的角度测量序列中估计，通常使用 α-β 或
  Kalman 滤波器
- 测量噪声直接传播到 LOS 率估计噪声中，导致末端脱靶量随距离减小而增大
  （这是终端脱靶的最主要来源之一）
- 目标机动（weaving、急转弯）引入额外的 LOS 率估计滞后，
  当前模型因使用真实位置而完全绕过此问题

### 2.4 诱饵逻辑（信号最强选择）是粗糙的 seduction 近似

```cpp
// default_guidance_model.cpp:93-97
// Seduction Logic: Pick strongest signal
if (c.signal_strength > max_sig) {
    max_sig = c.signal_strength;
    best_det = &c;
}
```

真实导引头在遭遇诱饵时的行为取决于：

- **诱饵的运动学分离**：诱饵必须从载机视线中分离才能被导引头分辨。
  热诱饵在投放后的 0.1-0.3 秒内不能提供足够的角分离
- **导引头分辨率**：在诱饵和载机之间的角距离小于导引头瞬时视场（IFOV）
  或跟踪门（track gate）时，导引头跟踪的是两者的**能量中心（centroid）**，
  而非单个最强信号。centroid 跟踪会使导弹飞向目标与诱饵之间的
  某个点，而非任何一个
- **信号瞬态**：热诱饵有上升时间（0.1-0.5 秒达到峰值）和衰减（2-5 秒），
  在此过程中信号强度持续变化。当前模型的信号强度是瞬时固定值
- **运动学鉴别**：真实导引头不仅比较信号强度，还使用运动学滤波器
  判断接触是否可能是一个按照弹道飞行（惯性）的目标——热诱饵因质量小
  快速减速，其速度/加速度模式与载机显著不同

### 2.5 导航增益为固定常量

```cpp
double nav_gain = missile.nav_gain > 0 ? missile.nav_gain : 3.0;
```

真实 PN 制导的有效导航比（N'）通常为 3-5，但实际应用中：

- 有效导航比 `N' = N × Vc / Vm × cos(γ)`，其中 γ 是导弹速度向量与
  LOS 之间的夹角。当导弹处于大离轴角时（发射初期或目标急转弯），
  有效导航比显著降低
- 末端制导段通常使用更高的 N'（4-5）以减少脱靶量，中制导段使用
  较低的 N'（3）以保留能量
- 某些现代导弹使用**变增益制导律**：N' 随剩余飞行时间（t_go）变化

### 2.6 坐标体系中的符号不一致

代码中有多处坐标转换（NAV 到 math 坐标系）和正负号推断，
注释中出现了犹豫的设计思考：

```cpp
// 第 158-168 行：多种 PN 公式变体在注释中并存
// a_cmd = N * V_c * Omega (Scalar approximation) -> Direction?
// Vector form: accel = N * V_closing_scalar * (Omega x Unit(V_missile)) ?
// Actually usually applied perpendicular to LOS.
```

```cpp
// 第 218-220 行
// Heuristic approach matching "Rate of Turn of Velocity = N * Rate of Turn of LOS"
// Turn Rate Vec = N * Omega_vec.
```

这表明当前 PN 实现是**多轮迭代后的混合体**，并非单一清晰的制导律。
`omega × V_missile` 产生了加速度（力矩方向），然后转换为速度向量
的 Rodrigues 旋转——但结果是否正确取决于 `omega` 的叉积方向和
Rodrigues 旋转轴的一致性。没有单元测试或解析解验证这一转换的
等效性。

---

## 三、导弹运动学（能量模型）的缺陷

### 3.1 恒定速度——无推力/阻力/质量变化

```cpp
// default_guidance_model.cpp:268
double new_speed = missile.max_speed; // Assume sustains speed for now
velocity.vx = (v_new_x / vn_norm) * new_speed;
```

每次制导更新后速度归一化为 `max_speed`。这意味着：

- **导弹永远不减速。** 真实导弹经历：
  - 助推段（boost）：2-5 秒内加速到最大速度，发动机燃尽（burnout）
  - 续航段（sustain）：部分导弹有续航发动机维持速度，持续 10-60 秒
  - 滑翔段（coast）：燃尽后依靠惯性飞行，速度因气动阻力持续下降。
    典型中程空空导弹（如 AIM-120）在燃尽后的速度衰减可达 30-50%
    在最大射程处
- **导弹永远不消耗质量。** 真实导弹的固体火箭发动机燃烧期间，
  推进剂质量占发射总质量的 30-50%。燃尽后质量显著降低，
  可用过载相应增大。当前 `Mass` 固定为 80kg
- **高空/低空性能相同。** 在 40000ft 低密度空气中，气动控制面效率
  大幅下降（动压 ~1/4 海平面），导弹的可用过载显著降低。
  同时阻力的降低使滑翔段延长。当前模型的 `turn_rate` 限制
  完全不随高度/动压变化
- **发射速度继承失配。** 载机速度被正确继承到导弹初速，
  但随后被直接覆盖为 `max_speed`。若载机以 0.8M 发射，
  导弹瞬间被加速到 1000 m/s（≈ 3M），等同于拥有了无限加速能力
  的火箭发动机

### 3.2 最大速度的意义被扭曲

当前 `max_speed = 1000 m/s`（≈ Mach 2.9 海平面，≈ Mach 3.3 高空）
的角色从"最大可达速度"变为"恒定巡航速度"。真实导弹的
`max_speed` 是发动机燃尽时的峰值速度，具有以下特征：

- 仅在特定高度和发射条件下可达（载机高速发射 + 高空低阻）
- 持续时间极短（1-3 秒后即因阻力开始衰减）
- 低空发射时因空气密度高，峰值速度显著低于高空发射

### 3.3 气动阻力完全缺失

导弹作为一个在空气中高速运动的物体（Mach 2-4），应经历：

- **零升阻力**：型阻（摩擦 + 压差）∝ ρ × V² × S × Cd0。
  在马赫 3 时，气动加热使表面温度超过 300°C，边界层特性改变
- **诱导阻力**：导弹高 G 转弯时，因大攻角产生显著的诱导阻力
  （Cd_i ∝ Cl²），导致速度快速下降。一个 30G 转弯的导弹在
  1-2 秒内速度可衰减 10-20%
- **波阻**：超声速时弹头激波和弹翼激波产生波阻。
  波阻在 Mach 1.2 附近急剧上升，影响加速和巡航性能

当前模型中没有阻力意味着导弹进行高 G 转弯时不消耗动能——
这在物理上等价于导弹有无穷大的推力和零阻力。

---

## 四、导引头/锁定模型的缺陷

### 4.1 导引头传感器是完整的雷达/红外传感器副本

```cpp
// simulation_kernel_weapon_api.cpp:185-189
.set<Sensor>({sensor_max_range, sensor_fov_deg, sensor_scan_period, -1.0,
              sensor_detection_prob, 2.0, sensor_bearing_noise,
              sensor_range_noise, sensor_track_memory, 0.2,
              20.0, // doppler_notch_width (m/s)
              static_cast<int>(sensor_max_range > 8000.0 ?
                  SensorType::Radar : SensorType::Infrared)})
```

导弹导引头被建模为一个独立的 `Sensor` 组件，等同于机载雷达的副本。

真实导弹导引头的差异：

- **半主动雷达制导（SARH）**：导弹自身无雷达发射机，仅接收载机雷达
  照射目标的反射信号。导弹不能独立搜索/截获目标，完全依赖载机
  的 STT（单目标跟踪）照射直至命中。当前模型中的导弹有独立雷达
- **主动雷达制导（ARH，如 AIM-120）**：导弹在中制导段依赖载机数据链
  更新（而非自身雷达），仅在末端（距目标 15-20km）开启自身雷达进行
  末端主动制导。当前模型中的导弹从发射瞬间即独立探测
- **红外制导（IR，如 AIM-9）**：被动探测目标热辐射，无距离测量能力。
  不能直接获得目标距离和距离变化率——LOS 率必须从纯角度测量估计，
  这使被动红外导弹的 PN 制导精度低于主动雷达导弹。当前模型中
  红外导弹的 `ContactList` 仍然包含距离信息（来自上帝视角的
  传感器扫描）
- **导引头扫描模式**：真实红外导引头使用调制盘（reticle）或焦平面
  阵列（FPA），不进行类似雷达的"帧扫描"。当前模型统一使用
  0.05 秒扫描周期，对雷达偏快（机械扫描雷达通常 0.5-2 秒），
  对红外可能偏慢（FPA 的帧率可达 100Hz+）

### 4.2 锁定距离与导引头 FOV 未反映真实导引头约束

```cpp
double missile_seeker_fov = 180.0;
double missile_seeker_range = 30000.0;
```

- `seeker_fov_deg = 180` 意味着导弹可以锁定其**后方**的目标。
  真实导弹导引头的视场通常在 ±30° 到 ±60° 范围内（AIM-9X 使用 FPA
  的高离轴能力约为 ±90°）。180° 意味着导弹不需要指向目标即可
  锁定——这在物理上要求导引头安装在可以向后看的万向节上
- `seeker_lock_range = 30000m` 与 `sensor_max_range = 30000m` 相同。
  真实主动雷达导引头的锁定距离通常远小于最大探测距离，
  因为锁定需要更高的 SNR（跟踪模式）而非仅检测（搜索模式）

### 4.3 锁定条件中缺少发射前锁定（LOBL）要求

```cpp
// simulation_kernel_weapon_api.cpp:79-94
const ContactList* contacts = attacker.get<ContactList>();
bool has_track = false;
for (const auto& c : contacts->contacts) {
    if (c.target_id != target_id) continue;
    has_track = true; break;
}
```

发射条件仅要求载机的 `ContactList` 中存在目标，不考虑：

- **发射前锁定（LOBL，Lock-On Before Launch）**：大多数红外导弹
  要求导引头在发射前已获得目标锁定（听到"growl"音调）。
  载机传感器有目标接触 ≠ 导弹导引头可以独立锁定该目标
- **发射后锁定（LOAL，Lock-On After Launch）**：部分现代导弹
  （如 AIM-9X + JHMCS 高离轴发射）支持 LOAL，导弹先按预计
  拦截点发射，再在飞行中截获目标。这需要中制导/数据链引导
- **载机雷达照射模式**：半主动雷达导弹（如 AIM-7）需要载机
  处于 STT 模式（单目标跟踪）持续照射。TWS（边扫描边跟踪）模式下
  的航迹不能支持 SARH 发射

### 4.4 无目标识别/拒止能力

当前模型中的导引头无条件接受 `ContactList` 中符合 FOV 的信号。
真实导引头具有对抗措施拒止能力：

- **红外诱饵拒止（IRCCM）**：基于双色（dual-color）鉴别、
  运动学鉴别（诱饵快速减速 vs 载机维持速度）、
  上升时间鉴别（诱饵 0.1s 峰值 vs 载机持续辐射）
- **箔条拒止**：基于多普勒鉴别（箔条迅速减速到风速 vs 载机维持速度）、
  距离门拖引检测（RGPO 的典型特征是指数增长的虚假距离）
- **拖引干扰检测**：检测速度门拖引（VGPO）的典型模式
  （速度突变后匀速移动）

---

## 五、近炸引信与命中判定

### 5.1 引信逻辑无法分辨脱靶方向

```cpp
// damage_system.h:66-75
if (dist < m[i].proximity_last_dist_m - epsilon) {
    m[i].proximity_engaged = true;    // 仍在接近
    m[i].proximity_last_dist_m = dist;
    continue;
}
// 开始远离 → 触发引信
```

近炸引信的触发条件是"距离开始增大且最近距离 < fuse_distance"。
这只依赖标量距离，不区分"从目标上方经过""从目标下方经过"
还是"从目标前方经过"。

真实近炸引信（如激光近炸引信或无线电近炸引信）具有：

- **定向杀伤战斗部**：爆炸不是各向同性的球形，而是一个狭窄的
  破片锥（通常倾角 10-30° 指向前方）。引信需要判断目标的方向
  和相对速度来确定起爆时机和方向
- **距离变化率（range rate）触发**：激光引信通过测量目标的
  range rate 进一步优化起爆时刻，使破片锥与目标交会

### 5.2 命中概率模型的品质-规避耦合不合理

```cpp
// damage_system.h:83-92
double quality = std::clamp(1.0 - min_dist / fuse, 0.0, 1.0);
double evasion = std::clamp(std::abs(ac->turn_rate_cmd), 0.0, 1.0);
double base_hit = 0.35 + 0.65 * quality;
double hit_prob = std::clamp(base_hit * (1.0 - 0.3 * evasion), 0.05, 0.98);
```

- `evasion` 使用 `turn_rate_cmd`（归一化转弯率指令）作为规避指标。
  真实规避效果取决于目标机动产生的**脱靶量增加**，而非转弯指令
  的绝对值。一个目标做小幅高频转向（jinking）产生的脱靶量远大于
  大幅平滑转弯
- 规避效应和距离品质是**独立相乘的**，暗示规避和接近度两个
  因素独立作用——实际上它们是强相关的：目标在导弹接近末段
  做的大幅机动同时增加了最小距离并构成规避
- `hit_prob` 的 clamp 范围 [0.05, 0.98] 意味着即使最近距离为零
  （直接命中）也只有 98% 概率判定命中，而 fuse_distance 边缘的最近
  距离仍有最小 5% 的命中率。这一统计分布在真实弹药中并无物理解释

### 5.3 引信延迟和战斗部破片传播时间缺失

真实引信的触发-起爆-破片到达目标之间存在时间延迟链：

- 引信探测到目标 → 引信处理延迟（~1-5 μs 对激光，~50-200 μs 对无线电）
- 起爆信号 → 传爆药起爆 → 主装药爆轰（~10-50 μs）
- 破片加速到最大速度（~100-500 μs）
- 破片飞行到目标位置（~1-5 ms 取决于距离）

在此期间导弹以 ~1000 m/s 的速度飞行，相对位置可能偏移 1-5 米。
这意味着引信需"提前"起爆（lead triggering），基于目标相对运动
预测交会时机。当前模型在"距离开始增大"的同一帧触发——这是
零延迟简化，将导致系统性脱靶偏置。

---

## 六、毁伤效果模型

### 6.1 通用 HP 扣除与几何毁伤的双轨模型不一致

```cpp
// default_effects_model.cpp:118-133
hp->current_hp -= missile.damage;
// ...
if (hp->current_hp <= 0) {
    target_entity.destruct();
    // ...
}
// 然后继续执行几何命中盒判定...
```

HP 扣除在几何命中盒判定之前执行。如果 HP 扣除直接触发 `destruct`，
后续的几何命中盒逻辑完全被跳过。这意味着存在两条**不一致的毁伤
判定路径**：HP 归零 → 瞬间摧毁（忽略部件毁伤的中间状态），
以及命中盒判定 → 部件毁伤但实体可能存活。

真实情况是：不存在独立的"HP"概念——毁伤是物理相互作用的结果。
导弹战斗部产生的破片/爆炸/连续杆对目标结构造成局部损伤，
各子系统的功能丧失是这些局部损伤的累积后果，而非先验的
"HP 数值"。

### 6.2 部件毁伤是二值的"瞬间摧毁"

```cpp
// default_effects_model.cpp:157-159
sys_health->systems[system] -= 1.0; // Instant kill for now
if (sys_health->systems[system] < 0)
    sys_health->systems[system] = 0;
```

每个系统仅有 1.0 的"血量"，被命中盒覆盖后立即归零。
真实情况：

- **雷达毁伤**从天线损坏（增益损失 3-6dB）到接收机/处理机损坏
  （完全失效）是渐进的。一个破片命中天线阵面可能仅损坏部分
  T/R 模块（对有源相控阵，10-30% 模块损毁仍能降级工作）
- **发动机毁伤**从推力轻微下降到单发完全停车再到双发全停。
  发动机有冗余（F-16 为单发无冗余，F-15/F-22 有双发冗余），
  单发失效后飞机仍能维持飞行并可能返回基地
- **燃油系统毁伤**从缓慢渗漏（0.5-1 kg/s）到严重泄漏
  （5-10 kg/s）到油箱完全破裂。漏洞位置（自密封油箱 vs 外部油箱）
  决定泄漏速率和是否可隔离

### 6.3 世界坐标系→体轴系的旋转变换有注释提到的不确定性

```cpp
// default_effects_model.cpp:24-31
// Coordinate system is ENU. Heading 0=North (Y).
// This math can be tricky. For MVP reliability, let's treat Heading
// as rotation around Z. Pitch around X, Roll around Y?
// Actually, standard Euler inverse: R_total = R_z(heading) * R_x(pitch) * R_y(roll).
// Inverse is R_y(-r)*R_x(-p)*R_z(-h).
// But standard aerospace sequence is usually Yaw -> Pitch -> Roll.
// Let's implement a simplified 2D+Height transformation for stability first.
```

注释表明 `world_to_body` 函数经过了多次尝试和怀疑，当前实现为
忽略俯仰/滚转的 2D+高度近似。

```cpp
// default_effects_model.cpp:70
double local_z = dz; // Assuming flat pitch/roll for MVP interception
```

当目标处于任何非水平姿态（爬升/俯冲/滚转）时，命中盒坐标变换
将产生错误的结果——导弹可能被判定命中错误的部件或遗漏真实的
命中位置。

### 6.4 无战斗部类型区分

当前模型中 `missile.damage = 120.0` 是一个通用标量。真实空空导弹
使用多种战斗部类型：

- **连续杆战斗部**（如 AIM-9、AIM-120）：金属杆在爆炸后展开形成
  膨胀圆环，通过切割作用毁伤目标。有效毁伤半径取决于杆的展开
  直径和杆速度，通常在 5-15 米内有效
- **破片战斗部**（如 R-73、Python 系列）：预制破片（钨合金立方体/
  圆柱体）在高速下穿透目标结构。破片的空间分布（破片锥角度、
  密度、速度）决定毁伤概率
- **爆轰波效应**：近距离（<3 米）爆炸时，爆轰波的超压可致结构
  变形/蒙皮剥离，即使没有破片直接命中

当前模型使用统一的 `damage` 常数无法区分这些机理。

---

## 七、发射包线与发射条件

### 7.1 无发射包线（Launch Acceptability Region）判断

导弹发射的唯一条件是：

1. 弹药充足（`ammo->missiles_remaining > 0`）
2. 冷却完毕（`current_time - last_fire_time > cooldown_s`）
3. 目标在载机传感器接触列表中（`has_track == true`）

真实导弹发射需要满足**发射包线**（LAR，Launch Acceptability Region），
包括：

- **射程门限**：目标在导弹的最大动力射程（R_max）和最小射程
  （R_min，考虑引信安全和导引头截获时间）之内
- **离轴角门限**：目标的当前视线方向在导引头的最大离轴角内
  （对 LOBL 发射尤其关键）
- **目标角速度（LOS rate）门限**：过高的 LOS 率意味着导弹需要
  过大的初始转弯，可能导致能量过快耗尽或导引头在锁定前就丢失目标
- **高度差/指向差**：导弹爬升/俯冲消耗额外能量，大俯仰角发射
  包线显著缩小
- **载机速度/高度**：低空低速发射时导弹初始动压低、转弯能力弱，
  且发动机在稠密空气中的推力效率低于标称值
- **R_max 和 R_min 是动态的**——随发射高度、发射速度、目标高度、
  目标速度、相对方位角（迎头/尾追/侧向）显著变化。
  同一种导弹迎头发射的最大射程可达尾追发射的 2-4 倍

### 7.2 无快速射击/多目标发射限制

当前冷却时间（`cooldown_s`）是唯一的射击速率限制。真实火控系统还有：

- **雷达时间线约束**：SARH 导弹发射后载机雷达必须持续照射目标
  直至命中（对 AIM-7 为数十秒），期间不能切换目标或发射另一枚
  SARH 导弹。ARH 导弹在中制导段也需要载机数据链更新（每 1-2 秒），
  限制了同时引导的导弹数量
- **火控解算延迟**：从按下发射按钮到导弹物理离轨，存在火控计算机
  解算拦截方案→导弹导引头冷却/校准→武器释放的时间延迟
  （0.5-3 秒取决于系统）

---

## 八、导引头与载机/数据链的断连

### 8.1 导弹-载机之间无中制导数据链

```cpp
// default_guidance_model.cpp:64-68
const ContactList* contacts = missile_entity.get<ContactList>();
if (!contacts) return;
```

导弹完全依赖自身导引头的 `ContactList` 进行制导。真实中远程导弹
（如 AIM-120）的制导分为：

- **中制导段**（command-inertial）：载机通过数据链向导弹发送目标
  位置/速度更新。导弹依靠自身 IMU 进行惯性导航，辅以载机数据链
  提供的目标状态修正。更新频率 1-2 Hz（Link 16 带宽限制）
- **末端主动段**（terminal active）：距目标 15-20km，导弹的自身
  雷达锁定目标，切换为完全自主 PN 制导

当前模型等价于导弹从发射到命中全程自主制导——这等同于发射后
载机可立即脱离，与 SARH 和早期 ARH 的现实严重不符。

### 8.2 发射高度/速度对 Pk 的影响为零

真实导弹的单发杀伤概率（Pk）随发射条件显著变化：

- 同一种导弹在 40000 ft / Mach 1.2 发射的 Pk 可能是
  海平面 / Mach 0.6 发射的 2-3 倍（因更高的初始动能
  和更低的空气阻力）
- 迎头射击的 Pk 通常高于尾追射击（目标相对速度更高、
  末端脱靶量积累时间更短）

当前模型中的 Pk 仅由 `hit_prob`（最近距离 + 规避）决定，
完全不关心发射时的运动学条件。

---

## 九、当前不应采用的表述

1. 不应将当前制导系统称为"比例导航制导"——它是
   **LOS 率驱动的速度向量旋转**，无加速度指令、无自动驾驶仪、
   无弹体动力学。
2. 不应将当前导弹称为"空空导弹仿真"——它是
   **恒速运动学质点 + 点火即锁定 + 零阻力**，
   无助推/滑翔阶段、无质量消耗、无气动阻尼。
3. 不应将当前毁伤模型称为"战斗部毁伤仿真"——它是
   **通用 HP 扣除 + 二值部件开关**，
   无破片分布、无战斗部类型、无渐进毁伤。
4. 不应将当前导引头称为"主动/红外导引头仿真"——它是
   **载机传感器的副本组件**，不区分 ARH/SARH/IR 制导体制、
   无中制导数据链、无 LOBL/LOAL 状态。
5. 不应将当前发射逻辑称为"火控解算"——它是
   **冷却时间 + 弹药 + 接触存在**的三条件发射，
   无发射包线、无雷达时间线约束。

本结论冻结到下一次明确重开武器系统分析前为止。
