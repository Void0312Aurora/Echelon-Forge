# 域分离现状审计 — 2026-06-09

## 审计范围

全仓 C++ 源码中 Air / Naval / Ground 三域在 `components/`、`systems/`、`models/` 三层的分离程度。判断当前实现是否符合 `docs/standards/` 中定义的 `foundation → bridge → joint → services → air/naval/ground` 层级方针。

## 总体判断

**command 和 tasking 层已经证明按域拆分子目录是可行的，但 combat 和 physics 层明显落后。** 最严重的问题是 `damage.h` + `damage_system.h`（合计 2720 行）将 Air/Naval 两域的毁伤数据结构与 ECS 系统逻辑挤在同一文件中，且 Ground 域完全缺失。

---

## 1. 已分离良好的部分

| 层 | 路径 | 分离方式 |
|----|------|----------|
| components/command | `air/` `common/` `ground/` `naval/` | 按域拆子目录，含 README |
| components/tasking | `air/` `common/` `ground/` `naval/` | 按域拆子目录 |
| components/naval | `ship_platform.h` `submarine_platform.h` `embarked_air_ops.h` | 独立 naval 目录 |
| systems/naval | 5 个文件 + README | 独立 naval 系统目录 |
| models/air | `default_control_model.cpp` + README | 独立 air 模型目录 |

## 2. 域耦合热点

### 热点 1：`damage.h` + `damage_system.h` — 最大的三域混合体

**文件**：`src/components/combat/damage.h`（843 行） + `src/systems/combat/damage_system.h`（1877 行）

| 域 | 数据结构 | 占 damage.h 比例 | ECS 系统 | 占 damage_system.h 比例 |
|----|----------|------------------|----------|------------------------|
| **Air** | `AircraftDamageState`（31 字段）、`AircraftVulnerabilityProfile`、`AircraftDamageBaseline`、`AircraftVulnerabilityEvidenceRow` | ~60% | `AircraftDamageStateUpdate` → 约 150 行 | ~60% |
| **Naval** | `PlatformDamageState`（复用通用壳，含 `flooding_severity`、`ongoing_hull_breach`） | ~10% | `NavalDamageStateUpdate` → 35 行 | ~3% |
| **通用** | `SystemHealth`、`Hitbox`、`ComponentDamageState`、`PlatformLossState`、`DamageComponent` | ~30% | `ProximityFuze`、命中几何、坐标变换 | ~37% |
| **Ground** | **不存在** | 0% | **不存在** | 0% |

**核心问题**：

- `damage.h` 的 70% 代码是航空专用逻辑，但文件位于 `components/combat/` 通用路径下，伪装成跨域组件
- `PlatformDamageState` 仅 8 个字段，其中 `flooding_severity` 和 `ongoing_hull_breach` 是 naval-specific，却被硬编码进"通用"状态
- Naval 的 ECS 系统仅 35 行：只做 fire/flooding/breach 衰减，无隔舱进水图、损管队、水密完整性、弹药库殉爆
- Ground 域无任何毁伤数据结构或 ECS 系统

**详细对比**：

```
AircraftDamageState（31 字段）         PlatformDamageState（8 字段）
─────────────────────────────         ─────────────────────────
structural_integrity                  mission_capability        ← 通用
flight_control_integrity              mobility_capability       ← 通用
hydraulic_integrity                   sensor_capability         ← 通用
hydraulic_pressure_availability       survivability_margin      ← 通用
roll_control_integrity                flooding_severity         ← naval-only!
pitch_control_integrity               fire_severity             ← 通用
yaw_control_integrity                 ongoing_hull_breach       ← naval-only!
control_asymmetry                     loss_state                ← 通用
propulsion_integrity
fuel_system_integrity                 缺失的 Naval 概念：
avionics_integrity                    ─────────────
crew_effectiveness                    隔舱进水图 (compartment flood graph)
pilot_effectiveness                   损管队 (damage control party)
mission_crew_effectiveness            水密完整性 (watertight integrity)
command_navigation_integrity          弹药库殉爆风险 (magazine explosion)
fire_severity                         轴系/舵机损伤 (shaft/rudder damage)
fuel_leak_severity
fuel_imbalance_severity               缺失的 Ground 概念：
flammable_fluid_exposure              ──────────────
ignition_source_severity              装甲穿透 (armor penetration)
fire_suppression_integrity            履带/轮式机动杀 (mobility kill)
smoke_heat_exposure                   武器站失效 (weapon station disablement)
engine_fire_zone_severity             乘员伤亡 (crew casualty)
wing_fire_zone_severity               弹药诱爆 (ammunition cook-off)
fuselage_fire_zone_severity
mission_fire_zone_severity
structural_overstress
flutter_exposure
forced_landing_required
flight_control_kill
propulsion_kill
crew_kill
```

### 热点 2：`weapon.h` — Air + Naval 类型混合

**文件**：`src/components/combat/weapon.h`

