# Jev integration audit

Audited on 2026-09-22. Source repository:
https://github.com/michaelshimeles/skills

Baseline commit: `4b72f46b045e6fef52e6a98d4c162dd309826aed`.
Local clone: `/Users/tomfrazier/Downloads/skills-jev`.
Implementation worktree: `/Users/tomfrazier/Downloads/skills-jev/.worktrees/jev-audit-0922`.
Branch: `agent/jev-audit-0922`. No upstream push, PR, merge, or hosted review was requested.

## Result

Jev now has a runnable, optional audit layer with 25 versioned questions across
nine checkpoints. The implementation includes context manifests, source hashes
and line ranges, explicit coverage inventories, request and decision schemas,
conservative input budgets, TypeSafe HTTP transport, fail-closed validation,
threshold routing, and a reproducible offline demo. All seven existing skills
have contextual hooks; `AGENTS.md` and `README.md` describe how to adopt them.

Keep Greptile. Jev is useful for asking whether a specific claim is supported,
whether a test observes its requirement, or whether a small extraction keeps
policy at the action boundary. It is a poor replacement for discovering subtle
bugs, reasoning through a large architecture, inspecting media, or explaining a
fix. The implemented gate therefore adds evidence-aware judgments without
weakening the existing Greptile 5/5 and zero-unresolved requirement.

The prior conversation's idea of replacing the Greptile completion criterion was
not adopted. Doing that without measured performance would trade one unvalidated
summary score for another. Jev also is not treated as an independent voting panel.
Repeated calls to one model do not establish independent agreement.

## Capability findings

The user's approximate 64k limit was only half the constraint. TypeSafe publishes
64k tokens for the complete request and 32k for state plus the longest question.
The current documented model is `jev-1.13.0`, which this implementation pins.
Jev accepts text and returns Choice, Score, and Noul answers. It cannot examine
screenshots or recordings. Details and source links are in
[verified capabilities](../jev-gate/references/capabilities.md).

No verified public tokenizer was found. The code enforces 16,000 ASCII JSON bytes
for state plus the longest question and 32,000 for the whole request, with a
512,000-byte run budget. These deliberately small operational caps account for
text, questions, criteria, and JSON framing. They are not claimed exact token
counts. Provider rejection stops the run; nothing silently truncates context.
The provider's per-question token accounting remains unobservable to this client.
See [context controls](../jev-gate/references/context.md).

## Audit method and scope

The audit covered all 25 tracked baseline files, including seven skill entrypoints,
the workflow template, README, recorder, screenshot/upload scripts, platform API
references, tests, ignores, and license files. The
[baseline inventory](jev-baseline-inventory.json) records paths, byte lengths,
line counts, and SHA-256 hashes. No application code, CI workflow, or deployment
service exists in this collection. Its integration points are skill instructions
and executable helpers, not an already-running factory scheduler.

The remote had two open PRs at inspection. PR 15 touches README; PR 10 proposes
review-freshness and workflow changes across several of the same skills. This
implementation uses an isolated local worktree from baseline `main`, does not
incorporate either pending PR, and does not change anyone else's branch. Reconcile
those upstream changes before any future publication of this local integration.

## Candidate insertion points

"Implemented" below means either an executable catalog condition and its skill
hook, or a named deterministic check in the new runner. A skill hook is a workflow
instruction, not an automatic interception of another program's actions.

