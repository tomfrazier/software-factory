# Validation record

Date: 2026-09-22. Host: macOS, Python 3.14.2.
Runtime/test environment: `/private/tmp/skills-jev-test-env`.

## New integration

- 70 offline Jev tests passed.
- The new skill passed the skill-creator frontmatter and scaffold validator.
- Python compilation and `git diff --check` passed.
- All eight phase request shapes match the documented local request schema.
- The generated question snapshot matches the executable catalog.
- The demo produced pass, review, and blocked decisions from labeled synthetic
  responses, with zero network calls. Every replay returned exit code 3 and an
  observation-only action, including the synthetic pass.

Commands, run from the implementation worktree:

```bash
/private/tmp/skills-jev-test-env/bin/python -m pytest tests/test_jev_gate.py -q
/private/tmp/skills-jev-test-env/bin/python -m pytest tests/ -q
/private/tmp/skills-jev-test-env/bin/python jev-gate/examples/demo.py --out .artifacts/jev-demo
/private/tmp/skills-jev-test-env/bin/python /Users/tomfrazier/.codex/skills/.system/skill-creator/scripts/quick_validate.py jev-gate
python3 -m compileall -q jev-gate/scripts jev-gate/examples
git diff --check
```

Covered failure modes include missing/stale sources and checks, invalid ranges,
empty or duplicate coverage, path traversal and symlinks, secret patterns,
Unicode byte budgets, both per-request limits, run budgets, malformed/non-finite
JSON, unexpected models, incomplete response sets, invalid distributions and
Scores, threshold boundaries, summaries, high risk, failed deterministic checks,
changes during a call, partial multi-unit failure, redirects, bounded retries,
missing credentials, replay binding, output overwrite protection, and CLI routes.

## Existing recorder baseline

Before the Jev changes, the original suite had 8 passes and 15 failures.
The final combined suite has 78 passes and the same 15 original failures.
No new Jev tests fail. The failed original test names match the baseline exactly.

The installed FFmpeg lacks the required `ass` subtitle filter. Several original
tests also assume Linux `start_time_ticks` and `pidfd_send_signal` APIs on this
macOS host. The integration leaves these recorder tests and their implementation
unchanged. SHA-256 comparison confirmed that all 15 original implementation,
platform-reference, and license files selected for preservation still match the
baseline inventory. This is not a claim that the recorder suite passes on macOS.

Local evidence files:

- `.artifacts/jev-audit/baseline-tests.txt`
- `.artifacts/jev-audit/jev-tests.txt`
- `.artifacts/jev-audit/final-tests.txt`
- `.artifacts/jev-demo/summary.json`
- `.artifacts/jev-demo/*-fixture.json` and `*-decision.json`

## Before and after behavior

| Scenario | Baseline | New integration |
|---|---|---|
| Structured Jev judgment | No executable Jev path | Scoped prepare/run CLI with typed decisions |
| Context controls | No Jev packaging or limit enforcement | Named excerpts, hashes, role checks, two byte caps, run budget |
| Incomplete evidence | No Jev decision state | Explicit review/error; cannot silently pass |
| Provider response corruption | No provider adapter | Strict validation rejects malformed or mismatched replies |
| Replayed favorable result | No replay mechanism | Labeled observation, non-success gate exit |
| Known failed test | Existing tests remain authoritative | Failed declared check blocks before a provider call |
| Greptile completion | 5/5 and zero unresolved comments | Same requirement; optional Jev enforcement adds a separate condition |
| External actions | Existing skill-driven actions | New helper performs no push, merge, upload, or thread resolution |

## Live verification limitation

`TYPESAFE_API_KEY` was not present in the session environment. No paid or live Jev
request was made, and no repository context was sent to TypeSafe. HTTP contract
and error handling were tested with an in-process fake transport. The offline
fixture is not evidence that Jev will make the expected semantic judgments.

A maintainer still needs to supply a key, run a small approved plan against the
pinned model, and calibrate the questions on human-reviewed examples before
choosing enforcement. Shadow mode is the default. Hosted Greptile review was not
run because this was local-only work with no PR or push.

## Mac Mini portability follow-up

The execution-host setup adds seven host-doctor and synthetic-video tests.
All 77 targeted tests pass, including the original 70 Jev tests. Both shell
launchers pass Bash syntax validation. The read-only desktop doctor detects this
laptop's missing ASS filter and missing before/after browser tools. The synthetic
video smoke correctly fails against that insufficient FFmpeg build. No system
packages or browser tools were installed on the laptop by the setup scripts.

The separate Mini has not been connected or validated. A successful real video
smoke on a compatible FFmpeg build, GUI permissions, browser launch, agent login,
and live Jev call remain host acceptance checks. The setup guide lists them
explicitly; dependency detection never labels the host ready for unattended work.

## Optional Supercov integration, 2026-09-23

Supercov 1.2.0 ran Node tests on the laptop through the adapter. Branch coverage
rose from 50% to 100%; a deliberate failed assertion stayed failed at 100%.
Private evidence is in `.artifacts/supercov-acceptance-001/.artifacts/`.
Six synthetic live Jev requests completed with adverse-condition outputs
0.95/0.04, 0.98/0.04, and 0.94/0.05 for the matched pairs. Plans and responses
are in `.artifacts/calibration-v1/`; no real application source was transmitted.
The new stage cannot grant an enforced pass. This is development evidence, not
held-out calibration. See the integration guide for reproduction commands.

The focused gate, adapter, host-doctor, and launcher regression suite passed
98 tests. `git diff --check` passed. The original recorder suite was not rerun
for this change; its previously documented macOS failures remain unresolved.
