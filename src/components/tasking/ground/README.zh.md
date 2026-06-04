# `src/components/tasking/ground` 边界

`components/tasking/ground` 保存第一版维护中的 ground tasking owner slice。它把
G0/G1 Army/ground tasking status 与 native static schema 证据正式化，但不声明
land combat runtime 已经存在。

## 允许

- `TaskOrderGround`、`LeaderIntentGround` 与 `PilotReportGround` 的 G0/G1
  tasking status 字段。
- static occupy/support relationship metadata，以及 `Ground_Platoon_MVP`
  的 native schema boundary identity。
- 显式 bool 字段，用于保持 movement、observation export 与 fires 处于 held，
  直到后续独立 release vote 接受这些 surface。

## 禁止

- `MissionCommand`、`PilotAction`、action-space 或 command-transport 对象。
- ground movement、route following、terrain passability、sensing、fires、
  effects、damage、suppression、sustainment 或 combat runtime behavior。
- `CommandPacket`、`ObservationPacket` 或 `TrackPacket` 声明。
- scenario loading、reward、termination、facade、binding 或 policy code。

## 当前状态

本目录是当前 ground bootstrap 线的正式 C++ component 边界。它有意窄于 naval
tasking slice：ground 现在有维护中的 tasking/status owner slice，但仍没有维护中的
movement 或 observation/action packet boundary。

当前已接受 runtime 证据仍是：

- normalized Army/ground `TaskOrder -> LeaderIntent -> PilotReport` status；
- native `Ground_Platoon_MVP` schema load/spawn/identity；
- 消费该 schema 的 native static scenario-loader fixture。

这些证据仍低于 G2 movement release。

## 依赖方向

本目录可以依赖 `components/tasking/common`。它不得依赖 `core/mission`、
`systems/`、`runtime/facade`、`interfaces/python` 或 scenario loader code。
