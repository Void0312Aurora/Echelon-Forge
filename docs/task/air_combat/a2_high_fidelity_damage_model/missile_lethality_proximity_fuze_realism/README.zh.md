# A2 导弹近炸引信真实性代理

状态：`2026-06-16` PF-R5 surrogate 验证完成但保留残余 / PF-R6 文档收口已同步。本子项目记录公开资料边界、
当前 runtime 缺口、surrogate contract、非权威 runtime 解释性切片，以及聚焦矩阵验证证据。

语言：

- 英文主文：[README.md](README.md)
- 中文辅文：`README.zh.md`

输入：

- A2 父入口：[../README.zh.md](../README.zh.md)
- MLF-2 几何/引信证据指针：
  [../missile_lethality_geometry_fuze/README.zh.md](../missile_lethality_geometry_fuze/README.zh.md)
- 目标几何 retained follow-on：
  [../missile_lethality_target_geometry/README.zh.md](../missile_lethality_target_geometry/README.zh.md)
- Agent 子项目标准：
  [../../../../agent/rules/subproject_creation_standard.zh.md](../../../../agent/rules/subproject_creation_standard.zh.md)
- 真实性与 authority 边界：
  [../../../../standards/foundation/realism_authority_boundary.zh.md](../../../../standards/foundation/realism_authority_boundary.zh.md)
- 公开来源准入：
  [../../../../standards/foundation/public_data_source_admission.zh.md](../../../../standards/foundation/public_data_source_admission.zh.md)
- 当前 runtime 实现面：
  [../../../../../src/systems/combat/damage_system_common.h](../../../../../src/systems/combat/damage_system_common.h)
- 当前引信真实性测试入口：
  [../../../../../tests/runtime/air_combat/weapon_guidance_realism/test_launch_guidance_and_dynamics.py](../../../../../tests/runtime/air_combat/weapon_guidance_realism/test_launch_guidance_and_dynamics.py)
