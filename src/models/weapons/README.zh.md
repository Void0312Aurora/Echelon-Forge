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

`detail/default_effects_*_detail.h` 文件是 `default_effects_model.cpp` 的私有
实现片段。namespace 级片段用于保持 helper 的本地链接，并把 `on_proximity_hit`
拆为 direct-hit、spatial-projection、system-effect、domain routing、
result-population 与 legacy/fallback 子模块。它们不是独立 API，也不是新的模型入口。
它们没有 include guard，只有在 `default_effects_model.cpp` 的匿名 namespace 内展开
才有效；使用 `.h` 后缀是为了让仓库的结构工具把它们计为 C++ 源码，并把 `.inc` 留给
X-macro 字段表。

`detail/default_effects_domain_routing_detail.h` 是 Air/Naval/Ground effects
ownership 的 generic router。Air consequence handling 位于
`models/domains/air/default_effects_air_domain.h`；naval 与 ground 路径当前只是显式
placeholder owner shell，等待各自 damage fidelity 拥有 runtime owner。
