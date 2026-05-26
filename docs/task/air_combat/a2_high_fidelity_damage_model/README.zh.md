# A2 高真实度空战毁伤模型

状态：`2026-05-26` 已开子项目；Phase 0 已完成主要证据审计，但 `PN miss-distance baseline` 尚未闭合，行为代码仍 held。

本子项目承接两份 forward 评估：

- [空战毁伤模型评估](../../../forward/air_combat_damage_model_evaluation_20260522.md)
- [代码现实交叉评估](../../../forward/air_combat_damage_model_cross_eval_20260522.md)

它服务于 `1v1` 真实度梯度课程，但不是 RL 便利性任务。高真实度毁伤模型的目标是让武器事件先产生物理可解释的局部结构/子系统毁伤，再从平台状态推导 mission kill、sensor kill、mobility kill、forced landing 或 lost。训练 reward、课程捷径和 legacy `health` 读数只能消费这些结果，不能反向定义物理毁伤权威。

## 设计立场

不可妥协原则：

- `Health.current_hp` 可以保留为兼容读数，但不能作为空战毁伤和击杀权威；
- 权威输入来自 weapon event：近炸/撞击、引信状态、miss distance、相对几何、战斗部类型、目标脆弱性；
- 毁伤首先作用到局部结构、飞控、推进、燃油、传感器、座舱/飞行员等子系统；
- 平台 kill state 必须从子系统和结构状态推导，而不是由单一 `damage` 标量直接扣血得到；
- 随机性只能表示显式建模的不确定性或物理采样，不能掩盖缺失几何、缺失脆弱性或缺失引信模型；
- RL reward 和课程 shaping 属于消费层，不属于 physical effects authority。

## 当前问题

当前代码存在两个并行毁伤路径：

- legacy air path：`Health` 存在且没有结构化 hitbox 时，直接 `hp -= missile.damage`，`hp <= 0` 即摧毁；
- naval subsystem path：`HitboxConfig + SystemHealth + PlatformDamageState` 通过局部 hitbox 和子系统状态推导能力损失。

Phase 0 审计修正了一点：多数带 `airframe.length_m` 的飞机在 spawn 时已经会生成 procedural hitbox，并挂载 `SystemHealth` 与 `PlatformDamageState`。但是交叉评估中的核心问题仍成立：legacy HP 分支在 `default_effects_model.cpp` 中先执行，并且可以在几何/子系统毁伤前提前 `return`。这意味着任何“飞机子系统毁伤”实现，如果不先处理 HP-first bypass，就可能永远不会成为权威路径。

## Phase 0 预检门

Phase 1 行为代码不得开始，除非下列门全部关闭并记录：

- `PlatformLossState` 枚举审计：确认没有 raw integer 比较依赖 `Lost = 4`；如果需要 `ForcedLanding`，只能 append-only 或采用 aircraft overlay state；
- Python health observer 审计：盘点 `health > 0`、`get_unit_health`、`is_unit_active` 等调用，准备 HP 从权威杀伤变为派生读数后的语义迁移；
- `ShipPlatform` filter 审计：确认 `NavalDamageStateUpdate` 与其他 ship-only 系统边界，决定新增 aircraft damage update 还是泛化 damage update；
- aircraft JSON inventory：列出所有飞机类型，决定 per-aircraft authored hitboxes 还是 generated whole-aircraft fallback；
- `Score` write-point 审计：把 effects model 内的 kill reward / kills_confirmed 写点迁移计划记录清楚；
- PN miss-distance benchmark：在 head-on、tail-chase、beam、high-off-boresight 等几何上测量当前制导 miss distance 分布，再决定是否移除 RNG fuze。

当前 Phase 0 证据：

- [Phase 0 预检审计 - 2026-05-26](phase0_preflight_20260526.zh.md)

## 实施阶段

### Phase 1：飞机结构化 hitbox 与 HP bypass 反转

目标：

