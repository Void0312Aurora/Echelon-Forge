# RB10 CUDA-Resident Continuation Decision: Hold

Language versions:

- English canonical: `cuda_resident_rb10_hold_decision_20260731.md`
- Chinese companion: [cuda_resident_rb10_hold_decision_20260731.zh.md](cuda_resident_rb10_hold_decision_20260731.zh.md)
- Machine-readable record: [cuda_resident_rb10_hold_decision_20260731.json](cuda_resident_rb10_hold_decision_20260731.json)

- Decision id: `rb10.hold.cuda_resident.20260731`
- Owner: exact-runtime / CUDA-resident backend workline
- Authority: branch-local CUDA-resident program
- Basis: mechanical application of the frozen RB10 gates to RB9 commit
  `c21757908bcd4c7c323215bba2e8c3afbbfa7e2c`
- Date: `2026-07-31`

## Outcome

**Hold the CUDA-resident backend as an unmaintained research candidate.** RB10
does not authorize RuntimeFacade promotion, support projection, capability
expansion, kernel/launch tuning, or a spatial/sensor/communications slice.
The maintained CPU backend remains the default and no public ABI changes.

The only next action authorized by this program is RB11 closure without
promotion: audit the rollback/retention boundary, confirm maintained state is
unchanged, and close the branch-local program record.

## Gate application

| Frozen RB10 gate | RB9 evidence | Result |
| --- | --- | --- |
| Full facade/window advance is measured | CUDA uses the private `inject -> publish_stage -> advance` sequence; `publish_stage` is absent from `IWorldBatchBackend` | Fail |
| CPU and CUDA invocation surfaces are equivalent | `backend_spi_world_batch` versus `backend_private_phase_sequence` | Fail |
| Learner-equivalent consumption is measured | The device consumer is diagnostics smoke with hidden host validation readback | Fail |
| Required hardware metrics are complete | Achieved counters are unavailable with `ERR_NVGPUCTRPERM` | Fail |
| Selected-slice parity can leave quarantine | RB8 selected-slice parity remains quarantined | Fail |
| Small-batch default does not regress | World `1` regresses in P50, P95, and rollout P50 | Fail |

RB9 reports a provisional internal threshold at world `4`, and worlds `4+`
show large timing deltas in the private comparison. Those values remain useful
diagnostics, but they are not a promotion gate because the compared invocation
surfaces and collection paths are not equivalent. The decision therefore
preserves `hold_required`, `required_metrics_complete=false`,
`break_even_eligible=false`, and `promotion_allowed=false`.

## Evidence identity

- RB9 comparison: `cd3d444a6171c32c0bc34d8e2ec23cd17d964d48a162a0c1f12979fa567e9840`
- CPU lane: `1a5bd2d1970621d8f808774b90c85953583d4151fc5d9dd1392adefafe28b4be`
- CUDA lane: `f03fc930f0781fc8f79aaf09d5bff4d1042c954e0a07516ad85642099d5dd94c`

No human promotion approval is recorded. This hold is the fail-closed result
of the already-frozen program gates, not a claim that the candidate has no
future research value. Reopening implementation work requires a new,
explicitly authorized program and new full-facade evidence; it is outside
RB10-RB11.

## Action boundary

Allowed now:

- retain the branch-local candidate and compact RB9 evidence;
- perform the RB11 closure audit without promotion.

Forbidden in this workline:

- RuntimeFacade promotion, capability-manifest expansion, or support-flag
  changes;
- CUDA-window CPU fallback;
- kernel/launch tuning or register-pressure experiments;
- spatial, sensor, or communications semantic expansion.
