# Warhead Spatial Structural Admission

Status: baseline probe implemented; integrated kill-chain admission is not claimed.

This review isolates the warhead spatial field from guidance and fuze decisions. The
probe places a synthetic warhead from the maintained F-16C hitbox envelope in six local directions, four standoff
distances, and eight detonation headings for both `blast_fragmentation` and
`continuous_rod`. Each row enters the real `DefaultEffectsModel` path through the
attitude-aware diagnostic API.

## Evidence boundary

- The database is loaded read-only; no default weapon or aircraft parameter is
  modified by the probe.
- The warhead profile is synthetic. The output is not a real-weapon `Pk`, damage,
  or lethality claim.
- Guidance, tracking, and fuze decisions are bypassed deliberately. This is a
  spatial-field admission, not an integrated kill-chain admission.
- Component response and platform consequence remain downstream observations;
  they are not used to retune the spatial field in this batch.

## Model-owned trace

The event now exports the candidate decomposition used by the model:

`base -> max(base, near_field_floor) -> axis * orientation * armor * exposure * sampling -> clamp`

The exported trace includes the two clamp bounds and explicit booleans for floor
application and final clamping. The report treats the decomposition and clamp
identity as hard gates. Distance monotonicity, mirror behavior, rotation-step
size, and orientation sign symmetry are reported as structural residuals so a known model limitation
cannot be hidden by a Python-side reimplementation.

## Baseline result

The retained 384-row matrix closes the model-owned decomposition on every row.
It records zero distance-monotonic and bilateral-mirror violations. The near-field
floor is selected in 66 rows and the final clamp is active in 50 rows. Forty-eight
0/180-degree comparisons have identical orientation weights, and the largest
adjacent 45-degree effect-scale change is `0.3717697996152012`.

The diagnostic trace gate passes, but warhead spatial-field admission remains
held. Fragmentation is still a spherical-density field with scalar directional
weights, and continuous rod still lacks an explicit expanding ring/band versus
target-geometry intersection. Component-load and integrated kill-chain admission
therefore remain unevaluated.

## Run

From this worktree, after building the matching extension:

```powershell
$env:CMO_BUILD_DIR = 'D:\workshop\Research\Echelon-Forge\build-warhead-spatial-admission-vs'
python tools/geometry/warhead_spatial_structural_admission.py
```

The generated raw JSON packet is retained outside the repository under
`artifacts/kill_chain/20260915/raw_review_packets/warhead_spatial_structural_admission_20260913/warhead_spatial_structural_admission_baseline_20260913.json`.
A non-zero exit code means the model-owned hard decomposition did not close.
