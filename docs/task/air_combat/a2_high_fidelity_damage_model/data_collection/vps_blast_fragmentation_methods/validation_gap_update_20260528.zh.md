# VPS blast_fragmentation source pin 与 validation gap 更新 - 2026-05-28

状态：`source_pin_update / validation_gap_update / non-authoritative`。本文只补强公开来源固定、benchmark design reference 充分性和缺口登记；不运行 benchmark，不生成 artifact，不创建 vulnerability descriptor，不写 runtime row，不授予 Pk、deterministic fuze、effect-scale 或 component-failure probability authority。

适用 scope 仍为：`F-16C_Block50` x `AIM-120C-class/blast_fragmentation` x `beam` x `high` x `near_miss_0_35m`。所有来源默认只能支持公开方法、benchmark 设计、validation criteria 或 reproducibility planning。

## 本轮 Source Pin 判定

| `source_id` | pin 状态 | 可采纳角色 | 审计说明 | residual |
|---|---|---|---|---|
| `VPS-BFM-001` | `pinned_public_method` | `method_ref`, `validation_criteria`, `benchmark_design_reference` | UN SaferGuard / IATG 01.80 PDF 和网页入口可继续作为 scaled-distance 与 fragment formula family 的公开方法导航。 | 需固定本地保留策略和 checksum；不能复制表格或把 QD/hazard model 迁移为 A2 kill probability。 |
| `VPS-BFM-002` | `pinned_public_method` | `method_ref`, `validation_criteria`, `benchmark_design_reference` | WBDG UFC 3-340-02 页面为公开入口；WBDG 摘要确认其 protective-construction blast-load 方法范围。 | 结构抗爆域不匹配 aircraft component fragility；只支持 blast method route and criteria。 |
| `VPS-BFM-003` | `pending_acquisition` | 仅在官方 artifact 固定后可作为未来 `method_ref` | Kingery-Bulmash ARBRL-TR-02555 当前只由题名、报告号和引用链固定，本轮未固定官方 PDF。 | 缺 official source URL、artifact hash、coefficient provenance 和摘录边界。 |
| `VPS-BFM-004` | `pinned_public_background` | `validation_criteria`, cross-check | GICHD public PDF 可用于术语、hazard axes 和 uncertainty framing。 | Tier B/background；不是方法校准或 target/weapon truth。 |
| `VPS-BFM-005` | `pinned_bibliographic` | `method_ref`, `validation_criteria` | Elsevier ISBN / 图书元数据可支持公开教材引用；版权受限。 | 不能复制正文或公式推导；无 benchmark dataset。 |
| `VPS-BFM-006` | `pinned_doi` | `method_ref`, `validation_criteria`, synthetic benchmark design | Mott DOI 可稳定指向 shell fragmentation mass-distribution theory。 | 出版社版权限制；不覆盖 preformed fragments、direction pattern 或 target consequence。 |
| `VPS-BFM-007` | `pending_acquisition` | 仅在官方 artifact 固定后可作为未来 `method_ref` | Gurney BRL-405 当前只由题名、报告号和引用链固定。 | 缺 official URL、rights、checksum 和 versioned equation provenance。 |
| `VPS-BFM-008` | `pinned_bibliographic` | `method_ref`, `validation_criteria` | Cooper textbook ISBN 路线可支持 implementation sanity checks。 | Copyright-limited；无 benchmark data ingestion。 |
| `VPS-BFM-009` | `rejected_for_use` | rejection evidence only | WBDG 官方 UFC 3-340-01 页面说明该文档不具备互联网公开分发条件并存在出口/分发限制。 | 不使用镜像、摘录方程或二手摘要作为 public source material。 |
| `VPS-BFM-010` | `pinned_public_method` | limited `method_ref`, `validation_criteria` | NASA standards record 和 PDF 为公开、active，可用于 BLE 结构和 domain rejection。 | Orbital debris / hypervelocity domain mismatch；coefficients 不能迁移到 A2。 |
| `VPS-BFM-011` | `pinned_doi` | `method_ref`, `validation_criteria` | Recht-Ipson DOI 可稳定指向 residual velocity / ballistic perforation equation shape。 | 需要 public numeric examples 后才可超出 formula-shape criteria。 |
| `VPS-BFM-012` | `metadata_route_pinned / artifact_pending` | `validation_criteria` candidate | DLA ASSIST / QuickSearch 是 MIL-STD-662F / V50 的官方查询路线；本轮 DNS/availability 不稳定，因此 artifact 仍 pending。 | PDF availability、distribution statement 和 sha256 未固定；criteria only。 |
| `VPS-BFM-013` | `pinned_doi` | `reproducibility`, `validation_criteria`, synthetic benchmark design | Marsaglia DOI 可稳定指向 uniform sphere sampling。 | Sampling is not physical warhead pattern。 |
| `VPS-BFM-014` | `candidate_route_identified / artifact_pending` | `benchmark_design_reference_candidate`, `method_ref_candidate`, future `reproducibility` | DENIX DDESB TP-20/BEC-O route 可作为 blast implementation benchmark design 的公开候选路线；本轮 DNS/robots 不稳定，未完成 artifact/rights/hash 固定。 | 需要 official availability check、artifact sha256、精确 tool package/version、allowed output policy 和 no munition-specific data leakage check。 |
| `VPS-BFM-015` | `candidate_route_identified / artifact_pending` | `benchmark_design_reference_candidate`, `validation_criteria_candidate` | DENIX DDESB TP-21 route 可作为 debris collection/density/mass/velocity vocabulary 的候选路线；本轮 DNS/robots 不稳定，未完成 artifact/rights/hash 固定。 | 需要 official availability check 和 artifact sha256；debris safety domain 不是 missile warhead truth。 |
| `VPS-BFM-016` | `not_admitted` | search lead only | 本轮未固定 TM 5-855-1 的官方稳定公开入口。 | 保持排除，直到固定官方公开入口和 rights statement。 |

