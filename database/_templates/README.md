# Templates

Language:
- English canonical: `README.md`
- Chinese companion: [README.zh.md](README.zh.md)

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/_templates/README.md`
Owner: `database/equipment-data`
Last verified: `not established`
Content status: provisional navigation scaffold; the final data contract is not established.

## Responsibility

Holds structural templates for object kinds. A template does not assert that an equipment item has been collected.

## Not Responsible For

This directory does not define runtime behavior, source authority, or the final equipment-data schema.

## Current Authority

- [Template field reference](FIELDS.md): field-level explanations, units, and current caveats for all provisional templates.
- [Shared schema definitions](common.schema.json): common JSON Schema definitions used by the type schemas.
- Type schemas: each `*.template.json` has a matching `*.schema.json` in the same directory.

## Hierarchy

- Parent: `database/`
- Children: `module/`, `platform/`, `source/`, `weapon/`

## Maintenance Trigger

Update this index when its responsibility, child structure, or governing data contract changes.
