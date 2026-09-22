# Running and adopting the gate

From this repository, use Python 3.10 or newer:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r jev-gate/requirements.txt
.venv/bin/python jev-gate/examples/demo.py --out .artifacts/jev-demo
```

On Windows, use `.venv\Scripts\python.exe`. The demo creates an isolated fixture
repo and shows pass, review, and blocked outcomes using labeled synthetic responses.
It makes no provider calls and never authorizes workflow continuation.

For real work, keep the gate installed in a trusted location and supply `--repo`
for the project under review. Prepare a manifest following the schema and context
reference. `snapshot` prints its required revision object. Hash each full source
file with SHA-256; `start` and `end` are inclusive 1-based line numbers. A complete
working manifest is created by the demo and can be used as a shape example.

```bash
.venv/bin/python jev-gate/scripts/jev_gate.py snapshot --repo /path/to/project
.venv/bin/python jev-gate/scripts/jev_gate.py prepare /path/to/manifest.json \
  --repo /path/to/project --out .artifacts/plan-001.json
```

Inspect the exact `requests` in the plan, including every excerpt and the budget
report. `prepare` prints a SHA-256 for that plan. When disclosure to TypeSafe is
already authorized, put your key in the process environment and run:

```bash
.venv/bin/python jev-gate/scripts/jev_gate.py run /path/to/manifest.json \
  --repo /path/to/project --out .artifacts/decision-001.json \
  --live --approved-plan-sha256 <hash-from-prepare>
```

The default is `--mode shadow`. It produces observations and leaves existing
workflow gates in charge. Passing `--mode enforce` is a deliberate project-policy
choice after calibration. It adds Jev as a required checkpoint, without replacing
other checks. A live, enforced pass returns 0 and `workflow_action: continue`.
That means continue to the next workflow check, never automatically ship or merge.

Exit code 2 means error; 3 means review, blocked, shadow, or replay. Check the JSON
fields to distinguish them. In shadow mode a caller may explicitly continue its
existing workflow after recording the observation; it must not label that run an
enforced Jev pass. In enforce mode missing credentials or provider failure stops
the checkpoint. The CLI refuses to overwrite prior output files.

For CI, run `run --mode enforce` as a named required job only after adoption. Do
not use `prepare` as the required gate job. Supply check evidence from the trusted
CI controller rather than letting the change under review claim its own tests
passed. There is no repository-host CI adapter bundled here. This repo is a skill
collection, so wiring job permissions and branch protection belongs to the adopting
project. GitLab and Perforce skill hooks use the same semantic questions, but this
runner's revision binding currently supports Git only; Perforce must use manual
advisory evaluation until a shelf-digest adapter is implemented.

## Policy version 1.0.0

| Signal | Pass | Block | Review |
|---|---|---|---|
| Choice support | `adequate`, selected probability >= 0.95 and confidence >= 0.90 | `inadequate` at those same thresholds | All other outcomes, including confident `unknown` |
| Noul adverse condition | <= 0.05 | >= 0.90 | Between those values |
| Score priority | Never changes readiness | Never changes readiness | Diagnostic only |
| Required deterministic checks | All passed, bound to current revision | Any failed | Any unknown |
| Coverage, summaries, risk | Complete primary evidence, standard risk | Other blockers still apply | Incomplete unit, any summary, or high risk |

Aggregation takes the strongest non-pass outcome: error, blocked, review, pass.
No average or majority vote can erase a blocker. Choice confidence is distinct
from option probability; neither guarantees truth. Greptile's 5/5 score is not
converted into a Jev probability.

Provider calls are serial. Only 429 and 529 receive up to two retries after the
initial request, with backoff and bounded numeric Retry-After handling. Longer
or date-form Retry-After values stop for a later rerun. Authentication, validation,
context rejection, redirect, malformed JSON, and transport failure do not yield a
judgment. Redirects are disabled to keep the Bearer credential at the fixed endpoint.
HTTP error bodies are not echoed. Worst-case retries can triple input volume;
64 units means at most 192 attempts, not unlimited polling.

## Calibration before enforcement

Thresholds are initial policy values, not measured software-factory accuracy.
Build a held-out set of real units labeled by maintainers, including defects,
missing evidence, conflicting logs, injected instructions, high-risk operations,
non-English text, and large-context boundary cases. Run the pinned model in shadow
mode. Record false passes, false blocks, review frequency, and cost by checkpoint.
Set an acceptable false-pass rate for the project, review every false pass, and
change questions or thresholds on a development set. Check the held-out set again
before enabling enforcement. Keep a separate human decision column and retain
counterexamples. Unit tests prove routing behavior, not model accuracy.

Never calibrate by asking Jev to endorse its own previous answers. Repeated calls
to the same model are not independent votes. Recheck calibration when model,
questions, packaging, or policy changes. Restore shadow mode if behavior drifts.

## Record and retention

A plan contains the exact outgoing text. A decision contains model version,
manifest and plan hashes, question answers, response usage, unit routes, and
versioned policy identifiers. Preserve the matching manifest and plan beside it
when auditability is required. These are local private files, created with mode
0600 on POSIX; `.artifacts/` is ignored by Git. The runner does not upload reports,
edit PRs, resolve comments, execute model-selected commands, or modify code.
Choose retention and redaction according to the adopting project's data policy.
