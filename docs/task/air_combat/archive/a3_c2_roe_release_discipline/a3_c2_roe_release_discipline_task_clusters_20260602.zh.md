# A3 C2/ROE 发射纪律任务簇

状态：`2026-06-03`，用于
[README.zh.md](README.zh.md) 的 A-H pass 任务簇记录。

英文规范页：
[a3_c2_roe_release_discipline_task_clusters_20260602.md](a3_c2_roe_release_discipline_task_clusters_20260602.md)

## Boundary Decision

A3 允许增加空战 C2/ROE 合同、观测面、奖励/诊断项和 S1 probe 入口。A3 不允许
宣称保密 ROE、真实 BVR shot doctrine、Pk authority、导弹物理 authority 或
sequence-native policy release。重复发射必须先放到显式 command state 下分类，
再作为 M2 证据使用。

## Finite Task Cluster List

| Cluster | Owner | Model / reasoning | Goal | Write set | Non-goals | Validation | Closure gate | Dependency / parallel | Round cap | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `A3-ROE-A Source And Boundary` | main thread 或只读 diagnostics worker | n/a | 记录公开 C2/ROE 术语和不可声明内容。 | `docs/task/air_combat/a3_c2_roe_release_discipline/*source*`、README 来源章节 | 保密战术、真实发射纪律、复制手册长文 | 链接/来源审查、`git diff --check` | 来源扫描链接稳定资料并记录边界。 | 与 B 并行；C 前串行验收。 | 1 | pass |
| `A3-ROE-B Code Surface Audit` | 只读 diagnostics worker | n/a | 盘点现有 mission command、观测、奖励、场景、配置和诊断面。 | 仅 A3 文档 | 代码修改、超出切入点地图的实现设计 | 文件/行号审查、`rg` audit | 切入点表列出文件、测试和残余。 | 与 A 并行；C/D/E 前串行验收。 | 1 | pass |
| `A3-ROE-C Schema Contract` | main thread | n/a | 定义 `air_combat_c2_roe_v1` 字段、值域、状态转换和 fail-closed 默认值。 | A3 README/任务文档、`python/mission_obs_taxonomy.py` | runtime C2 层级、数据链、完整空防模型 | 文档审查、字段表一致性检查 | 合同能区分 hold、tight/free、engage、cease/abort、shot policy 和 pending assessment。 | 依赖 A/B。 | 2 | pass |
| `A3-ROE-D Observation Wiring` | integration worker | n/a | 将合同暴露给策略观测。 | `python/mission_obs_taxonomy.py`、`gym_envs/scenario_loader/mission_observation.py`、observation/space tests | PPO/model 改写、仅 reward 可见的隐藏状态 | mission-observation 字段和 shape 测试 | `mission_obs_mode=air_combat_c2_roe_v1` 在单 env 和 world-batch 路径返回稳定字段。 | 依赖 C；合同冻结后可早于 E。 | 2 | pass |
| `A3-ROE-E Reward And Diagnostics` | integration worker | n/a | 增加 ROE hold、未授权开火、授权首发、过早第二发、齐射和再攻击奖励/诊断项。 | `gym_envs/scenario_loader/reward_runtime/air_combat.py`、diagnostics/probe 文件、focused tests | 把静默吞掉发射动作作为主要修复、导弹物理修改 | reward 单测、process-probe 指标检查 | 指标能把重复发射拆分为授权和违规类别。 | 依赖 C；可与 D 并行。 | 2 | pass |
| `A3-ROE-F Scenario Config Probe` | worker | n/a | 增加 S1 C2/ROE probe 场景和配置入口。 | `scenarios/air_combat/1v1/**`、`examples/config/training/active/air_combat/**`、训练入口测试 | Stage-2/3 战术、自博弈、红方武器扩展 | bootstrap tests 和短程确定性 probe | probe 可运行并输出预期 C2/ROE 指标。 | 依赖 D/E。 | 2 | pass |
| `A3-ROE-G M1 Evidence Review` | main thread | n/a | 在 A3 可观测后重新解释 M1 重复发射证据。 | `docs/task/model/m1_temporal_window_hmoe/**`、可选 A3 证据文档 | M2 实现 | 对比 reactive/temporal probe 指标 | 基于 A3-aware evidence 维持 held 或形成 M2 release vote。 | 依赖 F/P4 evidence。 | 1 | pass |
| `A3-ROE-H Closure And Index Sync` | main thread | n/a | 同步父 README、残余、archive 指针和验收状态。 | `docs/task/air_combat/README*`、A3 README/status 文档、相关 model README | 新功能范围 | `git diff --check` 与文档链接检查 | 维护文档中的 status line 和 residual map 一致。 | 最终串行簇。 | 1 | pass |

