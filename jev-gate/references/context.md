# Grounded context and bounded requests

The request service never walks the repository to build model context. A manifest
names every file and inclusive line range. The service loads only those text
sources, verifies their full-file hashes, and sends only the chosen excerpts.
Each excerpt carries its path, role, range, hash, and primary/summary label.
The check-evidence files are validated locally and are not automatically sent.

## Limits

| Budget | Enforced local limit |
|---|---|
| State plus longest serialized question | 16,000 ASCII JSON bytes |
| Whole serialized request including all questions and framing | 32,000 ASCII JSON bytes |
| Semantic units / requests per run | 64 |
| Total original request bytes per run | 512,000 |
| File loaded for excerpt selection | 1,000,000 bytes |
| Source references per unit | 30 |
| Attempts per request | 3, only for 429 or 529 |
| Response body per call | 1,000,000 bytes |
| HTTP timeout | 20 seconds per attempt |

Serialization escapes Unicode. This counts encoded structure, instructions,
criteria, and text rather than using the unsafe English characters/4 estimate.
It also makes CJK and emoji consume more of the byte budget. The local limits
leave substantial space below the vendor's 32k/64k token limits. They are an
engineering precaution, not an exact tokenizer or a mathematical guarantee about
undocumented provider serialization. `token_count` remains null in the plan.
Do not raise these caps by assuming one character equals one token. If TypeSafe
publishes a tokenizer, add exact counting for both limits with framing reserve,
then regression-test multilingual and code-heavy inputs before raising budgets.

TypeSafe input rejection fails closed. The service never truncates or retries an
oversized request with missing evidence. Reported total input usage above 64,000
also invalidates the result. The API does not expose per-question token usage;
we cannot verify that measurement independently after a call.

## Semantic chunks

A chunk is a manifest unit, not a fixed slice of characters. For example, one
requirement, its relevant caller and service function, one test, and its observed
result form a useful unit. Each unit gets its own state and the phase's questions.
All questions for that unit are batched in one request. Unrelated units do not
share context. Shared context may be repeated across units when needed to keep
the judgments grounded.

When a unit is too large:

1. Remove unrelated logs, boilerplate, generated files, lockfiles, and history.
2. Split at requirement, function, finding, or test-case boundaries. Keep each
   condition's supporting and contradicting evidence together.
3. Add a separate cross-boundary unit with the relevant caller/callee contracts
   when the split could hide an interaction. Mark all affected units incomplete
   until that interaction is checked.
4. Preserve the complete expected-unit inventory. If a run needs more than 64
   units or 512,000 bytes, the caller must track the complete set of sub-runs and
   take the worst result across them. There is no built-in cross-run aggregator;
   do not call one passing sub-run a complete factory audit.
5. If necessary, use a generative model or a person to write a shorter summary.
   Save it as a separate local file, mark `kind: summary`, and record its original
   source hashes and ranges in that file. Summary-bearing units always require
   review, even if Jev is confident. A summary cannot upgrade an omitted primary
   record into release evidence. Rebuild a primary-evidence unit to obtain a pass.

There is no automatic lossy summarizer. Oversized units stop with a structured
error so the caller can re-scope them deliberately. There is no voting or averaging
across chunks. A single blocked unit blocks the run; a single unresolved unit
requires review. Diagnostic Scores never offset blockers.

## Freshness and coverage

A manifest binds HEAD and the hash of the tracked working diff, including staged
and unstaged changes relative to HEAD. Every selected file has a full SHA-256
hash, which also covers selected untracked or ignored evidence files. The service
checks these bindings before each request and after the run. Changes during a
call invalidate the run. It does not detect changes to unrelated untracked files;
those must enter the reviewed manifest or be committed before release auditing.
Rebuild after a rebase, new review cycle, source change, or test rerun.

`expected_units` must exactly match unique unit IDs. `required_checks` must exactly
match unique check IDs, and each check needs a matching revision and readable
hashed evidence. A workflow maintainer chooses these inventories before evaluation.
They must include every applicable acceptance condition, affected interface,
review finding, and known risk. This is a trust boundary: Jev and this runner cannot
prove that a caller omitted nothing or that a recorded test was actually executed.
Keep test/check collection under the trusted CI or operator's control. Merely
editing a check's `status` field is not verification.

The source-role requirements are structural checks, not authentication of facts.
An agent-written claim labeled primary does not become independent evidence.
A person or trusted harness must verify evidence origin, scenario, and revision.
For release work, use a committed revision and a complete test/CI record.

## Data and adversarial text

Source paths must be relative regular files in the repo. Symlinks, path traversal,
common credential paths, and known binary formats are rejected. Selected excerpts
are screened for common secret patterns. This is not a complete secret or PII
scanner; inspect the prepared plan and use reviewed redacted extracts where needed.
The exact prepared plan hash is required for live calls so a changed payload
cannot silently reuse an earlier disclosure decision.

Jev receives source text as evidence, with explicit instructions to ignore embedded
commands. That reduces ambiguity but is not a security boundary. Adversarial
findings, comments, and prose can still influence judgments. Use a trusted copy of
the runner and policy when evaluating untrusted branches; never execute a PR's
modified gate as the authority over that same PR. Authorization and hard security
checks remain deterministic and outside the model.

Media remains local or on the existing evidence host. Give Jev text observations
and caveats only. A screenshot path, URL, or caption does not mean Jev saw the image.
A vision-capable reviewer or person must still inspect the actual media.
