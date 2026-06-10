# WP19-B Device-Resident Output Contract Pre-Gate

Status: `2026-05-21` pass / export-only DTO seam accepted.

Language:

- English canonical: `wp19_device_resident_output_contract_cluster_20260521.md`
- Chinese companion:
  [wp19_device_resident_output_contract_cluster_20260521.zh.md](wp19_device_resident_output_contract_cluster_20260521.zh.md)

Inputs:

- [WP19 main plan](cuda_resident_state_alignment_wp19_20260521.md)
- [WP6 resident-state boundary rules](../wp6_backend_profile_policy/wp6_resident_state_boundary_rules_20260519.md)
- [WP13 backend fidelity expansion](../wp13_backend_fidelity_expansion/backend_fidelity_expansion_wp13_20260520.md)

## Purpose

Define the smallest facade/backend contract surface that can describe
device-resident outputs without turning them into maintained resident-state
ownership.

Preflight conclusion:

- The current maintained/export DTOs already carry host-visible snapshot and
  barrier identity, but they do not carry device-buffer metadata.
- `RuntimeCapabilities` and backend profile projection already fail closed for
  `supports_device_observation_view`, `supports_resident_state`, and exact GPU
  support.
- Therefore WP19-B should not retrofit device-resident descriptors into the
  existing maintained packet DTOs. The safe seam is additive: a dedicated
  export-only/device-output descriptor adjacent to, not embedded inside, the
  maintained packet truth path.

## Scope

In scope:

- metadata requirements for device output shape, dtype, element count, source
  snapshot, sync/export barrier, host-visible availability, diagnostics label,
  and consumer constraints;
- fail-closed behavior for callers that request device-resident outputs without
  a maintained profile;
- focused tests or preflight notes for DTO/binding placement.

Out of scope:

- maintained resident-state promotion;
- exact GPU execution;
- broad facade redesign.

## Source-Backed Findings

| Source | Current fact | WP19-B implication |
|--------|--------------|--------------------|
| `src/runtime/facade/runtime_facade_types.h` | `ObservationBatchPacket` already exposes `snapshot_version`, `barrier_id`, `source_time_s`, and maintained `provenance`. `EngagementEventPacket` already exposes `snapshot_version`, `barrier_id`, `barrier_sequence`, `barrier_detail`, and diagnostics provenance. | The maintained facade already has a host-visible export envelope and diagnostics ancestry vocabulary. Reusing these packets for device pointer semantics would mix export truth with backend-local transport. |
| `src/interfaces/python/bindings_runtime.cpp` | Python bindings expose only host-visible packet fields for `ObservationBatchPacket` and `EngagementEventPacket`. There is no bound device-buffer descriptor. | Any first device-resident contract must be additive and explicitly bound, not silently inferred from existing packet bindings. |
| `src/runtime/facade/runtime_facade.cpp` | `RuntimeFacade::capabilities()` hard-codes `supports_device_observation_view = false`, `supports_resident_state = false`, and `supports_exact_gpu_backend = false`. | Device-output availability must not project as maintained support. |
| `src/runtime/contracts/backend_profile_contracts.h` | Diagnostics-only and unmaintained profiles must not authorize exact GPU, resident-state, shadow, or device observation support. | Device-resident output descriptors must remain `export-only` / diagnostics-only unless a later maintained profile explicitly promotes them. |
| `WP6 resident-state boundary rules` | Unsynced backend-local state is diagnostics-only until an accepted host-visible reconstruction/export rule and barrier exist. | A device-resident buffer without declared export barrier and host-visible rule cannot be treated as maintained state or parity evidence. |
| `WP13 backend fidelity expansion` | Capability projection is a conservative query surface, not a transport/data-plane schema. | WP19-B must not overload `RuntimeCapabilities` with per-output shape or buffer metadata. |

## Minimal Contract Fields

The smallest acceptable device-resident output descriptor is:

