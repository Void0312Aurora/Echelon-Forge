# A6 发射窗口时机契约

状态：`2026-06-04` contract 与 focused implementation pass；learned-policy
evidence 已在单独记录中完成，结果 held。

父级：[README.zh.md](README.zh.md)。

## 范围

`A6-EVT-K` 已证明 masked `hold/fire_once` event decision 可以通过专用
event-head optimizer lane 跨过 deterministic argmax。但 learned release 几乎贴着
authorization/contact 发生，因此 `A6-EVT-L` 将合法授权与发射窗口时机质量分开。

本契约只改变 A6 训练标签。它不改变 A3/A5 runtime 合法性 mask、shot budget、
pending-assessment suppression、武器释放内核、导弹物理、Pk、fuze、damage authority、M2、
`2v2` 或 self-play。

## 契约决策

legal support 与 timing quality 现在是两个谓词：

- Legal window：A3/A5 `AuthorizedReady` 加 policy-facing `fire_once` mask。
- Launch window：legal-window step，同时 policy observation 中存在近期 target contact
  且落入配置的 range gate，并且 legal-window age 达到配置下限。

维护中的 L probe config 使用：

- range gate：`8000 m <= target_range <= 30000 m`；
- max track age：`5 s`；
- legal-window 最小年龄：`32` steps；
- pre-window hold weight：`0.3`；
- early accepted negative weight：`1.0`。

这些数字只是当前 S1 训练探针的有边界 bootstrap 设置，不是真实 BVR doctrine、导弹发射区、
Pk 模型或 weapon authority claim。

## 标签语义

未提供 launch-window 输入时，既有 A6 hazard/deadline label 行为保持不变。

提供 launch-window 输入时：

- 落在 quality window 内的 accepted `fire_once` 仍是 positive first-event label；
- quality window 前的 accepted `fire_once` 变成显式 negative early-accepted label，
  不再是 positive teacher；
- legal-open 但尚未进入 quality window 的步可以获得 weighted hold labels；
- curriculum positives 只在 quality window 内 seeded；
- deadline positives 必须同时满足 launch-window gate 与 deadline age 条件后才发出。

也就是说，A3/A5 runtime 仍可合法接受一次早发 request，但 A6 objective 不再教
“legal 就等于现在 fire”。

## 实现表面

代码/配置变化：

- `python/rl/policy_algo/first_event_hazard.py`
  - 增加 launch-window gated label generation。
  - 增加 source ids `PREWINDOW=5` 与 `EARLY_ACCEPTED=6`。
- `python/rl/policy_algo/ppo_adaptive_kl.py`
  - 增加 launch-window PPO knobs。
  - 从 action selection 所用的同一个 policy observation 中读取 `contacts` 或最新
    `contacts_history` frame，提取 contact quality。
- `python/rl/support/nonfinite_probe.py`
  - 与 PPO rollout collection 保持 non-finite probe parity。
- `python/training_callbacks.py`
  - 记录 launch-window enabled state、pre-window hold count 与 early accepted count。
- `examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_deadline_event_head_launch_window_shaped_world_batch_probe_v1.json`
  - 新增独立 L active probe entry。

## 验证

Focused validation：

```bash
.venv/bin/python -m compileall -q \
  python/rl/policy_algo/first_event_hazard.py \
  python/rl/policy_algo/ppo_adaptive_kl.py \
  python/rl/support/nonfinite_probe.py \
  python/training_callbacks.py
```

Observed：pass。

```bash
.venv/bin/python -m json.tool \
  examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_deadline_event_head_launch_window_shaped_world_batch_probe_v1.json \
  >/dev/null
```

Observed：pass。

```bash
.venv/bin/python -m pytest \
  tests/policy/test_first_event_timing_contracts.py \
  tests/policy/test_auxiliary_training_updates.py \
  tests/training/test_diagnostics_callback_contracts.py \
  tests/training/test_event_timing_training_config_contracts.py \
  -q
```

Observed：`28 passed`。

## 验收与回滚

`A6-EVT-L` 可以视为 contract surface implementation-complete，但这不是 learned-policy
acceptance。`A6-EVT-M` 已完成短训/探针对照，并因 deterministic 未 crossing、stochastic
仍采样早期 authorized releases 而 held。

验收需要证明 deterministic release 不再坍缩到 authorization/contact 后的近立即发射，同时保持
A5 invariants：

- S1 single-shot surface 下每局至多一次 accepted release；
- 零 unauthorized releases；
- 零 repeat 或 shot-budget violations；
- launch-window diagnostics 显示 pre-window negatives 与 quality-window positives 是 live。

回滚条件：若后续 L variants 让 deterministic fire 完全消失，或破坏 A5 release discipline，
则回到 K event-head config，先重新 scope label window 或 value-credit 机制，再考虑任何
runtime legality 变化。
