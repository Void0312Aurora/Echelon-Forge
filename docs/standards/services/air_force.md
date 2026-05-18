<!-- Machine-translated draft generated on 2026-05-18 from docs/standards/services/air_force.zh.md. Review before treating this file as authoritative. -->

<!-- Machine-translated draft generated on 2026-05-18 from docs/standards/services/air_force.md. Review before treating this file as authoritative. -->

# USAF Profile

This document defines the USAF profile adopted by the project when modeling air combat/air operations.

## 1. Official Real-World Foundation

The official USAF `AFDP 3-0.1, Command and Control` explicitly places air power C2 under the Air Component Commander framework, and emphasizes:

- The Air Component Commander may also serve as `COMAFFOR` and `JFACC`
- The specific delegation of `OPCON` and `TACON` is decided by the JFC
- USAF adopts `Centralized Command – Distributed Control – Decentralized Execution`

Official source:

- [AFDP 3-0.1, Command and Control](https://www.doctrine.af.mil/Portals/61/documents/AFDP_3-0_1/AFDP3-0.1CommandandControl.pdf)

## 2. Modeling Conclusions

### 2.1 Layers that Should Not Enter the Tight-Loop Runtime

- Air Component Commander
- AOC
- Wing / MAJCOM / NAF and other administrative or theater-level structures

These layers are suitable as:

- Scenario development
- Mission authorization
- Campaign / operation metadata

### 2.2 Layers that Should Enter the Tight-Loop Runtime

For the current project, the air combat tight-loop runtime is better placed at the sortie-level tactical units:

- Mission package
- Flight
- Element
- Aircraft

Note:

- This is an inductive summary in project modeling, not a claim that AFDP verbatim prescribes all sortie-level details.
- Its basis is the USAF official doctrine's description of the Air Component Commander, subordinate echelons, distributed control, and wing-level and intermediate echelon authorities.

## 3. Direct Constraints on the Project

Under the air combat profile, the following can be used:

- Patrol
- Intercept
- Escort
- Recovery

And further subdivided within air specialization into:

- `CAP`
- `BARCAP`
- `TARCAP`
- `RTB`
- Landing / Approach

That is:

- `CAP` should not be a native task family at the joint/core layer
- `CAP` should be the air profile's concretization of patrol

## 4. Organizational Level Recommendations

If the current project primarily uses the USAF air tactical profile, the following may be adopted initially:

- Mission package
- Flight
- Element
- Aircraft

And further distinguish:

- Command/tactical role
- Execution/platform role

This aligns with reality and facilitates future expansion to two-ship, four-ship, and multi-mission packages.

## 5. Corresponding Platform-Specific Standards

The air/platform refinement standards under this profile are currently located at:

- [Air Platform-Specific Standards Overview](../air/README.md)
- [Pilot Observation Space Standard](../air/obs.md)
- [Pilot Action Space Standard](../air/act.md)
- [Mission Command Standard](../air/aim.md)
- [Pilot Reporting Standard](../air/rep.md)