- 公开机制参考：
  [FAS Naval Weapons, Chapter 14 Fuzing](https://man.fas.org/dod-101/navy/docs/fun/part14.htm)、
  [FAS Naval Weapons, Chapter 13 Warheads](https://man.fas.org/dod-101/navy/docs/fun/part13.htm)、
  [Smithsonian proximity fuze cutaway](https://www.si.edu/object/fuze-proximity-cutaway%3Anasm_A19940233000)、
  [JHU APL Talos continuous-rod paper](https://secwww.jhuapl.edu/techdigest/content/techdigest/pdf/V03-N02/03-02-Brown.pdf)

## 目的

当前空战杀伤链已经可以解释最近接近、引信评估、起爆交接、战斗部效果、连续杆暴露和部件失效事实。
但近期对发射窗口和 damage chain 的检查显示，近炸引信决策本身仍更接近几何代理：主要以最近距离和
触发半径作为起爆门，再叠加可靠性和目标签名缩放。

本子项目为替换该 proxy 建立持久化计划表面。目标不是复刻真实导弹，而是在非权威边界内保留对学习和诊断真正重要的因果结构：
保险/解保、末端跟踪、目标探测、目标穿过引信传感器窗口、起爆时机、战斗部方向和不同机制覆盖。
它不释放真实导弹引信模型、deterministic fuze authority、Pk 或具体弹种杀伤权威。

## 当前状态

| 区域 | 状态 | 证据 | 边界 |
| --- | --- | --- | --- |
| A2 authority | retained / sealed | [../README.zh.md](../README.zh.md) | A2 仍不释放 stock weapon truth、Pk 或 deterministic fuze。 |
| 当前引信事件链 | observed runtime | [../../../../../src/systems/combat/damage_system_common.h](../../../../../src/systems/combat/damage_system_common.h) | 事件可观察不等于引信触发真实。 |
| 当前触发 proxy | known gap | 当前 runtime 的最近距离、触发半径、可靠性和签名缩放行为 | 这是工程代理，不是真实近炸机制。 |
| 目标几何交接 | retained evidence | [../missile_lethality_target_geometry/README.zh.md](../missile_lethality_target_geometry/README.zh.md) | 几何 proxy 是 opt-in / retained evidence，不是默认引信替换。 |
| 公开机制调研 | pass / non-authoritative | [public_mechanism_source_note_20260616.zh.md](public_mechanism_source_note_20260616.zh.md) | 公开资料只能支持机制形状，不能给 AIM-120C-class 隐含参数。 |
| Runtime gap audit | pass / read-only | [current_runtime_gap_audit_20260616.zh.md](current_runtime_gap_audit_20260616.zh.md) | 识别 proxy 缺口；不改变行为。 |
| Surrogate contract | pass / implementation-ready design | [proximity_fuze_surrogate_contract_20260616.zh.md](proximity_fuze_surrogate_contract_20260616.zh.md) | 定义后续合同；实现仍需明确确认。 |
| 实现 | pass / 聚焦 surrogate evidence | [proximity_fuze_runtime_implementation_20260616.zh.md](proximity_fuze_runtime_implementation_20260616.zh.md) | runtime 修改仅限非权威近炸解释性，不是 Pk 或真实引信 authority。 |
| 验证 | pass_with_residuals / 聚焦矩阵证据 | [validation/pf_r5_proximity_fuze_validation_20260616.zh.md](validation/pf_r5_proximity_fuze_validation_20260616.zh.md)；[validation/pf_r5_proximity_fuze_validation_heatmaps_20260616.png](validation/pf_r5_proximity_fuze_validation_heatmaps_20260616.png) | 只验证 surrogate 门控趋势；live guidance 偏置不是纯起爆点对称性测试。 |

## 范围

纳入：

- 建立公开资料层面的非权威近炸机制摘要：保险/解保、探测、末端跟踪、距离/距离率线索、目标方位、起爆时机和未起爆结果。
- 将当前 runtime 链路和机制摘要对齐审计，分清已观察事实和 proxy 假设。
- 设计后续 surrogate contract，区分最近接近、引信传感器探测、引信触发、起爆点和战斗部覆盖。
- 区分 blast-fragmentation 与 continuous-rod 的机制差异。
- 为已实现 surrogate 保留聚焦验证和诊断。

不纳入：

- 超出已批准 surrogate evidence 切片的 runtime 扩展。
- AIM-120C 具体引信阈值、涉密逻辑、真实 target-detecting device 参数或真实 Pk。
- deterministic fuze authority、stock runtime authority 或具体弹种杀伤声明。
- 用 reward 或 terminal-state 调参掩盖引信链建模问题。
- 重开已归档的 MLF-2、MLF-3、MLF-4、MLF-5 或 sealed A2 包。

## 阶段计划

| 阶段 | 目标 | 入口条件 | 退出条件 | 状态 |
| --- | --- | --- | --- | --- |
| `P0 Boundary` | 建立子项目并冻结“不实现”边界 | 用户要求按 `docs/agent` 创建子项目 | README、任务簇、状态、dispatch、acceptance 草案和父链接存在 | active |
| `P1 Public Mechanism` | 记录公开资料中的高层引信机制事实 | P0 存在 | 来源列表和 admitted/rejected claim 已记录，且不含真实参数 | pass |
| `P2 Runtime Gap Audit` | 将当前 runtime 行为和机制事实对比 | P1 机制事实存在 | gap 表分清当前 proxy 与所需 surrogate 行为 | pass |
| `P3 Surrogate Contract` | 设计后续事件和诊断合同 | P2 gap 表存在 | 合同命名 detection、trigger、detonation point 和 mechanism coverage 字段 | pass |
| `P4 Implementation` | 只实现获批的有界 surrogate | P1-P3 经明确确认 | 聚焦 runtime 测试和诊断通过 | pass |
| `P5 Validation` | 运行矩阵测试并对照机制行为 | P4 聚焦测试通过 | 触发半径、初始横向/高度偏置和机制族行为可解释并记录 | pass_with_residuals |
| `P6 Closure` | 同步父文档、验收和残余 | P5 验证存在 | acceptance closeout 记录最终 surrogate 边界 | pass |

## 任务簇

- 任务簇计划：
  [missile_lethality_proximity_fuze_realism_task_clusters_20260616.zh.md](missile_lethality_proximity_fuze_realism_task_clusters_20260616.zh.md)
- 当前状态：
  [missile_lethality_proximity_fuze_realism_current_status_20260616.zh.md](missile_lethality_proximity_fuze_realism_current_status_20260616.zh.md)
- 派发队列：
  [missile_lethality_proximity_fuze_realism_dispatch_queue_20260616.zh.md](missile_lethality_proximity_fuze_realism_dispatch_queue_20260616.zh.md)
- 验收草案：
  [missile_lethality_proximity_fuze_realism_acceptance_20260616.zh.md](missile_lethality_proximity_fuze_realism_acceptance_20260616.zh.md)

## 输出和证据

计划输出：

- 本子项目下的公开资料近炸机制说明。
- 绑定 `damage_system_common.h` 和聚焦测试的当前 runtime gap audit。
- 面向 `nearest_approach`、`fuze_detection`、`fuze_trigger`、`detonation_point`
  和 mechanism coverage 诊断的后续 surrogate contract。
- 第一轮获批 surrogate evidence 切片的聚焦测试。
- 获批实现之后再生成 blast-fragmentation 与 continuous-rod 对照制品。

当前输出：

- 本 planning surface 和有限任务簇列表。
- [public_mechanism_source_note_20260616.zh.md](public_mechanism_source_note_20260616.zh.md)：
  PF-R1 公开机制来源说明。
- [current_runtime_gap_audit_20260616.zh.md](current_runtime_gap_audit_20260616.zh.md)：
  PF-R2 只读 runtime gap audit。
- [proximity_fuze_surrogate_contract_20260616.zh.md](proximity_fuze_surrogate_contract_20260616.zh.md)：
  PF-R3 后续 surrogate contract 和验证计划。
- [proximity_fuze_runtime_implementation_20260616.zh.md](proximity_fuze_runtime_implementation_20260616.zh.md)：
  PF-R4 聚焦 runtime 实现结果。
- [validation/pf_r5_proximity_fuze_validation_20260616.zh.md](validation/pf_r5_proximity_fuze_validation_20260616.zh.md)：
  PF-R5 聚焦矩阵验证摘要。
- [validation/pf_r5_proximity_fuze_validation_heatmaps_20260616.png](validation/pf_r5_proximity_fuze_validation_heatmaps_20260616.png)：
  no-load-aware 起爆概率、探测置信度和 mechanism coverage 的最终热图。

## 验收门

只有满足以下条件后，本子项目才可标为 accepted：

- 公开资料机制声明以高层、无参数、非权威证据准入；任何会暗示真实武器参数的 claim 均被拒绝。
- 当前 runtime gap audit 明确指出哪些 proxy 行为要替换，哪些保留。
- 后续 surrogate contract 保留事件解释性，不把引信行为压缩到 reward、terminal status 或单一 health 标量。
- 聚焦测试覆盖 no-terminal-track、outside-sensor-window、detection but no trigger、trigger with delay、
  blast-fragmentation coverage、continuous-rod coverage 和 no-detonation no-load。
- PF-R5 矩阵证据以最终 CSV、JSON、一张热图和摘要保留；不要求额外中间制品。
- 父 A2 文档继续拒绝 stock authority、Pk、deterministic fuze 和具体弹种击毁结论。

## 残余和下一步

- 公开资料只能支持机制结构，不能支持真实引信常数。
- 目标表面/几何距离可以为后续 surrogate 提供输入，但默认 runtime 替换需要单独验收。
- 轨迹随机性、导引头/天气/环境不确定性，以及飞行员/控制权限后果，是相邻包，不属于第一轮近炸引信切片。
- PF-R5 已确认 surrogate 在触发半径、初始横向/高度偏置和机制族上的趋势，但 live guidance 会把实际最近距离压在较窄区间，并让初始偏置对称性成为残余。
- 真实引信阈值、Pk、deterministic fuze authority 或具体弹种杀伤声明仍被拒绝。

## Archive

归档索引：[archive/README.zh.md](archive/README.zh.md)。当前还没有历史记录进入 archive。
