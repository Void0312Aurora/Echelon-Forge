# M3-S2 Learned-Policy 可达性探针

父级：[README.zh.md](README.zh.md)。

状态：`2026-06-05` evidence update；记录 oracle sweep 证明可达 winning shots 后，
learned policies 为什么仍然选择 no-fire。

## 问题

full delay sweep 证明环境/reward surface 中存在合法发射时刻，可以产生 effects、damage
与 terminal combat wins。剩余问题因此不是“物理上能不能发射”，而是 learned policy
能否通过 hybrid action contract 表达一个 supported `fire_once` event。

可执行链路是：

```text
observation/history
  -> actor event logits: [hold, fire_once]
  -> deterministic categorical mode or stochastic sample
  -> action[9] > 0.5
  -> C2/ROE fire_mask gate
  -> missile release
```

代码证据：

- `python/rl/policy_algo/policies.py`：`air_combat_hybrid_v1` 使用 action index
  `9` 作为 event action；deterministic mode 对 `[hold, fire]` 取 `argmax`，
  stochastic mode 从 categorical event 中采样。
- `gym_envs/universal_env_parts/air_combat_event_action.py`：runtime 只有在
  `action[9] > 0.5` 且 `fire_mask` 打开时接受 `fire_once`，随后记录一次 accepted event，
  并在 pending assessment 期间抑制后续 first-shot release。
- `python/rl/policy_algo/m3s1_grouped_stopping.py`：M3 stopping head 是辅助
  hazard/loss head；当前被探测的 policy 不会自动把该 head 转换成 executable
  `fire_once` action。

## 探针产物

M3-S1 state-completed 8k model：

```text
experiments_tmp/m3s1_p5_state_completed_8k_20260605_r1/final_model.zip
experiments_tmp/m3s1_p5_state_completed_8k_20260605_r1/m3s1_deterministic_probe.json
experiments_tmp/m3s1_p5_state_completed_8k_20260605_r1/m3s1_stochastic_probe.json
experiments_tmp/m3s1_p5_state_completed_8k_model_probe_deterministic_20260605.json
experiments_tmp/m3s1_p5_state_completed_8k_model_probe_stochastic_20260605.json
```

A7 conservative safe-bias 8k model：

```text
experiments_tmp/a7_event_policy_margin_safe_bias_8k_20260605_r1/final_model.zip
experiments_tmp/a7_event_policy_margin_safe_bias_8k_20260605_r1/deterministic_probe.json
experiments_tmp/a7_event_policy_margin_safe_bias_8k_20260605_r1/stochastic_probe.json
experiments_tmp/a7_event_policy_margin_safe_bias_8k_model_probe_deterministic_matched_20260605.json
experiments_tmp/a7_event_policy_margin_safe_bias_8k_model_probe_stochastic_matched_20260605.json
```

直接读取模型属性可确认训练对象保留了配置中的 A7/M3 knobs：

| Model | `a7_event_policy_margin_coef` | `a7_event_policy_projection_margin_coef` | `m3s1_grouped_stopping_coef` | Event head | Credit head | M3 head |
| --- | ---: | ---: | ---: | --- | --- | --- |
| M3-S1 state-completed 8k | `0.35` | `0.15` | `1.0` | yes | yes | yes |
| A7 safe-bias 8k | `0.35` | `0.15` | `0.0` | yes | yes | no |

## Learned-Policy 结果

deterministic probes：

| Model | Episodes | Accepted releases | Open-mask steps | Mean fire probability | Max fire probability | Event-mode fire count |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| M3-S1 state-completed 8k | `2` | `0` | `1880`, `1840` | `0.00354`, `0.00345` | `0.00384`, `0.00377` | `0`, `0` |
| A7 safe-bias 8k | `2` | `0` | `639`, `599` | `0.00309`, `0.00288` | `0.00314`, `0.00308` | `0`, `0` |

mask 打开了数百到上千步，但 deterministic categorical mode 始终选择 `hold`。

stochastic probes：

| Model | Episodes | Accepted releases | Release steps | Interpretation |
| --- | ---: | ---: | --- | --- |
| M3-S1 state-completed 8k | `4` | `3` | `[154]`, `[57]`, `[]`, `[451]` | 低概率随机采样，不是 deterministic timing。 |
| A7 safe-bias 8k | `4` | `3` | `[84]`, `[407]`, `[]`, `[18]` | 低概率随机采样，且常在 prewindow。 |

stochastic release 证明 runtime path 在采样到 `fire_once` 时可执行。它不证明 learned
deterministic policy 学到了 stopping boundary。

