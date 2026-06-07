# A8 损伤效果链任务簇

状态：`2026-06-07`，
[README.zh.md](README.zh.md) 的有限任务簇计划。

## 边界决定

A8 可以标准化并实现起爆后的损伤效果路径：起爆记录、战斗部作用、受影响飞机部位、
部位损伤类型、功能变化，以及随后通过已有动力、燃油、传感器、火灾和飞行消费方表现出的
飞机响应。A8 不得增加直接坠毁规则、独立“还能不能飞”判决、MQ-9 特例击杀规则、
真实世界击杀概率、确定性引信真值或 AIM-120C 权威杀伤声明。

选定路径是：

```text
引信/起爆
-> 战斗部作用
-> 受影响部位
-> 具体部位损伤
-> 功能变化
-> 已有飞机仿真响应
-> 观察到的结果
```

## 有限任务簇列表

| Cluster | Owner | Model / reasoning | Goal | Write set | Non-goals | Validation | Closure gate | Dependency / parallel | Round cap | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `A8-DEC-A Boundary` | main thread | n/a | 创建 A8 文档、父级链接、当前状态、任务簇和 archive 边界。 | `docs/task/air_combat/a8_damage_effect_chain/**`, `docs/task/air_combat/README.md`, `docs/task/air_combat/README.zh.md` | 运行时实现、新物理声明 | `git diff --check -- docs/task/air_combat` | 标准文件存在，父级 README 链接 A8。 | first, serial | 1 | pass |
| `A8-DEC-B Structure Evidence` | current-session explorers, main-thread integration | inherited model / read-only | 确认当前引信/效果、部件状态、飞行/动力、MQ-9/AIM-120C 测试结构。 | 只更新 A8 current status | 结构未确认前改代码 | 只读扫描和本地链接检查 | 发现明确入口、缺口和安全写入范围。 | after A; 按代码区域并行 | 1 + 1 repair | pass |
| `A8-DEC-C Shot Effect Record` | current-session worker | high reasoning | 定义每次射击记录，暴露引信、起爆、战斗部作用、受影响部位、损伤类型和后续后果。 | `src/core/interfaces/**`, `src/core/engine/*damage*`, `src/models/weapons/detail/default_effects_result_detail.inc`, `tests/runtime/air_combat/weapon_guidance_realism/**` | 改飞机物理或宣称真实杀伤 | contract tests 和 runtime guidance guards | 测试能解释为什么损伤、未损伤或未起爆。 | after B; 与 D/E public fields 串行 | 2 | pass：已有记录链合格 |
| `A8-DEC-D Part Effect Vocabulary` | current-session worker | high reasoning | 增加具体损伤模式，并把战斗部作用映射到结构化飞机部件。 | `src/components/combat/damage.h`, `src/content/unit_definition_loader.cpp`, `src/models/weapons/detail/default_effects_*`, 必要的 MQ-9/F-16 damage JSON，聚焦测试 | 校准脆弱性、大范围数据重写 | component-damage tests 和 loader tests | 部件损伤记录能命名物理或功能损伤，而不是只有完整度数字。 | after C record shape; 与 F 只通过不重叠测试并行 | 2 | partial：目前只有内部故障类型 |
| `A8-DEC-E Consumer Integration` | future worker | high reasoning | 将具体损伤传给动力、燃油/质量、传感器、火灾和飞行/气动行为。 | `src/systems/combat/damage_system.h`, `src/systems/physics/aerodynamics_system.h`, `src/systems/physics/propulsion_system.h`, 相关物理测试 | 直接坠毁规则、独立飞行判决 | 聚焦 runtime tests 和 flight-dynamics guards | 发动机、燃油、传感器、翼面/操纵和结构损伤被维护中的系统消费。 | after D; 物理写入范围串行 | 2 | planned |
| `A8-DEC-F MQ-9 / AIM-120C Validation` | current-session worker | medium/high reasoning | 构建固定样例，证明尾部发动机、翼面/操纵、燃油/火灾、传感器/数据链结果。 | `tests/runtime/air_combat/**`, 可选 test-only fixtures | 把一次 smoke 当真实概率 | `python -m pytest -q tests/runtime/air_combat/test_weapon_guidance_realism_guards.py tests/runtime/air_combat/test_air_combat_1v1_fire_missile.py` 加新聚焦测试 | 测试同时检查即时记录和后续飞机响应。 | after C/D/E; B 后可先准备 fixture 计划 | 2 | partial pass：固定样例和非权威保护 |
| `A8-DEC-G Acceptance And Index Sync` | main thread | n/a | 决定 accepted 或 held，同步父级 README/status，并记录残余。 | A8 README/status/acceptance、父级 air-combat README、必要 archive index | 把 docs-only 工作标成 runtime pass | docs link check 和 accepted validation commands | 能力声明有证据，过度声明继续被拒绝。 | last, serial | 1 | partial pass：仅第一轮 |

