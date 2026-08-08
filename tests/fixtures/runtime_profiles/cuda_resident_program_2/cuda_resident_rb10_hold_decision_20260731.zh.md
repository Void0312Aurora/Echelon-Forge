# RB10 CUDA 驻留后续决策：Hold

语言版本：

- 英文规范版：[cuda_resident_rb10_hold_decision_20260731.md](cuda_resident_rb10_hold_decision_20260731.md)
- 中文伴随版：`cuda_resident_rb10_hold_decision_20260731.zh.md`
- 机器可读记录：[cuda_resident_rb10_hold_decision_20260731.json](cuda_resident_rb10_hold_decision_20260731.json)

- 决策 ID：`rb10.hold.cuda_resident.20260731`
- Owner：exact-runtime / CUDA 驻留后端工作线
- 权威：分支内 CUDA 驻留计划
- 依据：把冻结的 RB10 gates 机械应用于 RB9 commit
  `c21757908bcd4c7c323215bba2e8c3afbbfa7e2c`
- 日期：`2026-07-31`

## 结论

**将 CUDA 驻留后端保持为 unmaintained research candidate。** RB10 不授权
RuntimeFacade 晋级、support projection、capability 扩张、kernel/launch tuning，
也不授权 spatial/sensor/communications slice。维护中的 CPU backend 继续作为
默认后端，公开 ABI 不变。

本计划唯一允许的下一动作是 RB11 无晋级收口：审计 rollback/retention 边界，
确认 maintained state 未改变，并关闭分支内计划记录。

## Gate 应用

| 冻结的 RB10 gate | RB9 证据 | 结果 |
| --- | --- | --- |
| 已测完整 facade/window advance | CUDA 使用私有 `inject -> publish_stage -> advance`；`publish_stage` 不在 `IWorldBatchBackend` 中 | 失败 |
| CPU/CUDA invocation surface 等价 | `backend_spi_world_batch` 对 `backend_private_phase_sequence` | 失败 |
| 已测 learner-equivalent consumption | device consumer 只是 diagnostics smoke，且含 hidden host validation readback | 失败 |
| 必需 hardware metrics 完整 | achieved counters 因 `ERR_NVGPUCTRPERM` 不可用 | 失败 |
| selected-slice parity 可解除 quarantine | RB8 selected-slice parity 仍 quarantine | 失败 |
| 小 batch 默认不退化 | world `1` 的 P50、P95、rollout P50 均退化 | 失败 |

RB9 给出 world `4` 的 provisional internal threshold，world `4+` 在私有比较中
也显示较大 timing delta。这些数值仍是有用的 diagnostics，但两侧 invocation
surface 与 collection path 不等价，因此不能作为 promotion gate。决策继续保持
`hold_required`、`required_metrics_complete=false`、
`break_even_eligible=false`、`promotion_allowed=false`。

## 证据身份

- RB9 comparison：`cd3d444a6171c32c0bc34d8e2ec23cd17d964d48a162a0c1f12979fa567e9840`
- CPU lane：`1a5bd2d1970621d8f808774b90c85953583d4151fc5d9dd1392adefafe28b4be`
- CUDA lane：`f03fc930f0781fc8f79aaf09d5bff4d1042c954e0a07516ad85642099d5dd94c`

当前没有 human promotion approval 记录。这个 hold 是既有冻结 gate 的 fail-closed
结果，不表示候选没有未来研究价值。若重新开启实现，必须建立新的显式授权计划，
并补充新的完整 facade 证据；这不属于 RB10-RB11。

## 动作边界

当前允许：

- 保留分支内 candidate 与 compact RB9 evidence；
- 执行无晋级的 RB11 closure audit。

本工作线禁止：

- RuntimeFacade 晋级、capability-manifest 扩张或 support flag 变化；
- CUDA window 内 CPU fallback；
- kernel/launch tuning 或寄存器压力实验；
- spatial、sensor、communications 语义扩张。
