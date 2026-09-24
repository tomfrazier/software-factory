# Research comparison and editorial examples

Reviewed 2026-09-24 against [Graphite's AI Tells](https://graphite.io/five-percent/research/ai-tells).

The study concerns web articles generated with a fixed prompt. Patterns vary by
model and version; individual tells cannot establish authorship. Its punctuation
findings do not support a universal em-dash ban. Treat these as editing leads,
not a detector or universal frequency targets.

## Comparison with the existing skill

| Existing capability | Decision in this update |
|---|---|
| Puffery, jargon, excessive adverbs | Keep; add a direct check for unsupported evaluation |
| One contrast formula | Broaden the framing check; preserve useful distinctions |
| Varying rhythm and avoiding synonym cycling | Keep; do not manufacture irregularity or replace exact terms |
| Filler and generic conclusions | Extend to repeated transitions and announcements of importance |
| No explicit tradeoff check | Add a check for promises that suppress a cost or limitation |
| Blanket punctuation ban | Replace with readability guidance and explicit house-style precedence |
| Encouragement to add personality | Preserve voice without invented experience or opinions |
| Jev fidelity audit | Keep optional; do not convert it into authorship detection |

Do not import a model-specific blacklist or scoring formula. The article does
not validate our technical-writing workflow or Jev thresholds. No detector,
new API call, or automatic replacement script was added.

## Original review cases

These examples were written for this repository. They are manual acceptance
cases, not measured evidence that the skill improves every model's writing.

| Input and context | Acceptable edit or decision |
|---|---|
| "The release is incredibly dependable." No reliability results supplied. | Remove the unsupported claim or request its evidence; never invent uptime. |
| "Caching cuts latency without adding any operational burden." The supplied design requires invalidation. | "Caching cuts latency and requires invalidation." Preserve the actual cost. |
| "This distinction is essential. An expired token receives HTTP 401." | "An expired token receives HTTP 401." The consequence carries the point. |
| "Furthermore, the job retries. Additionally, it records the attempt." | "The job retries and records the attempt." |
| "This is not a production deployment; it is a dry run." | Keep the distinction. It prevents an operational misunderstanding. |
| "The estimate may change after profiling." | Keep the uncertainty. No confirmed measurement was supplied. |
| "The worker pauses (up to five seconds) before retrying." | Keep the bounded timing and readable aside unless house style requires a rewrite. |
| "The parser returns a token. The token contains an offset." | Keep the precise repeated term. |
| A quoted sentence, code sample, or documented CLI flag contains a listed tell. | Preserve the literal content. Edit surrounding explanation if needed. |
| An incident report contains no personal anecdote. | Do not invent one or make the report conversational merely to imitate a person. |

## Validation boundary

Check frontmatter and relative links, review the diff, and walk through the
cases above. No wording-matching unit test can establish editorial quality.
Changing this reference should not silently change the Jev question catalog,
thresholds, or deployment behavior.
