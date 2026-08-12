# A2 MLF-2 导弹接近几何与引信评估任务簇

状态：`2026-06-09` archived finite task-cluster plan for [README.zh.md](README.zh.md)。MLF-2B、MLF-2C、MLF-2D、MLF-2E、MLF-2F 和 MLF-2G 已验收。

英文辅文：[missile_lethality_geometry_fuze_task_clusters_20260609.md](missile_lethality_geometry_fuze_task_clusters_20260609.md)

父子项目链接：

- A2 指针：[../../../README.zh.md](../../../README.zh.md)
- 当前 README：[README.zh.md](README.zh.md)
- 当前状态：[missile_lethality_geometry_fuze_current_status_20260609.zh.md](missile_lethality_geometry_fuze_current_status_20260609.zh.md)
- 派发队列：[missile_lethality_geometry_fuze_dispatch_queue_20260609.zh.md](missile_lethality_geometry_fuze_dispatch_queue_20260609.zh.md)
- MLF-1 证据包：[../../../missile_lethality_model_foundation/archive/mlf_1_chain_contract_accepted_20260609/README.zh.md](../../../missile_lethality_model_foundation/archive/mlf_1_chain_contract_accepted_20260609/README.zh.md)

## 边界决定

本子项目只推进 MLF-2：接近几何和引信评估。它可以修改受控场景、事件合同、事件记录、诊断导出和聚焦测试；它不能实现破片、连续杆、结构解体、残骸对象、Pk 或具体弹种/目标杀伤结论。

MLF-2 的输出不是“击毁”。输出是：最近接近几何、引信是否解保、是否触发、触发类型、触发/未触发/延迟/失败原因，以及可传给后续战斗部模型的起爆状态。

## 有限任务簇列表

| Cluster | Owner | Model / reasoning | Goal | Write set | Non-goals | Validation | Closure gate | Dependency / parallel | Round cap | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `MLF-2A Boundary And Index` | main thread | n/a | 创建独立 MLF-2 子项目，固定目标、边界、阶段和父级导航 | 本子项目 README/status/task cluster/dispatch queue/archive index；A2 父级 README；MLF-1 指针 README | runtime 改动、probe 实现、参数调优、worker 派发 | `git diff --check -- docs/systems/effects/reviews/a2_high_fidelity_damage_model_20260602/missile_lethality_evidence_20260619/missile_lethality_geometry_fuze docs/systems/effects/reviews/a2_high_fidelity_damage_model_20260602/README*.md` | 子项目可由未来 Agent 独立恢复，且不会在 MLF-1 目录继续 MLF-2 | first, serial | 1 | pass |
| `MLF-2B Controlled Geometry Fixtures` | Sartre `019eac6a-0546-7cc0-ab6b-9c914dcb4c24` | n/a | 设计或实现固定距离、方位、闭合速度、高度差、目标姿态的受控场景/测试夹具 | `tests/runtime/air_combat/weapon_guidance_realism/geometry_fixtures.py`；`tests/runtime/air_combat/test_weapon_guidance_realism_guards.py` | 引信物理、战斗部效果、击毁阈值、真实弹种校准 | worker packet + 聚焦 fixture/probe 测试；JSON 或 py_compile 检查 | 同一夹具可稳定生成不同几何输入，不依赖训练策略是否开火 | after 2A; serial before event writers | 2 | pass |
| `MLF-2C NearestApproachEvent Writer` | Sartre `019eac6a-0546-7cc0-ab6b-9c914dcb4c24` | n/a | 让 live 或受控场景能写入最近接近事件 | `src/components/combat/weapon.h`；`src/core/interfaces/engagement_event_recorder.h`；`src/core/engine/simulation_kernel_engagement_event_store.h`；`src/core/engine/simulation_kernel_engagement_event_store.cpp`；`src/core/engine/simulation_kernel_weapon_release_service.cpp`；`src/interfaces/python/bindings_core.cpp`；`src/systems/combat/damage_system.h`；相关 geometry/fuze tests | 引信触发判定、效果载荷、reward 消费 | `ef_py` build；3 个导弹几何/引信聚焦测试；7 个 engagement event capture 回归；diff check | 未起爆和错过目标也有最近接近记录和原因；最近点时间来自最近点刷新时刻 | after 2B; serial before FuzeEvaluationEvent | 2 | pass |
| `MLF-2D FuzeEvaluationEvent Writer` | Sartre `019eac6a-0546-7cc0-ab6b-9c914dcb4c24` / future fuze worker | n/a | 写入解保、接触、近炸、延迟、未触发和失败原因 | `src/core/interfaces/engagement_event_recorder.h`；`src/core/engine/simulation_kernel_engagement_event_store.h`；`src/core/engine/simulation_kernel_engagement_event_store.cpp`；`src/systems/combat/damage_system.h`；相关 geometry/fuze tests | 破片/连续杆、结构解体、直接 kill、真实 fuze authority | `ef_py` build；4 个导弹几何/引信聚焦测试；7 个 engagement event capture 回归；diff check | 接触和近炸判定分开；没有触发也有 failure/no-trigger reason | after 2C field ids; can parallel with 2E after APIs freeze | 2 | pass |
| `MLF-2E Diagnostics Projection` | Sartre `019eac6a-0546-7cc0-ab6b-9c914dcb4c24` / main thread | n/a | 让 process probe 按一枚弹输出 geometry/fuze 阶段行和 summary | `tools/diagnostics/air_combat_weapon_employment_process_probe.py`；`tests/runtime/air_combat/test_diagnostics_probe_contracts.py`；本子项目证据记录 | reward 语义、runtime 物理判定、旧字段长期别名 | `tests/runtime/air_combat/test_diagnostics_probe_contracts.py -q` | 不依赖 `last_effect_*` 判断触发原因；无起爆也能报告原因 | after 2C/2D API names freeze | 2 | pass |
| `MLF-2F Runtime Handoff Gate` | Sartre `019eac6a-0546-7cc0-ab6b-9c914dcb4c24` / main thread | n/a | 将起爆状态交给现有效果模型，未触发路径明确不产生物理效果 | `tests/runtime/air_combat/weapon_guidance_realism/fuze.py`；本子项目证据记录 | 战斗部机制、目标破碎、训练胜负、实体删除 | 3 个引信 gate 聚焦测试 | 起爆才进入后续效果；未触发、失败、未解保不沉默消失 | after 2C/2D/2E | 2 | pass |
| `MLF-2G Acceptance And Archive Prep` | main thread | n/a | 汇总证据，更新状态、父级导航和残余地图 | 本子项目 README/status/task cluster/dispatch queue/archive index；A2 README | 过度声明真实 AIM-120C/MQ-9、Pk 或结构解体 | docs diff check + referenced focused tests | accepted/held 状态与证据一致，并明确 MLF-3+ 残余 | last, serial | 1 | pass |