```
├── WarheadProfile           ← 通用（但 air-shaped）
├── FuzeProfile              ← 通用（但 air-shaped）
├── Missile                  ← air-to-air 导弹
├── Ammo                     ← 通用
├── WeaponCooldown           ← 通用
├── PilotWeaponReleaseState  ← air-only
├── Munition                 ← 通用
├── NavalWeaponType          ← naval-only（混入通用文件）
├── NavalWeaponMountDefinition ← naval-only（混入通用文件）
├── NavalWeaponSystem        ← naval-only（混入通用文件）
└── (GroundWeapon: 零)
```

### 热点 3：`logistics_system.h` — Air + Naval ECS 系统混合

**文件**：`src/systems/systems/logistics_system.h`

单个文件注册了 5 个 ECS 系统，横跨空中加油和海上补给：

| ECS 系统 | 域 | 说明 |
|----------|----|------|
| `FuelConsumption` | Air | 燃油消耗 |
| `LogisticsAction` | 通用 | 后勤动作分发 |
| `MassUpdate` | 通用 | 质量更新 |
| `NavalUnderwayResupply` | **Naval** | 海上航行补给（混入通用文件） |
| `ResupplyLogic` | 通用 | 补给逻辑（含 Naval-specific 阶段机） |

### 热点 4：`default_sensor_model.cpp` — 通用传感器嵌入了 Ship-specific 代码

**文件**：`src/models/systems/default_sensor_model.cpp`

```
#include "components/naval/ship_platform.h"   ← 通用 sensor model 直接依赖 naval 组件

// 雷达海杂波计算（硬编码在通用传感器中）
state.sea_state = std::max(0.0, ship->sea_state);
state.wave_heading_deg = ship->wave_heading_deg;

// 目标类型判断（domain check in generic code）
const bool target_is_ship = target_key && target_key->type == UnitType::Ship;
if (!target_is_ship) { ... }  // ship 特殊处理
```

### 热点 5：`default_effects_model.cpp` — detail 文件全为 Air 服务

**文件**：`src/models/weapons/default_effects_model.cpp`（213 行） + `detail/`（10 个 `.inc` 文件，约 22 万行）

```
detail/
├── default_effects_air_platform_resolution_detail.inc  ← air only
├── default_effects_component_damage_detail.inc          ← 调用 AircraftDamageState
├── default_effects_warhead_detail.inc                   ← air-shaped
├── default_effects_legacy_detail.inc                    ← 遗留 HP 扣减
├── default_effects_geometry_detail.inc                  ← 通用（但 air-shaped）
├── default_effects_spatial_projection_detail.inc        ← 通用
├── default_effects_state_detail.inc                     ← 通用
├── default_effects_result_detail.inc                    ← 通用
├── default_effects_direct_hit_detail.inc                ← 通用
├── default_effects_system_effect_detail.inc             ← 通用
│
└── (naval/ground detail: 零文件)
```

主 `.cpp` 中 `is_structured_damage_air_target()` 判定后分叉——但唯一的分叉路径是 air vs legacy（旧 HP 扣减）。没有 naval/ground damage resolution path。

### 热点 6：Air-only physics systems 误放在通用 `systems/physics/` 下

| 文件 | 实际域 | 证据 |
|------|--------|------|
| `aerodynamics_system.h` | Air-only | 直接读取 `AircraftDamageState`（structural/flight_control/hydraulic/roll/pitch/yaw…） |
| `control_system.h` | Air-only | FlightControl、FBW 保护逻辑 |
| `propulsion_system.h` | Air-only | `AircraftDamageState::propulsion_integrity` 驱动推力降级 |
| `aero_state_system.h` | Air-only | 气动状态计算 |
| `flight_dynamics_tuning.h` | Air-only | `AeroTuning` 结构体（CL/CD/CM 曲线） |

这些文件与 `systems/naval/ship_motion_system.h` 处于同一抽象层级，但没有 `systems/air/` 目录来承载它们。

---

## 3. 域分离全景对比

```
                        components/          systems/            models/
                        ───────────          ────────            ───────
command/tasking         ✅ air/common/       N/A                 N/A
                           naval/ground

Air     专用             ❌ 无 air/ 目录      ❌ 无 air/ 目录      ✅ air/
        实际位置         combat/damage.h      physics/aerodynamics  default_control
                        combat/weapon.h       physics/control      但 effects 散落
                                              physics/propulsion
                                              combat/damage_system

Naval   专用             ✅ naval/            ✅ naval/            ❌ 无 naval/
        实际位置         combat/damage.h      combat/damage_system  effects 共用
                        combat/weapon.h       systems/logistics    sensor 嵌入

Ground  专用             ❌ 无 ground/ 组件   ❌ 无 ground/ 系统   ❌ 无 ground/ 模型
        实际位置         (完全缺失)           (完全缺失)           (完全缺失)
```

---

## 4. 解耦设计建议

### 目标结构

