# USAF Profile

本文档定义项目在空战/空中行动建模时采用的 USAF profile。

## 1. 官方现实基础

USAF 官方 `AFDP 3-0.1, Command and Control` 明确把空中力量 C2 放在 air component commander
框架下处理，并强调：

- air component commander 同时可能担任 `COMAFFOR` 与 `JFACC`
- `OPCON` 与 `TACON` 的具体委托由 JFC 决定
- USAF 采用 `Centralized Command - Distributed Control - Decentralized Execution`

官方来源：

- [AFDP 3-0.1, Command and Control](https://www.doctrine.af.mil/Portals/61/documents/AFDP_3-0_1/AFDP3-0.1CommandandControl.pdf)

## 2. 建模结论

### 2.1 不应进入 tight-loop runtime 的层

- air component commander
- AOC
- wing / MAJCOM / NAF 等行政或 theater-level 结构

这些层级适合作为：

- scenario authoring
- tasking authority
- campaign / operation metadata

### 2.2 应进入 tight-loop runtime 的层

对于当前项目，空战 tight-loop runtime 更适合放在 sortie 级 tactical unit：

- `mission package`
- `flight`
- `element`
- `aircraft`

说明：

- 这是项目建模上的归纳，不是声称 AFDP 逐字规定了所有 sortie 细部结构。
- 其依据是 USAF 官方 doctrine 对 air component commander、subordinate echelon、distributed control、
  wing-level 及中间 echelon 授权的描述。

## 3. 对项目的直接约束

空战 profile 下可以使用：

- `patrol`
- `intercept`
- `escort`
- `recover`

并在 air specialization 中再细分为：

- `CAP`
- `BARCAP`
- `TARCAP`
- `RTB`
- `landing / approach`

也就是说：

- `CAP` 不应是 joint/core 层原生任务族
- `CAP` 应是 air profile 对 `patrol` 的具体化

## 4. 组织层级建议

当前项目若以 USAF air tactical profile 为主，可先采用：

- `package`
- `flight`
- `element`
- `aircraft`

并进一步区分：

- command/tactical role
- execution/platform role

这样既符合现实，又便于后续扩到双机、四机与多 package。

## 5. 对应的平台专用标准

本 profile 下的 air/platform 细化标准当前放在：

- [Air 平台专用标准总览](../air/README.md)
- [Pilot Observation Space Standard](../air/obs.md)
- [Pilot Action Space Standard](../air/act.md)
- [Mission Command Standard](../air/aim.md)
- [Pilot Reporting Standard](../air/rep.md)
