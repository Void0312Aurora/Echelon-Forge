# Kill-Chain Evidence Retention

The raw run-level packets produced by the 2026-09-15 kill-chain work are
generated evidence, not maintained repository authority. They are intentionally
not versioned under `docs/**/review_packets/`.

The local reproduction surface is the ignored directory
`artifacts/kill_chain/20260915/raw_review_packets/`. CI or release workflows
may publish that directory as an external artifact, but a published artifact
must carry the generator commit, schema version, input/config digests, file
SHA-256 values, and a retrieval/retention owner before it is treated as
admitted evidence.

The repository retains only concise conclusions, human-readable figures, and
small manifest records. The raw packets remain reproducible through the
diagnostic tools and an explicit `--output-dir` pointing at the ignored
artifact surface.

This follows the long-horizon governance rule: closed packets leave maintained
authority while provenance and retrieval routes remain explicit.
