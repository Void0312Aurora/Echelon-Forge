# Temporal HMoE Policy Plan - 2026-05-25

Language: English canonical; Chinese companion not maintained (English-only work surface).

Document kind: `plan`
Lifecycle: `draft`
Canonical: `docs/learning/work/issues/temporal_policy_roadmap.md`
Owner: `learning/policy-architecture`
Last verified: `not established`
Content status: 2026-05-25 planning snapshot; current implementation names are governed by the learning standard.

## Purpose

Build a model-side path from the current reactive HMoE PPO policy to a temporal
policy that can reason over recent observations, actions, and launch outcomes.
The first target is `1v1` air combat, but the rule is cross-domain: keep
simulation memory limited to physical state and contracts; put behavioral memory
in the policy.

## Findings Recorded On 2026-05-25

- `python/models/transformer.py::TransformerExtractor` is a per-frame token
  extractor. It attends over `instruments`, `mission`, optional `proprio`,
  `contacts`, and `rwr` tokens from the same observation frame.
- `python/rl/policy_algo/policies.py::HierarchicalMoEExecutionPolicy` calls
  `extract_features(obs)` per PPO step and does not carry hidden state or a
  causal attention cache.
- `gym_envs/universal_env_parts/observations.py` can expose `proprio`, but that
  is currently only the previous action. It is useful evidence, not a temporal
  policy by itself.
- `python/rl/policy_algo/device_dict_rollout_buffer.py` stores rollout tensors
  as `(time, env, ...)`, but `get()` flattens them to shuffled per-step samples.
  PPO training therefore loses contiguous sequence structure.
- `python/world_model/networks.py::GRUActor` and the Dreamer path already
  contain history-capable policy pieces, but they are separate from the current
  maintained PPO/HMoE air-combat line.

## Architectural Boundary

The simulation should store and expose physical truth or sensor-observable
facts:

- ammunition and launcher availability;
- weapon cooldown and launch constraints;
- missile entities, in-flight missiles, and ownership;
- launch events and sensor/RWR indications when observable;
- target tracks and track quality.

The policy should learn tactical timing:

- whether a previous shot is still pending assessment;
- whether to hold fire, re-attack, or switch target;
- how to coordinate fire with geometry, range, and closure;
- when repeated shots are useful rather than accidental.

Environment-side latches may be acceptable only as action-interface contracts or
hard physical constraints. They should not become tactical memory substitutes.

## Candidate Paths

### Path A: Observation Window Extractor

Add a temporal observation wrapper and a new extractor, for example
`TemporalTransformerExtractor`, that consumes a fixed window of recent
observations:

- shape options:
  - add a top-level `history` axis to each Dict observation key, or
  - add explicit keys such as `instruments_history`, `contacts_history`,
    `rwr_history`, `mission_history`, and `action_history`;
- encode each frame with the current per-frame token extractor or lightweight
  projections;
- apply causal or strictly ordered temporal attention across frame embeddings;
- output the most recent frame's contextual embedding to the existing
  `SquashedMultiInputPolicy` / `HierarchicalMoEExecutionPolicy`.

Advantages:

- lowest disruption to SB3 PPO;
- can keep current per-step PPO loss and buffer sampling;
- quick probe for whether temporal context fixes repeated launch behavior.

Limitations:

- temporal windows are part of the observation, so memory length is fixed;
- per-step random minibatches still train on precomputed windows, not on hidden
  state carried through minibatch sequences;
- large visual observations would be expensive unless excluded or downsampled.

Recommended first use:

- non-visual air-combat HMoE with `history_len` in the 8-32 step range;
- include previous actions, missile count/remaining ammo, contact features, and
  launch-event observables where physically appropriate.

### Path B: Recurrent HMoE PPO

Create a recurrent policy variant around the HMoE head:

- feature extractor embeds the current frame;
- a GRU/LSTM carries hidden state per environment during rollout;
- rollout buffer stores hidden states and `episode_starts`;
- training samples contiguous sequences and masks episode boundaries;
- actor and critic either share a recurrent trunk or use separate recurrent
  heads.

Advantages:

- well matched to online control;
- memory is not limited to a fixed observation stack;
- existing `GRUActor` in `python/world_model/networks.py` gives implementation
  precedent.

