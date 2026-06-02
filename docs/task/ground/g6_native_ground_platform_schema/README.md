# G6-E Native Ground Platform Schema

Status: `2026-06-02` archived pointer. The full evidence package was moved to
[archive/g6_native_ground_platform_schema](../archive/g6_native_ground_platform_schema/README.md).

G6-E accepted native ground platform schema evidence: `Ground_Platoon_MVP`
loads through the example database, Python exposes `ef_py.UnitType.Ground`, and
`spawn_unit(..., "Ground_Platoon_MVP", ...)` materializes a native ground entity
with stable inspection fields. Route movement, terrain, sensing, fires, damage,
and combat remain held.

This path is a lightweight summary only. New work should continue from
[../README.md](../README.md) and a fresh follow-on package.
