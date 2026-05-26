# A2 高真实度空战毁伤模型任务簇 - 2026-05-26

状态：`A2-D0` 已开启；`2026-05-26` Phase 0 预检已完成主要证据审计，但 `PN miss-distance baseline` 仍阻塞行为代码。

## 决策

本任务簇采用 forward 评估中的严格立场：

1. 空战毁伤模型是高真实度仿真路径，不是 RL reward 快捷路径；
2. `Health.current_hp` 不再被规划为带结构化毁伤飞机的 kill authority；
3. Phase 1 前必须先完成 Phase 0 审计，否则 HP bypass 反转、飞机 hitbox 接入和 deterministic fuze 都不能开工；
4. `ForcedLanding` 不能通过重排现有 `PlatformLossState` 数值实现。若需要，优先 append-only 或 aircraft overlay state；
5. deterministic fuze 必须等待 PN miss-distance baseline matrix。

## 任务流

| 流 | 状态 | 目标 | 写入面 | 非目标 | 验证 | 退出条件 |
|----|------|------|--------|--------|------|----------|
| `A2-D0 文档与边界冻结` | accepted | 建立子项目，冻结高真实度毁伤原则和 Phase 0 gate。 | `docs/task/air_combat/a2_high_fidelity_damage_model/**`、air_combat 索引 | 行为代码 | 文档 diff、索引可达 | 子项目能作为后续实现入口 |
| `A2-P0.1 PlatformLossState 审计` | closed_for_design | 查明枚举值、raw int 比较、Python 暴露和序列化风险。 | 文档、必要时只读脚本 | 改枚举 | grep + 测试引用清单 | 得出 append-only/overlay 决策 |
| `A2-P0.2 health observer 审计` | closed_with_guard | 盘点 `health > 0`、`get_unit_health`、`is_unit_active` 的语义依赖。 | 文档、只读 probe | 改 reward/termination | 调用点表 | 明确 HP 派生读数迁移影响 |
| `A2-P0.3 ShipPlatform filter 审计` | closed_for_design | 判定 damage update 是新建 aircraft 系统还是泛化现有 naval 系统。 | 文档、只读 grep | 移除 filter | consumer matrix | 不破坏 ship-only 系统 |
| `A2-P0.4 Aircraft content inventory` | evidence_closed/content_gap_open | 列出飞机类型与 hitbox 缺口，选择 authored/generator 策略。 | 文档、数据库清单 | 批量填内容 | aircraft inventory | 每类飞机有明确 hitbox 路径 |
| `A2-P0.5 Score write-point 审计` | closed_with_decoupling_required | 找出 effects model 中 reward/score 写点，设计事件消费层迁移。 | 文档、必要时测试计划 | 立即重构 score | write-point list | physical effects 不再被 reward 语义污染 |
| `A2-P0.6 PN miss-distance baseline` | blocked | 构造 head-on / tail-chase / beam / high-off-boresight miss-distance 基线。 | benchmark/test docs，可能新增 probe | deterministic fuze | 可重复基线输出 | 决定 Phase 4 是否可启动 |
| `A2-P1 Aircraft structured damage` | held | 反转 HP-first bypass，并让飞机走结构化毁伤路径。 | effects model、spawn path、aircraft JSON、tests | deterministic fuze、warhead profile 全量实现 | focused combat tests | structured target 不被 HP-first bypass kill |
| `A2-P2 Aircraft subsystem effects` | held | 飞机推进/飞控/结构/燃油/传感器/航电/飞行员级联效果。 | damage systems、flight/sensor consumers | Pk 曲线 | hitbox-specific tests | 不同 hitbox 后果可区分 |
| `A2-P3 Warhead profile` | held | 引入 blast/frag/rod/HTK profile，旧 JSON synthetic 兼容。 | weapon definitions、loader、effects model | external Pk 数据 | warhead unit tests | scalar damage 不再是高真实度权威 |
| `A2-P4 Deterministic fuze` | deferred | 几何优先引信/杀伤替代 RNG hit roll。 | fuze/damage system | 未验证 PN 前移除 RNG | miss-distance matrix + controlled fuze tests | evasion 通过 miss distance 生效 |
| `A2-P5 Vulnerability evidence` | future | 引入 weapon/target/aspect/closure 脆弱性或 Pk 校准数据。 | content/data/contracts | 黑箱替代物理模型 | provenance tests | 数据来源可审计 |

