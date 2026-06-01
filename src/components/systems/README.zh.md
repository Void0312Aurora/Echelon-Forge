# `src/components/systems` 边界

`components/systems` 保存平台系统状态 component，包括通信、数据链、电子战、导航、后勤、传感器、声呐和航迹管理。

这些状态组件在 air/naval platform system 与 contact evidence 侧是 multi-domain aware。它们不定义 full ground sensing、fires、logistics 或 C2 component model。

## 允许

- comm、data link、sensor、sonar、EW、navigation、logistics、track management 状态。
- 对应 `systems/systems` tick 逻辑需要读写的数据。

## 禁止

- 平台系统的 update/tick/scan/track fusion 行为。
- mission/tasking DTO。
- Python binding、facade 或 batch runtime 逻辑。
- ownership 明确前的 native ground-domain platform-system schema。

## 迁移备注

目录名较宽，但当前代表“平台系统 component”。若后续 `systems/systems` 重命名，本目录也应一并评估是否改名为 `components/platform`。
