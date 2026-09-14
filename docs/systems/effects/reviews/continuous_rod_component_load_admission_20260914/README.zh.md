# 连续杆 P8：Component Load 准入（2026-09-14）

## 结论

P8 已通过结构性准入。实验固定 P7.1 已通过的显式 expanding-ring-band 语义，在相同 `192` 个案例、seed、目标数据库和 `720 × 5` 采样下，对照：

- 基线：曲线 floor `0.05`、最终下界 `0.05`；
- 解耦变体：曲线 floor `0.05`、最终下界 `0.00`。

准入对象是 `geometry → component mechanism load → component response` 的结构闭合，不是 vulnerability 标定或真实武器 Pk。

## 硬门结果

| 门 | 结果 | 证据 |
| --- | --- | --- |
| 完整矩阵 | 通过 | `192 / 192` |
| 基线 load/response 一一映射 | 通过 | `220 / 220`，`0` residual |
| 解耦变体 load/response 一一映射 | 通过 | `220 / 220`，`0` residual |
| component load 数值范围 | 通过 | effect、rod margin、距离均闭合 |
| component response 数值范围 | 通过 | probability、integrity、冗余可用度均闭合 |
| primary trace 闭合 | 通过 | `0` residual |
| 冗余组闭合 | 通过 | `13` 个 group，`0` residual |
| component load topology 稳定 | 通过 | key 集合 `0` 变化 |
| response topology 稳定 | 通过 | key/source/mode 集合 `0` 变化 |
| dependency topology 稳定 | 通过 | edge/target/direction/propagated `0` 变化 |
| 空间场到 component load 传播 | 通过 | `36` 个 load effect 变化，均来自 baseline clamp 行 |
| component load admission | **passed** | P8 结构门闭合 |

解耦变体释放了 `24` 个 baseline clamp event，产生 `36` 个 component-load effect 变化；响应层有 `12` 个 failure probability 和 `12` 个 integrity-after 变化，failure mode 没有翻转。dependency source availability 有 `12` 个数值变化，但依赖边拓扑保持不变；这属于下游状态传播，不是结构断裂。

![连续杆 component load 准入热力图](continuous-rod-component-load-admission.png)

## 解释与边界

每个载荷行都能通过 `(component_name, component_system, component_redundancy_group_id)` 唯一回指一个 response 行，`source_row_index` 与载荷顺序一致。13 个冗余组各自保持单一 system 归属；primary component 的 rod margin 与对应载荷行闭合。

本实验只证明 component-load contract 的结构和传播关系。所有 warhead 参数仍是合成结构测试值；vulnerability/consequence、默认 profile promotion、集成制导/引信/Pk 仍未准入。

下一批进入 P9 Vulnerability / Consequence Admission：在保持 component-load topology 不变的前提下，检查 vulnerability evidence row、failure probability、integrity/consequence 转换和依赖传播的可解释性。

## 复现

```powershell
$env:CMO_BUILD_DIR = 'D:\workshop\Research\Echelon-Forge\build-warhead-spatial-admission-vs'
$env:PYTHONPATH = '.'
python tools/geometry/continuous_rod_component_load_admission.py
python tools/geometry/render_continuous_rod_component_load_admission.py `
  --report docs/systems/effects/reviews/continuous_rod_component_load_admission_20260914/review_packets/continuous_rod_component_load_admission_20260914.json `
  --output docs/systems/effects/reviews/continuous_rod_component_load_admission_20260914/continuous-rod-component-load-admission.png
```

机器可读证据位于 `review_packets/continuous_rod_component_load_admission_20260914.json`。
