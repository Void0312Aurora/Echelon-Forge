# Public Mechanism Source Note

Status: `2026-06-16` PF-R1 pass / non-authoritative mechanism note for
[README.md](README.md).

Chinese companion: [public_mechanism_source_note_20260616.zh.md](public_mechanism_source_note_20260616.zh.md).

## Scope Boundary

This note admits only high-level public mechanism facts that can shape a
non-authoritative proximity-fuze surrogate. It does not admit real missile
thresholds, real target-detecting-device logic, classified burst-control logic,
deterministic fuze authority, Pk, or weapon-specific lethality.

## Public Sources Used

| Source | Public fact admitted | Rejected authority claim |
| --- | --- | --- |
| [FAS Naval Weapons, Chapter 14 Fuzing](https://man.fas.org/dod-101/navy/docs/fun/part14.htm) | A fuze system separates safe/arm, target detection or recognition, warhead initiation, and sometimes direction of detonation. Proximity fuzes are target-detecting devices and may use range-gating, Doppler/range-rate, or other influence-sensing methods. | Does not provide an AIM-120C or AIM-120C-class implementation, constants, hidden circuits, or reliability validation. |
| [FAS Naval Weapons, Chapter 13 Warheads](https://man.fas.org/dod-101/navy/docs/fun/part13.htm) | Fragmentation and blast effects attenuate differently; fragment density depends on distance and exposed target area; modern air-target warheads may use directional or annular fragment patterns. | Does not authorize a real aircraft component probability, real warhead pattern, or real stock lethality. |
| [Smithsonian proximity fuze cutaway](https://www.si.edu/object/fuze-proximity-cutaway%3Anasm_A19940233000) | RF proximity fuzes can be understood as transmit/receive target-sensing devices where reflected signals and encounter geometry matter. | Does not provide modern missile fuze parameter truth. |
| [JHU APL Talos continuous-rod paper](https://secwww.jhuapl.edu/techdigest/content/techdigest/pdf/V03-N02/03-02-Brown.pdf) | Continuous-rod warheads should be modeled as a directed cutting mechanism, not as an isotropic blast sphere. | Talos history does not transfer constants or kill authority to the current A2 missile surrogate. |

## Admitted Mechanism Facts

1. The fuze decision is a separate chain, not a distance formula. A usable
   surrogate should keep at least: safing/arming, target detection, fire-signal
   decision, optional delay, and detonation handoff.
2. A proximity fuze senses a target without contact. The relevant event is not
   merely "closest point was inside a radius"; it is "a target return entered a
   usable sensor/warhead opportunity window."
3. The preferred detonation point for an air-target missile is generally not
   the closest-approach point. It depends on relative motion, closure, target
   orientation, warhead pattern, and vulnerable target region coverage.
4. Range and range-rate matter. A public surrogate can model range window,
   closing state, and a delay that depends on closing speed, but cannot claim
   real fuze constants.
5. Target signature matters. Radar/RF, laser/optical, and generic proximity
   sensors may share a common contract but should not share identical evidence
   fields.
6. Warhead mechanism matters. Blast-fragmentation should care about fragment
   density, distance, incidence, and exposed area. Continuous rod should care
   about a lateral cutting band or ring-like sweep relative to the missile axis.
7. No-detonation is a first-class outcome. A target can be near yet fail the
   sensor, track, burst-window, reliability, or mechanism-coverage gate.

## Rejected Claims

- The public sources do not admit real AIM-120C fuze thresholds, delay curves,
  TDD implementation details, warhead pattern, fragment mass distribution, or
  target-kill probability.
- The public sources do not justify deterministic fuze authority.
- The public sources do not justify changing the default runtime path without
  an implementation and validation package.
- The public sources do not justify reward shaping as a substitute for fuze
  realism.

## Consequence For This Subproject

The future surrogate should move from a single nearest-distance trigger proxy to
an event chain:

```text
nearest approach observed
  -> fuze sensor opportunity
  -> target detection / terminal track
  -> trigger or no trigger
  -> detonation point / delay
  -> mechanism-specific coverage
  -> effects or no-load event
```

This remains a research surrogate. It is acceptable for trends and diagnostics;
it is not a calibrated weapon model.
