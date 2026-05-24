<!-- Machine-translated draft generated on 2026-05-18 from src/runtime/facade/README.md. Review before treating this file as authoritative. -->

# `src/runtime/facade` Boundaries

`runtime/facade` is a maintained C++ application-layer API. It targets training environments, Python bindings, and future frontend mainlines, providing typed request/result instead of exposing the full details of the underlying world owner.

## Allowed

- `RuntimeFacade`.
- Facade request/result/capability types.
- Bulk reset, setup, step, command, tasking, episode, and observation operations.
- Dedicated diagnostics-trace query/export operations.
- Controlled wrapping of `WorldBatchRuntime` and `ExecutionEpisodeController`.
- Public header only exposes facade/contracts types; the underlying `WorldBatchRuntime` owner should remain in the implementation.

## Prohibited

- Implementing ECS systems or physics models.
- Inlining Python binding logic.
- Blindly copying all low-level APIs of `WorldBatchRuntime` into the facade API.
- Adding new mainline entry points without designed request/result.
- Directly including `core/engine/*` in `*_types.h` or facade public headers.

## Escape Hatch Retirement

`RuntimeFacade` no longer exposes a raw `WorldBatchRuntime` escape hatch. Maintained frontends must use facade-level request/result APIs, and low-level diagnostics or capability verification should instantiate `WorldBatchRuntime` directly in a diagnostics/test scope instead of drilling through the facade.

Mainline frontends must not cache raw `WorldBatchRuntime`, re-expose a compatibility runtime from an adapter, or branch based on raw runtime availability. When a long-term capability is needed, add a designed facade request/result method and bind that facade method at the Python layer.

为了保持仓库里的分层约束与自动化校验一致，下面这几条中文规范语句保留为权威短句：

- 必须把访问集中在一个显式 adapter。
- 不得重新引入 `RuntimeFacade.runtime_compatibility_quarantine()`。
- 不应缓存 raw `WorldBatchRuntime`。

When adding long-term APIs, priority should be given to supplementing facade request/result types, and binding the facade at the Python layer, rather than directly exposing new low-level runtime methods.

## Diagnostics Surface

`DiagnosticsTrace` is a maintained facade surface in its own right. It may
share kernel evidence with engagement export, but the facade must expose a
dedicated diagnostics query path instead of requiring consumers to piggyback on
`export_engagement_event_packet()` just to read traces.

## Split Threshold

Use this counting rule for `RuntimeFacade` governance:

- Count maintained public request/result methods only.
- Exclude constructors and simple accessors.
- When the maintained count approaches roughly 40 methods, plan the next split
  around Session, Setup, Execution, Observation, Diagnostics, Engagement, and
  Capability groups before expanding the mainline surface further.
