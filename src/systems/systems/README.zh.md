# `src/systems/systems` 边界

本目录是平台系统 runtime 的历史目录，包含 command link、data link、EW、navigation、sensor、sonar、track manager、logistics 等系统逻辑。目录名较宽，后续应重命名，但在冻结前不做行为性移动。

当前 platform-system runtime 支持 air/naval contact 与通信 flow，但不提供 full ground sensing、fires 或 land C2 runtime。

## 允许

- 平台系统的 Flecs tick/update 逻辑。
- 对 `components/systems` 中状态组件的读写。
- 与 sensor/data-link/track-management 模型有关的 per-frame 状态推进。
- 在仍属于本历史平台系统边界时，sonar/acoustic 等 naval-aware platform-system tick。

## 禁止

- 新增物理、战斗、视觉或 mission episode 逻辑。
- 定义 component 或 DTO。
- 拥有 batch runtime、facade 或 Python binding。
- split 明确前的 native ground-domain platform runtime ownership。

## 迁移备注

后续重命名候选：

- `src/systems/platform`
- `src/systems/avionics`
- `src/systems/mission_systems`

在重命名前，新增文件必须在文件名中表达具体业务域，避免继续使用泛化命名。
