# WP18-E C++ Hot Path Migration Matrix

状态：`2026-05-21` complete / accepted。

语言版本：

- 英文主文：[wp18_cxx_hot_path_migration_matrix_cluster_20260521.md](wp18_cxx_hot_path_migration_matrix_cluster_20260521.md)
- 中文辅文：`wp18_cxx_hot_path_migration_matrix_cluster_20260521.zh.md`

输入：

- [WP18 主计划](runtime_ownership_cxx_hot_path_consolidation_wp18_20260521.zh.md)
- [WP18-A ownership fact ledger](wp18_ownership_fact_ledger_hot_path_map_cluster_20260521.zh.md)
- [WP18 dispatch queue](wp18_subagent_dispatch_queue_20260521.zh.md)
- [架构与性能路线进一步调研](../../../plan/architecture/architecture_and_performance_research_followup.zh.md)

## 目标

把性能路线建议收敛为有边界的 migration matrix，并记录 WP18-E 已完成的
第一条切片。WP18-E 不重写全部 hot paths，而是排序候选项、记录已经完成的
安全迁移，并只命名下一条候选，不在本波实现。

## 范围

范围内：

- 为 reward/termination metadata、route/approach/post-transition metadata、
  request build/consume、observation export 与 episode-state sync 构建 migration matrix；
- 为每行标注 complexity、owner、risk、test anchors 与 dependency notes；
- 记录 second-wave reward metadata closure 与 residuals；
- 为 batch-prepare reward/termination/breakdown 覆盖提供有效 validation anchor。

范围外：

- CUDA/resident-state migration；
- 完整 Gym frontend rewrite；
- 本波启动 request-build migration；
- 修改 B/C ownership seam。

## Second-Wave 结果

已完成的 first slice 是 reward metadata。默认 compiled `ScenarioLoader`
路径现在会优先消费通过 `ef_py.build_episode_reward_breakdown_json` 生成的
C++ reward-breakdown metadata，只有在无法生成 C++ metadata 时才保留窄
Python mirror/fallback。这样 reward total、termination reason、status 与
reward-breakdown terms 都与 C++ `ExecutionEpisodeRuntimeInputs` /
`ExecutionEpisodeRuntimeProducts` contract 对齐。

之前的 batch-prepare 验证选择器
`tests/runtime/execution/test_execution_episode_batch_prepare.py -k "reward or termination or breakdown"`
不会选中任何测试。现在有效锚点是重命名后的
`test_batch_prepare_reward_termination_breakdown_matches_direct_runtime_inputs`：
它比较 batch prepare 产物与 direct runtime inputs 的运行结果，并同时验证两侧
生成的 C++ reward-breakdown JSON 一致。

## Migration Matrix

| Rank | Candidate | Status | Value | Complexity | Owner / seam | Risk | Test anchor | Routing |
|---|---|---|---|---|---|---|---|---|
| 1 | 默认 compiled path 的 reward/termination breakdown metadata | `closed in second wave` | high | low-medium | C++ `core/mission/runtime`、`episode/detail/episode_reward_breakdown`、Python compiled consume seam | low | `test_compiled_episode_runtime_prefers_cxx_reward_metadata`、`test_episode_reward_breakdown_builder_matches_reward_total_and_terms`、`test_batch_prepare_reward_termination_breakdown_matches_direct_runtime_inputs` | 作为 WP18-E closure evidence 保留；third wave 不再改 runtime。 |
| 2 | Route/approach/post-transition metadata handoff | `next safe candidate / not implemented` | high | medium | C++ episode detail helpers 与 `ScenarioLoader` runtime mirror | medium | 现有 route/approach controller 与 scenario-loader parity tests；迁移前需要新的窄 metadata-preference test | 这是下一条安全候选，因为 C++ transition/detail helper 已存在；但只能做 metadata handoff，不能扩展为 request-build rewrite。 |
| 3 | Episode-state sync 与 facade-owned batch consume | `partially advanced by WP18-B` | high | medium-high | `ExecutionEpisodeController`、facade DTO、`WorldBatchVecEnv` consume path | medium-high | WP18-B/D 的 facade/world-batch regression anchors | 路由给 B/D；WP18-E 本波不改 ownership seam。 |
| 4 | Observation export | `defer` | medium | medium-high | facade observation DTO 与 compatibility adapter | medium | observation runtime 与 world-batch compatibility tests | 等 facade-owned batch evidence 稳定后再回看。 |
| 5 | Request build/consume loop migration | `defer / blocked for this wave` | high | high | `WorldBatchVecEnv`、facade adapter、request DTO contracts | high | 需要更宽的 vec-env/facade 覆盖 | WP18-E third wave 不启动；等待 B/C seam 与 compatibility payload 稳定。 |

## Residuals

| Residual | Impact | Owner / next action |
|---|---|---|
| Reward metadata 的 Python fallback 仍保留 | 这是兼容性需要，但 maintained default path 应持续优先 C++ metadata。 | 保留 C++ metadata preference 聚焦测试；等兼容消费者退场后再考虑移除 fallback。 |
| Batch-prepare 曾经使用 no-op `-k` gate | 主线程验证可能没有实际选中 reward 相关 batch-prepare 测试。 | 现在 `-k "reward or termination or breakdown"` 已能选中重命名锚点；也可直接跑完整 batch-prepare 文件。 |
| Route/approach/post-transition metadata 仍有 Python mirror 工作 | 它是下一条安全迁移候选，但本波没有实现。 | 任何 runtime edit 前，先补一个窄 metadata-preference preflight test。 |
| Request build/consume 仍是 Python frontend hot path | 性能收益高，但 ownership 风险也高。 | 等 B/C ownership seam 与 facade compatibility contract 稳定后再迁移。 |

## Validation

Third-wave 必跑验证：

```bash
git diff --check
python3 tools/maintenance/wp_doc_closure_audit.py --wp WP18 --summary
bash tools/maintenance/cmo_env.sh python -m pytest -q tests/runtime/execution/test_execution_step_runtime.py
bash tools/maintenance/cmo_env.sh python -m pytest -q tests/runtime/execution/test_scenario_loader_execution_step_runtime.py -k "cxx_reward_metadata or selected_paths_match_legacy_runtime or flight_shaping_backends_match_legacy_runtime"
bash tools/maintenance/cmo_env.sh python -m pytest -q tests/runtime/execution/test_execution_episode_batch_prepare.py
```

可选窄锚点验证：

```bash
bash tools/maintenance/cmo_env.sh python -m pytest -q tests/runtime/execution/test_execution_episode_batch_prepare.py -k "reward or termination or breakdown"
```

## Handoff

WP18-E closure impact：第一条 hot-path metadata slice 已记录为完成；默认 compiled
路径的 C++ metadata preference 已写明；之前 no-op validation selector 现在对应真实
覆盖；下一条安全候选命名为 route/approach/post-transition metadata handoff，但没有
启动 request-build migration。
