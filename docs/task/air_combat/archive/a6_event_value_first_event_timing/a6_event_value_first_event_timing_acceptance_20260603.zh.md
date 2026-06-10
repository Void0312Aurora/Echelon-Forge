# A6 验收门

状态：`2026-06-04` launch-window short learned evidence 与 root-cause re-scope 后 gate
evaluated；not accepted。

父级：[README.zh.md](README.zh.md)。

## 可验收范围目标

A6 验收只限于：在 S1 C2/ROE 下，通过显式 event-value、hazard 或 first-event timing
objective，让 A5 masked `hold/fire_once` event surface 可训练。

## Gate Matrix

| Gate | Required outcome | Current state |
| --- | --- | --- |
| Objective contract | selected objective 直接针对 masked event timing。 | pass for first contracts 与 L contract：masked first-event hazard、deadline bootstrap、event-head optimization 和 launch-window gated labels。 |
| Legality boundary | A3/A5 masks 与 state transitions 继续持有 legal support 和 post-launch suppression。 | pass；没有恢复 reward-only legality penalties。 |
| Training-kernel tests | Policy/PPO tests 覆盖 objective shape、mask、finite loss/stats、deterministic eval 和 compatibility。 | pass；包含 deadline label/source tests、event-head update-strength diagnostics、event-head optimizer lane tests 与 launch-window label/PPO extraction tests。 |
| Config/diagnostics tests | Active S1 C2/ROE config 暴露 A6 knobs 和 diagnostics，且不恢复 legality-as-penalty defaults。 | pass；包含独立 deadline、event-head 和 launch-window config/logging tests。 |
| Learned evidence | deterministic event probability/mode 相对 A5 baseline 有实质移动，并且要么授权首发一次，要么留下精确 held residual。 | held：launch-window deterministic probe 达到 `34.6% / 35.0%` open-window probability，但 requests 为 `0`；stochastic release steps 为 `7`、`43`、`4`。 |
| Root-cause analysis | 继续训练前先把 held residual 归属到明确机制类别。 | pass：A6-EVT-N 将 blocker 归属到 stochastic hazard accumulation、absorbing first-event censoring 与缺失 counterfactual hold/fire credit。 |
| Overclaim refusal | M2、`2v2`、self-play、missile physics、Pk、fuze、damage authority 和 real doctrine 继续 held。 | active |

## 当前需要击败的 baseline

A5 retained short learned-policy evidence：

- deterministic：`1880` 个 fire-mask-open 步，`0` requests，`0` releases，
  `policy_event_prob_fire_once_mean=0.217%`，max `0.278%`；
- stochastic：`3` episodes 中 `3` 次 authorized releases，`0` violation releases，
  `0` repeat 或 budget violations。

首次 A6 learned-policy probe 保留了 stochastic discipline baseline，但没有实质推动
deterministic `fire_once` probability/mode。

Deadline-bootstrap probe 将 deterministic open-window probability 移动到
`0.494% / 0.496%`，但仍产生 `0` deterministic requests。Stochastic 产生 `3/3` 授权
releases，零 violation/repeat/budget issues，但退化出一次 `weapon_not_ready` rejected request。

Event-head update audit 记录了前一轮 held residual：labels 与 gradients 是 live，但当前
`3e-5` learning rate 加上受抑制的 HMoE residual ownership 太弱，无法把 final event delta
约 `-5.3` 推过 deterministic argmax。

Event-head optimization lane 解决了这个狭义 blocker。32k event-head run 跨过
deterministic argmax，deterministic probe 在 step `2` 执行一次 authorized release；
stochastic probing 在 `3` 个 episodes 中每局一次 authorized release，且无 rejected、
violation、repeat 或 budget issues。A6 仍 held，因为这不是成熟 first-event timing：learned
policy 几乎在 authorization/contact 后立即 release，导致原本希望验证的 deadline/open-window
timing evidence 被 vacate。

