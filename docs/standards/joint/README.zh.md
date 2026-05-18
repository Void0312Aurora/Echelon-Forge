# 联合标准总览

Language:
- English canonical: `README.md`
- Chinese companion: [README.zh.md](README.zh.md)

状态：`2026-05-18`，联合层标准入口。

本目录定义项目在空、海、陆建模中共享的联合层模板。

核心原则：

- `joint` 层只定义共享的授权关系、任务组织和汇报接口
- 不在 `joint` 层直接写 `wingman`、`runway`、`destroyer screen`、`platoon wedge`
- 具体军种语义下沉到 `service profile`

## 1. 为什么必须先定义 Joint 层

根据 Joint Chiefs 与各军种公开资料，美军并不存在一条完全统一的战术指挥链。

更接近现实的结构是：

- 联合层统一 authority relationships
- 军种层定义 tactical organization
- 平台层定义 execution 与 physical behavior

因此，项目中的通用模板应优先承载：

- `command relationship`
- `authority scope`
- `task organization`
- `intent / order / report`

## 2. 推荐阅读顺序

1. [联合指挥与建模基线](command_and_modeling_baseline.md)
2. [联合命令链与汇报基线](command_link_and_reporting_baseline.md)

## 3. 主要官方参考

- [Joint Chiefs Service Publications](https://www.jcs.mil/Doctrine/Service-Publications/)
- [CJCSM 3150.13C, Joint Reporting Structure](https://www.jcs.mil/Portals/36/Documents/Library/Manuals/m315013.pdf)

说明：

- 上述资料用于确认联合层共享的关系词汇与联合汇报结构
- 各军种在战术组织上的差异，继续分别放在 `services/` 下处理
