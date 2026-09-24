# Benchmark calibration and Supercov review

Reviewed 2026-09-22. Supercov source pinned at `891ce87d9bf915635de4a40461bb2bafddc60e0b`; factory implementation reviewed at `7159077`.

## Recommendation

Use independently verified buggy/fixed pairs and deliberately weakened tests to evaluate Jev. Add Supercov first as an optional source of measured coverage and assertion evidence. Keep its Jev quality assessments advisory until they have been calibrated for this factory.

This review inspected Supercov's quality transport, question catalog, scope selection, chunking, response validation, aggregation, and assertion-map documentation. It was a targeted integration review, not a complete security audit or execution test. No benchmark suite, Supercov binary, or live Jev request was run for this review.

## Suitable test repositories

| Resource | What it provides | Factory use |
|---|---|---|
| [SWT-Bench](https://github.com/logic-star-ai/swt-bench) | Repository-level test generation evaluated against buggy and fixed versions | Best direct fit for whether a proposed test actually reproduces the requested defect |
| [BugsInPy](https://github.com/soarsmu/BugsInPy) | Real Python defects and reproduction infrastructure | Smaller selected cases for Python test and evidence judgments |
| [Defects4J](https://github.com/rjust/defects4j) | Real Java defects, buggy/fixed revisions, and triggering tests | A later cross-language check of generalization |
| [StrykerJS](https://github.com/stryker-mutator/stryker-js) | Mutation testing for JavaScript and related languages | Introduce controlled faults and measure whether tests detect them in representative projects |

These resources do not label every factory judgment. A bug-fixing benchmark cannot independently establish whether a rollback plan is adequate, prose preserves a qualification, or an architecture follows this factory's rules. Those need separate maintained examples and human-reviewed labels.

Reproduce each selected case locally before accepting its label. A dependency failure, timeout, import failure, or unsupported platform is an environment result, not evidence that a test caught the intended bug. Exclude equivalent or invalid mutants from fault-detection labels after review.

Public benchmarks also have leakage and test-quality limitations. OpenAI's [review of SWE-bench Verified](https://openai.com/index/why-we-no-longer-evaluate-swe-bench-verified/) explains why public scores cannot simply be treated as capability estimates. Use public cases as one source and reserve fresh, private project cases for final validation.

## What Jev can determine

Jev can classify a candidate test against a supplied requirement, rate supplied alternatives, and flag a weakened assertion. A coding agent can propose actual input values such as empty strings, boundary integers, missing permissions, and malformed records. Executed tests, specifications, and independent reviewers establish the expected outcomes. Jev does not generate the test suite or define its own ground truth.

If “values” means decision thresholds, collect Jev outputs on labeled development cases and select thresholds with ordinary evaluation code. Freeze those thresholds before checking a separate held-out set. Our current 0.95 support probability and 0.90 confidence requirements are initial policy settings, not demonstrated accuracy. A model probability is not a measured probability that a software change is correct.

## Initial calibration design

Start with 20 reproducible defect families, each with four variants, for 80 cases:

1. A meaningful regression test that fails on the buggy version and passes on the fix.
2. A passing test whose important assertion is removed or weakened.
3. A passing test for an unrelated behavior.
4. A case with missing or stale evidence that should require review.

Use 12 families for development and eight for a held-out pilot. Keep all variants of a family in the same split. Later hold out whole projects to measure transfer. Eight held-out families are a pilot, not enough to claim a low production false-pass rate.

For each case retain: case and family ID; repository and exact revisions; license/source reference; requirement; test patch; expected observation; actual buggy/fixed outcomes; evidence hashes; question-specific labels and their basis; reviewer; split; model, question, packaging and policy versions; raw validated response; final route; cost and latency.

Keep oracle labels, gold solutions, filenames that reveal labels, and held-out answers outside the Jev request. Package only the requirement, relevant source and assertions, and the observations appropriate to the checkpoint. A test-plan judgment should not receive the later execution result. Evidence judgments may receive those results, without receiving the evaluator's label.

Report separately by question and defect family:

- Unsafe passes divided by known-bad cases.
- False blocks divided by known-good cases.
- Review/abstention rate, provider errors, and incomplete packaging.
- Detection of removed assertions, irrelevant tests, and stale evidence.
- Coverage and mutation results as independent execution measurements.

Do not report one blended accuracy number that hides unsafe passes. Count correlated variants by family when estimating uncertainty. As an illustration, zero false passes in 300 independent bad cases gives an approximately 1% one-sided 95% upper bound; 300 closely related variants do not provide that evidence.

Run the pinned model in shadow mode first. Keep the existing deterministic checks and Greptile requirements. Review counterexamples before changing the rubric, then version the changes and use a fresh holdout after repeated tuning.

## Supercov findings and proposed treatment

Source links below are pinned to the reviewed commit.

| Finding | Existing factory | Treatment |
|---|---|---|
| [Quality catalog](https://github.com/supercorp-ai/supercov/blob/891ce87d9bf915635de4a40461bb2bafddc60e0b/crates/supercov-cli/src/quality/catalog.rs) asks atomic smell questions and compares changes | Factory asks workflow-specific questions but has no general smell catalog | Optional advisory diagnostics; do not replace architecture rules with a health average |
| [Change risks](https://github.com/supercorp-ai/supercov/blob/891ce87d9bf915635de4a40461bb2bafddc60e0b/crates/supercov-cli/src/quality/risks.json) include weakened tests, injection, embedded credentials, auth changes, migrations, and debug remnants | Broad risk questions exist; explicit test weakening and injection questions are missing | Prioritize these in the next calibrated question revision; retain static checks and execution proof |
| [Coverage workflow](https://github.com/supercorp-ai/supercov/blob/891ce87d9bf915635de4a40461bb2bafddc60e0b/README.md) records coverage gaps and before/after differences | Factory accepts hashed result excerpts but does not collect structured coverage | Highest-value first integration: an optional, pinned Supercov evidence adapter |
| [Assertion maps](https://github.com/supercorp-ai/supercov/blob/891ce87d9bf915635de4a40461bb2bafddc60e0b/docs/assertion-maps.md) connect assertions to source, track dependencies and freshness | Factory binds evidence to revisions, but has no assertion-flow map | Import run IDs, source bindings, observed assertion evidence, and unresolved map questions |
| [Assertion evidence](https://github.com/supercorp-ai/supercov/blob/891ce87d9bf915635de4a40461bb2bafddc60e0b/docs/assertion-evidence.md) separates execution credit from agent explanations | Current test-observation question is coarse | Add per-assertion semantic review later; never equate an agent-authored map with independent proof |
| [Quality transport](https://github.com/supercorp-ai/supercov/blob/891ce87d9bf915635de4a40461bb2bafddc60e0b/crates/supercov-cli/src/quality.rs) caches exact requests and partitions large files at declarations | Factory uses explicit selected line ranges and no live-response cache | Consider parser-assisted manifest preparation; preserve source hashes, full unit inventory, and review on missing dependencies |
| Same transport estimates tokens at three bytes per token | Factory uses much smaller conservative serialized-byte budgets | Keep factory limits; neither method is an authoritative tokenizer. Supercov calls would need their own disclosure and budget checks |
| Transport allows independently rounded probability distributions | Factory currently requires distribution sums within 0.0001 | Investigate in the first synthetic live compatibility test; do not silently normalize or weaken schema validation based only on another project's observation |
| Catalog includes empirical threshold and prompt-shape observations | Factory has routing tests and synthetic replays, not live calibration | Adopt their practice of matched positive/negative examples and packaging experiments; independently reproduce rather than inherit their thresholds |

Supercov's `0.60` presence threshold controls which smells it displays. Its health number averages adverse probabilities; repository health weights by source size. Those are prioritization choices, not release safety thresholds. Its reported calibration observations are project-authored evidence, not independently reproduced results from this review.

The source also reports that adding metadata around a before/after pair changed detection. Our packaging includes role-tagged sources and hashes for auditability. Test that exact representation rather than assuming calibration transfers from a simpler prompt.

## Proposed integration boundary

The controller runs the project's trusted full test command through a pinned Supercov release and records the actual exit status. The adapter validates the report schema and binds it to the command, run ID, source revision, configuration, and report hash. Unsupported measurement remains unknown; zero detected gaps does not imply complete measurement.

Pass selected coverage gaps, assertion expressions, relevant source, and primary execution evidence to the factory's test-plan or evidence checkpoint. Preserve provenance and omit secrets and unrelated source. Let the coding agent propose a focused test, execute it, then compare measured results. Preserve the original complete-suite result separately.

Use Supercov quality assessment as an optional separate diagnostic. Its direct TypeSafe calls bypass our gate's prepared-plan approval hash and byte budgets, so do not present installing Supercov as automatically inheriting those controls. A poor health score or smell signal can create review work; a good score cannot waive a defect, failed test, or required review.

## Mac Mini implications

Supercov's packaging scripts include macOS ARM and Intel targets, but a released binary and its instrumentation must still be smoke-tested with the target project's actual test command. No Supercov installation or compatibility claim has been made for the Mini.

SWT-Bench recommends x86_64, Docker, substantial storage and memory; ARM64 support is experimental. Start with a small verified subset at one worker on an Apple Silicon Mini. Keep benchmark runtime checks optional and separate from the factory's existing headless/desktop checks. Do not make Docker, Java, or the entire benchmark dataset mandatory for every factory installation.

## Status

Completed: source review, benchmark selection, gap analysis, calibration design, and integration boundary.

Not implemented in this review: Supercov adapter, new question catalog, benchmark runner, threshold changes, or live probability compatibility fix. These require execution evidence and versioned fixtures. The existing factory remains unchanged at runtime and in shadow mode by default. Nothing was pushed upstream.
