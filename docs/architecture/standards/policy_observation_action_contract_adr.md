# ADR: field-level policy observation and action admission

Language:
- English canonical: `policy_observation_action_contract_adr.md`
- Chinese companion: [policy_observation_action_contract_adr.zh.md](policy_observation_action_contract_adr.zh.md)

Document kind: `standard`
Lifecycle: `proposed`
Canonical: `docs/architecture/standards/policy_observation_action_contract_adr.md`
Owner: `architecture/agent-contracts`
Last verified: `2026-11-26`

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
remain authoritative for legacy selection and reporting until a separate
migration decision replaces them. They never establish action authority.

## Admission receipt threat model and validation ownership (#295)

`_AdmissionValidationToken` and `PolicyAdmission._validation_marker` are private,
in-process consistency receipts. They are intentionally not cryptographic tokens,
secrets, signatures or a sandbox. The receipt snapshots the complete
`PolicyDescriptor`, the issuing `AgentBinding`, the admission schema version and
all public admission fields. `as_dict()` exports evidence without the marker;
reconstructing an admission from serialized evidence cannot restore admission.

| Input / actor | Boundary and guarantee |
| --- | --- |
| Accidental caller bugs | Reject a hand-built `admitted=True`, altered admission fields, a resealed rejection, or reuse with a changed descriptor/version/checkpoint owner. A changed Agent binding requires fresh admission; an existing receipt is rejected when compared with the new binding. The runtime also rejects a different role or an explicit incompatible authority scope. |
| External checkpoint bytes | Bytes cannot supply a receipt or grants. Binding gates run before either checkpoint loader seam or owner loader; SHA-256 is checked on an immutable byte copy before owner loading. Digest identity does not prove publisher trust or make executable deserialization safe; the trusted owner controls metadata provenance, loader selection and model protocol. |
| Same-process Python code | Trusted and outside the isolation threat model. Such code can import the private token type, construct a matching receipt, mutate frozen objects deliberately or replace validators. Neither an underscore nor a frozen dataclass prevents this. Hostile executable policies require a separate process/isolation design, which this pilot does not provide. |

The common `validate_policy_admission` helper checks receipt consistency. It
does not repeat owner catalogue negotiation or contact a revocation service.
Owners must re-admit when static descriptors, catalogues or grants change;
the stored receipt cannot discover a later external owner change by itself.

Validation has three distinct responsibilities:

1. `admit_policy` negotiates static field semantics/source visibility,
   observation/action major and minor versions, action interface/dimension/timing,
   Agent grants and checkpoint metadata agreement once using owner evidence.
2. `PolicyRuntimeBinding.__init__` checks the receipt and binding inputs.
   `from_checkpoint_artifact()` uses the same gate **before** loading, including
   finite ordered bounds and all optional callbacks, and freezes caller bounds
   and defaults. Construction repeats the cheap gate after the owner callback;
   it never re-runs catalogue admission. This deliberate boundary check is kept,
   as are digest verification and the returned model's lifecycle protocol check.
3. Every `decide` checks observation values/provenance and produced action
   dimension/bounds/timing, then invokes the configured owner action authorizer
   for current mask, authority and expiry before projection. A receipt never
   caches dynamic authorization. Held-output validity stays with the existing
   action-hold/endpoint owner.

## Versioned legacy migration adapter (#295)

`LegacyDecisionModelAdapter` consumes the explicit
`echelon_forge.legacy_decision_model.v1` format: `schema_version`, `model_id`,
`domain`, `role_id`, `model_kind`. Missing/unknown versions and extra fields
fail closed. Existing unversioned Python consumers can construct the adapter
explicitly; `DecisionRuntimeAgentSpec.legacy_adapter` provides this conversion.
Registration, registry selection and runtime checks share
`normalize_legacy_model_kind`; `DECISION_MODEL_KINDS` remains the v1 compatibility
vocabulary, not the vocabulary of open `PolicyDescriptor.categories`.

The migration sequence is explicit: obtain the adapter, call its `admit_policy`
with the existing registry, descriptor, Agent binding and owner catalogue/version
evidence, require a positive admission, create through existing `registry.create_for`,
then wrap in `PolicyRuntimeBinding` and pass it to `DecisionRuntimeAgent`.
The adapter verifies model ID/domain/role/kind/status selection and the descriptor's
explicit `legacy_model_kind` before ordinary Policy admission. It invokes no
factory and has no reset/decide/close dispatcher. Categories are never translated
to kinds or grants, including `human`, `commander` or unknown author tags.

