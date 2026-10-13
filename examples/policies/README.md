# External Policy checkpoint example

`air_basic_mission_linear.py` implements an untrained deterministic stand-in
using the existing `DecisionModel.reset/decide/close` lifecycle. Its JSON file
contains coefficients, a version and declared observation order. The loader
accepts JSON data only; importing the module registers no policy and imports no
native runtime or ML framework. This is a qualification example with no flight
performance or production admission claim.

The example consumes the four raw basic mission fields in the order supplied
by `mission_observation_field_names("basic")`. The caller obtains the action
dimension from the existing Air action owner and bounds from the existing
`takeoff4` space. The loader rejects incompatible checkpoint versions, field
order, parameter shapes and nonfinite coefficients. It does not clip an
out-of-bounds action or load executable Python from the artifact.

The focused native proof in
`tests/architecture/composition/test_rfc_qualified_composition.py`:

1. Reads the JSON artifact and binds its exact byte digest through
   `PolicyCheckpoint` and `PolicyRuntimeBinding.from_checkpoint_artifact`.
2. Reads a maintained mission command from the native facade and projects it
   with `build_air_mission_vector`, using the mission packet owner's catalogue.
3. Runs the model through the existing `DecisionRuntimeAgent`; contract checks
   and the explicit qualification authorizer run before the Air action owner
   creates a `PilotAction`.
4. Submits that action to `RuntimeFacade.set_pilot_actions_batch`, advances six
   native steps and checks control, physical movement and a direct-action
   reference world. A native mission speed update from 220 to 110 changes the
   model and observed native throttle from 0.8 to 0.4.
5. Rejects tampered bytes, unsupported schema, wrong field order, nonfinite
   coefficients, closed mask, expired action and out-of-bounds output. Rejected
   operations leave the existing native world snapshots unchanged.

On Windows, after building `ef_py` in the selected local build directory:

```powershell
$env:CMO_BUILD_DIR='build-rfc-mainline'
python -m pytest -q tests/architecture/composition/test_rfc_qualified_composition.py -k external_checkpoint
```

Mask and expiry inputs in this proof belong to the qualification harness.
The proof does not establish a production authorization provider, trained
checkpoint quality, rich ObservationView migration or execution of the Air
training matrix. Existing registries, default profiles and native factory/runtime
authority remain unchanged.
