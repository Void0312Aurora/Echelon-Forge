# `src/components/domains/naval` 边界

本目录是 component 层的 naval-domain 数据与 DTO 扩展所有者。naval 平台状态、战斗组件、command 扩展和 tasking 扩展统一收束在这个域边界下。

## 阅读入口

- [platform/README.md](platform/README.md)
- [combat/damage_naval.h](combat/damage_naval.h)
  - 声明 `NavalDamageResponseProfile`：naval 自有的数据化声明系数，覆盖 fire/flooding/hull-breach 演化、
    severity→capability 损失项，以及 mount 状态耦合增益。当前舰船只解析唯一的 parity-default profile；
    在补齐内容选择和运行时证据前，`naval_damage_response_profiles()` 有意保持 default-only。
- [combat/weapon_naval.h](combat/weapon_naval.h)
- [command/README.md](command/README.md)
- [tasking/README.md](tasking/README.md)

## 损伤响应

`systems/combat/damage_system_naval.h` 只负责舰船损伤 tick，本身不持有任何系数：它解析当前唯一获准的
`NavalDamageResponseProfile`，按 Flecs 步长应用每秒速率，推进 fire/flooding/breach 状态，把结果投影到共享
`PlatformDamageState` capability 字段，并把 loss 语义交给 `sync_platform_damage_loss_state`。weapon mount 状态
按 `ready_count / max_ready_count` 的截断平均值计算；parity default 把 `mount_response_weight` 声明为 0.0，
因此耦合严格中性。当前不宣称 submarine damage response；这里只是 damage-response 机制：不持有 naval
weapon-release 权限（N5），也不持有 kill/outcome 权限（N6）。