Limitations:

- requires deeper PPO integration than Path A;
- must update `collect_rollouts`, `evaluate_actions`, buffer samples, and
  inference/reset state handling together;
- SB3 compatibility and CUDA device-buffer path need careful regression tests.

### Path C: True Causal Transformer PPO

Build a sequence-native policy:

- store rollout chunks as contiguous `(batch, time, feature)` samples;
- apply causal masks over observation/action/history tokens;
- predict actions and values for each timestep in the training sequence;
- use the last state or full sequence loss with valid masks.

Advantages:

- best alignment with the stated Transformer direction;
- attention can directly inspect earlier launch actions, track evolution, and
  delayed outcomes;
- scales naturally to multi-agent event histories once observation schemas are
  stable.

Limitations:

- largest implementation cost;
- action log-prob, value loss, KL, entropy, and advantage normalization must all
  become sequence-aware;
- needs memory and throughput profiling before broad use.

## Recommended Implementation Ladder

1. Document and freeze the boundary: no new tactical memory boards for weapon
   behavior unless they represent physical constraints or explicit action
   contracts.
2. Add observation-level temporal windows for non-visual execution tasks.
   Implement a small wrapper in the env/runtime layer and a
   `TemporalTransformerExtractor` in `python/models/transformer.py` or a sibling
   module.
3. Create a stage-0 air-combat temporal config under
   `examples/config/training/active/air_combat/` that differs from the current
   HMoE probe only by temporal settings.
4. Run a short fixed-policy and PPO smoke check:
   - observation shapes are stable in normal and world-batch runtime paths;
   - no non-finite features;
   - launch count under held-fire diagnostics is explainable by action
     semantics and physical constraints.
5. Upgrade `DeviceDictRolloutBuffer` or add a sibling sequence buffer that can
   sample contiguous sequences without flattening time/env dimensions.
6. Implement recurrent HMoE or causal-Transformer HMoE as the maintained
   sequence-native path.
7. Compare reactive HMoE, observation-window HMoE, and sequence-native HMoE on
   the same air-combat stage-0 and stage-1 curricula.

## Initial Code Touchpoints

- `python/models/transformer.py`
  - add temporal extractor classes or factor out reusable frame-token embedding;
  - preserve current `TransformerExtractor` checkpoint compatibility.
- `gym_envs/universal_env.py`
  - maintain per-env observation history for the single-env path.
- `python/rl/runtime/world_batch_vec_env.py`
  - maintain per-handle observation/action history for world-batch training.
- `gym_envs/universal_env_parts/observations.py`
  - define how history keys are assembled and sanitized.
- `python/rl/policy_algo/policies.py`
  - add temporal HMoE policy only when hidden state or sequence semantics are
    needed; Path A can reuse the current policy class.
- `python/rl/policy_algo/device_dict_rollout_buffer.py`
  - add sequence sampling only after Path A proves useful.
- `python/rl/policy_algo/ppo_adaptive_kl.py`
  - sequence-native training must update `collect_rollouts()` and `train()`.

## Air-Combat Acceptance Signals

For the current missile-repeat issue, success should not mean "the environment
silently blocks all repeated shots." It should mean:

- the observation contains enough physical evidence for the policy to know
  whether it has recently fired and whether missiles are already in flight;
- the policy can learn a low repeated-shot rate when the target is unchanged and
  the first missile is still tactically relevant;
- deliberate salvos remain possible in later curriculum phases if reward and
  doctrine make them useful;
- fixed held-fire diagnostics clearly separate action-interface behavior from
  learned policy behavior.

## Open Design Questions

- Should `fire_weapon` become an explicit pulse command at the action adapter
  boundary, or remain a continuous high/low control whose timing is learned?
- Which launch observables are physically available to the pilot in each
  realism stage: own missile count, missile track, launch event bit, RWR launch
  cue, or only ammo/cooldown?
- What is the minimum useful history length for stage-0 weapon employment at the
  current simulation timestep?
- Should temporal attention include previous actions as first-class tokens or
  rely on `proprio` history?
- When visual observations are enabled, should visual history be excluded,
  sparsely sampled, or compressed before temporal attention?

