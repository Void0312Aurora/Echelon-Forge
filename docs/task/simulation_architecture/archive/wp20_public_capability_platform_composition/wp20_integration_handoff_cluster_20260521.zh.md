# WP20-F Integration And Handoff

状态：`2026-05-21` complete / accepted。

语言版本：

- 英文主文：[wp20_integration_handoff_cluster_20260521.md](wp20_integration_handoff_cluster_20260521.md)
- 中文辅文：`wp20_integration_handoff_cluster_20260521.zh.md`

输入：

- [WP20 主计划](public_capability_platform_composition_wp20_20260521.zh.md)
- A-E task returns

## 目的

集成 WP20 worker 结果、运行验证、记录 residuals、同步索引，并且只在实现证据存在后
准备验收。

## 范围

范围内：

- merge 并验证 A-E changes；
- 解决 B/C/D contract、runtime 与 binding surfaces 之间的冲突；
- 记录 compatibility boundaries 与 WP21 residuals；
- 更新 README/review indexes 与 bilingual closure docs；
- gate 通过后再创建 acceptance review。

范围外：

- first-wave implementation ownership；
- 从 planned docs 直接验收。

## 任务项

| ID | 任务 | 验收 |
|----|------|------|
| `F1` | Merge review | A-E changes 已按 scope、compatibility 与 guard consistency 检查。 |
| `F2` | Validation rollup | 精确记录 commands 与 outcomes。 |
| `F3` | Residual routing | scenario migration、arbitrary bundle materialization 与 WP21 dependencies 被诚实路由。 |
| `F4` | Acceptance prep | README/index sync 与 acceptance review 只在 gates pass 后准备。 |

## 验证汇总

```bash
git diff --check
bash tools/maintenance/cmo_env.sh python -m pytest -q tests/architecture/test_wp14_*.py tests/architecture/runtime_facade
bash tools/maintenance/cmo_env.sh python -m pytest -q tests/architecture/platform_spawn/test_typed_platform_spawn_contracts.py tests/architecture/platform_spawn/test_runtime_setup_consume_bridge.py
bash tools/maintenance/cmo_env.sh python -m pytest -q tests/runtime/bindings/test_bindings_runtime_dto_surface.py tests/runtime/bindings/test_typed_platform_spawn_bindings.py
bash tools/maintenance/cmo_env.sh python -m pytest -q tests/runtime/facade/test_runtime_facade.py -k "typed_platform_setup or world_setup or capability or spawn"
bash tools/maintenance/cmo_env.sh python -m pytest -q tests/world_batch/test_world_batch_runtime.py -k "spawn or world_setup"
bash tools/maintenance/cmo_env.sh python -m pytest -q tests/runtime/bindings/test_bindings_runtime_dto_surface.py tests/runtime/bindings/test_typed_platform_spawn_bindings.py
python3 tools/maintenance/wp_doc_closure_audit.py --wp WP20 --summary
```

观察结果：

- `git diff --check`：通过。
- Architecture batch：`34 passed in 3.05s`。
- Runtime binding DTO surface batch：`26 passed in 0.06s`。
- Runtime facade slice：`4 passed, 16 deselected in 0.27s`。
- `cmake --build build-workshop --target ef_py -j2`：通过，`ef_py` 已构建。
- `python3 tools/maintenance/wp_doc_closure_audit.py --wp WP20 --summary`：
  通过，且 WP20 验收审查与所需中文辅文都已存在。

## 交付

WP20 已作为 bounded public capability-platform composition 增量验收。

有意保留的 residuals：

- 没有 `spawn_platform` surface；
- 没有强制 scenario migration；
- 没有 arbitrary capability-bundle materialization；
- WP21/full counterfactual 仍然是独立路线；
- type-name compatibility 继续维持。

返回 validation rollup、residual register 与 next-route notes；WP20 closure
已无 blockers。
