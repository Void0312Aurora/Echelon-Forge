# Benchmark Matrix：PN/APN / miss-distance / evasion / seeker-filter 候选

状态：`2026-05-28 benchmark-matrix / non-authoritative`。

本矩阵把公开候选来源映射到可复现实验设计。所有 benchmark 只验证 guidance、track、energy、miss-distance 和 effects evidence chain 的方法行为；不验证真实 Pk，不放行 deterministic fuze，不授权 effect-scale 或 component-failure probability。

## 指标口径

| metric | 必填字段 | 不可替代为 |
|---|---|---|
| `miss_distance` | truth closest approach、runtime `proximity_min_dist_m`、time of closest approach、插值或 substep residual | hit/miss boolean 或 final Pk |
| `guidance_state` | LOS angle/rate、closing speed、navigation ratio、commanded acceleration、achieved acceleration、guidance mode | 单个命中概率 |
| `track_state` | seeker mode、FOV/range gate、measurement noise、filter covariance/proxy、track dropout、memory timeout | 真实 ECCM 或 seeker classified performance |
| `energy_state` | speed, burn phase, drag/turn drag, max-g cap, autopilot tau, saturation | 只看目标最终状态 |
| `terminal_effects_bridge` | fuze trigger outcome、miss distance、local detonation point、closure、warhead footprint evidence、DamageReport | deterministic fuze 或 Pk authority |

## 候选矩阵

| `benchmark_id` | 用途 | 候选来源 | 场景 / 输入轴 | 必须输出 | `benchmark_dataset` | `validation_criteria` | `reproducibility` | authority |
|---|---|---|---|---|---|---|---|---|
| `GEB-BM-001 pn_2d_baseline` | Classical PN sign convention 和 LOS-rate baseline | `GEB-SRC-001/002/008/019` | 2D head-on、tail-chase、beam；navigation ratio sweep；constant-speed vs drag-on | final miss distance、LOS-rate convergence、closing speed、commanded/achieved accel | yes, self-generated | yes | high if script+seed+dt pinned | none |
| `GEB-BM-002 pn_3d_geometry` | 3D PN geometry 与 A2 P0 regression 对齐 | `GEB-SRC-005/008/011/013` + A2 internal | head-on、tail-chase、beam、high-off-boresight；3D initial aspect sweep | truth min distance、proximity min distance、local detonation point, closure | yes, internal generated | yes | high for A2 harness | none |
| `GEB-BM-003 apn_target_accel` | APN/optimal guidance 的 target-accel admission | `GEB-SRC-003/007/020/001` | target step acceleration、Singer target accel process、with/without target acceleration estimate | target accel estimate/proxy、guidance mode、miss distance, estimator residual | partial, generated | yes | medium; estimator manifest required | none |
| `GEB-BM-004 evasion_linearized_optimal` | Linearized optimal evasion 的 timing/switching criteria | `GEB-SRC-014/015/001` | near head-on/tail-chase；bounded target acceleration；limited roll-rate；bang-bang switch timing | switch times、miss distance、roll/accel saturation, validity flag | pending fulltext/manifest | yes | medium; analytic reconstruction needed | none |
| `GEB-BM-005 terminal_jink_legacy` | 老式 fighter terminal evasion taxonomy | `GEB-SRC-009/010/008` | constant turn、switch/jink、last-second bank reversal、barrel roll；maneuver start time sweep | miss-distance distribution/ranking、maneuver timing sensitivity、scenario scope flag | pending fulltext for AFIT; yes for self-generated | yes | medium after rights+checksum | none |
| `GEB-BM-006 pn_clos_hybrid_swee` | PN vs command-to-line-of-sight vs hybrid bang-bang | `GEB-SRC-012/008/014` | 2D point-mass missile/target；drag-on missile；9-g target evasion；PN/CLOS/hybrid modes | miss distance、guidance mode transitions、drag/velocity profile | yes, self-generated from thesis manifest | yes | medium/high after Matlab or reimplementation manifest | none |
| `GEB-BM-007 seeker_filter_noise` | Track/filter noise 对 miss distance 的影响 | `GEB-SRC-004/007/016/017/021` | range/bearing/elevation noise、sample rate、filter tau、Singer maneuver, track dropout | covariance/proxy, filtered LOS/range, track break/memory, miss distance | generated | yes | high if Stone Soup/A2 commit pinned | none |
| `GEB-BM-008 glint_noise_beam_rider` | Glint/noise/target acceleration/missile accel capability sensitivity | `GEB-SRC-016/017/019` | coplanar beam-rider/homing surrogate；glint magnitude sweep；missile natural frequency/damping；target evasive acceleration | theoretical or simulated minimum miss distance, noise sensitivity, dynamics residual | generated, old-scope | yes | medium; equations and OCR need audit | none |
| `GEB-BM-009 track_memory_fov` | FOV、lock range、track memory 对 guidance continuity 的影响 | `GEB-SRC-004/002/011` + A2 internal | FOV-edge, lock-range edge, terminal local-contact only, datalink denied, dropout shorter/longer than memory timeout | seeker mode, valid track, memory/ballistic transition, miss distance | internal generated | yes | high for A2 tests | none |
| `GEB-BM-010 sixdof_module_boundary` | 6DOF terminal homing simulation module checklist | `GEB-SRC-005/013/018/006` | actuator/autopilot high-low frequency models, target motion, environment, seeker, propulsion/aero modules | module manifest, states, command/response lag, output plot/metric list | no raw dataset; generated architecture checks | yes | medium; AD769595 artifact pending | none |
| `GEB-BM-011 dynamic_flyout_vs_envelope` | Dynamic fly-out 相对 static envelope 的 benchmark 口径 | `GEB-SRC-011/018/005` | fixed launch envelope vs dynamic fly-out; target position at launch vs full fly-out; broad test condition grid | miss distance, reason-for-miss category, compute-cost note, launch-envelope disagreement | yes, generated from public method | yes | medium/high after test-condition manifest | none |
| `GEB-BM-012 a2_effects_bridge` | Miss-distance 到 fuze/effects evidence chain 的内部桥接 | A2 internal + `GEB-SRC-001/005/011` | guidance geometry sweep + target maneuver + fuze type/signature proxy | miss_distance_m、closure、fuze trigger、warhead footprint evidence、DamageReport | internal generated | yes | high in CI once harness pinned | none |

