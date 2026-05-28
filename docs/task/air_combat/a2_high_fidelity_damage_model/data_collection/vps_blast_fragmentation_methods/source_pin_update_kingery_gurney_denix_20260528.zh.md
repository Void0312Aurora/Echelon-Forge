# Kingery / Gurney / DENIX Source Pin Update - 2026-05-28

状态：`source_pin_update / non-authoritative`。本文只记录公开来源路径核对、访问状态、权利边界和 artifact/hash 缺口；不运行 benchmark，不生成校准数据，不创建 vulnerability descriptor，不授予 Pk、deterministic fuze、effect-scale 或 component-failure probability authority。

适用 scope 仍为：`F-16C_Block50` x `AIM-120C-class/blast_fragmentation` x `beam` x `high` x `near_miss_0_35m`。下列条目最多支持 `method_reference`、`benchmark_design_reference`、`validation_criteria_reference`、`pending_acquisition` 或 `rejected_for_use`。

## 访问方法

本轮优先核对官方或准官方入口：

- UN SaferGuard / IATG；
- DTIC DOI / DTIC citation 或 PDF 路线；
- DENIX / DDESB official technical papers；
- WBDG official UFC page；
- DOI、WorldCat 或出版社题录作为 bibliographic cross-check。

未使用论坛镜像、网盘、游戏数据、未授权手册正文或受限材料正文。对 DENIX、DTIC 的本地 `curl -I` 访问在本环境出现 DNS 解析失败；因此所有未实际下载和 hashing 的 artifact 都保持 `artifact_pending`。

## Source Pin Summary

| source | 官方/合法 Internet-public 路径判定 | 稳定 source_ref / URL | 版本 / 日期 | 权利边界 | artifact / hash 状态 | 当前 A2 用途 |
|---|---|---|---|---|---|---|
| Kingery-Bulmash ARBRL-TR-02555 | `not_confirmed_as_public_artifact`。未确认官方公开 PDF 或 DTIC 可下载路径；只确认公开题录和多条 Tier A/B 引用链。 | 题录：`Kingery, C. N.; Bulmash, G., Airblast Parameters from TNT Spherical Air Burst and Hemispherical Surface Burst, ARBRL-TR-02555, AD-B082713`; WorldCat record: `https://search.worldcat.org/nl/title/Airblast-parameters-from-TNT-spherical-air-burst-and-hemispherical-surface-burst/oclc/867650613`; UN IATG 01.80 PDF: `https://data.unsaferguard.org/iatg/en/IATG-01.80-Formulae-ammunition-management-IATG-V.3.pdf`; UN SaferGuard calculator route: `https://unsaferguard.org/un-saferguard/kingery-bulmash` | BRL report dated April 1984; WorldCat lists 51 pages. IATG v3 / IATG 01.80:2021 references the report and Kingery-Bulmash method. | Report body not acquired; possible distribution restrictions remain unresolved. Do not use unofficial mirrors, coefficient tables from forums, or copied report body. IATG may be cited as public method navigator under UN copyright boundaries. | No official report PDF acquired; no sha256. IATG PDF hash not fixed in this pass. | `method_reference` through IATG / SaferGuard route; original report stays `pending_acquisition` and cannot be benchmark artifact. |
| Gurney BRL Report 405 | `official_route_identified / artifact_pending`。DTIC DOI and citation/PDF route identified by DOI and public literature, but local direct access failed in this environment. | DOI: `https://doi.org/10.21236/ADA289704`; DTIC citation route reported in public literature: `https://apps.dtic.mil/sti/citations/tr/ADA800105`; DTIC PDF route reported in public literature: `https://apps.dtic.mil/sti/pdfs/ADA800105.pdf`; report title: `The Initial Velocities of Fragments from Bombs, Shells, and Grenades`, BRL Report 405. | BRL Report 405, 1943. DOI route appears as `ADA289704`; DTIC citation/PDF route appears as `ADA800105`. This alias mismatch requires final DTIC page verification before acquisition. | Do not use non-DTIC mirrors. Publisher/DOI references are acceptable for method discovery; report body and equations are not ingested until official artifact and rights are fixed. | No PDF downloaded; no sha256. Local `curl -I` to `apps.dtic.mil` failed DNS. | `method_reference_candidate` / `pending_acquisition` for Gurney velocity route; may support search and model-card citation after official artifact verification, not benchmark output. |
| DDESB TP-20 / BEC-O | `internet_public_route_identified / artifact_pending`。Official DENIX technical paper page is indexed and appears to expose Report Documentation metadata including public-release distribution statement. Local direct access failed DNS, so artifact is not acquired. | DDESB Technical Papers page: `https://www.denix.osd.mil/ddes/ddesb-technical-papers/`; TP-20 page: `https://www.denix.osd.mil/ddes/ddes-technical-papers/ddes-technical-papers/tp-20-ddesb-blast-effects-computer-open-bec-o-version-1-users-manual-and-documentation-11-june-2018`; related spreadsheet route listed on DENIX page as BEC-O Version 1 related spreadsheet. | DDESB Technical Paper 20; report date 06-11-2018; final report; 69 pages; title `DDESB Blast Effects Computer - Open (BEC-O), Version 1, User's Manual and Documentation`. | Search-indexed official metadata appears to state Distribution Statement A / public release, but local artifact availability, rights confirmation and checksum were not fixed. BEC-O V1 removes munition-specific data; do not import spreadsheet outputs as source truth. | No PDF/spreadsheet downloaded; no sha256; local DENIX `curl -I` failed DNS. | `benchmark_design_reference_candidate` for BFM-BM-001 blast curve lock and reproducibility planning; not an acquired benchmark artifact. |
| DDESB TP-21 Revision 2 | `internet_public_route_identified / artifact_pending`。Official DENIX PDF route is indexed and appears to expose Report Documentation metadata including public-release distribution statement. Local direct access failed DNS, so artifact is not acquired. | DDESB Technical Papers page: `https://www.denix.osd.mil/ddes/ddesb-technical-papers/`; TP-21 PDF route: `https://www.denix.osd.mil/ddes/denix-files/sites/32/2018/02/TP-21-Revision-22c-171130-final.pdf` | DDESB TP 21 Revision 2; report date 11/30/2017; final report; 108 pages; title `Procedures for the Collection, Analysis, and Interpretation of Explosion-Produced Debris--Revision 2`. | Search-indexed official metadata appears to state approved for public release / distribution unlimited, but direct rights confirmation and checksum remain pending. Use only as debris collection/analysis criteria; not missile warhead pattern truth. | No PDF downloaded; no sha256; local DENIX `curl -I` failed DNS. | `benchmark_design_reference_candidate` and `validation_criteria_reference_candidate` for fragment/debris areal-density bookkeeping; not an acquired benchmark artifact. |
| UFC 3-340-01 | `rejected_for_use`。Official WBDG page states it is not available on the Internet and has export/distribution limits. | Official rejection evidence: `https://www.wbdg.org/dod/ufc/ufc-3-340-01` | Publish date 06/30/2002 per WBDG page. | WBDG page indicates restricted/export-controlled distribution. | No artifact should be acquired. | `rejected_for_use`; never use mirrors or excerpts for benchmark, method, validation, calibration, or runtime. |

