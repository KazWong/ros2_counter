# Agent Git Branching Policy

The framework owns Git mechanics for framework-managed work; agents provide source changes and review decisions.

## Branch ownership

- One work item owns one active development branch.
- Branch convention: `agent/<work-item-id-lowercase>`.
- Example: `agent/rbt-002`.
- Branch from the work item's recorded base branch/baseline revision.
- Never implement directly on `main`, `master`, `develop`, `development`, or a release branch.
- Retries/corrections continue on the same work-item branch.
- Do not force-push automatically.

## Candidate commit

The framework creates the candidate implementation commit after coder success. Agents do not manually create the framework candidate commit.

A request-derived summary may be used for human-facing commit/PR text, but no independent work-item title is authoritative state.

## Candidate integrity

The commit published to a pull request must be the exact commit that passed every required gate:

```text
candidate_sha
  == local_test_sha
  == integration_test_sha   (when required)
  == reviewed_sha
  == pr_head_sha
```

Any tracked change after candidate creation invalidates the relevant verification binding. Generated build/test output must remain untracked/outside approved source scope.

## Remote publication

- Framework lifecycle code pushes the work-item branch only after deterministic verification and independent review pass.
- Framework lifecycle code creates the configured GitHub or Bitbucket PR automatically.
- `PR_OPEN` means a real remote PR exists and its head SHA matches the reviewed candidate.
- Human/agent inspection uses `agentctl show <WORK_ITEM> git`; the normal human provider-review point is the open PR.
- Human merge approval remains mandatory and repository/provider branch protection performs the actual protected-branch merge.
