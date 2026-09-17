# Database

Language:
- English canonical: `README.md`
- Chinese companion: [README.zh.md](README.zh.md)

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/README.md`
Owner: `database/equipment-data`
Last verified: `not established`
Content status: provisional navigation scaffold; the final data contract is not established.

## Responsibility

The directory separates reusable platforms, modules, weapons, facilities, and source-governance records.

## Not Responsible For

It does not define a final equipment-data contract, runtime behavior, model authority, or source approval.

## Hierarchy

- Parent: repository root
- Children: `_templates/`, `modules/`, `platforms/`, `research/`, `sources/`, `weapons/`

## Rules

- Directory paths are physical organization only.
- Stable logical IDs, not paths, should be used for cross-references.
- Shared modules and weapons must not be copied into platform directories.
- `research/` contains provisional collection material; it is not runtime data or a final contract.
- This tree is not consumed by the current runtime loader.

## Maintenance Trigger

Update this index when the object-kind roots, governance rules, or data contract change.
