# A9 高保真武器系统

状态：`2026-06-16` **accepted_with_residuals**。23 集群通过，5 推迟。详见英文 README 和验收文档。

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

本子项目将六个空战武器子系统从**工程代理保真度向研究级保真度升级**，严格保持**非权威性**和**非武器特定性**：

- **G1 — APN 制导**: 增广比例导引，含可配导航比、目标加速度前馈项、低通滤波加速度估计器（τ=0.30s）。
- **G2 — 卡尔曼滤波导引头**: 9 状态 Singer 模型 EKF（世界笛卡尔坐标系 + 机体↔世界转换）；通过 `use_kalman_seeker` 在 MissileTuning/JSON/Python 中可配。
- **G3 — 可配阶数自动驾驶仪**: order=1（传统一阶滞后）、order=2（状态空间滤波器）、order=3（状态空间 + 执行器滞后 τ=0.03s）；阻尼 ζ 可配。
- **G4 — 引信代理细化**: `hit_to_kill` 覆盖惩罚；`FuzeProfile.coverage_profile` 字段；PF-R4 代理保留。
- **G5 — 马赫相关气动**: 可配跨音速断点；功率飞行减阻（`cd0_power_on_ratio`，默认 0.90）。
- **G6 — 基于物理的战斗部**（opt-in）: Gurney 破片速度、大气衰减、连续杆焊接上限（1,150 m/s）、切割阈值（610 m/s）；配置 `gurney_constant_mps` + `explosive_mass_kg` + `case_mass_kg` 时激活。传统经验公式保留为默认。

完整杀伤链事件面保留，所有权限声明拒绝。详见英文 [README.md](README.md)。

## 当前状态

| 子系统 | 状态 |
|--------|------|
| G1 — APN 制导 | **pass** |
| G2 — 卡尔曼导引头 | **pass** |
| G3 — 自动驾驶仪 | **pass** |
| G4 — 近炸引信 | **pass** |
| G5 — 气动 | **pass** |
| G6 — 战斗部 | **pass** |
| G7 — 集成 | **pass** |
| A2 权限 | 保留/封存 |

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

| 阶段 | 状态 |
|------|------|
| P0 边界 | pass |
| P1 证据 | pass (P1-A); P1-B/C deferred |
| P2 实现 | pass (14/14) |
| P3 集成 | pass |
| P4 验证 | pass (P4-A/B); P4-C deferred |
| P5 闭合 | pass |

## 文档索引

- [验收文档](a9_high_fidelity_weapon_system_acceptance_20260616.md)
- [当前状态](a9_high_fidelity_weapon_system_current_status_20260616.md)
- [派发队列](a9_high_fidelity_weapon_system_dispatch_queue_20260616.md)
- [任务集群](a9_high_fidelity_weapon_system_task_clusters_20260616.md)
- [来源账本](p1_evidence/source_ledger_20260616.md)
- [差距审计](p1_evidence/p0b_gap_audit_summary_20260616.md)
- [P4-A 几何扫描](p4_validation/p4a_apn_geometry_sweep_20260616.py)
- [P4-B 灵敏度扫描](p4_validation/p4b_sensitivity_sweep_20260616.py)
- [P3-C 调优示例](p3_integration/p3c_a9_tuning_example.py)

## 残差

| ID | 描述 | 严重度 |
|----|------|--------|
| R2 | EKF 跟踪性能未定量验证 | 中 |
| R4 | 马赫 Cd₀ 多行表推迟（当前为单次 lerp） | 低 |

已关闭: R1 (APN 滤波器), R3 (autopilot order=3), R5 (Gurney), 破片衰减。
所有权限声明 (`pk_authority` 等) 保持拒绝。

## 存档

存档证据包: [archive/a9_high_fidelity_weapon_system_accepted_with_residuals_20260616/](archive/a9_high_fidelity_weapon_system_accepted_with_residuals_20260616/README.md)