## Benchmark Impact

| benchmark | impact from this update | still missing |
|---|---|---|
| `BFM-BM-001 blast_scaled_distance_curve_lock` | IATG/UFC/Baker remain sufficient for unit/domain design. DDESB TP-20/BEC-O adds an official candidate route for future public-tool comparison. Kingery-Bulmash original report remains pending, so no coefficient artifact is acquired. | Kingery-Bulmash official artifact or explicit exclusion; TP-20 PDF/spreadsheet availability; tool/package hash; selected comparison-output hashes; frozen tolerances. |
| `BFM-BM-002 mott_gurney_fragment_cloud_unit` | Gurney DOI / DTIC route is stronger than a title-only lead and can be recorded as `pending_acquisition`. | Resolve ADA289704 vs ADA800105 mapping on official DTIC page; acquire official artifact only if distribution permits; freeze toy config/seed/statistical thresholds. |
| `BFM-BM-003 fragment_areal_density_spatial_sampling` | TP-21 official route can support debris collection/analysis vocabulary as a candidate design reference. | TP-21 artifact availability and sha256; witness geometry config; sample count schedule; convergence thresholds. |
| `BFM-BM-004 penetration_margin_ble_crosscheck` | TP-21 may support debris metric vocabulary only; it does not replace aircraft material/component validation. UFC 3-340-01 remains rejected. | MIL-STD-662F artifact/hash or metadata-only exclusion; public numeric examples if needed; domain rejection thresholds. |
| `BFM-BM-006 source_trace_and_rights_manifest_check` | This update adds explicit checks for `official_route_identified` versus `artifact_acquired` so source discovery cannot be mistaken for benchmark ingestion. | Linter implementation, fixture hash, required-field freeze, reviewer signoff. |

## Rejected / Not-Admitted Guardrails

- UFC 3-340-01 and any third-party mirror remain `rejected_for_use`.
- Kingery-Bulmash report body remains `pending_acquisition`; do not ingest unofficial copies or coefficient tables from forums.
- Gurney BRL-405 body remains `pending_acquisition`; do not ingest non-DTIC mirrors.
- DDESB TP-20/TP-21 are candidate design references until official artifacts and hashes are retained; do not treat spreadsheet outputs or examples as validation results.
- No source in this file supports calibrated component loads, live fuze behavior, Pk, or runtime descriptor rows.
