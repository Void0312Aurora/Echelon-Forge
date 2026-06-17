# A9 Source Ledger — Public-Source Data Admission

Status: `2026-06-16` P1-A pass. 14 entries with full admission fields per
`public_data_source_admission.zh.md`. All entries are `non-authoritative`.

Parent: [../README.md](../README.md)
Standard: [public_data_source_admission.zh.md](../../../../standards/foundation/public_data_source_admission.zh.md)

## Ledger Schema

Each entry records: `source_id`, `tier`, `stable_ref`, `publisher`, `rights`,
`scope_match`, `cross_validation`, `plausibility`, `ingest_status`,
`authority_status`, `residual`.

- `ingest_status`: `pending` = not yet acquired in full; `acquired` = accessed
  and reviewed; `rejected` = reviewed and excluded; `superseded` = replaced.
- `authority_status`: always `non-authoritative` for this ledger.
- `tier`: per standard — `A (official-standard)`, `B (public-engineering)`,
  `C (sanity-check)`.

---

## G1: Augmented Proportional Navigation (APN)

| Field | Entry |
|-------|-------|
| source_id | `LEDGER-A9-G1-001` |
| tier | A (public textbook) |
| stable_ref | Zarchan, "Tactical and Strategic Missile Guidance," 7th Ed., AIAA, 2019. ISBN 978-1-62410-537-1 |
| publisher | AIAA (American Institute of Aeronautics and Astronautics) |
| rights | Copyrighted; fair-use citation of formulas only. Full text not redistributable. |
| scope_match | Classical PN, APN, and optimal guidance derivations apply to generic tactical missiles. NOT AIM-120-specific. |
| cross_validation | Widely cited in DTIC and AIAA literature. Multiple independent textbooks confirm the same ZEM/APN derivation. |
| plausibility | Navigation ratios N'=3–5 and target-accel feed-forward gain 0.5·N' are consistent with open missile-guidance literature. |
| ingest_status | acquired |
| authority_status | non-authoritative |
| residual | Parameters are generic missile guidance theory, not calibrated to any specific weapon. |

| Field | Entry |
|-------|-------|
| source_id | `LEDGER-A9-G1-002` |
| tier | A (public expired patents) |
| stable_ref | US Patents 4456862, 4494202, 4502650 (APN predictive schemes). Available: https://patents.google.com/ |
| publisher | US Patent and Trademark Office |
| rights | Public domain (expired). |
| scope_match | Describes APN implementation with time-varying gains C₂, C₃, C₄. Generic missile application. |
| cross_validation | Consistent with Zarchan and Yanushevsky textbook derivations. |
| plausibility | Patent claims match open-literature APN formulation. |
| ingest_status | acquired |
| authority_status | non-authoritative |
| residual | Expired patents describe mechanism, not calibrated weapon parameters. |

| Field | Entry |
|-------|-------|
| source_id | `LEDGER-A9-G1-003` |
| tier | A (public textbook) |
| stable_ref | Yanushevsky, "Modern Missile Guidance," CRC Press. ISBN 978-1-4200-6226-7. Available: https://ftp.idu.ac.id/wp-content/uploads/ebook/tdg/MILITARY%20PLATFORM%20DESIGN/Modern%20Missile%20Guidance.pdf |
| publisher | CRC Press / Taylor & Francis |
| rights | Copyrighted; fair-use citation. Linked PDF is institutional repository copy. |
| scope_match | APN and optimal guidance derivations; generic missile applications. |
| cross_validation | Consistent with Zarchan. |
| plausibility | Standard reference. |
| ingest_status | acquired |
| authority_status | non-authoritative |
| residual | Generic theory only. |

---

## G2: Kalman Filter Seeker

| Field | Entry |
|-------|-------|
| source_id | `LEDGER-A9-G2-001` |
| tier | A (public technical report) |
| stable_ref | Barton, "Report on Seeker Track Filters," MIT Lincoln Laboratory, 2004. Available: https://dspace.mit.edu/bitstream/handle/1721.1/71781/Barton-2004-Report.pdf |
| publisher | MIT Lincoln Laboratory |
| rights | Publicly released technical report. |
| scope_match | 9-state Cartesian EKF for missile seeker tracking. Process noise σ_a=5 m/s² at Δt=1s. Generic missile application. |
| cross_validation | Consistent with Singer (1970) maneuver model and Bar-Shalom tracking texts. |
| plausibility | Standard reference for missile seeker filtering. |
| ingest_status | acquired |
| authority_status | non-authoritative |
| residual | Process noise values are illustrative for generic missile, not calibrated to specific seeker hardware. |

