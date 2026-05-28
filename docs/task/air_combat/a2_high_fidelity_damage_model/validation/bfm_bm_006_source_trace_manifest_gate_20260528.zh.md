# BFM-BM-006 Source Trace Manifest Gate - 2026-05-28

状态：`implemented_gate / administrative_linter / non-authoritative`。

本文记录 A2 高保真空战毁伤模型在数据尚未闭合时的第一个可执行完善切口：先实现来源追踪、权利边界、pending/rejected 状态和 authority 字段的准入门禁，而不是提前实现校准 blast-fragmentation 参数、Pk、确定性引信或组件失效概率。

## 目标

`BFM-BM-006 source_trace_and_rights_manifest_check` 用来阻止三类退化：

- 公开来源候选被误写成已获取、已验证或已校准；
- source pin / gap update 文档绕过 source ledger 和 validation manifest 审计；
- 未完成 artifact、rights、sha256、acceptance criteria 和 residual closeout 时创建 runtime descriptor 或 authority row。

该门禁只检查准入卫生，不运行物理 benchmark，不生成机制载荷 artifact，不授予 runtime authority。

## 实现入口

| 项 | 当前实现 |
|---|---|
| 维护工具 | `tools/maintenance/a2_source_admission_audit.py` |
| 架构测试 | `tests/architecture/test_a2_source_admission_audit.py` |
| 扫描对象 | A2 `data_collection/*/source_ledger*.zh.md`、A2 `**/*update*.zh.md` / `**/*source_pin_integration*.zh.md`、A2 `calibration/*/*.zh.md` |
| 默认失败条件 | error-level authority、candidate update 或 manifest 违规 |
| strict 失败条件 | 默认失败条件 + source pin warning |

推荐命令：

```bash
python3 tools/maintenance/a2_source_admission_audit.py
python3 tools/maintenance/a2_source_admission_audit.py --strict
python3 -m pytest -q tests/architecture/test_a2_source_admission_audit.py
```

## 当前覆盖

当前门禁检查：

- source ledger 是否包含 source_ref、发布方/持有人、权利、scope、交叉验证、residual 和 authority 边界；
- source ledger row 是否暴露稳定 URL、DOI、报告号、标准号或 catalog handle；
- source ledger row 是否显式写明 candidate、non-authoritative、pending 或 rejected 边界；
- source pin / gap update 是否保留非权威、待获取、拒绝或不授予边界；
- source pin / gap update 是否暴露基本来源引用面；
- calibration candidate 文档是否保留 `non-authoritative` 边界；
- validation manifest / report 是否记录 `validation_status` 和 artifact hash / sha256 状态；
- 是否意外写入 `effect_scale_authority`、`component_failure_probability_authority`、`pk_authority`、`deterministic_fuze_authority` 的真值；
- 是否意外写入 `validation_status=passed/validated` 或 `calibration_status=calibrated`；
- candidate calibration 文档是否暗示已经创建 runtime descriptor 且没有负向边界。

## 本轮数据结论

并行数据收集后，A2 仍停留在 `candidate / non-authoritative`：

- guidance / miss-distance：PN/APN、terminal evasion、seeker/filter/noise 只达到 `method_reference`、`validation_criteria_reference`、`benchmark_design_reference` 或 `reproducibility_candidate`。
- VPS / blast-fragmentation：Kingery-Bulmash、Gurney、DDESB TP-20/TP-21 仍缺官方 artifact、rights 和 sha256；UFC 3-340-01 继续 rejected。
- target / material / fuze：F-16 内部几何、材料分区、AIM-120C 战斗部/引信、MIL-STD-662F artifact 仍未闭合；只能作为 reference / sanity / pending。
- component fragility：公开来源可支持方法、准则和 benchmark design；尚无 scope-matched AAM/F-16 组件失效概率校准数据。

因此当前不应进入 calibrated descriptor、effect-scale row、component-failure probability row、Pk 或 deterministic fuze 放行。

## 下一门

只有在本门禁 default 通过、strict warning 被逐项解释或关闭后，才允许进入后续 benchmark scaffold：

1. 固定 `BFM-BM-001..005` 的 benchmark config、seed、单位、输入域和 output artifact 保留策略。
2. 冻结 metrics 和 acceptance criteria，且必须在运行前完成。
3. 对每个 acquired artifact 记录 source_ref、rights、版本、sha256 和允许输出策略。
4. 生成 validation report，保持 `validation_status=not_run/pending/failed`，直到所有 residual closeout 和审阅完成。
5. 另行审议是否创建有限 `validated_physics_surrogate` descriptor；Pk 和 deterministic fuze 仍不由本包放行。

## 当前验收

当前可验收为：`BFM-BM-006 行政准入门禁已实现并纳入测试`。

当前不能验收为：

- blast-fragmentation 物理模型已验证；
- F-16C / AIM-120C 杀伤参数已校准；
- 组件失效概率已校准；
- deterministic fuze 或 Pk 已具备公开证据链；
- 可训练层可以把本门禁输出当物理毁伤标签。
