# WP4-H Information And Agent Shim Implementation Notes

Status: `2026-05-19` passive Python shim landed.

Inputs:

- [WP4-H dispatch sheet](wp4_agent_shim_cluster_20260519.md)
- [WP4 first-wave acceptance review](../review/wp4_first_wave_acceptance_review_20260519.md)
- [WP4-D/E policy-binding alignment notes](wp4_policy_binding_alignment_notes_20260519.md)
- [WP4-A surface inventory](wp4_surface_inventory_wp4a_20260519.md)

## Decision

WP4-H uses a Python-only passive shim in `python/rl/runtime/agent_shim.py`.
It does not add public C++ bindings, does not alter policy inference, and does
not hook into existing Gymnasium or batch runtime step flows.

The shim provides:

- `AgentRole` as the five-element role/authority/information/decision/action
  metadata boundary,
- `ActionIntentCompat` as a wrapper for existing `PilotAction` and
  `WorldPilotActionAssignment` payloads,
- `CoordinationIntentCompat` as a wrapper for existing mission/task/leader/report
  command-chain payloads,
- `ObservationProvenance` labels for maintained, compatibility, and
  diagnostics-only information-state sources.

## Boundary Labels

| Label | Meaning | Status |
|-------|---------|--------|
| `facade_observation_packet` | Observation came from `ObservationBatchPacket`. | `maintained` |
| `agent_observation_compat` | Observation came from legacy agent-observation getters or equivalent adapter output. | `compatibility_adapter` |
| `raw_world_truth` | Input came from raw runtime or simulation internals. | `diagnostics_only` |
| `diagnostics_oracle` | Input came from teacher, oracle, debug, or privileged helper logic. | `diagnostics_only` |

Current policy, batch, multi-agent, leader, and scripted-director flows remain
`compatibility_adapter` until they carry source id, input snapshot version,
effective time, validity, merge policy, and role metadata at the adapter
boundary.

## Binding Deferral

`AgentRole`, `ActionIntentPacket`, `ActionHoldPolicy`, `CoordinationIntentPacket`,
`DecisionBelief`, and `ObservationViewSpec` remain deferred from C++ binding
promotion until WP4-A/WP4 integration stabilizes surface names and fields.

## Validation

The narrow test file `tests/runtime/test_agent_shim.py` verifies:

- observation provenance classification,
- `AgentRole` five-element output,
- roster role metadata,
- action wrapper metadata without mutating the underlying assignment payload,
- coordination wrapper payload-field reporting,
- rejection of unknown status and merge-policy values.
