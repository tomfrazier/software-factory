# Optional Supercov evidence integration

Implemented 2026-09-23. Supercov is a local measurement dependency pinned to
1.2.0, Rust contract v1. Its quality command and direct Jev calls are not used.
Our own Jev gate retains context review, byte budgets, revision checks and routing.

## Install on the execution Mac

From the factory checkout, with Node 22 or later and npm installed:

```bash
npm install --prefix .tools/supercov --save-exact supercov@1.2.0
.tools/supercov/node_modules/.bin/supercov --version
bash scripts/factory-python.sh scripts/supercov_smoke.py \
  --supercov "$PWD/.tools/supercov/node_modules/.bin/supercov" \
  --out "$PWD/.artifacts/supercov-smoke-001"
```

Use a new output directory for each run. Installation is optional; the normal Mac
setup does not install this dependency. The adapter verifies the exact binary
version each time. The smoke test verifies branch evidence and preservation of a
failed test even when coverage is 100%. Run it on the Mini itself, then check the
actual target project's test runner. The laptop result does not establish Mini
or every-language compatibility.

## Collect project evidence

Use a dedicated project worktree. Add `.supercov/` and `.artifacts/` to that
project's ignore rules. Run its trusted complete test command, for example:

```bash
bash scripts/factory-python.sh scripts/supercov_evidence.py \
  --repo /absolute/path/to/project \
  --supercov "$PWD/.tools/supercov/node_modules/.bin/supercov" \
  --out /absolute/path/to/project/.artifacts/coverage-001 \
  -- npm test
```

The collector strips TYPESAFE_API_KEY from subprocesses, never invokes a shell
for the test command, and never calls Supercov quality. Other environment
variables remain available because the project's test command may need them.
Run only a trusted command in an appropriate test environment.

The collector creates private output files, records the actual command and exit
status, discovers exactly one newly created run, then queries that immutable run
ID. It rejects concurrent ambiguous runs, changed inputs, mismatched commands,
unsupported response envelopes, malformed counts, and missing measurement status.
It binds tracked and nonignored untracked file contents, including configuration,
plus the Git revision. Ignored dependencies, external services and environment
values are not captured by that digest; record relevant toolchain/environment
provenance separately. Symlink inputs and submodules are currently unsupported.

Exit 3 means a passing test was observed in shadow mode. Exit 1 means a failed or
unknown test result; inspect report.json to distinguish them. Exit 2 means an
adapter error and no usable final report. No exit grants a workflow pass.

The report records test status separately from measurement status, coverage,
source scope, and the agent-assessed assertion summary. Raw query pages and the
execution log are retained with hashes. Pages can be partial; their pagination
metadata remains visible. Missing flow explanations are unassessed, not passing.
Failed tests stay failed even when coverage reaches 100%.

## Feed the existing Jev gate

Use selected lines of report.json and relevant raw assertion/gap records as
hashed `result` source excerpts in the normal manifest. Include the requirement,
actual test, and relevant implementation separately. Use the report's revision
binding for checks; use `failed` for a failed test and `unknown` for stale or
unsupported evidence. Measurement availability alone is not a passed quality
check. Review the collector's source scope and any partial pages before declaring
an inventory complete. The adapter deliberately does not invent a manifest's
acceptance criteria or declare that all project behavior is covered.

Normal `prepare` checks apply, including size and privacy limits. Oversized
reports need selected primary excerpts. The adapter is local; it does not
upload the reports or automatically send them to Jev.

## Additional judgment questions

Catalog and policy 1.1.0 add `change-risk`, requiring before/after primary excerpts:

- `test_weakened`: an existing test checks less after the change.
- `injection_introduced`: untrusted input crosses into an executable query or command unsafely.
- `credential_embedded`: a credential moves from configuration into a source literal.

The context-sufficiency question remains mandatory. Secret detection and static
checks stay local. Never send a real credential to ask whether it is a credential.
Use a reviewed redacted excerpt and disclose what was removed; mark the unit
incomplete if necessary facts are missing.

This stage always requires at least review, even under enforce mode. Strong
adverse answers can block. It cannot grant an enforced pass until a future,
explicitly calibrated policy revision removes that restriction.

## Calibration and observed results

Prepare matched development examples without sending them:

```bash
bash scripts/factory-python.sh jev-gate/examples/calibration.py \
  --out .artifacts/calibration-001
```

The generator produces six manifests and plans. Oracle labels stay outside the
fixture repo and outgoing requests. These are tiny synthetic cases, not public
benchmark or held-out evaluations. Review each plan before using the normal
live gate command and its approved hash. The generator performs no API calls.

Six live calls to jev-1.13.0 on 2026-09-23 produced:

| Matched condition | Adverse example | Safer example |
|---|---:|---:|
| Assertion removed / strengthened | 0.95 | 0.04 |
| Query interpolation / parameters | 0.98 | 0.04 |
| Literal password / environment | 0.94 | 0.05 |

All adverse cases routed to blocked; all safer cases routed to review because
calibration is incomplete. All six retained `workflow_action: observe`.
The calls used 5,920 input tokens in total. No threshold was tuned from this set.
The current response validator accepted all six responses without modification;
this does not settle every possible provider rounding edge case.

A Node smoke test on this laptop measured 50% branch coverage before adding
missing discount and rejection tests, then 100%. A deliberate failing assertion
still produced a failed test status at 100% coverage. Assertion flows remained
unassessed, correctly distinct from measured execution.

The planned real-defect corpus and held-out calibration remain future work.
See [the benchmark review](jev-benchmarks-supercov-review.md). Parser-assisted
context selection and response caching are also deferred: manual grounded
excerpts already work, and neither is needed to validate this adapter. Reusing
cached answers for changed evidence is never permitted.
