# WP18 Subagent Dispatch Queue

状态：`2026-05-21` closed / accepted。

语言版本：

- 英文主文：[wp18_subagent_dispatch_queue_20260521.md](wp18_subagent_dispatch_queue_20260521.md)
- 中文辅文：`wp18_subagent_dispatch_queue_20260521.zh.md`

使用本队列发布 subagents。主线程拥有 integration 与最终验收。

## First Wave

| Stream | Agent type | Model / reasoning | Task | Write scope |
|--------|------------|-------------------|------|-------------|
| `WP18-A` | explorer 或 lightweight worker | `gpt-5.4-mini`, xhigh | 校验 ownership facts、hot paths、C++ assets 与 first-slice candidates。 | 仅 WP18 docs/fixtures/architecture inventory tests；不改 runtime behavior。 |
| `WP18-B` | worker | `gpt-5.4`, xhigh | 在 A 确认 slice 后，实现或预检一条 execution-episode ownership sink。 | Execution episode facade/runtime seams 与聚焦测试；不拆 `ScenarioLoader`。 |
| `WP18-C` | worker | `gpt-5.4`, high | 拆分或守住 `ScenarioLoader` 在 scenario/content adapter、runtime mirror 与 frontend helper 之间的责任。 | 仅 `ScenarioLoader` boundary files/tests；不改 C++ runtime logic。 |
| `WP18-D` | worker | `gpt-5.4`, high | A 之后强化 facade/compatibility guards 与 allowlists，再集成 B/C surfaces。 | Architecture guard tests、facade shape checks、compatibility allowlists。 |
| `WP18-E` | worker | `gpt-5.4`, xhigh | 构建 migration matrix，并在安全时实现一条 bounded C++ hot-path slice。 | Matrix docs 加 selected C++ runtime 或 request build/consume files；需与 B/C 协调。 |

## 发布规则

| Stream | Release condition |
|--------|-------------------|
| `WP18-A` | 立即发布；它是 first-wave fact authority。 |
| `WP18-B` | A 返回 selected ownership slice 后发布；若 A 仍运行，只能作为 preflight-only。 |
| `WP18-C` | A 命名 loader owner/mirror/helper categories 后发布；也可作为 responsibility-map preflight。 |
| `WP18-D` | A 后可发布 guard prework；final hardening 等 B/C replacement surfaces。 |
| `WP18-E` | A 后发布；implementation 部分等待 B/C conflict risks 已知。 |
| `WP18-F` | A-E 返回 mergeable 或 blocked packets 前不要发布。 |

## First-Wave Return State

| Stream | Agent | Return status | Planning consequence |
|--------|-------|---------------|----------------------|
| `WP18-A` | Socrates | `pass` | Ownership facts 已在 WP18-A ledger 冻结。第一条实现应从 `ExecutionEpisodeController` 与既有 C++ runtime helpers 后面的 execution-episode ownership sink 开始，而不是 broad `ScenarioLoader` split 或 VecEnv rewrite。 |
| `WP18-C` | Volta | `preflight-only / pass` | `ScenarioLoader` 已经模块化，但仍以一个混合对象呈现。最安全的 C 首切片是为 `SCENARIO_LOADER_STATE_SHELL_ATTRS` 添加字段分类 guard，而不是 behavioral split。 |
| `WP18-D` | Copernicus | `preflight-only / pass` | 现有 facade guards 对 `leader_world_batch_runtime` 与 `WorldBatchVecEnv` 较强，但可以在不删除 public APIs 的前提下补强全局 maintained-path `.world()` / `.batch_runtime.` 覆盖。 |
| `WP18-E` | Ampere | `preflight-only / pass` | 最安全的 E 首切片是用 C++-generated metadata 替代 default compiled path 上的 Python reward-breakdown / termination reconstruction。Request build/consume 与 episode-state sync 风险高，应与 B/C 协调。 |

## Second Wave

| Stream | Agent type | Model / reasoning | Task | Write scope |
|--------|------------|-------------------|------|-------------|
| `WP18-B` | worker | `gpt-5.4`, xhigh | 使用 `ExecutionEpisodeController` 与既有 facade/runtime state exports 实现第一条 execution-episode ownership sink。 | Execution episode facade/runtime seams 与聚焦测试；不编辑 `ScenarioLoader` internals 或 C++ hot-path reward logic。 |
| `WP18-C` | worker | `gpt-5.4`, high | 添加 `ScenarioLoader` state-shell responsibility classification guard，并保留 public loader APIs。 | `gym_envs/scenario_loader/runtime_state.py`、窄 loader classification tests 与 WP18-C docs；不编辑 C++ runtime logic。 |
| `WP18-D` | worker | `gpt-5.4`, high | 添加 maintained-path raw runtime/world/batch access guard prework，不删除 compatibility APIs。 | `tests/architecture/test_runtime_facade_layering.py` 与 allowlist docs/comments；final hard bans 等 B/C。 |
| `WP18-E` | worker | `gpt-5.4`, xhigh | 若能避开 B/C ownership 冲突，实现低风险 reward/termination metadata first slice。 | C++ reward/termination metadata helper/binding 或 Python compiled-path consume seam 加聚焦测试；不改变 request build/consume ownership。 |

