# 平尾失效语义

Language:
- English canonical: `docs/architecture/standards/stabilator_failure_semantics.md`
- Chinese companion: `stabilator_failure_semantics.zh.md`

Document kind: `standard`
Lifecycle: `maintained`
Canonical: `docs/architecture/standards/stabilator_failure_semantics.md`
Owner: `architecture/air-damage`
Last verified: `2026-10-10`

飞机损伤内容将控制作动与升力面及其结构支撑分开表达。

## 运行时规则

- `*_stabilator_actuator` 是控制链路 receiver。其损坏可以通过普通飞机损伤投影降低
  控制能力，但不会直接触发 `TailLeft` 或 `TailRight` 脱离。
- `*_stabilator_surface` 是结构升力面 receiver。在维护阈值内发生结构损伤时，可以
  产生对应的尾部脱离组。
- `*_stabilator_hinge` 是结构支撑 receiver。该 receiver 存在时，结构损伤可以产生
  对应的脱离组。
- 旧版 `*_horizontal_tail_actuator_or_surface_component` 名称继续作为兼容路径。只有
  其主失效模式属于结构损伤时才允许脱离；纯液压或控制失效仍不会脱离。

当前 F-16C 示例内容使用分离后的 surface receiver 名称。该拆分修正的是语义归属，
不声称合成代理几何是权威飞机工程模型。

原生回归测试覆盖仅作动器失效的负例、结构 surface 失效的正例、旧版兼容以及 F-16C
内容加载。
