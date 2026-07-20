Handle the requested Codex task from a GitHub issue or pull request comment.

Focus on the user's explicit request. Inspect the repository and relevant context before answering.
Do not modify files in this comment-task workflow. If the request needs code changes, describe the recommended change or ask the maintainer to run the manual Codex patch workflow.
Provide a concise answer with any important caveats.

If the request is a review of a pull request (e.g. "review", "re-review",
"check the latest changes"), this is a review task: read and follow
`.github/codex/prompts/pr-review.md` and the severity/boundary/convergence
contract in `.github/codex/review-boundaries.md`, including reading any
provided prior review context and reporting findings in the
blocking/follow-up format defined there.
