# Review Severity and Boundary Protocol

Shared contract for automated and human reviews in this repository. Review
prompts reference this file; findings must follow its severity ladder,
blocking semantics, and scope boundaries. The goal is convergence: each
round of review should move a change closer to merge, not open an unbounded
frontier.

## Severity ladder

| Level | Definition | Blocking? |
|-------|------------|-----------|
| P0 | Breaks correctness, loses data, or defeats a security guarantee on a mainline path (default configuration, shipped scenarios/fixtures, documented workflows). | Yes |
| P1 | Real defect or regression reachable under specific but plausible conditions; includes broken contracts between components and races with observable consequences. | Yes |
| P2 | Hardening beyond the declared threat model, edge cases reachable only with synthetic data not present in any repository fixture, performance concerns without a demonstrated pathology. | No |
| P3 | Style, naming, readability, documentation polish. | No |

Blocking means "should change before merge". P2/P3 findings must be listed
separately under a "Follow-up suggestions" heading and must not be counted
toward an approve/reject verdict. A review whose only findings are P2/P3
concludes: "No blocking issues; N follow-up suggestions."

## Default threat-model boundary

Unless a change explicitly claims a stronger guarantee in its own
documentation, reviews assume:

- The local developer environment is semi-trusted: user-writable caches,
  home-directory configuration, git configuration, and PATH are not
  defended against an attacker who can already write to them. Defenses
  against such attackers are P2 hardening, not blocking findings.
- Supply-chain integrity is anchored at pinned digests/lockfiles. Attacks
  requiring compromise of the pinning mechanism itself are out of scope.
- Denial-of-service by the machine owner against their own tooling is out
  of scope.

When a finding sits outside this boundary, report it once as P2 with a note
that it exceeds the default threat model, and suggest recording it under
"Accepted residual risks" below rather than re-raising it.

## Complexity audit

Every review includes a complexity audit of the changes: new functionality
must earn its structure. Check, in order:

1. **Reuse before reimplementation.** Does the change reimplement something
   the repository already provides (helpers, DTOs, validation layers,
   rendering paths, test utilities)? Search for existing equivalents before
   concluding. Duplicating a maintained implementation splits future
   maintenance and is a P1 finding.
2. **Speculative abstraction (YAGNI).** Does a new abstraction (class,
   layer, configuration knob, DTO field, feature flag, extension point)
   have at least a second user or a concrete, named near-term consumer? If
   not, flag it as P2 with the simpler inline alternative.
3. **Mechanism minimization.** Could the same behavior be expressed with
   less machinery -- fewer layers, fewer states, merged near-duplicate
   functions, a plain function instead of a class, data instead of code?
   Report as P2/P3 with the concrete simplification.
4. **Defensive code at internal boundaries.** Validation or fallback logic
   for inputs that cannot occur (values produced and consumed inside the
   same trusted codebase) is noise; flag as P3. Validation at system
   boundaries (user input, external files, network payloads) is correct
   and must not be flagged.

Severity mapping: duplicated maintained functionality is P1 (blocking);
unused abstractions and reducible mechanisms are P2; readability-level
simplifications and internal-boundary defensiveness are P3. The audit's
purpose is convergence toward the smallest change that does the job, not
style enforcement.

## Depth-probing rule

When reviewing a defense or validation mechanism, evaluate its **complete
boundary in one round**: state what the mechanism does defend, the next
layer of attack it does not, and where the sensible stopping point is given
the threat model above. Do not return one layer deeper on each successive
review round; that pattern produces unbounded review cycles on a frontier
that was already knowingly accepted.

## Convergence protocol for repeated reviews

Before reviewing, read the pull request's existing review comments and the
author's responses (provided as context by the workflow when available):

1. Do not re-raise a finding that was reported and fixed, reported and
   answered with an accepted-risk rationale, or recorded below.
2. Focus on commits pushed since the last review round; the accumulated
   diff is context, not the primary search space.
3. New findings in previously reviewed code are allowed but must meet the
   P0/P1 bar to block.

## Accepted residual risks

Maintainers record knowingly accepted risks here so reviews stop re-raising
them. Each entry: scope, risk, rationale, date.

- `tools/environment/arnis/bootstrap.py` — attackers with write access to
  the local source cache *and* git/tool configuration can defeat pinned-
  build verification in ways beyond raw-byte tree comparison (e.g. PATH or
  toolchain substitution). Verification stops at byte-identity of the
  source tree against the pinned commit plus pinned patch; deeper
  local-host compromise is out of scope per the default threat model.
  (2026-07-21)