## 验收准则

| area | minimum acceptance | residual flag |
|---|---|---|
| PN | head-on、tail-chase、beam、off-boresight 的 miss distance 不应塌缩成同一结果；LOS-rate sign convention 必须有独立 check。 | `RES-GEB-002` if only 2D/old-scope sources used |
| APN | 只有存在 target acceleration estimate、filter state 或等价建模时才允许声明 APN；否则只能声明 PN/biased PN。 | `RES-GEB-006 apn-estimator-gap` |
| Evasion | 目标机动必须通过 LOS、track、energy、miss distance 影响 outcome；不得直接乘 final Pk。 | `RES-GEB-007 evasion-shortcut-risk` |
| Seeker/filter | dropout、noise、FOV、lock range、track memory 要输出 track state 和 filter residual；不能只输出命中/未命中。 | `RES-GEB-004 seeker-ecm-gap` |
| 6DOF/fly-out | module boundary、time step、integrator、state vector、commanded vs achieved response 要可审计。 | `RES-GEB-008 6dof-parameter-gap` |
| Effects bridge | fuze/effects evidence 可以消费 miss distance 和 closure，但不能把 threshold 变成 deterministic-fuze authority。 | `RES-GEB-009 fuze-authority-deferred` |

## 复现 manifest 模板

```yaml
benchmark_id: GEB-BM-001
status: generated_non_authoritative
source_refs:
  - GEB-SRC-001
  - GEB-SRC-002
rights:
  public_summary_only: true
  copied_tables_or_figures: false
scenario:
  dimensions: 2
  initial_geometry: head_on
  missile_model: point_mass_or_a2_default
  target_maneuver: straight_or_scripted
  guidance_law: PN
  seeker_filter: none_or_declared
numerics:
  dt_s: TBD
  integrator: TBD
  seed: TBD
outputs:
  - truth_min_dist_m
  - proximity_min_dist_m
  - time_of_closest_approach_s
  - los_rate_rad_s
  - closing_speed_mps
  - commanded_accel_mps2
  - achieved_accel_mps2
authority:
  pk: false
  deterministic_fuze: false
  effect_scale: false
  component_failure_probability: false
residuals:
  - RES-GEB-002
```

## 候选优先级

| priority | package | 为什么先做 |
|---|---|---|
| P0 | `pn_classical_miss_distance_v1` | 与当前 A2 baseline 最直接，风险低，能快速发现 LOS/PN/单位错误。 |
| P1 | `terminal_evasion_sweep_v1` | 直接覆盖用户关心的 terminal evasion 与 miss-distance sensitivity。 |
| P1 | `seeker_filter_noise_v1` | 把 evasion 从 final probability 迁移到 track quality、filter lag 和 dropout 输入侧。 |
| P2 | `dynamic_flyout_vs_envelope_v1` | 为 BVR/air-combat simulation 解释为什么不能只用 launch-time envelope 或黑盒 Pk。 |
| P2 | `sixdof_module_boundary_v1` | 为后续更高保真飞控/气动/传感器模块建立 manifest 形状。 |

## 降级与拒绝规则

- 教材公式：可作为 validation criteria，不是 dataset，不是 Pk。
- 论文示例：可重建 toy benchmark，但图表/表格需权利和 OCR 审计。
- NASA/NACA/NTIS/NPS 老报告：可做 old-scope benchmark，不代表现代 AAM。
- MIL-HDBK：可做 simulation-model checklist，不是强制 requirement，不是 AAM truth。
- Stone Soup：可做 filter scaffold，必须 pin commit/version；不代表 missile seeker truth。
- 第三方镜像、论坛、游戏和匿名表格：默认 rejected 或 `sanity_check_only`。