## 派发规则

- 第一轮实现派发队列：
  [a8_damage_effect_chain_dispatch_queue_20260607.md](a8_damage_effect_chain_dispatch_queue_20260607.md)
- 每个 worker packet 必须对应上表中且仅一个 cluster。
- 不允许两个 worker 同时编辑同一 public record 字段、部件 schema、飞机配置段、物理消费方或状态行。
- 严禁创建新会话线程。当前会话 subagent 只可作为上述 cluster 写入范围内的有边界 worker。
- boundary、acceptance 和父级索引同步必须串行。
- 如果一个 cluster 超过 round cap，先停下重新收缩范围，而不是继续追加 follow-up。
- 遵循 [Subagent 使用规范](../../../standards/governance/subagent_usage_policy.zh.md)。

## Worker Packet 要求

```md
status: pass | partial | blocked | failed
touched files:
commands/outcomes:
remaining paths:
behavior risks:
integration notes:
```

## 验证计划

初始 docs-only 验证：

```bash
git diff --check -- docs/task/air_combat
```

`A8-DEC-B/C` 后细化的实现验证预计为：

```bash
cmake --build build-workshop -j 8
python -m pytest -q tests/runtime/air_combat/test_weapon_guidance_realism_guards.py
python -m pytest -q tests/runtime/air_combat/test_air_combat_1v1_fire_missile.py
python -m pytest -q tests/runtime/air_combat/test_flight_dynamics_realism_guards.py
```

新测试必须检查过程记录和后续飞机响应，不能只看最后血量或生死状态。

## 验收标准

- 射击记录能解释引信结果、起爆几何、战斗部作用、受影响部位、具体损伤模式和后续飞机响应。
- 结构化飞机保留血量作为兼容输出，而不是主要损伤解释。
- 发动机或螺旋桨损伤能进入动力推力。
- 翼面/操纵损伤能通过维护中的飞行系统影响滚转、俯仰、偏航、不对称或气动行为。
- 燃油损伤能进入漏油、质量、供油、火灾风险或火灾传播行为。
- 传感器/数据链损伤可以造成任务或感知后果，但不假装飞机一定坠毁。
- MQ-9 / AIM-120C 样例包含尾部、翼面/操纵、燃油/火灾、传感器/数据链，并有固定检查。
- 文档继续拒绝真实世界击杀概率、确定性引信真值和 AIM-120C/MQ-9 权威杀伤声明。

## 残余图

立即：

- 使用已整合的只读发现冻结射击效果记录形状，再改部件或物理消费方。
- 第一轮运行时切入点保持在“机制载荷到具体部件故障记录”层，再扩大到气动或控制模型。

后续：

- 校准脆弱性或战斗部证据只能通过独立数据准入包加入。
- 固定翼 MQ-9/F-16 样例稳定后，再增加不同平台族的消费方。

延后：

- 真实世界击杀概率。
- 确定性引信真值。
- 机密或 stock 武器数据。
- 大范围多机型脆弱性校准。
