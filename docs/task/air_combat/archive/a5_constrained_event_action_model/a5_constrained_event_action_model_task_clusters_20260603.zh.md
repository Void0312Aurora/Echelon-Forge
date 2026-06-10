# A5 受约束事件动作模型任务簇

状态：`2026-06-03`，面向
[README.zh.md](README.zh.md) 的有限任务簇计划。

## Boundary Decision

A5 可以修改 S1 C2/ROE 动作合同、观测支持字段、runtime release state machine、
policy event distribution、active probe configs、diagnostics、tests，以及让导弹释放成为
受约束事件动作所需的任务文档。A5 不修改导弹物理、毁伤 authority、Pk/引信 authority、
真实 BVR doctrine 声明、M2 release、self-play 或 `2v2`。

已选长期架构是 state machine + action mask + event head。首版实现优先采用
masked categorical `hold/fire_once`；如果 deterministic timing 仍需要价值比较，再推进
event Q-head；hazard 和 option 模型等 event surface 稳定后再说。

## Finite Task Cluster List

| Cluster | Owner | Model / reasoning | Goal | Write set | Non-goals | Validation | Closure gate | Dependency / parallel | Round cap | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `A5-EAM-A Boundary` | main thread | n/a | 创建 A5 scope、status、dispatch、acceptance、archive 边界和父级链接。 | `docs/task/air_combat/a5_constrained_event_action_model/**`、父级 air-combat README、A4 residual docs | runtime 或 policy 实现 | `git diff --check -- docs/task/air_combat` | 标准文件存在，父级文档链接 A5。 | first，串行 | 1 | pass |
| `A5-EAM-B Surface Audit` | 当前会话 subagent `Lagrange` | inherited model / xhigh，只读审计 | 映射当前 action、observation、reward、policy、diagnostics 和 config 触点。 | A5 status docs，可选 A5 code-scan evidence | contract 冻结前改 runtime | read-only scan 加链接检查 | write-set 和风险图足够支撑实现。 | A 之后；代码修改前可执行 | 1 + 1 repair | pass |
| `A5-EAM-C Event Contract` | main thread | high-reasoning design | 定义 `engagement_state`、`fire_mask`、事件动作、允许转移和 deterministic eval 语义。 | `docs/standards/air/act*.md`、A5 docs、必要的 focused contract tests | 真实 doctrine、导弹物理 | markdown checks 加 contract/unit tests | contract 将合法性和 reward preference 分开。 | B 之后；与 D/E 表格编辑串行 | 1 + 1 repair | pass，tests pending in D/E |
| `A5-EAM-D Runtime State Machine` | 当前会话 subagent `Noether` | inherited model / high，implementation | 实现 `AuthorizedReady -> FiredAssess` fire-once 流程和 post-launch fire suppression。 | `gym_envs/**`、`scenarios/air_combat/1v1/**`、runtime tests | policy distribution、reward-only fix | runtime 和 scenario tests | accepted fire 消费 event，并禁射直到显式 reattack state。 | C 之后；仅通过不重叠写集与 E 并行 | 2 | pass |
| `A5-EAM-E Policy Event Head` | 当前会话 subagent `Hume` | inherited model / high，implementation | 增加 masked event action 语义或 event Q-head，并保持 PPO log-prob/eval 行为正确。 | `python/rl/policy_algo/**`、`python/rl/runtime/**`、HMoE/policy tests | sequence-native M2 或 option-critic | policy forward/evaluate tests、finite entropy/log-prob checks | stochastic 和 deterministic 路径共享同一 masked action support。 | C 之后；仅通过不重叠写集与 D 并行 | 2 | pass |
| `A5-EAM-F Reward And Config Cleanup` | 当前会话 subagent `Noether`，main-thread integration | inherited model / high，implementation | 将 active S1 C2/ROE entries 转到 event-action 语义，并降低 invalid-fire penalty 依赖。 | `gym_envs/scenario_loader/reward_runtime/air_combat.py`、active config JSON、reward/config tests | 用 config change 声明 learned policy 成功 | reward/config tests | 约束由 mask/state-machine 负责；reward 表达结果和时机偏好。 | D/E 最小路径之后 | 2 | pass |
| `A5-EAM-G Diagnostics And Evidence` | 当前会话 subagent `Hume`，main-thread integration | inherited model / high，implementation after read-only pre-audit | 扩展 probe，报告 event state、mask、requested/executed fire、post-launch suppression 和 deterministic/stochastic outcomes。 | `tools/diagnostics/**`、`python/training_callbacks.py`、A5 evidence docs、diagnostics tests | stage `experiments_tmp`、单次 lucky run 即验收 | diagnostics tests 加 focused probes | 证据能区分结构性多发、invalid requests 和 learned hold/fire behavior。 | D/E/F 之后；closure evidence 串行 | 2 | pass |
| `A5-EAM-H Acceptance And Closure` | 当前会话 subagent `Lagrange` pre-audit，main thread closure | inherited model / xhigh，read-only pre-audit before serial closure | 判定 accepted 或 held，同步 A3/A4/M1/M2 和父级 README。 | A5 README/status/acceptance、A4 README residuals、父级 air-combat README、必要时 model docs | 无 A5 gate 即释放 M2 | focused test suite、docs check、learned-policy evidence review | accepted/held 状态有证据支撑，过度声明继续拒绝。 | 最后，串行 | 1 | held closure pending cross-doc sync |

