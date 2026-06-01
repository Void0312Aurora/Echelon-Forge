# WP22-B Python 业务绕过退场

状态：`2026-05-22` 源事实复核已完成；WP22-B 维护中业务退场是 `pass`；`common_core_profile` 与 `loading.py` 现在都是 compatibility-only guard surfaces，raw sim seam 由 C/F compatibility guard lane 负责，而 `command_chain_cache` 中剩余的 import-time `ef_py.TaskOrder` 命中只属于 validation-only follow-up。

输入：

- [WP22 main plan](legacy_compatibility_retirement_wp22_20260522.zh.md)
- [WP22-A fact ledger](wp22_retirement_fact_ledger_cluster_20260522.zh.md)

## 目的

退场仍通过 raw loader/runtime access、raw truth reads、hardcoded air profile
dispatch 或 untyped mission-command dictionaries 绕过已接受运行时架构的维护中
Python 业务路径。本流现在已经完成维护中业务退场；剩余的 `TaskOrder`
import unlock 只是 C/F guard 的 validation-only follow-up。

## 拥有范围

- `python/rl/tasking/leader_tasking.py`
- `python/rl/tasking/bridge.py`
- `python/rl/tasking/common_core_profile.py`
- `python/rl/tasking/*_adapter.py`
- `python/rl/profile/*_profile.py`
- `gym_envs/scenario_loader/` 中的 mission-command loader/runtime-state adapters
- tasking/profile/mission-command 的聚焦测试

本流不编辑 runtime facade C++ internals。

## 必需产出

| 区域 | 必须退场内容 |
|------|--------------|
| Hardcoded air profile | `build_kernel_mission_command(loader)` 通过 bridge/profile selection 路由，而不是直接调用 `_air_profile`。 |
| Direct loader writes | 生产 tasking writes 不再直接调用 `loader.sim.set_task_order`、`set_leader_intent` 或 `set_pilot_report`。 |
| Raw truth reads | 面向 policy 的 tasking reads 使用 maintained observation/information-state surfaces，或显式隔离到 diagnostics path。 |
| Mission command dict | maintained consumers 使用 typed adapter/DTO，而不是开放式 `getattr(loader, "mission_cmd", {})` 模式。 |
| Profile duplication | 在安全处将 shared normalization/dispatch 移到 bridge-owned helpers；air-specific logic 离开 common core。 |
| Monkey patching | 生产中的 `ef_py =` monkey patching 必须移除或以窄 import boundary 隔离；测试本地 stub 允许存在，但剩余的 `command_chain_cache` import-time `TaskOrder` unlock 只算 validation-only follow-up。 |

## Gate

只有 architecture tests 能区分 maintained tasking paths 与 compatibility diagnostics，
并且对新的 production `loader.sim.*` writes 失败时才通过。

## 建议验证

```bash
git diff --check
python -m pytest -q tests/architecture -k "tasking or facade or legacy"
python -m pytest -q tests/scenario -k "mission or loader"
python -m pytest -q tests/rl -k "tasking or profile"
rg -n "loader\\.sim\\.(set_task_order|set_leader_intent|set_pilot_report)|_air_profile\\.build_kernel_mission_command|getattr\\(loader, \"mission_cmd\"" python gym_envs tests
```

## 停止规则

- 不得把 raw runtime writes 仅换名藏入 helper；helper 必须由 facade/bridge 拥有并有 guard。
- 本流不强制修改所有 scenario JSON schema。
- 若迁移所需 facade surface 缺失，停止并把缺失方法作为 WP22-C dependency 返回。

## 第一轮实现快照

| 字段 | 值 |
|------|----|
| `status` | `pass` |
| `commands run` | `git diff --check` -> 通过；`python -m pytest -q tests/architecture -k "tasking or facade or legacy"` -> 受 collection 限制，未形成 closure 信号；`python -m pytest -q tests/scenario -k "mission or loader"` -> 聚焦 mission-loader 分片 `2` 个通过；`python -m pytest -q tests/rl -k "tasking or profile"` -> 聚焦 Python 业务绕过分片 `5` 个通过 |
| `remaining blockers` | 维护中业务退场没有 blocker；剩余的 `command_chain_cache` import-time `TaskOrder` unlock 只属于 C/F guard lane 的 validation-only follow-up。 |
| `integration notes` | 保持维护中 caller 与 compatibility-only guard seam 的边界清晰；不要把 `TaskOrder` import work 再写回 B blocker。 |

## 第二轮实现快照

| 字段 | 值 |
|------|----|
| `status` | `pass` |
| `commands run` | `git diff --check` -> 通过；`python -m pytest -q tests/architecture -k "tasking or facade or legacy"` -> 受 collection 限制，未形成 closure 信号；`python -m pytest -q tests/scenario -k "mission or loader"` -> 聚焦 mission-loader 分片 `2` 个通过；`python -m pytest -q tests/rl -k "tasking or profile"` -> 聚焦 Python 业务绕过分片 `5` 个通过 |
| `remaining blockers` | 维护中业务退场没有 blocker；仅剩 `command_chain_cache` 的 import-time `TaskOrder` validation-only follow-up。 |
| `integration notes` | 保持维护中 caller 与 compatibility-only guard seam 的边界清晰，并把 `TaskOrder` import work 交给 C/F guard lane。 |
