<!-- Machine-translated draft generated on 2026-05-18 from docs/standards/services/air_force.md. Review before treating this file as authoritative. -->

# USAF 概况

本文档定义项目在空战/空中行动建模时采用的 USAF 概况。

## 1. 官方现实基础

USAF 官方 `AFDP 3-0.1，指挥与控制` 明确把空中力量 C2 放在空中组成部队指挥官
框架下处理，并强调：

- 空中组成部队指挥官同时可能担任 `COMAFFOR` 与 `JFACC`
- `OPCON` 与 `TACON` 的具体委托由 JFC 决定
- USAF 采用 `集中指挥 - 分布式控制 - 分散执行`

官方来源：

- [AFDP 3-0.1，指挥与控制](https://www.doctrine.af.mil/Portals/61/documents/AFDP_3-0_1/AFDP3-0.1CommandandControl.pdf)

## 2. 建模结论

### 2.1 不应进入紧循环运行时的层

- 空中组成部队指挥官
- AOC
- 联队 / MAJCOM / NAF 等行政或战区级结构

这些层级适合作为：

- 想定编写
- 任务授权
- 战役 / 行动元数据

### 2.2 应进入紧循环运行时的层

对于当前项目，空战紧循环运行时更适合放在架次级战术单位：

- 任务包
- 飞行
- 编组
- 飞机

说明：

- 这是项目建模上的归纳，不是声称 AFDP 逐字规定了所有架次细部结构。
- 其依据是 USAF 官方条令对空中组成部队指挥官、下属梯队、分布式控制、
  联队级及中间梯队授权的描述。

## 3. 对项目的直接约束

空战概况下可以使用：

- 巡逻
- 拦截
- 护航
- 回收

并在空中专业化中再细分为：

- `CAP`
- `BARCAP`
- `TARCAP`
- `RTB`
- 着陆 / 进近

也就是说：

- `CAP` 不应是联合/核心层原生任务族
- `CAP` 应是空中概况对巡逻的具体化

## 4. 组织层级建议

当前项目若以 USAF 空中战术概况为主，可先采用：

- 任务包
- 飞行
- 编组
- 飞机

并进一步区分：

- 指挥/战术角色
- 执行/平台角色

这样既符合现实，又便于后续扩到双机、四机与多任务包。

## 5. 对应的平台专用标准

本概况下的空中/平台细化标准当前放在：

- [Air 平台专用标准总览](../air/README.md)
- [飞行员观察空间标准](../air/obs.md)
- [飞行员行动空间标准](../air/act.md)
- [任务指挥标准](../air/aim.md)
- [飞行员报告标准](../air/rep.md)
