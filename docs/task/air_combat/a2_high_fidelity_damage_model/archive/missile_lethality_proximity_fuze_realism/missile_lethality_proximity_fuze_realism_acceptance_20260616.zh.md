# A2 近炸引信真实性代理验收草案

状态：`2026-06-16` PF-R5 聚焦 surrogate 验证 accepted with residuals / 真实引信和 Pk authority 仍拒绝。

英文辅文：
[missile_lethality_proximity_fuze_realism_acceptance_20260616.md](missile_lethality_proximity_fuze_realism_acceptance_20260616.md)。

## 已接受范围

已接受：

- PF-R1 公开机制说明。
- PF-R2 当前 runtime gap audit。
- PF-R3 surrogate contract。
- PF-R4 聚焦非权威 runtime evidence 实现。
- PF-R5 聚焦 surrogate 矩阵验证。

当前完成的 planning package 包括：

- [public_mechanism_source_note_20260616.zh.md](public_mechanism_source_note_20260616.zh.md)
- [current_runtime_gap_audit_20260616.zh.md](current_runtime_gap_audit_20260616.zh.md)
- [proximity_fuze_surrogate_contract_20260616.zh.md](proximity_fuze_surrogate_contract_20260616.zh.md)
- [proximity_fuze_runtime_implementation_20260616.zh.md](proximity_fuze_runtime_implementation_20260616.zh.md)
- [validation/pf_r5_proximity_fuze_validation_20260616.zh.md](validation/pf_r5_proximity_fuze_validation_20260616.zh.md)
- [validation/pf_r5_proximity_fuze_validation_heatmaps_20260616.png](validation/pf_r5_proximity_fuze_validation_heatmaps_20260616.png)

PF-R5 只作为 surrogate 趋势验证被接受。它不是真实引信校准，也不是 kill-probability authority。

## 验收前必需证据

- 公开资料机制说明，并区分 admitted 与 rejected claims：已完成。
- 当前 runtime gap audit，命名现有 fuze path 中的 proxy 行为：已完成。
- surrogate contract，区分以下内容：已完成。
  - nearest approach；
  - fuze sensor detection；
  - fuze trigger；
  - detonation point；
  - mechanism-specific coverage；
  - no-detonation no-load outcomes。
- PF-R4 聚焦 runtime 测试和验证命令：已完成。
- 触发半径、初始横向/高度偏置和机制族行为矩阵对照摘要：已完成但保留残余。

## 必需验证命令

Docs-only checkpoint：

```bash
git diff --check -- docs/task/air_combat/a2_high_fidelity_damage_model/missile_lethality_proximity_fuze_realism docs/task/air_combat/a2_high_fidelity_damage_model/README.md docs/task/air_combat/a2_high_fidelity_damage_model/README.zh.md
```

runtime 验证命令和结果已经记录在
[proximity_fuze_runtime_implementation_20260616.zh.md](proximity_fuze_runtime_implementation_20260616.zh.md)。

PF-R5 验证命令：

```bash
.\tools\maintenance\cmo_env.ps1 python docs/task/air_combat/a2_high_fidelity_damage_model/missile_lethality_proximity_fuze_realism/validation/pf_r5_proximity_fuze_validation.py
```

PF-R5 结果已经记录在
[validation/pf_r5_proximity_fuze_validation_20260616.zh.md](validation/pf_r5_proximity_fuze_validation_20260616.zh.md)。

## 禁止声明

- 真实武器引信参数真值。
- deterministic fuze authority。
- Pk 或具体弹种 kill probability。
- stock runtime replacement。
- 把 PF-R4/PF-R5 surrogate 证据当成真实引信校准或完整杀伤接受。

## 开放残余

- 公开资料机制说明已完成。
- 当前 runtime gap audit 已完成。
- surrogate contract 已完成。
- PF-R4 implementation 已作为聚焦 surrogate evidence 切片完成。
- PF-R5 验证已作为聚焦 surrogate 矩阵完成。
- live guidance 会把实际最近距离压在较窄区间，所以初始发射偏置不是纯起爆点对称性测试。

## 验收决策

当前决策：`PF-R5 focused surrogate validation accepted with residuals / real fuze-Pk authority rejected`。
