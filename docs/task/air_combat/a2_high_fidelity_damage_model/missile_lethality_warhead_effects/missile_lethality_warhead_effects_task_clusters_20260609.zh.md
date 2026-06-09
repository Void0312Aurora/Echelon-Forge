# A2 MLF-3 战斗部作用任务簇

状态：`2026-06-09` MLF-3B/3E focused pass for [README.zh.md](README.zh.md)。`MLF-3A` 已验收，`MLF-3B` writer 与 `MLF-3E` 诊断标准事件优先已有聚焦验证。

英文辅文：[missile_lethality_warhead_effects_task_clusters_20260609.md](missile_lethality_warhead_effects_task_clusters_20260609.md)

父子项目链接：

- A2 指针：[../README.zh.md](../README.zh.md)
- MLF-2 归档：[../missile_lethality_geometry_fuze/README.zh.md](../missile_lethality_geometry_fuze/README.zh.md)
- 当前 README：[README.zh.md](README.zh.md)
- 当前状态：[missile_lethality_warhead_effects_current_status_20260609.zh.md](missile_lethality_warhead_effects_current_status_20260609.zh.md)
- 派发队列：[missile_lethality_warhead_effects_dispatch_queue_20260609.zh.md](missile_lethality_warhead_effects_dispatch_queue_20260609.zh.md)

## 边界决定

MLF-3 只处理起爆后的通用战斗部作用和载荷事实。它可以修改战斗部机制事件、空间覆盖事件、部件受载事件、现有效果模型的标准事件输出、诊断投影和聚焦测试。

MLF-3 不输出“击毁”。它输出的是：战斗部机制、机制载荷、空间覆盖和部件受载，供后续脆弱性、结构失效和残骸阶段消费。

数据只按 research 规则进入：通用、未校准、可替换；具体型号数据只能预留字段和替换路径，不能在本阶段作为真实参数落地。

## 有限任务簇列表

| Cluster | Owner | Model / reasoning | Goal | Write set | Non-goals | Validation | Closure gate | Dependency / parallel | Round cap | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `MLF-3A Boundary And Inventory` | Sartre / current session subagent | n/a | 盘点现有 warhead/spatial/component 字段、测试和 live writer 缺口 | 本子项目文档；只读源码/测试审计记录 | runtime 修改、参数调优、真实弹种校准 | docs diff check；只读审计 packet | 缺口和可复用入口可由未来 worker 独立恢复 | first, serial | 1 | accepted |
| `MLF-3B Standard Event Writers` | main thread | n/a | 增加 warhead/spatial/component recorder 与 event-store writer | `src/core/interfaces/engagement_event_recorder.h`；`src/core/engine/simulation_kernel_engagement_event_store.*`；相关 bindings/tests | 修改效果物理、改变 damage/reward | `ef_py` build；engagement event capture tests | 起爆后标准事件可导出，parent/chain 与 MLF-2 对齐 | after 3A | 2 | focused pass / wider live gate pending |
| `MLF-3C Generic Blast-Fragmentation Loads` | future worker | n/a | 实现通用未校准破片/爆风机制载荷 | `src/models/weapons/detail/default_effects_warhead_detail.inc`；focused tests | 真实 AIM-120C 参数、连续杆、Pk | family/range/aspect focused tests | 载荷随距离、方向和 family 改变 | after 3B | 2 | planned |
| `MLF-3D Spatial Coverage And Component Load` | future worker | n/a | 将机制载荷投影到 hitbox/component 并写标准受载事件 | `default_effects_spatial_projection_detail.inc`；component-load tests | 部件失效概率校准、结构断裂 | focused projection tests | 空间覆盖和部件受载可从标准事件读出 | after 3C | 2 | planned |
| `MLF-3E Diagnostics Projection` | main thread | n/a | 诊断优先消费标准 warhead/spatial/component 事件 | `tools/diagnostics/air_combat_stage0_process_probe.py`；diagnostics tests | reward 语义、效果物理 | process probe tests | 旧 `EffectsEvent` 只作同链路缺省回退 | after 3B-D | 2 | focused pass |
| `MLF-3F Runtime Handoff Gate` | main thread / future worker | n/a | 钉住未起爆无载荷、起爆一次载荷链 | focused fuze/warhead tests | 直接 kill、直接 crash、实体删除 | gate tests | 未起爆路径没有 warhead/spatial/component 标准事件 | after 3E | 1 | planned |
| `MLF-3G Acceptance And Archive Prep` | main thread | n/a | 汇总 accepted/held 状态并归档 | 本子项目 README/status/task cluster/dispatch/archive；A2 README | 过度声明结构解体、Pk、真实弹种结论 | docs diff check + referenced tests | accepted/held 状态与证据一致 | last, serial | 1 | planned |

## 派发规则

- 每个 worker packet 必须只对应上表一个 cluster。
- 不允许两个 worker 同时修改 recorder 接口、event-store writer、效果模型核心片段或 status line。
- 严禁创建新的会话线程；如使用 subagent，只能作为当前会话内受控派发。
- MLF-3B 之前不得写 runtime；MLF-3A 只读。
- 任何实现都必须保持“未起爆没有战斗部载荷”。

## Worker Packet 要求

```md
status: pass | partial | blocked | failed
touched files:
commands/outcomes:
remaining paths:
behavior risks:
integration notes:
```

每个返回包还必须说明：

- 是否新增或改变标准事件字段。
- 是否增加默认参数；若有，来源和证据等级是什么。
- 若涉及数据，是否保持通用 research 口径，并保留 source category、scope、unit、uncertainty 和 replacement rule。
- 未起爆路径是否仍无 warhead/spatial/component 事件。
- 是否避免了直接 kill、直接坠毁或实体删除规则。

## 验证计划

规划阶段验证：

```bash
git diff --check -- \
  docs/task/air_combat/a2_high_fidelity_damage_model/missile_lethality_warhead_effects \
  docs/task/air_combat/a2_high_fidelity_damage_model/README.md \
  docs/task/air_combat/a2_high_fidelity_damage_model/README.zh.md
```

进入代码后，按实际写入范围补充：

```bash
cmake --build build-workshop --target ef_py -j2
PYTHONPATH=build-workshop ./.venv/bin/python -m pytest tests/runtime/engagement/test_live_engagement_event_capture.py -q
PYTHONPATH=build-workshop ./.venv/bin/python -m pytest tests/runtime/air_combat/test_weapon_guidance_realism_guards.py -q -k "warhead or fuze"
PYTHONPATH=build-workshop ./.venv/bin/python -m pytest tests/diagnostics/test_air_combat_process_probe.py -q
```

## 验收标准

- 起爆后能产生同链路的 warhead/spatial/component 标准事件。
- 未起爆路径没有战斗部载荷事件。
- 破片/爆风载荷随距离、方位、family 和空间覆盖改变。
- 诊断能解释部件受载，但不声明击毁。
- 默认参数都有证据等级和适用范围。

## 残余地图

| Residual | Owner | Release condition |
| --- | --- | --- |
| 连续杆切割 | future MLF-4 | MLF-3 blast-fragmentation 标准载荷链 accepted 后 |
| 目标脆弱性/失效概率 | future MLF-5 | ComponentLoadEvent 稳定后 |
| 结构解体和残骸 | future MLF-6/MLF-8 | 部件失效和结构失效模型 accepted 后 |
| Pk/统计层 | future MLF-9 | 高细节链路可回放后 |
| AIM-120C/MQ-9 个案 | future calibration gate | 几何、引信、战斗部、目标脆弱性和结构模型都有可追溯证据 |
