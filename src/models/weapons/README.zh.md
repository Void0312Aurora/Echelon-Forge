# `src/models/weapons` 边界

`models/weapons` 保存武器效果、制导、命中相关默认模型实现，以及 naval weapon-mount 选择 helper。

当前维护范围仍是共享 weapon/effects model 层。naval mount helper 支持当前 naval
pre-fire 与受限 engagement-evidence 路径，但本目录不拥有完整 naval mission
runtime，也不拥有 ground fires/damage runtime。

## 允许

- effects model。
- guidance model。
- naval weapon-mount selection helper。
- 纯计算的武器行为模型。

## 禁止

- ECS system registration。
- combat component 定义。
- Python binding 或 mission episode 编排。
- 在维护中的 ground runtime 存在前，拥有 ground fires 或 ground damage model。

## 迁移备注

系统调度放在 `systems/combat`，状态放在 `components/combat`，模型实现放在本目录。
