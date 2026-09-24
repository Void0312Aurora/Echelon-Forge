# Equipment Coverage Plan

Language: English canonical. Chinese companion: not established.

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/research/equipment/coverage/README.md`
Owner: `database/equipment-data`
Last verified: `not established`
Content status: provisional expansion queue for simulation-parameter collection.

## Purpose

This plan turns the broad current-and-Cold-War equipment goal into bounded research batches. It is a coverage queue, not an inventory claim and not a final equipment schema.

The queue is intentionally representative rather than an assertion that every historical subtype is already enumerated. A candidate becomes an equipment record only after its concrete variant, configuration, parameter evidence, and source package are collected.

## Scope axes

- Eras: `current`, `post_cold_war`, and `cold_war`.
- Domains: `ground`, `air`, `naval`, `weapon`, and `module`.
- Priority: `P1` for common simulation actors and shared systems; `P2` for important supporting actors; `P3` for later breadth expansion.
- Collection state: a newly discovered candidate may start as `queued`; once it
  is admitted to a domain backlog, its status must mirror that backlog row.

## Parameter gate

Each candidate must be collected as a concrete variant/configuration. The minimum useful package is geometry, configuration-specific mass, propulsion, mobility, crew or payload, armament or mission system, publicly supported protection or signature information, and field-level source context. Inventory counts are optional. `unknown` is allowed only while a candidate is being searched; before `parameter_complete`, every target field must be filled from an official, professional, archival, museum, or specialist-community source, or with a bounded estimate that is explicitly labelled and tied to its source.

## Batch order

1. Ground combat and support vehicles, including Cold-War predecessors of current families.
2. Air combat, strike, transport, and rotary-wing platforms.
3. Naval surface, subsurface, and support platforms.
4. Air-to-air, air-to-surface, surface-to-air, anti-ship, and anti-armor weapons.
5. Engines, sensors, datalinks, electronic warfare, and other shared modules.

The candidate rows are recorded in [coverage.csv](coverage.csv). This file does
not replace the equipment backlog or become an inventory claim. In the current
tree it is a cross-domain index of 105 already admitted rows, so its statuses
are `parameter_complete` and must agree with the domain backlog. Future
discovery candidates may be added as `queued`, but promotion into a domain
backlog must be accompanied by a matching status update in both files.