## Second-Wave Return State

| Stream | Agent | Return status | Integration consequence |
|--------|-------|---------------|-------------------------|
| `WP18-B` | Mendel | `pass` | `ExecutionBatchStepResult.execution_episode_states` 现在携带 facade/runtime-owned post-step episode state。`WorldBatchVecEnv` mainline 会先消费该字段，再回退到 legacy `step_result.controller_state`；compatibility payloads 保留。 |
| `WP18-C` | Herschel | `pass` | `ScenarioLoaderStateShell` 字段已有不可变 responsibility classifications 与 import-time contract validation。本切片只做 guard，不拆 public loader behavior。 |
| `WP18-D` | Bohr | `pass` | Facade-layer architecture tests 现在阻止新的 maintained `.batch_runtime.` 与 `RuntimeFacade.runtime()` consumers 落到命名 compatibility/diagnostic allowlists 之外。Public compatibility APIs 保留。 |
| `WP18-E` | Linnaeus | `pass` | Default compiled path 现在通过 Python-visible helper 优先消费 C++ reward-breakdown metadata。Python 仅保留窄 mirror/fallback；request-build 与 episode-state sync ownership 仍属后续独立切片。 |

主线程 second-wave validation：

- `cmake --build build-workshop --target ef_core ef_py -j4` 通过。
- `git diff --check` 通过。
- `python3 tools/maintenance/wp_doc_closure_audit.py --wp WP18 --summary` 通过；WP18 仍在推进中，因此 acceptance review 继续保持缺席。
- `bash tools/maintenance/cmo_env.sh python -m pytest -q tests/architecture/test_runtime_facade_layering.py` 通过：`17 passed`。
- `bash tools/maintenance/cmo_env.sh python -m pytest -q tests/architecture/test_wp16_legacy_path_gates.py` 通过：`6 passed`。
- `bash tools/maintenance/cmo_env.sh python -m pytest -q tests/runtime/execution/test_execution_episode_state.py` 通过：`5 passed`。
- `bash tools/maintenance/cmo_env.sh python -m pytest -q tests/runtime/execution/test_scenario_loader_execution_step_runtime.py -k "state or runtime or reward or termination"` 通过：`11 passed, 8 subtests passed`。
- `bash tools/maintenance/cmo_env.sh python -m pytest -q tests/runtime/facade/test_runtime_facade.py -k "execution or episode or batch"` 通过：`4 passed, 14 deselected`。
- `bash tools/maintenance/cmo_env.sh python -m pytest -q tests/runtime/facade/test_facade_step_evidence_gates.py` 通过：`1 passed`。
- `bash tools/maintenance/cmo_env.sh python -m pytest -q tests/world_batch/test_world_batch_vec_env.py -k "execution_episode_controller_mainline or compatibility_view"` 通过：`6 passed, 31 deselected`。
- `bash tools/maintenance/cmo_env.sh python -m pytest -q tests/world_batch/test_world_batch_runtime.py -k "execution_episode"` 通过：`3 passed, 18 deselected`。
- `bash tools/maintenance/cmo_env.sh python -m pytest -q tests/runtime/bindings/test_bindings_runtime_dto_surface.py` 在同步 cadence DTO public-field expectations 后通过：`17 passed`。
- `bash tools/maintenance/cmo_env.sh python -m pytest -q tests/runtime/execution/test_execution_step_runtime.py` 通过：`14 passed`。
- `bash tools/maintenance/cmo_env.sh python -m pytest -q tests/runtime/execution/test_scenario_loader_execution_step_runtime.py -k "cxx_reward_metadata or selected_paths_match_legacy_runtime or flight_shaping_backends_match_legacy_runtime"` 通过：`3 passed, 8 deselected, 4 subtests passed`。
- `bash tools/maintenance/cmo_env.sh python -m pytest -q tests/runtime/execution/test_execution_episode_batch_prepare.py` 通过：`2 passed`；当前树中较窄的 `-k "reward or termination or breakdown"` 不是有效覆盖门槛。

## Third Wave