| Field | Entry |
|-------|-------|
| source_id | `LEDGER-A9-G2-002` |
| tier | A (public journal) |
| stable_ref | Singer, R.A., "Estimating Optimal Tracking Filter Performance for Manned Maneuvering Targets," IEEE T-AES, Vol. 6, No. 4, 1970. DOI: 10.1109/TAES.1970.310128 |
| publisher | IEEE |
| rights | Copyrighted; fair-use citation of model. |
| scope_match | Singer maneuver model (τ_m, σ_m²) for target acceleration. Generic fighter τ_m≈10-20s. |
| cross_validation | Foundation paper; widely validated in tracking literature. |
| plausibility | τ_m values for evasive fighter are consensus estimates, not weapon-specific. |
| ingest_status | acquired |
| authority_status | non-authoritative |
| residual | Generic maneuver time constants; not specific to any aircraft or engagement. |

| Field | Entry |
|-------|-------|
| source_id | `LEDGER-A9-G2-003` |
| tier | B (public DTIC report) |
| stable_ref | DTIC ADA080249, "Seeker Track Filters." Available: https://apps.dtic.mil/ |
| publisher | Defense Technical Information Center |
| rights | Publicly releasable DTIC document. |
| scope_match | Seeker measurement noise: angle 0.5-5 mrad (radar), 0.1-1 mrad (IR). Generic seeker classes. |
| cross_validation | Consistent with Barton 2004 and US Patent 2012/0109538. |
| plausibility | Ranges reflect generic radar/IR seeker classes. |
| ingest_status | acquired |
| authority_status | non-authoritative |
| residual | Generic seeker class values; not calibrated to specific seeker models. |

---

## G3: Three-Loop Autopilot

| Field | Entry |
|-------|-------|
| source_id | `LEDGER-A9-G3-001` |
| tier | A (public journal) |
| stable_ref | KAIST, "The Inverse Optimal Control Problem for a Three-Loop Missile Autopilot," Int. J. Control Autom. Syst., 2018. DOI: 10.1007/s12555-018-0123-5. Available: https://koasas.kaist.ac.kr/handle/10203/244556 |
| publisher | KAIST / Springer |
| rights | Copyrighted; fair-use citation. |
| scope_match | Three-loop (rate/stability/acceleration) topology for generic tail-controlled AAM. τ≈0.08-0.20s. |
| cross_validation | Consistent with World Scientific 2025 and IOP 2019 autopilot papers. |
| plausibility | Standard three-loop topology is well-documented in open autopilot literature. |
| ingest_status | acquired |
| authority_status | non-authoritative |
| residual | τ range is for generic tail-controlled missiles; not AIM-120 or AIM-9 specific. |

| Field | Entry |
|-------|-------|
| source_id | `LEDGER-A9-G3-002` |
| tier | A (public journal) |
| stable_ref | "Optimal Control Approach to Design a Three-Loop Autopilot," World Scientific, 2025. DOI: 10.1142/S2301385025500359 |
| publisher | World Scientific |
| rights | Copyrighted; fair-use citation. |
| scope_match | Three-loop autopilot parameterization with damping ζ≈0.6-0.8. |
| cross_validation | Consistent with KAIST 2018 and IEEE autopilot papers. |
| plausibility | Damping values are standard for control system design. |
| ingest_status | acquired |
| authority_status | non-authoritative |
| residual | Generic control theory; not weapon-specific. |

---

## G4: Proximity Fuze Surrogate

| Field | Entry |
|-------|-------|
| source_id | `LEDGER-A9-G4-001` |
| tier | B (public expired patent) |
| stable_ref | US Patent 20060087472, "System and method for triggering an explosive device." Available: https://patents.google.com/patent/US20060087472 |
| publisher | USPTO |
| rights | Public domain (expired application). |
| scope_match | UWB fuze (3-6 GHz), range shells ~30 cm, N-frame confirmation logic, forward/annular antenna patterns. Generic fuze concept. |
| cross_validation | Consistent with FAS Naval Weapons Ch.14 general fuze principles. |
| plausibility | UWB fuze architecture is a public design concept; not extracted from any operational weapon. |
| ingest_status | acquired |
| authority_status | non-authoritative |
| residual | Patent describes a generic fuze concept, not a specific weapon's fuze parameters. |

| Field | Entry |
|-------|-------|
| source_id | `LEDGER-A9-G4-002` |
| tier | A (public reference) |
| stable_ref | FAS Naval Weapons, Chapter 14 — Fuzing. Available: https://man.fas.org/dod-101/navy/docs/fun/part14.htm |
| publisher | Federation of American Scientists |
| rights | Publicly accessible. |
| scope_match | General fuze types (contact, timed, radar proximity, laser proximity), safe/arm sequence. |
| cross_validation | Consistent with standard ordnance engineering textbooks. |
| plausibility | Textbook-level fuze principles; no weapon-specific data. |
| ingest_status | acquired |
| authority_status | non-authoritative |
| residual | General reference only; no calibrated trigger thresholds. |

