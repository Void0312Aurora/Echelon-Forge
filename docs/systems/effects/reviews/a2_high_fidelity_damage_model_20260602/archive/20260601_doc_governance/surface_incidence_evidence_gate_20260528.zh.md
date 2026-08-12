# A2 surface-incidence evidence/row gate 进展记录 - 2026-05-28

状态：`evidence_row_gate_only / non_authoritative_lethality`。

本文记录 `surface_incidence_cos` 进入 A2 高真实度空战毁伤模型审计面的最新进展。它只代表命中点或候选组件表面的入射斜度证据，并允许 vulnerability evidence rows 用 `min_surface_incidence_cos` / `max_surface_incidence_cos` 做适用性过滤。它不是 kill authority、不是 Pk、不是 deterministic fuze、也不是 calibrated lethality authority。

## 当前语义

`surface_incidence_cos` 是一个 `[0, 1]` 范围内的 obliquity proxy：

- 接近 `1`：导弹轴与候选 hitbox/component 表面法向更接近法向入射；
- 接近 `0`：导弹轴更接近擦掠或斜入射；
- 无有效导弹轴、无有效 hitbox/component 几何或无法稳定估计表面时，事件值保持 `0`。

当前估计基于目标机体系中的局部命中点、轴对齐 hitbox/component 表面法向和导弹轴。它适合做可审计证据和 row gate，但不等价于真实接触点法线、蒙皮曲率、入射姿态、穿透角、连续杆切割角或破片云方向性模型。

## 已进入的事件面

当前 evidence 已进入以下运行时/契约表面：

- `EffectsEvent.mechanism_surface_incidence_cos`：事件级机制载荷采样的 surface-incidence 证据；
- `EffectsEvent.component_primary_mechanism_surface_incidence_cos`：主组件机制载荷中的 surface-incidence 证据；
- `ComponentMechanismLoadRow.mechanism_surface_incidence_cos`：候选组件机制载荷 row 的 surface-incidence 证据；
- Python bindings、engagement contract shape、launch adapter static shape 均已覆盖字段存在性。

这些字段与 `mechanism_fragment_energy_j`、`mechanism_fragment_areal_density_per_m2`、`mechanism_penetration_margin`、`mechanism_blast_*`、`mechanism_rod_cut_margin` 属于同一类机制载荷审计证据。它们能帮助解释为什么某个授权 row 被选中或被过滤，但不能单独决定平台是否击毁。

## Row Gate

`a2.vulnerability_evidence.v1` row 可声明：

- `min_surface_incidence_cos`
- `max_surface_incidence_cos`

只有在 descriptor 已通过非 synthetic、calibrated、target/weapon/aspect/closure/miss-distance/source/provenance gate，且 descriptor 明确授予 `effect_scale_authority` 或 `component_failure_probability_authority` 时，row 才可能被消费。`surface_incidence_cos` 只是在已授权 row 集合内继续做适用性过滤。

明确边界：

- 不因为某个 row 匹配 `surface_incidence_cos` 就授予 Pk；
- 不因为法向入射证据较高就放行 deterministic fuze；
- 不把 `effect_scale` 或 `component_failure_probability` fixture 当作真实校准杀伤率；
- 不允许缺少 `row_id` / `source_ref` / `provenance` 的 row 进入权威消费路径；
- 不允许 synthetic descriptor、synthetic profile 或 aircraft JSON 自声明越过 evidence gate。

## 当前验证锚点

聚焦回归覆盖两层语义：

- `test_phase3_surface_incidence_cos_reports_obliquity_evidence`：证明 normal / oblique 局部命中能产生不同 `mechanism_surface_incidence_cos`，无效导弹轴时为 `0`，主组件与候选组件 row 的字段范围保持在 `[0, 1]`。
- `test_phase5_effect_scale_rows_can_use_surface_incidence_gate`：证明授权 descriptor 内的 `min_surface_incidence_cos` / `max_surface_incidence_cos` row gate 能区分 normal / oblique fixture，并把被消费 row id/source/provenance 写回事件审计面。
- `test_phase5_component_failure_rows_can_use_surface_incidence_gate`：证明授权 component-failure probability rows 也能用 `min_surface_incidence_cos` / `max_surface_incidence_cos` 区分 normal / oblique fixture，并把 `component_failure_probability_evidence_row_id` 与 source ref 写回事件审计面。

相关契约/绑定测试继续证明字段能跨 C++ contract、Python binding 和 launch adapter snapshot 暴露；它们只证明数据面稳定，不证明校准有效性。

## 与 A2 主线的关系

该进展补强 Phase 3 的 warhead mechanism evidence 和 Phase 5 的 vulnerability evidence row gate：

- Phase 3：使 mechanism-load vector 增加入射斜度维度，便于后续校准模型区分法向/擦掠事件；
- Phase 5：使 calibrated descriptor rows 能在 weapon/aspect/closure/miss-distance 之外，再按当前事件的 obliquity 证据做过滤；
- Phase 4：仍 deferred。surface-incidence evidence 不改变当前 deterministic fuze 未放行的结论。

当前可声明的关闭项只有：surface-incidence 证据面和 row gate 形状已可审计。仍未关闭：真实破片云、真实连续杆切割角、真实穿透/跳弹、校准组件失效概率、Pk 曲线、kill-chain 校准和确定性引信。
