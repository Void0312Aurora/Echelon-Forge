# Python RuntimeFacade Capability Admission

Language:
- English canonical contract: `python_runtime_facade_capability_admission.md`.
- Chinese companion document.
Document kind: `standard`
Lifecycle: `maintained`
Canonical: `docs/architecture/standards/python_runtime_facade_capability_admission.md`
Owner: `python/rl/runtime/world_batch/adapter.py`
Last verified: `2026-10-10`

`RuntimeFacadeAdapterCapabilities` is the single capability snapshot used by
the maintained Python world-batch adapter. The snapshot is recomputed when the
facade object changes, which keeps test and provider swaps explicit without
probing a legacy fallback.

## Capability classes

The required production ABI contains the maintained window, observation
request/export, task-order, leader-intent, pilot-report, launch, mission,
command-link, and corresponding write/read batch bindings. A missing required
field is exposed through `capabilities.missing_required` and every operation
that needs that field raises a `RuntimeError` before dispatch.

`get_unit_messages_batch` is an optional communication query family. It is not
silently substituted when absent: a caller that requests it receives the same
fail-closed error through the explicit capability gate. No compatibility
writer or raw runtime fallback is probed.

The `uses_compat_fallback` field in `RuntimeWindowEvidence` remains a stable
false value for this maintained adapter path. It is evidence-schema data and is
not used to convert an unsupported binding into a valid result.

## Task-order read contract

`get_task_orders_maintained_batch` requires its maintained binding. A missing
method raises an error that identifies the missing capability; an available
method returning no contracts produces the valid empty list. These outcomes are
therefore distinguishable to callers and evidence consumers.
