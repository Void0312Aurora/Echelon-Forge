# `src/models/domains/ground` 边界

`models/domains/ground` 保存共享 default model 使用的 ground-owned model route 与 consequence application。

## 允许

- 显式的 ground target selection 与 consequence application，避免 ground 概念藏回 generic model 文件。
- 保留 legacy routing 名称的小型 owner-shell helper。

## damage route 的准确定义

`default_effects_ground_domain.h` 仅在目标同时带有 ground-owned 的 `GroundPlatformDamageState` **以及**共享 `HitboxConfig`/`SystemHealth`/`PlatformDamageState` 界面时才将其选为 ground target：它把 warhead mechanism load 施加到 ground state，将该 state 投影进共享 platform capability 字段，然后调用共享 finalize。它只是 consequence ledger 加 bootstrap reachability path，仅此而已。

该 state 的组件 id 是**由外部传入该路由的，不在这里推导**。组合路径按 world 解析一次
`GroundPlatformDamageState` 并把 id 传进 effects model，再转交 selection predicate 与
`ecs_get_mut_id`。因此本文件不会为了查找组件而写出组件类型：身份仍由 owner 派生注册表与引擎
组合持有，models 层不会开出第二条成员关系通道。

不满足 selection predicate 的 ground target 回落到 `is_default_effects_ground_placeholder_target` / `resolve_default_effects_ground_placeholder_consequences`，这两个名称只作为 selection 未满足时的 fallback 保留。

## 禁止

- ECS system registration。
- 定义 ground component（这些位于 `components/domains/ground`）。
- 宣称 ground movement dynamics、ground sensing、ground fires、terrain interaction 或 ground damage-model 保真度。

## 当前文件

- [default_effects_ground_domain.h](default_effects_ground_domain.h)
  - Ground-owned target selection 与 consequence application。它用于解析的 whole-body hitbox 是 spawn 时合成的临时中性尺寸，不是已作者的 ground geometry，因此该文件不宣称任何 ground damage 保真度。