Tests compare all four v1 kinds through the existing runtime, reject mismatched
or unauthorized migration, and assert zero checkpoint-loader and owner-loader
calls for inadmissible inputs. The Air qualification compares direct legacy
actions with the adapter/admission/runtime path using the existing mission field
catalogue, maintained `takeoff4` bounds and `build_pilot_action` projection.

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
construction; `PolicyRuntimeBinding.from_checkpoint_artifact` keeps that
verified loading step on the existing binding path. Binding admission, its
owner-issued validation marker, checkpoint agreement, action timing and width,
and action callbacks are checked before invoking the loader. A valid byte
digest does not bypass rejected or caller-forged admission. The selected maintained
observation view is admitted by its owner and its identity/version is carried
into the existing model context. The binding can run an owner action-authorizer
callback after generic bounds/timing checks and before projection, so live mask,
authority and expiry decisions remain owner-controlled. The current maintained
outputs remain authoritative; Python or third-party code is not auto-admitted by
a descriptor, and loading a real external checkpoint through its production
owner remains open. The binding can hand an authorized action to an explicit
owner projector after contract checks; wiring that projector to the production
native action endpoint remains open. The explicit qualification consumer below
now exercises the existing native facade endpoint without enabling a default
Policy profile.

Mechanism ports (#229), platform/force composition (#236/#237), and RuntimeFacade
capability presence (#224) remain separate owners; this ADR only defines the
agent-facing compatibility layer.

## Option comparison and implementation checkpoint

| Option | Disposition in this proposed ADR |
| --- | --- |
| Extend ObservationViewSpec and existing role contracts | target ownership remains here; broader catalogue work needs owner acceptance |
| Non-authoritative Policy descriptor consuming owner catalogues | proposed pilot route with unchanged DecisionModel lifecycle |
| Use a closed category enum as compatibility/permission | rejected; category metadata cannot prove contract compatibility or rights |

The pilot consumes the basic mission field catalogue from mission_obs_taxonomy and actual Air action dimensions/bounds. It checks source/frame, action timing/bounds, explicit optional defaults, deterministic selection and legacy-kind mismatch. The binding is exercised through the existing `DecisionRuntimeAgent`; the wrapped model still owns reset/decide/close. The maintained observation view is admitted before binding, and an owner authorizer can reject an actual action for current mask, authority or expiry before the owner projector creates the domain DTO. Checkpoint digest verification and the owner-loader protocol seam are covered; production external checkpoint loading and native action endpoint wiring remain open.

See [qualification evidence and remaining gates](../work/issues/rfc_qualified_composition_implementation.md). Lifecycle remains proposed; this checkpoint does not establish owner approval or production admission.

## External checkpoint and native consumer proof

The opt-in [external JSON example](../../../examples/policies/README.md) owns
only its coefficients and the existing DecisionModel lifecycle. It is an
untrained linear stand-in, as allowed by the RFC proof plan; it loads JSON data
after the checkpoint digest and binding-admission gates, without framework
deserialization or automatic registration. Field order comes from the mission
packet owner, action dimensions/projection from the Air action owner, and bounds
from the maintained `takeoff4` space.

The focused consumer reads an actual native maintained command, projects its
basic mission vector with the existing domain function and supplies the named
fields to `PolicyRuntimeBinding`. `DecisionRuntimeAgent` runs the loaded model;
generic contract checks and an explicit qualification authorizer precede the
owner `PilotAction` projection and actual native facade submission. Native
mission speed changes from 220 to 110 cause the model and instrument throttle to
change from 0.8 to 0.4 across two decisions and six native steps. Physical
position advances, and native state matches a direct-action reference world.
The native runtime/factory remains the sole execution/materialization authority.

Negative controls cover byte digest, checkpoint schema, observation order,
nonfinite coefficients, closed mask, expired action and out-of-bounds output;
rejection leaves existing world snapshots unchanged. The mask/expiry provider
here is a qualification harness, not a production authorization service. This
proves the scoped checkpoint/model/DecisionRuntime/native consumer seam;
trained checkpoint quality, production selection/profile admission, broader
typed observation migration and complete Air matrix execution remain open.
