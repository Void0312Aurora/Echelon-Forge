# A3 C2/ROE 发射纪律任务簇

状态：`2026-06-02`，用于
[README.zh.md](README.zh.md) 的有限任务簇计划。

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
| `A3-ROE-A Source And Boundary` | main thread 或只读 diagnostics worker | n/a | 记录公开 C2/ROE 术语和不可声明内容。 | `docs/task/air_combat/a3_c2_roe_release_discipline/*source*`、README 来源章节 | 保密战术、真实发射纪律、复制手册长文 | 链接/来源审查、`git diff --check` | 来源扫描链接稳定资料并记录边界。 | 与 B 并行；C 前串行验收。 | 1 | active |
| `A3-ROE-B Code Surface Audit` | 只读 diagnostics worker | n/a | 盘点现有 mission command、观测、奖励、场景、配置和诊断面。 | 仅 A3 文档 | 代码修改、超出切入点地图的实现设计 | 文件/行号审查、`rg` audit | 切入点表列出文件、测试和残余。 | 与 A 并行；C/D/E 前串行验收。 | 1 | active |
| `A3-ROE-C Schema Contract` | main thread | n/a | 定义 `air_combat_c2_roe_v1` 字段、值域、状态转换和 fail-closed 默认值。 | A3 README/任务文档；实现开始后可能包含 `python/mission_obs_taxonomy.py` | runtime C2 层级、数据链、完整空防模型 | 文档审查、字段表一致性检查 | 合同能区分 hold、tight/free、engage、cease/abort、shot policy 和 pending assessment。 | 依赖 A/B。 | 2 | planned |
| `A3-ROE-D Observation Wiring` | integration worker | n/a | 将合同暴露给策略观测。 | `python/mission_obs_taxonomy.py`、`gym_envs/scenario_loader/mission_observation.py`、observation/space tests | PPO/model 改写、仅 reward 可见的隐藏状态 | mission-observation 字段和 shape 测试 | `mission_obs_mode=air_combat_c2_roe_v1` 在单 env 和 world-batch 路径返回稳定字段。 | 依赖 C；合同冻结后可早于 E。 | 2 | planned |
| `A3-ROE-E Reward And Diagnostics` | integration worker | n/a | 增加 ROE hold、未授权开火、授权首发、过早第二发、齐射和再攻击奖励/诊断项。 | `gym_envs/scenario_loader/reward_runtime/air_combat.py`、diagnostics/probe 文件、focused tests | 把静默吞掉发射动作作为主要修复、导弹物理修改 | reward 单测、process-probe 指标检查 | 指标能把重复发射拆分为授权和违规类别。 | 依赖 C；可与 D 并行。 | 2 | planned |
| `A3-ROE-F Scenario Config Probe` | worker | n/a | 增加 S1 C2/ROE probe 场景和配置入口。 | `scenarios/air_combat/1v1/**`、`examples/config/training/active/air_combat/**`、训练入口测试 | Stage-2/3 战术、自博弈、红方武器扩展 | bootstrap tests 和短程确定性 probe | probe 可运行并输出预期 C2/ROE 指标。 | 依赖 D/E。 | 2 | planned |
| `A3-ROE-G M1 Evidence Review` | main thread | n/a | 在 A3 可观测后重新解释 M1 重复发射证据。 | `docs/task/model/m1_temporal_window_hmoe/**`、可选 A3 证据文档 | M2 实现 | 对比 reactive/temporal probe 指标 | 基于 A3-aware evidence 维持 held 或形成 M2 release vote。 | 依赖 F/P4 evidence。 | 1 | planned |
| `A3-ROE-H Closure And Index Sync` | main thread | n/a | 同步父 README、残余、archive 指针和验收状态。 | `docs/task/air_combat/README*`、A3 README/status 文档、相关 model README | 新功能范围 | `git diff --check` 与文档链接检查 | 维护文档中的 status line 和 residual map 一致。 | 最终串行簇。 | 1 | planned |

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

首轮文档验证：

```bash
git diff --check -- docs/task/air_combat docs/task/model
```

后续实现预期验证：

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop \
  ./.venv/bin/python -m pytest -q \
  tests/runtime/mission/test_mission_command_roe_fields.py \
  tests/runtime/air_combat/test_weapon_roe_runtime.py \
  tests/training/test_air_combat_active_training_entries.py
```

实现开始后，还应增加 `mission_obs_mode=air_combat_c2_roe_v1` 与 S1 C2/ROE
process-probe 指标的专项测试。

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
