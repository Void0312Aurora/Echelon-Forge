# A7 验收门

状态：`2026-06-04` defined；`A7-EVC-C` policy-head prototype 已评估。

父级：[README.zh.md](README.zh.md)。

## 可验收范围目标

A7 验收仅限于证明：在既有 A3/A5 legal event surface 下，event-value / advantage-credit
机制能够教会 first-event timing。

## Gate Matrix

| Gate | Required outcome | Current state |
| --- | --- | --- |
| Objective contract | A7 target 提供 counterfactual hold/fire credit，并命名 target source。 | pass：[objective contract](a7_event_value_advantage_credit_head_objective_contract_20260604.zh.md) |
| Policy head prototype | Head shape、zero init、optimizer lane、default-off behavior、serialization/load 与 A6 coexistence 有测试覆盖。 | pass：`tests/hmoe/test_hmoe_policy.py` |
| PPO auxiliary credit | Loss、masks、finite stats 与 event-logit coupling 有测试覆盖。 | pass：`tests/hmoe/test_a6_event_head_update_strength.py`、`tests/hmoe/test_hmoe_ppo_warmup.py` |
| Config/diagnostics | Active entries 与 callback/process-probe metrics 暴露 A7 credit behavior。 | not started：由 `A7-EVC-E` 持有 |
| Legality boundary | A3/A5 masks 与 state machine 继续持有权威。 | required |
| HMoE risk handling | HMoE gap 在 head placement 与 diagnostics 中被考虑。 | partial：A7-C 将 credit 保持在 policy-head level，且不重设计 HMoE |
| Learned evidence | Deterministic 在 quality window 内单发；stochastic early hazard 有界。 | not evaluated |
| Overclaim refusal | M2、HMoE redesign、missile authority、`2v2`、self-play 与 doctrine 继续 held。 | required |

## 失败条件

若出现以下情况，A7 继续 held 或必须 re-scope：

- implementation 只改变 L weights 或 generic reward magnitude；
- advantage head 只是 diagnostic-only，不能影响 event logits 或 policy updates；
- early stochastic release 仍然 censor quality-window targets，且没有 counterfactual repair；
- deterministic 再次在 authorization/contact 后近立即发射；
- stochastic probing 破坏 one-shot release discipline；
- 在没有 A7 evidence 的情况下，用 HMoE gap 正当化 broad architecture rewrite。

## 验证命令

Initial docs gate：

```bash
git diff --check -- docs/task/air_combat docs/task/issues
```

`A7-EVC-B` 已选择 implementation gates：

- policy head shape、zero initialization 与 constructor serialization tests；
- pre-quality、quality、early accepted 与 shadow-quality cases 的 first-event credit
  label tests；
- PPO auxiliary-loss finite-value 与 mask-handling tests；
- event advantage signs 与 cumulative pre-window hazard 的 diagnostics tests；
- active config parsing 以及 focused compile/JSON gates。

`A7-EVC-C` focused gates：

```bash
python -m compileall -q python/rl/policy_algo/policies.py
pytest tests/hmoe/test_hmoe_policy.py -q
pytest tests/hmoe/test_a6_event_head_update_strength.py -q
git diff --check -- python/rl/policy_algo/policies.py tests/hmoe/test_hmoe_policy.py
```

观察结果：compileall 通过；HMoE policy tests 为 `31 passed`；A6 event-head
update-strength tests 为 `3 passed`；diff whitespace check 通过。

`A7-EVC-D` focused gates：

```bash
python -m compileall -q python/rl/policy_algo/first_event_hazard.py python/rl/policy_algo/ppo_adaptive_kl.py
pytest tests/hmoe/test_a6_event_head_update_strength.py -q
pytest tests/hmoe/test_hmoe_ppo_warmup.py -q
pytest tests/hmoe/test_hmoe_policy.py -q
```

观察结果：compileall 通过；event-head/credit gradient tests 为 `5 passed`；
HMoE PPO warmup tests 为 `8 passed`；HMoE policy tests 为 `31 passed`。
