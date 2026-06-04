# A7 分发队列

状态：`2026-06-04` A7 已开启。Objective contract 已选定，`A7-EVC-C Policy Head
Prototype` 已通过；当前队列转入 PPO auxiliary-credit integration。

父级：[README.zh.md](README.zh.md)。任务簇：
[a7_event_value_advantage_credit_head_task_clusters_20260604.zh.md](a7_event_value_advantage_credit_head_task_clusters_20260604.zh.md)。

## Active Queue

| Cluster | Dispatch status | Owner guidance | Write scope | Guard |
| --- | --- | --- | --- | --- |
| `A7-EVC-D PPO Auxiliary Credit` | planned next | implementation worker；训练 A7 head，并将 advantage credit 接到 event-logit updates。 | `python/rl/policy_algo/**`、focused rollout/loss tests。 | 不削弱 A3/A5 masks；focused tests 通过前不跑 learned-policy。 |

## 已完成分发

| Cluster | Result | Evidence | Residual |
| --- | --- | --- | --- |
| `A7-EVC-C Policy Head Prototype` | pass | `hybrid_event_credit_head_lr_scale`、`get_hybrid_event_credit()`、distribution-side `fire_event_q_values()` / `fire_event_advantage()`，以及 default-disabled 与 A6-coexistence tests。 | Head 仅已暴露；PPO loss coupling 仍属于 `A7-EVC-D`。 |

## Still Blocked

| Cluster | Blocker | Unlock condition |
| --- | --- | --- |
| `A7-EVC-E Config And Diagnostics` | 需要 loss/head metrics。 | `A7-EVC-D` passes focused tests。 |
| `A7-EVC-G Short Learned Evidence` | 需要 implementation validation。 | `A7-EVC-F` passes。 |

## Dispatch Packet Template

```md
cluster: A7-EVC-*
scope:
write set:
non-goals:
validation:
return packet:
```

## 集成说明

- 严禁为本工作创建新的会话线程。
- `A7-EVC-A/B` 已由
  [objective contract](a7_event_value_advantage_credit_head_objective_contract_20260604.zh.md)
  关闭。
- `experiments_tmp` 不入 staging。
- 保持 A3/A5 legality 权威。
- 除非另有 release vote 或 issue task，M2 与 HMoE redesign 继续 held。
