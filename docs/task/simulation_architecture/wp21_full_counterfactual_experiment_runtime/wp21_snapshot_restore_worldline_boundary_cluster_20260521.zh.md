# WP21-B Snapshot Restore And Worldline Boundary

状态：`2026-05-21` planned；等待 WP21-A facts。

Language:

- English canonical:
  [wp21_snapshot_restore_worldline_boundary_cluster_20260521.md](wp21_snapshot_restore_worldline_boundary_cluster_20260521.md)
- Chinese companion: `wp21_snapshot_restore_worldline_boundary_cluster_20260521.zh.md`

## 目的

将已验收的 selected-entity snapshot/branch path 扩展为 final counterfactual runtime
所需的最小 bounded snapshot/restore boundary。

## 范围

范围内：

- 捕获和恢复第一条 full experiment runtime slice 所需的 declared host-owned state；
- worldline identity、seed、barrier、provider/fidelity 与 evidence refs；
- facade-owned restore authority 与 fail-closed rejection reasons；
- 如果暴露 public DTOs，则补充 C++/facade/binding tests。

范围外：

- exact GPU 或 resident-state promotion；
- 没有 explicit boundary evidence 的 arbitrary live-world cloning；
- experiment orchestration 或 scenario generation。

## 任务项

| ID | 项目 | 验收 |
|----|------|------|
| `B1` | Snapshot boundary DTO/runtime | Declared host-owned state 被捕获，并带 worldline id、barrier id、deterministic seed、provider/fidelity 与 evidence refs。 |
| `B2` | Restore boundary runtime | Restore 只能通过 facade authority 执行，并拒绝 unsupported state、raw mutation、invalid worldline ids 与 backend/resident-state claims。 |
| `B3` | Worldline registry seed | Parent/branch worldline ids 被足够追踪，使 C 可运行 independent rollouts。 |
| `B4` | Public surface proof | 如暴露 public DTOs，facade/binding tests 证明 reachable 与 fail-closed。 |

## 建议验证

```bash
git diff --check
bash tools/maintenance/cmo_env.sh python -m pytest -q tests/runtime/facade/test_runtime_facade.py -k "counterfactual or worldline or restore or snapshot"
bash tools/maintenance/cmo_env.sh python -m pytest -q tests/runtime/bindings/test_bindings_runtime_dto_surface.py -k "counterfactual or worldline"
```

## 交接

返回 snapshot schema、restore semantics、rejected unsupported claims、touched files、
commands run，以及 C 必须消费的精确 assumptions。
