# AN/APG-68(V)9 Multimode Fire-Control Radar

Language: English canonical. Chinese companion: not established.

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/research/equipment/catalog/module/sensor/an-apg-68/apg-68v9/README.md`
Owner: `database/equipment-data`
Last verified: `2026-09-14`
Content status: parameter-complete research draft; public values are separated from bounded engineering estimates.

## Identity

- Family: AN/APG-68
- Variant: AN/APG-68(V)9
- Role: X-band pulse-Doppler multimode fire-control radar with SAR ground mapping
- Manufacturer: Northrop Grumman Electronic Systems (Westinghouse lineage)
- Host boundary: F-16 Block 50/52 and retrofit kits; customer OFP and weapon integrations can differ.
- Availability/status: fielded legacy radar. Northrop's archived product page reports more than 250 delivered and seven foreign customers; current production-order status is not claimed by that 2009 page.

## Parameters

| Parameter | Value / bounded estimate | Source | Confidence | Evidence and uncertainty |
| --- | --- | --- | --- | --- |
| Band | X-band, 8–12 GHz public operating envelope | `p5-us-air-apg68v9-shephard` | B | Shephard's APG-68 entry gives the 8–12 GHz band and identifies (V)9 on Block 50/52. Exact agile-frequency table and waveform allocations are controlled technical-order data. |
| Range | 296 km (160 nmi) air-to-air maximum search figure; use as a target/geometry-dependent ceiling, not a guaranteed fighter detection range | `p5-us-air-apg68v9-shephard`; `p5-us-air-apg68v9-northrop` | B/A | The professional handbook publishes 296 km, while Northrop publishes a 33% air-to-air improvement over earlier APG-68 versions. RCS, aspect, look-down clutter, jamming and weather conditions are not specified publicly, so no single combat detection distance is inferred. |
| Track | Track-while-scan (TWS) up to 10 target tracks; Situation Awareness search-while-track mode up to 4 tracked targets | `p5-us-air-apg68v9-shephard`; `p5-us-air-apg68v9-lockheed`; `p5-us-air-apg68v9-globalsecurity` | A/B | The 10-target TWS and 4-target Situation Awareness figures describe different mode/file limits; they are retained separately rather than collapsed into one count. Single-target-track capability is also documented. |
| Scan | Mechanically scanned planar array; Extended Range Search (ERS) azimuth sector ±60° (120°); bounded geometry prior for the public family search cone is ±60° elevation (120° total), with elevation bar count and scan rate left as implementation parameters | `p5-us-air-apg68v9-northrop-brochure`; `p5-us-air-apg68v9-wikipedia` | A/C | Northrop's brochure labels the V9 ERS scan ±60°. The ±60° elevation value is an explicitly bounded family-derived geometry prior, not a V9 flight-test limit; no public customer-specific bar schedule is asserted. |
| Power | 5,606 VA (about 5.6 kVA) radar input; 400 Hz aircraft-supply convention used only as an electrical integration estimate | `p5-us-air-apg68v9-northrop-brochure`; `p5-us-air-apg68v9-wikipedia` | A/B | Northrop's physical-statistics table gives 5,606 VA. Voltage, power factor and transient profile are not released in the brochure; 400 Hz is retained as a bounded F-16 aircraft-supply convention, not as a measured radar-output rating. |
| Interfaces | Internal LRUs: antenna, Modified Dual Mode Transmitter (MDT), Modular Receiver/Exciter (MoRE), Common Radar Processor (CoRP). External semantic interfaces: F-16 fire-control computer/avionics (Block 20–50 adaptation and all-F-16-suite compatibility), LITENING II/EO pods, ASPJ/ASPIS/ALQ-131-class EW, AMRAAM/AIM-9X and JDAM/JSOW/WCMD weapon cueing | `p5-us-air-apg68v9-northrop-brochure`; `p5-us-air-apg68v9-northrop`; `p5-us-air-apg68v9-globalsecurity` | A/B | These are named hardware and mission-system integrations. Electrical bus names, message formats, customer OFP revisions and exact missile software baselines are not public; the record therefore models semantic interfaces, not a pin-level protocol contract. |

## Configuration and estimation boundary

The leaf represents the generic AN/APG-68(V)9 implementation, not APG-68(V)1–(V)8, APG-83 SABR, or a particular export customer's software load. The 296 km range, 8–12 GHz band, and 10-target TWS figure are public handbook values with target/mode assumptions. The ±60° elevation scan and 400 Hz supply note are bounded engineering priors explicitly marked above; replace them with a customer technical order before calibration or acceptance testing.

## Source references

- `p5-us-air-apg68v9-northrop`: `raw/sources/northrop_grumman/p5-us-air-apg68v9-northrop/manifest.md`
- `p5-us-air-apg68v9-northrop-brochure`: `raw/sources/northrop_grumman/p5-us-air-apg68v9-northrop-brochure/manifest.md`
- `p5-us-air-apg68v9-lockheed`: `raw/sources/lockheed_martin/p5-us-air-apg68v9-lockheed/manifest.md`
- `p5-us-air-apg68v9-shephard`: `raw/sources/shephard/p5-us-air-apg68v9-shephard/manifest.md`
- `p5-us-air-apg68v9-globalsecurity`: `raw/sources/globalsecurity/p5-us-air-apg68v9-globalsecurity/manifest.md`
- `p5-us-air-apg68v9-wikipedia`: `raw/sources/wikipedia/p5-us-air-apg68v9-wikipedia/manifest.md`