| Field | Required meaning | Current host/export source | Placement decision |
|-------|------------------|----------------------------|--------------------|
| `output_shape` | Logical shape of the exported tensor/buffer. | Not represented today. | Additive DTO seam required. |
| `dtype` | Scalar element dtype for the exported buffer. | Not represented today. | Additive DTO seam required. |
| `element_count` | Logical element count after shape normalization. | Not represented today. | Additive DTO seam required. |
| `source_snapshot` | Normalized source snapshot identity for the data the device buffer was derived from. | Existing `snapshot_version` / `source_snapshot_version` vocabulary. | Reuse existing snapshot vocabulary in additive descriptor; do not replace maintained packet fields. |
| `sync_or_export_barrier` | Barrier id, and when relevant barrier detail/sequence, at which the descriptor is valid to consume or export. | Existing `barrier_id`, `barrier_detail`, `barrier_sequence`. | Reuse existing barrier vocabulary in additive descriptor. |
| `host_visible_availability` | Whether a host-visible mirror/export exists now, requires explicit readback, or is unavailable. | Not represented as a standalone output contract today. | Additive DTO seam required. |
| `diagnostics_label` | Explicit label such as `diagnostics_only`, `export_only_candidate`, or later maintained classification. | Existing diagnostics-only vocabulary and maintained-status labels. | Reuse vocabulary, but keep it per-output in the additive descriptor. |
| `consumer_constraints` | Declares whether the payload may be consumed only by device-resident consumers, only through explicit host export/readback, or only as diagnostics evidence. | Not represented today. | Additive DTO seam required. |

Normalization rule:

- `element_count` MUST equal the product of `output_shape`, with scalar outputs
  normalized as an explicit one-element shape or another single documented
  convention shared across producer and consumer.

## DTO Placement Decision

Decision:

- Do not add device-resident fields directly to `ObservationBatchPacket`.
- Do not add device-resident fields directly to `EngagementEventPacket`.
- Do not add per-output transport metadata to `RuntimeCapabilities`.
- Use an additive DTO seam, owned as export-only metadata adjacent to the
  maintained packet/result that names the same snapshot/barrier source.

Why the current DTOs are not the right seam:

1. `ObservationBatchPacket` and `EngagementEventPacket` are already the
   host-visible maintained/export envelopes. They represent what crossed the
   facade boundary, not opaque backend-local transport.
2. Their current bindings and tests assume host-readable structured payloads.
   Backfilling device descriptors into these DTOs would make every existing
   caller appear device-aware without an explicit contract upgrade.
3. `RuntimeCapabilities` is a maintained support projection. It answers what is
   supported, not what one emitted buffer looks like at a given barrier.

Safe additive shape:

- A future DTO may be a small descriptor such as
  `DeviceResidentOutputDescriptor` or `DeviceResidentExportDescriptor`.
- That descriptor should be attached only to export-only/diagnostics result
  seams, for example as an optional sibling collection on a result packet or a
  dedicated diagnostics export result.
- The additive descriptor MUST refer back to the maintained/export source via
  `source_snapshot` and `sync_or_export_barrier`; it MUST NOT become a second
  authoritative truth path.

## Fail-Closed Rules

WP19-B requires the following fail-closed behavior:

1. Missing `output_shape`, `dtype`, or `element_count` invalidates the
   descriptor. The output is unavailable to consumers.
2. `element_count` mismatch with normalized `output_shape` invalidates the
   descriptor. The output MUST be quarantined as diagnostics-only and MUST NOT
   satisfy parity or maintained export claims.
3. Missing `source_snapshot` or `sync_or_export_barrier` means the output is
   unsourced. Unsourced outputs MUST be treated as backend-local diagnostics
   only.
4. If `host_visible_availability` does not explicitly say a host-visible export
   exists, callers MUST assume host-readback is unavailable through the
   maintained facade surface.
5. Missing `diagnostics_label` defaults to diagnostics-only rejection, not
   silent promotion.
6. Missing `consumer_constraints` blocks consumption. Callers MUST NOT infer
   that host consumers, device consumers, and diagnostics consumers are
   interchangeable.
7. Presence of a descriptor MUST NOT set or imply
   `supports_device_observation_view`, `supports_resident_state`,
   `supports_exact_gpu_backend`, or `supports_shadow_compare`.
8. Presence of a device pointer, CUDA helper success, benchmark speedup, or GPU
   build success MUST NOT substitute for `source_snapshot`, barrier metadata, or
   maintained profile acceptance.

