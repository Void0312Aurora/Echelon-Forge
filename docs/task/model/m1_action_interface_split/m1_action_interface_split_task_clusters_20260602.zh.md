# M1 动作接口拆分任务簇

状态：`2026-06-02`，用于
[M1 空战动作接口拆分](README.zh.md) 的有限任务簇计划与实现检查点。

## 边界决定

本子项目修复训练动作接口，不修导弹释放物理。现有 runtime gate 可以继续作为物理约束和命令合同检查，
但不能被当成隐藏的战术记忆替代品。

实现上可以为了兼容 SB3 rollout buffer 继续使用 flat numeric transport vector；但验收时必须有显式
hybrid 语义：连续飞行轴、Bernoulli 式开关、categorical 选择器和 pulse release command
必须作为不同的 policy/action-adapter 概念被表示和测试。

## 有限任务簇列表

| Cluster | Owner | Model / reasoning | Goal | Write set | Non-goals | Validation | Closure gate | Dependency / parallel | Round cap | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `M1-AS-A Evidence And Boundary` | main thread | current main thread | 记录为什么 `full` 连续开关维度不利于训练，同时说明 runtime release gate 仍有效。 | `docs/task/model/m1_action_interface_split/**`, `docs/task/model/README*` | 代码实现、M2 release、导弹内核改动 | `git diff --check -- docs/task/model` | README 与 cluster docs 链接父 model 入口并拒绝过度声明 | 首先串行 | 1 + 1 repair | pass |
| `M1-AS-B Action Contract Design` | main thread 或 future integration worker | high-reasoning design | 定义可接受的空战动作面，包括字段名、reset 行为、held 行为、selector 范围、pulse 时长和 `proprio` 语义。 | `docs/standards/air/act.md`, `docs/standards/air/act.zh.md`, `gym_envs/universal_env_parts/spaces.py`, `gym_envs/universal_env_parts/actions.py`, focused tests | 战术记忆、毁伤、导弹发射包线改动 | env-config tests、action adapter unit tests、markdown diff check | 合同命名稳定 mode，并写清所有 switch/pulse 语义 | 在 `M1-AS-A` 之后；和同表实现串行 | 1 + 1 repair | pass |
| `M1-AS-C Transition Adapter Probe` | main thread | implementation | 增加 Box-compatible action-mode adapter 路径，验证 pulse/effective-action 行为。 | `gym_envs/universal_env_parts/actions.py`, `gym_envs/universal_env.py`, `python/rl/runtime/world_batch_vec_env.py`, active air-combat probe config, runtime tests | Gym Dict action-space 迁移、导弹释放内核改动 | action adapter tests、world-batch action/proprio tests、training bootstrap test | held `fire_weapon` policy command 只产生 rising-edge 单帧 release intent；effective action 写入 `proprio` | 在 `M1-AS-B` 之后 | 1 + 1 repair | pass |
| `M1-AS-D Hybrid HMoE Action Distribution` | main thread | high-reasoning implementation | 实现 policy 侧混合动作语义：连续飞行轴 + 离散开关/选择器/pulse 命令，同时保持 PPO log-prob 正确。 | `python/rl/policy_algo/policies.py`, HMoE tests | sequence-native PPO、recurrent hidden state、M2 Causal Transformer 实现 | HMoE forward/evaluate tests、PPO smoke、non-finite probe | 新 surface 的 joint log-prob、deterministic mode 和 action shape 有测试；熵沿用 sampled fallback | 在 `M1-AS-B` 后 | 1 + 1 repair | pass |
| `M1-AS-E Runtime Surface Wiring` | main thread | implementation | 将已接受动作面接入 `UniversalEnv`、`WorldBatchVecEnv`、temporal history 和 compiled observation bridge。 | `gym_envs/universal_env.py`, `python/rl/runtime/world_batch/state.py`, `python/rl/runtime/world_batch_vec_env.py`, world-batch tests | naval action modes、cooperative weapon release、导弹释放内核 | world-batch temporal/action/proprio tests、single-env compatibility tests | reset/done/terminal observation 与 last-action history 在维护路径一致 | 在 `M1-AS-B` 后；和 `M1-AS-D` 同步 | 1 + 1 repair | pass |
| `M1-AS-F Active Probe Migration` | main thread | implementation | 增加使用新动作接口的 stage-1 active 空战配置，并和 `full` baseline 配对。 | `examples/config/training/active/air_combat/**`, `tests/training/test_air_combat_active_training_entries.py`, 本子项目 docs | learned-policy acceptance、长训声明 | training-entry pytest、`train.py --test_only` bootstrap、实现可用时的短 smoke | 配置使用相同 scenario、seed 规则和 temporal/reactive extractor 设置 | runtime path 通过后 | 1 + 1 repair | pass |
| `M1-AS-G Diagnostics And Acceptance` | main thread integration | evidence review | 记录 action reachability、launch attempts、invalid fire attempts、repeated launch interval，以及和 M1 temporal history 的交互证据。 | `tools/diagnostics/**`, `docs/task/model/m1_action_interface_split/**`, M1 evidence docs | M2 实现、战术记忆板、广泛空战成熟度声明 | 聚焦 diagnostics、`git diff --check`、已链接测试结果 | 写入 accepted 或 held residual，父 README 保持同步 | 在 `M1-AS-F` 后；closure 串行 | 1 review + 1 repair | pass |

