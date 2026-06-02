# M1 空战动作接口拆分

状态：`2026-06-02`，`accepted`。`air_combat_hybrid_v1` 训练动作接口切片已实现、
通过聚焦测试和短场景 probe；learned `1v1` policy 与 M2 release 仍未验收。

语言：

- 英文规范页：[README.md](README.md)
- 中文配套页：`README.zh.md`

输入：

- [时间 HMoE 策略计划](../temporal_hmoe_policy_plan_20260525.zh.md)
- [M1 观测窗口 HMoE 验证](../m1_temporal_window_hmoe/README.zh.md)
- [A3 C2/ROE 发射纪律](../../air_combat/a3_c2_roe_release_discipline/README.zh.md)
- [Pilot Action Contract](../../../standards/air/act.md)
- 当前动作适配：
  [actions.py](../../../../gym_envs/universal_env_parts/actions.py)
- 当前 world-batch runtime：
  [world_batch_vec_env.py](../../../../python/rl/runtime/world_batch_vec_env.py)
- 当前 HMoE policy：
  [policies.py](../../../../python/rl/policy_algo/policies.py)

## 目的

为 stage-0 / stage-1 空战 probe 暴露出的动作接口问题建立一个有边界的 M1 后续子项目。
当前 `full` 动作面把飞行连续控制和作战开关都塞进同一个连续 `Box`；运行时发射闩锁能防止
按住发射后无限成功连发，但策略仍必须靠不连续阈值去发现雷达、TMS、主武器开关和发射动作。

本子项目把 `1v1` 空战训练面推进到更自然的混合接口：飞行轴保持连续，雷达 /
目标管理 / 主武器开关 / 武器选择 / 武器释放在 policy/action-adapter 边界成为显式离散或
脉冲命令。

## 当前状态

| 区域 | 状态 | 证据 | 边界 |
| --- | --- | --- | --- |
| `full` action mode | 已实现 | `make_action_space("full")` 是 17 维 `Box`；`build_pilot_action()` 对开关维度做阈值。 | 这是维护中的 runtime surface，但不适合作为稀疏开关发现的训练接口。 |
| `air_combat_hybrid_v1` action mode | accepted | 12 维 flat `Box` transport，policy 侧为连续飞行轴 + Bernoulli 开关/脉冲 + categorical 武器选择。 | 为 SB3/runtime 兼容仍是 flat transport；不是 Gym `Dict` action-space 迁移。 |
| 武器释放闩锁 | 已实现 | `PilotWeaponReleaseState` 在一次成功释放后消费 held trigger。 | 能防成功连发；不能把连续阈值动作变成好的策略接口。 |
| M1 temporal history | accepted | hybrid runtime 记录 effective transport action 到 `proprio` / `proprio_history`；raw policy intent 只用于 rising-edge 判定。 | 时间窗口是否改善 learned fire/release 仍属 M1-A4 后续证据。 |
| multi-timescale wrapper | 已有支撑 | `MultiTimescaleActionController` 支持 hold、snap 和 hysteresis。 | 仍是 flat continuous `Box`；可作为过渡 probe，不是真正混合动作分布。 |
| HMoE PPO policy | accepted | `HierarchicalMoEExecutionPolicy(..., hybrid_action_spec="air_combat_hybrid_v1")` 输出 19 维参数并计算 joint log-prob。 | tanh-squashed Gaussian 连续轴没有可靠闭式熵；PPO 熵项沿用 `-log_prob` 采样估计。 |

## 范围

范围内：

- 定义空战训练动作合同，把连续飞行控制、开关、选择器和脉冲语义拆开。
- 增加过渡动作 adapter 或 action mode，让 `1v1` probe 具备明确的 `fire_weapon` pulse 行为，
  并记录 `proprio` 语义。
- 增加或扩展 policy 支撑，让作战开关按 Bernoulli / categorical 命令采样，而不是依赖
  raw Gaussian 动作跨过 `0.5`。
- 一致接通单 env 兼容路径和维护中的 `WorldBatchVecEnv` 训练路径。
- 增加 active 空战 probe 配置和聚焦测试，用相同 stage / seed 规则比较 `full` 与新动作接口。

范围外：

- 导弹物理、制导、引信、毁伤、弹药或冷却改动。
- 在 `src/systems/combat` 中新增战术记忆板。
- 声明已训练 `1v1` policy 通过验收。
- 在 M1 evidence review 前启动 M2 sequence-native PPO。
- 超出当前 `PilotAction` 合同的广泛 HOTAS 建模。

## 阶段计划

