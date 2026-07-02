# Agent Instructions

## Branch Hygiene

- Before making coding changes, check the current branch and worktree state.
- If the current branch is `main`, ask the user whether to create a feature or fix branch before editing files.
- If the worktree is dirty, warn the user before starting new work and help separate existing changes into the appropriate branch or stash.
- Do not mix unrelated feature, fix, or chore changes in the same local branch unless the user explicitly asks for that.

## Change Scope

- Keep changes focused on the user-requested feature, fix, or chore.
- Avoid unrelated refactors, formatting churn, generated files, or metadata changes unless they are required for the task.
- If unrelated issues are discovered, mention them separately instead of folding them into the current change.

## Tests and Verification

- Add or update tests for new features, bug fixes, and behavior changes.
- Prefer focused tests that cover the new behavior, regression, or edge case being changed.
- Run the relevant test suite or targeted tests before finishing.
- If tests cannot be run, explain why and describe the residual risk.
- For lint/type-check changes, run the relevant lint/type-check command and report any remaining unrelated findings.

## Documentation and Configuration

- Update README, add-on docs, config schema, examples, or release notes when user-visible behavior or configuration changes.
- Keep documented defaults and option names aligned with the implementation.
- Avoid committing local-only files such as `.DS_Store`, editor caches, or temporary artifacts.

## Delivery Notes

- Summarize what changed, what was verified, and what remains.
- Call out any files intentionally left unstaged or any pre-existing dirty worktree state.
