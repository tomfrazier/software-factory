# Question map

The executable source is `scripts/catalog.py`. `questions.json` is its inspectable
snapshot; tests keep them aligned. Version 1.0.0 has 25 questions across eight
checkpoints. Every unit also receives `context_sufficient` as a Choice question.

| Checkpoint and unit | Choice conditions | Noul risk flags | Score | Primary source roles |
|---|---|---|---|---|
| `intake`: one planned acceptance outcome | `acceptance_clear`, `scope_faithful` | `ownership_conflict` | None | requirement, plan, ownership |
| `architecture`: one proposed shared-service extraction | `policy_in_action`, `service_contract`, `extraction_justified` | None | None | implementation, rule, plan |
| `test-plan`: one behavior with a specified failure/boundary case | `test_observes_requirement`, `negative_case_present` | None | `test_priority` | requirement, test |
| `evidence`: one observed before/after scenario and proposed claim | `assertion_supported`, `pair_comparable`, `caveats_disclosed` | None | None | requirement, result, before, after, claim |
| `review`: one finding and its proposed fix, with cycle history | `finding_supported`, `fix_addresses_finding` | `review_repetition` | None | finding, implementation, before, after, history |
| `ship`: one acceptance claim with a relevant recovery rule | `claim_supported`, `scope_complete`, `rollback_described` | None | None | claim, result, requirement, plan, rule |
| `prose`: one edited passage | `meaning_preserved`, `text_clear` | `claim_inflation` | None | before, after, rule |
| `risk`: one changed trust boundary or external operation | None | `trust_boundary_change`, `destructive_change`, `sensitive_disclosure` | None | before, after, rule, implementation, plan |

Roles are names for excerpts, not instructions to send whole files. One file may
supply several different ranges. All listed roles are required in that phase.
Use the phase only when its complete bundle of conditions applies. For example,
architecture here audits an extraction with shared callers; it is not a gate on
every one-off function. The release phase needs a concrete recovery rule; if a
project judges rollback irrelevant, record that applicability decision outside the
run rather than manufacturing a rollback plan. More flexible per-question profiles
are a future extension and must retain reviewed coverage inventories.

Every Choice uses `adequate`, `inadequate`, and `unknown`. Adequate means primary
evidence directly supports the exact condition. Inadequate means it contradicts
it. Unknown covers missing, ambiguous, conflicting, summary-only, or reasoning-heavy
evidence. These states are intentionally different from "test passed".

All Noul conditions are adverse predicates. Low probability is favorable only
when the separate context question passes. A probability of 0.5 is uncertainty,
not medium severity. `test_priority` is an impact diagnostic on levels 0 through 2;
it is never permission to skip a test or a readiness signal.

A finding that appears unsupported goes back to a reviewer with its source
excerpts. It is not automatically dismissed. Likewise, repetition signals a stuck
loop; it does not prove the finding is false. Every condition is independently
judged, then the local policy combines the outcomes. No question depends on a
sibling answer hidden in the same request.
