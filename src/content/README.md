# `src/content` 边界

`content/` 保存内容 schema、unit definition 和加载器。它描述“有哪些单位和静态配置”，不拥有 runtime 行为。

## 允许

- unit definition 类型。
- JSON 或其他内容格式的加载器。
- 静态内容校验和转换。

## 禁止

- simulation step、mission episode、reward 或 termination 逻辑。
- Python binding。
- 训练配置治理。
- 直接管理 ECS world lifecycle。

## 依赖方向

`core/engine` 和 `models/core` 可以消费 `content/`。`content/` 不依赖 `core/engine`、`runtime/facade` 或 `interfaces/python`。
