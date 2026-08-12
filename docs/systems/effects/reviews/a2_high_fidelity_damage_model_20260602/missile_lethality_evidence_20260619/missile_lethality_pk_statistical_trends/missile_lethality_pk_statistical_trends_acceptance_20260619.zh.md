# MLF-9 Pk / 统计趋势验收记录

状态：`2026-06-19` accepted / archived，用于有边界的 simulation-trend 切片。
P0 到 P6 已针对 deterministic row-level trend extraction 和 retained diagnostics/report
exposure 满足。

英文主文：
[missile_lethality_pk_statistical_trends_acceptance_20260619.md](missile_lethality_pk_statistical_trends_acceptance_20260619.md)。

## 验收范围

本记录将有边界 MLF-9 切片标记为 accepted。`[x]` = 已满足；`[~]` = 有意留在
MLF-9 外。

已验收：

- 基于显式 `lethality_chain_rows` 的确定性趋势提取。
- simulation trend report 的诚实分母和后果分桶。
- Wilson-style 区间字段与样本/来源标签。
- process-probe retained diagnostics payload 和可选 standalone JSON report 输出。
- Python diagnostics row/snapshot 表面中的 `structural_breakup` 可见性。

保持 held：

- 现实 Pk。
- 具体弹种杀伤率。
- 具体目标杀伤率。
- 公开结果校准或验证。
- Reward shaping 或训练收益声明。
- 实体删除、直接坠毁规则和碎片物理。

## P0 Boundary

- [x] MLF-9 只负责 Pk/statistical trend reporting。
- [x] 父级 A2 README 链接 MLF-9 工作面。
- [x] README/status/contract docs 已列出禁止声明。
- [x] MLF-10 继续保留为 calibration gates。

## P1 Evidence Inventory

- [x] Inventory 命名 MLF-5 到 MLF-8 的 accepted upstream inputs。
- [x] Inventory 将 accepted row facts 与 calibration、reward、debris-physics residuals 分离。
- [x] Safe write sets 限定为 MLF-9 docs、diagnostics rows/reporting 和 focused tests。

## P2 Metric Contract

- [x] Contract 定义 row source、accepted stages、denominators、outcome buckets、
  grouping fields 和 uncertainty labels。
- [x] `structural_breakup` 已进入 Python diagnostics row contract。
- [x] Contract 拒绝 calibrated Pk 和真实武器/目标真值。

## P3 Trend Harness

- [x] `tools/diagnostics/mlf9_statistical_trends.py` 消费显式 row lists 或包含
  `lethality_chain_rows` 的 JSON 对象。
- [x] 它按 `(episode, chain_id)` 分组，派生 denominator/outcome counts，并输出有边界
  rate records。
- [x] 聚焦测试覆盖 deterministic fixture summaries、grouping、intervals 和 non-claim flags。

## P4 Report Integration

- [x] Process probe 在结果 payload 中嵌入 `mlf9_statistical_trends`。
- [x] Process probe 可通过 `--mlf9_report_json_out` 写出 standalone retained
  diagnostics artifact。
- [x] Report metadata 记录 `sample_source` 和 `report_surface`。
- [x] Report authority flags 保持 real-world Pk、weapon/target lethality、
  calibration、reward 和 entity deletion 为 false。

## P5 Focused Validation

- [x] MLF-9 diagnostics/probe/test files 的 `py_compile` 通过。
- [x] 聚焦 pytest 报告 `53 passed`。
- [x] `git diff --check` 通过。
- [x] 本地 Markdown 链接检查覆盖 30 个文件，0 个本地链接缺失。

## P6 Closeout

- [x] README、current status、task clusters、dispatch queue、validation 和 acceptance
  docs 的 accepted/held 边界一致。
- [x] 父级 A2 README 将 MLF-9 描述为 accepted / archived。
- [x] MLF-9 证据包已物理归档到父级 A2 本地 archive。
- [x] 旧 active 路径只包含轻量兼容指针。
- [x] 最终 closeout 本地 Markdown 链接检查覆盖 30 个文件，0 个本地链接缺失。

## 保留边界

已验收的 MLF-9 输出应被理解为：

```text
在这个 synthetic scenario / fixture population 内，在满足显式分母的 rows 中，
有这个比例到达了这个 simulated outcome bucket。
```

它不能被理解为：

```text
这个真实武器对这个真实目标有这个杀伤概率。
```

## 残余

- MLF-10 必须负责 calibration gates、public-source outcome admission，以及任何真实武器 /
  目标概率讨论。
- 后续 report consumers 必须保留 `synthetic_simulation_trend` 框架和 false authority flags。
- Archive registry 和 archive index updates 标识物理证据路径。
