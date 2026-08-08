# Naval 任务域

Language:
- English canonical: [README.md](README.md)
- Chinese companion: `README.zh.md`

Document kind: `reference`
Lifecycle: `maintained`
Canonical: `docs/domains/naval/README.md`
Owner: `domains/naval`
Last verified: `2026-08-08`

状态：naval 执行语义的维护中 owner 入口。

本目录拥有当前 naval 执行合同：海上 screen/support 行为、station 几何、
recovery 行为、naval command 与 observation 特化，以及用于锚定这些工作的舰艇
单位参考。它不拥有共享 Joint schema，也不拥有该 schema 的 Navy 军种解释。

## 维护中的权威文档

这些 owner-local 文档应配套阅读：

1. [海军最小任务结构](standards/minimal_task_structure.zh.md)
2. [海军观测合同](standards/observation_contract.zh.md)
3. [舰艇单位参考基准](reference/ship_unit_references.zh.md)

前两份文档是规范性标准。舰艇单位页面是维护中的参考基线，不定义任务语义。

## 所有权边界

[Navy service profile](../joint/service_profiles/standards/navy_profile.zh.md)
负责解释 Joint common-core 字段在 Navy 组织与权限中的含义。它拥有以下军种层
语义：

- `task_group` 与 `task_unit`
- `warfare_role_code`
- `officer_in_tactical_command`
- Navy 特定的任务封装与权限锚点

本 Naval 任务域拥有海上单位如何执行该解释的语义：

- `screen`、`support`、`station` 与 `recover` 行为
- 舰艇与编队控制语义
- screen/station 观测几何与汇报状态
- naval command、tasking 与 execution 特化

Joint common core 继续拥有军种无关的 carrier 形状，包括
`service_profile`、`task_family`、`command_relationship`、
`authority_scope`、`coordination_mode`、`tactical_unit_type` 与共享标识符。
Naval 可以约束这些形状在海上执行中的使用方式，但不重新定义其跨军种 schema。

## 当前实现边界

仓库当前提供的是维护中且范围受限的 naval surface，而不是完整舰队仿真：

- naval tasking 与 command DTO 扩展
- `naval_screen_station_v1`：固定 23 字段的 mission-observation mode
- screen、support、patrol 与 recover family 的 task/profile 映射
- contact、assignment、reporting、ROE 与 station/screen 执行输入
- 初始舰艇与 naval weapon-system 配置基线

这些 surface 不构成完整舰队 doctrine、完整机动与驻站控制器、海上补给行动，
也不构成权威的海军武器与伤害标定。

## 标准化规则

- 共享合同定义保留在
  [Joint 标准](../joint/standards/command_and_modeling_baseline.zh.md)。
- Navy 军种解释保留在
  [Navy service profile](../joint/service_profiles/standards/navy_profile.zh.md)。
- 海上执行与汇报语义保留在本 owner 目录。
- 先描述维护中的代码与测试合同，再单独说明拟议扩展。
- 除非 naval 接口明确消费，否则不要引入空军特有的 sortie、runway 或
  lead/wingman 语义。

## 活跃工作与相关文档

- [Naval 任务线](../../task/naval/README.zh.md)
- [Joint 指挥与建模基线](../joint/standards/command_and_modeling_baseline.zh.md)
- [Joint 指挥链路与汇报基线](../joint/standards/command_link_and_reporting_baseline.zh.md)
