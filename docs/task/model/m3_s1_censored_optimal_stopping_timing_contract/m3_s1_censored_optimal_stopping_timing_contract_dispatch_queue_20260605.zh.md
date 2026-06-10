# M3-S1 Censored Optimal-Stopping Timing Contract 分发队列

状态：`2026-06-05`，用于
[M3-S1 Censored Optimal-Stopping Timing Contract](README.zh.md) 的 active dispatch queue。

## 分发边界

本队列此前只启动 M3S1-P1 的 evidence gathering。现在 P1-P4 已作为有边界切片
accepted，因此队列打开 P5 diagnostics 与 short-training evidence split。

worker 不得创建新的 Codex conversation thread。subagents 只能作为当前线程下的有边界
worker 使用。

## 当前分发

| Dispatch | Cluster | Worker type | Model / reasoning | Scope | Write set | Output | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `M3S1-D1 Data Censoring Evidence` | `M3S1-P1 Data Censoring Contract` | explorer | inherited / high | 审计 rollout/env/info 路径，推荐 wait-preserving data route 与必要 metadata。 | none；read-only | 已集成进 [P1 Data/Censoring Contract](m3_s1_data_censoring_contract_20260605.zh.md) | pass |
| `M3S1-D2 Group Preservation Evidence` | `M3S1-P1 Data Censoring Contract` | explorer | inherited / high | 审计 rollout buffer/minibatch 行为，说明 episode/window grouping 如何保留到 loss computation。 | none；read-only | 已集成进 [P1](m3_s1_data_censoring_contract_20260605.zh.md) 与 [P2](m3_s1_grouped_stopping_objective_contract_20260605.zh.md) | pass |
| `M3S1-D3 Reward/Loss Boundary Evidence` | `M3S1-P1 Data Censoring Contract` | explorer | inherited / high | 审计 reward runtime、A6/A7 losses 与 C2/ROE gate ownership，识别禁止耦合与安全 handoff。 | none；read-only | 已集成进 [P1 Data/Censoring Contract](m3_s1_data_censoring_contract_20260605.zh.md) | pass |
| `M3S1-P4A Policy Head Skeleton` | `M3S1-P4 Minimal Integration` | worker | inherited / high | 给 HMoE policy surface 增加 optional independent stopping/survival head，并用 focused tests 证明它与 executable event logits 分离。 | `python/rl/policy_algo/policies.py`；focused policy tests only | 已集成进 [P4 dispatch review](m3_s1_p4_dispatch_review_20260605.zh.md) | pass |
| `M3S1-P4B Grouped Evidence/Loss Skeleton` | `M3S1-P4 Minimal Integration` | worker | inherited / high | 增加 grouped evidence dataclasses 与 pure grouped stopping loss helper，落地 P2 survival/event-mass contract。 | `python/rl/policy_algo/` 下新 sibling module；dedicated grouped-loss tests only | 已集成进 [P4 dispatch review](m3_s1_p4_dispatch_review_20260605.zh.md) | pass |
| `M3S1-P4C PPO Auxiliary Integration` | `M3S1-P4 Minimal Integration` | main thread | high | 将 P4A/P4B 串接进 rollout collection 与 auxiliary pass，同时保持 base PPO minibatch flow 不变。 | `python/rl/policy_algo/ppo_adaptive_kl.py`；`tests/policy/test_auxiliary_training_updates.py` | 已集成进 [P4 dispatch review](m3_s1_p4_dispatch_review_20260605.zh.md) | pass |
| `M3S1-P5A Diagnostics Surface` | `M3S1-P5 Diagnostics And Short Training` | worker | inherited / high | 增加/报告缺失的 `m3s1/*` validation diagnostics，用于 stop-boundary movement、early/prewindow mass、no-event mass、grouped-label persistence 与 mask/one-shot legality。 | `python/rl/policy_algo/ppo_adaptive_kl.py`；`tests/policy/test_auxiliary_training_updates.py` | 已集成进 [P5 dispatch plan](m3_s1_p5_dispatch_plan_20260605.zh.md) 与 focused test evidence | pass |
| `M3S1-P5B Short Training Evidence Path` | `M3S1-P5 Diagnostics And Short Training` | explorer | inherited / high | 确认保守短训命令、输出 artifacts、metrics 与 stop criteria，不执行 long formal train。 | none；read-only | 已集成进 [P5 dispatch plan](m3_s1_p5_dispatch_plan_20260605.zh.md) | pass |

## Worker Packet 模板

```md
status: pass | partial | blocked | failed
touched files:
commands/outcomes:
key evidence:
recommended contract clauses:
behavior risks:
integration notes:
```

## 集成规则

主线程已本地复核 D1/D2/D3 引用的 rollout、buffer、reward、C2/ROE、observation 与 policy
表面，并将其集成。P3 已完成，且 P4 已明确打开。

P4-A、P4-B 与 P4-C 已通过本地复核。P5 已 active，但必须保持独立，并且只有
diagnostic 与 short-training gates 存在后，才能声明 learned behavior。任何 P5 worker
都不得修改 reward magnitude、削弱 C2/ROE 或 action masks，也不得把 event-logit delta
当作 primary stopping score。

P5-A 与 P5-B packet 均已返回。主线程拥有规范性 README/status tables、最终集成，以及是否
打开第一份短训 config 的决策。
