# `src/components/command/ground` 边界

本目录是早期 ground command DTO 的维护中 C++ owner-slice 归属点。当前只通过
`MissionCommandGround` 暴露静态 tasking intent。

## 允许

- `MissionCommandGround` 作为通过 flat `MissionCommand` compatibility shell
  投影的 static task/status command slice。
- objective/area 引用、ground static task mode、tactical commander ID 和
  tactical cadence 元数据。
- 这些静态字段的 JSON round-trip 与 episode equality 支持。

## 禁止

- route-following、speed/acceleration、terrain passability、sensing、fires、
  damage、suppression 或 combat outcome control。
- 用 ground-only command pipeline 替代已接受的 tasking bridge。
- 在对应 runtime owner 接受前，把 ground-specific execution control 泛化进
  `common/`。

## 当前切片

`MissionCommandGround` 是 command 侧 G0/G1 static task metadata 的承载面。它
不是 movement command，也不证明 G2 route movement。
