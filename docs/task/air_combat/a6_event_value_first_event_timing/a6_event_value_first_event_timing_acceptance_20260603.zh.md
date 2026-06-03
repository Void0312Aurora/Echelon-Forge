# A6 验收门

状态：`2026-06-03` event-head learned evidence 后 gate evaluated；not accepted。

父级：[README.zh.md](README.zh.md)。

## 可验收范围目标

A6 验收只限于：在 S1 C2/ROE 下，通过显式 event-value、hazard 或 first-event timing
objective，让 A5 masked `hold/fire_once` event surface 可训练。

## Gate Matrix

| Gate | Required outcome | Current state |
| --- | --- | --- |
| Objective contract | selected objective 直接针对 masked event timing。 | pass for first contracts：masked first-event hazard 与 deadline bootstrap；下一 contract 必须区分 authorization 与 launch-window quality。 |
| Legality boundary | A3/A5 masks 与 state transitions 继续持有 legal support 和 post-launch suppression。 | pass；没有恢复 reward-only legality penalties。 |
| Training-kernel tests | Policy/PPO tests 覆盖 objective shape、mask、finite loss/stats、deterministic eval 和 compatibility。 | pass；包含 deadline label/source tests、event-head update-strength diagnostics 与 event-head optimizer lane tests。 |
| Config/diagnostics tests | Active S1 C2/ROE config 暴露 A6 knobs 和 diagnostics，且不恢复 legality-as-penalty defaults。 | pass；包含独立 deadline config/logging tests。 |
| Learned evidence | deterministic event probability/mode 相对 A5 baseline 有实质移动，并且要么授权首发一次，要么留下精确 held residual。 | crossing 通过、timing held：event-head deterministic probe 在 step `2` release 一次；stochastic 在 `3/3` episodes 中各 release 一次；timing 收敛到 near-immediate authorization/contact。 |
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

## 验证命令

Docs-only initial gate：

```bash
git diff --check -- docs/task/air_combat
```

已执行 implementation validation gate：

```bash
.venv/bin/python -m pytest -q \
  tests/hmoe/test_a6_first_event_hazard.py \
  tests/hmoe/test_hmoe_policy.py \
  tests/hmoe/test_hmoe_ppo_warmup.py \
  tests/training/test_a6_event_value_active_config.py \
  tests/training/test_a6_event_value_diagnostics_callback.py \
  tests/diagnostics/test_a6_event_value_process_probe.py \
  tests/training/test_air_combat_active_training_entries.py \
  tests/training/test_cooperative_diagnostics_callback.py \
  tests/diagnostics/test_air_combat_process_probe.py
```

Observed：`68 passed, 8 subtests passed`。

Deadline focused gate：

```bash
.venv/bin/python -m pytest -q \
  tests/hmoe/test_a6_first_event_hazard.py \
  tests/training/test_a6_event_value_active_config.py \
  tests/training/test_a6_event_value_diagnostics_callback.py \
  tests/training/test_air_combat_active_training_entries.py
```

Observed：`26 passed, 9 subtests passed`。

Deadline full A6/diagnostics gate：

```bash
.venv/bin/python -m pytest -q \
  tests/hmoe/test_a6_first_event_hazard.py \
  tests/hmoe/test_hmoe_policy.py \
  tests/hmoe/test_hmoe_ppo_warmup.py \
  tests/training/test_a6_event_value_active_config.py \
  tests/training/test_a6_event_value_diagnostics_callback.py \
  tests/diagnostics/test_a6_event_value_process_probe.py \
  tests/training/test_air_combat_active_training_entries.py \
  tests/training/test_cooperative_diagnostics_callback.py \
  tests/diagnostics/test_air_combat_process_probe.py
```

Observed：`71 passed, 9 subtests passed`。

Event-head update-strength gate：

```bash
.venv/bin/python -m pytest -q tests/hmoe/test_a6_event_head_update_strength.py
```

Observed：`2 passed`。

Event-head optimization gate：

```bash
.venv/bin/python -m pytest -q \
  tests/hmoe/test_a6_event_head_update_strength.py \
  tests/hmoe/test_a6_first_event_hazard.py \
  tests/hmoe/test_hmoe_policy.py \
  tests/hmoe/test_hmoe_ppo_warmup.py \
  tests/training/test_a6_event_value_active_config.py \
  tests/training/test_a6_event_value_diagnostics_callback.py \
  tests/diagnostics/test_a6_event_value_process_probe.py \
  tests/training/test_air_combat_active_training_entries.py \
  tests/training/test_cooperative_diagnostics_callback.py \
  tests/diagnostics/test_air_combat_process_probe.py
```

Observed：`77 passed, 10 subtests passed`。
