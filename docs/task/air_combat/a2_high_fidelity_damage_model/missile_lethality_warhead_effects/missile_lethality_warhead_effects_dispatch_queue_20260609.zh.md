# A2 MLF-3 派发队列

状态：`2026-06-09` MLF-3B/3E focused pass；`MLF-3A-X1` 已验收，`MLF-3B-W1` writer 和 `MLF-3E-W1` 诊断标准事件优先已有聚焦验证。

英文辅文：[missile_lethality_warhead_effects_dispatch_queue_20260609.md](missile_lethality_warhead_effects_dispatch_queue_20260609.md)

父任务簇：[missile_lethality_warhead_effects_task_clusters_20260609.zh.md](missile_lethality_warhead_effects_task_clusters_20260609.zh.md)

## 边界

本队列只用于 MLF-3 战斗部作用和通用破片/爆风载荷。任何派发都不得创建新的会话线程，不得进入连续杆、结构解体、残骸、Pk、AIM-120C/MQ-9 个案校准或直接击毁规则。

数据边界：本阶段按 research 口径只使用通用、未校准、可替换的数据和方法。可以预留具体型号补充入口，但不得把 CMO-DB、公开网页、历史测试或工程假设写成真实 AIM-120C/MQ-9 参数。

## 待派发包

| Packet | Cluster | Assignee | Write set | Required output | Status |
| --- | --- | --- | --- | --- | --- |
| `MLF-3A-X1` | `MLF-3A Boundary And Inventory` | Sartre / current session subagent | read-only inspection; optional status note only | 盘点当前 warhead/spatial/component 字段、writer 缺口、诊断投影和可复用测试入口；不得改 runtime。 | accepted |
| `MLF-3B-X1` | `MLF-3B Standard Event Writers` | Sartre / current session subagent | read-only writer-path audit | 找出写入 `WarheadMechanismEvent`、`SpatialCoverageEvent`、`ComponentLoadEvent` 的最小 producer/recorder 路径。 | accepted via 3A |
| `MLF-3B-W1` | `MLF-3B Standard Event Writers` | main thread | recorder/event-store/bindings/tests after X1 | 写入标准战斗部、空间覆盖和部件受载事件。 | focused pass / wider live gate pending |
| `MLF-3C-W1` | `MLF-3C Generic Blast-Fragmentation Loads` | future worker | effects warhead detail + focused tests | 建立通用未校准破片/爆风载荷，带证据等级。 | planned |
| `MLF-3D-W1` | `MLF-3D Spatial Coverage And Component Load` | future worker | spatial projection/component load tests | 将载荷投影到目标部件并写标准受载事实。 | planned |
| `MLF-3E-W1` | `MLF-3E Diagnostics Projection` | main thread | process probe + diagnostics tests | 诊断优先消费标准事件，旧 `EffectsEvent` 只作回退。 | focused pass |
| `MLF-3F-W1` | `MLF-3F Runtime Handoff Gate` | main thread / future worker | focused gate tests | 钉住未起爆无载荷、起爆一次载荷链。 | planned |
| `MLF-3G-C1` | `MLF-3G Acceptance And Archive Prep` | main thread | docs/archive/index | 汇总验收证据和后续残余。 | planned |

## 当前派发建议

下一步建议补更广 live geometry/fuze 门：证明真实发射起爆路径也导出标准事件，未起爆路径没有 warhead / spatial / component load 标准事件。之后再进入 `MLF-3C/3D` 的通用破片/爆风载荷和空间/部件投影参数面。

## Worker Packet 合同

```md
status: pass | partial | blocked | failed
touched files:
commands/outcomes:
remaining paths:
behavior risks:
integration notes:
```

返回包必须明确：

- 是否发现标准事件 live writer。
- 哪些字段仍只存在于 `EffectsEvent` 或 debug/projection 路径。
- 哪些测试可以复用，哪些只能作为历史脚手架。
- 是否存在会让未起爆路径产生载荷的风险。

## 集成说明

- 主线程负责验收返回包和更新状态。
- 当前运行中：无。
- `MLF-3B` 仍需更广 live geometry/fuze 门；当前仅聚焦通过。
