# Countermeasure snapshot provenance (#128)

The stable producer names are `instrument_projection` and
`countermeasure_release_projection`. Native writers use the named
`CountermeasureSnapshotProducer` enum and update the source, timestamp and
post-EW flag together. They never read contribution ordinals or exact-trace
indices. The Python `countermeasure_snapshot_producer` property exposes those
names, returning `unknown` for an unrecognized legacy code.

For wire and Python compatibility, `countermeasure_snapshot_stage` remains an
integer with the existing 24/31 codes. These are now explicitly **fixed producer
codes**, not positions in a registry or phases. No component fields, reflection
schema, state-transfer payload or evidence version changed. Native round-trip
tests preserve source, inventory, timestamp and flag through existing reflection.

The regular instrument pass projects current inventory (or -1 when absent).
Both EW release nodes retain their same-frame post-EW projection, including a
command that is denied by inventory/cadence. This producer therefore means the
EW projection ran, not proof that an expendable was actually released. Quantity
changes and last-release timestamps establish release success separately.
Chaff-only, flare-only, combined, no-command and missing-component paths are
covered. No EW mechanics, timing or observation vector layout changed.

Scheduler placement is described by the separate realized topology from #127;
these producer codes have no scheduler-order meaning.
