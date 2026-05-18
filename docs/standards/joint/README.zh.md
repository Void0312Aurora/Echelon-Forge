<!-- Machine-translated draft generated on 2026-05-18 from docs/standards/joint/README.md. Review before treating this file as authoritative. -->

# Joint 标准总览

本目录定义项目在空、海、陆建模时共用的联合层模板。

核心原则：

- `joint` 层只定义共通的授权关系、任务组织和汇报接口
- 不在 `joint` 层直接写 `wingman`、`runway`、`destroyer screen`、`platoon wedge`
- 具体军种语义下沉到 `service profile`

## 1. 为什么必须先做 Joint 层

根据 Joint Chiefs 和各军种官方资料，美军并不存在一条完全统一的战术指挥链。

真实结构更接近：

- 联合层统一授权关系
- 军种层定义战术组织
- 平台层定义执行与物理行为

因此，项目中的通用模板应优先承载：

- `command relationship`
- `authority scope`
- `task organization`
- `intent / order / report`

## 2. 推荐阅读顺序

1. [Joint 指挥关系与建模基线](command_and_modeling_baseline.md)

## 3. 主要官方依据

- [Joint Chiefs Service Publications](https://www.jcs.mil/Doctrine/Service-Publications/)
- [CJCSM 3150.13C, Joint Reporting Structure](https://www.jcs.mil/Portals/36/Documents/Library/Manuals/m315013.pdf)

说明：

- 上述资料用于确认联合层共通关系与联合报告结构。
- 军种战术组织差异则分别在 `services/` 下处理。