## 派发规则

- 每个 worker packet 必须只对应上表一个 cluster。
- 不允许两个 worker 同时修改同一张事件字段表、同一段 runtime 判定或同一个 status line。
- `MLF-2B` 必须先于 runtime writer，因为没有受控几何输入就无法验收触发差异。
- `MLF-2C` 与 `MLF-2D` 的字段名冻结后，`MLF-2E` 才能派发。
- `MLF-2F` 必须在 geometry/fuze 事件可观察后执行。
- 严禁创建新的会话线程；如使用 subagent，只能作为当前会话内受控派发。

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

- 是否修改了事件字段名称或含义。
- 是否增加了新默认参数；若有，来源和证据等级是什么。
- 是否有未触发/失败路径证据。
- 是否避免了直接 kill、直接坠毁或实体删除规则。

## 验证计划

规划阶段验证：

```bash
git diff --check -- \
  docs/systems/effects/reviews/a2_high_fidelity_damage_model_20260602/missile_lethality_evidence_20260619/missile_lethality_geometry_fuze \
  docs/systems/effects/reviews/a2_high_fidelity_damage_model_20260602/README.md \
  docs/systems/effects/reviews/a2_high_fidelity_damage_model_20260602/README.zh.md \
  docs/systems/effects/reviews/a2_high_fidelity_damage_model_20260602/missile_lethality_evidence_20260619/missile_lethality_model_foundation/README.md \
  docs/systems/effects/reviews/a2_high_fidelity_damage_model_20260602/missile_lethality_evidence_20260619/missile_lethality_model_foundation/README.zh.md
```

进入代码后，至少需要按实际写入范围补充：

```bash
python -m py_compile tools/diagnostics/air_combat_weapon_employment_process_probe.py tests/runtime/air_combat/test_diagnostics_probe_contracts.py
python -m pytest tests/runtime/air_combat/test_diagnostics_probe_contracts.py -q
python -m pytest tests/runtime/air_combat/test_air_combat_reward_surface.py -q
```

如新增 C++ contract 或 event-store 测试，还必须补相应 build/CTest 目标。

## 验收标准

- 每枚导弹有稳定链路 id，可连接发射、最近接近、引信评估和后续效果事件。
- 受控距离、方位、速度、高度差和姿态变化能产生可解释差异。
- 没有起爆时也报告原因。
- 接触、近炸、未解保、错过窗口、延迟和故障不是同一个模糊状态。
- 起爆状态只传给后续效果模型，不直接生成击毁、碎裂、坠毁或 reward 结论。
- 旧 `last_effect_*` 字段不被扩展成长期接口。

## 残余地图

| Residual | Owner | Release condition |
| --- | --- | --- |
| 战斗部破片/连续杆模型缺失 | future MLF-3/MLF-4 | MLF-2 只能给出起爆状态，后续模型负责作用机制 |
| 结构解体和残骸对象缺失 | future MLF-6/MLF-8 | 部件载荷与结构失效模型通过后再处理 |
| Pk/统计层缺失 | future MLF-9 | 高细节链路能运行后才做趋势校验 |
| AIM-120C/MQ-9 个案仍不能下结论 | future calibration gate | 几何、引信、战斗部、目标脆弱性和结构模型都有可追溯证据 |
