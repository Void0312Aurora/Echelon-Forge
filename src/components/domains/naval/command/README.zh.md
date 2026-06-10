# `src/components/domains/naval/command` 边界

`components/domains/naval/command` 保存舰艇/海上执行面的 command 扩展。这里承载
的是 naval-specific 的执行意图，例如舰载机发收舰、编队站位和 OTH relay
控制，而不是跨域共享 command core。

当前 slice 是维护中的，但范围刻意收窄：它提供 `MissionCommandNaval`
字段与 command code，供 naval system 和 contract 使用。它本身不表示完整
naval mission runtime、N4 stack 或战役级 maritime C2 model 已经存在。

## 允许

- `MissionCommandNaval` 这类 naval 扩展字段。
- 仅服务舰艇/海上执行面的 command code 常量与轻量 helper。
- 可被 `systems/domains/naval` 和 `core/mission` 消费的 naval execution DTO。

## 禁止

- 跨域共享 command transport/core；这些进入 `common/`。
- `TaskOrder`、`LeaderIntent`、`PilotReport` 等 tasking DTO。
- 舰艇运动、舰载机调度、数据链时序等 tick 逻辑；这些属于 `systems/domains/naval` 或 `systems/systems`。
- Python binding、facade request/result 或 env glue。

## 当前文件

- [mission_command_naval.h](mission_command_naval.h)
  - 舰载机发收舰、OTH relay、站位半径/方位等 naval 扩展字段与 command code。

## Held 范围

- 完整 naval mission/task 编排不归本目录所有。
- contact evidence、launch request/event 和 damage diagnostics 通过 runtime engagement contract 导出，而不是由这里持有。
- 不应把 ground 或 amphibious command 语义作为捷径加入本目录。

## 依赖方向

本目录可以依赖 `components/command/common`。它不应依赖 `systems/`、
`core/mission`、`runtime/facade` 或 `interfaces/python` 的实现细节。
