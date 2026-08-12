# A2 MLF-5 部件失效任务簇

状态：`2026-06-11` accepted / archived finite task-cluster record for [README.zh.md](README.zh.md)。MLF-5A 只读盘点、5B 标准部件损伤事件面、5C 通用失效概率、5D 状态交接、5E 诊断/gate 与 5F 收口归档均已验收。

英文辅文：[missile_lethality_component_failure_task_clusters_20260611.md](missile_lethality_component_failure_task_clusters_20260611.md)

父子项目链接：

- A2 指针：[../../../README.zh.md](../../../README.zh.md)
- MLF-3 指针：[../../../missile_lethality_warhead_effects/README.zh.md](../../../missile_lethality_warhead_effects/README.zh.md)
- MLF-4 指针：[../../../missile_lethality_continuous_rod/README.zh.md](../../../missile_lethality_continuous_rod/README.zh.md)
- 当前 README：[README.zh.md](README.zh.md)
- 当前状态：[missile_lethality_component_failure_current_status_20260611.zh.md](missile_lethality_component_failure_current_status_20260611.zh.md)
- 派发队列：[missile_lethality_component_failure_dispatch_queue_20260611.zh.md](missile_lethality_component_failure_dispatch_queue_20260611.zh.md)
- 收口验收：[missile_lethality_component_failure_acceptance_20260611.zh.md](missile_lethality_component_failure_acceptance_20260611.zh.md)

## 边界决定

MLF-5 可以标准化并验证部件失效事实：部件完整度前后值、失效概率、概率样本、失效模式、严重度、证据来源和对已有损伤状态的 handoff。

MLF-5 不得输出结构解体、空中碎裂、坠毁、残骸、训练胜负、实体删除、Pk 或真实弹种结论。它也不得单独定义“飞行是否能够维持”；飞行后果必须通过已有损伤、动力学、推进、传感器和地面接触系统传播。

## 有限任务簇列表

| Cluster | Owner | Model / reasoning | Goal | Write set | Non-goals | Validation | Closure gate | Dependency / parallel | Round cap | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `MLF-5A-X1 Boundary And Inventory` | read-only worker `019eb545-f28c-7723-8e9a-07c16138ebe0` / Herschel | inherited / inherited | 盘点 ComponentDamageEvent、failure probability、failure mode、integrity、redundancy、历史测试和缺口 | 本子项目文档；只读源码/测试审计 packet | runtime 修改、参数调优、真实弹种校准 | docs diff check；引用源码/测试清单 | current status 命名可复用字段和缺口 | first, serial | 1 | accepted |
| `MLF-5B-W1 Component Damage Event Surface` | current-session worker `019eb555-8c9b-78e3-8d02-4b6b05f56b14` / Helmholtz + main-thread repair | inherited / inherited | 稳定同链路部件损伤标准事件和绑定/导出 | `src/runtime/contracts/**`、event-store、bindings、focused tests | 概率模型重写、结构解体、坠毁 | contract shape tests + focused live event tests | 样本触发后可写出 component damage 行，未起爆/无载荷/未触发样本无虚假行 | after 5A | 2 | accepted |
| `MLF-5C-W1 Generic Vulnerability Probability` | main thread local continuation | inherited / inherited | 建立通用、未校准、可替换的部件失效概率模型 | default effects vulnerability/probability focused tests | 具体 AIM-120C/MQ-9 校准、Pk authority | probability trend tests + evidence-label checks | 概率随载荷、切割曝光、部件脆弱性、冗余和方位变化 | after 5B | 1 | accepted |
| `MLF-5D-W1 Component State Handoff` | main thread local continuation | inherited / inherited | 将部件失效样本和完整度变化写入已有损伤状态并导出前后值 | contracts、default effects state sample、bindings、focused tests | 单独定义飞行可维持性、直接 crash/kill | state-before/after tests + maintained-system handoff evidence | 标准事件复制实际状态写入前后值，现有损伤状态继续传播 | after 5C | 1 | accepted |
| `MLF-5E-W1 Diagnostics And Gates` | main thread local continuation | inherited / inherited | 让诊断解释部件损伤事实并保护禁止声明 | `tools/diagnostics/air_combat_weapon_employment_process_probe.py`、diagnostics tests | reward 语义、训练胜负、实体删除 | diagnostics tests + no-load/no-detonation gates | probe 行能解释部件损伤，且无虚假失效/坠毁行 | after 5B-D | 1 | accepted |
| `MLF-5F-C1 Acceptance And Archive Prep` | main thread | n/a | 汇总 accepted/held 状态并同步索引 | 本 README/status/task cluster/dispatch/archive；A2 README；MLF-4 指针 | 过度声明解体、坠毁、残骸、Pk 或真实弹种结论 | docs diff check + referenced tests | accepted/held 状态与证据一致 | after 5B-E | 1 | accepted |

