# flugzeuginfo.net — Dassault Mirage 2000 technical data

Source ID: `p5-fr-air-mirage2000d-flugzeuginfo`
Tier: `C`
Publisher: flugzeuginfo.net, aircraft technical data reference
Author / maintainer: flugzeuginfo.net, site maintainer
Title: Dassault Mirage 2000 — specifications, technical data and description
URL: http://www.flugzeuginfo.net/acdata_php/acdata_mirage2000_en.php
Domain: air
Equipment: Mirage 2000 family / 2000D
Configuration: The page opens with a description that separates the marks: the 2000N is the two-seat nuclear-strike variant and the 2000D is the two-seat fighter-bomber variant. The technical table below it is a single-seat 2000 baseline table, crew 1.
Retrieval:
  attempted_at: 2026-09-17T17:34:44Z
  method: tavily_proxy
  status: success
  returned: the variant description and the technical table through search indexing of this URL: crew 1, one turbofan, engine model SNECMA M53-P2, dry 64.3 kN and with afterburner 95.1 kN (14,455 and 21,379 lbf), speed 2,334 km/h, service ceiling 17,983 m (59,000 ft), range 1,450 km (783 nm)
  did_not_return: a two-seat variant column, a combat radius, or any 2000D-specific row
Estimation / uncertainty: Tier C specialist technical-data compilation. Its table is written for the single-seat Mirage 2000 baseline and states crew 1, so its performance rows are family values rather than 2000D measurements. Its dry thrust of 64.3 kN agrees with the encyclopedic and GlobalSecurity readings; its afterburner figure of 95.1 kN agrees with the encyclopedic reading and is 0.1 kN above the GlobalSecurity 95 kN.
Retention: manifest and extracted parameter notes only

## Extracted parameter notes

Variant description: the Mirage 2000 is based on the Mirage III; the 2000N is the two-seat nuclear-strike variant; the 2000D is the two-seat fighter-bomber variant.

Technical table, single-seat baseline: crew 1; propulsion one turbofan; engine model SNECMA M53-P2; engine power dry 64.3 kN (14,455 lbf) and with afterburner 95.1 kN (21,379 lbf); speed 2,334 km/h (1,260 kn, 1,450 mph); service ceiling 17,983 m (59,000 ft); range 1,450 km (783 nm, 901 mi).

## Why this package matters

The Mirage 2000D RMV leaf recorded its powerplant and performance rows as not established from the held sources, because the GlobalSecurity compilation it rests on writes those blocks for the single-seat 2000C and warns that two-seat and strike variants differ marginally.

This package supplies an independent second reading of the same M53-P2 powerplant and of the family performance envelope, and it states explicitly that the 2000D is the two-seat fighter-bomber variant. That makes the engine fit a two-publisher reading rather than a single one, and it gives the leaf a named artifact for the dry thrust figure of 64.3 kN, which no package held for it before.

The performance rows remain family values on the single-seat baseline. This package does not convert them into 2000D measurements and the leaf does not present them as such.
