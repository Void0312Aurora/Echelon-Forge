# `src/models/domains` 边界

`models/domains` 持有具体域专属的可替换模型实现、adapter 与显式 placeholder route。新增域 model owner 应放到这里，而不是继续摊到 `models/` 根目录。

## 布局

- `air/`：航空控制模型与 air-owned default effects helper。
- `naval/`：naval model adapter 与显式 naval placeholder effects route。
- `ground/`：ground placeholder effects route，以及防止 ground 概念藏进 generic model 文件的 owner-shell helper。

## 依赖方向

域 model 可以依赖 component 数据与 `core/interfaces` contract。它们不得注册 ECS system，不拥有 runtime/facade 行为，也不得依赖 binding 或训练配置。
