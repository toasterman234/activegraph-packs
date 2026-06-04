export const relations = [
  { id: "r1", type: "depends_on", source: "task:deploy-api", target: "task:run-tests", created: "14:02:11.204" },
  { id: "r2", type: "depends_on", source: "task:run-tests", target: "task:build", created: "14:02:09.881" },
  { id: "r3", type: "owns", source: "agent:planner", target: "task:deploy-api", created: "14:01:55.013" },
  { id: "r4", type: "owns", source: "agent:planner", target: "task:run-tests", created: "14:01:55.010" },
  { id: "r5", type: "references", source: "task:build", target: "artifact:bundle-v3", created: "14:00:42.667" },
  { id: "r6", type: "assigned_to", source: "task:run-tests", target: "agent:worker-2", created: "14:01:12.339" },
  { id: "r7", type: "assigned_to", source: "task:build", target: "agent:worker-1", created: "14:00:40.120" },
  { id: "r8", type: "references", source: "agent:worker-2", target: "doc:test-policy", created: "13:59:01.554" },
];

export const relationTypes = [
  { type: "depends_on", count: 2 },
  { type: "owns", count: 2 },
  { type: "references", count: 2 },
  { type: "assigned_to", count: 2 },
];

export const patches = [
  {
    id: "p1", time: "14:02:11.204", object: "task:deploy-api", behavior: "advance_task",
    changes: [
      { field: "status", from: "\"pending\"", to: "\"running\"" },
      { field: "started_at", from: "null", to: "\"2026-06-04T14:02:11Z\"" },
      { field: "attempts", from: "0", to: "1" },
    ],
  },
  {
    id: "p2", time: "14:01:58.660", object: "task:run-tests", behavior: "complete_task",
    changes: [
      { field: "status", from: "\"running\"", to: "\"done\"" },
      { field: "result.passed", from: "null", to: "142" },
      { field: "result.failed", from: "null", to: "0" },
    ],
  },
  {
    id: "p3", time: "14:00:42.667", object: "artifact:bundle-v3", behavior: "register_artifact",
    changes: [
      { field: "size_kb", from: "null", to: "884" },
      { field: "checksum", from: "null", to: "\"a91f…c2\"" },
    ],
  },
];

export const tools = [
  { id: "t1", time: "14:02:10.991", name: "shell.exec", behavior: "run_tests", status: "ok", ms: 4120,
    args: { cmd: "pnpm test", cwd: "/app" }, result: { exit_code: 0, stdout_lines: 142 } },
  { id: "t2", time: "14:02:05.330", name: "http.fetch", behavior: "deploy_api", status: "ok", ms: 612,
    args: { url: "https://api.internal/health", method: "GET" }, result: { status: 200 } },
  { id: "t3", time: "14:01:40.118", name: "fs.write", behavior: "build", status: "ok", ms: 88,
    args: { path: "dist/bundle.js", bytes: 905216 }, result: { ok: true } },
  { id: "t4", time: "14:01:12.004", name: "http.fetch", behavior: "deploy_api", status: "error", ms: 30000,
    args: { url: "https://registry.internal/push", method: "POST" }, result: { error: "ETIMEDOUT after 30000ms" } },
  { id: "t5", time: "14:00:39.770", name: "db.query", behavior: "load_config", status: "ok", ms: 41,
    args: { sql: "SELECT * FROM config LIMIT 1" }, result: { rows: 1 } },
];

export const toolSummary = [
  { name: "http.fetch", calls: 2 },
  { name: "shell.exec", calls: 1 },
  { name: "fs.write", calls: 1 },
  { name: "db.query", calls: 1 },
];

export const failures = [
  { id: "f1", time: "14:01:12.004", reason: "TOOL_ERROR", subject: "deploy_api", kind: "behavior",
    message: "http.fetch → ETIMEDOUT after 30000ms (registry.internal/push)" },
  { id: "f2", time: "13:58:44.219", reason: "BUDGET_EXHAUSTED", subject: "summarize_logs", kind: "behavior",
    message: "token budget 8000 exceeded while expanding context window" },
  { id: "f3", time: "13:57:02.880", reason: "VALIDATION_FAILED", subject: "create_task", kind: "behavior",
    message: "missing required field 'owner' on object task:orphan-9" },
  { id: "f4", time: "13:55:31.447", reason: "TOOL_ERROR", subject: "load_config", kind: "tool",
    message: "db.query → connection refused (127.0.0.1:5432)" },
  { id: "f5", time: "13:54:10.002", reason: "TIMEOUT", subject: "run_tests", kind: "behavior",
    message: "behavior exceeded 60s wall-clock limit" },
];

export const failureReasons = [
  { reason: "TOOL_ERROR", count: 2 },
  { reason: "BUDGET_EXHAUSTED", count: 1 },
  { reason: "VALIDATION_FAILED", count: 1 },
  { reason: "TIMEOUT", count: 1 },
];

export const traceEvents = [
  { id: "e1", time: "14:02:11.204", type: "patch_object", pack: "orchestrator", behavior: "advance_task", object: "task:deploy-api" },
  { id: "e2", time: "14:02:10.991", type: "tool.responded", pack: "orchestrator", behavior: "run_tests", object: "task:run-tests" },
  { id: "e3", time: "14:02:09.640", type: "tool.called", pack: "orchestrator", behavior: "run_tests", object: "task:run-tests" },
  { id: "e4", time: "14:01:58.660", type: "behavior.completed", pack: "orchestrator", behavior: "complete_task", object: "task:run-tests" },
  { id: "e5", time: "14:01:12.004", type: "behavior.failed", pack: "deployer", behavior: "deploy_api", object: "task:deploy-api" },
  { id: "e6", time: "14:00:42.667", type: "create_object", pack: "builder", behavior: "register_artifact", object: "artifact:bundle-v3" },
  { id: "e7", time: "14:00:40.120", type: "create_relation", pack: "builder", behavior: "assign_work", object: "task:build" },
];

export const eventTypes = ["create_object", "patch_object", "create_relation", "behavior.completed", "behavior.failed", "tool.called", "tool.responded"];
export const packs = ["orchestrator", "deployer", "builder"];
export const behaviors = ["advance_task", "run_tests", "complete_task", "deploy_api", "register_artifact", "assign_work"];