| Existing location / decision | Candidate value from Jev | Disposition and reason |
|---|---|---|
| `AGENTS.md`, handoff between beats | Judge scoped evidence before continuing | Implemented as opt-in phase hooks and a shared CLI; shadow first |
| `new-feature`, request interpretation | Is the acceptance outcome observable? | Implemented: `acceptance_clear` |
| `new-feature`, proposed task scope | Does the plan stay within the request? | Implemented: `scope_faithful` |
| `new-feature`, concurrent ownership | Do known plans conflict semantically? | Implemented: `ownership_conflict`; exact file overlap remains a direct check |
| `new-feature`, fetch/name/worktree creation | Choose branch names, confirm identity | Deliberately deterministic; no model needed |
| `new-feature`, ports and shared databases | Confirm process ownership and isolation | Deliberately deterministic; Jev cannot authenticate a process or authorize DB work |
| `new-feature`, cleanup and lockfiles | Decide safe deletion or conflict repair | Kept with Git, package manager, and the operator; no automated deletion judgment |
| `code-structure`, domain-policy placement | Is policy still at the action boundary? | Implemented: `policy_in_action`, on the supplied rule and code |
| `code-structure`, reusable contract | Are inputs and failures explicit? | Implemented: `service_contract` |
| `code-structure`, extraction trigger | Are mechanics shared by real callers? | Implemented: `extraction_justified`; one-off code is outside this phase |
| `code-structure`, migration order | Which caller should be migrated next? | Deferred; benefit depends on application-specific dependency data |
| `code-structure`, complex architectural correctness | Find hidden interactions across an entire codebase | Left with generative review, static checks, and tests; too much reasoning/indirection |
| `evidence-driven-testing`, test planning | Does the test observe the acceptance behavior? | Implemented: `test_observes_requirement` |
| Same, negative-case coverage | Does the stated boundary case have a test? | Implemented: `negative_case_present`; measured coverage stays in test tooling |
| Same, test priority | Rank impact of a broken behavior | Implemented: `test_priority` Score, diagnostic only |
| Same, assertion-to-result link | Does an observation support the acceptance condition? | Implemented: `assertion_supported`; claimed pass alone is not evidence |
| Same, failure and caveat reporting | Are untested cases disclosed in the claim? | Implemented: `caveats_disclosed`; failed checks also block deterministically |
| Recorder `doctor`, source choice, FFmpeg checks | Judge whether recording can run | No Jev call; these are executable capability checks |
| Recorder process identity, locking, supervision | Judge whether stopping a process is safe | No Jev call; preserve exact identity checks and race protections |
| Recorder annotations, counts, timestamps, file integrity | Check validity and finalization | No model arithmetic or attestation; retained recorder and test mechanics |
| `before-and-after`, scenario comparison | Do written records describe a comparable pair? | Implemented: `pair_comparable` on text records |
| Same, actual pixels, layout, playback | Judge screenshot/video visual correctness | Not implemented in Jev; retain actual visual inspection |
| Capture and upload helpers | Choose destination or approve protected/public upload | No Jev authority; existing tools and permission rules remain |
| `greploop`, review provenance | Is the review current and from the expected bot? | Explicit direct-check guidance; no semantic model for identity or SHA comparison |
| Both Greptile loops, finding triage | Is the finding supported by code excerpts? | Implemented: `finding_supported`; false-positive disposition requires source review |
| Both loops, post-fix audit | Does the change address the reported defect? | Implemented: `fix_addresses_finding`; tests and fresh review still required |
| Both loops, repeated findings | Is the same unresolved defect recurring? | Implemented: `review_repetition`; stops for investigation rather than dismissing it |
| Both loops, fix generation and explanation | Write the fix and explain why | Retained generative agent role |
| Both loops, score and unresolved count | Replace 5/5 with model confidence | Deliberately not implemented; different quantities with no validated equivalence |
| Both loops, thread resolution / push / retry | Take external actions from the judgment | Not implemented; existing bounded workflow and authorization apply |
| Greptile platform reference files | Fetch paginated reviews, threads, metadata | Retained as API mechanics; no provider calls inserted into reads |
| `AGENTS.md` / PR completion claims | Does a claim follow from the result? | Implemented: `claim_supported`, `scope_complete`, one acceptance condition per unit |
| Release handoff | Is a relevant recovery action described? | Implemented: `rollback_described`; does not prove rollback succeeds |
| Trust-boundary changes | Spot a weakened explicit rule | Implemented: `trust_boundary_change`, triage only; high risk always needs review |
| Irreversible operations | Recognize destructive intent | Implemented: `destructive_change`; does not authorize the action |
| Output/data handling | Recognize a prohibited disclosure in a described change | Implemented: `sensitive_disclosure`; not a complete secret/PII scanner |
| `unslop`, edited meaning | Preserve facts and qualifications | Implemented: `meaning_preserved`, `claim_inflation` |
| `unslop`, clarity | Check a supplied writing rule | Implemented: `text_clear`; actual writing stays generative |
| All checkpoints, context quality | Is primary evidence sufficient? | Implemented: `context_sufficient` plus deterministic source/role/coverage checks |
| Test suite | Use Jev as assertion oracle | Not implemented; tests exercise deterministic policy and mocked provider contracts |
| Licenses and `.gitignore` | Interpret ownership or tracked artifacts | No semantic gate; licenses retained, local artifacts/worktrees ignored |

## Implementation by file family

- `jev-gate/scripts/catalog.py` defines the 25 conditions, required source roles,
  typed provider questions, and catalog version. `references/questions.json` is
  a tested machine-readable snapshot.