Launch-window timing contract 改变 label surface，使 legal authorization 不再天然成为
positive teacher。它加入 pre-window hold labels、early-accepted negative labels、
contact-quality range gating 与独立 active config。这只是 implementation evidence；仍需短训
learned-policy probe 击败当前 baseline。

Launch-window short probe 显示 contract 是 live 的，但未 accepted。Deterministic mode 不再
重复 K-style step-2 release，但也没有跨过 masked argmax：`0` requests、`0` releases，
open-window fire probability 为 `34.6% / 35.0%`。Stochastic mode 仍然每局采样一次
authorized release，steps 为 `7`、`43`、`4`；无 rejected、violation、repeat 或 budget issues。

Root-cause re-scope 将该结果视为 first-event survival/hazard blocker，而不是 L tuning
问题。Stochastic releases 对应的 release 前累计 early-fire probabilities 为 `0.810`、`0.556`
与 `0.625`，但 deterministic mode 仍需要 `fire_once` probability 超过 `0.5` 才能跨过
argmax。Accepted early release 对 first-event window 是吸收事件，因此后续 quality-window
evidence 会在 on-policy 轨迹中被 censor。未来 gate 因此需要 counterfactual hold/fire credit
或 event-time survival objective，再考虑继续训练。

## 失败条件

若出现以下情况，A6 必须保持 held 或重新 scope：

- selected objective 只是改变 generic reward magnitude；
- implementation 绕开或削弱 A5 masks/state transitions；
- deterministic policy 仍为零 `fire_once` requests，且没有记录更强诊断；
- stochastic discipline 退化，且没有具名、有边界的修复路径；
- deterministic crossing 被表述为成熟 timing，但 release 发生在 authorization/contact 后的近立即时刻；
- 文档暗示 M2、missile authority 或真实 tactics 已释放。
- fixed-age deadline 行为被表述为 doctrine 或最终战术成熟度，而不是有边界 bootstrap evidence。
- event-head update diagnostics 被表述为 learned-policy acceptance。
- event-head deterministic crossing 在没有 launch-window timing contract 的情况下被表述为完整 A6 acceptance。
- launch-window held evidence 被表述为 A6 acceptance。
- L range/age bootstrap 数值被表述为 doctrine、missile authority 或最终战术成熟度。
- 在 A7 定义并验证 counterfactual target source、stochastic collection handling 与
  cumulative hazard diagnostics 前启动进一步 L 训练。

## 验证命令

Docs-only initial gate：

```bash
git diff --check -- docs/task/air_combat
```

已执行 implementation validation gate：

```bash
.venv/bin/python -m pytest -q \
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

Observed：`68 passed, 8 subtests passed`。

Deadline focused gate：

```bash
.venv/bin/python -m pytest -q \
  tests/policy/test_first_event_timing_contracts.py \
  tests/training/test_event_timing_training_config_contracts.py \
  tests/training/test_diagnostics_callback_contracts.py \
  tests/training/test_air_combat_training_entry_contracts.py
```

Observed：`26 passed, 9 subtests passed`。

Deadline full A6/diagnostics gate：

```bash
.venv/bin/python -m pytest -q \
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

Observed：`71 passed, 9 subtests passed`。

Event-head update-strength gate：

```bash
.venv/bin/python -m pytest -q tests/policy/test_event_head_update_contracts.py
```

Observed：`2 passed`。

Event-head optimization gate：

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

Launch-window focused implementation gate：

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

Launch-window learned-policy gate：

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python train.py \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_deadline_event_head_launch_window_shaped_world_batch_probe_v1.json \
  --output_base experiments_tmp \
  --run_name a6_launch_window_temporal_32k_20260604 \
  --n_envs 4 \
  --torch_threads 1 \
  --seed 20260641
```

Observed：完成 `32768` timesteps。

Deterministic probe observed `0` requests 与 `34.6% / 35.0%` open-window event
probability。Stochastic probe observed steps `7`、`43`、`4` 的 `3/3` authorized
releases，且 zero rejected / violation / repeat / budget issues。

Root-cause docs gate：

```bash
git diff --check -- docs/task/air_combat/a6_event_value_first_event_timing
```