当前 A-F 说明：A 为 `pass`，因为公开来源扫描记录了术语与不可声明边界。B 为
`pass`，因为代码表面扫描已盘点 mission command、observation、reward、scenario、
config 和 process-probe 切入点。C 为 `pass`，因为字段顺序、值域和 fail-closed
默认值已经文档化并注册。D 为 `pass`，因为 taxonomy、CLI、single-env loader observation 路径以及
`WorldBatchVecEnv.reset()` 的 mission slot 都已暴露稳定的 `air_combat_c2_roe_v1`
字段。E 为 `pass`，因为 additive reward 和 process-probe bucket 已能拆分授权发射、
未授权/违规发射、pending assessment、shot budget、hold-fire、salvo、reattack 与
legacy fallback。F 为 `pass`，因为 S1 C2/ROE 场景/配置对可 bootstrap，保留既有
M1 baseline 的 `basic`，启用 C2/ROE reward gate，并且短程 process probe 已输出授权
C2/ROE 发射指标。

当前 G 说明：G 为 `pass`，因为 P4 process probe 在同一个 S1 C2/ROE 合同下记录了
授权单发（`forced_fire`）和重复违规发射（`switch_explore`）。M2 继续 held，因为这
不是 learned temporal-policy 验收。

当前 H 说明：H 为 `pass`，因为父级空战 README、A3 README、任务簇、M1 current-status
文档和 M1 temporal 入口现在一致记录：有边界的 A3 C2/ROE 层 accepted，但 M2 在
learned-policy 训练/评估证据前继续 held。

## Dispatch Rules

- 每个 worker packet 必须只对应上表一个 cluster。
- 不允许两个 worker 同时修改同一个 mission-observation 合同、ROE 值表、训练配置对或 status line。
- 来源和代码扫描可以并行；合同与实现必须等待二者验收。
- acceptance、M1/M2 解释和父索引同步必须串行。
- 若某 cluster 超过 round cap，停止并重新划分范围，不直接追加新 wave。
- 遵守仓库 subagent 使用规范；不得创建新的 Codex 会话线程。

## Worker Packet Requirements

```md
status: pass | partial | blocked | failed
touched files:
commands/outcomes:
remaining paths:
behavior risks:
integration notes:
```

## Validation Plan

最新本地验证：

```powershell
git diff --check -- docs/task/air_combat docs/task/model
.\tools\maintenance\cmo_env.ps1 validate-rl
.\tools\maintenance\cmo_env.ps1 python -m pytest -q `
  tests/runtime/air_combat/test_air_combat_c2_roe_mission_observation.py `
  tests/runtime/air_combat/test_air_combat_reward_surface.py `
  tests/runtime/core/test_env_config.py `
  tests/runtime/mission/test_mission_obs_taxonomy.py `
  tests/runtime/air_combat/test_diagnostics_probe_contracts.py `
  tests/training/test_air_combat_training_entry_contracts.py `
  tests/world_batch/test_world_batch_vec_env.py::WorldBatchVecEnvTests::test_world_batch_vec_env_uses_air_combat_c2_roe_python_owned_mission_observation
.\tools\maintenance\cmo_env.ps1 python train.py `
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json `
  --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_shaped_world_batch_probe_v1.json `
  --test_only
# 已 bootstrap 到 mission_obs_mode=air_combat_c2_roe_v1；随后停在预期的
# --test_only requires --resume_path 边界。
```

## Acceptance Standards

- A3 不把公开术语写成保密战术或校准的真实发射纪律。
- 策略能观测做出 fire/no-fire 决策所需的 command state。
- 重复发射证据能区分授权齐射/再攻击与过早第二发或未授权开火。
- M1/M2 决策引用 A3-aware 指标，而不是只看原始 missile count。

## Residual Map

| Residual | Owner | Exit condition |
| --- | --- | --- |
| Self-defense override | 未来空战 C2 扩展 | S1 单机合同 accepted，且定义 threat/self-defense tests。 |
| 长机/僚机授权委派 | 未来多机任务 | A3 单机 command 语义稳定。 |
| 数据链/外部传感器 | 未来 sensor/C2 任务 | contact provenance 与 assigned-target source 语义进入维护路径。 |
| 完整 no-fire/friendly 逻辑 | 未来 ROE safety 任务 | friendly track identity 与 no-fire zones 有 runtime facts 和 tests。 |
| M2 sequence-native policy | model 工作线 | A3-aware evidence 在 command 约束后仍显示记忆/序列缺口。 |
