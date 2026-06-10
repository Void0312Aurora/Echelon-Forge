# A2 MLF-4 连续杆任务簇

状态：`2026-06-10` finite task-cluster plan for [README.zh.md](README.zh.md)。MLF-4 仅处于 planning，不声明 runtime accepted。

英文辅文：[missile_lethality_continuous_rod_task_clusters_20260610.md](missile_lethality_continuous_rod_task_clusters_20260610.md)

父子项目链接：

- A2 指针：[../README.zh.md](../README.zh.md)
- MLF-3 指针：[../missile_lethality_warhead_effects/README.zh.md](../missile_lethality_warhead_effects/README.zh.md)
- 当前 README：[README.zh.md](README.zh.md)
- 当前状态：[missile_lethality_continuous_rod_current_status_20260610.zh.md](missile_lethality_continuous_rod_current_status_20260610.zh.md)
- 派发队列：[missile_lethality_continuous_rod_dispatch_queue_20260610.zh.md](missile_lethality_continuous_rod_dispatch_queue_20260610.zh.md)

## 边界决定

MLF-4 可以标准化并验证起爆后的连续杆/切割事实。它可以修改 rod 相关事件字段、默认效果模型中的 rod 几何、部件切割载荷投影、诊断行和聚焦测试。

MLF-4 不得输出部件失效、结构解体、残骸、坠毁、训练胜负、实体删除、Pk 或真实弹种结论。

## 有限任务簇列表

| Cluster | Owner | Model / reasoning | Goal | Write set | Non-goals | Validation | Closure gate | Dependency / parallel | Round cap | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `MLF-4A-X1 Boundary And Inventory` | read-only worker | `gpt-5.4-mini` / `xhigh` | 盘点现有 rod 字段、continuous_rod 分支、历史测试和事件缺口 | 本子项目文档；只读源码/测试审计 packet | runtime 修改、参数调优、真实弹种校准 | docs diff check；引用源码/测试清单 | current status 命名可复用字段和缺口 | first, serial | 1 | accepted |
| `MLF-4B-W1 Standard Rod Event Surface` | future worker | n/a | 稳定 warhead/component-load 事件中的标准 rod/cut 字段 | `src/runtime/contracts/engagement_contracts.h`；bindings/export tests；必要时 event-store writer | 新失效状态、结构解体、击毁 | `ef_py` build；engagement contract shape tests；rod event 聚焦测试 | continuous_rod 起爆输出同链路正 rod 事实；非 rod 为零 | after 4A | 2 | planned |
| `MLF-4C-W1 Generic Rod Geometry` | future worker | n/a | 建立或确认通用切割带/方向投影 | `src/models/weapons/default_effects_model.cpp`；`src/models/weapons/detail/default_effects_warhead_detail.inc`；geometry helpers；focused tests | 真实导弹 rod count/velocity；Pk | 距离/方位/方向轴聚焦测试 | rod cut margin 随距离、侧向/方位和方向轴改变 | after 4B | 2 | planned |
| `MLF-4D-W1 Component Cut Projection` | future worker | n/a | 将 rod 切割曝光投影到 hitbox/component | `src/models/weapons/detail/default_effects_spatial_projection_detail.inc`；state/result fragments；component-load tests | 部件失效概率或 integrity 修改 | 左/右/部件投影聚焦测试 | 部件行暴露 rod cut margin 和 cut source，但不输出失效 | after 4C | 2 | planned |
| `MLF-4E-W1 Diagnostics And Gates` | future worker | n/a | 诊断优先读取标准 rod 事实，并保护未起爆/非 rod 路径 | `tools/diagnostics/air_combat_stage0_process_probe.py`；diagnostics tests；no-detonation tests | reward 语义、训练胜负、实体删除 | diagnostics tests + 未起爆/非 rod gates | probe 行能解释 rod/cut 事实，且无虚假 rod 行 | after 4D | 2 | planned |
| `MLF-4F-C1 Acceptance And Archive Prep` | main thread | n/a | 汇总 accepted/held 状态并同步索引 | 本 README/status/task cluster/dispatch/archive；A2 README；必要时 MLF-3 指针 | 过度声明失效、解体、Pk 或真实弹种结论 | docs diff check + referenced tests | accepted/held 状态与证据一致 | after 4B-E | 1 | planned |

## 派发规则

- 每个 worker packet 必须只对应上表一个 cluster。
- 不允许两个 worker 同时修改事件合同、event-store writer、默认效果模型 rod 片段、诊断投影或状态行。
- 严禁创建新的会话线程；如使用 subagent，只能作为当前会话内受控派发。
- 验收/收口保持串行。
- 若某个 cluster 超过 round cap，停止并重新界定范围，不追加开放式 wave。
- 保持 gate：未起爆没有 rod/cut 事实；非 rod family 不得输出正 rod/cut 事实。

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
- 未起爆和非 rod 路径是否仍无正 rod/cut 事实。
- 是否避免了部件失效、结构解体、坠毁、实体删除、Pk 和训练胜负规则。
- 是否提升、改写或保留历史 Phase 3 测试。

## 验证计划

规划阶段验证：

```bash
git diff --check -- \
  docs/task/air_combat/a2_high_fidelity_damage_model/missile_lethality_continuous_rod \
  docs/task/air_combat/a2_high_fidelity_damage_model/README.md \
  docs/task/air_combat/a2_high_fidelity_damage_model/README.zh.md \
  docs/task/air_combat/a2_high_fidelity_damage_model/missile_lethality_warhead_effects/README.md \
  docs/task/air_combat/a2_high_fidelity_damage_model/missile_lethality_warhead_effects/README.zh.md
```

进入 runtime 后，按写入范围补充：

```bash
cmake --build build-workshop --target ef_py -j2
PYTHONPATH=build-workshop ./.venv/bin/python -m pytest tests/runtime/engagement/test_engagement_contract_shape.py -q
PYTHONPATH=build-workshop ./.venv/bin/python -m pytest tests/runtime/engagement/test_live_engagement_event_capture.py -q
PYTHONPATH=build-workshop ./.venv/bin/python -m pytest tests/runtime/air_combat/test_diagnostics_probe_contracts.py -q
PYTHONPATH=build-workshop ./.venv/bin/python -m pytest tests/runtime/air_combat -q -k "mlf4 or continuous_rod or rod_cut"
```

## 验收标准

- `continuous_rod` 起爆产生同链路 rod/cut 事实。
- 非 rod 和未起爆路径不产生正 rod/cut 事实。
- rod/cut 事实随距离、侧向/方位、方向轴和部件投影变化。
- 诊断能从标准事件解释 rod/cut 事实。
- 部件行暴露切割曝光，但不声明部件失效或结构解体。

## 残余地图

Immediate:

- 在 4B 中固定现有 `rod_cut_margin` 字段的标准事件语义；4A 建议先复用现有字段。
- 将 accepted MLF-4 测试与历史 Phase 3 retained scaffold 测试分开。

Follow-on:

- MLF-5 消费切割事实，建立部件失效概率。
- MLF-6 消费部件失效，建立结构解体。

Deferred:

- 真实弹种 rod 参数、Pk、残骸、AIM-120C/MQ-9 校准。