## Credit/Action 分裂

探针暴露了 value support 与 executable action 之间的分裂：

| Model/probe | Prewindow event fire probability | Quality-window event fire probability | Prewindow credit advantage | Quality-window credit advantage |
| --- | ---: | ---: | ---: | ---: |
| M3-S1 deterministic | `0.003776` | `0.003763` | `0.8122` | `0.8116` |
| A7 safe-bias deterministic ep0 | `0.003098` | `0.003100` | `0.8103` | `0.8109` |
| A7 safe-bias deterministic ep1 | `0.003078` | `0.003078` | `0.8031` | `0.8042` |

credit head 可以给出正的 `fire_once - hold` advantage，但 actor event logit delta
仍然约为 `-5.6` 到 `-5.8`，fire probability 约 `0.3%`。这远低于 deterministic
`argmax` 边界。

M3 stopping head 当前也没有解决这个执行步骤。state-completed deterministic probe
中它报告 `stop_prob = 0.5` 且每一步都 boundary crossing，但 executable event action
仍为 `hold`，没有导弹释放。

## 机制性成因

低 `fire_once` probability 只是观测症状。A7 后续探针定位到的因果链是：

```text
episode-level first-event label
  -> rollout-local / stochastic on-policy support
  -> A7 credit head
  -> detached, tiny Q_fire_once - Q_hold target
  -> event-logit delta
  -> deterministic categorical argmax
```

这条链路有两个失败点。

第一，label function 是 episode-level，而 PPO 在 rollout chunks 上训练。cross-rollout
修复之前，quality window 前的 early stochastic release 会让环境进入 `FiredAssess`；
后续 quality-window shadow-positive labels 在完整 episode 上存在，但 episode 被切成
rollout-local chunks 后会丢失。这解释了早期训练日志中 active A7 labels 归零的现象。

第二，即使 label-support 问题修复后，剩余的 policy contract 仍然太弱。A7 先训练
credit head，然后可选地把 event-logit delta 对齐到 detached credit advantage：

```text
target_delta = stop_gradient(Q_fire_once - Q_hold)
```

post-repair fixed-batch probe 中，这个 advantage 在 prewindow 和 quality rows 上都约为
`0.004`。这不是经过校准的 signed decision target。把 event logits 对齐到它，会把两个区域
都拉向阈值附近，而不是教会“quality 前 hold、quality 内 fire”。同时
`a7_event_credit_delta_align_positive_only=true` 会在 credit head 变负后移除负标签压力，
导致普通 prewindow rows 不能可靠地把 event logits 推到零以下。

offline event-logit probe 排除了基础模型容量是主因。只训练 event head 的 direct labels
仍偏弱，但用 direct signed labels 同时训练 `hybrid_event_head` 与
`mlp_extractor.policy_net` 可以分离窗口：quality rows 进入高 fire probability，
prewindow rows 被强力推负。因此真正根因是 labels、credit、actor representation 与
executable event logits 之间的训练合同，而不是最优发射是否存在或 C2/ROE mask。

## 诊断

当前 no-fire 问题已经收窄到 learned event/action layer：

- 不是 C2/ROE 可达性：mask 打开，oracle/stochastic path 都能 release；
- 不是物理 kill 可达性：full oracle sweep 找到了 effects 与 terminal wins；
- 不是单纯缺少 credit head：probe rows 中 credit advantage 可为正，但它未校准，且没有向
  actor 提供 signed timing discriminator；
- 不是 M3 stopping head 已解决：该 head 除非显式适配到 event action，否则只是诊断/辅助；
- executable actor event logits 仍在 `hold` 一侧，因为 actor/event path 没有用强 signed
  timing target 训练。

这是 event-head 到 executable-event 的 training-contract failure。先前 A7 短训证据已经显示两个坏极端：

- 放松 startup prior 会整体抬高 fire probability，并导致 quality labels 维持前就发生 early
  stochastic releases；
- 恢复 conservative prior 可以保持 one-shot discipline，但 event logits 又太负，无法 deterministic
  release。

## 后果

下一步模型修改不应再是 coefficient sweep。维护合同必须显式打通以下路径之一：

1. stop/event head 到 `fire_mask` 下 executable one-step pulse；
2. 维护 legal-open positive support 的 direct actor event-logit target；
3. 修复 reward contract，避免 terminal timing 被排序到 late wins。

M2 memory 仍是 representation candidate，但本探针显示：如果它的 stopping output 不接到
executable pulse，memory 本身不能解决当前 actuator boundary。