**Note:** The PF-R4 surrogate is already implemented and PF-R5 is validated
(pass_with_residuals). These sources support the existing surrogate's
mechanism shape, not new implementation.

---

## G5: Missile Aerodynamics

| Field | Entry |
|-------|-------|
| source_id | `LEDGER-A9-G5-001` |
| tier | A (public military standard) |
| stable_ref | MIL-HDBK-1211(MI), "Missile Flight Simulation Part One: Surface-to-Air Missiles." Available: https://quicksearch.dla.mil/ |
| publisher | US Department of Defense |
| rights | Publicly available military handbook. |
| scope_match | Reference area convention (π·d²/4), Cd₀ estimation, power-on/power-off base drag distinction. Generic missile. |
| cross_validation | Consistent with Fleeman "Tactical Missile Design" and DTIC ADA095118. |
| plausibility | Standard reference for missile simulation. |
| ingest_status | acquired |
| authority_status | non-authoritative |
| residual | Cd₀ values are for generic fineness-ratio-10 body; not AIM-120-specific. |

| Field | Entry |
|-------|-------|
| source_id | `LEDGER-A9-G5-002` |
| tier | A (public experimental data) |
| stable_ref | UNT Digital Library, "Experimental investigation of zero-lift drag of fin-stabilized body of fineness ratio 10 at Mach numbers 0.6-10." Available: https://digital.library.unt.edu/ |
| publisher | UNT / NACA/NASA |
| rights | Public domain (government-funded research). |
| scope_match | Mach-dependent Cd₀ table for generic fineness-ratio-10 missile body. Cd₀ subsonic 0.30-0.45, transonic peak 0.45-0.70, supersonic 0.28-0.40. |
| cross_validation | Consistent with MIL-HDBK-1211 and Fleeman. |
| plausibility | Experimental data for generic body; not a specific weapon. |
| ingest_status | acquired |
| authority_status | non-authoritative |
| residual | Generic body shape; actual missile Cd₀ depends on specific geometry, fins, and protrusions. |

| Field | Entry |
|-------|-------|
| source_id | `LEDGER-A9-G5-003` |
| tier | A (public textbook) |
| stable_ref | Fleeman, E.L., "Tactical Missile Design," 2nd Ed., AIAA, 2006. ISBN 978-1-56347-782-9 |
| publisher | AIAA |
| rights | Copyrighted; fair-use citation. |
| scope_match | Induced drag factor k≈0.6-1.2 for tail-controlled missiles, Mach-dependent. Reference area, drag polar formulation. |
| cross_validation | Consistent with MIL-HDBK-1211. |
| plausibility | Standard missile design textbook. |
| ingest_status | acquired |
| authority_status | non-authoritative |
| residual | Generic design estimates; not calibrated. |

**Engineering proxy table (2026-06-17 follow-up):** A9 now accepts explicit
Mach-indexed tables through `cd0_mach_breakpoints` / `cd0_mach_values` and
`induced_drag_k_mach_breakpoints` / `induced_drag_k_mach_values`. The temporary
proxy uses Mach breakpoints `[0.0, 0.8, 1.0, 1.2, 2.0, 3.0, 4.0]`, Cd₀ values
`[0.30, 0.34, 0.58, 0.52, 0.38, 0.33, 0.31]`, and k(M) values
`[6.0, 7.5, 9.5, 10.5, 9.0, 8.0, 7.0]`. This table follows the public-source
shape above: low/subsonic drag, transonic peak, then supersonic decline. It is
an engineering proxy only, not CFD, not flight-test calibration, and not
weapon-specific.

---

## G6: Warhead Lethality

| Field | Entry |
|-------|-------|
| source_id | `LEDGER-A9-G6-001` |
| tier | A (public reference) |
| stable_ref | FAS Naval Weapons, Chapter 13 — Warheads. Available: https://man.fas.org/dod-101/navy/docs/fun/part13.htm |
| publisher | Federation of American Scientists |
| rights | Publicly accessible. |
| scope_match | Gurney equations (√(2E) Comp B ~2,402 m/s, Octol ~2,560 m/s), fragment velocity decay, kill interval formula, continuous-rod velocity cap <1,150 m/s, rod cutting threshold >610 m/s. Generic warhead engineering. |
| cross_validation | Consistent with Lloyd "Physics of Direct Hit and Near Miss Warhead Technology" and DTIC warhead reports. |
| plausibility | Standard warhead engineering reference. |
| ingest_status | acquired |
| authority_status | non-authoritative |
| residual | General warhead physics; not calibrated to any specific weapon warhead. |

