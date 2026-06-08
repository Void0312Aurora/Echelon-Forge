# A4 授权首发 Routing Probe - 2026-06-03

状态：`2026-06-03`，routing 实现证据。A4 仍为 held；本记录不验收 learned policy，
也不释放 M2。

语言：

- 英文规范页：
  [a4_authorized_first_shot_routing_probe_20260603.md](a4_authorized_first_shot_routing_probe_20260603.md)
- 中文辅文：`a4_authorized_first_shot_routing_probe_20260603.zh.md`

## Scope

A4 reward-only probe 已经显示：即便使用 episode 内一次性授权武器链 shaping，
deterministic policy 仍是 `0` fire attempt / `0` release。因此下一步有边界
修改转向 policy mechanics：

- 不再把 `air_combat_c2_roe_v1` mission observation 路由到通用 `nav/vector`；
- 给维护中的 C2/ROE probe 一个真实的 weapons-employment HMoE family；
- 将 pulse-prior 试验与保留的 routing 变更分开处理。

本步骤不改变导弹物理、弹药 runtime、发射包线、毁伤 authority、Pk/fuze authority，
也不声明真实 BVR doctrine。

## Implementation

`python/rl/policy_algo/hmoe_routing.py` 现在增加：

- `FAMILY_COMBAT_WEAPONS = 4`；
- 默认 family counts `[3, 2, 3, 1, 3]`；
- combat subexperts：
  - `weapons_hold`；
  - `authorized_first_shot`；
  - `post_launch_assess`。

20 字段的 `air_combat_c2_roe_v1` mission layout 会在 nav/formation 启发式之前被识别。
路由规则为：

- 当 target contact 存在、允许开火、WCS 非 hold、shot policy active、
  shot budget 仍可用且没有 pending assessment 时，路由到 `authorized_first_shot`；
- 当 pending assessment、own missiles in flight 或 active shot budget 已耗尽可见时，
  路由到 `post_launch_assess`；
- 其余情况路由到 `weapons_hold`。

`python/rl/policy_algo/policies.py` 现在记录以下训练统计：

- `hmoe/fam/combat`；
- `hmoe/sub/combat/hold`；
- `hmoe/sub/combat/first_shot`；
- `hmoe/sub/combat/assess`。

两个维护中的 A3/A4 C2/ROE active config 现在设置：

- `family_subexpert_counts: [3, 2, 3, 1, 3]`；
- `hmoe_head_lr_scale: 0.35`；
- `hmoe_residual_start_factor: 0.25`。

`train.py` 不保留 pulse-prior 放松。后续 routed 32k probe 测试过 naive A4-only
放松，并拒绝了它：它增加违规发射，但没有让 deterministic policy fire。

## Validation

Commands：

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q \
  tests/hmoe/test_hmoe_routing.py \
  tests/hmoe/test_hmoe_policy.py
```

Result：

- `27 passed in 3.70s`。

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q \
  tests/training/test_air_combat_active_training_entries.py
```

Result：

- `9 passed, 8 subtests passed in 13.84s`。

## Interpretation

前一个失败模式现在被拆清楚了：

- reward-only shaping 不足；
- C2/ROE mission semantics 现在进入专用 weapons family，而不是通用 nav/vector route；
- pulse-prior 放松仍只是未接受的假设，不是保留代码。

这仍不是 learned-policy 验收。后续 routed temporal probe 记录在
[a4_authorized_first_shot_post_routing_probe_20260603.zh.md](a4_authorized_first_shot_post_routing_probe_20260603.zh.md)。

## Superseded Next Evidence

原本跟在 routing review 后面的 next evidence command 已被保留的 post-routing run
`a4_authorized_first_shot_routed_retained_temporal_32k_20260603` 和 binary diagnostics
packet 取代：

- [a4_authorized_first_shot_post_routing_probe_20260603.zh.md](a4_authorized_first_shot_post_routing_probe_20260603.zh.md)
- [a4_authorized_first_shot_binary_diagnostics_20260603.zh.md](a4_authorized_first_shot_binary_diagnostics_20260603.zh.md)

M2 继续 held。剩余失败现在收窄到 supervised/curriculum binary pulse optimization
或 route-specific initialization，而不是通用 routing。
