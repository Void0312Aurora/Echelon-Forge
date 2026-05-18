# US Army Profile

This document defines the US Army profile used by the project when modeling land warfare and ground operations.

## 1. Official Real-World Baseline

Official Army material shows that the key organizing idea is not an Air-Force-style air component C2 structure, but echeloned formations plus command and control / mission command.

Current public official references:

- [Army MCCoE](https://usacac.army.mil/Organizations/Centers-of-Excellence-CoE/MCCoE)
- [Army doctrinal references](https://www.ikn.army.mil/apps/IKNHostedWebsites/Home/LoadPublishedPage?PageUID=30c204aa-de54-471a-8252-2df7d9f5a5cc)
- [Army force structure reference](https://www.army.mil/core/support/best-practices/ap/ap_stylebook_quick_reference.html)

These official pages confirm that:

- The Army currently uses the `Command and Control Warfighting Function`.
- The current public doctrinal baseline includes `ADP 3-0 (March 2025)`, `ADP 6-0 (July 2019)`, `FM 3-90 (May 2023)`, `FM 3-96 (January 2021)`, and `FM 3-94 (July 2021)`.
- The Army has a stable conventional hierarchy: `squad/section -> platoon -> company/troop/battery -> battalion/squadron -> brigade -> division -> corps -> army`

## 2. Modeling Conclusions

### 2.1 Echelons That Should Not Enter the Tight-Loop Runtime

- corps
- division
- brigade

These echelons fit better as:

- scenario / campaign tasking
- operational-level resource and boundary setting

### 2.2 Echelons Better Suited for the Tight-Loop Runtime

- `squad / section`
- `platoon`
- `company / troop / battery`

If the project later expands into land-warfare modeling, the tight-loop tactical unit should be centered on these echelons first.

## 3. Impact on the Project's Common Template

The land-warfare profile shows that:

- the air-combat `element / wingman` structure cannot be generalized directly to land operations
- land modeling needs more emphasis on:
  - echelon-aware task organization
  - support / supported relationships
  - separation of maneuver elements, fires, and sustainment

Therefore, the joint/core layer should preserve:

- `tactical_unit_type`
- `supported/supporting relation`
- `role_code`

rather than hardcoding air-combat terminology.