## Consumer Constraint Classes

WP19-B distinguishes three consumer modes:

| Consumer mode | Allowed contract | Forbidden inference |
|---------------|------------------|---------------------|
| `host_readback` | Consumer receives a maintained/export packet or an explicit host-visible mirror at a declared barrier. | MUST NOT infer that a device-local descriptor alone is host-readable. |
| `device_resident_consumer` | Consumer may read the device-resident output only when it accepts the descriptor's `dtype`, shape, barrier, and diagnostics/export label. | MUST NOT imply maintained resident-state ownership or device observation support. |
| `diagnostics_only` | Output may be recorded, profiled, or compared as report-only evidence. | MUST NOT drive committed state, fallback choice, capability promotion, or parity acceptance. |

## Focused Test Slice

Safe focused guard added in this preflight:

- `tests/architecture/runtime_facade/test_dto_contracts_batch1.py` now asserts that
  `ObservationBatchPacket` and `EngagementEventPacket` keep their host-visible
  metadata surfaces while not silently growing device-resident descriptor
  fields. This protects the additive seam decision without changing runtime
  behavior.

Implementation update for WP19-B2:

- `src/runtime/facade/runtime_facade_types.h` now defines an additive
  export-only `DeviceResidentOutputDescriptor` carrying
  `output_shape`, `dtype`, `element_count`, `source_snapshot`,
  `sync_or_export_barrier`, `host_visible_availability`,
  `diagnostics_label`, and `consumer_constraints`.
- `src/interfaces/python/bindings_runtime.cpp` now exports that descriptor to
  Python as a standalone DTO with fail-closed defaults.
- `ObservationBatchPacket`, `EngagementEventPacket`, and `RuntimeCapabilities`
  remain unchanged as host-visible packet/support surfaces; the descriptor is
  not inlined into those DTOs and does not promote any support flags.

Tests intentionally still not added in WP19-B:

- No CUDA helper implementation tests.
- No support-flag promotion tests beyond the already conservative
  `RuntimeFacade::capabilities()` and backend-profile contract coverage.
- No attachment of the descriptor to maintained packet DTOs or capability
  projection.

## Task Items

| ID | Item | Acceptance |
|----|------|------------|
| `B1` | Contract fields | Complete. Minimal fields are split into reusable snapshot/barrier vocabulary plus additive-only shape/dtype/count/availability/consumer metadata. |
| `B2` | Fail-closed projection | Complete. Preflight keeps device output descriptors unable to imply `supports_resident_state`, `supports_device_observation_view`, or exact GPU support. |
| `B3` | Consumer constraints | Complete. Host-readback, device-resident, and diagnostics-only consumers are explicitly separated. |
| `B4` | Test plan or tests | Complete for implementation. Focused binding and architecture guards prove the standalone descriptor fields, fail-closed defaults, assignability, and non-inline packet/capability boundaries. |

## Suggested Validation

```bash
git diff --check
python -m pytest -q tests/runtime/facade/test_runtime_facade.py -k "capab or backend or profile"
python -m pytest -q tests/runtime/bindings/test_bindings_runtime_dto_surface.py
python -m pytest -q tests/architecture/runtime_facade/test_dto_contracts_batch1.py -k "device_resident or packet"
```

## Residuals

- The descriptor is currently export-only metadata only; no runtime result seam
  publishes descriptor collections yet.
- No maintained profile declares a device-resident consumer contract, host
  reconstruction rule, or resident-state promotion gate.
- WP19-D still needs to formalize shard/barrier ownership language for any
  later promotion beyond export-only diagnostics.

## Handoff

Return contract fields, touched files, tests run, blockers, and whether the
stream is implementation-ready or preflight-only.

Current return recommendation after WP19-B2:

- Status: `pass`
- Implementation readiness: additive DTO seam exists as a standalone export-only
  descriptor, but integration must continue to keep it off maintained packet
  DTOs, capability projection, and support-flag promotion paths.

## Closure Outcome

WP19-B is accepted for WP19 as the additive export-only descriptor seam. It
does not publish descriptor collections from runtime result packets yet, and it
does not promote exact GPU, device-observation, or maintained resident-state
support.
