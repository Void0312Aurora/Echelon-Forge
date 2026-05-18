<!-- Machine-translated draft generated on 2026-05-18 from src/components/command/air/README.md. Review before treating this file as authoritative. -->

# `src/components/command/air` 边界

`components/command/air` 保存当前航空执行面的 command 扩展。这里承载的是
air-specific 的命令语义，例如航路、回收、跑道和低层控制输入解析。

## 允许

- `MissionCommandAir` 这类航空执行面扩展字段。
- 当前 air runtime 复用的 command 解释辅助类型。
- `PilotAction -> legacy command` 解析中确实属于 air surface 的轻量 helper。

## 禁止

- 跨域共享 command core；这些进入 `common/`。
- `TaskOrder`、`LeaderIntent`、`PilotReport` 等 tasking DTO。
- 控制律、物理积分、mission transition 或 reward 逻辑。
- Python binding、facade request/result。

## 当前文件

- [mission_command_air.h](mission_command_air.h)
  - 航路、回收、起降等 air 扩展字段。
- [control_input_resolution.h](control_input_resolution.h)
  - air 低层控制输入解析 helper。

## 依赖方向

本目录可以依赖 `components/command/common`。它不应依赖 `systems/`、
`core/mission` 或 `interfaces/python`。
