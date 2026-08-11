# M3-S1 Data/Censoring Contract

状态：`2026-06-05` pass；已依据 D1/D2/D3 diagnostics packets 与本地复核验收为 P1 合同。

父项目：[M3-S1 Censored Optimal-Stopping Timing Contract](README.zh.md)。

证据包：

- `M3S1-D1 Data Censoring Evidence`：pass。
- `M3S1-D2 Group Preservation Evidence`：pass。
- `M3S1-D3 Reward/Loss Boundary Evidence`：pass。

## 决策

M3-S1 在修改 PPO loss 前，先采用 wait-preserving data route。

近期开局路线：

```text
ordinary on-policy rollout:
  只作为 executed prefix evidence
  如果 early fire 被 accepted，则把 suffix 视为 action-induced censored

wait-preserving probe rollout:
  在数据路线边界强制 continue / suppress executable fire request
  C2/ROE masks 继续权威
  从 mission C2/ROE V2 fields 重构 desirable windows

future optional route:
  如果 simulator ownership 和 tooling 明确，再考虑同 prefix counterfactual replay branch
```

Low-hazard exploration 不能作为第一合同，因为它仍可能采不到足够 delayed desirable windows。

## 当前证据

rollout 路径已经收集 event state：

- `AdaptiveKLPPO.collect_rollouts()` 从 policy observations 与 env info 记录 engagement
  state、fire mask、accepted fire、episode id 与 launch-window state。
- labels 在 rollout 后、returns/advantages 计算前写入 buffer。
- event-action gate 只接受通过 fire mask 的 requested fire。accepted fire 会切到
  `FiredAssess` 并关闭 fire mask。
- mission observation V2 已暴露 `fire_mask_open`、`launch_window_open`、
  `quality_window_ready`、legal/launch window ages、target range 与 target track age。
- first-event buffer 已保存 active、target、weight、source、window age、window id 与
  had-accepted flags。

这些足够启动窄 wait-preserving evidence route，但不足以安全定义 grouped stopping loss。

## 删失语义

设 `tau_fire` 是 episode/window 中首次 accepted executable fire event。

如果 `tau_fire` 早于 desirable window：

```text
observed prefix:     rows t <= tau_fire
unobserved suffix:   no-fire path 上 rows t > tau_fire
training meaning:    prefix survival/no-stop evidence + early-event penalty
not allowed:         把 unobserved suffix 当作 ordinary negative rows
```

如果 wait-preserving probe 到达 desirable window：

```text
observed window:     legal-open / launch-open / quality-ready rows
training meaning:    desirable window 内的 positive stop mass support
not allowed:         没有 projection/source metadata 时，用 closed-mask shadow row
                     训练 executable fire logits
```

如果 horizon 前没有 desirable window：

```text
training meaning:    到 observed end 为止的 no-event / survival evidence
not allowed:         从 reward magnitude 发明 positive stop labels
```

## 必需元数据

每个 M3-S1 timing evidence row 或 group 必须标识：

| Field | Purpose |
| --- | --- |
| `row_index` | 用于连接 observations/actions/labels 的稳定 flattened row id。 |
| `step_idx` | rollout fragment 内有序 timestep。 |
| `env_idx` | 环境槽。 |
| `episode_id` | 跨 rollout fragments 稳定的 episode id。 |
| `window_id` | 稳定 timing-window id。 |
| `window_age` | 当前 legal/open window 内年龄。 |
| `route_source` | `on_policy`、`forced_hold_probe`、`counterfactual_replay` 或后续支持 route。 |
| `forced_hold` | executable fire 是否为数据收集而被 suppress。 |
| `policy_fire_requested` | 执行 suppression 前的 raw policy intent。 |
| `policy_fire_logit_delta` | candidate boundary 的可选 support diagnostic。 |
| `fire_mask_open` | executable legal fire mask。 |
| `launch_window_open` | desirable launch geometry / track freshness mask。 |
| `quality_window_ready` | timing objective 使用的 desirable window indicator。 |
| `fire_once_accepted` | executed accepted event。 |
| `censoring_kind` | `none`、`early_event_prefix`、`forced_hold`、`timeout` 或 `unsupported`。 |
| `censor_step` | first accepted fire 或 route-specific censor boundary。 |
| `group_start_row` / `group_end_row` | survival/stopping loss 使用的有序 group extent。 |
| `support_horizon` | 支持 candidate stop/no-stop decision 的最后 observed row。 |

当前 A6/A7 labels 尚未把这些字段完整带入 minibatch loss。M3-S1 implementation 必须增加
sidecar grouped evidence object 或等价 group-preserving view。

## 归属条款

- `air_combat_event_action.py` 继续是 execution legality owner。
- `reward_runtime/air_combat.py` 继续是 scalar environment reward owner。
- `ppo_adaptive_kl.py::collect_rollouts()` 与 first-event label attachment 是初始 data
  handoff surface。
- first-event label helpers 可以构建 evidence，但 event-time target interpretation 归
  M3-S1 grouped objectives。
- P1 实现不得削弱 C2/ROE masks、missile authority、one-shot gates 或 action transport
  thresholds 来制造数据。

## 已验收 Worker 发现

D1/D2/D3 packets 被 P1 接受，因为本地复核确认：

- ordinary accepted fire 会改变未来状态，因此同一 trajectory 上的 later no-fire suffix
  不可观测；
- mission V2 已暴露 desirable-window reconstruction 所需 window features；
- PPO minibatches 会 flatten/shuffle first-event fields，因此 grouped timing evidence 需要
  sidecar 或 grouped view；
- reward shaping 只为 scalar return 观察 C2/ROE categories，不拥有 legality 或
  event-time labels。

## 下一合同

P2 必须定义 grouped stopping objective 与承载机制。它不能依赖普通
`rollout_buffer.get(batch_size)` samples 来计算 grouped likelihood。
