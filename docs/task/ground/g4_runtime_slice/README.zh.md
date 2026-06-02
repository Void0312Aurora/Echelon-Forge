# G4 Runtime 切片

状态：`2026-06-02` 归档指针。完整证据包已移入
[archive/g4_runtime_slice](../archive/g4_runtime_slice/README.zh.md)。

G4 已接受有边界的 tasking-only lifecycle slice。它封存了经由 normalized
`TaskOrder -> LeaderIntent -> PilotReport` 的 maintained bridge，但不声明 command
delivery、observation/export、movement、sensing、terrain、fires、damage、combat 或
broad facade authority。

本路径仅保留轻量摘要。新工作应从 [../README.zh.md](../README.zh.md) 和新的
follow-on package 继续。
