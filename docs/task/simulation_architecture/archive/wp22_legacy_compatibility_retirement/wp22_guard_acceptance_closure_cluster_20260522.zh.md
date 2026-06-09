# WP22-F Guardrail 与验收收尾

状态：`2026-05-22` not eligible；只在 B-E 证据存在后才串行 closure。
最新 preflight 只返回 guard hardening：repo 级 `batch_runtime` consumer scan
更强，但公开 escape hatches、default-factory typed control-state replacement、
aggregate DTO retirement 与 broad binding/service debt 仍开放，因此不授权
acceptance review。
第八轮验收没有改变这个 gate：Banach 与 Planck 是 scoped pass，Harvey 是
`partial`；本地 focused sweep 通过，但 closure audit 仍报告 `0` 个 canonical WP22
acceptance review。

输入：

- [WP22 main plan](legacy_compatibility_retirement_wp22_20260522.zh.md)
- [WP22-A fact ledger](wp22_retirement_fact_ledger_cluster_20260522.zh.md)
- [WP22-B Python business bypass retirement](wp22_python_business_bypass_retirement_cluster_20260522.zh.md)
- [WP22-C runtime escape-hatch closure](wp22_runtime_escape_hatch_closure_cluster_20260522.zh.md)
- [WP22-D command DTO legacy retirement](wp22_command_dto_legacy_surface_retirement_cluster_20260522.zh.md)
- [WP22-E structural decomposition](wp22_structural_god_file_decomposition_cluster_20260522.zh.md)
- [WP22 dispatch queue](wp22_subagent_dispatch_queue_20260522.zh.md)

## 目的

只有强制退场实际发生后才关闭 WP22。本流拥有 guards、validation rollup、index sync、
bilingual closure，以及实现证据存在后的 acceptance draft。

## 拥有范围

- legacy/default access 的 architecture guard tests
- validation rollup 与 kill-list closure notes
- README 与 review index sync
- 必需中文 companion
- 实现证据存在后的 acceptance review draft

## 必需产出

| 区域 | 要求 |
|------|------|
| Guard pack | 新的默认 `loader.sim.*`、`.runtime(`、`batch_runtime`、silent `legacy` mode、raw mission-cmd consumers 与 allowlist 外 unowned legacy command usage 会使测试失败。 |
| Kill-list closure | 每个 WP22-A 项都是 `retired`、`quarantined with opt-in` 或 `blocked with failing guard`；没有 “accepted residual”。 |
| Validation rollup | B-E 实现证据存在后记录 commands 与 outcomes。 |
| Publication | README/review indexes、中文 companion 与 acceptance review 只在实现 gate 通过后同步。 |

## Gate

如果任何 maintained default path 仍在没有 explicit opt-in compatibility boundary 和
new-caller failing guard 的情况下使用 legacy surface，则 closure 失败。

Preflight-only note：当前 WP22-C guard hardening 收紧了 repo-level non-test
Python scan，但不改变 not-eligible closure state，也不退场任何 public escape
hatch。Pauli/Ramanujan 的 guard-and-quarantine pass 也不是 closure evidence：
它们标记 DTO transport shell 与 binding helper role，但没有移除剩余 compatibility
surface。

预检说明：当前 WP22-C 的 guard hardening 只是把 maintained Python scan 扩展到
repo-level 非测试入口，并不会改变 not-eligible 的 closure 状态，也不会把任何
public escape hatch 写成 retired。
Banach 在本切片关闭了 maintained binding raw-entity seam，Planck 抽出了一条
visual-binding service helper；但 broad bindings、diagnostics/legacy raw ECS、
public escape hatches 与 default-factory typed control-state blocker 仍然开放。

最新本地预检：

- `python3 -m pytest -q tests/architecture/test_wp22_default_factory_legacy_seed_guard.py tests/architecture/test_wp22_structural_guardrails.py tests/architecture/runtime_facade/test_layering.py -k "wp22 or bindings or world_batch_runtime or gpu_visual_binding or visual_binding_raw_world_access or escape_hatch or batch_runtime"` -> `32 passed, 16 deselected`
- `python3 tools/maintenance/wp_doc_closure_audit.py --wp WP22 --summary` -> `0` 个 canonical acceptance review；必需 zh companion 存在
- `git diff --check` -> 通过

这只是 guard/preflight evidence，不得转写成 acceptance review。

## 建议验证

```bash
git diff --check
python3 tools/maintenance/wp_doc_closure_audit.py --wp WP22 --summary
python -m pytest -q tests/architecture -k "legacy or facade or runtime or tasking or command"
python -m pytest -q tests/runtime/facade
python -m pytest -q tests/world_batch
python -m pytest -q tests/scenario
```

## 停止规则

- 不得从 planned docs 创建 acceptance。
- 不得因为路径 compatibility-preserving 就标记 complete。
- 不得在 prose 中隐藏 blockers；blocker 必须有 owner、guard 与下一条 command。