## BFM-BM-001..006 Design Reference 充分性

| `benchmark_id` | 当前是否足够支撑 `benchmark_design_reference` | 已足够支撑的设计内容 | 仍缺 artifact / hash / threshold | 当前允许结论 |
|---|---|---|---|---|
| `BFM-BM-001` | `partial_yes_for_unit_design` | `VPS-BFM-001/002/005` 足以设计 scaled-distance、unit/domain 和 monotonicity checks；`VPS-BFM-014` 可作为 BEC-O comparison 的候选路线。 | `VPS-BFM-003` official artifact；`VPS-BFM-014` official availability/rights/hash；BEC-O tool/package hash；selected comparison output hashes；frozen Z-domain and monotonic tolerances；reviewer signoff。 | 可设计非权威 blast unit benchmark；不足以 validation pass 或 calibration。 |
| `BFM-BM-002` | `partial_yes_for_synthetic_unit_design` | `VPS-BFM-006/008/001` 足以设计非敏感 Mott-style mass distribution checks 和 energy-unit sanity；`VPS-BFM-007` 仍 pending。 | Gurney official artifact/hash 或显式排除；toy input config hash；seed policy；distribution normalization tolerance；quantile replay threshold。 | 可设计 synthetic fragment mass/energy unit tests；velocity model 必须保持 IATG/textbook-backed 或 pending。 |
| `BFM-BM-003` | `yes_for_sampler_design / partial_for_debris_metrics` | `VPS-BFM-013` 与 fragment method refs 足以设计 isotropy 和 witness-surface bookkeeping；`VPS-BFM-015` 可作为 debris/areal-density vocabulary 候选路线。 | `VPS-BFM-015` official availability/rights/hash；geometry witness config hash；sample-count schedule；seed list；convergence threshold；closed-surface conservation tolerance；explicit directional-pattern residual。 | 可设计 sampler/areal-density accounting 的 reproducibility benchmark；debris metrics 仍 pending artifact。 |
| `BFM-BM-004` | `partial_yes_for_formula_shape_and_domain_design` | `VPS-BFM-010/011/012` 足以设计 BLE/residual-velocity/V50 vocabulary and domain separation；`VPS-BFM-015` 可作为 debris vocabulary 候选路线；`VPS-BFM-009` rejected。 | MIL-STD-662 artifact/hash 或保持 ASSIST route metadata-only；`VPS-BFM-015` official availability/rights/hash；public numeric examples for residual velocity if desired；toy material/projectile config hash；monotonic/domain-rejection thresholds。 | 可设计 penetration-margin formula-shape 和 fail-closed tests；不是 aircraft component penetration validation。 |
| `BFM-BM-005` | `partial_yes_for_integration_manifest_design` | `BFM-BM-001..004` design refs 与 candidate scope docs 足以定义 mechanism-load vector toy integration manifest。 | All upstream benchmark artifact hashes；integrated config hash；`near_miss_0_35m`、`beam`、`high` bucket sampling definition；source-trace completeness threshold；no-authority field linter。 | 可设计 toy integration benchmark manifest；不能运行 authoritative validation 或创建 descriptor。 |
| `BFM-BM-006` | `yes_for_administrative_linter_design` | A2 source admission rules、foundation source standard 和所有 `VPS-BFM-*` rows 足以设计 source/rights/authority manifest linter。 | Linter implementation artifact；schema version；required-field list freeze；test fixture hash；pass/fail threshold；reviewer signoff。 | 可作为首个 benchmark scaffold 冻结；不授予 physics authority。 |

