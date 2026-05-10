# `src/core/interfaces` 边界

`core/interfaces` 保存 C++ 模型接口和跨 core 的抽象 contract。它定义系统和模型之间的边界，不提供默认实现。

## 允许

- control、sensor、environment、effects、guidance 等模型接口。
- unit data、unit factory、observation 等跨层 contract。
- 小型纯虚接口或稳定值类型。

## 禁止

- 默认模型实现。
- ECS system registration。
- runtime owner、facade 或 Python binding。
- GPU backend 选择逻辑。

## 迁移备注

默认实现放在 `models/`。当新增模型能力需要跨系统复用时，先在本目录定义 contract，再在 `models/` 提供实现。
