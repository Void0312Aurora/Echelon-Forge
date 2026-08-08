# Architecture 测试系统治理收口

Document kind: `review`
Lifecycle: `accepted`
Canonical: `docs/engineering/testing/reviews/architecture_test_system_governance_closeout_20260610.zh.md`
Owner: `engineering/testing`
Last verified: `2026-06-10`

状态：`2026-06-10` 本轮 `tests/architecture` 治理关闭。

## 结论

本轮治理把 `tests/architecture` 从“按工作包/历史过程增生脚本”推进到“按功能能力承载 guard”的状态。当前收口标准不是所有历史标签完全消失，而是：

- 文件名优先表达被守护的能力面或架构不变量。
- 新场景默认并入既有能力文件；只有新增独立 failure policy、执行模型或所有权边界时才新增脚本。
- CI smoke 只引用代表性 nodeid，不把 broad architecture 目录或文件整体塞进 smoke。
- 历史 `WP`、`A2` 等标签可以保留在测试函数名和归档文档中，用于证据追溯，而不是继续驱动文件命名。

## 已完成

| 区域 | 本轮动作 | 收口状态 |
| --- | --- | --- |
| `damage_model/` | 已完成 external signoff 三件套合并，并把 damage-model 文件压缩为 source/provenance、release authority、fragility/probability、retained manifest 等能力面。 | 关闭本轮治理。 |
| `platform_spawn/` | 合并 typed spawn DTO、capability materialization、resolved spawn plan 等小文件；保留 6 个能力文件。 | 关闭本轮治理。 |
| `runtime_facade/` | 删除旧 broad layering guard，拆为 scenario setup facade、runtime escape hatch、runtime facade contract、tasking batch contract 四个语义文件，并抽出共享 helper。 | 关闭本轮治理。 |
| `structural_boundaries/` | 删除旧 broad structural guard，拆为 counterfactual structure、runtime window、weapon release、binding quarantine、domain separation 五个语义文件，并抽出共享 helper。 | 关闭本轮治理。 |
| suite manifests | 更新 CI smoke nodeid、focused runtime suite、test system matrix 和 manifest 自检。 | 关闭本轮治理。 |
| stale guards | 修复 domain split 后仍指向旧 flat domain 路径的 command/tasking guard，修复 archived WP closure audit 的 active-only 假设，修复 platform spawn 的格式脆弱断言。 | 关闭本轮治理。 |
| local residue | 删除 ignored 的 `tests/architecture/build/` 旧残留，避免与 `build_system/test_cmake_target_readiness.py` 同名 import mismatch。 | 关闭本轮治理。 |

## 保留边界

- 不把 `tools/maintenance/a2_blastfrag_*` 这类生产/维护工具重命名；它们属于工具历史兼容面，不属于本轮测试脚本语义重建。
- 不把所有 `WP` / `A2` 函数名清零；函数名里的历史标签仍作为归档证据锚点。
- 不在本轮继续把 runtime escape hatch、binding quarantine、structured-air authority 等测试跨目录再迁移一次。只读 subagent 已指出这些是可选的更激进切片，但当前文件名已经按能力面收口，继续跨目录迁移会扩大文档和 suite churn。

## 当前形态

- `tests/architecture` 当前 `test_*.py` 文件数：`54`。
- architecture collection：`461 tests collected`。
- `runtime_facade/` 当前测试文件：
  - `test_design_boundary_gates.py`
  - `test_runtime_dto_contracts.py`
  - `test_runtime_escape_hatches.py`
  - `test_runtime_facade_contract_boundaries.py`
  - `test_scenario_setup_facade_boundary.py`
  - `test_tasking_batch_contract_boundaries.py`
- `structural_boundaries/` 当前测试文件：
  - `test_binding_quarantine_boundaries.py`
  - `test_counterfactual_structure_boundaries.py`
  - `test_domain_separation_boundaries.py`
  - `test_runtime_window_structure.py`
  - `test_weapon_release_structure.py`

## 验证

- `source tools/maintenance/cmo_env.sh && cmo_python -m pytest -q tests/architecture/runtime_facade tests/architecture/structural_boundaries tests/architecture/platform_spawn tests/architecture/command_tasking tests/architecture/governance tests/architecture/policy_execution tests/runners/test_pytest_suite_manifests.py`
  - `192 passed`
- `source tools/maintenance/cmo_env.sh && cmo_python -m pytest --collect-only -q tests/architecture`
  - `461 tests collected`
- `source tools/maintenance/cmo_env.sh && cmo_python tools/runners/run_pytest_suite.py --suite tests/smoke/ci_smoke_suite.json`
  - `321 passed, 38 subtests passed`
- legacy architecture-test filename residual scan
  - no matches
- `git diff --check -- docs tests tools`
  - clean