## Rejected 与 Not-Consumed Sources

| item | disposition | reason | guardrail |
|---|---|---|---|
| UFC 3-340-01 | `rejected_for_use` | WBDG 官方页显示该文档不具备互联网公开分发条件并有出口/分发限制。 | 不下载、不镜像、不引用非官方副本正文，也不用作 penetration benchmark support。 |
| TM 5-855-1 | `not_admitted` | 本轮未固定官方稳定 `source_ref` 和 distribution statement。 | 只保留为 search lead。 |
| Forum/game/wiki warhead parameters | `rejected_for_direct_calibration` | Provenance、rights 和 scope 不满足 A2 admission rules。 | 不用于 warhead mass、lethal radius、fuze、Pk 或 component probability。 |

## Cross-Validation 状态

| mechanism area | current cross-validation | gap |
|---|---|---|
| Blast scaled distance / pressure / impulse | IATG + UFC 3-340-02 + Baker 提供公开 method/design chain；DDESB TP-20/BEC-O route 可作为候选 comparison route。 | Kingery-Bulmash official artifact、DDESB official availability/rights/hash 和 BEC-O executable/output hashes 仍 open。 |
| Fragment mass/velocity | Mott DOI + IATG + Cooper 支撑 mass-distribution and method vocabulary。 | Gurney official artifact/hash 和 non-sensitive velocity benchmark inputs 仍 open。 |
| Fragment/debris areal density | Marsaglia DOI + IATG/GICHD 支撑 sampler design；DDESB TP-21 route 可作为 debris-metric candidate。 | DDESB official availability/rights/hash、directional warhead pattern 和 casing breakup 仍为 open residual。 |
| Penetration / ballistic threshold | NASA-HDBK-8719.14 + Recht-Ipson DOI + MIL-STD-662 ASSIST/QuickSearch route 支撑 formula-shape and threshold vocabulary；DDESB TP-21 route 可作为 debris vocabulary candidate。 | 无 scope-matched aircraft material/component benchmark；MIL-STD artifact/hash 和 DDESB artifact/hash 仍 pending；UFC 3-340-01 cannot be used。 |
| Source trace / rights | Foundation and A2 admission rules 足以设计 fail-closed linter。 | Implementation、fixture hashes 和 acceptance threshold 仍 missing。 |

## Runtime Authority Boundary

本更新不改变 runtime authority。当前最高用途仅限：

- `benchmark_design_reference`;
- `method_ref`;
- `validation_criteria_reference`;
- `reproducibility` planning.

仍然禁止：

- 把 validation 状态写成已通过；
- 把 calibration 状态写成已校准；
- 将 effect-scale、component-failure probability、Pk 或 deterministic-fuze authority 置为授权；
- 写入任何 runtime descriptor row 或 calibrated mechanism-load row。
