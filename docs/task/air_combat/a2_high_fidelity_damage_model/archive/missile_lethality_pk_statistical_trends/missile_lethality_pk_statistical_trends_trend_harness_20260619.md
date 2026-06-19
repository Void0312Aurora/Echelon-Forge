# MLF-9 Trend Harness Result

Status: `2026-06-19` P3 initial pass.

Companion:
[missile_lethality_pk_statistical_trends_trend_harness_20260619.zh.md](missile_lethality_pk_statistical_trends_trend_harness_20260619.zh.md).

## Result

`tools/diagnostics/mlf9_statistical_trends.py` now provides a deterministic
row-level trend summarizer for MLF-9. It consumes an explicit list of
`lethality_chain_rows` or a JSON object containing that field, groups rows by
`chain_id`, derives chain records, and emits bounded simulation trend summaries.

The implementation is intentionally downstream-only. It does not change fuze,
warhead, component, structural, consequence, lifecycle, reward, deletion, or
calibration behavior.

## Report Shape

The summary payload includes:

- `schema_version`: `mlf9.statistical_trends.v1`.
- `confidence_level`, `confidence_z`, and `interval_method`.
- `group_by`, `chain_count`, and one entry per requested group.
- denominator counts for chain, released, detonated, component-damage,
  structural-breakup, and platform-consequence chains.
- outcome counts for fuze negatives, effective component damage, structural
  breakup, airframe breakup, functional kill, and terminal lifecycle.
- rate records with success count, sample count, rate, and Wilson interval
  bounds.
- explicit authority-boundary flags refusing real-world Pk, weapon-specific
  lethality, target-specific lethality, calibration authority, reward
  authority, and entity-deletion authority.

## Controlled Fixture Coverage

`tests/tools/test_mlf9_statistical_trends.py` covers:

- denominator counts across released, component-damage, structural-breakup, and
  platform-consequence chains.
- outcome counts for fuze negative, component damage, structural breakup,
  airframe breakup, and terminal lifecycle.
- Wilson-bounded rates for structural breakup given component damage and
  terminal lifecycle given structural breakup.
- grouping by miss-distance bucket and breakup mode.
- non-claim flags that keep the payload inside synthetic simulation trend
  authority.

## Validation

```bash
python3 -m py_compile tools/diagnostics/mlf9_statistical_trends.py
PYTHONPATH=build-workshop:. pytest -q tests/tools/test_mlf9_statistical_trends.py
```

Result:

- `2 passed`.

## Boundary

This is not a calibrated Pk model. It is a deterministic summarizer over rows
that the simulation already produced. Real weapon Pk, target-specific lethality,
public-outcome validation, source-admission promotion, and calibration gates
remain held for MLF-10 or later work.