## Dispatch Rules

- 每个 worker packet 必须精确映射到上表一个 cluster。
- 不允许两个 worker 同时编辑同一规范动作表、policy distribution、runtime state-machine
  contract、scenario config 或 status line。
- 不得创建新的会话线程。如果当前会话可用 subagent，只能在上表 write set 内使用。
- boundary、acceptance 和 closure cluster 必须串行。
- 若 cluster 超过 round cap，先停止并重新划分范围，不追加开放式 follow-up wave。
- 遵从 [Subagent 使用规范](../../../../standards/governance/subagent_usage_policy.zh.md)。

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

初始 docs-only validation：

```bash
git diff --check -- docs/task/air_combat
```

预期 focused implementation validation，待 `A5-EAM-B/C` 后细化：

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q \
  tests/runtime/air_combat/test_air_combat_c2_roe_mission_observation.py \
  tests/runtime/air_combat/test_air_combat_reward_surface.py \
  tests/policy/test_execution_policy_surface.py \
  tests/training/test_air_combat_training_entry_contracts.py \
  tests/runtime/air_combat/test_diagnostics_probe_contracts.py
```

learned-policy validation 必须记录 deterministic 与 stochastic probes，且不得 stage
`experiments_tmp`。

## Acceptance Criteria

- accepted S1 C2/ROE policy-facing release 使用受约束事件语义，而不是 raw per-frame
  continuous threshold 或 unconstrained Bernoulli。
- valid event states 之外，illegal fire 不在 action support 中。
- post-launch state 禁止 repeat fire，直到存在显式 reattack permission。
- PPO log-prob、entropy/stats、stochastic sampling 和 deterministic eval 都遵守同一
  event mask。
- diagnostics 能解释 requested versus executed release 和 post-launch suppression。
- learned evidence 要么证明 deterministic authorized first shot，要么记录 reward-only tuning
  之外的显式 held residual。

## Residual Map

Immediate：

- runtime/policy 编辑前先冻结 event contract。
- 在依赖 learned residual event behavior 前，修复 HMoE residual gate load/eval consistency。

Follow-on：

- 如果 masked categorical 后 deterministic timing 仍不稳定，用 event Q-head 做价值比较。
- 等 valid windows 和 event datasets 稳定后，再做 hazard / first-event timing model。

Deferred：

- hierarchical option / option-critic release flow。
- M2 sequence-native policy release。
- `2v2`、self-play 和真实 BVR doctrine claims。
