# Cross-Pack Integration Fixtures

This directory contains three multi-pack integration scenarios that verify packs work correctly when composed together. All fixtures run without an LLM or API key.

---

## Fixtures

### `cross_pack_integration.py` — Tool Gateway → Core → Memory Gateway

The full capability pipeline end-to-end:

1. A `CapabilityProvider` is registered
2. A `CapabilityCall` is proposed (low risk → `policy_enforcer` auto-approves)
3. `call_executor` fires on `capability_approval.created` → executes the mock CRM tool → creates `CapabilityResult`
4. `result_sourcer` creates a Core `source` from the result
5. Core `observation_extractor` extracts observations from the source
6. Core `memory_candidate_proposer` proposes memory candidates for durable observations
7. Memory Gateway `candidate_evaluator` evaluates candidates
8. Memory Gateway `memory_writer` promotes accepted candidates → `MemoryItem`
9. A `memory_retrieval_request` triggers `memory_retriever` → `MemoryRetrieval`
10. `memory_ranker` scores retrieved items → `MemoryRanking`

**Verifies:** policy enforcement, credential injection, output sanitization, Core observation pipeline, memory lifecycle, graph-driven retrieval.

```bash
python packs/fixtures/cross_pack_integration.py
```

---

### `comm_chat_email_integration.py` — Communication + Chat + Email + Identity + Core

The full communication stack with multiple channels and identity resolution:

1. Inbound email from a founder → `email_ingester` creates `Source` + `CommMessage` + `EmailThread`
2. Identity Pack resolves sender → `Principal` (`role=external`)
3. Communication Pack classifies intent (`request`) and creates `CommThread`
4. A response candidate is created → `reply_drafter` creates `EmailDraft`
5. `send_approver` gates the external send → `Action(kind=approval_request, risk_class=high)` created
6. Owner sends a chat message → `chat_ingester` creates `ChatTurn`; `chat_llm_responder` generates response → `ChatTurn.assistant_message` populated
7. Owner is resolved as `Principal(role=owner)`
8. A threaded reply arrives → existing `EmailThread` updated (`message_count=2`)

**Verifies:** email deduplication, CommThread + EmailThread co-existence, external approval gate, chat session continuity, multi-channel identity convergence.

```bash
python packs/fixtures/comm_chat_email_integration.py
```

---

### `identity_profile_entity_integration.py` — Identity/Auth + Agent Profile + Entity + Core

The identity, context, and entity composition loop:

1. An email arrives from an owner contact → `source.created`
2. Identity Pack resolves sender → `Principal(role=owner)` + `AuthContext`
3. Entity Pack extracts entity mentions from the email body → `EntityMention` objects → resolved/created `Entity` objects
4. Agent Profile Pack assembles a behavior-scoped `ProfileContextView` for `channel=email, audience_role=owner`
5. `principal_entity_linker` links `Principal` to the matching `Entity` via identifier overlap

**Verifies:** source → principal → auth_context chain, entity extraction + resolution, profile context assembly (owner vs. external filtering), Identity ↔ Entity linking.

```bash
python packs/fixtures/identity_profile_entity_integration.py
```

---

## Running all three

```bash
# Run each individually
python packs/fixtures/cross_pack_integration.py
python packs/fixtures/comm_chat_email_integration.py
python packs/fixtures/identity_profile_entity_integration.py

# Or run all at once with a summary
python packs/fixtures/run_all.py
```

`run_all.py` exits with code 0 if all pass, 1 if any fail.

---

## No API key required

All three fixtures use deterministic mock stubs:
- Tool Gateway uses a locally registered mock CRM function (no HTTP)
- Chat Pack uses `llm_provider="mock"` for deterministic LLM-free responses
- Memory Gateway uses an in-memory backend

---

## CI

These fixtures are run as part of CI (`.github/workflows/ci.yml`) on every push and pull request after all per-pack fixture runners pass.