## Phase 0 证据表模板

每个 Phase 0 gate 关闭时，必须记录：

- grep / probe 命令；
- 发现的关键调用点；
- 风险等级；
- 是否允许进入下一阶段；
- 若允许，采用的迁移策略；
- 若不允许，阻塞原因和最小解除条件。

建议输出位置：

- `docs/task/air_combat/a2_high_fidelity_damage_model/phase0_preflight_YYYYMMDD.zh.md`

当前审计输出：

- [Phase 0 预检审计 - 2026-05-26](phase0_preflight_20260526.zh.md)

## Phase 1 最小补丁边界

Phase 1 的第一批代码变更应该足够小：

- 只针对带结构化 damage state 的 aircraft 禁用 HP-first bypass；
- 不改变 legacy 无 hitbox 目标的兼容行为；
- aircraft hitbox 可以先用明确标注的 generated whole-aircraft fallback，但必须仍走 structured damage path；
- `Score` 写入迁移可以先通过事件消费层最小实现，不把奖励逻辑留在 effects model；
- 新测试必须能证明 HP bypass 不再提前 `return`。

## 风险与保护

- **行为突变风险**：已有 air combat tests 可能默认一次导弹命中直接击杀。Phase 1 必须保留 legacy fixture 或更新断言，使测试描述真实语义；
- **训练信号风险**：RL 可能失去连续 HP reward。应从 `DamageReport` 和 kill state 构造训练读数；
- **舰船回归风险**：泛化 `NavalDamageStateUpdate` 容易伤及 ship-only 系统。若证据不足，优先新建 aircraft damage update；
- **数据缺口风险**：没有 aircraft hitbox 内容时，不允许声称真实度提升，只能称 generated fallback；
- **引信过确定风险**：没有 PN miss-distance 基线时，deterministic fuze 可能让 evasion 在 damage 上失效。

## 当前推荐下一步

继续 Phase 0，不写行为代码：

1. `A2-P0.6`：补 PN miss-distance benchmark/probe；
2. 只读暴露 `proximity_min_dist_m`、`proximity_last_dist_m`、`proximity_engaged` 或等价 benchmark 输出；
3. 形成 head-on / tail-chase / beam / high-off-boresight 基线；
4. 基线闭合后再评审是否允许 Phase 1 最小行为 patch。

## 建议命令

边界 smoke：

```bash
bash -lc 'source tools/maintenance/cmo_env.sh && cmo_python tools/runners/run_pytest_suite.py --suite tests/smoke/ci_smoke_suite.json'
```

当前空战固定链路：

```bash
bash tools/maintenance/cmo_env.sh python -m pytest -q \
  tests/runtime/air_combat/test_air_combat_1v1_fixture.py \
  tests/runtime/air_combat/test_air_combat_1v1_fire_missile.py \
  tests/runtime/engagement
```

world-batch 契约：

```bash
bash tools/maintenance/cmo_env.sh python -m pytest -q \
  tests/world_batch/test_world_batch_runtime.py \
  tests/runtime/facade/test_runtime_facade.py
```

## 退出状态

本任务簇只能以以下状态推进或关闭：

- `phase0 accepted`：六个预检门均有证据，允许设计 Phase 1 patch；
- `phase0 blocked`：任一预检门发现未处理的跨层风险，禁止行为代码；
- `phase1 accepted`：structured aircraft target 已能通过非 HP-first 权威路径产生 kill state；
- `deferred`：损伤模型被明确排在训练或可视化任务之后；
- `rejected`：仅当项目决定不追求高真实度毁伤模型时使用。
