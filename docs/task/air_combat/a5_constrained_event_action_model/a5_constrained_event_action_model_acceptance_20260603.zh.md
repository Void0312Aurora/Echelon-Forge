# A5 受约束事件动作模型验收门

状态：`2026-06-03`，not accepted。本文在实现开始前冻结验收条件。

## Accepted Scope To Prove

A5 验收对象是 S1 C2/ROE policy-facing weapon release event model。它不验收更广泛的
learned `1v1` tactical maturity，也不释放 M2。

## Required Evidence

| Gate | Required evidence | Status |
| --- | --- | --- |
| Event action support | accepted S1 C2/ROE entry 暴露 `hold/fire_once` 或等价受约束事件语义。 | pending |
| Mask legality | authorized event states 之外，fire 通过 mask/state-machine support 不可用。 | pending |
| Post-launch suppression | accepted `fire_once` 进入 assessment/no-fire state，并阻止 immediate repeat fire。 | pending |
| Explicit reattack path | 后续 fire 需要 `ReattackReady`、salvo 或其他显式 authorization state。 | pending |
| Policy semantics | stochastic sampling、deterministic eval、log-prob 和 entropy/stats 都遵守同一 mask。 | pending |
| Reward boundary | reward 表达 outcome/timing/ammo/track preferences，不承担主要合法性机制。 | pending |
| Diagnostics | probes 能区分 requested、executed、rejected、authorized、violation、repeated 和 post-launch fire attempts。 | pending |
| Learned evidence | deterministic learned policy 执行一次授权首发，或 held residual 被收窄到 reward-only tuning 之外。 | pending |
| Documentation | A3/A4/M1/M2 与父级 air-combat docs 同步，且无过度声明。 | pending |

## Minimum Test Shape

最终验收记录必须包含实际运行命令。预期命令族包括：

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q \
  tests/runtime/air_combat/test_air_combat_c2_roe_mission_observation.py \
  tests/runtime/air_combat/test_air_combat_reward_surface.py \
  tests/hmoe/test_hmoe_policy.py \
  tests/training/test_air_combat_active_training_entries.py \
  tests/diagnostics/test_air_combat_process_probe.py

git diff --check -- docs/task/air_combat docs/standards/air gym_envs python scenarios examples/config/training/active/air_combat tests tools
```

learned-policy probes 必须报告 deterministic 与 stochastic event behavior，且不得 stage
`experiments_tmp`。

## Rejection Conditions

如果出现以下任一情况，A5 必须保持 held：

- accepted S1 C2/ROE policy-facing release path 仍依赖 raw `sigmoid(logit)>0.5`
  或 continuous threshold 来 fire。
- invalid fire samples 仍被预期为 policy 学习合法性的主要方式。
- post-launch repeated fire 只靠 reward penalty 阻止，而不是靠 state 或 action support。
- deterministic 和 stochastic evaluation 使用不同 event semantics。
- 文档暗示导弹物理、Pk/引信、真实 BVR doctrine 或 M2 release authority。

## Residual Policy

如果 masked categorical event semantics 已结构性 accepted，但 learned deterministic timing
仍失败，A5 可以以 held 关闭，并显式创建 event Q-head 或 hazard follow-on。该 follow-on
不得被隐藏成 reward tuning。
