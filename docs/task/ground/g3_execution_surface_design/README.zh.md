# G3 执行面设计

状态：`2026-06-02` 归档指针。完整证据包已移入
[archive/g3_execution_surface_design](../archive/g3_execution_surface_design/README.zh.md)。

G3 已接受 execution-surface preflight，并选择安全的 G4 候选：经由 normalized
`TaskOrder -> LeaderIntent -> PilotReport` status shell 的 tasking-only lifecycle
proof。更广的 packet/runtime surface 仍保持 held。

本路径仅保留轻量摘要。新工作应从 [../README.zh.md](../README.zh.md) 和新的
follow-on package 继续。
