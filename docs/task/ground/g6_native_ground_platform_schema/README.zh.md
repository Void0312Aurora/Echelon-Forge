# G6-E Native Ground Platform Schema

状态：`2026-06-02` 归档指针。完整证据包已移入
[archive/g6_native_ground_platform_schema](../archive/g6_native_ground_platform_schema/README.md)。

G6-E 已接受 native ground platform schema evidence：`Ground_Platoon_MVP` 可经由示例数据库加载，
Python 暴露 `ef_py.UnitType.Ground`，并且
`spawn_unit(..., "Ground_Platoon_MVP", ...)` 能 materialize native ground entity，且具备稳定
inspection fields。Route movement、terrain、sensing、fires、damage 和 combat 仍保持 held。

本路径仅保留轻量摘要。新工作应从 [../README.zh.md](../README.zh.md) 和新的
follow-on package 继续。
