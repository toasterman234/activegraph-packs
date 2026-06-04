---
name: Orval query-key invalidation
description: How React Query cache keys work with the orval-generated API client in this repo, and the silent no-op trap.
---

The generated `useXxx` query hooks (from `@workspace/api-client-react`) require
an explicit `queryKey` in the `query` options object — the type will not compile
without one.

**Rule:** use the generated `getXxxQueryKey()` helper as the `queryKey` for the
hook, AND pass the same helper to `queryClient.invalidateQueries({ queryKey: ... })`.

**Why:** if a component invents a custom key like `["getChatConfig"]` for the hook
but invalidates with `getGetChatConfigQueryKey()` (or vice-versa), the keys don't
match, invalidation silently no-ops, and the UI shows stale data until the next
refetchInterval fires. This was flagged in code review on the Secrets/chat pages.

**How to apply:** when adding a new query hook + a mutation that should refresh it,
import both `useXxx` and `getXxxQueryKey` from the client; reuse the helper in both
places. Don't hand-write key arrays.
