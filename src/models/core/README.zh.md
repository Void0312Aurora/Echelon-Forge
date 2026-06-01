# `src/models/core` 边界

`models/core` 保存基础模型实现，例如 unit factory 默认实现。

default unit factory 现在在 content/materialization 边界具备 multi-domain
awareness：它可以挂载 naval platform/stores/weapon component，并为早期
ground-aware unit 产出 typed setup capability evidence。ground mobility
当前记录为 deferred flat mobility evidence，不是完整 land movement model。

## 允许

- 默认 unit factory。
- 对 `content/` unit definition 的转换和实例化辅助。
- 从 content definition 派生的 platform capability bundle 与 resolved-spawn evidence。

## 禁止

- world lifecycle ownership。
- ECS system registration。
- Python binding 或 facade。
- native ground movement/sensing/fires/damage runtime 或维护中的 ground tasking schema。

## 迁移备注

实例化流程的 owner 仍应在 `core/engine`；本目录只提供模型实现和工厂策略。
