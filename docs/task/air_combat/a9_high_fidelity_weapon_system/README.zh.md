# A9 高保真武器系统

状态：`2026-06-16` planning / P0 边界冻结。尚未开始实现。

语言：

- English canonical: [README.md](README.md)
- 中文对照: `README.zh.md`

输入：

- 父级空战任务索引: [../README.md](../README.md)
- A2 封存毁伤模型记录: [../archive/a2_high_fidelity_damage_model/README.md](../archive/a2_high_fidelity_damage_model/README.md)
- A2 后续近炸引信真实性（PF-R4 通过，PF-R5 带残差通过）:
  [../a2_high_fidelity_damage_model/missile_lethality_proximity_fuze_realism/README.md](../a2_high_fidelity_damage_model/missile_lethality_proximity_fuze_realism/README.md)
- A8 毁伤效果链条: [../archive/a8_damage_effect_chain/README.md](../archive/a8_damage_effect_chain/README.md)
- Agent 子项目标准: [../../../agent/rules/subproject_creation_standard.zh.md](../../../agent/rules/subproject_creation_standard.zh.md)
- 真实性权限边界: [../../../standards/foundation/realism_authority_boundary.zh.md](../../../standards/foundation/realism_authority_boundary.zh.md)
- 公开数据源准入: [../../../standards/foundation/public_data_source_admission.zh.md](../../../standards/foundation/public_data_source_admission.zh.md)
- 杀伤链合同（C++）: [../../../../src/runtime/contracts/engagement_contracts.h](../../../../src/runtime/contracts/engagement_contracts.h)
- 杀伤链合同（Python）: [../../../../tools/diagnostics/lethality_chain_contract.py](../../../../tools/diagnostics/lethality_chain_contract.py)
- 交战事件类型: [../../../../src/core/engine/engagement_event_types.h](../../../../src/core/engine/engagement_event_types.h)

## 目的

当前空战武器系统在大多数子系统上处于**工程代理保真度**水平。制导律为经典比例导引（PN）加经验终端捕获增强项，导引头使用一阶指数平滑滤波器，自动驾驶仪为单一阶滞后环节，气动模型使用固定阻力系数。近炸引信代理（PF-R4/PF-R5）已从纯最近距离门控升级为传感器探测机会/检测/触发分层模型，但仍保持非权威性。

本子项目**计划**将每个剩余代理子系统**向研究级保真度方向升级**，同时严格保持**非权威性**和**非武器特定性**：

- **制导 (G1)**: 计划从经典 PN 升级为增广比例导引（APN），加入基于最优控制/ZEM 推导的目标机动补偿项。
- **导引头/跟踪器 (G2)**: 计划用 9 状态扩展卡尔曼滤波器（笛卡尔坐标系下的相对位置、速度、加速度，使用 Singer 模型过程噪声）替代一阶指数平滑。
- **自动驾驶仪 (G3)**: 计划用三环（速率/稳定/加速度）拓扑参数化自动驾驶仪替代单一阶滞后，参数由闭环时间常数 τ 和阻尼 ζ 描述。
- **近炸引信 (G4)**: 在已完成的 PF-R4 代理基础上细化（当前状态 `pass`），添加机构特定的覆盖区分和额外诊断字段。PF-R5 矩阵验证状态为 `pass_with_residuals`；G4 不得退行或扩大这些残差。
- **战斗部杀伤力 (G6)**: 计划用基于物理的 Gurney 破片速度、大气衰减和定向效率因子细化爆破碎片和连续杆模型。
- **气动 (G5)**: 计划用与马赫数相关的阻力系数查找表和功率开/关底座阻力区分替代固定 Cd₀ 参数，并加入正确的诱导阻力公式。

每次计划升级必须保留 `RecentEngagementEvents` 定义的完整杀伤链事件面（参见
[engagement_event_types.h](../../../../src/core/engine/engagement_event_types.h)）：
`NearestApproachEvent`、`FuzeEvaluationEvent`、`WarheadMechanismEvent`、
`SpatialCoverageEvent`、`ComponentLoadEvent`、`ComponentDamageEvent`、
`PlatformConsequenceEvent`、`StructuralBreakupEvent`、
`LifecycleTransitionEvent`、`TrainingProjectionEvent`。任何升级子系统均不声明
`pk_authority`、`deterministic_fuze_authority`、`effect_scale_authority` 或库存武器真值。

## 当前状态

