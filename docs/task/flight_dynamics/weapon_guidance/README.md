# Weapon And Guidance Subproject

Language:
- English canonical: `README.md`
- Chinese companion: [README.zh.md](README.zh.md)

Status: `2026-05-17` with `P0/P1` implementation packages already formed. The
current framing is taken from the analysis doc closure markers, not
`program/` or `archive/`.

This subproject collects documents for the weapon chain, seekers, guidance
loops, proximity fuzes/damage, and their reference-data plans.

## Document Entry Points

- [weapon-system and guidance-loop realism analysis](weapon_guidance_realism_analysis_20260516.zh.md)
  - Frozen record of the main current distortion points in the weapon chain and
    missile guidance behavior.
## Maintenance Conventions

1. Future weapon-parameter reference tables, seeker calibration notes, and
   external data-source notes should land here first.
2. If missile-database or fuze-specific subtracks are split out later, keep
   layering them under this directory instead of moving back to the
   `flight_dynamics/` top level.
