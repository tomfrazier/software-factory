---
name: jev-gate
description: Audit software-factory checkpoints with TypeSafe Jev using scoped text evidence, typed questions, and explicit uncertainty. Use for task scope, shared-service changes, test plans, evidence claims, review fixes, release claims, prose fidelity, or risk triage when the project enables Jev.
metadata:
  version: "1.1.0"
---

# Jev judgment audit

Python 3.10+, Git, and the dependencies in requirements.txt. Live calls require TYPESAFE_API_KEY and an explicitly reviewed context plan. Offline preparation and replay need no API key.

Use Jev for narrow semantic judgments. The builder still investigates and fixes
code. Tests, authorization, worktree isolation, and Greptile remain independent
requirements. A Jev result applies only to the listed units and evidence.

## Select a checkpoint

Use `intake`, `architecture`, `test-plan`, `evidence`, `review`, `ship`, `prose`,
`risk`, or `change-risk`. Each evaluates three atomic conditions plus a context-sufficiency
question. Read the [question map](references/question-map.md) to select a suitable
unit. Do not apply a shared-service extraction question to an unrelated change.
When a required condition cannot be evidenced, request more evidence or a human
review. Never invent facts to fill a required role.

The project owner chooses applicable checkpoints and required deterministic
checks. Start in `shadow` mode. Read [operation and calibration](references/operation.md)
before enabling enforcement. Repo-wide completeness is a responsibility of the
calling workflow; this tool checks the declared unit inventory, not whether its
author found every relevant requirement.

## Build and inspect context

1. Run normal checks and collect primary evidence for the current revision.
2. Create the [manifest](schemas/manifest.schema.json) with one subject per unit,
   exact source ranges and SHA-256 hashes, required checks and evidence, and an
   independently reviewed `expected_units` inventory. Mark gaps with
   `complete: false`; high-risk changes require `risk: high`.
3. Follow [context rules](references/context.md). Keep related requirements,
   callers, changed behavior, and observations together. Jev cannot inspect media.
4. Prepare a plan using `scripts/jev_gate.py prepare`. Inspect the exact outgoing
   excerpts. The privacy scan is only a backstop. Keep plans and results in
   ignored `.artifacts/` storage, with an appropriate local retention policy.
5. Run with `--live` and the prepared plan hash only when TypeSafe disclosure is
   authorized. Get the API key from the environment; never place it in a manifest.
   For offline testing, use `--responses`; replay cannot authorize continuation.

See [operation](references/operation.md) for complete commands and the runnable
example. Use the same interpreter for dependency installation and execution.

## Act on the result

- `pass`: all scoped judgments and declared deterministic checks passed.
- `review`: gather missing primary evidence or ask a person to assess the specific
  unit. Summary-only reasoning, high risk, and uncertain probabilities stay here.
- `blocked`: address the cited condition or failed check, then rerun affected
  checks and rebuild the manifest. A generative reviewer explains and proposes fixes.
- `error`: no usable decision. Resolve the schema, stale input, size, or provider
  problem. Never reuse a prior pass or quietly switch models.

`shadow` only observes. Only a live, explicitly enforced pass returns exit code 0
from `run`. All other runs return 2 or 3. `prepare` returning 0 means the plan was
built, not that a checkpoint passed. Inspect `workflow_action` as well as `status`.
Jev cannot grant permission to push, publish, merge, resolve a review thread,
change a database, or bypass a failed test.

For uncertain results, allow at most one evidence expansion per unit. If the
judgment stays uncertain, route to a person or a reasoning model. Do not repeat
identical requests until one passes. Any changed evidence requires new hashes.

The `change-risk` stage checks weakened tests, injection, and embedded credentials.
It is uncalibrated and always requires at least review, even in enforce mode.
Use the [Supercov guide](../docs/supercov-integration.md) for optional measured
evidence and matched calibration examples.
