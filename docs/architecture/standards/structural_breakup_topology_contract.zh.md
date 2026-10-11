# 结构解体拓扑契约

Language:
- English canonical: `docs/architecture/standards/structural_breakup_topology_contract.md`
- Chinese companion: `structural_breakup_topology_contract.zh.md`

Document kind: `standard`
Lifecycle: `maintained`
Canonical: `docs/architecture/standards/structural_breakup_topology_contract.md`
Owner: `architecture/air-damage`
Last verified: `2026-10-10`

结构解体通过 `HitboxConfig` 中的显式拓扑 profile，并将其复制到
`ComponentDamageState` 中选择路径。单独出现某个组件名称不会再放行专用路径。

## Profile 与准入

- `default_shared_spar_v1` 是默认 profile，使用共享翼梁、发动机核心、控制面、
  燃油单元、尾部与机身贡献项。
- `tg_p7_split_surface_v1` 只有在八个 split receiver 全部存在时才准入：三个发动机
  分段、四个翼梁分段以及翼梁承力贯穿分段。
- 已声明 TG-P7 profile 但 receiver 不完整时，状态明确记为
  `TgP7IncompleteFallback`，并使用默认共享翼梁路径。
- 未知 profile 标识符由 unit-definition loader 拒绝；直接构造的运行时未知 profile
  则 fail-closed 到默认路径。

准入后 TG-P7 的阈值和结果保持不变；profile 只控制已有拓扑映射是否可用。

## 解体结果解释

- `active_structural_groups` 统计物理脱离组。
- `active_break_modes` 是由这些组导出的 family 位掩码。
- `detached_part_count` 统计激活的物理组，而不是 mode family 数量。
- `breakup_state` 根据唯一 mode family 数量计算：一个 family 为
  `PartialDetachment`，两个为 `PartialBreakup`，三个或更多为 `FullBreakup`，同时增加
  `MultiAxis`。
- 机动性和损失后果单独消费 mode 位掩码，不从脱离部件数量推断。

原生 structural-failure 测试覆盖共享翼梁合成 profile、完整 TG-P7 准入、不完整 profile
回退、family 计数以及既有 TG-P7 结果保持。
