# 联合任务域

Language: [English canonical](README.md); Chinese companion.

Document kind: `reference`
Lifecycle: `maintained`
Canonical: `docs/domains/joint/README.md`
Owner: `domains/joint`
Last verified: `2026-08-07`

联合 owner 定义必须在空中、海上和地面工作中保持相同含义的跨域授权关系、
任务组织词汇以及意图/命令/汇报接口。它不拥有军种条令，也不拥有任何领域的
执行几何、时序、控制、感知或武器语义。

## 当前权威

- [联合指挥与建模基线](standards/command_and_modeling_baseline.zh.md)：
  定义 common core 的命名、授权和建模边界。
- [联合命令链与汇报基线](standards/command_link_and_reporting_baseline.zh.md)：
  定义最小命令投递、汇报、数据链和 ROE 闭环。

## Owner 边界

- Joint 拥有跨军种仍成立的关系和共享合同形状。
- Service profile 负责解释某个军种如何使用这些共享对象。
- Air、naval 和 ground owner 分别定义自身的平台与任务执行语义。
- `wingman`、`runway`、`destroyer screen` 和 `platoon wedge` 等词不得提升为
  Joint common core 概念。

## 待迁移 Owner

Service profile 和领域特化标准在各自迁移切片落地前，仍位于当前维护中的
legacy 路径：

- [军种 Profile](../../standards/services/README.zh.md)
- [空中特化](../../standards/air/README.zh.md)
- [海上特化](../../standards/naval/README.zh.md)
- [地面特化](../../standards/ground/README.zh.md)

这些链接只是迁移期路由，并不表示 Joint 拥有所链接的执行语义。

## 参考依据

- [Joint Chiefs service publications](https://www.jcs.mil/Doctrine/Service-Publications/)
- [CJCSM 3150.13C, Joint Reporting Structure](https://www.jcs.mil/Portals/36/Documents/Library/Manuals/m315013.pdf)
