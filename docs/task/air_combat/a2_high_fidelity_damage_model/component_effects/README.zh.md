# A2 组件/平台后果模型后续路线

状态：`2026-05-28` 路线文档。本文档包只描述当前 structured-aircraft component effects 的工程现状、后续路线、验收建议和非权威边界，不改动运行时代码、测试或 aircraft database。

## 文档索引

- [当前 aircraft component inventory 概览](current_aircraft_component_inventory_20260528.zh.md)
- [可工程化扩展项 vs 必须等校准项](engineering_extensions_vs_calibration_gates_20260528.zh.md)
- [冗余/依赖图路线](redundancy_dependency_graph_roadmap_20260528.zh.md)
- [平台后果模型路线](platform_consequence_model_roadmap_20260528.zh.md)
- [验收测试建议和 non-authoritative 边界](acceptance_tests_and_non_authoritative_boundaries_20260528.zh.md)

## 总体结论

当前 A2 structured-aircraft 路径已经具备代表性组件 inventory、组件几何入口、组件完整性记忆、冗余组可用性、依赖传播、aircraft overlay 后果状态以及 `EffectsEvent`/`DamageReport` 审计面。首批覆盖平台为 `F-16C_Block50`、`Su-35S_Flanker-E`、`MQ-9_Reaper`、`MH-60R_MVP` 和 `E-3_Sentry_AWACS`。

但这些内容仍是工程校准和数据通路证明。不得把现有组件样例、合成 component-failure probability、synthetic vulnerability profile、RNG proximity fuze 或参数化 warhead sampling 宣称为校准 Pk、确定性引信、真实破片云、真实连续杆切割或完整平台脆弱性 authority。

## 建议推进顺序

1. 先冻结组件命名、系统 taxonomy、依赖边类型和 event contract，避免后续校准数据接入时反复迁移。
2. 再补全当前五类代表平台的组件覆盖一致性和冗余组一致性，优先补 dependency graph 的可解释传播。
3. 然后按 flight-control、hydraulic、fuel、fire、sensor、crew 六条后果线分别建立 monotonic 工程模型与回归测试。
4. 最后接入校准数据包、validated physics surrogate 或外部 calibration dataset，并通过 authority gate 放行概率、阈值、速率和 Pk/kill-chain claims。