```
src/
├── components/
│   ├── combat/
│   │   ├── damage.h              ← 保留：PlatformDamageState, SystemHealth, Hitbox,
│   │   │                            ComponentDamageState, PlatformLossState（真正通用）
│   │   ├── health.h              ← 保留（已是通用）
│   │   ├── scoring.h             ← 保留（已是通用）
│   │   ├── weapon.h              ← 保留：FuzeProfile, WarheadProfile, Missile（通用武器）
│   │   ├── air/
│   │   │   ├── damage_air.h      ← 迁出：AircraftDamageState, AircraftVulnerabilityProfile,
│   │   │   │                        AircraftDamageBaseline, 所有 is_air_* 函数
│   │   │   └── weapon_air.h      ← 迁出：PilotWeaponReleaseState
│   │   ├── naval/
│   │   │   ├── damage_naval.h    ← 新建：NavalDamageState
│   │   │   └── weapon_naval.h    ← 迁出：NavalWeaponType, NavalWeaponMountDefinition,
│   │   │                            NavalWeaponSystem
│   │   └── ground/
│   │       ├── damage_ground.h   ← 新建：GroundDamageState
│   │       └── weapon_ground.h   ← 新建
│   └── physics/
│       ├── dynamics.h, forces.h, action.h, performance.h  ← 保留（通用）
│       └── air/
│           └── flight_dynamics_tuning.h  ← 迁出：AeroTuning（air-only）
│
├── systems/
│   ├── combat/
│   │   ├── damage_system.h       ← 保留：通用逻辑（引信判定、命中几何、坐标变换）
│   │   ├── damage_system_air.h   ← 迁出：AircraftDamageStateUpdate（~150 行）
│   │   ├── damage_system_naval.h ← 迁出：NavalDamageStateUpdate（~35 行，后续扩展）
│   │   ├── damage_system_ground.h← 新建：GroundDamageStateUpdate
│   │   ├── guidance_system.h     ← 保留（已是通用）
│   │   └── pilot_weapon_release_system.h ← 保留
│   ├── air/                      ← 新建目录
│   │   ├── aerodynamics_system.h ← 迁入
│   │   ├── control_system.h      ← 迁入
│   │   ├── propulsion_system.h   ← 迁入
│   │   └── aero_state_system.h   ← 迁入
│   ├── naval/                    ← 已存在，补齐 README
│   ├── ground/                   ← 新建目录
│   │   └── ground_contact_system.h ← 迁入（GroundState 专属）
│   └── systems/
│       ├── sensor_system.h       ← 保留但需移除 ShipPlatform 直接依赖
│       └── logistics_system.h    ← 拆分：NavalUnderwayResupply → systems/naval/
│
├── models/
│   ├── air/                      ← 已存在
│   ├── naval/                    ← 新建
│   ├── ground/                   ← 新建
│   ├── weapons/
│   │   ├── default_effects_model.cpp  ← 保留：仅做域路由
│   │   └── detail/
│   │       ├── *_air_*.inc       ← 保留
│   │       ├── *_naval_*.inc     ← 新建
│   │       └── *_ground_*.inc    ← 新建
│   └── systems/
│       └── default_sensor_model.cpp ← 需重构：移除 ShipPlatform 直接依赖
```

### 迁移优先级

| 优先级 | 变更 | 理由 |
|--------|------|------|
| **P0** | 拆分 `damage.h` → `damage_air.h` + 通用 `damage.h` | 843 行最大单体混合，Air 占 60% |
| **P0** | 拆分 `damage_system.h` → `damage_system_air.h` + `damage_system_naval.h` | 1877 行最大系统混合 |
| **P1** | 创建 `systems/air/`，迁入 aerodynamics/control/propulsion/aero_state | 4 个 air-only 系统伪装成通用 physics |
| **P1** | 拆分 `weapon.h` → `weapon_naval.h`（迁出 naval 类型） | Air/Naval 类型混合 |
| **P1** | 创建 `components/combat/ground/` + `systems/ground/` | 当前完全缺失 |
| **P2** | `logistics_system.h` 拆分 NavalUnderwayResupply → `systems/naval/` | 局部混合 |
| **P2** | `default_sensor_model.cpp` 移除 ShipPlatform 直接依赖 | 通用 sensor 不应知道 ShipPlatform |
| **P2** | 创建 `models/naval/` + `models/ground/`，补齐 detail 文件 | 补齐模型层目录 |

---

## 5. 关于 Naval 作为示范域

当前 command/tasking 层已经证明 `air/common/naval/ground` 子目录拆分是可行的。Naval 域在 systems 层拥有最完整的结构分离（5 个独立系统文件 + README），唯一缺失的是 models 层和 combat 层。补齐 Naval 三层结构后，它可以作为"域完整分离"的参考模板，指导后续 Air 和 Ground 的重构。

具体建议：将 Naval 从 70% 完整提升到 100% 完整（创建 `models/naval/`、`components/combat/naval/`），然后将它的文件清单和 README 模式文档化为域分离的示范模板。

---

*审计基于 2026-06-09 工作树。所有文件引用和行数可复现。*
