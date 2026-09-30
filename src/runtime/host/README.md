# `src/runtime/host` Boundary

`runtime/host` contains the non-production host candidate used by the
long-horizon governance work. It owns host-bound publication, replacement and
state-transfer admission, generation fencing, bounded shutdown, and dark or
shadow evidence paths. The candidate is not a maintained facade and does not
authorize production caller cutover.

## Allowed

- Host identity, incarnation, episode, lease, candidate, and transfer values.
- Dark/shadow publication and replacement barriers at governed boundaries.
- Stable runtime-contract vocabulary and the native composition/engine seams
  needed by an explicitly admitted candidate adapter.
- Bounded quarantine, retry, and orphan-reclamation evidence.

## Forbidden

- Python or other binding logic.
- Direct truth-changing production publication or caller cutover.
- ECS system registration, step scheduling, or a second facade owner.
- Raw ownership of APIs outside the explicit candidate and adapter contracts.

The candidate remains a build-tree/dark-shadow surface until the later
maintained-facade parity, activation, rollback, and cutover gates are accepted.
