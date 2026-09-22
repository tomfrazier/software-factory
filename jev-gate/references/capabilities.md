# Verified TypeSafe contract

Verified on 2026-09-22 from docs linked by [TypeSafe](https://typesafe.ai/).
Unrelated sites using Jev or TypeSafe in their domain names were not used as authority.

| Fact | Verified value | Source |
|---|---|---|
| Pinned model | `jev-1.13.0` | [Models](https://docs.typesafe.ai/models) |
| Total context | 64k tokens per request, state plus all questions | [Models](https://docs.typesafe.ai/models) |
| Per-question context | 32k tokens, state plus longest question | [Models](https://docs.typesafe.ai/models) |
| Input | Text; no image, audio, or video understanding | [State](https://docs.typesafe.ai/concepts/state) |
| Endpoint | `POST https://api.typesafe.ai/v1/systemone`, Bearer authentication | [API](https://docs.typesafe.ai/api) |
| Questions | Map of IDs to Choice, Score, or Noul definitions | [Primitives](https://docs.typesafe.ai/primitives) |
| Choice | Options map, at most 255 options | [API](https://docs.typesafe.ai/api) |
| Score | Ordered rubric, 2 to 10 levels; fractional weighted result | [API](https://docs.typesafe.ai/api) |
| Noul | Probability of yes; no separate confidence | [Primitives](https://docs.typesafe.ai/primitives) |
| Confidence | Choice/Score distribution statistic; not probability of correctness | [Confidence](https://docs.typesafe.ai/confidence) |
| Response | Model, answers by question ID, token usage | [API](https://docs.typesafe.ai/api) |
| Retry signals | 429 and 529 require backoff | [API](https://docs.typesafe.ai/api) |

The published rate limits were 250,000 tokens/second and 1,200 requests/minute,
with an explicit notice that these can change. This client serializes requests
and bounds retries rather than treating published rates as guaranteed capacity.
Aliases can move; changing the pinned version requires a contract review and new
calibration. [Models](https://docs.typesafe.ai/models)

Questions in one request independently see the same state. They do not see one
another's answers. A dependent question needs a later request with the needed
result supplied explicitly. This integration has no hidden chained judgments.
[Primitives](https://docs.typesafe.ai/primitives)

Numeric checks, dates, counts, identity, complex reasoning, and generation stay
outside Jev. Irrelevant context and adversarial text can harm judgment. Precise
conditions and source references help, but cannot make injected instructions or
confident mistakes impossible. [Known limitations](https://docs.typesafe.ai/model-jaggedness/jev-1.13)

No official tokenizer or preflight token-count endpoint was found in the official
documentation index or the linked SDK references inspected for this integration.
The local limits are therefore **byte caps, not verified token counts**. See
[context enforcement](context.md) for the conservative limits and remaining limit.
The provider remains the authority on actual token acceptance.
