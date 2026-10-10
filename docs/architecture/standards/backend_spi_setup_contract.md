# Internal Backend SPI Setup and Export Contract

Language:
- English canonical contract: `backend_spi_setup_contract.md`.
- Chinese companion document.
Document kind: `standard`
Lifecycle: `maintained`
Canonical: `docs/architecture/standards/backend_spi_setup_contract.md`
Owner: `runtime/facade/internal/world_batch_backend.h`
Last verified: `2026-10-10`

The internal `IWorldBatchBackend` seam accepts a closed `SetupOperation` sum. A
caller selects exactly one operation by constructing
`std::variant<BatchSetup, LayoutSetup, WorldSpawnSetup, TypedPlatformSpawnSetup>`.
The public `RuntimeFacade` remains the owner of request validation and public
evidence; this contract only describes the backend-neutral translation layer.

## Setup operations

| Operation | Valid payload | CPU reference | CUDA resident candidate |
| --- | --- | --- | --- |
| `BatchSetup` | Per-world seeds, spawns, time steps, and optional environment assignments | Accepted | Accepted only for the fixed-air capability: one seed/spawn/time-step per world and no dynamic environment assignments |
| `LayoutSetup` | One world index, terrain, weather, zones, spawns, time steps, sun, and geodetic anchor | Accepted | Rejected deterministically |
| `WorldSpawnSetup` | One non-null synchronous `WorldSpawnRequest` | Accepted | Rejected deterministically |
| `TypedPlatformSpawnSetup` | One non-null synchronous `TypedPlatformSpawnRequest` | Accepted | Rejected deterministically |

`VectorBatchView` is a synchronous, non-owning view. The caller keeps the
source vector alive through the virtual call. A backend that queues work past
the call boundary must copy the values explicitly; it may not retain the view.
Pointer payloads have the same call-boundary lifetime and are fail-closed when
null.

## Export requests

`ExportRequest` remains a bounded aggregate because its flags describe
independent query families already used by the facade. CPU accepts the
supported families and requires `world_index` for world-scoped time-step or
engagement-event exports and `kinematics_ref` for kinematics. The CUDA
resident candidate supports fixed-air kinematics, time-step, instrument, and
observation projection only; mission, task, leader, pilot-report, unit-message,
and engagement-event flags are rejected. Projection exports require a committed
observation window and validate resident identity references.

Unsupported variants and payloads throw before backend state mutation. No
public facade, Python, authority, or serializable evidence contract changes in
this migration.
