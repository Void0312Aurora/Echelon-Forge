# 仿真架构归档

这里保留历史、已验收、blocked、已替代或已闭合的架构工作包，用于追溯。
当前架构入口仍是 [../README.zh.md](../README.zh.md)。

## 已闭合 / 已冻结工作线

- [WP22 Legacy Compatibility Retirement And Architecture Hardening](wp22_legacy_compatibility_retirement/legacy_compatibility_retirement_wp22_20260522.zh.md)：
  已被 owner 否决并冻结、由 WP23 取代的工作流；其 dispatch queue 只作历史记录。
- [WP23 Legacy Retirement Recovery And Reset](wp23_legacy_retirement_recovery/legacy_retirement_recovery_wp23_20260523.zh.md)：
  WP22 冻结后的受控 blocked recovery 记录。
- [WP24 TaskOrder Maintained Business Migration](wp24_taskorder_maintained_business_migration/taskorder_maintained_business_migration_wp24_20260524.zh.md)：
  已接受的 replacement-backed TaskOrder 业务迁移，并已发布 canonical acceptance review。
- [TM01 Architecture Closure Remediation](tm01_architecture_closure_remediation/README.md)：
  `2026-05-25` 闭合的 audited-slice remediation；后续 TM02/TM03 已关闭它记录的
  两个明确 ledger gap。
- [TM02 WP24 Acceptance Closure](tm02_wp24_acceptance_closure/README.md)：
  临时 closure lane，用于发布 WP24 canonical acceptance review 并同步索引。
- [TM03 Launch Bridge Boundary](tm03_launch_bridge_boundary/README.md)：
  临时 closure lane，通过 `IWeaponReleaseService` 关闭两个明确的 launch-helper
  `systems -> SimulationKernel` bridge。

## 旧 WP 记录

其余 `wp*` 归档目录保存早期 work-package packet 和 acceptance 记录。日常阅读请优先使用父级
[仿真架构 README](../README.zh.md) 的整理后顺序；只有需要 provenance 时再进入这些归档包。