| 区域 | 状态 | 证据 | 边界 |
|------|------|------|------|
| A2 权限 | 保留/封存 | A2 封存档 | A2 仍为非权威性的库存武器真值、Pk 和确定性引信 |
| 经典 PN 制导 | 已实现/代理 | default_guidance_model.cpp:700-725 | PN + 经验捕获项；无目标机动补偿 |
| 一阶导引头滤波 | 已实现/代理 | missile_guidance_math.h:70-84 | α-β 级别平滑；无协方差传播，无加速度状态 |
| 单环自动驾驶仪 | 已实现/代理 | default_guidance_model.cpp:740-744 | 一阶滞后 τ=0.12s；无速率/稳定内环 |
| PF-R4 引信代理 | **已实现/通过** | PF-R4 实现文档；触及 C++、Python 绑定、测试和诊断共 13 个文件 | 代理为非权威性可解释性切片，非真实引信校准 |
| PF-R5 引信验证 | **带残差通过** | PF-R5 验证文档；CSV、JSON、热图已保留 | 仅验证代理门控趋势；实际制导偏移非纯起爆点对称性测试 |
| A9 G4 引信细化范围 | 计划中 | 本 README；任务集群 P2-D | G4 细化现有代理（机构覆盖区分、额外诊断）；不重新实现 PF-R3 |
| 固定 Cd 气动 | 已实现/代理 | missile_guidance_types.h:17-18 | 每个速度区间单一 Cd₀；无马赫表，无功率开/关区分 |
| 爆破碎片战斗部 | 已实现/候选 | default_effects_warhead_detail.inc | Kingery-Bulmash 代理；质量/半径为玩具输入 |
| 连续杆战斗部 | 已实现/候选 | MLF-4 证据包 | 杆切割带已建模；未校准 |
| 网络调研来源账本 | 已收集/非权威 | [p1_evidence/source_ledger_20260616.md](p1_evidence/source_ledger_20260616.md) | 仅公开来源；无涉密/ITAR 参数 |

## 范围

范围内：

- **G1 — APN 制导**: 实现带目标加速度前馈的增广比例导引。从最优控制/ZEM 推导出发。添加可配置导航比 N' 和目标加速度增益参数。
- **G2 — 卡尔曼滤波导引头**: 实现 9 状态 EKF 跟踪器，使用 Singer 模型过程噪声。当 `use_kalman_seeker = true` 时替代一阶平滑；保留现有平滑为回退模式。
- **G3 — 三环自动驾驶仪**: 以可配置的二阶或三阶传递函数建模速率/稳定/加速度拓扑，参数由 τ 和 ζ 描述。保留 G 限制和速率饱和。
- **G4 — 引信代理细化**: 在已完成的 PF-R4 代理基础上构建。添加 `blast_fragmentation` 和 `continuous_rod` 之间的机构特定覆盖区分。添加 P0-B 差距审计中发现的任何缺失诊断字段。不得退行 PF-R5 验证残差。
- **G5 — 马赫相关气动**: 用马赫索引查找表替代固定 Cd₀，增加功率开/关底座阻力区分，以及正确的诱导阻力公式 k(M)·CL²。
- **G6 — 基于物理的战斗部细化**: 增加 Gurney 破片速度、大气破片衰减、定向破片效率因子，以及带焊接限制速度上限的连续杆展开运动学。
- **G7 — 集成与诊断**: 将所有升级接入现有 `MissileTuning` 结构体、制导/毁伤系统、Python 绑定、场景配置和诊断探测器。

范围外：

- 声明 `pk_authority`、`deterministic_fuze_authority` 或库存武器真值。
- AIM-120C 特定的涉密参数、ITAR 受限数据或真实引信常数。
- 海军或地面领域武器效果（仅空战）。
- 目标机动预测（IMM 滤波器组、自适应滤波）——推迟至未来。
- ECM/EW 对导引头或引信性能的影响——推迟至未来。
- 实时硬件在环约束。
- 训练奖励重新设计。
- 重新打开已封存的 A2、MLF-2、MLF-3、MLF-4 或 MLF-5 包。
- 从零开始重新实现 PF-R3（PF-R4/PF-R5 已完成）。

## 阶段计划

| 阶段 | 目标 | 进入条件 | 退出条件 | 状态 |
|------|------|---------|---------|------|
| `P0 边界` | 冻结范围、权限和非目标。链接父文档。对齐 PF 基线与 PF-R4/PF-R5 已完成状态。 | 用户请求高保真武器子项目。 | README、任务集群、当前状态、派发队列、验收草案、来源账本和存档边界存在。父 README 链接 a9。PF 状态正确反映 PF-R4 通过/PF-R5 带残差通过。 | active |
| `P1 证据` | 完成逐子系统差距审计和基准参数表。收集网络调研来源账本。映射现有测试覆盖。 | P0 存在且 PF 基线已对齐。 | 6 份差距审计、基准参数表、测试覆盖图和来源账本已记录。 | planned |
| `P2 实现` | 在 C++ 模型和 ECS 组件中实现 G1-G6 升级。 | P1 证据存在。每个子系统门控审查通过。 | 所有六个模型升级编译通过、通过聚焦单元测试，并保留现有合同测试。G4 不退行 PF-R5 残差。 | planned |
| `P3 集成` | 将升级接入 MissileTuning、Python 绑定、场景 JSON 和诊断探测器。 | P2 通过每个子系统门控。 | 集成测试通过；现有空战场景冒烟测试绿色。 | planned |
| `P4 验证` | 运行矩阵验证：交战几何扫描、子系统参数灵敏度、与代理基线的比较。 | P3 集成测试通过。 | 验证矩阵产物（CSV、热图、摘要）保留。残差记录。 | planned |
| `P5 闭合` | 同步父文档、验收门控、残差登记和存档。 | P4 验证完成并带残差。 | 验收闭合记录最终代理边界。父 README 更新。 | planned |