- `service.py` owns file/range validation, source hashes, revision checks,
  explicit packaging, byte limits, privacy screening, HTTP mechanics, and strict
  answer validation. It rejects unsupported model versions and incomplete replies.
- `policy.py` owns the thresholds and aggregation. Choice support needs probability
  at least 0.95 and confidence at least 0.90. Risk Noul values pass at or below
  0.05, block at or above 0.90, and otherwise require review. These are conservative
  initial values, not calibrated software-factory accuracy.
- `jev_gate.py` orchestrates snapshot, preparation, live execution, and replay.
  It requires the inspected plan hash for live calls and checks sources again
  before each request and after the run. Only a live enforced pass can return
  success from the run command. It executes no model-selected operations.
- `schemas/` specifies local manifest, request, replay, and decision structures.
  Dynamic probability keys and weighted Score consistency are checked in code.
- `references/` explains capabilities, context, phase selection, operational
  commands, failure handling, and calibration before enforcement.
- `examples/demo.py` builds an isolated Git fixture and produces three synthetic
  outcomes. `tests/test_jev_gate.py` covers the executable contract and guardrails.
- Existing workflow and skill files add narrow, optional hooks. The recorder,
  capture/upload scripts, API reference implementations, licenses, and original
  recorder tests retain their baseline contents.

## Grounding and enforcement boundaries

A run evaluates its declared units, not every possible property of the repository.
The caller must choose complete acceptance, finding, and risk inventories. The
runner validates that the declared inventory is fully present and checks its
source hashes; it cannot establish that the caller selected all relevant facts.
Likewise, hashed test output does not authenticate that a test ran. Trusted CI or
the operator must collect and verify that evidence.

There is no blind repository upload or automatic lossy compression. Each unit
contains only its selected excerpts. Oversized units fail before network use;
split them by behavior with relevant caller/callee context and cross-boundary
checks. Summary-bearing units require review even if their answers look certain.
Any failed or unresolved chunk prevents a run-wide pass. Separate large sub-runs
need caller-controlled complete aggregation; no built-in cross-run gate is claimed.

Prompt-injection instructions in source text remain untrusted evidence. Precise
questions reduce confusion but do not guarantee robustness. Use trusted gate code
and policy, retain deterministic controls, and include adversarial examples in
calibration. Risk classification is supplementary; critical auth, data-loss, and
publishing decisions never become model-authorized actions.

The runner currently has Git revision support. GitLab repositories can use it;
Perforce workflow guidance can use the question map manually, but automated
shelf-digest binding is explicitly deferred. No hosted CI or branch-protection
integration is installed because the source repo supplies neither a factory
controller nor a project-specific check inventory.

## Deliberately deferred

- Replacing Greptile, the builder, or the visual reviewer.
- Repository-wide autonomous approval, merge, push, publication, or thread closure.
- Exact token accounting until TypeSafe publishes a verifiable tokenizer/count API.
- Automated summarization or token-boundary chunking that could drop a contradiction.
- Automatic waiver of supposedly irrelevant phase conditions. Current phase bundles
  have explicit applicability; finer per-question profiles need a reviewed inventory.
- Live model-quality claims, automatic threshold optimization, and false-pass-rate
  guarantees. Offline unit tests do not establish Jev accuracy.
- Application-specific CI check collectors, Perforce shelf adapters, persistent
  multi-run orchestration, and branch-protection setup.

These are bounded extension points, not silent fallbacks. In enforcement mode,
unavailable evidence or API service produces a non-pass. Shadow mode leaves the
original workflow in charge and records only an observation.

## Validation

See [validation record](jev-validation.md) for commands, counts, baseline failures,
offline demonstration outcomes, and the live-call limitation. No evidence was
published externally. The included synthetic responses test the adapter and policy;
they are explicitly labeled and must not be represented as live Jev judgments.

## Benchmark and Supercov follow-up

The [benchmark calibration and Supercov review](jev-benchmarks-supercov-review.md)
records the 2026-09-22 source comparison, missing coverage and assertion-map
adapters, and a proposed independent calibration corpus. This follow-up is a
review and design; it does not enable Supercov or change runtime thresholds.

## Supercov implementation follow-up, 2026-09-23

The [optional adapter and calibration guide](supercov-integration.md) supersedes
the previous follow-up's not-implemented status for evidence collection and three
change-risk questions. It records real Supercov smoke results and six live
synthetic Jev observations. Broader held-out calibration, automated assertion
flow authoring, parser-assisted context selection, and caching remain deferred.
