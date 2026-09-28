# Carrier Strike Group Engagement Acceptance Gate

Document kind: `task`
Lifecycle: `maintained`
Canonical: `docs/domains/naval/work/active/carrier_strike_group_engagement/carrier_strike_group_engagement_acceptance_20260928.md`
Owner: `domains/naval`
Last verified: `2026-09-28`

Status: `2026-09-28`; decision `not accepted`. No stage has been accepted.

Parent project: [Carrier Strike Group Engagement](README.md)

## Acceptance Decision

Current decision: `not accepted`. The package is in `P0 Boundary`.

## Stage Gates

A stage is accepted only when its acceptance cluster records all of:

1. both the named and the symmetric-mirror scenario run on the maintained
   runtime for their full stated duration;
2. focused tests pass for every mechanism the stage added;
3. the stage's claim ceiling is met by maintained evidence, not a
   diagnostics-only path;
4. a throughput record exists (entities, fixed step, simulated duration,
   wall-clock, host);
5. a replay artifact and visualization profile exist;
6. every new named-platform parameter has a provenance record;
7. lower-stage scenarios still pass; a regression below blocks the stage
   (Claim Rule 5).

| Stage | Claim ceiling | Stage-specific requirement | Status |
| --- | --- | --- | --- |
| `CSG-S0` | `G0` | full order of battle spawns with identity, side, and position; geodetic frame in use | planned |
| `CSG-S1` | `G1`-`G2` | formations hold through turns; damage reduces mobility through the maintained path | planned |
| `CSG-S2` | `G3` | launch and recovery rates are bounded by deck resources; CAP is sustained | planned |
| `CSG-S3` | `G4` | group picture forms from sensors and data links with no truth reads | planned |
| `CSG-S4` | `G5` | anti-ship strike, layered defense, soft-kill, and leaker damage close one causal chain | planned |
| `CSG-S5` | `G6` | two-sided strikes with escort, jamming, and depletion | planned |
| `CSG-U1` | `G1`-`G2` | submarine noise tracks speed and depth | planned |
| `CSG-U2` | `G4` | undersea detection with no truth reads | planned |
| `CSG-U3` | `G5` | torpedo engagement including countermeasures and flooding damage | planned |
| `CSG-S6` | `G6` | adjudicated termination in named and mirror variants; RL boundaries exercised | planned |

## Package Acceptance

The package is accepted when every stage above is accepted, the conditions in the
[README acceptance gate](README.md#acceptance-gate) hold, and the naval owner
README and indexes point at the accepted record.

## Fail-Closed Rules

- A stage that needs an unsourced, calibrated-looking coefficient to pass is
  `partial`, not accepted.
- A stage whose sensing path reads true state while claiming `G4` or higher fails.
- A stage that passes only on the mirror variant is `partial`.
- Any claim of learned-policy quality or real-world prediction fails the package.