## 派发规则

- 每个 worker packet 必须只对应上表一个 cluster。
- 不允许两个 worker 同时修改事件合同、event-store writer、默认概率模型、损伤状态 handoff、诊断投影或状态行。
- 严禁创建新的会话线程；如使用 subagent，只能作为当前会话内受控派发。
- 5F 已由主线程本地收口，不分发 worker；5C/5D/5E 同样由主线程本地串行推进，不计作新 worker 派发。
- 验收/收口保持串行。
- 若某个 cluster 超过 round cap，停止并重新界定范围，不追加开放式 wave。

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

- 是否改变标准事件字段。
- 是否新增默认常量；若有，来源类别、适用范围、单位、不确定性和替换规则是什么。
- 未起爆、无受载和无正切割路径是否仍无虚假部件失效。
- 是否避免了结构解体、坠毁、残骸、实体删除、Pk 和训练胜负规则。
- 是否提升、改写或保留历史 Phase 5 / `weapon_guidance_realism` 测试。

## 验证计划

已执行的 5C/5D/5E runtime 验证：

```bash
cmake --build build-workshop --target ef_py -j2
PYTHONPATH=build-workshop ./.venv/bin/python -m pytest tests/runtime/air_combat/test_component_damage_event_surface.py tests/runtime/air_combat/test_component_failure_probability_surface.py tests/runtime/air_combat/test_warhead_spatial_component_projection.py tests/runtime/air_combat/test_live_detonation_event_surface.py -q
PYTHONPATH=build-workshop ./.venv/bin/python -m pytest tests/runtime/air_combat/test_diagnostics_probe_contracts.py -q
PYTHONPATH=build-workshop ./.venv/bin/python -m pytest tests/runtime/air_combat -q -k "component_damage or vulnerability or component_failure"
```

清理绑定默认值、补充近炸距离/方位探测并修复调试抽样种子后的结果：组合回归 `42 passed`；5E 诊断 `26 passed`；宽筛选 `41 passed, 282 deselected, 7 subtests passed`。先前的 nanobind 退出泄漏提示在收集阶段和实际运行阶段复测中均不再出现。

规划阶段验证：

```bash
git diff --check -- \
  docs/systems/effects/reviews/a2_high_fidelity_damage_model_20260602/missile_lethality_evidence_20260619/missile_lethality_component_failure \
  docs/systems/effects/reviews/a2_high_fidelity_damage_model_20260602/README.md \
  docs/systems/effects/reviews/a2_high_fidelity_damage_model_20260602/README.zh.md \
  docs/systems/effects/reviews/a2_high_fidelity_damage_model_20260602/missile_lethality_evidence_20260619/missile_lethality_continuous_rod/README.md \
  docs/systems/effects/reviews/a2_high_fidelity_damage_model_20260602/missile_lethality_evidence_20260619/missile_lethality_continuous_rod/README.zh.md
```

收口阶段按写入范围补充：

```bash
cmake --build build-workshop --target ef_py -j2
PYTHONPATH=build-workshop ./.venv/bin/python -m pytest tests/runtime/air_combat/test_diagnostics_probe_contracts.py -q
PYTHONPATH=build-workshop ./.venv/bin/python -m pytest tests/runtime/air_combat -q -k "component_damage or vulnerability or component_failure"
```

## 验收标准

- 起爆后的部件受载/切割曝光能产生同链路部件损伤事实。
- 部件损伤事实包含概率、样本、失效模式、完整度前后值和证据标签。
- 未起爆、无载荷或无正切割路径不产生虚假部件失效。
- 部件状态传入已有损伤和飞行/系统模型，而不是 MLF-5 自己判断目标是否坠毁。
- 诊断能解释部件损伤事实，但不声明结构解体、残骸、Pk 或具体弹种杀伤。

## 残余地图

Immediate:

- 保持 `MLF-5A-F` accepted 状态，不继续分发。
- MLF-5 已归档；后续结构解体、残骸、Pk 或具体弹种校准另建子项目。

Follow-on:

- MLF-6 消费部件失效，建立结构解体。
- MLF-8 消费结构结果，建立残骸和碎片对象生命周期。

Deferred:

- 真实弹种/目标校准、Pk、训练胜负和实体删除。
