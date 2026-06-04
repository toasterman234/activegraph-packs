---
name: Conversation-driven long-term memory
description: How the assistant builds and recalls durable cross-session memory, and where the swappable seams are.
---

# Key finding: the write path already worked

When wiring "the assistant doesn't remember across sessions", do NOT assume the
write path is missing. Core's `source → observation → memory_candidate →
evaluation → memory_item` pipeline already extracts and persists memories from
any inbound message. The real gap was **retrieval**: chat never issued a query
or folded recalled memory into the prompt.

**How to apply:** when extending memory, check what Core already produces before
adding a new producer; you may only need a retrieval/consumer behavior.

# The three swappable seams (stay unopinionated)

1. **Write path** — contract is the `memory_candidate` object. The default is a
   zero-LLM keyword heuristic (chat_memory_proposer), gated by
   `ChatSettings.memory_write_path` ("heuristic"|"off"). Any pack that emits
   `memory_candidate` feeds the same lifecycle — no Chat Pack edits needed.
2. **Backend** — tiny interface (store_item / retrieve_by_query / find_by_text /
   enforce_limit / clear). Swap `get_backend()` to point at mem0/pgvector/etc.
3. **Embeddings** — `set_embedder` / `set_embedder_factory` /
   `auto_configure_embedder`. Lexical Jaccard by default; cosine when an embedder
   is registered, with PER-ITEM lexical fallback for NULL vectors. Must NEVER
   raise without a key (a misbehaving embedder degrades to lexical).

**Why:** the library is meant to be installable and testable with zero deps and
no API key; embedding providers are deliberately NOT bundled.

# Cross-session recall wiring (the gotcha)

Recall reads the SAME backend the writer persists to. For persistence across a
restart, `MemoryGatewaySettings.backend_url` AND `ChatSettings.memory_backend_url`
must point at the same SQLite file. If they diverge, writes succeed but recall
silently returns nothing.

`close_all_backends()` closes connections but keeps data (used by fixtures to
simulate a restart); `clear_all_backends()` DELETES rows.

# Lexical recall needs keyword overlap

Default Jaccard needs shared tokens between query and stored text. When writing
fixtures, the session-2 query must share words with the stored memory (e.g.
store "I always prefer dark mode...", query "dark mode preferences" → overlap
clears the default min_score 0.1). Natural-language paraphrases recall poorly
without embeddings — that's expected, not a bug.

# Duplicate suppression

Both Core and chat_memory_proposer fire on the same message, so memory_writer
dedups by normalized text via `find_by_text` before creating an item. Note Core
still stores a *question* containing a preference keyword (e.g. "what are my dark
mode preferences?" → category preference) as its own item — that's pre-existing
Core extraction, not a dedup failure.
