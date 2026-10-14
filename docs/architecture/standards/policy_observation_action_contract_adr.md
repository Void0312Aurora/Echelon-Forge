# ADR: field-level policy observation and action admission

Language:
- English canonical: `policy_observation_action_contract_adr.md`
- Chinese companion: [policy_observation_action_contract_adr.zh.md](policy_observation_action_contract_adr.zh.md)

Document kind: `standard`
Lifecycle: `proposed`
Canonical: `docs/architecture/standards/policy_observation_action_contract_adr.md`
Owner: `architecture/agent-contracts`
Last verified: `2026-10-11`

**Status:** proposed qualification design; current `DecisionModel`, Gym spaces
and domain packet owners remain unchanged.

## Decision

Introduce an opt-in, non-authoritative policy compatibility descriptor that
negotiates field-level observation and action contracts. The descriptor lowers
to existing `ObservationViewSpec`, Agent/role authority, command endpoints and
owner-controlled lifecycle admission. It does not replace `DecisionModel`,
turn `model_kind` into a permission system, or make a policy category an
authority claim.

Each field declares stable ID/version, shape, dtype, unit, frame, timing,
truth/belief visibility, optionality and source authority. Actions additionally
declare endpoint, bounds, timing and required rights. Admission rejects missing
fields, shape/unit/version mismatches, unauthorized world truth, unsupported
action families, out-of-bounds actions and incompatible timing before policy
binding or runtime side effects.

Author-declared policy categories are open metadata. Unknown categories neither
grant capability nor bypass owner checks. A minor revision or optional field is
admitted only through a declared projection/default policy that preserves tensor
ordering and provenance. Legacy `model_kind` callers use an explicit bridge
with deterministic diagnostics during migration.

## Proof and boundaries

The qualification proof binds scripted and learned/stand-in implementations to
the same field contract, tests positive optional-field projection and all
negative admission cases, and records contract identities as evidence. It must
preserve current maintained outputs and default structural-only views. Python
or third-party code is not auto-admitted by a descriptor.

Mechanism ports (#229), platform/force composition (#236/#237), and RuntimeFacade
capability presence (#224) remain separate owners; this ADR only defines the
agent-facing compatibility layer.

## Option comparison and implementation checkpoint

| Option | Disposition in this proposed ADR |
| --- | --- |
| Extend ObservationViewSpec and existing role contracts | target ownership remains here; broader catalogue work needs owner acceptance |
| Non-authoritative Policy descriptor consuming owner catalogues | proposed pilot route with unchanged DecisionModel lifecycle |
| Use a closed category enum as compatibility/permission | rejected; category metadata cannot prove contract compatibility or rights |

The pilot consumes the basic mission field catalogue from mission_obs_taxonomy and actual Air action dimensions/bounds. It checks source/frame, action timing/bounds, explicit optional defaults, deterministic selection and legacy-kind mismatch. Two existing-registry model implementations retain reset/decide/close. Full observation-view binding, checkpoint admission and runtime/report migration remain open.

See [qualification evidence and remaining gates](../work/issues/rfc_qualified_composition_implementation.md). Lifecycle remains proposed; this checkpoint does not establish owner approval or production admission.