| Field | Entry |
|-------|-------|
| source_id | `LEDGER-A9-G6-002` |
| tier | A (public journal) |
| stable_ref | JHU APL Technical Digest, Vol. 3, No. 2, "Talos Continuous-Rod Warhead." Available: https://secwww.jhuapl.edu/techdigest/content/techdigest/pdf/V03-N02/03-02-Brown.pdf |
| publisher | Johns Hopkins APL |
| rights | Publicly accessible. |
| scope_match | Continuous-rod expansion kinematics, weld-limited velocity cap, rod opening radius vs. time. |
| cross_validation | Consistent with FAS Ch.13 and DTIC rod warhead reports. |
| plausibility | Well-documented historical continuous-rod design; not a current weapon. |
| ingest_status | acquired |
| authority_status | non-authoritative |
| residual | Talos is a historical (1950s) system; modern continuous-rod designs may differ. |

| Field | Entry |
|-------|-------|
| source_id | `LEDGER-A9-G6-003` |
| tier | A (public textbook) |
| stable_ref | Lloyd, R.M., "Physics of Direct Hit and Near Miss Warhead Technology," AIAA, 2001. ISBN 978-1-56347-473-6 |
| publisher | AIAA |
| rights | Copyrighted; fair-use citation. |
| scope_match | Fragment velocity, fragment decay, directional warhead efficiency, kill probability formulation P=1-e^(-N_d·S_v). |
| cross_validation | Consistent with FAS Ch.13. |
| plausibility | Standard warhead physics reference. |
| ingest_status | acquired |
| authority_status | non-authoritative |
| residual | Generic warhead physics; not weapon-specific. |

---

## Illustrative / Sanity-Check Only (Not Used As Defaults)

The following parameter values are publicly known physical dimensions or
open-source fact-sheet data for the AIM-120 AMRAAM. They are recorded here
for **sanity-check and illustrative purposes only**:

- They are NOT used as default simulation parameters.
- They are NOT calibration targets.
- They do NOT imply AIM-120C-specific modeling authority.
- They are Tier C (open-source fact sheet / encyclopedia) at best.

| Parameter | Value | Source | Retrieval | Admission |
|-----------|-------|--------|-----------|-----------|
| AIM-120 body diameter | ~178 mm (7 in) | Open-source fact sheets (generalstaff.org, Wikipedia) | 2026-06-16 | `sanity_check_only` — illustrates reference area order-of-magnitude (~0.025 m²). NOT used as default S_ref. |
| AIM-120 warhead mass | ~22 kg (WDU-33/B) | Open-source fact sheets | 2026-06-16 | `sanity_check_only` — illustrates warhead mass order-of-magnitude for a medium-range AAM. NOT used as default warhead_mass_kg. |
| AIM-120 warhead type | Blast-fragmentation (prefragmented) | Open-source fact sheets | 2026-06-16 | `sanity_check_only` — illustrates that AIM-120 uses blast-frag, not continuous-rod. NOT used as mechanism-family default. |
| AIM-120 length | ~3.66 m | Open-source fact sheets | 2026-06-16 | `sanity_check_only` — illustrates missile scale. NOT used in simulation. |
| AIM-120 launch mass | ~152 kg (A/B) | Open-source fact sheets | 2026-06-16 | `sanity_check_only` — illustrates mass order-of-magnitude. NOT used as default. |

**Rule**: Any A9 implementation that needs a default parameter value MUST use
the generic estimates from the G1-G6 ledger tables above, NOT these AIM-120
illustrative values. If a scenario or test explicitly configures AIM-120-like
parameters, it must do so via explicit JSON/config override with a comment
citing the open-source provenance and the `sanity_check_only` caveat.

---

## Rejected Sources

The following source categories are explicitly NOT used and must NOT be
introduced into any A9 artifact:

| Category | Reason | Reference |
|----------|--------|-----------|
| ITAR/EAR-controlled technical data | Export-restricted; cannot be stored or referenced in this repository | Standard §拒絕來源 |
| Classified or FOUO weapon manuals | Not publicly available; possession would violate security policy | Standard §拒絕來源 |
| Leaked/unauthorized specifications | No provenance; cannot verify authenticity or rights | Standard §拒絕來源 |
| Proprietary defense contractor simulation data | Not publicly licensed; unclear rights | Standard §拒絕來源 |
| Forum/game/commercial-sim parameter sets | No provenance; typically balanced for gameplay, not physics | Standard §Tier C / rejected |
| Anonymous Pk curves or hit-rate graphs | No source, no methodology, no verifiability | Standard §拒絕來源 |
