# A7 当前状态

状态：`2026-06-04` active implementation。A7 已选定 objective contract，并完成
`A7-EVC-C Policy Head Prototype`；PPO auxiliary credit 是下一实现切片。

父级：[README.zh.md](README.zh.md)。

## 本检查点

- A3 已作为 accepted C2/ROE evidence packet 归档，并通过 pointer README 保持可达。
- A6 在 root-cause analysis 后继续 held；L tuning 暂停。
- A7 开启，用于实现 counterfactual event-value / advantage credit。
- Objective contract 已选定：
  [a7_event_value_advantage_credit_head_objective_contract_20260604.zh.md](a7_event_value_advantage_credit_head_objective_contract_20260604.zh.md)。
- `A7-EVC-C Policy Head Prototype` 已完成：zero-safe `hybrid_event_credit_head`
  API 已暴露，并由 focused HMoE policy tests 覆盖。
- HMoE hierarchical computation gap 被记录为 architecture risk：A7 不应只依赖 hard-routed
  subexpert behavior。

## 成熟度矩阵

| Surface | 状态 | 证据 | 边界 |
| --- | --- | --- | --- |
| A7 docs | active | README/task clusters/current status/dispatch/acceptance/objective contract 已存在。 | 仅 documentation 与 dispatch surface。 |
| Objective contract | pass | 已选合同定义 counterfactual target semantics、window balancing、head placement、loss coupling、diagnostics 与 rollback gates。 | 只授权 focused implementation，不释放 broad architecture。 |
| Policy head prototype | pass | `python/rl/policy_algo/policies.py` 暴露 `hybrid_event_credit_head_lr_scale`、`get_hybrid_event_credit()` 与 distribution-side credit values；`tests/hmoe/test_hmoe_policy.py` 覆盖 default-off、zero init、optimizer lane、A6 coexistence、load smoke 与 bootstrap zeroing。 | 不声明 PPO auxiliary loss 或 training 已完成。 |
| PPO implementation | not started | 切入点仍是 `first_event_hazard.py` 与 `ppo_adaptive_kl.py`。 | `A7-EVC-D` 持有 loss coupling 与 target handling。 |
| HMoE relation | watch item | issue board 记录 flat subexpert input 与 combat-family collapse。 | 除非证据强迫新任务，A7 不修 HMoE。 |

## 立即下一步

分发 `A7-EVC-D PPO Auxiliary Credit`：训练 A7 head，并在不削弱 A3/A5 masks 的前提下
将 advantage signal 接到 event-logit updates。

## 验证快照

- `python -m compileall -q python/rl/policy_algo/policies.py`：pass。
- `pytest tests/hmoe/test_hmoe_policy.py -q`：pass，`31 passed`。
- `pytest tests/hmoe/test_a6_event_head_update_strength.py -q`：pass，`3 passed`。
- `git diff --check -- python/rl/policy_algo/policies.py tests/hmoe/test_hmoe_policy.py`：pass。

## Held Items

- M2 release。
- HMoE redesign 或 soft routing。
- Missile/Pk/fuze/damage authority。
- `2v2`、self-play 与 real doctrine。
