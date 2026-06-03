# A4 授权首发训练信号任务簇

状态：`2026-06-03`，面向 [README.zh.md](README.zh.md) 的有限任务簇计划。

## Boundary Decision

A4 可以修改 reward shaping、维护中的 S1 C2/ROE probe knobs、focused tests，以及让
授权首发可训练所需的文档。A4 不修改导弹物理、毁伤 authority、Pk/引信 authority、
弹药 runtime、M2、自博弈，也不声明真实 BVR doctrine。

## Finite Task Cluster List

| Cluster | Owner | Model / reasoning | Goal | Write set | Non-goals | Validation | Closure gate | Dependency / parallel | Round cap | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `A4-SIG-A Boundary` | main thread | n/a | 创建 A4 范围、阶段计划和残余地图。 | `docs/task/air_combat/a4_authorized_first_shot_training_signal/**`、父级空战 README 链接 | 重开 A3 accepted scope 或 M2 | 链接/可读性检查 | README 和任务簇计划存在，父级文档链接它们。 | first，串行 | 1 | pass |
| `A4-SIG-B Reward Surface` | main thread | n/a | 增加可配置的授权武器链 reward terms。 | `gym_envs/scenario_loader/reward_runtime/air_combat.py`、`tests/runtime/air_combat/test_air_combat_reward_surface.py` | 静默吞 fire、物理或弹药修改 | `pytest tests/runtime/air_combat/test_air_combat_reward_surface.py` | terms 受授权与 single-shot 状态约束。 | A 之后 | 2 | pass |
| `A4-SIG-C Scenario Probe` | main thread | n/a | 在维护中的 S1 C2/ROE training-shaped 场景打开保守 shaping knobs。 | `scenarios/air_combat/1v1/*c2_roe_training_shaped*.json`、`tests/training/test_air_combat_active_training_entries.py` | 改动 M1 basic baselines | active-entry pytest | config test 证明 knobs 只在 A3/A4 probe 上打开。 | B 之后；可与 docs 并行 | 2 | pass |
| `A4-SIG-D Short Evidence` | main thread | n/a | 运行 post-change 有边界 learned-policy probe。 | `docs/task/air_combat/a4_authorized_first_shot_training_signal/*probe*.md`，不 stage `experiments_tmp` | 单次运行即声明 accepted | 记录训练/probe 命令 | deterministic/stochastic fire/release 指标与 A3 证据对比。 | B/C tests 之后 | 2 | pass, held outcome |
| `A4-SIG-E Routing Review` | main thread | n/a | 判断 HMoE 是否需要空战 weapons route。 | `python/rl/policy_algo/hmoe_routing.py`、`python/rl/policy_algo/policies.py`、`train.py`、C2 configs、相关 tests/docs | 无证据大改 policy | routing、policy 与 active-entry tests | combat-weapons route 已测试并文档化。 | D 之后 | 2 | pass |
| `A4-SIG-F Binary Diagnostics` | main thread | n/a | 暴露 binary action logits/probabilities，并测试一次有边界 opportunity-penalty reward trial。 | `python/rl/policy_algo/policies.py`、`python/training_callbacks.py`、`tools/diagnostics/air_combat_stage0_process_probe.py`、reward/config tests、A4 evidence docs | failed learned-policy probe 后仍把 reward urgency 当 accepted | focused tests 加 32k/probe evidence | diagnostics 保留；opportunity penalty 已文档化并作为 active default 禁用。 | E 之后 | 2 | pass, held outcome |
| `A4-SIG-G Closure` | main thread | n/a | 同步 A3/M1/M2 决策并收口残余。 | A4 README/status、父级 air-combat README、M1/M2 docs | 无 A4 gate 即释放 M2 | focused tests 和 docs check | accepted/held 状态有证据支撑。 | 最后，串行 | 1 | planned |

## Dispatch Rules

- 每个 worker packet 必须精确映射到上表一个 cluster。
- 不允许两个 worker 同时编辑同一 reward table、scenario、routing contract 或 status line。
- 短训证据和 closure cluster 必须串行。
- 若 cluster 超过 round cap，先停止并重新划分范围。
- 遵从 [Subagent 使用规范](../../../standards/governance/subagent_usage_policy.zh.md)。

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

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q \
  tests/runtime/air_combat/test_air_combat_reward_surface.py \
  tests/hmoe/test_hmoe_routing.py \
  tests/hmoe/test_hmoe_policy.py \
  tests/training/test_air_combat_active_training_entries.py
```

可选短训证据：

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python train.py \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_shaped_world_batch_probe_v1.json \
  --output_base experiments_tmp \
  --run_name a4_authorized_first_shot_routed_retained_temporal_32k_20260603
```

## Acceptance Criteria

- 新 reward terms 默认为 0，只有配置场景受影响。
- reward tests 证明 shaping 在授权首发前窗口给出，并在 single-shot budget 被消耗后停止。
- S1 C2/ROE active entry 仍可发现，且不改变既有 M1 `basic` baselines。
- learned-policy 证据要么证明 deterministic 授权首发，要么把残余收窄到 binary pulse optimization。

## Residual Map

Immediate:

- 转入
  [A5 受约束事件动作模型](../a5_constrained_event_action_model/README.zh.md)，
  而不是继续追加 reward-only pulse target。

Follow-on:

- 只有在 A5 具备显式 event action 语义和 post-launch suppression 后，再运行
  learned-policy evidence。

Deferred:

- M2 release、sequence-native policy、自博弈和真实 shot doctrine。
