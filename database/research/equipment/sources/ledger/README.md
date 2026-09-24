# Source Ledger

Language: English canonical. Chinese companion: not established.

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/research/equipment/sources/ledger/README.md`
Owner: `database/equipment-data`
Last verified: `not established`
Content status: materialized source index with explicit missingness.

## Responsibility

Stores the normalized source ledger for source identity, tier, rights, scope,
retrieval, authority boundary, and residual status. The materialized index is
[`ledger.csv`](ledger.csv); it is generated from the `raw/sources/**/manifest.md`
files by [build_equipment_source_ledger.py](../../../../_work/build_equipment_source_ledger.py).
It is an audit/index, not a second copy of source content.

Blank or `not_recorded` values are intentional findings. The generator never
infers rights, configuration scope, or retrieval success from a URL or a source
tier. The ledger therefore makes source-admission debt visible without granting
runtime authority.

## Columns

`source_id`, `tier`, `publisher`, `author_or_maintainer`, `title`, `url`,
`domain`, `equipment`, `configuration`, `rights_status`, `retrieval_status`,
`authority_status`, `scope_status`, `residual_status`, and `manifest_path`.

All current rows default to `authority_status=non-authoritative`. Tier C
community rows remain valid research candidates when their URL, scope and
uncertainty are retained, but they are not calibration or runtime authority.

## Hierarchy

- Parent: `../`
- Children: [`ledger.csv`](ledger.csv)
