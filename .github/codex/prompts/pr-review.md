Review this pull request against the full review contract in
`.github/codex/review-boundaries.md`: the review dimensions (correctness,
contracts/compatibility, tests, security, complexity, architecture
consistency, documentation sync), the severity ladder and blocking
semantics, the threat-model boundary, risk-tiered depth, the round budget,
the finding lifecycle/arbitration rules, and the gate-feedback discipline.
That file is the shared contract for every review round; read it before
writing findings.

Review discipline:

- Only report high-confidence issues. Avoid style-only comments, broad
  refactors, speculative suggestions, and duplicate findings.
- If prior review context is provided, read it first. Do not re-raise
  findings that were fixed, answered with an accepted-risk rationale, or
  recorded as accepted residual risks. Focus on commits pushed since the
  last review round; treat the accumulated diff as context, not as the
  primary search space.
- When reviewing a defense or validation mechanism, evaluate its complete
  boundary in one round (what it defends, what it does not, where the
  sensible stopping point is). Do not go one layer deeper per round.
- Run the complexity audit on the added functionality: reuse before
  reimplementation (search the repository for existing equivalents),
  speculative abstractions without a second user, machinery that could be
  simpler, and defensive code at internal trust boundaries. Classify each
  audit finding on the same severity ladder (duplicated maintained
  functionality is P1; the rest is P2/P3).

For each finding:

- assign a severity from the ladder (P0-P3) and name its review dimension;
- cite the relevant file and line or diff hunk;
- explain the impact;
- suggest a concrete fix;
- if the defect class is mechanical (catchable by a linter, type checker,
  or contract test), add a one-line gate suggestion for the class.

Output format:

1. A `## Blocking findings` section listing only P0/P1 items (or "none").
2. A `## Follow-up suggestions` section listing P2/P3 items (or "none").
3. A `## Complexity audit` section: either "No over-engineering found" or
   a short list of simplification/reuse opportunities with severities
   (items already listed above may be referenced instead of repeated).
4. A one-line verdict: either "Blocking issues found: N" or
   "No blocking issues; N follow-up suggestions."

Only P0/P1 findings may justify requesting changes. A review whose only
findings are P2/P3 is an approval with suggestions.
