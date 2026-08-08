# CUDA-resident CR2-5b achieved-counter 证据（2026-08-04）

## 范围

本记录覆盖 CR2-5a 之后单独要求的 Nsight Compute 尝试。它复用同一个
Release/SM86 resource-probe binary，以及同一个单 window、256-world
`cudaProfilerApi` body。机器可读 artifact 是
`cuda_resident_cr2_counter_evidence_20260804.json`。

CR2-5b 不修改 CUDA kernel、launch shape、allocation path、runtime selection 或
public support flag。目标计数器是 achieved occupancy、branch divergence，以及 kernel
global/local/shared-memory traffic。缺失的硬件计数器不能用零、CR2-5a theoretical
occupancy、Nsight Systems launch metadata 或 CUDA API transfer bytes 替代。

## 真实 profiler 尝试

Nsight Compute 2025.3.1.0 以 application-only target、`cudaProfilerApi` range
control、kernel replay、demangled name、`full` counter set 与 12-launch limit 启动冻结
probe。collector 自己构造并执行命令。compact artifact 记录 absolute argument vector、
NCU executable、resource-probe binary、attempt log、probe output、CR2-5a 父证据、
collector 与 contract 的 hash；可读 command template 会遮蔽机器绝对路径。

profiler 连接一个进程，只报告一个 error，并从同一个进程断开。退出码为 1，错误是：

`ERR_NVGPUCTRPERM` —— 该进程没有读取 NVIDIA GPU performance counter 的权限。

本次没有生成 `.ncu-rep`。应用本身仍完成完整 profile body、等待 device consumer，
并写出与 CR2-5a 相同 hash 的冻结 probe payload。因此失败发生在 kernel result 之外，
状态是 `external_blocked`，不能把它解释成成功采得的零值。

## Fail-closed 结果

| Counter family | 结果 |
| --- | --- |
| achieved occupancy | null |
| branch divergence | null |
| kernel global-memory traffic | null |
| kernel local-memory traffic | null |
| kernel shared-memory traffic | null |

required counter-launch count 为 12，实际取得的 hardware-counter record count 为 0。
由于真实尝试和外部 blocker 已记录，`cr2_5b_counter_attempt_complete=true`；
`cr2_5_achieved_counter_gate_complete` 仍为 false，disposition 是
`documented_external_blocker`。tuning、promotion、public support 与
maintained-backend claim 继续关闭。

raw log 与 probe output 保留在仓库外；compact artifact 保存其 raw-byte SHA-256。
tracked source hash 使用声明的 UTF-8/LF canonical form。开启 GPU performance counter
属于外部 host policy 变更，本迭代不执行该变更。