## 任务集群

- 任务集群计划: [a9_high_fidelity_weapon_system_task_clusters_20260616.md](a9_high_fidelity_weapon_system_task_clusters_20260616.md)
- 当前状态: [a9_high_fidelity_weapon_system_current_status_20260616.md](a9_high_fidelity_weapon_system_current_status_20260616.md)
- 派发队列: [a9_high_fidelity_weapon_system_dispatch_queue_20260616.md](a9_high_fidelity_weapon_system_dispatch_queue_20260616.md)
- 验收草案: [a9_high_fidelity_weapon_system_acceptance_20260616.md](a9_high_fidelity_weapon_system_acceptance_20260616.md)

## 产出与证据

当前产出（P0）：

- 本 README 和英文规范版。
- [来源账本](p1_evidence/source_ledger_20260616.md)：所有 6 个子系统的公开来源参数表，含 URL、检索日期和非权威准入注释。
- [任务集群](a9_high_fidelity_weapon_system_task_clusters_20260616.md)：6 个阶段共 28 个集群（2 P0 + 3 P1 + 14 P2 + 4 P3 + 3 P4 + 2 P5）。
- [当前状态](a9_high_fidelity_weapon_system_current_status_20260616.md)：成熟度矩阵、证据链接、残差登记表。
- [派发队列](a9_high_fidelity_weapon_system_dispatch_queue_20260616.md)：工作包状态和串行化约束。
- [验收草案](a9_high_fidelity_weapon_system_acceptance_20260616.md)：逐子系统检查清单及禁止声明断言。

计划产出（P1-P5）：

- 逐子系统当前运行时差距审计（6 份审计：制导、导引头、自动驾驶仪、引信细化、气动、战斗部）。
- 代理值→目标值映射的基准参数表。
- 带差距优先级排序的测试覆盖图。
- 带聚焦单元测试的 G1-G6 C++ 模型实现。
- 含新可配置参数的更新 `MissileTuning` 结构体。
- 暴露新调优参数和运行时诊断的更新 Python 绑定。
- 使用新保真度参数的示例场景配置。
- 验证矩阵产物。

## 验收门控

本子项目仅在以下条件全部满足时方可标记为 `accepted`：

- 所有六个 G1-G6 模型升级编译通过并通过聚焦子系统测试。
- G4 不退行 PF-R4 代理行为或扩大 PF-R5 验证残差。
- 现有制导真实性测试继续通过或附带记录的理由更新。
- 完整杀伤链事件面（`NearestApproachEvent`、`FuzeEvaluationEvent`、
  `WarheadMechanismEvent`、`SpatialCoverageEvent`、`ComponentLoadEvent`、
  `ComponentDamageEvent`、`PlatformConsequenceEvent`、`StructuralBreakupEvent`、
  `LifecycleTransitionEvent`、`TrainingProjectionEvent`）得以保留，每种事件类型保持可观测。
- APN 制导对机动目标的脱靶量可证明地小于经典 PN 基线。
- 卡尔曼滤波跟踪器相比一阶平滑基线展示改善的跟踪连续性和协方差收敛。
- 引信代理已输出 PF-R4 诊断字段；G4 细化添加机构特定覆盖区分。
- 马赫相关气动表在亚音速-跨音速-超音速包络内产生物理上合理的速度剖面。
- 战斗部破片速度遵循 Gurney 方程，连续杆速度在焊接限制阈值处截断。
- 验证矩阵产物已保留。
- 父级 A2 和空战文档继续拒绝 `pk_authority`、`deterministic_fuze_authority` 和库存武器真值。
- 所有公开来源数据在来源账本中标注来源 URL、检索日期和非权威准入声明。

详细验收检查清单见：[a9_high_fidelity_weapon_system_acceptance_20260616.md](a9_high_fidelity_weapon_system_acceptance_20260616.md)。

## 残差与后续步骤

预期残差：

- **目标机动预测**: IMM/CV/CA/CT 滤波器组——推迟。
- **ECM/EW 交互**: 干扰下的性能退化——推迟。
- **定向战斗部瞄准点优化**: PIOS 式 3D 破片引导——推迟。
- **实时性能**: 卡尔曼滤波器和三环自动驾驶仪的 CPU 成本——推迟至集成基准测试后。
- **海军/地面领域**: 仅空战——推迟。
- **权限提升**: 所有升级保持研究级和非权威性。

## 存档

存档索引: [archive/README.md](archive/README.md)。尚无历史记录存档。
