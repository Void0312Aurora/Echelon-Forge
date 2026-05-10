# `src/components/systems` 边界

`components/systems` 保存平台系统状态 component，包括通信、数据链、电子战、导航、后勤、传感器和航迹管理。

## 允许

- data link、command link、sensor、EW、navigation、logistics、track management 状态。
- 对应 `systems/systems` tick 逻辑需要读写的数据。

## 禁止

- 平台系统的 update/tick/scan/track fusion 行为。
- mission/tasking DTO。
- Python binding、facade 或 batch runtime 逻辑。

## 迁移备注

目录名较宽，但当前代表“平台系统 component”。若后续 `systems/systems` 重命名，本目录也应一并评估是否改名为 `components/platform`。