- 让带结构化毁伤状态的飞机不再通过 HP-first branch 直接击杀；
- 飞机 spawn path 能挂载 `HitboxConfig`、`SystemHealth`、`PlatformDamageState` 或等价 aircraft damage state；
- kill state 从平台毁伤状态推导；
- reward/score 写入从 physical effects path 解耦。

风险：中高。它会改变导弹命中飞机后的主行为路径。

### Phase 2：飞机子系统级联效果

目标：

- 推进：推力衰减、单发/双发差异、火焰熄灭；
- 飞控/液压：操纵面效率、速率限制、控制延迟；
- 结构：g-limit、flutter boundary、翼梁/蒙皮损伤；
- 燃油：泄漏、起火、续航/返场约束；
- 传感器/航电：雷达、RWR、数据链、导航能力下降；
- 座舱/飞行员：任务能力和控制能力下降。

风险：中。需要触及飞行动力学和传感器行为消费层。

### Phase 3：战斗部 profile

目标：

- 从单一 `damage` 标量转到 `WarheadProfile`；
- 支持 blast、fragmentation、continuous rod、hit-to-kill 等族；
- 旧 weapon JSON 可通过 synthetic profile 兼容加载，但必须在诊断中标记为 synthetic。

### Phase 4：确定性引信，暂缓

目标是把当前 RNG hit probability 替换为 geometry-first fuze/effects 模型。但它必须等待 PN miss-distance benchmark。否则可能把当前唯一的 evasion 影响点移除，导致高机动目标和低机动目标在杀伤结果上过于确定。

### Phase 5：脆弱性 / Pk 证据集成

目标是引入 weapon/target/aspect/closure/miss-distance 相关的证据表或函数。Pk 曲线只能校准物理模型，不能替代 `EffectsEvent`、`DamageReport` 和平台状态。

## 非目标

- 不为了短训练 reward 简化物理杀伤；
- 不用单一 `damage` scalar 冒充高真实度战斗部；
- 不把 `health <= 0` 继续作为带结构化毁伤状态飞机的权威 kill 判据；
- 不在缺少 PN miss-distance 证据前移除 RNG fuze；
- 不在 Phase 0 前改动 `PlatformLossState` 枚举值。

## 主要写入面

- `src/models/weapons/default_effects_model.cpp`
- `src/systems/combat/damage_system.h`
- `src/components/combat/damage.h`
- `src/content/unit_definition.h`
- `src/content/unit_definition_loader.cpp`
- `examples/config/database/aircraft/**/*.json`
- `examples/config/database/weapons/air_to_air/**/*.json`
- `src/runtime/contracts/engagement_contracts.h`
- RL / runtime consumers that currently read `health` or direct score writes

## 验收信号

最低验收不以“训练更容易”为标准，而以物理语义为标准：

- structured aircraft target 不能被 HP-first bypass 击杀；
- missile event 至少产生可检查的 `EffectsEvent` / `DamageReport` / subsystem mutation；
- 不同 hitbox 命中能产生不同能力后果；
- HP 只作为派生兼容读数存在；
- reward/score 消费毁伤报告和 kill state，不写回 physical effects authority；
- legacy smoke 可以通过兼容读数继续运行，但测试明确区分 legacy HP path 与 structured damage path。

## 推荐验证

Phase 0：

```bash
bash tools/maintenance/cmo_env.sh python -m pytest -q \
  tests/runtime/air_combat/test_air_combat_1v1_fixture.py \
  tests/runtime/engagement \
  tests/world_batch/test_world_batch_runtime.py
```

架构边界：

```bash
bash -lc 'source tools/maintenance/cmo_env.sh && cmo_python tools/runners/run_pytest_suite.py --suite tests/smoke/ci_smoke_suite.json'
```

Phase 1 后必须新增专用测试，至少覆盖：

- structured aircraft hitbox 命中；
- HP-first bypass 被禁止；
- aircraft damage update 不依赖 `ShipPlatform`；
- `DamageReport` loss state 和派生 `Health` 一致。

## 后续入口

- [任务簇](high_fidelity_damage_model_cluster_20260526.zh.md)