| Stream | Agent type | Model / reasoning | Task | Write scope |
|--------|------------|-------------------|------|-------------|
| `WP18-B/D` | worker | `gpt-5.4`, high | 补充 regression evidence，证明 maintained vec-env/facade consumers 会优先消费 facade-owned batch fields（`execution_episode_states`、reward、termination、status、reward breakdown），再回退 legacy `step_result` payloads。 | 聚焦 `tests/world_batch/test_world_batch_vec_env.py` 和/或 `tests/runtime/facade/test_facade_step_evidence_gates.py`。除非测试暴露真实 bug，否则不要改 runtime implementation。 |
| `WP18-C/D` | worker | `gpt-5.4`, high | 将 `ScenarioLoaderStateShell` responsibility classification 提升到 architecture guard 或窄 ownership test，避免未来 loader fields 绕过分类。 | 仅 classification/architecture tests。优先新增聚焦测试或复用 execution-state tests；避免编辑 runtime behavior。 |
| `WP18-E` | worker | `gpt-5.4`, high | 收束 hot-path matrix coverage hole：记录 second-wave reward metadata slice，替换无效 `-k` validation 为有意义测试锚点，并命名下一条安全迁移候选但不实现。 | WP18-E matrix docs 加必要的聚焦测试。不要改变 B/C ownership seams，也不要在本轮启动 request-build migration。 |

## Third-Wave Return State

| Stream | Agent | Return status | Integration consequence |
|--------|-------|---------------|-------------------------|
| `WP18-B/D` | Raman | `pass` | 新增聚焦 vec-env regression evidence，证明 facade-owned batch fields 会优先于被污染的 legacy `step_result` values，用例覆盖 reward、done/truncated、status vector、termination reason、reward breakdown JSON 与 state-change flag。Runtime implementation 未编辑。 |
| `WP18-C/D` | Helmholtz | `pass` | 新增 architecture-owned classification contract，钉住 `ScenarioLoaderStateShell` dataclass fields、bucket membership 与 allowed buckets。Runtime behavior 与 C++ logic 未编辑。 |
| `WP18-E` | Godel | `pass` | 在 hot-path matrix 中记录 reward metadata migration slice，并把先前 no-op 的 batch-prepare `-k` gate 替换为真实 reward/termination/breakdown 测试锚点。Request-build migration 继续 deferred。 |

主线程 third-wave validation：

- `git diff --check` 通过。
- `python3 tools/maintenance/wp_doc_closure_audit.py --wp WP18 --summary` 通过；WP18 仍在推进中，因此 acceptance review 继续保持缺席。
- `bash tools/maintenance/cmo_env.sh python -m pytest -q tests/architecture/test_runtime_facade_layering.py` 通过：`18 passed`。
- `bash tools/maintenance/cmo_env.sh python -m pytest -q tests/runtime/execution/test_execution_episode_state.py` 通过：`5 passed`。
- `bash tools/maintenance/cmo_env.sh python -m pytest -q tests/world_batch/test_world_batch_vec_env.py -k "execution_episode_controller_mainline or compatibility_view or facade"` 通过：`11 passed, 27 deselected`。
- `bash tools/maintenance/cmo_env.sh python -m pytest -q tests/runtime/facade/test_facade_step_evidence_gates.py` 通过：`1 passed`。
- `bash tools/maintenance/cmo_env.sh python -m pytest -q tests/runtime/execution/test_execution_step_runtime.py` 通过：`14 passed`。
- `bash tools/maintenance/cmo_env.sh python -m pytest -q tests/runtime/execution/test_scenario_loader_execution_step_runtime.py -k "cxx_reward_metadata or selected_paths_match_legacy_runtime or flight_shaping_backends_match_legacy_runtime"` 通过：`3 passed, 8 deselected, 4 subtests passed`。
- `bash tools/maintenance/cmo_env.sh python -m pytest -q tests/runtime/execution/test_execution_episode_batch_prepare.py` 通过：`2 passed`。
- `bash tools/maintenance/cmo_env.sh python -m pytest -q tests/runtime/execution/test_execution_episode_batch_prepare.py -k "reward or termination or breakdown"` 通过：`1 passed, 1 deselected`。

## Required Worker Return Packet

```md
Stream:
Status: pass | fail | blocked | preflight-only
Touched files:
Commands run:
Evidence:
Residuals:
Integration notes:
Closure impact:
```

Worker 提醒：

- 你不是独自工作；不要回滚无关改动或其他 worker 的改动。
- 保持写入范围互不重叠。
- 碰到 blocker 应命名后停止，不要扩展到 WP19/WP20/WP21。
