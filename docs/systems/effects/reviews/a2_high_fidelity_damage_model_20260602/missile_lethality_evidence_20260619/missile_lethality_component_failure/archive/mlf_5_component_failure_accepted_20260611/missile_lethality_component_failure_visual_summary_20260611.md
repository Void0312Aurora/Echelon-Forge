# A2 MLF-5 Visual Summary

Status: `2026-06-11` retained visual evidence. Chinese main text: [missile_lethality_component_failure_visual_summary_20260611.zh.md](missile_lethality_component_failure_visual_summary_20260611.zh.md).

This page turns the expanded aspect/distance matrix into heatmaps. Darker cells mean a higher rate where at least one component sampled a failure. Gray blanks mean that aspect did not include that offset point; they are not zero-rate cells.

## How To Read

- Rows: incoming aspect or offset mode.
- Columns: test offset in meters.
- Cell value: rate where at least one component sampled failure across 64 reset seeds.
- `D`: the point enters the target hitbox. It is a direct hit and should not be read as the same distance curve as an ordinary proximity or grazing point.
- Right-high/right-low rows: fixed right beam at 6 m, then vertical offset changes; column `0` means no vertical offset.
- These graphics cover component failure sampling only, not crash, breakup, or real weapon Pk.

## Blast/Fragmentation

![Blast/fragmentation heatmap](missile_lethality_component_failure_blast_fragmentation_heatmap_20260611.svg)

Plain reading: blast/fragmentation responds on nose, tail, top, bottom, and beam aspects at close range, then fades quickly with distance. Tail 6 m direct hit is now stronger than tail 8 m proximity, avoiding the earlier false valley where a direct hit looked weaker than a nearby miss.

## Continuous Rod

![Continuous rod heatmap](missile_lethality_component_failure_continuous_rod_heatmap_20260611.svg)

Plain reading: continuous rod is more aspect-sensitive. Beam, top, bottom, and diagonal cut exposure are strong; ordinary non-direct nose/tail grazing is much weaker. Nose 4 m is non-direct grazing while nose 6 m is direct impact, so the jump from near zero to high response is a category change, not a mesh penetration bug.

## Short Conclusion

- Ideal near-miss cases are now high-risk rather than about 10%.
- Edge distance still decays quickly, and outside projection is zero.
- Blast/fragmentation behaves like close multi-aspect coverage.
- Continuous rod behaves like aspect-sensitive sweep/cut exposure.
