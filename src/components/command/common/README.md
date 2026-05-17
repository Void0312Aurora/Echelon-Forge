# `src/components/command/common` 边界

`components/command/common` 保存跨域共享的 command 基础结构。这里放的是
“多个执行域都可能复用的命令壳、传输语义和共享字段”，而不是当前 air
执行面特有的控制或回收语义。

## 允许

- `MissionCommand` 的共享 core 字段。
- 通信/消息层会复用的 command 级公共枚举或值类型。
- 不绑定特定平台的 command payload 壳。

## 禁止

- runway、approach、takeoff、formation 这类明显 air-specific 字段。
- `TaskOrder`、`LeaderIntent`、`PilotReport` 等 tasking/C2 DTO。
- 命令投递、延迟、生效时机的 tick 逻辑；这些属于 `systems/`。
- Python binding 或 facade 适配逻辑。

## 当前文件

- [mission_command_core.h](mission_command_core.h)
  - `MissionCommand` 的共享 core 语义。
- [comm_message.h](comm_message.h)
  - 共享通信消息类型。

## 依赖方向

本目录只能依赖更底层的值类型与 component 头。`air/` 或未来的 `naval/`
扩展层可以组合这里的 core 结构；这里不应反向依赖具体域。
