# ADR: field-level policy observation and action admission

Language:
- English canonical: `policy_observation_action_contract_adr.md`
- Chinese companion: [policy_observation_action_contract_adr.zh.md](policy_observation_action_contract_adr.zh.md)

Document kind: `standard`
Lifecycle: `proposed`
Canonical: `docs/architecture/standards/policy_observation_action_contract_adr.md`
Owner: `architecture/agent-contracts`
Last verified: `2026-10-12`

**Status:** proposed qualification design; current `DecisionModel`, Gym spaces
and domain packet owners remain unchanged.

## Decision

Treat Policy as one first-class lifecycle contract: scripted, learned, human,
rule-based, search and composite implementations may all implement it. Their
categories remain optional author metadata for discovery, never a dispatch ABI
or permission. Introduce an opt-in, non-authoritative policy compatibility descriptor that
negotiates field-level observation and action contracts. The descriptor lowers
to existing `ObservationViewSpec`, Agent/role authority, command endpoints and
owner-controlled lifecycle admission. It does not replace `DecisionModel`,
turn `model_kind` into a permission system, or make a policy category an
authority claim.

Policy and Agent remain separate. Policy declares identity, ports and execution
requirements; the Agent/role binding grants observation visibility, authority
and action permissions. A self-declared `human` or `commander` category cannot
change arbitration rights.

Each field declares stable ID/version, shape, dtype, unit, frame, timing,
truth/belief visibility, optionality and source authority. Actions additionally
declare endpoint, bounds, timing and required rights. Pre-binding admission
rejects missing fields, shape/unit/version mismatches, unauthorized world truth,
unsupported action families and incompatible timing before policy binding or
runtime side effects. Per-decision validation then checks produced action values,
current masking/authorization, expiry and timing through the existing action
endpoint; an action's runtime value cannot be validated before the Policy
produces it.

Author-declared policy categories are open metadata. Unknown categories neither
grant capability nor bypass owner checks. A minor revision or optional field is
admitted only through a declared projection/default policy that preserves tensor
ordering and provenance. Legacy `model_kind` callers use a staged explicit
bridge: deterministic `policy_id` selection and category matching happen in
this opt-in descriptor, while existing registry kind checks and report fields
remain authoritative until a separate migration decision replaces them.

## Proof and boundaries

The qualification proof binds scripted and learned/stand-in implementations to
the same field contract, tests positive optional-field projection and all
negative admission cases, and records contract identities as evidence. An
admitted `PolicyRuntimeBinding` now wraps the existing `DecisionModel`
reset/decide/close lifecycle, preserves observation provenance and validates
the produced action before returning it to the existing runtime. An owner-issued
`PolicyCheckpoint` metadata contract can now bind an artifact digest and the
policy, observation and action identities before binding. A small checkpoint
seam verifies immutable artifact bytes and then hands them to an owner-provided
loader, which remains responsible for framework deserialization and model
construction. The current maintained outputs remain authoritative; Python or
third-party code is not auto-admitted by a descriptor, and loading a real
external checkpoint through its production owner or migrating the native action
endpoint remains open.

Mechanism ports (#229), platform/force composition (#236/#237), and RuntimeFacade
capability presence (#224) remain separate owners; this ADR only defines the
agent-facing compatibility layer.

## Option comparison and implementation checkpoint

| Option | Disposition in this proposed ADR |
| --- | --- |
| Extend ObservationViewSpec and existing role contracts | target ownership remains here; broader catalogue work needs owner acceptance |
| Non-authoritative Policy descriptor consuming owner catalogues | proposed pilot route with unchanged DecisionModel lifecycle |
| Use a closed category enum as compatibility/permission | rejected; category metadata cannot prove contract compatibility or rights |

The pilot consumes the basic mission field catalogue from mission_obs_taxonomy and actual Air action dimensions/bounds. It checks source/frame, action timing/bounds, explicit optional defaults, deterministic selection and legacy-kind mismatch. The binding is exercised through the existing `DecisionRuntimeAgent`; the wrapped model still owns reset/decide/close and the domain action DTO. Checkpoint digest verification and the owner-loader protocol seam are covered, while full observation-view binding, production external checkpoint loading and native action endpoint migration remain open.

See [qualification evidence and remaining gates](../work/issues/rfc_qualified_composition_implementation.md). Lifecycle remains proposed; this checkpoint does not establish owner approval or production admission.