## 派发规则

- 每个 worker packet 必须只映射到上表一个 cluster。
- 不允许两个 worker 同时编辑同一个规范动作表、policy distribution、训练配置配对或 status line。
- `M1-AS-A` 和 `M1-AS-G` 保持串行。
- 本项目不得创建新的会话线程。若当前环境可用 worker/subagent，必须遵循仓库 subagent policy 和上表写集。
- 如果某个 cluster 超过 round cap，先停止并重划范围，不追加开放式 wave。

## Worker Packet 要求

```md
status: pass | partial | blocked | failed
touched files:
commands/outcomes:
remaining paths:
behavior risks:
integration notes:
```

## 验证计划

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/runtime/core/test_env_config.py
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/world_batch/test_world_batch_vec_env.py -k "action or temporal_history"
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/hmoe/test_hmoe_policy.py tests/hmoe/test_hmoe_ppo_warmup.py
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/training/test_air_combat_active_training_entries.py
git diff --check -- docs/task/model docs/standards/air gym_envs python examples/config/training/active/air_combat tests tools
```

更窄 cluster 可以运行更小的 focused subset，但验收记录必须写明实际运行了哪些命令、哪些命令有意推迟。

## 2026-06-02 Worker Packet Summary

```md
status: pass
touched files:
  gym_envs/universal_env_parts/spaces.py
  gym_envs/universal_env_parts/actions.py
  gym_envs/universal_env.py
  python/env_config.py
  python/rl/policy_algo/policies.py
  python/rl/runtime/world_batch/state.py
  python/rl/runtime/world_batch_vec_env.py
  train.py
  examples/config/training/active/air_combat/**
  tests/runtime/core/test_air_combat_hybrid_action.py
  tests/hmoe/test_hmoe_policy.py
  tests/hmoe/test_hmoe_ppo_warmup.py
  tests/training/test_air_combat_active_training_entries.py
commands/outcomes:
  python -m py_compile ...: pass
  pytest focused hybrid/runtime/HMoE/training entries: 40 passed
  pytest expanded bootstrap + hybrid/runtime/HMoE/training entries: 46 passed
  git diff --check scoped paths: pass
  32-step hybrid smoke train: pass
  1000-step hybrid load/predict/step smoke: pass
  Stage-1 hybrid range-gate action metrics: pass, release_count=1, invalid_fire_attempt_count=0
  Stage-1 full range-gate baseline: pass, same first_fire/release=1233
remaining paths:
  learned policy still needs shaping/curriculum before weapon-employment acceptance
behavior risks:
  entropy uses sampled fallback because squashed continuous axes have no closed form
  cooperative world-batch path is not part of the active air-combat config route
integration notes:
  no missile physics, damage, ammo, cooldown or tactical memory board changed
```

## 验收标准

- 已接受的空战训练动作面不再把 raw continuous `fire_weapon > 0.5` 当作 policy-facing command。
- switch 和 selector command 有明确 reset、hold 与 repeat 语义。
- `proprio` / `proprio_history` 对 policy intent 和 effective transport action 的语义已定义。
- 若实现 hybrid policy，PPO log-prob 与 entropy 保持正确。
- Stage-0 / Stage-1 probe 配置能在不改变导弹物理、毁伤或 scenario truth 的情况下比较新动作面和旧 `full` 动作面。

## 残余地图

Immediate：

- 将 action-interface acceptance 并入 M1-A4 / M1-A5 evidence review，但 M2 release 继续 held。
- 后续 S1 训练应优先使用 hybrid action interface，并增加 weapon-employment shaping/curriculum。

Follow-on：

- 把成功的动作接口证据并回 M1-A4 / M1-A5 release review，再决定 M2。
- 只有在动作面稳定且策略能表达 intentional pulse 后，才增加 target-engagement memory。

Deferred：

- Sequence-native Causal Transformer PPO。
- 完整 cockpit HOTAS 建模。
- 导弹模型、毁伤模型或战术 release-kernel 改动。
