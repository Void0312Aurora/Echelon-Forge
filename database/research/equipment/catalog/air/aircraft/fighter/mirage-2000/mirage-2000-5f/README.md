# Mirage 2000-5F

Language: English canonical. Chinese companion: not established.

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/research/equipment/catalog/air/aircraft/fighter/mirage-2000/mirage-2000-5f/README.md`
Owner: `database/equipment-data`
Last verified: `2026-09-17`
Equipment ID: `eq-fr-air-mirage2000-5f`
Content status: parameter table present with per-field source and confidence. Retrieval status is recorded per package in each manifest's `Retrieval:` block. This leaf previously carried no parameter table at all; the table below was built on 2026-09-17.

## Identity

- Family: Mirage 2000
- Variant: Mirage 2000-5F
- Role: Single-seat air-defence fighter
- Manufacturer: Dassault Aviation
- Configuration scope: the French air-defence rebuild of the Mirage 2000C, entered service 1999. It is a single-seat airframe of the 2000C geometry with new radar and mission equipment. The two-seat 2000D and 2000N and the export 2000-5 marks are separate configurations.

## Operators

| Operator | Status | Source |
| --- | --- | --- |
| French Air and Space Force | In service | `p5-fr-air-mirage2000-5f` |

## Parameters

| Parameter | Value | Source | Confidence |
| --- | --- | --- | --- |
| Role | Single-seat air-defence variant | `p5-fr-air-mirage2000-5f` | A |
| Entry into French service | 1999 | `p5-fr-air-mirage2000-5f` | A |
| Length | 14.36 m (47 ft 1 in) | `p5-fr-air-mirage2000-gs` | C |
| Wingspan | 9.13 m (30.0 ft) | `p5-fr-air-mirage2000-gs` | C |
| Height | 5.20 m (17.1 ft) | `p5-fr-air-mirage2000-gs` | C |
| Wing area | 41.0 m² (441 ft²) | `p5-fr-air-mirage2000-gs` | C |
| Empty weight | 7,500 kg (16,500 lb) | `p5-fr-air-mirage2000-gs` | C |
| Maximum takeoff weight | 17,000 kg (37,500 lb) | `p5-fr-air-mirage2000-gs` | C |
| Internal fuel capacity | 3,080 kg (6,790 lb) | `p5-fr-air-mirage2000-gs` | C |
| External stores capacity | 6,300 kg (13,900 lb) | `p5-fr-air-mirage2000-gs` | C |
| Hardpoints | 9 | `p5-fr-air-mirage2000-gs` | C |
| Powerplant | One SNECMA M53-P2 afterburning turbofan | `p5-fr-air-mirage2000-gs` | C |
| Thrust (survey-page reading) | 54 kN (12,000 lbf) dry and 95 kN (21,400 lbf) with afterburner | `p5-fr-air-mirage2000-gs` | C |
| Thrust (2000-5F page reading) | 64 kN dry and 95 kN with afterburner | `p5-fr-air-mirage2000-5f-armyrecognition` | C |
| Thrust (2000C page reading) | 64.3 kN (14,455 lbf) dry and 95.1 kN (21,379 lbf) with afterburner | `p5-fr-air-mirage2000d-flugzeuginfo` | C |
| Maximum speed | Mach 2.2 (2,340 km/h) at altitude; 1,350 km/h at sea level | `p5-fr-air-mirage2000-gs` | C |
| Maximum speed (2000-5F page reading) | Mach 2.2 (2,336 km/h) | `p5-fr-air-mirage2000-5f-armyrecognition` | C |
| Service ceiling | 17,060 m (56,000 ft) | `p5-fr-air-mirage2000-gs` | C |
| Combat radius | 1,550 km (960 mi) | `p5-fr-air-mirage2000-gs` | C |
| Ferry range | 3,335 km (2,070 mi) with auxiliary fuel | `p5-fr-air-mirage2000-gs` | C |
| Rate of climb | 285 m/s at sea level | `p5-fr-air-mirage2000-gs` | C |
| Load limits | +9.0 / −4.5 g | `p5-fr-air-mirage2000-gs` | C |
| Radar | Thales RDY multimode radar | `p5-fr-air-mirage2000-5f-armyrecognition` | C |
| Self-protection | SPECTRA suite covering electronic warfare, missile warning and jamming | `p5-fr-air-mirage2000-5f-armyrecognition` | C |
| Navigation | GPS-aided inertial navigation system | `p5-fr-air-mirage2000-5f-armyrecognition` | C |
| Helmet-mounted display | Fitted | `p5-fr-air-mirage2000-5f-armyrecognition` | C |
| Datalink | NATO-compatible Link 16 | `p5-fr-air-mirage2000-5f-armyrecognition` | C |

## Configuration Boundary

This leaf carried no parameter table before 2026-09-17. The official French source held for it states the role and the service entry year and no dimension, mass or performance figure, which is why every technical row is Tier C.

The 2000-5F is a rebuild of the single-seat 2000C, so the geometry and mass rows are the 2000C readings from the GlobalSecurity specification page, whose crew field is 1 and which lists the two-seat airframes separately as the B, D and N. They are recorded as 2000C geometry, not as measurements of the 2000-5F airframe, which differs in mission equipment rather than in size.

The thrust carries three readings for the same engine: 54 kN dry from the GlobalSecurity page, 64 kN dry from the Army Recognition 2000-5F page and 64.3 kN dry from a page the site itself labels as the 2000C. The afterburner figures are 95 kN and 95.1 kN. No reading is preferred and none is averaged, because no package states which rating it is describing.

The systems rows are the part of this table that is variant-specific to the 2000-5F rather than inherited from the 2000C: the RDY radar, the SPECTRA suite, the GPS-aided inertial navigation, the helmet-mounted display and the Link 16 datalink all rest on the Army Recognition 2000-5F page.

That page also prints a range field reading `17,000 m (55,774 feet)`, which is its maximum takeoff weight repeated in a range row. It is not a range and the leaf records no range from that package.

The Mirage 2000-5F is a single-seat airframe with the 2000C geometry. Its values are not carried to the two-seat 2000D leaf or to the 2000C leaf, and the two-seat length of 14.55 m recorded on the 2000D leaf is not carried here.

## Source References

- `p5-fr-air-mirage2000-5f`: `raw/sources/ministere_des_armees/p5-fr-air-mirage2000-5f/manifest.md` — role and service entry only, no technical rows
- `p5-fr-air-mirage2000-gs`: `raw/sources/globalsecurity/p5-fr-air-mirage2000-gs/manifest.md` — 2000C geometry, masses, fuel and family performance
- `p5-fr-air-mirage2000-5f-armyrecognition`: `raw/sources/army_recognition/p5-fr-air-mirage2000-5f-armyrecognition/manifest.md` — variant-specific systems and a second mass and thrust reading
- `p5-fr-air-mirage2000d-flugzeuginfo`: `raw/sources/flugzeuginfo/p5-fr-air-mirage2000d-flugzeuginfo/manifest.md` — 2000C thrust reading
