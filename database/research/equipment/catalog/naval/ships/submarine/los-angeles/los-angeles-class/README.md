# Los Angeles-Class Fast Attack Submarine

Language: English canonical. Chinese companion: not established.

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/research/equipment/catalog/naval/ships/submarine/los-angeles/los-angeles-class/README.md`
Owner: `database/equipment-data`
Last verified: `2026-09-13`
Content status: extracted class-baseline simulation-parameter draft; not a runtime record.

## Identity

| Field | Value |
| --- | --- |
| Equipment ID | `eq-us-naval-losangeles` |
| Family / variant | Los Angeles / SSN-688 class baseline |
| Configuration boundary | Flight I, Improved Los Angeles, and 688i boats (SSN-688 through SSN-773). The leaf uses the common four-torpedo-tube, S6G-reactor baseline and records VLS as a Flight II/III branch; Seawolf/Virginia replacements are excluded. |
| Role | Nuclear-powered fast attack submarine; anti-submarine, anti-surface, strike, and special operations support |

## Parameters

| Field | Value | Source | Tier | Configuration / uncertainty |
| --- | --- | --- | --- | --- |
| Hull dimensions | 110.3 m length x 10.1 m beam x approximately 9.4 m draft | `p5-us-naval-losangeles-factfile`; `p5-us-naval-losangeles-wikipedia` | A/C | Overall surfaced dimensions; trim and mast state change observed draft. |
| Displacement (surfaced / standard proxy) | 6,082 long tons surfaced; standardized normal-load proxy 6,100-6,500 LT | `p5-us-naval-losangeles-factfile`; `p5-us-naval-losangeles-globalsecurity` | A/C | Submarine references publish surfaced/submerged, not naval-standard/full. The proxy is explicitly for normal surfaced load. |
| Displacement (submerged / mission load) | 6,927 LT submerged; Improved/688i boats bounded at 6,900-7,200 LT | `p5-us-naval-losangeles-factfile`; `p5-us-naval-losangeles-wikipedia` | A/C | Submerged displacement includes variable ballast and mission stores; it is not interchangeable with surfaced displacement. |
| Propulsion / power | One S6G pressurized-water reactor driving one shaft; approximately 35,000 shp | `p5-us-naval-losangeles-factfile`; `p5-us-naval-losangeles-globalsecurity` | A/C | Reactor core and acoustic treatment are not publicly itemized; shaft-power value is the class public rating. |
| Speed / endurance | 20+ knots submerged; effectively unlimited range; approximately 90 days stores endurance | `p5-us-naval-losangeles-factfile`; `p5-us-naval-losangeles-wikipedia` | A/C | Nuclear range is fuel-unlimited between refuelling; food, maintenance, and crew endurance bound deployment length. |
| Crew / payload | 12-15 officers plus 117-120 enlisted (129-135 total); four 533 mm torpedo tubes and 26 torpedo/missile weapons in the torpedo room | `p5-us-naval-losangeles-factfile`; `p5-us-naval-losangeles-globalsecurity` | A/C | Crew varies by boat and refit. Flight II/III boats add a 12-cell vertical launch module; Flight I has no VLS. |
| Sensors / combat system | AN/BQQ-5 spherical sonar, TB-16/TB-23 towed array, AN/BQS-15 mine/ice detection, periscope/photonic mast fit, AN/BPS-15 navigation radar, Mk 2/3 ESM, CCS Mk 2 combat-control system | `p5-us-naval-losangeles-factfile`; `p5-us-naval-losangeles-wikipedia` | A/C | Exact sonar processing baseline differs among 688i and earlier boats; named suites are retained as capability anchors. |
| Weapons / payload | Mk 48 ADCAP torpedoes; UGM-109 Tomahawk and UGM-84 Harpoon through the four tubes; 26 total torpedo-room weapons; 12 Tomahawk VLS cells on Flight II/III | `p5-us-naval-losangeles-factfile`; `p5-us-naval-losangeles-globalsecurity` | A/C | Actual loadout is mission-specific. VLS branch must not be applied to Flight I hulls. |
| Protection / survivability | HY-80 high-yield-steel pressure hull, reserve buoyancy and variable ballast, watertight compartmentation, acoustic isolation, emergency blow and damage-control systems | `p5-us-naval-losangeles-wikipedia`; `p5-us-naval-losangeles-globalsecurity` | C/C | No public plate schedule. Simulation bound for pressure-hull plating is 25-60 mm high-strength steel, explicitly an engineering estimate and not a certified thickness. |

## Source References

- `p5-us-naval-losangeles-factfile`
- `p5-us-naval-losangeles-wikipedia`
- `p5-us-naval-losangeles-globalsecurity`
