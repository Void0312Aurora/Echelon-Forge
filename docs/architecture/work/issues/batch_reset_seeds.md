# Batch reset and setup seeds

Native reset and full setup admit exactly these modes:

- Empty: seed world `i` with `42 + i`.
- One base seed: seed world `i` with `base + i`.
- One seed per world: use each supplied seed unchanged.

Arithmetic uses uint32 wraparound. Every other count is an input error checked
before parallel reset or setup begins. The compiled Python loader resolves the
same modes before producing contexts and the maintained setup request; its
per-world context therefore records the effective seed used by native setup.
Native state-transfer evidence already includes `StableIdentityState.episode_seed`.

DTO construction without a target cannot know the batch size. The receiving
facade/native runtime validates it. No malformed supplied array falls back to
the empty-mode defaults. Tests inspect effective native singleton seeds,
including wraparound, and prove entity survival, seed and dt preservation after
rejected calls with multiple worker threads enabled.
