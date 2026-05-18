<!-- Machine-translated draft generated on 2026-05-18 from docs/standards/services/marine_corps.zh.md. Review before treating this file as authoritative. -->

<!-- Machine-translated draft generated on 2026-05-18 from docs/standards/services/marine_corps.md. Review before treating this file as authoritative. -->

# United States Marine Corps Overview

This document defines the United States Marine Corps profile adopted by the project for amphibious, ground, and air expeditionary modeling.

## 1. Official Real-World Basis

The official Marine Corps `MCDP 1-0` explicitly emphasizes the Marine Corps component and MAGTF organization.

Public official reference:

- [MCDP 1-0 with Changes 1-3](https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/1323621/mcdp-1-0-w-ch-1-3/)

The official page for that document clearly states:

- `MCDP 1-0` focuses on the role of the Marine Corps component at the operational level
- And how the largest MAGTF organizes operations at the tactical level

## 2. Modeling Conclusions

The USMC is not simply:

- An Army ground profile
- + Navy shipboard operations
- + Air Force air support

Its actual organization is closer to:

- `Command Element`
- `Ground Combat Element`
- `Aviation Combat Element`
- `Logistics Combat Element`

Therefore, if the project expands to amphibious or expeditionary scenarios in the future,
the Marine Corps should be an independent service profile, rather than an ad-hoc composite.

## 3. Impact on Project Common Template

The USMC profile indicates that the joint/core layer needs to support:

- Coexistence of multiple combat elements
- Unified command by the command element
- Cross-domain mission relationships (air/ground/logistics)

This further demonstrates:

- The common template should be based on a `Joint/Common Core + Service Profile` architecture
- Rather than directly pushing outward from a single-domain air combat structure
