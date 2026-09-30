# P11 Expectation Rebaseline Independent Review Decision

Review date: `2026-09-15`

Review mode: read-only independent-agent review; treated as equivalent to
manual review by project decision

Reviewed revision: `5ae8e06ae5a8a0cfcaac34f157800b42b90c2eda`

Verdict: `accept-with-residuals`

## Accepted Scope

- Accept the 93-cell candidate N/M/O mapping: `N=63, M=2, O=28`.
- Permit the expectation harness to adopt that exact candidate matrix.
- Keep the two mild-maneuver, 6 km, +/-60-degree cells as `M`:
  `kces_anchor_grid_mild_6km_m60deg` and
  `kces_anchor_grid_mild_6km_p60deg`.
- Retain `seeker_fov_exit_then_memory_timeout` as the reason for both
  residuals.
- Limit acceptance to a synthetic engineering expectation contract. It grants
  no real AIM-120, deterministic-fuze, lethality, or Pk authority.

## Review Results

- The integrated evidence contained 279 unique `(case_id, seed)` runs and 93
  unique cells; every cell contained seeds `20260621`, `20260622`, and
  `20260623`.
- All 279 runs reported `structural_consistent=true`.
- Independent recomputation produced 189 runs / 63 cells in
  `complete_effect_chain`, 6 runs / 2 cells in `in_radius_fuze_blocked`, and 84
  runs / 28 cells in `outside_no_load`.
- All 49 label changes matched the candidate mapping. Angular topology showed
  no mirror inconsistency or off-axis miss-to-hit reversal.
- Terminal-track sensitivity covered 2 cases x 8 timeouts x 3 seeds:
  `0.25-0.50 s` remained outside, `0.75-2.00 s` remained in-radius blocked,
  and `3.00-5.00 s` completed the chain.
- Sensitivity explains dependence on the memory window. It does not prove that
  `0.75 s` is wrong or authorize `3.0 s` as a production default.

## Findings And Disposition

- High: none.
- Medium: the rebaseline and timeout-sensitivity gates must verify unique
  case/seed tuples, complete Cartesian products, exact seed sets per cell,
  nonempty residual causes, and recovery in both mirror cases. These checks
  were required when adopting the new harness.
- Low: normalize an empty integrated-report `outcome_state` to its chain state
  for downstream JSON compatibility.

## Not Accepted

- P11 complete remains `false`.
- No change to `track_break_time_s`, seeker FOV, the terminal-fuze support
  gate, or the AIM-120 database definition is authorized.
- The remaining substantive blocker is the terminal-track runtime contract,
  including stale-track risk, tracking semantics, and fuze-safety impact of a
  longer memory window.
