---
name: restart_workflow tool vs restartWorkflow callback
description: The restart_workflow tool consistently fails for artifact-managed workflows even when the server starts fine; use the restartWorkflow callback instead.
---

## Rule

For artifact-managed workflows (those created via `createArtifact`), use the `restartWorkflow({ workflowName, timeout })` callback from the workflows skill instead of the `restart_workflow` tool.

**Why:** The `restart_workflow` tool uses a stricter port-detection check that times out even when Vite/the server is actually listening and serving HTTP 200. It reports "DIDNT_OPEN_A_PORT" after 120–180s despite the service being reachable. The `restartWorkflow` callback from `code_execution` succeeds immediately.

**How to apply:** Any time you need to restart a workflow for an artifact (kind="web", kind="design"), use:
```js
await restartWorkflow({ workflowName: "artifacts/<slug>: web", timeout: 30 });
```

## Additional context

- Vite starts in ~300ms and serves HTTP 200 on both the direct port and via proxy (port 80)
- The proxy at port 80 correctly routes paths to internal service ports
- Manually confirmed: `curl http://localhost:5173/` → 200, `curl http://localhost:80/` → 200
- Port detection via `getWorkflowStatus` shows `openPorts: null` for the failed workflow but `openPorts: [80]` for working ones — this is a monitoring artifact, not a real connectivity issue
- The `restart_workflow` tool appears to check via the external proxy URL, not localhost directly