| 阶段 | 目标 | 进入条件 | 退出条件 | 状态 |
| --- | --- | --- | --- | --- |
| `P0 Boundary` | 冻结动作接口问题，并和导弹释放内核行为区分。 | 已有 M1-A4 action-stat 证据和 held-trigger runtime 测试。 | README 与任务簇定义范围。 | pass |
| `P1 Source Audit` | 映射 action-mode、config、runtime、policy 和 test 触点。 | `P0` 接受。 | 形成 patch list 与风险图。 | pass |
| `P2 Transition Adapter` | 提供低风险 probe 路径，在不改 PPO distribution 前先去掉 held threshold 歧义。 | `P1` 接受。 | 聚焦测试证明 pulse、effective action 和 proprio 行为确定。 | pass |
| `P3 Hybrid Policy` | 增加 policy 侧混合动作分布，或等价的 joint log-prob flat transport。 | `P2` 有证据。 | HMoE PPO 能用离散开关/选择器头与连续飞行轴训练。 | pass |
| `P4 Air-Combat Probe` | 增加 stage-0 / stage-1 配置和诊断，比较 `full`、transition adapter 与 hybrid policy。 | `P3` 实现通过 smoke。 | 同 seed probe 报告 action reachability、invalid fire 和 repeated launch interval。 | pass |
| `P5 Closure` | 决定修复后的动作接口是否并入 M1 evidence，再进入 M2 release vote。 | `P4` 有证据。 | 记录 accepted 或 held residual，并同步父 model README。 | accepted |

## 任务簇

- 任务簇计划：
  [m1_action_interface_split_task_clusters_20260602.zh.md](m1_action_interface_split_task_clusters_20260602.zh.md)
- 英文规范页：
  [m1_action_interface_split_task_clusters_20260602.md](m1_action_interface_split_task_clusters_20260602.md)

## 输出与证据

- 空战训练动作接口文档更新。
- 开关、选择器和脉冲行为的聚焦 action-adapter 测试。
- 覆盖 `UniversalEnv` 兼容路径与 `WorldBatchVecEnv` 的 runtime 测试。
- 若实现 hybrid distribution，则增加 HMoE policy 测试。
- Stage-0 / Stage-1 active 空战 probe 配置和证据记录。
- 当前检查点：
  [m1_action_interface_split_current_status_20260602.zh.md](m1_action_interface_split_current_status_20260602.zh.md)
- 验收记录：
  [m1_action_interface_split_acceptance_20260602.zh.md](m1_action_interface_split_acceptance_20260602.zh.md)

已运行证据：

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop pytest -q tests/runtime/core/test_air_combat_hybrid_action.py tests/runtime/core/test_env_config.py tests/hmoe/test_hmoe_policy.py tests/hmoe/test_hmoe_ppo_warmup.py tests/training/test_air_combat_active_training_entries.py
# 40 passed

git diff --check -- docs/task/model docs/standards/air gym_envs python examples/config/training/active/air_combat tests train.py
# pass

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop python train.py --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_v1.json --train_config /tmp/cmo_m1_air_combat_hybrid_smoke_config.json --output_base /tmp/cmo_m1_hybrid_smoke_runs --run_name m1_hybrid_smoke_20260602 --n_envs 1 --torch_threads 1 --seed 20260602
# 32-step hybrid smoke train passed; final_model.zip saved

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop python train.py --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_v1.json --train_config /tmp/cmo_m1_air_combat_hybrid_smoke_config.json --output_base /tmp/cmo_m1_hybrid_smoke_runs --run_name m1_hybrid_smoke_eval_20260602 --n_envs 1 --torch_threads 1 --seed 20260602 --test_only --resume_path /tmp/cmo_m1_hybrid_smoke_runs/m1_hybrid_smoke_20260602/final_model.zip
# 1000-step hybrid load/predict/step smoke passed

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop python tools/diagnostics/air_combat_stage0_process_probe.py --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_v1.json --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_hybrid_world_batch_probe_v1.json --mode range_gate_fire --episodes 1 --seed 20260602 --max_steps 2400 --json_out /tmp/cmo_m1_hybrid_range_gate_report.json --csv_out /tmp/cmo_m1_hybrid_range_gate_trace.csv
# pass; fire_attempt_count=1, release_count=1, invalid_fire_attempt_count=0, damage_report_count=1
```

## 验收门

本子项目只有在满足以下条件时才能标为 accepted：

- `fire_weapon` 在已接受 probe surface 中是显式 pulse 或离散命令，而不是含糊的连续阈值。
- radar / master-arm / target-management 开关语义覆盖 reset、held 和 repeated-command 行为，并有测试。
- 新动作接口下的 `proprio` / temporal history 语义已记录。
- 维护中的 world-batch 路径和 training bootstrap 接受新 surface。
- 至少一个 stage-0 或 stage-1 短 probe 能报告新接口下的 action reachability、launch attempts 和 repeated-release 指标。
- 文档仍拒绝导弹物理、毁伤或战术记忆的过度声明。

## 残余与下一步

- 在动作可达性和时间记忆证据分离前，M1-A4 证据不足以释放 M2。
- 32-step smoke 模型 deterministic probe 仍没有发射：`fire_attempt_count=0`、
  `release_count=0`，并以 `failfast_deep_stall` 结束；这证明动作接口已可达，但 learned policy
  质量未验收。
- 65k shaped hybrid 后续训练已恢复飞行稳定性：deterministic final-model probe 到达
  `combat_timeout` 但不发射，stochastic final-model probe 能发射但仍早发/多发。
- “同一目标已有己方导弹在飞时是否再打一枚”先交由 A3 定义 shot policy、
  pending assessment、salvo 和 reattack 授权；只有 A3 约束可观测后仍出现未解释的多发，
  才回到后续 policy/memory package。

## Archive

当前没有 archive 记录。只有当 current README 或 acceptance 文档告诉后续 Agent 从哪里开始时，
历史记录才应移入 `archive/`。
