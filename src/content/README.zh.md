# `src/content` 边界

`content/` 保存内容 schema、unit definition 和加载器。它描述“有哪些单位和静态配置”，不拥有 runtime 行为。

content surface 是 multi-domain aware。它可以描述 air、naval 和早期
ground-aware unit definition，包括 `UnitType::Ground` 以及 typed platform
setup 消费的 capability evidence。任何 ground tasking/native-schema 引用都应保持
bootstrap evidence 口径，而不是声明 `src/content` 拥有维护中的 C++ ground
command/tasking 子域或 full ground runtime。

## 允许

- unit definition 类型。
- JSON 或其他内容格式的加载器。
- 静态内容校验和转换。
- naval platform/stores/weapon-system definition 与 ground-aware type/capability metadata。

## 禁止

- simulation step、mission episode、reward 或 termination 逻辑。
- Python binding。
- 训练配置治理。
- 直接管理 ECS world lifecycle。
- ground movement、sensing、terrain control、fires 或 damage runtime 行为。

## 依赖方向

`core/engine` 和 `models/core` 可以消费 `content/`。`content/` 不依赖 `core/engine`、`runtime/facade` 或 `interfaces/python`。
