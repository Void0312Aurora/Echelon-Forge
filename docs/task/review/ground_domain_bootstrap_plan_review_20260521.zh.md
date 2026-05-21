<!-- Machine-translated draft generated on 2026-05-21 from docs/task/review/ground_domain_bootstrap_plan_review_20260521.md. Review before treating this file as authoritative. -->

# 地面域引导计划——架构批准

状态：`2026-05-21` 计划已审核；批准，附带五个必需的 G0 补充项。
来源：[ground_domain_bootstrap_plan_20260521.md](../task/ground/ground_domain_bootstrap_plan_20260521.md)
权威依据：[仿真系统架构设计](../../plan/architecture/simulation_system_architecture_design.md)

## 1. 总体评估

该计划**结构正确**。它遵循现有的 `common + specialization + profile bridge` 模式（空域/海域域已采用）。明确禁止单独的“陆军运行时堆栈”。其五阶段分解（G0 边界冻结至 G4 运行时切片）范围适当，首波有意保守——小单元分层、有限任务族、无新的物理假设。

计划已批准。然而，在 G1 合同骨架开始之前，G0 必须产生五项额外的架构承诺。这些不是实现问题——而是架构基线第 10 节要求的架构声明。

## 2. 架构对齐

| 架构要求（§10） | 计划状态 | 裁定 |
|-------------------------------|-------------|---------|
| 阶段覆盖范围——涉及哪些 P0-P10 阶段 | 未声明 | ❌ G0 必需 |
| 消费/产生的数据包——哪些数据包族 | 未声明 | ❌ G0 必需 |
| 能力族——哪些模型族被扩展 | 列为开放问题（§8.2），推迟至 G1 | ⚠️ 必须在 G0 中解决 |
| 读/写集——阶段节点声明 | 未声明 | 推迟至 G3 |
| 时钟域/延迟策略 | 未声明 | ❌ G0 必需 |
| 外观可见性规则 | 未声明 | 推迟至 G3 |
| 能力接口 | 未声明 | 推迟至 G3 |
| 对等/回归测试 | 未声明 | 推迟至 G3 |
| 现有调用者的兼容性行为 | 隐含于 §6 | 适合 G0 |
| “无私有运行时路径”（规则 10） | ✅ §2：明确禁止 | 正确 |
| 能力组合路径（规则 15） | 未声明 | ❌ G0 必需 |
| 信息状态边界（§3） | 部分（§8.6），未映射到六层模型 | ⚠️ 必须在 G0 中解决 |

## 3. 必需的 G0 补充项

G0 目前列出的输出为：“此任务线、子项目 README、计划基线、开放问题列表。”架构第 10 节要求每个域扩展文档包含十一项。对于 G0 —— 一个仅文档的冻结 —— 在 G1 开始之前必须添加以下五项。

### 补充项 1：阶段覆盖声明

声明首次地面切片参与哪些 P0-P10 阶段。

仅用于 G1 任务启动的建议：

```
P0 ContentCompile   — 将地面平台定义作为能力包
P2 TaskingIntent    — 地面任务指令、指挥官意图、指挥关系
P3 CommandDelivery   — 推迟至 G3（仅当 G1 包含时才涉及命令面）
P6 SenseTrackLink    — 推迟；地面传感受地形遮挡约束
```

### 补充项 2：数据包词汇声明

列出地面域消费和产生的现有合同族。

建议：

```
消费：  TaskingPacket（扩展了地面特定字段）
           AgentRole（地面班/排/连角色）
产生：  TaskOrder（地面任务族）
           LeaderIntent（地面指挥层级）
           PilotReport（地面单元状态）
推迟：  CommandPacket, ObservationPacket, TrackPacket
```

### 补充项 3：能力组合声明

声明地面平台将定义为能力包，而非新的硬编码类型名称分发路径。这是第三个域证明架构规则 15 (`spawn_platform({capabilities...})`) 的机会。

首波族的建议：

```
PlatformFamily: ground_vehicle_section, dismounted_unit
MotionFamily:   ground_mobility（轮式、履带式、徒步）
SensorFamily:   ground_visual, ground_acoustic（推迟至 G3+）
LauncherFamily: direct_fire_platform, indirect_fire_battery（推迟至 G3+）
DoctrineFamily: land_tactics（移动、占领、支援、掩护）
EffectsFamily:  推迟至 G3+
```

### 补充项 4：时钟域假设

地面单元的运行时间尺度与空中/海上平台根本不同。徒步班不会以 60Hz 物理频率进行机动——其指令节奏可能以秒或分钟为单位，而非毫秒。

建议：

```
基本战术时钟：1 Hz（1 秒任务评估窗口）
  — 与空中/海上 60Hz 物理基准不同
  — 嵌套触发：地面任务每 N 个基本滴答运行一次
运动更新：事件驱动或低频率（推迟至 G3+）
传感：地形遮挡，视线受限（推迟至 G3+）
```

### 补充项 5：代理图影响

地面域引入具有不同权限范围和指挥/支持关系的新代理角色，这些关系不同于空中/海上层级。

首波角色的建议：

```
ground_squad_leader      — 权限：班；信息：传感+观察；
                           行动：任务指令执行
ground_platoon_commander — 权限：排；信息：共享战术图像；
                           行动：指挥官意图，任务指令委托
ground_company_commander — 权限：连；信息：共享战术图像；
                           行动：协调意图（推迟至 G3+）
```

每个角色必须根据架构 §8 声明其五部分模式：`role`、`authority_scope`、`information_state_source`、`decision_model_ref` 和 `action_interface`。

## 4. 信息状态边界

架构第 3 节要求六层信息状态纪律。地面域引入了与空中/海上雷达/声纳链性质不同的信息退化机制（地形遮挡、视线、无线电范围）。

对于 G0，地面域应声明：

- 地面单元的 `SensedState` 默认为地形遮挡而非自由空间雷达传播。
- 地面接触的 `TrackState` 可能使用视觉/声学关联而非雷达融合。
- 地面单元的 `SharedTacticalPicture` 受无线电范围和中继拓扑约束，而非数据链路带宽。
- 这些规则在 G3+ 实现之前是占位符——但架构承诺必须在 G0 中做出。

## 5. 开放问题解决

计划第 7 节列出了六个“需在 G1 前讨论”的开放问题。为使 G0 产生有意义的语义合同，其中三个必须解决：

| 问题 | 需要解决的原因 | 建议默认值 |
|----------|----------------------|-------------------|
| 命名：`ground` vs `land` | 服务配置文件对齐，DTO 着陆点 | `ground`（匹配现有的 `air`/`naval` 并行） |
| 首个战术单元 | 任务指令粒度，层级权限范围 | 排（足够窄以进行第一次切片，足够宽以表达指挥层级） |
| 首个任务族 | DTO 字段集，任务指令词汇 | `move / occupy / support`（最少的新物理假设，可通过现有 `TaskOrder` 模式表达） |

其余三个（平台族、命令面范围、观察面）可能在 G1 中保持开放。

## 6. 决定

地面域引导计划**已批准**，但需满足上述第 3 节详细说明的五项 G0 补充项。G0 应在 G1 合同骨架开始之前关闭这些补充项。

这五项补充项并非新工作——它们是架构基线第 10 节已经要求的架构承诺。在 G0 中明确它们，能防止 G1 合同骨架建立在隐含假设之上，而这些假设在后续阶段将不得不被撤销。
