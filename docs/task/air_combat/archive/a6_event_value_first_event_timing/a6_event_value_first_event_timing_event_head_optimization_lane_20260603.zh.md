# A6 事件头优化通道

状态：`2026-06-03` `A6-EVT-K` 在 implementation、active config wiring 与短训 learned
evidence 上 pass；A6 因 timing quality 继续 held。

父级：[README.zh.md](README.zh.md)。前置审计：
[a6_event_value_first_event_timing_event_head_update_audit_20260603.zh.md](a6_event_value_first_event_timing_event_head_update_audit_20260603.zh.md)。

## 范围

本 slice 为 A5/A6 masked `hold/fire_once` event logits 增加一个由 optimizer 明确持有、
受边界约束的更新路径。它不改变 A3/A5 合法性、导弹物理、damage authority、`2v2`、
self-play 或 M2 release 状态。

实现刻意保留既有 `action_net` 接口。这可以兼容现有 safe-action initialization、测试和
saved-policy constructor 行为。

## 实现

代码：

- `HierarchicalMoEExecutionPolicy` 现在接受 `hybrid_event_head_lr_scale`。
- 当 `hybrid_action_spec="air_combat_hybrid_v1"` 且 `hybrid_event_head_lr_scale > 0` 时，
  policy 创建零初始化的 `hybrid_event_head`。
- 该 head 输出两个 additive deltas，分别加到 event `hold` logit 和 event `fire_once` logit。
- 该 head 拥有名为 `hybrid_event_head` 的专用 optimizer group，且
  `lr_scale=hybrid_event_head_lr_scale`。
- Route diagnostics 暴露：
  - `a6/event_head_enabled`
  - `a6/event_head_lr_scale`
  - `a6/event_head_delta_abs_mean`
  - `a6/event_head_delta_hold_mean`
  - `a6/event_head_delta_fire_mean`
- Parameter diagnostics 暴露：
  - `a6/event_head_params/enabled`
  - `a6/event_head_params/lr_scale`
  - `a6/event_head_params/weight_norm`
  - `a6/event_head_params/bias_norm`
  - `a6/event_head_params/max_abs`

Active config：

- 新增
  `air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_deadline_event_head_shaped_world_batch_probe_v1.json`。
- 它保留 deadline-bootstrap C2/ROE temporal shaped surface，只额外增加
  `policy_kwargs.hybrid_event_head_lr_scale=10.0`。
- 既有 deadline-bootstrap config 保持不变，用作对照。

## 证据

Focused tests 显示：

- event head 零初始化，因此初始 policy behavior 不变。
- event head 获得专用 optimizer group 与 LR scale。
- 在相同 base LR 下，focused hazard-only probe 中 event-head lane 推动 event delta 的速度超过
  当前 shared/HMoE-only path 的五倍。
- active config 与 deadline baseline 分离，并且能通过 `train.py --test_only` bootstrap。

验证命令：

```bash
.venv/bin/python -m pytest -q tests/policy/test_event_head_update_contracts.py tests/policy/test_execution_policy_surface.py
```

Observed：`28 passed`。

```bash
.venv/bin/python -m pytest -q tests/training/test_event_timing_training_config_contracts.py tests/training/test_air_combat_training_entry_contracts.py
```

Observed：`15 passed, 10 subtests passed`。

更宽的 focused validation：

```bash
.venv/bin/python -m pytest -q \
  tests/policy/test_event_head_update_contracts.py \
  tests/policy/test_first_event_timing_contracts.py \
  tests/policy/test_execution_policy_surface.py \
  tests/policy/test_auxiliary_training_updates.py \
  tests/training/test_event_timing_training_config_contracts.py \
  tests/training/test_diagnostics_callback_contracts.py \
  tests/runtime/air_combat/test_diagnostics_probe_contracts.py \
  tests/training/test_air_combat_training_entry_contracts.py \
  tests/training/test_diagnostics_callback_contracts.py \
  tests/runtime/air_combat/test_diagnostics_probe_contracts.py
```

Observed：`77 passed, 10 subtests passed`。

Compile/check：

```bash
python -m compileall -q python/rl/policy_algo tests/policy tests/training
git diff --check -- python/rl/policy_algo tests/policy tests/training docs/task/air_combat examples/config/training/active/air_combat
```

Observed：pass。

Learned-policy evidence：

- [Event-head 短训 learned-policy probe](a6_event_value_first_event_timing_event_head_short_learned_probe_20260603.zh.md)
  完成 `32768` training steps。
- Deterministic probe：first release at step `2`，`1` request，`1` accepted authorized
  release，`0` rejected，`0` violation / repeat / budget issues。
- Stochastic probe：release steps `4`、`42`、`2`；`3/3` accepted authorized releases；
  `0` rejected、violation、repeat 或 budget issues。
- Event-head training diagnostics 约在 `30720` timesteps 跨过 deterministic event argmax，
  open-window fire probability 约 `67.9%`。

## 残余

本 slice 证明 event decision 在当前 A3/A5 surface 下是可训练的。但它仍不是完整 A6
acceptance，因为 learned policy 几乎在 authorization/contact 后立即发射。这会让大部分
deadline/open-window diagnostics 被 vacate，first-event timing quality 仍未证明。

下一步应定义 launch-window / engagement-quality timing contract，而不是继续简单增大
event-head LR。

## Worker Packet

```md
status: pass; held timing residual
touched files:
- python/rl/policy_algo/policies.py
- tests/policy/test_event_head_update_contracts.py
- tests/policy/test_execution_policy_surface.py
- tests/training/test_event_timing_training_config_contracts.py
- tests/training/test_air_combat_training_entry_contracts.py
- examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_deadline_event_head_shaped_world_batch_probe_v1.json
- examples/config/training/active/air_combat/README.md
- examples/config/training/active/air_combat/README.zh.md
- docs/task/air_combat/a6_event_value_first_event_timing/a6_event_value_first_event_timing_event_head_optimization_lane_20260603.md
- docs/task/air_combat/a6_event_value_first_event_timing/a6_event_value_first_event_timing_event_head_optimization_lane_20260603.zh.md
commands/outcomes:
- .venv/bin/python -m pytest -q tests/policy/test_event_head_update_contracts.py tests/policy/test_execution_policy_surface.py -> 28 passed
- .venv/bin/python -m pytest -q tests/training/test_event_timing_training_config_contracts.py tests/training/test_air_combat_training_entry_contracts.py -> 15 passed, 10 subtests passed
- .venv/bin/python -m pytest -q tests/policy/test_event_head_update_contracts.py tests/policy/test_first_event_timing_contracts.py tests/policy/test_execution_policy_surface.py tests/policy/test_auxiliary_training_updates.py tests/training/test_event_timing_training_config_contracts.py tests/training/test_diagnostics_callback_contracts.py tests/runtime/air_combat/test_diagnostics_probe_contracts.py -> 77 passed, 10 subtests passed
- python -m compileall -q python/rl/policy_algo tests/policy tests/training -> pass
- git diff --check -- python/rl/policy_algo tests/policy tests/training docs/task/air_combat examples/config/training/active/air_combat -> pass
- event-head 32k train plus deterministic/stochastic probes -> deterministic crossing 与 one-shot authorized releases；held timing residual
remaining paths:
- 定义 launch-window / engagement-quality timing contract。
behavior risks:
- 更高 event-head LR 已推动 deterministic argmax crossing，并在短探针中保留 one-shot discipline；但如果 label/window semantics 不区分 authorization 与良好 launch timing，它会学习 immediate release。
integration notes:
- 既有 deadline-bootstrap config 仍保留为 A6-EVT-I 直接对照 baseline。
```
