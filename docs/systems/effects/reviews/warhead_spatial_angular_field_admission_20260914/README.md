# Warhead Spatial Angular-Field Admission

Status: fragmentation angular-field admission passed; overall warhead spatial-field admission remains held.

This review extends the retained 384-row spatial matrix with a model-owned
polar/azimuthal fragmentation density and a switchable near-field floor. It
continues to bypass guidance and fuze decisions and uses a synthetic warhead
profile against the maintained F-16C hitbox envelope.

## Evidence boundary

- The database is loaded read-only. No default weapon or aircraft parameter is
  modified by the probe.
- The angular profile is synthetic: `polar_azimuthal`, concentration `0.5`,
  isotropic fraction `0.55`, two azimuthal lobes, and `0.10` modulation. These
  values demonstrate the field path; they are not calibrated weapon data.
- Guidance, tracking, and fuze decisions remain bypassed. No integrated kill
  probability or lethality claim is made.
- Continuous rod remains a legacy side-sweep surrogate and is explicitly
  regression-checked rather than retuned in this batch.

## Model-owned angular field

For fragmentation rows, the model now exports the signed polar cosine, polar
angle, azimuth, polar density, azimuth density, and mixed angular density. The
mixed density is applied to the fragmentation spatial pattern; legacy scalar
profiles retain the previous absolute-dot behavior. The profile and every
exported sample are visible in the event DTO and Python bindings.

## Results

The full matrix contains 384 rows: two families, six directions, four
standoffs, and eight detonation headings.

- Projection trace: 384/384 valid; all post-clamp, pre-clamp, candidate
  aggregate, and flag-closure checks passed.
- Fragmentation angular field: 192/192 rows active; zero distance-monotonic,
  bilateral-mirror, or axial (front/back) orientation-sign residuals. The
  family-specific adjacent 45-degree maximum is `0.09224384286905474`.
- The report retains 10 non-axial sign-collapses for fragmentation. They occur
  only in right/left/up/down cases where the radial sample is equatorial to the
  orientation frame, so a polar distribution is expected to be symmetric in
  the 0/180 comparison. They are reported, not silently discarded.
- Continuous-rod regression: 192/192 rows compared with
  `warhead_spatial_structural_admission_baseline_20260913.json`; mismatch count
  is zero across the spatial, mechanism, hit-estimate, and rod-cut fields.
- Near-field floor ablation: 24 paired cases; the enabled switch applied in
  12 pairs, the disabled switch applied in 0 pairs, and 12 pairs changed the
  effect scale. The maximum paired delta is `0.040703117619857065`.

## Admission decision

The diagnostic trace gate and fragmentation angular-field admission pass. The
overall warhead spatial-field admission remains held because continuous rod
still lacks an explicit expanding ring-band versus target-geometry
intersection. Component-load admission and integrated kill-chain admission are
not evaluated in this review.

## Reproduction

From this worktree, after building the matching extension:

```powershell
$env:CMO_BUILD_DIR = 'D:\workshop\Research\Echelon-Forge\build-warhead-spatial-admission-vs'
python tools/geometry/warhead_spatial_structural_admission.py
```

The generated packet is
`review_packets/warhead_spatial_angular_field_admission_20260914.json`.

The human-readable inline heatmaps are in `warhead-spatial-evidence.html`; a
static PNG is provided as `warhead-spatial-evidence.png`. Both can be
regenerated from the packet with the corresponding render scripts under
`tools/geometry/`.
