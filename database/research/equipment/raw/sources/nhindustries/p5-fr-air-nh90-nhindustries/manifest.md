# NHIndustries — NH90 platform overview

Source ID: `p5-fr-air-nh90-nhindustries`
Tier: `B`
Publisher: NHIndustries (consortium of Airbus Helicopters 62.5 percent, Leonardo 32 percent, Fokker 5.5 percent)
Author / maintainer: NHIndustries, the programme manufacturer
Title: NH90 Helicopter Platform Overview
URL: https://www.nhindustries.com/nh90-helicopter
NFH page: https://www.nhindustries.com/nh90-helicopter/nh90-nfh-nato-frigate-helicopter/ (mission and sensor content only, no specification table)
Brochure: https://www.nhindustries.com/wp-content/uploads/2025/06/NH90_Brochure_NHI_2024.pdf
Retrieval:
  attempted_at: 2026-09-22T17:05:00Z
  method: tavily_proxy
  status: success
  returned: NH90 common geometry, weights, fuel, cargo, common performance at 10,000 kg, engine options, avionics and design-envelope values
  did_not_return: a complete NFH-specific performance block; the separate Airbus NFH card supplies NFH headline speed, range, crew, useful load and weapon mission data
Domain: air
Equipment: NH90 / NFH
Configuration: This package carries common NH90 platform data. Its performance block is labelled `NH90 General Performance (basic aircraft)` and footnoted `(*) at 10000 kg`, which is below the NFH maximum gross weight of 11,000 kg. Weight, dimension, capacity and fuel rows are not footnoted; the separate Airbus NFH card carries the variant-specific headline block.
Estimation / uncertainty: Tier B manufacturer documentation, authoritative for its own product. The reference condition of the performance block is a basic-aircraft figure at 10,000 kg and is not an NFH-at-maximum-weight figure.
Retention: manifest and extracted parameter notes only
Rights status: not_recorded
Provenance status: manifest+retrieval+retention
Residual status: open
Scope status: complete

## Extracted parameter notes

External dimensions, rotors turning: length 19.56 m (64.18 ft), width 16.30 m (53.48 ft), height 5.31 m (17.42 ft).

Weights: maximum gross weight 10,600 kg (23,369 lb); alternate gross weight 11,000 kg (24,250 lb); empty weight 6,400 kg (14,109 lb); useful load 4,200 kg (9,260 lb). The platform page gives the NFH maximum gross weight as 24,250 lb (11,000 kg) and the TTH maximum gross weight as 23,369 lb (10,600 kg).

Cargo: cargo hook 4,000 kg (8,818 lb); single or dual rescue hoist 270 kg (595 lb); rescue hoist on ground 400 kg (880 lb).

Fuel capacity: internal cell system 2,035 kg (4,486 lb); internal auxiliary tanks 400 kg (882 lb) each; external auxiliary tanks 492 kg (644 lb) each.

Internal dimensions: width 2.00 m (6.56 ft), length 4.80 m (15.75 ft), height 1.58 m (5.18 ft), volume 15.20 m³ (536.78 ft³); sliding door opening 1.60 x 1.50 m; rear ramp opening 1.78 x 1.58 m.

Performance, all footnoted at 10,000 kg: maximum cruise speed 300 km/h (162 kt); economical cruise speed 260 km/h (140 kt); maximum rate of climb 11.2 m/s (2,200 ft/min); one-engine-inoperative rate of climb 4.3 m/s (850 ft/min) at two-minute rating and 1.5 m/s (300 ft/min) continuous at 2,000 m; hover ceiling in ground effect 3,200 m (10,500 ft); out of ground effect 2,600 m (8,530 ft); maximum range 982 km (530 nm); maximum range with 2,500 kg payload 900 km (486 nm); maximum endurance 5 hours; ferry range with internal auxiliary fuel tanks 1,600 km (864 Nm).

Powerplant: two Turbomeca RTM 322-01/9 or RTM 322-01/9A, or two General Electric T700/T6E1 or CT7-8F5. Both options are listed for NFH and TTH together.

Design envelope: flight envelope sea level to 6,000 m (20,000 ft); temperature range −40 °C to +50 °C; operation in continuous icing conditions to DEF-STN 00-970; auto flight control; quadruplex redundant fly-by-wire; five NVG-compatible displays.

## Why this package was added, and one correction

The French Ministry of the Armed Forces page held for this leaf returns a site-under-maintenance response. This manufacturer page is the authoritative source actually reachable.

A correction: an earlier revision of this package recorded empty weight, powerplant and dimensions as absent from the page. They are present. The block that was genuinely not captured in that pass is the external-dimensions table, and the omission has been fixed here.
